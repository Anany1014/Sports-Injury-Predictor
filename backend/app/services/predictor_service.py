"""
backend.app.services.predictor_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Business-logic layer: wraps the ML InjuryPredictor for the API.
"""
from __future__ import annotations

import pandas as pd

from backend.app.core.config import settings
from backend.app.schemas.prediction import AthleteRecord, PredictionResponse
from model.src.models.predict import InjuryPredictor

MODEL_VERSION = "1.0.0"


class PredictorService:
    """Singleton service that holds the loaded ML model."""

    def __init__(self) -> None:
        self._predictor = InjuryPredictor(artifacts_dir=settings.artifacts_dir)

    def load(self) -> None:
        self._predictor.load()

    def _get_top_factors(self, record_dict: dict) -> list[str]:
        factors = []
        # Intensity factor
        intensity = record_dict.get("weekly_intensity_score", 0)
        if intensity >= 7.5:
            factors.append(f"High Weekly Intensity ({intensity:.1f}/10)")
        elif intensity >= 5.0:
            factors.append(f"Moderate Training Exertion ({intensity:.1f}/10)")

        # Volume factor
        volume = record_dict.get("weekly_volume_hrs", 0)
        if volume >= 14.0:
            factors.append(f"Elevated Weekly Volume ({volume:.1f} hrs)")

        # Recovery factors
        sleep = record_dict.get("sleep_hours", 8)
        if sleep < 7.0:
            factors.append(f"Sleep Deficit ({sleep:.1f} hrs/night)")

        soreness = record_dict.get("soreness_score", 0)
        if soreness >= 5.0:
            factors.append(f"High Muscle Soreness ({soreness:.1f}/10)")

        rest = record_dict.get("rest_days", 2)
        if rest <= 1:
            factors.append(f"Insufficient Rest ({rest} rest days)")

        # Injury history
        priors = record_dict.get("prior_injuries", 0)
        days_since = record_dict.get("days_since_last_injury", 365)
        if priors > 0 and days_since < 90:
            factors.append(f"Recent Injury History ({priors} prior, {int(days_since)}d ago)")

        if not factors:
            factors = ["Workload within safe threshold", "Normal recovery baseline"]

        return factors[:3]

    def predict_one(self, record: AthleteRecord) -> PredictionResponse:
        record_dict = record.model_dump()
        result = self._predictor.predict_single(record_dict)
        factors = self._get_top_factors(record_dict)

        return PredictionResponse(
            athlete_id=record.athlete_id,
            injury_probability=result["injury_probability"],
            injury_risk_label=result["injury_risk_label"],
            top_contributing_factors=factors,
            model_version=MODEL_VERSION,
        )

    def predict_batch(self, records: list[AthleteRecord]) -> list[PredictionResponse]:
        df = pd.DataFrame([r.model_dump() for r in records])
        result_df = self._predictor.predict(df)
        responses = []
        for i, record in enumerate(records):
            record_dict = record.model_dump()
            factors = self._get_top_factors(record_dict)
            responses.append(
                PredictionResponse(
                    athlete_id=record.athlete_id,
                    injury_probability=float(result_df["injury_probability"].iloc[i]),
                    injury_risk_label=str(result_df["injury_risk_label"].iloc[i]),
                    top_contributing_factors=factors,
                    model_version=MODEL_VERSION,
                )
            )
        return responses
