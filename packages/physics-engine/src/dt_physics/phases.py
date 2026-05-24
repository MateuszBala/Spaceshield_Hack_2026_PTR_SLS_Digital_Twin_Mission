"""Fazy lotu — calkowanie RHS per faza przy uzyciu scipy.solve_ivp.

Stan kanoniczny: [x, y, vx, vy, m] w ukladzie inercjalnym (srodek Ziemi=0,0).

Profil kata ciagu — gravity turn (czasowy):
  t < PITCH_KICK_START : pionowo (radialnie) — budowanie predkosci
  PITCH_KICK_START..PITCH_END_TIME: liniowy zwrot pitch: 90deg → PITCH_FINAL_RAD
  t >= PITCH_END_TIME   : ciag podaza za wektorem predkosci (prograde tracking)

Uzasadnienie programu pitch S1 + coast do apoapsis + S3:
  Po S2 burnout (h~210 km, v~97% v_circ, FPA~12.8 deg) bezposrednie odpalenie
  S3 daje cutoff za nizko — perygeum pod ziemia. Zamiast tego:
  rakieta coastuje balistycznie do apoapsis (~1260 km, v_r=0), dopiero tam S3
  zapala sie w kierunku prograde = tangentialnym. Circularyzacja Hohmannem.

Transformacja: F = T * v_hat  (prograde) lub T*(sin*r_hat + cos*t_hat) dla programu.
  r_hat = (x,y)/r,  t_hat = (-y,x)/r (prograde, CCW)
  pitch=pi/2 → radialny (pionowy); pitch=0 → tangentialny (poziomy).

Faza 1 ASCENT:  cial + g(r) + opor D(rho,v)
Faza 2 INSERTION: cial + g(r), opor pomijalny

Zdarzenia terminalne (kolejnosc priorytetu):
  ev_burnout    — czas pracy stopnia wyczerpany
  ev_drag_neg   — D/(m*g) < DRAG_EPS (koniec atmosferycznego oporu)
  ev_vcir_cutoff — v >= sqrt(mu/r) przy h > CUTOFF_MIN_ALT (gorny stopien)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp  # type: ignore[import-untyped]

from dt_contracts import EventKind, MissionEvent, Phase, TelemetryFrame
from dt_contracts.constants import MIN_PERIAPSIS_ALTITUDE, MU_EARTH, R_EARTH

from .atmosphere import air_density, dynamic_pressure
from .forces import gravity_accel

# ---------------------------------------------------------------------------
# Profil kata ciagu — time-based pitch program + prograde tracking
# ---------------------------------------------------------------------------

# Program czasowy zapewnia, ze pozny S1 (wysoka T/m, ~78 m/s^2) pali prawie poziomo.
# Pitch=pi/2 → pionowo; pitch=0 → poziomo (tangentialnie).

PITCH_KICK_START: float = 10.0              # [s] poczatek zwrotu; ponizej: pionowo
PITCH_END_TIME: float = 95.0               # [s] koniec programu; po nim: prograde
PITCH_FINAL_RAD: float = math.radians(4.0) # kat na koncu programu (prawie poziomy)

# Cutoff gornego stopnia — odciecie ciagu gdy v dorownuje v_circ
# Bramka h > CUTOFF_MIN_ALT zapobiega przedwczesnemu odpalu tuż po starcie.
CUTOFF_MIN_ALT: float = MIN_PERIAPSIS_ALTITUDE  # [m] = 200 km

# Faza wybiegowa (coast) — max czas swobodnego lotu do apoapsis przed S3.
# Orbit S2 ma apoapsis ~1260 km (z danych misji), co zajmuje ~1200 s.
COAST_MAX_TIME: float = 1800.0  # [s] limit bezpieczenstwa

DRAG_EPS: float = 5e-4   # prog D/(m*g) dla wylaczenia oporu
_IVP_OPTS: dict = dict(method="RK45", rtol=1e-8, atol=1e-8, max_step=1.0)


# ---------------------------------------------------------------------------
# Wektor ciagu — time-based pitch program + prograde tracking
# ---------------------------------------------------------------------------

def _thrust_vec(x: float, y: float, vx: float, vy: float,
                thrust: float, t: float) -> tuple[float, float]:
    """Wektor ciagu: czasowy program zwrotu w S1 → prograde tracking w S2/S3.

    t < PITCH_KICK_START     : czysto radialny (pionowo)
    PITCH_KICK_START..PITCH_END_TIME: pitch liniowo z pi/2 → PITCH_FINAL_RAD
    t > PITCH_END_TIME       : ciag = kierunek predkosci (prograde tracking)

    Po apoapsis (coast), faza S3: prograde = tangentialny (v_r~0 w apoapsis),
    co daje circularyzacje Hohmannem minimalnym zuzycie propellentu.
    """
    r = math.sqrt(x * x + y * y)
    rx, ry = x / r, y / r      # r_hat (radialny = "pionowo w gore")
    tx, ty = -y / r, x / r    # t_hat (prograde, CCW)

    if t < PITCH_KICK_START:
        return thrust * rx, thrust * ry

    if t < PITCH_END_TIME:
        frac = (t - PITCH_KICK_START) / (PITCH_END_TIME - PITCH_KICK_START)
        pitch = math.pi / 2.0 + frac * (PITCH_FINAL_RAD - math.pi / 2.0)
        sp, cp = math.sin(pitch), math.cos(pitch)
        return thrust * (sp * rx + cp * tx), thrust * (sp * ry + cp * ty)

    # Prograde tracking: ciag = kierunek predkosci
    v2 = vx * vx + vy * vy
    if v2 < 1.0:
        return thrust * rx, thrust * ry
    v = math.sqrt(v2)
    return thrust * vx / v, thrust * vy / v


# ---------------------------------------------------------------------------
# Sila oporu — pomocnicza (inline, by uniknac importu forces w tym scope)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# RHS — czyste funkcje
# ---------------------------------------------------------------------------

def _rhs_ascent(thrust: float, mflow: float, cd: float, area: float
                ) -> Callable[[float, np.ndarray], np.ndarray]:
    def rhs(t: float, s: np.ndarray) -> np.ndarray:
        x, y, vx, vy, m = s
        m = max(m, 1.0)
        gx, gy = gravity_accel(x, y)
        ftx, fty = _thrust_vec(x, y, vx, vy, thrust, t)
        fdx, fdy = _drag_force(x, y, vx, vy, cd, area)
        return np.array([vx, vy, (ftx + fdx) / m + gx, (fty + fdy) / m + gy, -mflow])
    return rhs


def _rhs_insertion(thrust: float, mflow: float) -> Callable[[float, np.ndarray], np.ndarray]:
    def rhs(t: float, s: np.ndarray) -> np.ndarray:
        x, y, vx, vy, m = s
        m = max(m, 1.0)
        gx, gy = gravity_accel(x, y)
        ftx, fty = _thrust_vec(x, y, vx, vy, thrust, t)
        return np.array([vx, vy, ftx / m + gx, fty / m + gy, -mflow])
    return rhs


# ---------------------------------------------------------------------------
# Zdarzenia terminalne
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
        r2 = x * x + y * y
        alt = math.sqrt(r2) - R_EARTH
        rho = air_density(alt)
        v2 = vx * vx + vy * vy
        d = 0.5 * rho * v2 * cd * area
        g = MU_EARTH / r2
        ratio = d / (m * g) if m * g > 0 else 0.0
        return ratio - DRAG_EPS
    ev.terminal = True   # type: ignore[attr-defined]
    ev.direction = -1    # type: ignore[attr-defined]
    return ev


def _rhs_coast() -> Callable[[float, np.ndarray], np.ndarray]:
    """RHS bez ciagu: czysta grawitacja (Keplerowski lot swobodny)."""
    def rhs(t: float, s: np.ndarray) -> np.ndarray:
        x, y, vx, vy, m = s
        gx, gy = gravity_accel(x, y)
        return np.array([vx, vy, gx, gy, 0.0])
    return rhs


def _ev_apoapsis() -> Callable:
    """Apoapsis: radialny skladnik predkosci v_r przechodzi przez zero (+ → -).

    v_r = (r_vec · v_vec) / |r_vec| = (x*vx + y*vy) / r.
    direction=-1: odpala gdy v_r maleje i przekracza zero z gory.
    """
    def ev(t: float, s: np.ndarray) -> float:
        x, y, vx, vy, m = s  # noqa: F841
        r = math.sqrt(x * x + y * y)
        return (x * vx + y * vy) / r
    ev.terminal = True   # type: ignore[attr-defined]
    ev.direction = -1    # type: ignore[attr-defined]
    return ev


def _ev_vcir_cutoff() -> Callable:
    """Cutoff gornego stopnia: v >= v_circ(r) przy h > CUTOFF_MIN_ALT.

    W chwili odpalu: eps = v^2/2 - mu/r = mu/(2r) - mu/r = -mu/(2r) < 0 (zawsze
    zwiazana) i e = |sin(FPA)| — mimosrod zalezy od FPA w tej chwili.

    Bramka altitudowa (h > CUTOFF_MIN_ALT) zapobiega odpaleniu w atmosferze.
    direction=1: zdarzenie odpala gdy v rosnie i przekracza v_circ.
    """
    def ev(t: float, s: np.ndarray) -> float:  # noqa: ARG001
        x, y, vx, vy, m = s  # noqa: F841
        r2 = x * x + y * y
        r = math.sqrt(r2)
        alt = r - R_EARTH
        if alt < CUTOFF_MIN_ALT:
            return -1.0  # bramka wysokosciowa
        v2 = vx * vx + vy * vy
        return v2 - MU_EARTH / r  # zero gdy v = v_circ
    ev.terminal = True   # type: ignore[attr-defined]
    ev.direction = 1     # type: ignore[attr-defined]
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
    accel: np.ndarray | None = None  # |a| = sqrt(ax²+ay²) per krok [m/s²]


def _compute_accel(rhs: Callable, t_arr: np.ndarray, y_arr: np.ndarray) -> np.ndarray:
    """Modul przyspieszenia |a|=sqrt(ax²+ay²) dla kazdego punktu trajektorii.

    Wywoluje RHS (ten sam co w solve_ivp) i wyciaga skladowe ax=d[2], ay=d[3].
    """
    out = np.empty(len(t_arr))
    for i in range(len(t_arr)):
        d = rhs(float(t_arr[i]), y_arr[:, i])
        out[i] = math.sqrt(d[2] * d[2] + d[3] * d[3])
    return out


def state_to_frame(t: float, y: np.ndarray, phase: Phase, stage_idx: int,
                   accel: float = 0.0) -> TelemetryFrame:
    x, yc, vx, vy, m = y
    alt = math.sqrt(x * x + yc * yc) - R_EARTH
    spd = math.sqrt(vx * vx + vy * vy)
    q = dynamic_pressure(alt, spd)
    return TelemetryFrame(
        t=t, x=x, y=yc, vx=vx, vy=vy, mass=max(m, 1e-3),
        altitude=alt, speed=spd, dynamic_pressure=q, acceleration=accel,
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
        # Pre-check: czy drag juz zaniedbywalny na poczatku stopnia?
        # Potrzebne gdy stopien startuje po burnoucie poprzedniego na duzej
        # wysokosci — solve_ivp nie wykrywa zdarzenia jesli funkcja jest juz
        # po przejsciu (direction=-1 ale wartosc startuje ujemna).
        # ----------------------------------------------------------------
        if not drag_done:
            _x, _y, _vx, _vy, _ms = state
            _ms = max(_ms, 1.0)
            _r2 = _x * _x + _y * _y
            _r = math.sqrt(_r2)
            _alt = _r - R_EARTH
            _rho = air_density(_alt)
            _v2 = _vx * _vx + _vy * _vy
            _d = 0.5 * _rho * _v2 * s.drag_coefficient * s.reference_area
            _g = MU_EARTH / _r2
            if _v2 > 1.0 and _ms * _g > 0 and _d / (_ms * _g) < DRAG_EPS:
                drag_done = True

        # ----------------------------------------------------------------
        # Sub-etap A: calkowanie z oporem (jesli drag jeszcze nie pomijalny)
        # ----------------------------------------------------------------
        if not drag_done:
            rhs_a = _rhs_ascent(s.thrust, s.mass_flow, s.drag_coefficient, s.reference_area)
            evs_a = [
                _ev_burnout(t_burnout),
                _ev_drag_negligible(s.drag_coefficient, s.reference_area),
            ]
            sol = _integrate(rhs_a, state, t_now, t_limit, evs_a)
            segments.append(FlightSegment(sol.t, sol.y, Phase.ASCENT, idx,
                                          accel=_compute_accel(rhs_a, sol.t, sol.y)))
            state = sol.y[:, -1].copy()
            t_now = float(sol.t[-1])

            if sol.t_events[1].size > 0:
                drag_done = True
                t_d = float(sol.t_events[1][0])
                yd = sol.y_events[1][0]
                alt_d = math.sqrt(yd[0]**2 + yd[1]**2) - R_EARTH
                spd_d = math.sqrt(yd[2]**2 + yd[3]**2)
                events_out.append(MissionEvent(
                    kind=EventKind.DRAG_NEGLIGIBLE, t=t_d,
                    altitude=alt_d, speed=spd_d,
                    note=f"D/mg<{DRAG_EPS:.0e} @ h={alt_d/1000:.1f}km",
                ))

        # ----------------------------------------------------------------
        # Faza wybiegowa (coast) przed ostatnim stopniem — Hohmann insertion
        # Rakieta coastuje balistycznie do apoapsis orbity S1+S2.
        # W apoapsis v_r=0, wiec prograde S3 = tangentialny → optymalna
        # circularyzacja, FPA<<1deg przy v_circ cutoff.
        # ----------------------------------------------------------------
        is_last = (idx >= len(stages_params) - 1)
        if is_last and drag_done and not orbit_achieved:
            rhs_c = _rhs_coast()
            t_coast_end = min(t_now + COAST_MAX_TIME, max_flight_time)
            sol_c = _integrate(rhs_c, state, t_now, t_coast_end, [_ev_apoapsis()])
            segments.append(FlightSegment(sol_c.t, sol_c.y, Phase.INSERTION, idx,
                                          accel=_compute_accel(rhs_c, sol_c.t, sol_c.y)))
            state = sol_c.y[:, -1].copy()
            t_now = float(sol_c.t[-1])
            alt_apo = math.sqrt(state[0]**2 + state[1]**2) - R_EARTH
            spd_apo = math.sqrt(state[2]**2 + state[3]**2)
            events_out.append(MissionEvent(
                kind=EventKind.APOGEE, t=t_now,
                altitude=alt_apo, speed=spd_apo,
                note=f"apoapsis coast h={alt_apo/1000:.0f}km v={spd_apo:.0f}m/s",
            ))
            # Aktualizuj t_limit na nowy burn_time od t_now
            t_burnout = t_now + s.burn_time
            t_limit = min(t_burnout + 0.1, max_flight_time)

        # ----------------------------------------------------------------
        # Sub-etap B: calkowanie bez oporu (wstawienie)
        # ----------------------------------------------------------------
        if drag_done and t_now < t_burnout - 0.01 and not orbit_achieved:
            rhs_b = _rhs_insertion(s.thrust, s.mass_flow)
            if is_last:
                evs_b = [_ev_burnout(t_burnout), _ev_vcir_cutoff()]
            else:
                evs_b = [_ev_burnout(t_burnout)]
            sol_b = _integrate(rhs_b, state, t_now, t_limit, evs_b)
            segments.append(FlightSegment(sol_b.t, sol_b.y, Phase.INSERTION, idx,
                                          accel=_compute_accel(rhs_b, sol_b.t, sol_b.y)))
            state = sol_b.y[:, -1].copy()
            t_now = float(sol_b.t[-1])

            # vcir_cutoff odpalony (index 1) => orbita osiagnieta
            if is_last and len(sol_b.t_events) > 1 and sol_b.t_events[1].size > 0:
                orbit_achieved = True

        # ----------------------------------------------------------------
        # Burnout + separacja
        # ----------------------------------------------------------------
        alt_bo = math.sqrt(state[0]**2 + state[1]**2) - R_EARTH
        spd_bo = math.sqrt(state[2]**2 + state[3]**2)
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

    alt_ins = math.sqrt(state[0]**2 + state[1]**2) - R_EARTH
    spd_ins = math.sqrt(state[2]**2 + state[3]**2)
    events_out.append(MissionEvent(
        kind=EventKind.ORBIT_INSERTION, t=t_now,
        altitude=alt_ins, speed=spd_ins,
        note=f"insertion v={spd_ins:.0f}m/s h={alt_ins/1000:.1f}km",
    ))

    return segments, events_out, state
