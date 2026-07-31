"""
backend.app.schemas.prediction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pydantic request and response schemas for the /predict endpoint.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


import html
import re
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class AthleteRecord(BaseModel):
    """A single athlete's biometric and training-load snapshot."""

    # Identity / demographics
    athlete_id: str = Field(..., examples=["ATH-001"])
    date: str = Field(..., examples=["2026-07-24"], description="ISO-8601 date string")
    sport: str = Field(..., examples=["Football"])
    position: str = Field(..., examples=["Midfielder"])
    age: float = Field(..., ge=15, le=50, examples=[24.0])
    weight_kg: float = Field(..., ge=40, le=150, examples=[75.5])
    height_cm: float = Field(..., ge=140, le=220, examples=[178.0])

    # Training load
    weekly_volume_hrs: float = Field(..., ge=0, le=40, examples=[12.5])
    weekly_intensity_score: float = Field(..., ge=0, le=10, examples=[7.2])

    # Recovery
    sleep_hours: float = Field(..., ge=0, le=12, examples=[7.5])
    hrv_ms: float = Field(..., ge=0, le=200, examples=[65.0])
    soreness_score: float = Field(..., ge=0, le=10, examples=[3.0])
    rest_days: int = Field(..., ge=0, le=7, examples=[1])

    # Injury history
    prior_injuries: int = Field(..., ge=0, le=20, examples=[2])
    days_since_last_injury: float = Field(..., ge=0, le=10000, examples=[90.0])

    @field_validator("athlete_id")
    @classmethod
    def validate_athlete_id(cls, v: str) -> str:
        v = v.strip()
        # Strictly alphanumeric and dashes/underscores starting with ATH-
        if not re.match(r"^ATH-[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "athlete_id must start with ATH- and contain only letters, numbers, dashes or underscores"
            )
        return html.escape(v)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        v = v.strip()
        # Ensure ISO-8601 YYYY-MM-DD
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("date must match YYYY-MM-DD format Exactly")
        return html.escape(v)

    @field_validator("sport", "position")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        v = v.strip()
        # Prevent SQL injection/CSS escaping: permit only characters, numbers, spaces, dash and underscore
        if not re.match(r"^[a-zA-Z0-9\s_-]+$", v):
            raise ValueError(
                "text fields must only contain alphanumeric characters, spaces, dashes or underscores"
            )
        return html.escape(v)


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

