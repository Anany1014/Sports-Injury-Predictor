"""
backend.app.api.auth
~~~~~~~~~~~~~~~~~~~~
API handlers for user login, session termination, and identity retrieval
using HTTP-Only secure cookies.
"""
from __future__ import annotations

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from backend.app.core.security import (
    MOCK_USER_DB,
    User,
    create_access_token,
    get_current_user,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    username: str
    role: str
    athlete_id: str | None = None
    sport: str | None = None


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate user and set HTTP-only cookie session",
)
async def login(payload: LoginRequest, response: Response) -> LoginResponse:
    """Validate credentials and issue standard cookie session."""
    user_record = MOCK_USER_DB.get(payload.username)
    if not user_record or not verify_password(payload.password, user_record["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Prepare token payloads
    token_data = {
        "sub": user_record["username"],
        "role": user_record["role"],
        "athlete_id": user_record.get("athlete_id"),
        "sport": user_record.get("sport"),
    }
    
    token = create_access_token(data=token_data, expires_delta=timedelta(hours=2))
    
    # Store access token in HttpOnly SameSite cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set False for localhost HTTP development stability
        max_age=7200,  # 2 hours session life
    )

    return LoginResponse(
        username=user_record["username"],
        role=user_record["role"],
        athlete_id=user_record.get("athlete_id"),
        sport=user_record.get("sport")
    )


@router.post(
    "/logout",
    summary="Clear the authentication session cookie",
)
async def logout(response: Response) -> dict[str, str]:
    """Clean the user token session cookie."""
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=False,
    )
    return {"status": "success", "detail": "Session terminated successfully"}


@router.get(
    "/me",
    response_model=LoginResponse,
    summary="Retrieve current user session metadata",
)
async def get_me(user: User = Depends(get_current_user)) -> LoginResponse:
    """Retrieve logged-in user context."""
    return LoginResponse(
        username=user.username,
        role=user.role,
        athlete_id=user.athlete_id,
        sport=user.sport
    )
