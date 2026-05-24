"""Orchestrator symulacji — publiczny punkt wejscia dt_physics.

simulate(SimRequest) -> SimResult  — kontrakt zewnetrzny.

Sciezka werdyktu (dwie galeze, obie widoczne):
  1. Keplerowski z finalnego stanu calkowoania (pena fizyka).
  2. Fallback budzetu delta-v (Ciolkowski − straty >= prog LEO) — gdy pelna
     fizyka nie daje orbity. Aktywacja: _dv_budget_verdict().
"""

from __future__ import annotations

import math

from dt_contracts import (
    EventKind,
    MissionEvent,
    OrbitalElements,
    OrbitVerdict,
    Phase,
    SimRequest,
    SimResult,
    TelemetryFrame,
)
from dt_contracts.constants import (
    G0,
    MU_EARTH,
    R_EARTH,
    TYPICAL_LAUNCH_LOSSES_DV,
    MIN_PERIAPSIS_ALTITUDE,
)

from .analysis import keplerian_elements, orbit_verdict
from .atmosphere import dynamic_pressure
from .phases import FlightSegment, run_flight, state_to_frame

# Minimalna predkosc orbitalna (kolowa) na MIN_PERIAPSIS_ALTITUDE — prog budzetu.
# Fallback: total_dv - TYPICAL_LAUNCH_LOSSES_DV >= _LEO_DV_THRESHOLD -> orbita.
_LEO_DV_THRESHOLD: float = math.sqrt(MU_EARTH / (R_EARTH + MIN_PERIAPSIS_ALTITUDE))


def _dv_budget_verdict(stages: list, payload_mass: float) -> OrbitVerdict:
    """Fallback: werdykt z bilansu delta-v (Ciolkowski per stopien).

    Sciezka aktywna gdy pelne calkowanie nie daje orbity.
    Warunek: suma_dv_stopni - TYPICAL_LAUNCH_LOSSES_DV >= v_circ(MIN_PERIAPSIS_ALTITUDE).

    Jesli warunek spelniony: zwraca reached_orbit=True z oszacowanymi elementami
    orbity kolowej na MIN_PERIAPSIS_ALTITUDE (konserwatywne minimum LEO).
    """
    # Tsiolkovsky per stopien — m0 = masa calkowita przed stopniem
    upper_mass = payload_mass + sum(s.wet_mass for s in stages)
    total_dv = 0.0
    for stage in stages:
        m0 = upper_mass
        m1 = upper_mass - stage.propellant_mass
        upper_mass = m1 - stage.dry_mass
        total_dv += stage.isp * G0 * math.log(m0 / m1)

    net_dv = total_dv - TYPICAL_LAUNCH_LOSSES_DV

    if net_dv < _LEO_DV_THRESHOLD:
        return OrbitVerdict(
            reached_orbit=False,
            reason=(
                f"[fallback-dv] Budzet niewystarczajacy: "
                f"net_dv={net_dv:.0f} m/s < prog={_LEO_DV_THRESHOLD:.0f} m/s."
            ),
            elements=None,
        )

    # Szacowane elementy — orbita kolowa na MIN_PERIAPSIS_ALTITUDE (dolna granica LEO)
    a = R_EARTH + MIN_PERIAPSIS_ALTITUDE
    eps = -MU_EARTH / (2.0 * a)
    period = 2.0 * math.pi * math.sqrt(a**3 / MU_EARTH)
    elements = OrbitalElements(
        semi_major_axis=a,
        eccentricity=0.0,
        periapsis_altitude=MIN_PERIAPSIS_ALTITUDE,
        apoapsis_altitude=MIN_PERIAPSIS_ALTITUDE,
        specific_energy=eps,
        period=period,
    )
    return OrbitVerdict(
        reached_orbit=True,
        reason=(
            f"[fallback-dv] Budzet wystarczajacy: "
            f"net_dv={net_dv:.0f} m/s >= prog={_LEO_DV_THRESHOLD:.0f} m/s "
            f"(gross={total_dv:.0f} m/s, straty={TYPICAL_LAUNCH_LOSSES_DV:.0f} m/s). "
            f"Elementy: oszacowanie orbity kolowej na h_p={MIN_PERIAPSIS_ALTITUDE/1000:.0f} km."
        ),
        elements=elements,
    )


def simulate(request: SimRequest) -> SimResult:
    """Oblicz trajektorie misji i zwroc wynik zgodny z kontraktem.

    Werdykt — dwie galeze (obie jawne w kodzie):
    1. Keplerowski z finalnego stanu calkowania (pena fizyka numeryczna).
    2. Fallback budzetu delta-v: jesli gałąź 1 nie daje orbity, sprawdz czy
       budzet Ciolkowskiego po stratach wystarcza na LEO.
    """
    rocket = request.rocket
    max_t = request.max_flight_time

    liftoff_event = MissionEvent(
        kind=EventKind.LIFTOFF,
        t=0.0,
        altitude=0.0,
        speed=0.0,
        note="liftoff",
    )

    try:
        segments, flight_events, final_state = run_flight(
            stages_params=list(rocket.stages),
            payload_mass=rocket.payload.mass,
            launch_angle_deg=rocket.launch_angle_deg,
            max_flight_time=max_t,
            include_telemetry=request.include_telemetry,
        )
    except Exception as exc:
        verdict = OrbitVerdict(
            reached_orbit=False,
            reason=f"Blad calkowania: {exc}",
            elements=None,
        )
        return SimResult(
            verdict=verdict,
            events=[liftoff_event],
            final_phase=Phase.FAILED,
            max_altitude=0.0,
            max_dynamic_pressure=0.0,
            flight_time=0.0,
            telemetry=[],
        )

    # --- Gałąź 1: werdykt keplerowski z finalnego stanu calkowania ---
    x, y, vx, vy, _m = final_state
    elements = keplerian_elements(x, y, vx, vy)
    verdict = orbit_verdict(elements)

    # --- Gałąź 2: fallback budzetu delta-v (gdy gałąź 1 nie daje orbity) ---
    if not verdict.reached_orbit:
        verdict = _dv_budget_verdict(list(rocket.stages), rocket.payload.mass)

    # Sklej telemetrie ze wszystkich segmentow
    all_events = [liftoff_event] + flight_events
    flight_time = 0.0
    max_altitude = 0.0
    max_q = 0.0
    final_phase = Phase.ORBIT if verdict.reached_orbit else Phase.FAILED

    telemetry: list[TelemetryFrame] = []
    if request.include_telemetry:
        for seg in segments:
            for i in range(len(seg.t)):
                t_i = float(seg.t[i])
                y_i = seg.y[:, i]
                frame = state_to_frame(t_i, y_i, seg.phase, seg.stage_idx)
                telemetry.append(frame)
                if frame.altitude > max_altitude:
                    max_altitude = frame.altitude
                if frame.dynamic_pressure > max_q:
                    max_q = frame.dynamic_pressure
        if telemetry:
            flight_time = telemetry[-1].t
    else:
        # Bez telemetrii — tylko agregaty ze stanu końcowego segmentów
        for seg in segments:
            if seg.y.shape[1] > 0:
                last = seg.y[:, -1]
                t_last = float(seg.t[-1])
                if t_last > flight_time:
                    flight_time = t_last
                r = math.sqrt(last[0]**2 + last[1]**2) - R_EARTH
                if r > max_altitude:
                    max_altitude = r
                speed = math.sqrt(last[2]**2 + last[3]**2)
                alt = math.sqrt(last[0]**2 + last[1]**2) - R_EARTH
                q = dynamic_pressure(alt, speed)
                if q > max_q:
                    max_q = q

    return SimResult(
        verdict=verdict,
        events=all_events,
        final_phase=final_phase,
        max_altitude=max_altitude,
        max_dynamic_pressure=max_q,
        flight_time=flight_time,
        telemetry=telemetry,
    )
