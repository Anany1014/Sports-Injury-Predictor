"""
backend.app.api.health
~~~~~~~~~~~~~~~~~~~~~~~~
GET /health — liveness probe
GET /health/ready — readiness probe (checks model is loaded)
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    return HealthResponse(status="ok", model_loaded=False)


@router.get("/health/ready", response_model=HealthResponse, summary="Readiness probe")
async def ready(request: Request) -> HealthResponse:
    model_loaded = hasattr(request.app.state, "predictor") and request.app.state.predictor is not None
    return HealthResponse(status="ready" if model_loaded else "not_ready", model_loaded=model_loaded)
