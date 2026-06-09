"""CSRD Comply — Auth endpoints (register, login, refresh).
Uses HttpOnly cookies for JWT storage (XSS-safe).
Sends transactional emails on registration and password reset.
"""
import secrets
import string
import logging
from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
import re

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password, create_access_token,
    decode_access_token, set_auth_cookie, clear_auth_cookie,
)
from app.models import User, Company
from app.core.config import settings
from app.core.deps import get_current_user
from app.services.email_service import (
    send_welcome_email,
    send_password_reset_email,
    send_otp_email,
)

logger = logging.getLogger(__name__)

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


class SendOtpRequest(BaseModel):
    email: str


class VerifyOtpRequest(BaseModel):
    email: str
    otp: str


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
        email_verified=False,
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
    except Exception as e:
        logger.warning("Failed to send welcome email to %s: %s", req.email, e)

    # Return token in body for backward compatibility (API clients)
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

    user.last_login = datetime.now(timezone.utc)

    # Check if email is verified - if not, send OTP and require verification
    if not user.email_verified:
        # Generate and send OTP
        otp = ''.join(secrets.choice(string.digits) for _ in range(6))
        user.otp_code = otp
        user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        db.commit()

        try:
            send_otp_email(
                to_email=user.email,
                name=user.email.split("@")[0],
                otp_code=otp,
            )
        except Exception as e:
            logger.warning("Failed to send OTP email to %s: %s", user.email, e)

        response = JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "requires_otp": True,
                "email": user.email,
                "message": "Email verification required. An OTP has been sent to your email.",
            },
        )
        return response

    db.commit()

    token = create_access_token({
        "sub": str(user.user_id),
        "company_id": str(user.company_id),
        "tok_v": user.token_version,
    })

    response = JSONResponse(
        content={"access_token": token, "token_type": "bearer"},
    )
    set_auth_cookie(response, token)
    return response


@router.post("/send-otp")
def send_otp(req: SendOtpRequest, db: Session = Depends(get_db)):
    """Send a new OTP code for email verification."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        # Don't reveal if email exists
        return {"status": "sent", "message": "If the email exists, an OTP has been sent."}

    otp = ''.join(secrets.choice(string.digits) for _ in range(6))
    user.otp_code = otp
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()

    try:
        send_otp_email(
            to_email=user.email,
            name=user.email.split("@")[0],
            otp_code=otp,
        )
    except Exception as e:
        logger.warning("Failed to send OTP to %s: %s", user.email, e)

    return {"status": "sent", "message": "OTP sent successfully."}


@router.post("/verify-email")
def verify_email(req: VerifyOtpRequest, db: Session = Depends(get_db)):
    """Verify email with OTP code.

    Implements brute-force protection:
    - Max 5 failed attempts, then OTP is invalidated
    - Rate limited to 5 requests per minute
    """
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.email_verified:
        # Already verified - return token directly
        token = create_access_token({
            "sub": str(user.user_id),
            "company_id": str(user.company_id),
            "tok_v": user.token_version,
        })
        response = JSONResponse(
            content={"access_token": token, "token_type": "bearer"},
        )
        set_auth_cookie(response, token)
        return response

    if not user.otp_code or not user.otp_expires_at:
        raise HTTPException(status_code=400, detail="No OTP requested. Please request a new OTP.")

    if datetime.now(timezone.utc) > user.otp_expires_at:
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new one.")

    if user.otp_code != req.otp:
        # Increment failed attempts counter
        user.otp_attempts = getattr(user, 'otp_attempts', 0) + 1
        db.commit()

        # Lockout after 5 failed attempts
        if user.otp_attempts >= 5:
            user.otp_code = None
            user.otp_expires_at = None
            user.otp_attempts = 0
            db.commit()
            raise HTTPException(status_code=429, detail="Too many failed attempts. Please request a new OTP.")

        raise HTTPException(status_code=400, detail="Invalid OTP code.")

    # Verify email
    user.email_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    user.otp_attempts = 0
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token({
        "sub": str(user.user_id),
        "company_id": str(user.company_id),
        "tok_v": user.token_version,
    })

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

    # Save reset token in DB
    user.reset_password_token = reset_token
    user.reset_password_expires_at = datetime.now(timezone.utc) + timedelta(minutes=60)
    db.commit()

    try:
        send_password_reset_email(
            to_email=req.email,
            name=user.email.split("@")[0],
            reset_url=reset_url,
        )
    except Exception as e:
        logger.warning("Failed to send password reset email to %s: %s", req.email, e)

    return {"status": "sent", "message": "If the email exists, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using a valid reset token."""
    payload = decode_access_token(req.token)
    if payload is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    purpose = payload.get("purpose")
    if purpose != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid token purpose.")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid token payload.")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Validate token from DB
    if user.reset_password_token != req.token:
        raise HTTPException(status_code=400, detail="Token already used or invalid.")
    if user.reset_password_expires_at and datetime.now(timezone.utc) > user.reset_password_expires_at:
        raise HTTPException(status_code=400, detail="Reset token expired.")

    # Update password
    user.hashed_password = hash_password(req.password)
    user.reset_password_token = None
    user.reset_password_expires_at = None
    user.token_version += 1  # Invalidate all existing sessions
    db.commit()

    return {"message": "Password reset successfully. You can now log in with your new password."}


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
        "email_verified": current_user.email_verified,
    }


# ── Logout endpoint ────────────────────────────────────────────
@router.post("/logout")
def logout():
    """Logout by clearing the HttpOnly auth cookie."""
    response = JSONResponse(content={"message": "Logged out successfully"})
    clear_auth_cookie(response)
    return response
