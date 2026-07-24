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

    def predict_one(self, record: AthleteRecord) -> PredictionResponse:
        result = self._predictor.predict_single(record.model_dump())
        return PredictionResponse(
            athlete_id=record.athlete_id,
            injury_probability=result["injury_probability"],
            injury_risk_label=result["injury_risk_label"],
            model_version=MODEL_VERSION,
        )

    def predict_batch(self, records: list[AthleteRecord]) -> list[PredictionResponse]:
        df = pd.DataFrame([r.model_dump() for r in records])
        result_df = self._predictor.predict(df)
        responses = []
        for i, record in enumerate(records):
            responses.append(
                PredictionResponse(
                    athlete_id=record.athlete_id,
                    injury_probability=float(result_df["injury_probability"].iloc[i]),
                    injury_risk_label=str(result_df["injury_risk_label"].iloc[i]),
                    model_version=MODEL_VERSION,
                )
            )
        return responses
