"""Orchestrator symulacji - publiczny punkt wejscia dt_physics.

simulate(SimRequest) -> SimResult  — kontrakt zewnetrzny.
Parametry rakiety czytane jako request.rocket; request.include_telemetry
steruje obecnoscia pelnej telemetrii; request.max_flight_time to twardy
limit t_span w solve_ivp.
Implementacja przyrostowa: krok 1 = zasiepka strukturalna; krok 2+ = realna
trajektoria (see BRIEF-engine-02).
"""

from __future__ import annotations

from dt_contracts import (
    EventKind,
    MissionEvent,
    OrbitVerdict,
    Phase,
    SimRequest,
    SimResult,
)


def simulate(request: SimRequest) -> SimResult:  # noqa: ARG001
    """Oblicz trajektorie misji i zwroc wynik zgodny z kontraktem.

    Krok 1 (stub): zwraca poprawny strukturalnie SimResult z reached_orbit=False.
    Gotowy do transportu przez API — odblokowanie pionowego plastra.
    Krok 2 zastapi stub realnym calkowaniem (see engine_phases.py).
    """
    liftoff_event = MissionEvent(
        kind=EventKind.LIFTOFF,
        t=0.0,
        altitude=0.0,
        speed=0.0,
        note="start (stub)",
    )
    verdict = OrbitVerdict(
        reached_orbit=False,
        reason="Stub krok 1: fizyka niezaimplementowana.",
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
