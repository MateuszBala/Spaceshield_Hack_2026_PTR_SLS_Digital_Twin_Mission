"""Gotowe presetty parametrow rakiety - punkty startowe symulacji i testow."""

from __future__ import annotations

from dt_contracts import Payload, RocketParams, Stage


def golden_preset() -> RocketParams:
    """Trojstopniowa rakieta referencyjna gwarantujaca osiagniecie LEO.

    Budzet delta-v efektywny ≈ 12 096 m/s (zapas ~2 700 m/s nad wymaganym
    ~9 400 m/s). Wartosci z GOLDEN_PRESET.md (zweryfikowane arytmetycznie).
    TWR startowy S1 ≈ 2,02 (powyzej progu 1,2).
    """
    return RocketParams(
        stages=[
            Stage(
                name="S1-core",
                dry_mass=3_000.0,
                thrust=780_000.0,
                isp=282.0,
                burn_time=105.0,
                drag_coefficient=0.30,
                reference_area=3.0,
            ),
            Stage(
                name="S2",
                dry_mass=700.0,
                thrust=145_000.0,
                isp=345.0,
                burn_time=120.0,
                drag_coefficient=0.25,
                reference_area=1.2,
            ),
            Stage(
                name="S3-upper",
                dry_mass=120.0,
                thrust=22_000.0,
                isp=448.0,
                burn_time=115.0,
                drag_coefficient=0.22,
                reference_area=0.8,
            ),
        ],
        payload=Payload(mass=150.0, name="sat-150"),
        launch_angle_deg=90.0,
    )
