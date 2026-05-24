"""Testy dt_physics — krok 1: struktura SimResult i golden_preset."""

from __future__ import annotations

import math

import pytest

from dt_contracts import EventKind, Phase, RocketParams, SimRequest, SimResult, constants
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
# Testy simulate(SimRequest) — krok 1 (zasiepka)
# ---------------------------------------------------------------------------


def test_simulate_returns_sim_result() -> None:
    result = simulate(_req())
    assert isinstance(result, SimResult)


def test_simulate_result_is_frozen() -> None:
    """SimResult jest niemutowalny (FrozenModel)."""
    result = simulate(_req())
    with pytest.raises(Exception):
        result.flight_time = 999.0  # type: ignore[misc]


def test_simulate_stub_has_failed_phase() -> None:
    result = simulate(_req())
    assert result.final_phase == Phase.FAILED


def test_simulate_stub_reached_orbit_false() -> None:
    result = simulate(_req())
    assert result.verdict.reached_orbit is False


def test_simulate_stub_has_liftoff_event() -> None:
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
