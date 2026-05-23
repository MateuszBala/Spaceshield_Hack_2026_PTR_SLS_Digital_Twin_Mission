"""Wspolna baza dla wszystkich schematow kontraktu.

Kazdy schemat dziedziczy z `DTModel`, ktory narzuca jednolita polityke:
- extra="forbid"  -> nieznane pola sa odrzucane (contract-first, ochrona przed
                     rozjazdem miedzy instancjami pracujacymi w osobnych worktree)
- validate_default -> domyslne wartosci tez sa walidowane
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class DTModel(BaseModel):
    """Baza: zakazuje nieznanych pol, waliduje domyslne."""

    model_config = ConfigDict(extra="forbid", validate_default=True)


class FrozenModel(DTModel):
    """Niemutowalna odmiana - dla wejscia (RocketParams) i wynikow (SimResult).

    Po utworzeniu instancji jej pola sa zamrozone; chroni przed przypadkowa
    mutacja, gdy ten sam obiekt krazy po tysiacach przebiegow Monte Carlo.
    """

    model_config = ConfigDict(extra="forbid", validate_default=True, frozen=True)


# ---------------------------------------------------------------------------
# Wspolne aliasy typow z metadanymi.
# Uzywamy Annotated[..., Field(...)] zamiast `x: t = Field(...)` (czytelniej dla
# type-checkerow, jednoznacznie odroznia pole wymagane od majacego default).
# Granice fizyczne (np. Isp) egzekwowane sa w rocket.py wzgledem dt_contracts.constants.
# ---------------------------------------------------------------------------

# Wielkosci fizyczne w SI. Tu tylko gt/ge tam, gdzie bezdyskusyjne;
# twarde granice dziedzinowe (np. Isp <= 455 s) zyja przy uzyciu (rocket.py).
Mass = Annotated[float, Field(gt=0.0, description="Masa [kg]")]
Length = Annotated[float, Field(gt=0.0, description="Dlugosc/wymiar [m]")]
Area = Annotated[float, Field(gt=0.0, description="Pole przekroju [m^2]")]
Thrust = Annotated[float, Field(gt=0.0, description="Ciag [N]")]
Isp = Annotated[float, Field(gt=0.0, description="Impuls wlasciwy [s]")]
MassFlow = Annotated[float, Field(gt=0.0, description="Strumien masy paliwa [kg/s]")]
Cd = Annotated[float, Field(ge=0.0, description="Wspolczynnik oporu [-]")]
Duration = Annotated[float, Field(gt=0.0, description="Czas [s]")]
Altitude = Annotated[float, Field(description="Wysokosc nad poziomem morza [m]")]
