"""
backend.app.core.middleware
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Middleware for security headers, exception shielding, and simple in-memory rate limiting.
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that injects HTTP security headers into every response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)
        # Content Security Policy (restrict all scripts/styles/requests)
        # Allow unsafe-inline style for standard frontend routing/transitions
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self' http://localhost:8000 http://localhost:5173 http://127.0.0.1:8000;"
        )
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class RateLimiter:
    """A thread-safe in-memory rate limiter using sliding window log."""

    def __init__(self, limit: int = 5, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        # Maps key (usually client IP or username) to a list of request timestamps
        self.history: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        # Clean up timestamps older than window
        cutoff = now - self.window_seconds
        self.history[key] = [t for t in self.history[key] if t > cutoff]

        if len(self.history[key]) < self.limit:
            self.history[key].append(now)
            return True
        return False


# Global instance of predictor rate limiter (defaults to settings.prediction_rate_limit)
# Parser for limit: "5/minute" or similar
def _parse_rate_limit(limit_str: str) -> tuple[int, int]:
    try:
        parts = limit_str.split("/")
        limit = int(parts[0])
        unit = parts[1].strip().lower()
        if "minute" in unit:
            return limit, 60
        elif "hour" in unit:
            return limit, 3600
        elif "second" in unit:
            return limit, 1
        return limit, 60
    except Exception:
        return 5, 60  # Safe fallback: 5 req / minute


limit, window = _parse_rate_limit(settings.prediction_rate_limit)
prediction_limiter = RateLimiter(limit=limit, window_seconds=window)


async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    """Rate limit the prediction endpoints only."""
    # Apply to prediction endpoints
    if request.url.path in {"/predict", "/predict/batch", "/api/v1/predict", "/api/v1/predict/batch"}:
        # Bypass rate limiting in testing mode
        if settings.app_env == "testing":
            return await call_next(request)

        # Use client IP as the rate-limiting key, or fallback to user ID if authenticated
        client_ip = request.client.host if request.client else "unknown-ip"
        
        # Check authorization cookie to find sub-claim (user ID) if available
        # This prevents rate-limiting the entire NAT/subnetwork if multiple users are logged in
        auth_cookie = request.cookies.get("access_token")
        rate_limit_key = client_ip
        if auth_cookie:
            try:
                import jwt
                payload = jwt.decode(
                    auth_cookie,
                    settings.jwt_secret_key,
                    algorithms=[settings.jwt_algorithm],
                    options={"verify_exp": True}
                )
                rate_limit_key = payload.get("sub", client_ip)
            except Exception:
                pass  # Fallback to IP if token is invalid/expired

        if not prediction_limiter.is_allowed(rate_limit_key):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please wait before submitting more predictions."
                }
            )
            
    return await call_next(request)
