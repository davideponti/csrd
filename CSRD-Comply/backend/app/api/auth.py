"""CSRD Comply — Auth endpoints (register, login, refresh).
Uses HttpOnly cookies for JWT storage (XSS-safe).
Sends transactional emails on registration and password reset.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
import re
from datetime import timedelta
from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password, create_access_token,
    decode_access_token, set_auth_cookie, clear_auth_cookie,
)
from app.models import User, Company
from app.core.config import settings
from app.core.deps import get_current_user
from app.services.email_service import send_welcome_email, send_password_reset_email

router = APIRouter()


# ── Schemas ─────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    company_name: str
    company_size: int | None = None
    sector: str | None = None
    country: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


# ── Endpoints ───────────────────────────────────────────────────
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new company & admin user. Returns JWT via HttpOnly cookie."""
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Registration unavailable")

    company = Company(
        company_name=req.company_name,
        sector=req.sector or "Unknown",
        country=req.country or "IT",
        employee_count=req.company_size,
        reporting_year=2026,
    )
    db.add(company)
    db.flush()

    user = User(
        company_id=company.company_id,
        email=req.email,
        hashed_password=hash_password(req.password),
        role="admin",
    )
    db.add(user)
    db.commit()

    token = create_access_token({
        "sub": str(user.user_id),
        "company_id": str(company.company_id),
        "tok_v": 0,
    })

    # Send welcome email in background (non-blocking)
    try:
        login_url = f"https://{settings.DEPLOYMENT_DOMAIN}/auth/login"
        send_welcome_email(
            to_email=req.email,
            name=req.email.split("@")[0],
            company_name=req.company_name,
            login_url=login_url,
        )
    except Exception:
        pass  # Email failure should not block registration

    # Return token in body for backward compatibility (API clients)
    from fastapi.responses import JSONResponse
    response = JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"access_token": token, "token_type": "bearer"},
    )
    set_auth_cookie(response, token)
    return response


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT via HttpOnly cookie."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    user.last_login = None  # set programmatically
    db.commit()

    token = create_access_token({
        "sub": str(user.user_id),
        "company_id": str(user.company_id),
        "tok_v": user.token_version,
    })

    # Return token in body (for API clients) + set HttpOnly cookie (for browser)
    from fastapi.responses import JSONResponse
    response = JSONResponse(
        content={"access_token": token, "token_type": "bearer"},
    )
    set_auth_cookie(response, token)
    return response


@router.post("/refresh")
def refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh an expired token — implements token rotation.

    On each refresh, the token_version is incremented, invalidating
    all previously issued tokens. This prevents token reuse if a JWT
    is compromised.
    """
    payload = decode_access_token(req.refresh_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Token rotation: verify token_version matches, then increment
    token_version = payload.get("tok_v", 0)
    if token_version != user.token_version:
        raise HTTPException(
            status_code=401,
            detail="Token has been revoked. Please log in again.",
        )

    # Increment token_version to invalidate the old token
    user.token_version += 1
    db.commit()

    new_token = create_access_token({
        "sub": str(user.user_id),
        "company_id": str(user.company_id),
        "tok_v": user.token_version,
    })

    from fastapi.responses import JSONResponse
    response = JSONResponse(
        content={"access_token": new_token, "token_type": "bearer"},
    )
    set_auth_cookie(response, new_token)
    return response


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send password reset email."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        # Don't reveal whether the email exists — return success either way
        return {"status": "sent", "message": "If the email exists, a reset link has been sent."}

    # Generate a password reset token (short-lived)
    reset_token = create_access_token(
        {"sub": str(user.user_id), "purpose": "password_reset"},
        expires_delta=timedelta(minutes=60),  # 1 hour
    )
    reset_url = f"https://{settings.DEPLOYMENT_DOMAIN}/auth/reset-password?token={reset_token}"

    try:
        send_password_reset_email(
            to_email=req.email,
            name=user.email.split("@")[0],
            reset_url=reset_url,
        )
    except Exception:
        pass  # Email failure should not expose anything

    return {"status": "sent", "message": "If the email exists, a reset link has been sent."}


# ── Get current user ──────────────────────────────────────────
@router.get("/me")
def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get the current authenticated user's info.
    Used by frontend to verify session via HttpOnly cookie.
    """
    return {
        "id": str(current_user.user_id),
        "email": current_user.email,
        "company_id": str(current_user.company_id),
        "company_name": current_user.company.company_name if current_user.company else "",
        "role": current_user.role,
    }


# ── Logout endpoint ────────────────────────────────────────────
@router.post("/logout")
def logout():
    """Logout by clearing the HttpOnly auth cookie."""
    from fastapi.responses import JSONResponse
    response = JSONResponse(content={"message": "Logged out successfully"})
    clear_auth_cookie(response)
    return response
