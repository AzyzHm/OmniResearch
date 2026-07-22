from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, status

from backend.config.settings import get_settings

from backend.config.auth import create_access_token, hash_password, verify_password
from backend.database.db import get_supabase
from backend.models.auth import LoginRequest, RegisterRequest, TokenResponse
from backend.models.log import MessageResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account (pending admin approval)",
)
async def register(payload: RegisterRequest):
    db = get_supabase()

    existing = (
        db.table("users")
        .select("id")
        .eq("username", payload.username)
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken.",
        )

    hashed = hash_password(payload.password)
    db.table("users").insert(
        {
            "username": payload.username,
            "password": hashed,
            "role": "user",
            "is_approved": False,
        }
    ).execute()

    return MessageResponse(
        message="Account created successfully. Please wait for an administrator to approve your account."
    )

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive a JWT access token",
)
async def login(payload: LoginRequest, request: Request, response: Response):
    db = get_supabase()

    result = (
        db.table("users")
        .select("id, username, password, role, is_approved")
        .eq("username", payload.username)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    user : Any = result.data[0]

    if not verify_password(payload.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    if user["role"] != "admin" and not user["is_approved"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending admin approval.",
        )

    ip = request.client.host if request.client else None
    db.table("login_logs").insert(
        {
            "user_id": user["id"],
            "username": user["username"],
            "login_time": datetime.now(timezone.utc).isoformat(),
            "ip_address": ip,
        }
    ).execute()

    token = create_access_token(
        user_id=user["id"],
        username=user["username"],
        role=user["role"],
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=get_settings().cookie_secure,
        samesite="lax",
        max_age=get_settings().jwt_expire_minutes * 60,
        path="/",
    )

    return TokenResponse(
        access_token=token,
        user_id=user["id"],
        username=user["username"],
        role=user["role"],
    )

@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Clear the access token cookie",
)
async def logout(response: Response):
    response.delete_cookie(key="access_token", path="/")
    return MessageResponse(message="Logged out successfully.")