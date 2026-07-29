from datetime import datetime, timedelta, timezone
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from backend.config.settings import get_settings

_ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2)


def hash_password(plain: str) -> str:
    """Return an Argon2id hash of *plain*. No length limit."""
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Return True if *plain* matches *hashed*.
    Returns False (never raises) on any mismatch or malformed hash.
    """
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


_bearer = HTTPBearer(auto_error=False)


def create_access_token(user_id: str, username: str, role: str, expires_delta: Optional[timedelta] = None,) -> str:
    """ Return a JWT access token for the given user ID, username, and role. """
    settings = get_settings()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _extract_token(
    credentials: Optional[HTTPAuthorizationCredentials],
    request: Request = None  # type: ignore[assignment]
) -> str:
    """Prefer the Authorization header if present, otherwise fall back to
    the httpOnly access_token cookie set by /auth/login."""
    if credentials is not None:
        return credentials.credentials
    if request is not None:
        cookie_token = request.cookies.get("access_token")
        if cookie_token:
            return cookie_token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    request: Request = None  # type: ignore[assignment]
) -> dict:
    """Return token payload for any authenticated user."""
    token = _extract_token(credentials, request)
    return _decode_token(token)


def _require_role(*allowed_roles: str, message: str):
    """Factory for role-gated dependencies. require_admin and
    require_superadmin below are just two instances of this"""
    def dependency(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
        request: Request = None  # type: ignore[assignment]
    ) -> dict:
        token = _extract_token(credentials, request)
        payload = _decode_token(token)
        if payload.get("role") not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)
        return payload
    return dependency


require_admin = _require_role("admin", "superadmin", message="Admin access required.")
require_superadmin = _require_role("superadmin", message="Super admin access required.")