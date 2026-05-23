"""Wyjscie symulacji: telemetria, elementy orbitalne, zdarzenia, werdykt.

To jest kontrakt produkowany przez physics-engine i konsumowany przez api,
ai oraz (posrednio, przez OpenAPI) frontend.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import Field

from ._base import DTModel, FrozenModel


class Phase(str, Enum):
    """Faza misji - odpowiada trzem rezimom numerycznym silnika."""

    ASCENT = "ascent"        # wznoszenie atmosferyczne (cial + grawitacja + opor)
    INSERTION = "insertion"  # wstawienie na orbite (opor znikomy)
    ORBIT = "orbit"          # lot orbitalny / werdykt
    FAILED = "failed"        # misja nieudana (spadek, brak orbity)


class EventKind(str, Enum):
    """Rodzaj zdarzenia w sekwencji misji."""

    LIFTOFF = "liftoff"
    MAX_Q = "max_q"                  # maksymalne cisnienie dynamiczne
    STAGE_BURNOUT = "stage_burnout"  # wypalenie paliwa stopnia
    STAGE_SEP = "stage_separation"   # separacja stopnia
    DRAG_NEGLIGIBLE = "drag_negligible"  # prog wylaczenia oporu (D/mg < eps)
    PAYLOAD_SEP = "payload_separation"
    ORBIT_INSERTION = "orbit_insertion"
    APOGEE = "apogee"
    IMPACT = "impact"                # uderzenie w Ziemie (porazka)


class TelemetryFrame(DTModel):
    """Pojedyncza probka stanu lotu w czasie.

    Odpowiada kanonicznemu wektorowi stanu [x, y, vx, vy, m] rozszerzonemu o
    wielkosci pochodne wygodne do wykresow i analizy. Wszystko w SI, uklad
    inercjalny kartezjanski wokol srodka Ziemi.
    """

    t: Annotated[float, Field(ge=0.0, description="Czas od startu [s]")]
    # Stan kanoniczny (inercjalny, srodek Ziemi w (0,0)):
    x: Annotated[float, Field(description="Pozycja X [m]")]
    y: Annotated[float, Field(description="Pozycja Y [m]")]
    vx: Annotated[float, Field(description="Predkosc X [m/s]")]
    vy: Annotated[float, Field(description="Predkosc Y [m/s]")]
    mass: Annotated[float, Field(gt=0.0, description="Masa chwilowa [kg]")]
    # Wielkosci pochodne (liczone, nie czesc stanu - wygodne dla frontu/AI):
    altitude: Annotated[float, Field(description="Wysokosc nad powierzchnia [m]")]
    speed: Annotated[float, Field(ge=0.0, description="Predkosc (modul) [m/s]")]
    dynamic_pressure: Annotated[float, Field(ge=0.0, description="Cisnienie dynamiczne Q [Pa]")]
    acceleration: Annotated[float, Field(ge=0.0, description="Przyspieszenie (modul) [m/s^2]")]
    phase: Phase
    active_stage: Annotated[int, Field(ge=0, description="Indeks aktywnego stopnia (0-based)")]


class MissionEvent(DTModel):
    """Dyskretne zdarzenie misji - wykryte jako zero funkcji zdarzenia w solverze."""

    kind: EventKind
    t: Annotated[float, Field(ge=0.0, description="Czas zdarzenia [s]")]
    altitude: Annotated[float, Field(description="Wysokosc w chwili zdarzenia [m]")]
    speed: Annotated[float, Field(ge=0.0, description="Predkosc w chwili zdarzenia [m/s]")]
    note: Annotated[str, Field(default="", description="Opcjonalny opis")]


class OrbitalElements(DTModel):
    """Elementy keplerowskie liczone z wektorow stanu w momencie wstawienia.

    To z nich (nie z chwilowej wysokosci) wynika werdykt o orbicie.
    """

    semi_major_axis: Annotated[float, Field(description="Polos wielka a [m]")]
    eccentricity: Annotated[float, Field(ge=0.0, description="Mimosrod e [-]")]
    periapsis_altitude: Annotated[float, Field(description="Wysokosc perygeum nad powierzchnia [m]")]
    apoapsis_altitude: Annotated[float, Field(description="Wysokosc apogeum nad powierzchnia [m]")]
    specific_energy: Annotated[float, Field(description="Energia wlasciwa eps [J/kg]")]
    period: Annotated[float | None, Field(default=None, description="Okres orbitalny [s] (None gdy niezwiazana)")]


class OrbitVerdict(DTModel):
    """Werdykt: czy misja osiagnela zadana orbite.

    Kryterium liczbowe (SMAD rozdz. 7.3 + wykres 7-8), egzekwowane w silniku:
      - orbita zwiazana: energia wlasciwa eps < 0,
      - perygeum > constants.MIN_PERIAPSIS_ALTITUDE (domyslnie 200 km),
      - mimosrod <= constants.MAX_ECCENTRICITY_LEO dla "stabilnej LEO".
    Tu tylko struktura werdyktu; progi zyja w constants.py.
    """

    reached_orbit: Annotated[bool, Field(description="Czy orbita zwiazana i stabilna")]
    reason: Annotated[str, Field(description="Uzasadnienie werdyktu w jezyku naturalnym")]
    elements: Annotated[OrbitalElements | None, Field(default=None)]


class SimResult(FrozenModel):
    """Pelny wynik pojedynczej symulacji - niemutowalny.

    Telemetria moze byc dluga; dla masowego Monte Carlo AI bedzie zwykle
    prosic o wynik BEZ pelnej telemetrii (patrz SimRequest.include_telemetry).
    """

    verdict: OrbitVerdict
    events: list[MissionEvent]
    final_phase: Phase
    max_altitude: Annotated[float, Field(description="Maksymalna osiagnieta wysokosc [m]")]
    max_dynamic_pressure: Annotated[float, Field(ge=0.0, description="Max-Q [Pa]")]
    flight_time: Annotated[float, Field(ge=0.0, description="Calkowity czas lotu [s]")]
    telemetry: Annotated[
        list[TelemetryFrame],
        Field(default_factory=list, description="Pusta, gdy include_telemetry=False"),
    ]
