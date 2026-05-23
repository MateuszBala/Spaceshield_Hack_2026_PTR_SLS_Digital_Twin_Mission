"""Testy endpointów API — capabilities, simulate, optimize."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import dt_contracts
from dt_contracts import (
    OrbitalElements,
    OrbitVerdict,
    Phase,
    SimResult,
)


@pytest.fixture()
def client():
    from dt_api.app import app

    return TestClient(app)


# ---------------------------------------------------------------------------
# /capabilities
# ---------------------------------------------------------------------------


def test_capabilities_returns_200(client: TestClient) -> None:
    resp = client.get("/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert "ai_available" in data
    assert "engine_available" in data
    assert "contract_version" in data
    assert data["contract_version"] == dt_contracts.__contract_version__


def test_capabilities_ai_false_when_not_installed(client: TestClient) -> None:
    import dt_api.routes as routes_module

    with patch.object(routes_module, "_ai_available", False):
        resp = client.get("/capabilities")
    assert resp.status_code == 200
    assert resp.json()["ai_available"] is False


def test_capabilities_ai_true_when_installed(client: TestClient) -> None:
    import dt_api.routes as routes_module

    with patch.object(routes_module, "_ai_available", True):
        resp = client.get("/capabilities")
    assert resp.status_code == 200
    assert resp.json()["ai_available"] is True


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# /simulate
# ---------------------------------------------------------------------------

_VALID_PAYLOAD = {
    "rocket": {
        "stages": [
            {
                "name": "S1",
                "dry_mass": 5000.0,
                "thrust": 500_000.0,
                "isp": 280.0,
                "burn_time": 120.0,
                "drag_coefficient": 0.5,
                "reference_area": 10.0,
            }
        ],
        "payload": {"mass": 200.0, "name": "sat"},
        "launch_angle_deg": 90.0,
    },
    "include_telemetry": False,
    "max_flight_time": 600.0,
}

_FAKE_SIM_RESULT = SimResult(
    verdict=OrbitVerdict(
        reached_orbit=True,
        reason="test",
        elements=OrbitalElements(
            semi_major_axis=6_778_000.0,
            eccentricity=0.0,
            periapsis_altitude=400_000.0,
            apoapsis_altitude=400_000.0,
            specific_energy=-29_400.0,
            period=5560.0,
        ),
    ),
    events=[],
    final_phase=Phase.ORBIT,
    max_altitude=400_000.0,
    max_dynamic_pressure=50_000.0,
    flight_time=300.0,
    telemetry=[],
)


def test_simulate_returns_200_with_stub_engine(client: TestClient) -> None:
    """Gdy silnik niedostępny, endpoint zwraca stub SimResult (200)."""
    import dt_api.routes as routes_module

    with patch.object(routes_module, "_engine_available", False):
        resp = client.post("/simulate", json=_VALID_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert "verdict" in data
    assert "reached_orbit" in data["verdict"]


def test_simulate_delegates_to_engine(client: TestClient) -> None:
    """Gdy silnik dostępny, endpoint wołał simulate() i zwraca jego wynik."""
    import dt_api.routes as routes_module

    mock_engine = MagicMock(return_value=_FAKE_SIM_RESULT)
    with (
        patch.object(routes_module, "_engine_available", True),
        patch.object(routes_module, "_physics_simulate", mock_engine),
    ):
        resp = client.post("/simulate", json=_VALID_PAYLOAD)

    assert resp.status_code == 200
    assert resp.json()["verdict"]["reached_orbit"] is True
    mock_engine.assert_called_once()


def test_simulate_validation_error_on_bad_stages(client: TestClient) -> None:
    """Więcej niż 4 stopnie → błąd walidacji, nie 500."""
    bad = dict(_VALID_PAYLOAD)
    bad["rocket"] = dict(_VALID_PAYLOAD["rocket"])
    stage = _VALID_PAYLOAD["rocket"]["stages"][0]
    bad["rocket"]["stages"] = [stage] * 5  # kontrakt: max 4 stopnie
    resp = client.post("/simulate", json=bad)
    assert resp.status_code == 422


def test_simulate_validation_error_on_isp_out_of_range(client: TestClient) -> None:
    """Isp > 455 s → błąd walidacji (chemiczny próg z kontraktu)."""
    bad_stage = dict(_VALID_PAYLOAD["rocket"]["stages"][0])
    bad_stage["isp"] = 500.0
    bad = {**_VALID_PAYLOAD, "rocket": {**_VALID_PAYLOAD["rocket"], "stages": [bad_stage]}}
    resp = client.post("/simulate", json=bad)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# /optimize
# ---------------------------------------------------------------------------

_VALID_OPT_PAYLOAD = {
    "base_rocket": _VALID_PAYLOAD["rocket"],
    "objective": {
        "minimize_liftoff_mass": True,
        "require_orbit": True,
        "max_stages": 4,
    },
    "n_samples": 10,
}


def test_optimize_returns_503_when_ai_unavailable(client: TestClient) -> None:
    """Brak dt_ai → 503, nie 500."""
    import dt_api.routes as routes_module

    with patch.object(routes_module, "_ai_available", False):
        resp = client.post("/optimize", json=_VALID_OPT_PAYLOAD)
    assert resp.status_code == 503
    data = resp.json()
    assert data["ai_available"] is False


def test_optimize_delegates_to_ai_when_available(client: TestClient) -> None:
    """Gdy dt_ai dostępne, endpoint deleguje do _ai_optimize()."""
    import dt_api.routes as routes_module

    fake_optimize = MagicMock(return_value={"result": "ok"})
    with (
        patch.object(routes_module, "_ai_available", True),
        patch.object(routes_module, "_ai_optimize", fake_optimize),
    ):
        resp = client.post("/optimize", json=_VALID_OPT_PAYLOAD)

    assert resp.status_code == 200
    fake_optimize.assert_called_once()
