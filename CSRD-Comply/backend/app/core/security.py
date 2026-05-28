"""CSRD Comply — JWT auth utilities."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from app.core.config import settings


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    password_bytes = plain.encode("utf-8")
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


# ── HttpOnly Cookie Helpers (for secure JWT storage) ────────────

def set_auth_cookie(response, token: str, max_age: int = 86400):
    """Set JWT as a secure HttpOnly cookie.
    
    Args:
        response: FastAPI Response object
        token: JWT token string
        max_age: Cookie lifetime in seconds (default 24h)
    """
    # `secure=True` only in production (HTTPS), otherwise it won't work in local dev

    is_production = getattr(settings, "ENVIRONMENT", "development") == "production"
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,        # Not accessible via JavaScript
        secure=is_production, # HTTPS only in production
        samesite="lax",       # CSRF protection

        max_age=max_age,
        path="/",
    )


def clear_auth_cookie(response):
    """Remove the authentication cookie."""

    is_production = getattr(settings, "ENVIRONMENT", "development") == "production"
    response.set_cookie(
        key="access_token",
        value="",
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=0,
        path="/",
    )


# ── Alias for backward compatibility with multitenancy.py ──────

decode_token = decode_access_token
