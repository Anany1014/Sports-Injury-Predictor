"""
backend.app.api.predict
~~~~~~~~~~~~~~~~~~~~~~~~
POST /api/v1/predict       — single prediction
POST /api/v1/predict/batch — batch predictions (up to 100 athletes)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from backend.app.schemas.prediction import (
    AthleteRecord,
    BatchPredictionRequest,
    BatchPredictionResponse,
    PredictionResponse,
)

router = APIRouter()


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict injury risk for a single athlete",
    status_code=status.HTTP_200_OK,
)
async def predict_single(record: AthleteRecord, request: Request) -> PredictionResponse:
    """
    Accept a single athlete record and return an injury risk prediction.

    - **injury_probability**: float in [0, 1]
    - **injury_risk_label**: LOW | MEDIUM | HIGH
    """
    try:
        return request.app.state.predictor.predict_one(record)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {exc}",
        ) from exc


@router.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    summary="Predict injury risk for a batch of athletes",
    status_code=status.HTTP_200_OK,
)
async def predict_batch(payload: BatchPredictionRequest, request: Request) -> BatchPredictionResponse:
    """Batch prediction — accepts up to 100 athlete records."""
    try:
        predictions = request.app.state.predictor.predict_batch(payload.athletes)
        return BatchPredictionResponse(predictions=predictions, total=len(predictions))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {exc}",
        ) from exc
