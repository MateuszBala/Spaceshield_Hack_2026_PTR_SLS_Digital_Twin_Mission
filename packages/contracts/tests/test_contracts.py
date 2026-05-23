"""Testy jednostkowe kontraktu dt_contracts.

Pokrywaja wlasciwosci stanowiace SEDNO kontraktu:
- niespojne dane sa NIEMOZLIWE (mass_flow jest pochodna, nie parametrem),
- twarde granice walidacji (Isp <= 455 s, liczba stopni 1-4, masy > 0),
- poprawnosc pol pochodnych (rownanie ciagu SMAD Eq.17-4, liftoff_mass),
- niemutowalnosc (frozen) wejscia i wyniku,
- odrzucanie nieznanych pol (extra="forbid").
"""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from dt_contracts import (
    OrbitalElements,
    OrbitVerdict,
    Payload,
    Phase,
    RocketParams,
    SimResult,
    Stage,
    TelemetryFrame,
    constants,
)


# --------------------------------------------------------------------------
# Pomocnicze fabryki - poprawny stopien i rakieta do modyfikacji w testach.
# --------------------------------------------------------------------------
def make_stage(**overrides) -> Stage:
    defaults = dict(
        name="S1",
        dry_mass=2_000.0,
        thrust=800_000.0,
        isp=280.0,
        burn_time=120.0,
        drag_coefficient=0.3,
        reference_area=1.5,
    )
    defaults.update(overrides)
    return Stage(**defaults)


def make_rocket(**overrides) -> RocketParams:
    defaults = dict(
        stages=[make_stage()],
        payload=Payload(mass=150.0),
    )
    defaults.update(overrides)
    return RocketParams(**defaults)


# --------------------------------------------------------------------------
# Pola pochodne Stage - poprawnosc wzorow (SMAD Eq. 17-4).
# --------------------------------------------------------------------------
class TestStageDerived:
    def test_mass_flow_matches_thrust_equation(self):
        s = make_stage(thrust=800_000.0, isp=280.0)
        expected = 800_000.0 / (280.0 * constants.G0)
        assert math.isclose(s.mass_flow, expected, rel_tol=1e-12)

    def test_thrust_equation_is_invertible(self):
        # F = mass_flow * isp * g0 powinno wrocic do thrust
        s = make_stage()
        recovered = s.mass_flow * s.isp * constants.G0
        assert math.isclose(recovered, s.thrust, rel_tol=1e-9)

    def test_propellant_mass(self):
        s = make_stage(thrust=800_000.0, isp=280.0, burn_time=120.0)
        assert math.isclose(s.propellant_mass, s.mass_flow * 120.0, rel_tol=1e-12)

    def test_total_impulse(self):
        s = make_stage(thrust=800_000.0, burn_time=120.0)
        assert math.isclose(s.total_impulse, 800_000.0 * 120.0, rel_tol=1e-12)

    def test_wet_mass_and_fraction(self):
        s = make_stage(dry_mass=2_000.0)
        assert math.isclose(s.wet_mass, s.dry_mass + s.propellant_mass, rel_tol=1e-12)
        assert math.isclose(s.mass_fraction, s.propellant_mass / s.wet_mass, rel_tol=1e-12)
        assert 0.0 < s.mass_fraction < 1.0


# --------------------------------------------------------------------------
# Walidacja granic - to, co odrozni "dzialajacy prototyp" od bzdury.
# --------------------------------------------------------------------------
class TestStageValidation:
    def test_isp_above_chemical_limit_rejected(self):
        with pytest.raises(ValidationError):
            make_stage(isp=500.0)  # > 455, naped elektryczny - niedozwolony

    def test_isp_at_limit_accepted(self):
        s = make_stage(isp=constants.ISP_MAX_CHEMICAL)
        assert s.isp == constants.ISP_MAX_CHEMICAL

    def test_isp_nonpositive_rejected(self):
        with pytest.raises(ValidationError):
            make_stage(isp=0.0)

    def test_negative_dry_mass_rejected(self):
        with pytest.raises(ValidationError):
            make_stage(dry_mass=-1.0)

    def test_zero_thrust_rejected(self):
        with pytest.raises(ValidationError):
            make_stage(thrust=0.0)

    def test_unknown_field_rejected(self):
        # extra="forbid" - nieznane pole to blad (ochrona przed rozjazdem instancji)
        with pytest.raises(ValidationError):
            make_stage(turbopump_rpm=12000)


# --------------------------------------------------------------------------
# RocketParams - liczba stopni, masa startowa.
# --------------------------------------------------------------------------
class TestRocketParams:
    def test_empty_stages_rejected(self):
        with pytest.raises(ValidationError):
            make_rocket(stages=[])

    def test_too_many_stages_rejected(self):
        with pytest.raises(ValidationError):
            make_rocket(stages=[make_stage(name=f"S{i}") for i in range(5)])

    def test_four_stages_accepted(self):
        r = make_rocket(stages=[make_stage(name=f"S{i}") for i in range(4)])
        assert len(r.stages) == 4

    def test_liftoff_mass_sums_wet_masses_plus_payload(self):
        s1 = make_stage(name="S1", dry_mass=2_000.0)
        s2 = make_stage(name="S2", dry_mass=500.0, thrust=100_000.0, isp=340.0, burn_time=200.0)
        r = make_rocket(stages=[s1, s2], payload=Payload(mass=150.0))
        expected = s1.wet_mass + s2.wet_mass + 150.0
        assert math.isclose(r.liftoff_mass, expected, rel_tol=1e-12)

    def test_launch_angle_bounds(self):
        make_rocket(launch_angle_deg=90.0)
        make_rocket(launch_angle_deg=0.0)
        with pytest.raises(ValidationError):
            make_rocket(launch_angle_deg=91.0)
        with pytest.raises(ValidationError):
            make_rocket(launch_angle_deg=-1.0)


# --------------------------------------------------------------------------
# Niemutowalnosc - frozen chroni przed mutacja w petli Monte Carlo.
# --------------------------------------------------------------------------
class TestImmutability:
    def test_stage_is_frozen(self):
        s = make_stage()
        with pytest.raises(ValidationError):
            s.thrust = 999.0  # type: ignore[misc]

    def test_rocket_is_frozen(self):
        r = make_rocket()
        with pytest.raises(ValidationError):
            r.launch_angle_deg = 45.0  # type: ignore[misc]


# --------------------------------------------------------------------------
# Wyjscie - struktury telemetrii/werdyktu daja sie zbudowac i serializowac.
# --------------------------------------------------------------------------
class TestOutputModels:
    def test_telemetry_frame_roundtrip(self):
        f = TelemetryFrame(
            t=0.0, x=constants.R_EARTH, y=0.0, vx=0.0, vy=0.0, mass=43_000.0,
            altitude=0.0, speed=0.0, dynamic_pressure=0.0, acceleration=0.0,
            phase=Phase.ASCENT, active_stage=0,
        )
        dumped = f.model_dump()
        restored = TelemetryFrame(**dumped)
        assert restored.phase is Phase.ASCENT
        assert restored.t == 0.0

    def test_orbit_verdict_with_elements(self):
        el = OrbitalElements(
            semi_major_axis=constants.R_EARTH + 400_000.0,
            eccentricity=0.01,
            periapsis_altitude=390_000.0,
            apoapsis_altitude=410_000.0,
            specific_energy=-3.0e7,
            period=5_500.0,
        )
        v = OrbitVerdict(reached_orbit=True, reason="perygeum > 200 km, e < 0.25", elements=el)
        assert v.reached_orbit
        assert v.elements is not None
        assert v.elements.eccentricity < constants.MAX_ECCENTRICITY_LEO

    def test_sim_result_defaults_empty_telemetry(self):
        v = OrbitVerdict(reached_orbit=False, reason="brak orbity")
        res = SimResult(
            verdict=v, events=[], final_phase=Phase.FAILED,
            max_altitude=80_000.0, max_dynamic_pressure=35_000.0, flight_time=120.0,
        )
        assert res.telemetry == []  # default_factory=list
        assert res.final_phase is Phase.FAILED


# --------------------------------------------------------------------------
# Stale - sanity, ze wartosci SMAD sa w rozsadnych zakresach.
# --------------------------------------------------------------------------
class TestConstants:
    def test_earth_constants_sane(self):
        assert math.isclose(constants.MU_EARTH, 3.986e14, rel_tol=1e-3)
        assert math.isclose(constants.R_EARTH, 6.378e6, rel_tol=1e-3)
        assert math.isclose(constants.G0, 9.80665, rel_tol=1e-9)

    def test_circular_orbit_velocity_leo_sane(self):
        # v_circ = sqrt(mu/r) na 400 km powinno byc ~7.67 km/s
        r = constants.R_EARTH + 400_000.0
        v = math.sqrt(constants.MU_EARTH / r)
        assert 7_600.0 < v < 7_700.0
