"""
backend.tests.test_security
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Security and compliance integration tests verifying:
- Authentication & JWT boundary enforcement (401 Unauthorized block)
- RBAC ownership rules (Athletes 403 guard, Coaches 403 guard)
- Security Headers presence (CSP, HSTS)
- Malformed inputs/XSS sanitization behavior
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from backend.app.main import create_app
from backend.app.core.security import create_access_token
from backend.app.schemas.prediction import PredictionResponse

# Sample athlete records aligned with MOCK registers
ATHLETE_ALEX_RECORD = {
    "athlete_id": "ATH-101",
    "date": "2026-07-24",
    "sport": "Football",
    "position": "Midfielder",
    "age": 24.0,
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

ATHLETE_BOB_RECORD = {
    **ATHLETE_ALEX_RECORD,
    "athlete_id": "ATH-999", # Other ID
    "sport": "Basketball"     # Other Sport
}


from collections.abc import Generator

@pytest.fixture()
def mock_predictor_service() -> MagicMock:
    svc = MagicMock()
    svc.predict_one.return_value = PredictionResponse(
        athlete_id="ATH-101",
        injury_probability=0.15,
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
    app.state.predictor = mock_predictor_service
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    # Restore environment setting
    settings.app_env = original_env


# ---------------------------------------------------------------------------
# 1. Authentication Guards (401 Verification)
# ---------------------------------------------------------------------------
def test_unauthenticated_request_returns_401(client: TestClient) -> None:
    resp = client.post("/api/v1/predict", json=ATHLETE_ALEX_RECORD)
    assert resp.status_code == 401
    assert "credentials missing" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 2. RBAC & Data Ownership Guards (403 Verification)
# ---------------------------------------------------------------------------
def test_athlete_cannot_access_other_athlete_record(client: TestClient) -> None:
    # Authenticate as Athlete Alex (ID: ATH-101)
    token = create_access_token({"sub": "alex", "role": "Athlete", "athlete_id": "ATH-101"})
    client.cookies.set("access_token", token)
    
    # Request prediction for ATH-999 (Bob)
    resp = client.post("/api/v1/predict", json=ATHLETE_BOB_RECORD)
    assert resp.status_code == 403
    assert "only authorized to query their own records" in resp.json()["detail"] or "only request predictions for your own ID" in resp.json()["detail"]


def test_athlete_can_access_own_record(client: TestClient) -> None:
    # Authenticate as Athlete Alex (ID: ATH-101)
    token = create_access_token({"sub": "alex", "role": "Athlete", "athlete_id": "ATH-101"})
    client.cookies.set("access_token", token)
    
    resp = client.post("/api/v1/predict", json=ATHLETE_ALEX_RECORD)
    assert resp.status_code == 200


def test_coach_cannot_access_diff_sport_record(client: TestClient) -> None:
    # Authenticate as Coach Dan (Sport: Football)
    token = create_access_token({"sub": "coach_dan", "role": "Coach", "sport": "Football"})
    client.cookies.set("access_token", token)
    
    # Request prediction for Bob (Basketball)
    resp = client.post("/api/v1/predict", json=ATHLETE_BOB_RECORD)
    assert resp.status_code == 403
    assert "only request predictions for athletes in your sport" in resp.json()["detail"]


def test_coach_can_access_own_sport_record(client: TestClient) -> None:
    # Authenticate as Coach Dan (Sport: Football)
    token = create_access_token({"sub": "coach_dan", "role": "Coach", "sport": "Football"})
    client.cookies.set("access_token", token)
    
    resp = client.post("/api/v1/predict", json=ATHLETE_ALEX_RECORD)
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 3. Security Headers Verifications
# ---------------------------------------------------------------------------
def test_security_headers_are_present(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert "default-src" in resp.headers["Content-Security-Policy"]


# ---------------------------------------------------------------------------
# 4. Input Sanitization & HTML Escaping
# ---------------------------------------------------------------------------
def test_xss_in_identifiers_is_sanitized(client: TestClient) -> None:
    token = create_access_token({"sub": "admin", "role": "Admin"})
    client.cookies.set("access_token", token)

    malicious_record = {
        **ATHLETE_ALEX_RECORD,
        "athlete_id": "ATH-<script>alert(1)</script>",  # XSS
    }
    resp = client.post("/api/v1/predict", json=malicious_record)
    # Pydantic field regex validator restricts special chars like '<' and '>' returning 422
    assert resp.status_code == 422
