"""
backend.app.core.security
~~~~~~~~~~~~~~~~~~~~~~~~~
Core security logic: JWT token creation/decryption, password hashing using bcrypt,
and Role-Based Access Control (RBAC) dependency checkers.
"""
from __future__ import annotations

import bcrypt
from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from fastapi import Depends, HTTPException, Request, status
import jwt
from pydantic import BaseModel

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models & Schemas
# ---------------------------------------------------------------------------
class User(BaseModel):
    username: str
    role: str
    athlete_id: str | None = None
    sport: str | None = None


# ---------------------------------------------------------------------------
# Cryptographic Helpers
# ---------------------------------------------------------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify standard bcrypt password matches plain input."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Generate bcrypt hash for a plain password string."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


# ---------------------------------------------------------------------------
# Mock Database containing hashed passwords
# ---------------------------------------------------------------------------
MOCK_USER_DB = {
    "alex": {
        "username": "alex",
        "role": "Athlete",
        "athlete_id": "ATH-101",
        "sport": "Football",
        # bcrypt hash of 'alex123'
        "hashed_password": get_password_hash("alex123")
    },
    "coach_dan": {
        "username": "coach_dan",
        "role": "Coach",
        "sport": "Football",
        # bcrypt hash of 'coach123'
        "hashed_password": get_password_hash("coach123")
    },
    "physio_sarah": {
        "username": "physio_sarah",
        "role": "Medical Staff",
        # bcrypt hash of 'physio123'
        "hashed_password": get_password_hash("physio123")
    },
    "admin": {
        "username": "admin",
        "role": "Admin",
        # bcrypt hash of 'admin123'
        "hashed_password": get_password_hash("admin123")
    }
}



def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Generate a signed HS256 JWT key."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=2)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


# ---------------------------------------------------------------------------
# Dependencies & Guards
# ---------------------------------------------------------------------------
async def get_current_user(request: Request) -> User:
    """Validate JWT cookie and retrieve user metadata parameters."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials missing from application request cookie"
        )

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        username: str | None = payload.get("sub")
        if not username or username not in MOCK_USER_DB:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated user identity could not be retrieved from system record"
            )
        
        user_info = MOCK_USER_DB[username]
        return User(
            username=user_info["username"],
            role=user_info["role"],
            athlete_id=user_info.get("athlete_id"),
            sport=user_info.get("sport")
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please authenticate again"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is invalid or structurally distorted"
        )


def require_roles(*allowed_roles: str):
    """Factory creating dependency checking if current user role matches permitted roles."""
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: Permissions restricted to roles: {', '.join(allowed_roles)}. Your role is {current_user.role}"
            )
        return current_user
    return dependency
