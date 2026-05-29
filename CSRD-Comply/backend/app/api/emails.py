"""
CSRD Comply — Transactional Email API Endpoints.

Provides endpoints for:
- Sending welcome emails
- Password reset emails
- Custom email sending (admin only)
- Email quota/status
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.services.email_service import (
    get_email_service,
    send_welcome_email as svc_send_welcome,
    send_password_reset_email as svc_send_reset,
    send_report_ready_email as svc_send_report,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────

class SendWelcomeRequest(BaseModel):
    email: str
    name: str
    company_name: str
    login_url: str = ""


class SendPasswordResetRequest(BaseModel):
    email: str
    name: str
    reset_url: str


class SendReportRequest(BaseModel):
    email: str
    name: str
    report_title: str
    report_url: str


class EmailStatus(BaseModel):
    configured: bool
    provider: str = "none"
    environment: str = ""


# ── Endpoints ────────────────────────────────────────────────

@router.get("/status")
def get_email_status():
    """Get email service configuration status."""
    from app.core.config import settings
    svc = get_email_service()
    
    if settings.ENVIRONMENT == "development":
        provider = "console (development)"
    elif svc._sendgrid_key:
        provider = "sendgrid"
    elif svc._mailgun_key:
        provider = "mailgun"
    elif svc._smtp_host != "localhost":
        provider = f"smtp ({svc._smtp_host})"
    else:
        provider = "not configured"
    
    return {
        "configured": provider != "not configured",
        "provider": provider,
        "environment": settings.ENVIRONMENT,
    }


@router.post("/welcome")
def send_welcome(
    data: SendWelcomeRequest,
    current_user: User = Depends(get_current_user),  # Requires auth
):
    """Send a welcome email. Admin-only in production."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can send welcome emails",
        )
    
    success = svc_send_welcome(
        to_email=data.email,
        name=data.name,
        company_name=data.company_name,
        login_url=data.login_url or "https://csrdcomply.com/login",
    )
    
    if success:
        return {"status": "sent", "to": data.email}
    else:
        return {"status": "failed", "to": data.email}, 500


@router.post("/password-reset")
def send_password_reset(
    data: SendPasswordResetRequest,
    current_user: User = Depends(get_current_user),
):
    """Send a password reset email."""
    if current_user.role != "admin" and current_user.email != data.email:
        # Only admins can send password reset for other users
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only request password reset for your own account",
        )
    
    success = svc_send_reset(
        to_email=data.email,
        name=data.name,
        reset_url=data.reset_url,
    )
    
    if success:
        return {"status": "sent", "to": data.email}
    else:
        return {"status": "failed", "to": data.email}, 500


@router.post("/report-ready")
def send_report_ready(
    data: SendReportRequest,
    current_user: User = Depends(get_current_user),
):
    """Send a report ready notification."""
    success = svc_send_report(
        to_email=data.email,
        name=data.name,
        report_title=data.report_title,
        report_url=data.report_url,
    )
    
    if success:
        return {"status": "sent", "to": data.email}
    else:
        return {"status": "failed", "to": data.email}, 500
