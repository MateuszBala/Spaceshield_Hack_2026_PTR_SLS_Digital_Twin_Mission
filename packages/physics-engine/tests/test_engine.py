"""Testy dt_physics — krok 1+2: struktura SimResult, golden_preset, werdykt."""

from __future__ import annotations

import math

import pytest

from dt_contracts import EventKind, Phase, RocketParams, SimRequest, SimResult, Stage, Payload, constants
from dt_physics import golden_preset, simulate


def _req(rocket: RocketParams | None = None, **kwargs: object) -> SimRequest:
    """Pomocnik: opakowuje RocketParams w SimRequest."""
    return SimRequest(rocket=rocket or golden_preset(), **kwargs)


# ---------------------------------------------------------------------------
# Testy golden_preset
# ---------------------------------------------------------------------------


def test_golden_preset_returns_valid_rocket_params() -> None:
    preset = golden_preset()
    assert isinstance(preset, RocketParams)


def test_golden_preset_has_three_stages() -> None:
    assert len(golden_preset().stages) == 3


def test_golden_preset_payload() -> None:
    preset = golden_preset()
    assert preset.payload.mass == 150.0
    assert preset.payload.name == "sat-150"


def test_golden_preset_liftoff_mass() -> None:
    """Masa startowa ≈ 39 304 kg (wartosc z GOLDEN_PRESET.md ± 5 kg)."""
    preset = golden_preset()
    assert abs(preset.liftoff_mass - 39_304.0) < 5.0


def test_golden_preset_isp_within_chemical_limits() -> None:
    preset = golden_preset()
    for stage in preset.stages:
        assert constants.ISP_MIN <= stage.isp <= constants.ISP_MAX_CHEMICAL


def test_golden_preset_mass_fractions_typical() -> None:
    """Wszystkie frakcje masowe w przedziale typowym SMAD [0.80, 0.95]."""
    preset = golden_preset()
    for stage in preset.stages:
        assert constants.STAGE_MASS_FRACTION_TYPICAL_MIN <= stage.mass_fraction
        assert stage.mass_fraction <= constants.STAGE_MASS_FRACTION_TYPICAL_MAX


def test_golden_preset_delta_v_budget() -> None:
    """Budzet delta-v z Ciołkowskiego (bez strat) > 13 000 m/s."""
    preset = golden_preset()
    g0 = constants.G0
    stages = preset.stages
    payload_mass = preset.payload.mass
    cumulative_dv = 0.0
    upper_mass = payload_mass + sum(s.wet_mass for s in stages)
    for stage in stages:
        m0 = upper_mass
        m1 = upper_mass - stage.propellant_mass
        upper_mass = m1 - stage.dry_mass
        dv = stage.isp * g0 * math.log(m0 / m1)
        cumulative_dv += dv
    assert cumulative_dv > 13_000.0, f"delta-v={cumulative_dv:.0f} m/s < 13 000"


# ---------------------------------------------------------------------------
# Testy simulate(SimRequest) — krok 1: struktura
# ---------------------------------------------------------------------------


def test_simulate_returns_sim_result() -> None:
    result = simulate(_req())
    assert isinstance(result, SimResult)


def test_simulate_result_is_frozen() -> None:
    """SimResult jest niemutowalny (FrozenModel)."""
    result = simulate(_req())
    with pytest.raises(Exception):
        result.flight_time = 999.0  # type: ignore[misc]


def test_simulate_has_liftoff_event() -> None:
    result = simulate(_req())
    kinds = {e.kind for e in result.events}
    assert EventKind.LIFTOFF in kinds


def test_simulate_non_negative_scalars() -> None:
    result = simulate(_req())
    assert result.flight_time >= 0.0
    assert result.max_altitude >= 0.0
    assert result.max_dynamic_pressure >= 0.0


def test_simulate_include_telemetry_default_true() -> None:
    """include_telemetry=True (domyslnie) — kontrakt przyjety poprawnie."""
    req = SimRequest(rocket=golden_preset(), include_telemetry=True)
    result = simulate(req)
    assert isinstance(result, SimResult)


def test_simulate_no_telemetry_flag() -> None:
    """include_telemetry=False — simulate przyjmuje i nie wywala wyjatku."""
    req = SimRequest(rocket=golden_preset(), include_telemetry=False)
    result = simulate(req)
    assert result.telemetry == []


def test_simulate_max_flight_time_custom() -> None:
    """max_flight_time przechodzi przez SimRequest bez bledu walidacji."""
    req = SimRequest(rocket=golden_preset(), max_flight_time=600.0)
    result = simulate(req)
    assert isinstance(result, SimResult)


# ---------------------------------------------------------------------------
# Testy werdyktu — krok 2: werdykt keplerowski + fallback delta-v
# ---------------------------------------------------------------------------


def test_golden_preset_reaches_orbit() -> None:
    """Golden preset musi osiagnac orbite (gałąź keplerowski lub fallback dv)."""
    result = simulate(_req())
    assert result.verdict.reached_orbit is True, (
        f"Golden preset nie osiagnal orbity: {result.verdict.reason}"
    )


def test_golden_preset_final_phase_orbit() -> None:
    """final_phase == ORBIT gdy orbita osiagnieta."""
    result = simulate(_req())
    assert result.final_phase == Phase.ORBIT


def test_golden_preset_verdict_has_elements() -> None:
    """Werdykt sukcesu zawiera elementy keplerowskie."""
    result = simulate(_req())
    assert result.verdict.elements is not None


def test_insufficient_rocket_fails() -> None:
    """Rakieta z drastycznie zmniejszonym paliwem nie osiaga orbity."""
    tiny = RocketParams(
        stages=[
            Stage(
                name="S1-weak",
                dry_mass=500.0,
                thrust=50_000.0,
                isp=282.0,
                burn_time=10.0,  # bardzo krotki czas pracy
                drag_coefficient=0.30,
                reference_area=3.0,
            ),
        ],
        payload=Payload(mass=50.0, name="cubesat"),
        launch_angle_deg=90.0,
    )
    result = simulate(SimRequest(rocket=tiny))
    assert result.verdict.reached_orbit is False


def test_fallback_dv_threshold_demo_slider() -> None:
    """Demo slider: redukcja S3 burn_time ponizej progu -> brak orbity.

    Prog: przy burn_time=1s budzet Ciolkowskiego drastycznie spada.
    """
    preset = golden_preset()
    stages = list(preset.stages)
    s3 = stages[2]
    # burn_time=1s: Δv_S3 ≈ isp*g0*ln(m0/m1) z 1s propellant — minimal
    s3_weak = Stage(
        name=s3.name,
        dry_mass=s3.dry_mass,
        thrust=s3.thrust,
        isp=s3.isp,
        burn_time=1.0,
        drag_coefficient=s3.drag_coefficient,
        reference_area=s3.reference_area,
    )
    # Rowniez drastycznie ogranicz S2 i S1
    s1 = stages[0]
    s1_weak = Stage(
        name=s1.name,
        dry_mass=s1.dry_mass,
        thrust=s1.thrust,
        isp=s1.isp,
        burn_time=10.0,  # 10s zamiast 105s
        drag_coefficient=s1.drag_coefficient,
        reference_area=s1.reference_area,
    )
    weak_rocket = RocketParams(
        stages=[s1_weak, stages[1], s3_weak],
        payload=preset.payload,
        launch_angle_deg=90.0,
    )
    result = simulate(SimRequest(rocket=weak_rocket))
    assert result.verdict.reached_orbit is False, (
        "Oslabiona rakieta nie powinna osiagac orbity"
    )
