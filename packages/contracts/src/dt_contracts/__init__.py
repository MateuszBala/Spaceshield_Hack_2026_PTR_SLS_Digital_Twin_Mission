"""dt_contracts - wspoldzielone schematy danych (zrodlo prawdy).

READ-ONLY dla wiekszosci instancji. Zmiana kontraktu = zmiana styku WSZYSTKICH
pakietow, wiec sie ja ZGLASZA, nie wprowadza samodzielnie.

Wszystkie wielkosci w SI, uklad inercjalny kartezjanski wokol srodka Ziemi,
kanoniczny wektor stanu lotu: [x, y, vx, vy, m].
"""

from __future__ import annotations

from . import constants
from ._base import DTModel, FrozenModel
from .api_messages import (
    OptimizationObjective,
    OptimizationRequest,
    SimRequest,
)
from .rocket import Payload, RocketParams, Stage
from .telemetry import (
    EventKind,
    MissionEvent,
    OrbitalElements,
    OrbitVerdict,
    Phase,
    SimResult,
    TelemetryFrame,
)

__all__ = [
    # modul stalych fizycznych i progow
    "constants",
    # baza
    "DTModel",
    "FrozenModel",
    # wejscie
    "Stage",
    "Payload",
    "RocketParams",
    # wyjscie
    "Phase",
    "EventKind",
    "TelemetryFrame",
    "MissionEvent",
    "OrbitalElements",
    "OrbitVerdict",
    "SimResult",
    # api / ai
    "SimRequest",
    "OptimizationObjective",
    "OptimizationRequest",
]

# Wersja kontraktu - bump przy KAZDEJ zmianie ksztaltu schematow.
__contract_version__ = "0.1.0"
