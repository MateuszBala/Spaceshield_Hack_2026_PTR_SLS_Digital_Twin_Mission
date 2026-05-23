"""Testy dt_physics — krok 1: struktura SimResult i golden_preset."""

from __future__ import annotations

import math

import pytest

from dt_contracts import EventKind, Phase, RocketParams, SimResult, constants
from dt_physics import golden_preset, simulate


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
    # Liczymy delta-v per stopien od dolnego do gornego.
    # m0_i = payload + wet_mass stopni od i do konca
    # m1_i = m0_i - propellant_mass_i
    stages = preset.stages
    payload_mass = preset.payload.mass
    # masa na poczatku kazdego stopnia = payload + wet_masses powyzej
    cumulative_dv = 0.0
    upper_mass = payload_mass + sum(s.wet_mass for s in stages)
    for stage in stages:
        m0 = upper_mass
        m1 = upper_mass - stage.propellant_mass
        upper_mass = m1 - stage.dry_mass  # po separacji odpada dry_mass
        dv = stage.isp * g0 * math.log(m0 / m1)
        cumulative_dv += dv
    assert cumulative_dv > 13_000.0, f"delta-v={cumulative_dv:.0f} m/s < 13 000"


# ---------------------------------------------------------------------------
# Testy simulate() — krok 1 (zasiepka)
# ---------------------------------------------------------------------------


def test_simulate_returns_sim_result() -> None:
    result = simulate(golden_preset())
    assert isinstance(result, SimResult)


def test_simulate_result_is_frozen() -> None:
    """SimResult jest niemutowalny (FrozenModel)."""
    result = simulate(golden_preset())
    with pytest.raises(Exception):
        result.flight_time = 999.0  # type: ignore[misc]


def test_simulate_stub_has_failed_phase() -> None:
    result = simulate(golden_preset())
    assert result.final_phase == Phase.FAILED


def test_simulate_stub_reached_orbit_false() -> None:
    result = simulate(golden_preset())
    assert result.verdict.reached_orbit is False


def test_simulate_stub_has_liftoff_event() -> None:
    result = simulate(golden_preset())
    kinds = {e.kind for e in result.events}
    assert EventKind.LIFTOFF in kinds


def test_simulate_non_negative_scalars() -> None:
    result = simulate(golden_preset())
    assert result.flight_time >= 0.0
    assert result.max_altitude >= 0.0
    assert result.max_dynamic_pressure >= 0.0
