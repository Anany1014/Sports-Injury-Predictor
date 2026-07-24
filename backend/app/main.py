"""
backend.app.main
~~~~~~~~~~~~~~~~
FastAPI application entrypoint for the Sports Injury Predictor API.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import health, predict
from backend.app.core.config import settings
from backend.app.services.predictor_service import PredictorService

# ---------------------------------------------------------------------------
# Lifespan: load model once at startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Load ML model at startup and clean up at shutdown."""
    app.state.predictor = PredictorService()
    app.state.predictor.load()
    yield
    # cleanup (if needed) goes here


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    application = FastAPI(
        title="Sports Injury Predictor API",
        description="Predict the probability of sports injury from athlete biometrics and training load.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    application.include_router(health.router, tags=["Health"])
    application.include_router(predict.router, tags=["Prediction"])
    application.include_router(predict.router, prefix="/api/v1", tags=["Prediction (v1)"])

    return application


app = create_app()
