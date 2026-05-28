"""CSRD Comply — FastAPI dependencies (auth).
Supports both HttpOnly cookie and Authorization header for JWT.
"""
import uuid
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Verify JWT token and return the current user.
    
    Supports both:
    1. HttpOnly cookie (`access_token`) — recommended for production
    2. Authorization: Bearer header — fallback for API clients
    """
    token = None

    # 1) Try HttpOnly cookie first (XSS-safe)
    if request.cookies and "access_token" in request.cookies:
        token = request.cookies["access_token"]

    # 2) Fallback to Authorization header
    if token is None and credentials is not None:
        token = credentials.credentials

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide token via HttpOnly cookie or Authorization header.",
        )

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    user = db.query(User).filter(User.user_id == uuid.UUID(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    # Verify token version (prevents reuse of revoked tokens)
    token_version = payload.get("tok_v", 0)
    if token_version != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
        )
    return user
