"""
backend.app.api.recommendations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
FastAPI router for OpenRouter AI LLM Personalised Recovery & Workload Prescriptions.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.app.schemas.prediction import AthleteRecord, PredictionResponse
from backend.app.services.llm_service import LLMRecoveryService

router = APIRouter(prefix="/api/v1/recommendations", tags=["AI Recommendations"])
llm_service = LLMRecoveryService()


class RecommendationRequest(BaseModel):
    record: AthleteRecord
    prediction: PredictionResponse


@router.post("", summary="Generate AI Athletic Recovery Plan (JSON)")
async def generate_recommendation(body: RecommendationRequest) -> dict[str, Any]:
    """Generate a non-streaming AI recovery prescription using OpenRouter Nemotron LLM."""
    try:
        result = await llm_service.generate_recovery_plan(body.record, body.prediction)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI recommendation: {str(e)}",
        )


@router.post("/stream", summary="Stream AI Athletic Recovery Plan (SSE)")
async def stream_recommendation(body: RecommendationRequest) -> StreamingResponse:
    """Stream AI recovery prescription via Server-Sent Events ("stream": true)."""
    return StreamingResponse(
        llm_service.stream_recovery_plan(body.record, body.prediction),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/stream/tips", summary="Stream short AI Recovery Tips (SSE)")
async def stream_recovery_tips(body: RecommendationRequest) -> StreamingResponse:
    """Stream short, conversational recovery tips via Server-Sent Events."""
    return StreamingResponse(
        llm_service.stream_recovery_tips(body.record, body.prediction),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/stream/prescription", summary="Stream Structured AI Prescription Cards (SSE)")
async def stream_prescription(body: RecommendationRequest) -> StreamingResponse:
    """Stream structured 4-card recovery prescription (Sleep / Workload / Therapy / Nutrition)."""
    return StreamingResponse(
        llm_service.stream_prescription(body.record, body.prediction),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/stream/full", summary="Stream Unified AI Prescription: 4 Metric Cards + Detailed Plan (SSE)")
async def stream_full_prescription(body: RecommendationRequest) -> StreamingResponse:
    """Stream a single unified recovery prescription with 4 metric cards and a detailed narrative plan."""
    return StreamingResponse(
        llm_service.stream_full_prescription(body.record, body.prediction),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )



