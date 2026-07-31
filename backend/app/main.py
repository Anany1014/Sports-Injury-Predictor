"""
backend.app.main
~~~~~~~~~~~~~~~~
FastAPI application entrypoint for the Sports Injury Predictor API.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.api import health, predict, auth, recommendations
from backend.app.core.config import settings
from backend.app.core.middleware import SecurityHeadersMiddleware, rate_limit_middleware
from backend.app.services.predictor_service import PredictorService


# Configure server-side logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

    # Global Exception Handlers for Security Shielding
    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Shield client from detailed Exception details while passing HTTP statuses."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Bubble up structural Pydantic errors for user debugging details."""
        # Sanitize any malicious input reflection in validation errors
        sanitized_errors = []
        for error in exc.errors():
            sanitized_errors.append({
                "loc": error.get("loc"),
                "msg": error.get("msg"),
                "type": error.get("type")
            })
        return JSONResponse(
            status_code=422,
            content={"detail": sanitized_errors}
        )

    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Intercept any raw python Exception and mask it to prevent trace/path leakage."""
        logger.error(f"Internal system error at {request.url.path}: {exc}", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred. Please contact system support."}
        )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Security Headers and Rate Limiting Middlewares
    application.add_middleware(SecurityHeadersMiddleware)
    application.middleware("http")(rate_limit_middleware)

    # Routers
    application.include_router(health.router, tags=["Health"])
    application.include_router(auth.router, tags=["Authentication"])
    application.include_router(auth.router, prefix="/api/v1", tags=["Authentication (v1)"])
    application.include_router(predict.router, tags=["Prediction"])
    application.include_router(predict.router, prefix="/api/v1", tags=["Prediction (v1)"])
    application.include_router(recommendations.router, tags=["AI Recommendations"])
    application.include_router(recommendations.router, prefix="", tags=["AI Recommendations (root)"])

    return application



app = create_app()

