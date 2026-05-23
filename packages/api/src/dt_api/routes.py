"""Endpointy HTTP: symulacja, capabilities, optymalizacja (graceful)."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import dt_contracts
from dt_contracts import (
    EventKind,
    MissionEvent,
    OptimizationRequest,
    OrbitVerdict,
    Phase,
    SimRequest,
    SimResult,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Wykrywanie dostępności pakietów opcjonalnych przy starcie modułu.
# ---------------------------------------------------------------------------

try:
    from dt_physics import simulate as _physics_simulate  # type: ignore[import-not-found]

    _engine_available = True
    log.info("dt_physics.simulate dostępne")
except (ImportError, AttributeError):
    _engine_available = False
    _physics_simulate = None
    log.warning("dt_physics.simulate niedostępne — endpoint /simulate zwraca stub")

try:
    from dt_ai import optimize as _ai_optimize  # type: ignore[import-not-found]

    _ai_available = True
    log.info("dt_ai.optimize dostępne")
except (ImportError, AttributeError):
    _ai_available = False
    _ai_optimize = None
    log.info("dt_ai.optimize niedostępne — /optimize zwraca 503")

# ---------------------------------------------------------------------------
# Stub SimResult — zwracany, gdy silnik fizyczny nie jest jeszcze gotowy.
# Wszystkie pola muszą być zgodne z kontraktem (FrozenModel).
# ---------------------------------------------------------------------------

_STUB_SIM_RESULT = SimResult(
    verdict=OrbitVerdict(
        reached_orbit=False,
        reason="[STUB] Silnik fizyczny (dt_physics) nie jest jeszcze zaimplementowany.",
        elements=None,
    ),
    events=[
        MissionEvent(
            kind=EventKind.LIFTOFF,
            t=0.0,
            altitude=0.0,
            speed=0.0,
            note="stub",
        )
    ],
    final_phase=Phase.FAILED,
    max_altitude=0.0,
    max_dynamic_pressure=0.0,
    flight_time=0.0,
    telemetry=[],
)

# ---------------------------------------------------------------------------
# Schemat odpowiedzi capabilities (API-specyficzne metadane, nie w dt_contracts).
# ---------------------------------------------------------------------------


class CapabilitiesResponse(BaseModel):
    """Informacja o dostępnych funkcjach systemu."""

    contract_version: Annotated[str, Field(description="Wersja kontraktu dt_contracts")]
    engine_available: Annotated[bool, Field(description="Silnik fizyczny dostępny")]
    ai_available: Annotated[bool, Field(description="Pakiet optymalizacji AI dostępny")]
    api_version: Annotated[str, Field(description="Wersja API")]


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter()


@router.get("/capabilities", response_model=CapabilitiesResponse, tags=["meta"])
async def capabilities() -> CapabilitiesResponse:
    """Zwraca dostępne funkcje systemu.

    Frontend używa `ai_available` do chowania/pokazywania UI optymalizacji.
    """
    return CapabilitiesResponse(
        contract_version=dt_contracts.__contract_version__,
        engine_available=_engine_available,
        ai_available=_ai_available,
        api_version="0.1.0",
    )


@router.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Prosty health-check (liveness probe)."""
    return {"status": "ok"}


@router.post("/simulate", response_model=SimResult, tags=["simulation"])
async def simulate(request: SimRequest) -> SimResult:
    """Uruchamia symulację lotu rakiety.

    Przyjmuje `SimRequest` (RocketParams + opcje), zwraca `SimResult`.
    Walidacja wejścia jest automatyczna (Pydantic / dt_contracts).
    """
    if not _engine_available:
        log.debug("Silnik niedostępny — zwracam stub SimResult")
        return _STUB_SIM_RESULT

    try:
        result: SimResult = _physics_simulate(request.rocket)
    except Exception as exc:
        log.exception("Błąd silnika fizycznego")
        raise HTTPException(status_code=500, detail=f"Błąd silnika: {exc}") from exc

    return result


@router.post("/optimize", tags=["optimization"])
async def optimize(request: OptimizationRequest) -> Any:
    """Optymalizacja masy startowej rakiety (wymaga dt_ai).

    Gdy pakiet AI jest niedostępny, zwraca status 503 z opisem.
    Endpoint ZAWSZE istnieje — frontend steruje widocznością UI przez /capabilities.
    """
    if not _ai_available:
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Pakiet optymalizacji (dt_ai) nie jest dostępny.",
                "ai_available": False,
            },
        )

    try:
        result = _ai_optimize(request)  # type: ignore[misc]
    except Exception as exc:
        log.exception("Błąd pakietu AI")
        raise HTTPException(status_code=500, detail=f"Błąd AI: {exc}") from exc

    return result
