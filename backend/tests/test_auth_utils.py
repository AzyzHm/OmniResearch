import time
from datetime import timedelta

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from backend.config.auth import (
    create_access_token, hash_password, require_admin, require_superadmin, verify_password,
)
from backend.config.settings import get_settings


def _creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("mysecret")
        assert hashed != "mysecret"

    def test_verify_correct_password(self):
        hashed = hash_password("correct-horse-battery")
        assert verify_password("correct-horse-battery", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct-horse-battery")
        assert verify_password("wrong-password", hashed) is False

    def test_verify_empty_password_returns_false(self):
        hashed = hash_password("correct")
        assert verify_password("", hashed) is False

    def test_verify_malformed_hash_returns_false(self):
        assert verify_password("anything", "not-a-valid-hash") is False

    def test_two_hashes_of_same_password_differ(self):
        """Argon2 uses a random salt so hashes must never be identical."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2
        assert verify_password("same", h1)
        assert verify_password("same", h2)


class TestJWT:
    def test_token_decodes_correctly(self):
        settings = get_settings()
        token = create_access_token(user_id="u1", username="alice", role="user")
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == "u1"
        assert payload["username"] == "alice"
        assert payload["role"] == "user"

    def test_token_contains_expiry(self):
        settings = get_settings()
        token = create_access_token(user_id="u1", username="alice", role="user")
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert "exp" in payload

    def test_custom_expiry_respected(self):
        settings = get_settings()
        delta = timedelta(minutes=5)
        before = int(time.time())
        token = create_access_token("u1", "alice", "user", expires_delta=delta)
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert 290 <= payload["exp"] - before <= 310

    def test_admin_role_encoded(self):
        settings = get_settings()
        token = create_access_token(user_id="a1", username="admin", role="admin")
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert payload["role"] == "admin"


class TestRequireAdmin:
    """require_admin accepts both 'admin' and 'superadmin' roles."""

    def test_admin_role_is_accepted(self):
        token = create_access_token(user_id="a1", username="admin", role="admin")
        payload = require_admin(_creds(token))
        assert payload["role"] == "admin"

    def test_superadmin_role_is_accepted(self):
        token = create_access_token(user_id="s1", username="root", role="superadmin")
        payload = require_admin(_creds(token))
        assert payload["role"] == "superadmin"

    def test_regular_user_role_is_rejected(self):
        token = create_access_token(user_id="u1", username="alice", role="user")
        with pytest.raises(HTTPException) as exc_info:
            require_admin(_creds(token))
        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail

    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            require_admin(_creds("not-a-valid-token"))
        assert exc_info.value.status_code == 401


class TestRequireSuperadmin:
    """require_superadmin only accepts the 'superadmin' role — not plain 'admin'."""

    def test_superadmin_role_is_accepted(self):
        token = create_access_token(user_id="s1", username="root", role="superadmin")
        payload = require_superadmin(_creds(token))
        assert payload["role"] == "superadmin"

    def test_admin_role_is_rejected(self):
        token = create_access_token(user_id="a1", username="admin", role="admin")
        with pytest.raises(HTTPException) as exc_info:
            require_superadmin(_creds(token))
        assert exc_info.value.status_code == 403
        assert "Super admin access required" in exc_info.value.detail

    def test_regular_user_role_is_rejected(self):
        token = create_access_token(user_id="u1", username="alice", role="user")
        with pytest.raises(HTTPException) as exc_info:
            require_superadmin(_creds(token))
        assert exc_info.value.status_code == 403