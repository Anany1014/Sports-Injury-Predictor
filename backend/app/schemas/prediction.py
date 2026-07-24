"""
backend.app.schemas.prediction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pydantic request and response schemas for the /predict endpoint.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class AthleteRecord(BaseModel):
    """A single athlete's biometric and training-load snapshot."""

    # Identity / demographics
    athlete_id: str = Field(..., example="ATH-001")
    date: str = Field(..., example="2026-07-24", description="ISO-8601 date string")
    sport: str = Field(..., example="Football")
    position: str = Field(..., example="Midfielder")
    age: float = Field(..., ge=15, le=50, example=24)
    weight_kg: float = Field(..., ge=40, le=150, example=75.5)
    height_cm: float = Field(..., ge=140, le=220, example=178.0)

    # Training load
    weekly_volume_hrs: float = Field(..., ge=0, le=40, example=12.5)
    weekly_intensity_score: float = Field(..., ge=0, le=10, example=7.2)

    # Recovery
    sleep_hours: float = Field(..., ge=0, le=12, example=7.5)
    hrv_ms: float = Field(..., ge=0, le=200, example=65.0)
    soreness_score: float = Field(..., ge=0, le=10, example=3.0)
    rest_days: int = Field(..., ge=0, le=7, example=1)

    # Injury history
    prior_injuries: int = Field(..., ge=0, example=2)
    days_since_last_injury: float = Field(..., ge=0, example=90.0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        from datetime import datetime
        datetime.strptime(v, "%Y-%m-%d")  # raises ValueError if malformed
        return v


class PredictionResponse(BaseModel):
    """Injury prediction result for a single athlete."""

    athlete_id: str
    injury_probability: float = Field(..., ge=0.0, le=1.0, description="Probability of injury (0–1)")
    injury_risk_label: str = Field(..., description="LOW | MEDIUM | HIGH")
    top_contributing_factors: list[str] = Field(default_factory=list, description="Top factors contributing to injury risk")
    model_version: str


class BatchPredictionRequest(BaseModel):
    athletes: list[AthleteRecord] = Field(..., min_length=1, max_length=100)


class BatchPredictionResponse(BaseModel):
    predictions: list[PredictionResponse]
    total: int
