"""Koperty zadan/odpowiedzi dla warstwy API (HTTP).

physics-engine operuje na RocketParams -> SimResult bezposrednio. Te modele to
cienka koperta dla styku HTTP miedzy frontendem a api oraz dla zlecen AI.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from ._base import DTModel
from .rocket import RocketParams


class SimRequest(DTModel):
    """Zadanie pojedynczej symulacji (frontend -> api)."""

    rocket: RocketParams
    include_telemetry: Annotated[
        bool,
        Field(default=True, description="False -> SimResult.telemetry pusta (lzejsze dla MC)"),
    ]
    # TODO: parametry numeryczne (krok, tolerancje, max czas) - gdy domkniemy fazy.
    max_flight_time: Annotated[
        float,
        Field(default=3600.0, gt=0.0, description="Twardy limit czasu symulacji [s]"),
    ]


class OptimizationObjective(DTModel):
    """Cel optymalizacji dla backendu AI.

    Sedno zadania: minimalizacja masy startowej (RocketParams.liftoff_mass)
    przy twardym warunku osiagniecia orbity. Wiezy parametrow (zakresy Isp,
    frakcje masowe) sa egzekwowane przez sam kontrakt RocketParams/Stage oraz
    progi w constants.py.
    """

    minimize_liftoff_mass: Annotated[bool, Field(default=True)]
    require_orbit: Annotated[bool, Field(default=True, description="Twardy warunek: orbita osiagnieta")]
    max_stages: Annotated[int, Field(default=4, ge=1, le=4, description="Gorny limit liczby stopni")]


class OptimizationRequest(DTModel):
    """Zlecenie optymalizacji/Monte Carlo (uzywane wewnetrznie przez ai)."""

    base_rocket: RocketParams
    objective: OptimizationObjective
    n_samples: Annotated[int, Field(default=1000, ge=1, description="Liczba przebiegow MC")]
