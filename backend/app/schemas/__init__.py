"""backend.app.schemas package."""
from backend.app.schemas.prediction import (
    AthleteRecord,
    BatchPredictionRequest,
    BatchPredictionResponse,
    PredictionResponse,
)

__all__ = [
    "AthleteRecord",
    "BatchPredictionRequest",
    "BatchPredictionResponse",
    "PredictionResponse",
]
