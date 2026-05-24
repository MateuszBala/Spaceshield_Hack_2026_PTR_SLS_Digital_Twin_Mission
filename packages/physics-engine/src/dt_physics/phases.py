"""Fazy lotu — calkowanie RHS per faza przy uzyciu scipy.solve_ivp.

Stan kanoniczny: [x, y, vx, vy, m] w ukladzie inercjalnym (srodek Ziemi=0,0).

Profil kata ciagu (pitch) w lokalnym ukladzie ciala:
  pitch=pi/2 = radialnie (pionowo)
  pitch=0    = tangentialnie, prograde (poziomo)
Transformacja: F = T*(sin(pitch)*r_hat + cos(pitch)*t_hat)
  r_hat = (x,y)/r,  t_hat = (-y,x)/r (prograde, CCW)

Faza 1 ASCENT:  cial + g(r) + opor D(rho,v)
Faza 2 INSERTION: cial + g(r), opor pomijalny

Zdarzenia terminalne (kolejnosc priorytetu):
  ev_burnout    — czas pracy stopnia wyczerpany
  ev_drag_neg   — D/(m*g) < DRAG_EPS (koniec atmosferycznego oporu)
  ev_orbit_ok   — orbita zwiazana z perygeum > prog (cutoff wstawienia)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp  # type: ignore[import-untyped]

from dt_contracts import EventKind, MissionEvent, Phase, TelemetryFrame
from dt_contracts.constants import MAX_ECCENTRICITY_LEO, MIN_PERIAPSIS_ALTITUDE, MU_EARTH, R_EARTH

from .atmosphere import air_density, dynamic_pressure
from .forces import gravity_accel

# Profil kata: pionowy start, szybkie kladzenie w S1, prawie poziomy od S2
# Agresywne kladzenie skraca czas radialnego ciagu -> mniejsza predkosc radialna
# na koncu S2 -> lepsza ekscentrycznosc przy wstawieniu
PITCH_TURN_START: float = 5.0       # [s] szybko zacznij kladz
PITCH_TURN_END: float = 80.0        # [s] juz w trakcie S1 skoncz kladzenie
PITCH_FINAL_RAD: float = math.radians(4.0)  # prawie poziomy

DRAG_EPS: float = 5e-4   # prog D/(m*g)

_IVP_OPTS: dict = dict(method="RK45", rtol=1e-7, atol=1e-7, max_step=1.0)


# ---------------------------------------------------------------------------
# Pomocnicze geometryczne
# ---------------------------------------------------------------------------

def _pitch(t: float) -> float:
    if t <= PITCH_TURN_START:
        return math.pi / 2.0
    if t >= PITCH_TURN_END:
        return PITCH_FINAL_RAD
    frac = (t - PITCH_TURN_START) / (PITCH_TURN_END - PITCH_TURN_START)
    return math.pi / 2.0 + frac * (PITCH_FINAL_RAD - math.pi / 2.0)


def _thrust_vec(x: float, y: float, thrust: float, t: float) -> tuple[float, float]:
    r = math.sqrt(x * x + y * y)
    rx, ry = x / r, y / r
    tx, ty = -y / r, x / r
    sp, cp = math.sin(_pitch(t)), math.cos(_pitch(t))
    return thrust * (sp * rx + cp * tx), thrust * (sp * ry + cp * ty)


def _drag_force(x: float, y: float, vx: float, vy: float,
                cd: float, area: float) -> tuple[float, float]:
    alt = math.sqrt(x * x + y * y) - R_EARTH
    rho = air_density(alt)
    v2 = vx * vx + vy * vy
    if v2 < 1e-12:
        return 0.0, 0.0
    v = math.sqrt(v2)
    d = 0.5 * rho * v2 * cd * area
    return -d * vx / v, -d * vy / v


def _keplerian_check(x: float, y: float, vx: float, vy: float) -> tuple[float, float, float]:
    """Zwraca (eps, e, periapsis_alt) z wektora stanu 2D.

    Wzor mimosrodu z dokumentu PHYSICS_THEORY_BASE.md (Laplace vector):
      h = x*vy - y*vx
      e_x = vy*h/mu - x/r
      e_y = -vx*h/mu - y/r
      e = sqrt(e_x^2 + e_y^2)
    """
    r = math.sqrt(x * x + y * y)
    v2 = vx * vx + vy * vy
    eps = 0.5 * v2 - MU_EARTH / r

    h = x * vy - y * vx
    e_x = vy * h / MU_EARTH - x / r
    e_y = -vx * h / MU_EARTH - y / r
    e = math.sqrt(e_x * e_x + e_y * e_y)

    if eps >= 0 or e >= 1.0:
        return eps, e, float("-inf")

    a = -MU_EARTH / (2.0 * eps)
    r_p = a * (1.0 - e)
    return eps, e, r_p - R_EARTH


def _state_summary(s: np.ndarray) -> tuple[float, float]:
    x, y, vx, vy, _ = s
    return math.sqrt(x*x + y*y) - R_EARTH, math.sqrt(vx*vx + vy*vy)


# ---------------------------------------------------------------------------
# RHS — czyste funkcje
# ---------------------------------------------------------------------------

def _rhs_ascent(thrust: float, mflow: float, cd: float, area: float
                ) -> Callable[[float, np.ndarray], np.ndarray]:
    def rhs(t: float, s: np.ndarray) -> np.ndarray:
        x, y, vx, vy, m = s
        m = max(m, 1.0)
        gx, gy = gravity_accel(x, y)
        ftx, fty = _thrust_vec(x, y, thrust, t)
        fdx, fdy = _drag_force(x, y, vx, vy, cd, area)
        return np.array([vx, vy, (ftx+fdx)/m+gx, (fty+fdy)/m+gy, -mflow])
    return rhs


def _rhs_insertion(thrust: float, mflow: float) -> Callable[[float, np.ndarray], np.ndarray]:
    def rhs(t: float, s: np.ndarray) -> np.ndarray:
        x, y, vx, vy, m = s
        m = max(m, 1.0)
        gx, gy = gravity_accel(x, y)
        ftx, fty = _thrust_vec(x, y, thrust, t)
        return np.array([vx, vy, ftx/m+gx, fty/m+gy, -mflow])
    return rhs


# ---------------------------------------------------------------------------
# Zdarzenia
# ---------------------------------------------------------------------------

def _ev_burnout(t_burnout: float) -> Callable:
    def ev(t: float, s: np.ndarray) -> float:  # noqa: ARG001
        return t - t_burnout
    ev.terminal = True   # type: ignore[attr-defined]
    ev.direction = 1     # type: ignore[attr-defined]
    return ev


def _ev_drag_negligible(cd: float, area: float) -> Callable:
    def ev(t: float, s: np.ndarray) -> float:  # noqa: ARG001
        x, y, vx, vy, m = s
        m = max(m, 1.0)
        r2 = x*x + y*y
        alt = math.sqrt(r2) - R_EARTH
        rho = air_density(alt)
        v2 = vx*vx + vy*vy
        d = 0.5 * rho * v2 * cd * area
        g = MU_EARTH / r2
        ratio = d / (m * g) if m * g > 0 else 0.0
        return ratio - DRAG_EPS
    ev.terminal = True   # type: ignore[attr-defined]
    ev.direction = -1    # type: ignore[attr-defined]
    return ev


def _ev_orbit_achieved() -> Callable:
    """Terminal: zatrzymaj palenie gdy orbita LEO jest osiagnieta.

    Funkcja przecina ZERO gdy perygeum osiaga MIN_PERIAPSIS_ALTITUDE
    (przy spelnionej energii i mimosrodzie). scipy.brentq wymaga realnego
    przejscia przez zero — tu: peri_alt - MIN_PERIAPSIS_ALTITUDE.

    direction=1: zdarzenie odpala przy przejsciu z ujemnego na dodatni
    (perygeum rosnie i przekracza prog 200 km od dolu).
    """
    def ev(t: float, s: np.ndarray) -> float:  # noqa: ARG001
        x, y, vx, vy, m = s  # noqa: F841
        eps, e, peri_alt = _keplerian_check(x, y, vx, vy)
        # Jezeli ε ≥ 0 lub e > MAX: warunki niespelnione (duze ujemne)
        if eps >= 0 or e > MAX_ECCENTRICITY_LEO:
            return -MIN_PERIAPSIS_ALTITUDE  # ujemne, duze
        # Gdy warunki ε i e spelnione: zwroc peri_alt - prog
        # Ujemne gdy peri za nizko, dodatnie gdy OK → przejscie przez zero
        return peri_alt - MIN_PERIAPSIS_ALTITUDE

    ev.terminal = True   # type: ignore[attr-defined]
    ev.direction = 1     # type: ignore[attr-defined]  # ujemny → dodatni
    return ev


# ---------------------------------------------------------------------------
# Dane segmentu
# ---------------------------------------------------------------------------

@dataclass
class FlightSegment:
    t: np.ndarray
    y: np.ndarray
    phase: Phase
    stage_idx: int


def state_to_frame(t: float, y: np.ndarray, phase: Phase, stage_idx: int) -> TelemetryFrame:
    x, yc, vx, vy, m = y
    alt = math.sqrt(x*x + yc*yc) - R_EARTH
    spd = math.sqrt(vx*vx + vy*vy)
    q = dynamic_pressure(alt, spd)
    return TelemetryFrame(
        t=t, x=x, y=yc, vx=vx, vy=vy, mass=max(m, 1e-3),
        altitude=alt, speed=spd, dynamic_pressure=q, acceleration=0.0,
        phase=phase, active_stage=stage_idx,
    )


# ---------------------------------------------------------------------------
# Glowna petla lotu
# ---------------------------------------------------------------------------

def _integrate(rhs: Callable, state: np.ndarray, t0: float, t_end: float,
               events: list[Callable]) -> object:
    return solve_ivp(rhs, (t0, t_end), state, events=events, **_IVP_OPTS)


def run_flight(
    stages_params: list,
    payload_mass: float,
    launch_angle_deg: float,  # noqa: ARG001
    max_flight_time: float,
    include_telemetry: bool,  # noqa: ARG001
) -> tuple[list[FlightSegment], list[MissionEvent], np.ndarray]:
    """Petla po stopniach — sekwencyjne calkowanie z separacja stanow."""

    state = np.array([R_EARTH, 0.0, 0.0, 0.0,
                      payload_mass + sum(s.wet_mass for s in stages_params)])
    t_now = 0.0
    segments: list[FlightSegment] = []
    events_out: list[MissionEvent] = []
    drag_done = False
    orbit_achieved = False

    for idx, s in enumerate(stages_params):
        if orbit_achieved:
            break

        t_burnout = t_now + s.burn_time
        t_limit = min(t_burnout + 0.1, max_flight_time)

        # ----------------------------------------------------------------
        # Sub-etap A: calkowanie z oporem (jesli drag jeszcze nie pomijalny)
        # ----------------------------------------------------------------
        if not drag_done:
            rhs_a = _rhs_ascent(s.thrust, s.mass_flow, s.drag_coefficient, s.reference_area)
            evs_a = [_ev_burnout(t_burnout), _ev_drag_negligible(s.drag_coefficient, s.reference_area)]
            sol = _integrate(rhs_a, state, t_now, t_limit, evs_a)
            segments.append(FlightSegment(sol.t, sol.y, Phase.ASCENT, idx))
            state = sol.y[:, -1].copy()
            t_now = float(sol.t[-1])

            # drag pomijalny — przejdz do B bez przerywania stopnia
            if sol.t_events[1].size > 0:
                drag_done = True
                t_d = float(sol.t_events[1][0])
                yd = sol.y_events[1][0]
                alt_d, spd_d = _state_summary(yd)
                events_out.append(MissionEvent(
                    kind=EventKind.DRAG_NEGLIGIBLE, t=t_d,
                    altitude=alt_d, speed=spd_d,
                    note=f"D/mg<{DRAG_EPS:.0e} @ h={alt_d/1000:.1f}km",
                ))
                # Dopal resztke stopnia bez oporu (sub-etap B ponizej)

        # ----------------------------------------------------------------
        # Sub-etap B: calkowanie bez oporu (wstawienie)
        # ----------------------------------------------------------------
        if drag_done and t_now < t_burnout - 0.01 and not orbit_achieved:
            rhs_b = _rhs_insertion(s.thrust, s.mass_flow)
            # Od S3 dodaj zdarzenie cutoff wstawienia (nie w S1/S2 - za wczesnie)
            if idx >= len(stages_params) - 1:
                evs_b = [_ev_burnout(t_burnout), _ev_orbit_achieved()]
            else:
                evs_b = [_ev_burnout(t_burnout)]
            sol_b = _integrate(rhs_b, state, t_now, t_limit, evs_b)
            segments.append(FlightSegment(sol_b.t, sol_b.y, Phase.INSERTION, idx))
            state = sol_b.y[:, -1].copy()
            t_now = float(sol_b.t[-1])

            # Sprawdz orbit achieved (zdarzenie index=1 w ostatnim stopniu)
            if idx >= len(stages_params) - 1 and len(sol_b.t_events) > 1 and sol_b.t_events[1].size > 0:
                orbit_achieved = True

        # ----------------------------------------------------------------
        # Burnout + separacja
        # ----------------------------------------------------------------
        alt_bo, spd_bo = _state_summary(state)
        events_out.append(MissionEvent(
            kind=EventKind.STAGE_BURNOUT, t=t_now,
            altitude=alt_bo, speed=spd_bo,
            note=f"{s.name} burnout h={alt_bo/1000:.1f}km v={spd_bo:.0f}m/s",
        ))

        if idx < len(stages_params) - 1 and not orbit_achieved:
            state[4] -= s.dry_mass
            state[4] = max(state[4], 1.0)
            events_out.append(MissionEvent(
                kind=EventKind.STAGE_SEP, t=t_now,
                altitude=alt_bo, speed=spd_bo,
                note=f"{s.name} sep m_rem={state[4]:.0f}kg",
            ))

        if t_now >= max_flight_time or orbit_achieved:
            break

    alt_ins, spd_ins = _state_summary(state)
    events_out.append(MissionEvent(
        kind=EventKind.ORBIT_INSERTION, t=t_now,
        altitude=alt_ins, speed=spd_ins,
        note=f"insertion v={spd_ins:.0f}m/s h={alt_ins/1000:.1f}km",
    ))

    return segments, events_out, state
