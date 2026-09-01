"""Password hashing and JWT helpers. Never log secrets, tokens, or hashes."""

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

_password_hasher = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(plain_password, password_hash)
    except Exception:
        return False


def create_access_token(
    *,
    subject: UUID,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "token_type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("token_type") != "access":
        raise jwt.InvalidTokenError("Not an access token")
    return payload


def create_refresh_token(*, subject: UUID, role: str) -> tuple[str, UUID, datetime]:
    settings = get_settings()
    token_id = uuid4()
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": str(subject), "role": role, "jti": str(token_id), "token_type": "refresh", "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm), token_id, expires_at


def decode_refresh_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("token_type") != "refresh":
        raise jwt.InvalidTokenError("Not a refresh token")
    return payload


def hash_refresh_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()
