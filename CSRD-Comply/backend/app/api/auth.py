"""CSRD Comply — Auth endpoints (register, login, refresh)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.models import User, Company

router = APIRouter()


# ── Schemas ─────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    company_name: str
    company_size: int | None = None
    sector: str | None = None
    country: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Endpoints ───────────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new company & admin user."""
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

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

    token = create_access_token({"sub": str(user.user_id)})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    user.last_login = None  # set programmatically
    db.commit()

    token = create_access_token({"sub": str(user.user_id)})
    return TokenResponse(access_token=token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest):
    """Refresh an expired token."""
    payload = decode_access_token(req.refresh_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    new_token = create_access_token({"sub": payload.get("sub")})
    return TokenResponse(access_token=new_token)
