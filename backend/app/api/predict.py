"""
backend.app.api.predict
~~~~~~~~~~~~~~~~~~~~~~~~
POST /api/v1/predict       — single prediction
POST /api/v1/predict/batch — batch predictions (up to 100 athletes)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.app.core.security import get_current_user, User
from backend.app.schemas.prediction import (
    AthleteRecord,
    BatchPredictionRequest,
    BatchPredictionResponse,
    PredictionResponse,
)

router = APIRouter()


def verify_prediction_access(user: User, record: AthleteRecord) -> None:
    """Enforce ownership validation on requests for HIPAA/GDPR compliance."""
    if user.role == "Athlete":
        if record.athlete_id != user.athlete_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: As an Athlete, you can only request predictions for your own ID ({user.athlete_id}). Trying to access {record.athlete_id}."
            )
    elif user.role == "Coach":
        if record.sport != user.sport:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: As a Coach, you can only request predictions for athletes in your sport ({user.sport}). Trying to access {record.sport}."
            )
    # Medical Staff and Admin have unrestricted access


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict injury risk for a single athlete",
    status_code=status.HTTP_200_OK,
)
async def predict_single(
    record: AthleteRecord,
    request: Request,
    user: User = Depends(get_current_user),
) -> PredictionResponse:
    """
    Accept a single athlete record and return an injury risk prediction.

    - **injury_probability**: float in [0, 1]
    - **injury_risk_label**: LOW | MEDIUM | HIGH
    """
    # Enforce data boundary ownership rules
    verify_prediction_access(user, record)
    
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
async def predict_batch(
    payload: BatchPredictionRequest,
    request: Request,
    user: User = Depends(get_current_user),
) -> BatchPredictionResponse:
    """Batch prediction — accepts up to 100 athlete records."""
    # Enforce ownership rules on every record in the batch
    for record in payload.athletes:
        verify_prediction_access(user, record)

    try:
        predictions = request.app.state.predictor.predict_batch(payload.athletes)
        return BatchPredictionResponse(predictions=predictions, total=len(predictions))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {exc}",
        ) from exc

