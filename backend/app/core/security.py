from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from app.core.config import settings
from app.core.exceptions import AuthenticationException


# Argon2 hasher instance with recommended secure parameters
_ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)

ALGORITHM = "HS256"


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return _ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against an Argon2 hash, safely handling invalid formats."""
    try:
        return _ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """Generate a signed HS256 JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token, strictly enforcing HS256 and expiration."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub", "iat"]},
        )
        if payload.get("type") != "access":
            raise AuthenticationException("Invalid token type.")
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationException("Access token has expired. Please log in again.")
    except jwt.InvalidTokenError as exc:
        raise AuthenticationException(f"Invalid token: {str(exc)}")


def create_set_password_token(subject: str | Any, email: str, expires_delta: timedelta | None = None) -> str:
    """Generate a signed set-password activation token valid for 24 hours."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(hours=24))

    payload = {
        "sub": str(subject),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "set_password",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_set_password_token(token: str) -> dict[str, Any]:
    """Decode and validate a set-password activation token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub", "email", "type"]},
        )
        if payload.get("type") != "set_password":
            raise AuthenticationException("Invalid token type for password setup.")
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationException("Activation link has expired. Please request a new signup link.")
    except jwt.InvalidTokenError as exc:
        raise AuthenticationException(f"Invalid activation link: {str(exc)}")
