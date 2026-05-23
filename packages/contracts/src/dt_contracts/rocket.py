"""Wejscie symulacji: parametry rakiety - "pokretla" Digital Twina.

Model napedu (decyzja potwierdzona, zgodna ze SMAD rozdz. 17):
PARAMETRY WEJSCIOWE stopnia to ciag (thrust), impuls wlasciwy (isp) i czas
pracy (burn_time). Z nich WYNIKAJA (computed_field):
  mass_flow      = thrust / (isp * g0)              [SMAD Eq. 17-4]
  propellant_mass = mass_flow * burn_time
  total_impulse  = thrust * burn_time
Dzieki temu dane sa zawsze spojne fizycznie - nie da sie podac sprzecznej
trojki (thrust, isp, mass_flow), bo mass_flow nie jest parametrem.

Liczba stopni jest PARAMETRYCZNA (lista 1-4).
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, computed_field, field_validator

from ._base import Area, Cd, Duration, FrozenModel, Isp, Mass, Thrust
from .constants import G0, ISP_MAX_CHEMICAL, ISP_MIN


class Stage(FrozenModel):
    """Pojedynczy stopien rakiety.

    Wejscie: dry_mass, thrust, isp, burn_time, aerodynamika.
    Pochodne (liczone): mass_flow, propellant_mass, total_impulse, ignition_mass.
    """

    name: Annotated[str, Field(min_length=1, description="Etykieta stopnia")]
    dry_mass: Annotated[Mass, Field(description="Masa konstrukcji (sucha) [kg]")]
    thrust: Thrust
    isp: Isp
    burn_time: Annotated[Duration, Field(description="Czas pracy silnika [s]")]
    # Aerodynamika - uproszczona: jeden Cd i pole przekroju na stopien.
    drag_coefficient: Cd
    reference_area: Area

    @field_validator("isp")
    @classmethod
    def _check_isp_range(cls, v: float) -> float:
        """Twardy limit Isp dla napedu chemicznego wynoszacego z powierzchni."""
        if not (ISP_MIN <= v <= ISP_MAX_CHEMICAL):
            raise ValueError(
                f"isp={v} s poza zakresem chemicznym [{ISP_MIN}, {ISP_MAX_CHEMICAL}] s. "
                "Naped elektryczny (Isp>450) nie nadaje sie do wynoszenia z powierzchni."
            )
        return v

    @computed_field  # type: ignore[prop-decorator]
    @property
    def mass_flow(self) -> float:
        """Strumien masy paliwa [kg/s] = thrust/(isp*g0)  (SMAD Eq. 17-4)."""
        return self.thrust / (self.isp * G0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def propellant_mass(self) -> float:
        """Masa paliwa [kg] = mass_flow * burn_time."""
        return self.mass_flow * self.burn_time

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_impulse(self) -> float:
        """Impuls calkowity [N*s] = thrust * burn_time (do porownan z tab. SMAD)."""
        return self.thrust * self.burn_time

    @computed_field  # type: ignore[prop-decorator]
    @property
    def wet_mass(self) -> float:
        """Masa stopnia z paliwem [kg] = dry_mass + propellant_mass."""
        return self.dry_mass + self.propellant_mass

    @computed_field  # type: ignore[prop-decorator]
    @property
    def mass_fraction(self) -> float:
        """Frakcja masowa = propellant / wet  (SMAD: solid ~0.91-0.94, liquid ~0.85-0.93)."""
        return self.propellant_mass / self.wet_mass


class Payload(FrozenModel):
    """Ladunek uzyteczny (satelita) wynoszony na orbite."""

    mass: Annotated[Mass, Field(description="Masa ladunku [kg]")]
    name: Annotated[str, Field(default="payload", min_length=1)]


class RocketParams(FrozenModel):
    """Pelny zestaw parametrow rakiety - wejscie pojedynczej symulacji.

    Niemutowalny: ten sam obiekt moze krazyc po wielu przebiegach Monte Carlo
    bez ryzyka, ze ktorys krok go zmodyfikuje.
    """

    stages: Annotated[
        list[Stage],
        Field(min_length=1, max_length=4, description="Stopnie od dolnego do gornego"),
    ]
    payload: Payload
    launch_angle_deg: Annotated[
        float,
        Field(default=90.0, ge=0.0, le=90.0, description="Kat startu od poziomu [deg]"),
    ]
    # TODO: parametry gravity turn (kiedy zaczac, jak szybko klasc rakiete) - przy fazach lotu.

    @computed_field  # type: ignore[prop-decorator]
    @property
    def liftoff_mass(self) -> float:
        """Masa startowa [kg] = suma mas mokrych stopni + ladunek.

        To wielkosc minimalizowana w optymalizacji (cel zadania).
        """
        return sum(s.wet_mass for s in self.stages) + self.payload.mass
