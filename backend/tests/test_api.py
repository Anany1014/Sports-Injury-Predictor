"""
API integration tests for /health and /api/v1/predict endpoints.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from backend.app.main import create_app
from backend.app.schemas.prediction import PredictionResponse


SAMPLE_ATHLETE = {
    "athlete_id": "ATH-TEST-001",
    "date": "2026-07-24",
    "sport": "Football",
    "position": "Midfielder",
    "age": 24,
    "weight_kg": 75.5,
    "height_cm": 178.0,
    "weekly_volume_hrs": 12.5,
    "weekly_intensity_score": 7.2,
    "sleep_hours": 7.5,
    "hrv_ms": 65.0,
    "soreness_score": 3.0,
    "rest_days": 1,
    "prior_injuries": 2,
    "days_since_last_injury": 90.0,
}


from collections.abc import Generator
from backend.app.core.security import create_access_token

@pytest.fixture()
def mock_predictor_service() -> MagicMock:
    svc = MagicMock()
    svc.predict_one.return_value = PredictionResponse(
        athlete_id="ATH-TEST-001",
        injury_probability=0.23,
        injury_risk_label="LOW",
        model_version="1.0.0",
    )
    return svc


@pytest.fixture()
def client(mock_predictor_service: MagicMock) -> Generator[TestClient, None, None]:
    # Set app_env to testing to bypass rate limiter
    from backend.app.core.config import settings
    original_env = settings.app_env
    settings.app_env = "testing"

    app = create_app()

    # Bypass the real lifespan (no model on disk in CI)
    app.state.predictor = mock_predictor_service

    with TestClient(app, raise_server_exceptions=True) as c:
        # Bake a valid JWT and inject into client cookie
        token = create_access_token({"sub": "admin", "role": "Admin"})
        c.cookies.set("access_token", token)
        yield c

    # Restore environment setting
    settings.app_env = original_env


def test_health_endpoint(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_predict_single_returns_200(client: TestClient) -> None:
    resp = client.post("/api/v1/predict", json=SAMPLE_ATHLETE)
    assert resp.status_code == 200
    body = resp.json()
    assert body["athlete_id"] == "ATH-TEST-001"
    assert 0.0 <= body["injury_probability"] <= 1.0
    assert body["injury_risk_label"] in {"LOW", "MEDIUM", "HIGH"}


def test_predict_single_invalid_age_returns_422(client: TestClient) -> None:
    bad = {**SAMPLE_ATHLETE, "age": 200}  # out of range
    resp = client.post("/api/v1/predict", json=bad)
    assert resp.status_code == 422
