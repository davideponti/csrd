"""CSRD Comply — Company endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import uuid
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User, Company

router = APIRouter()


class CompanyResponse(BaseModel):
    company_id: uuid.UUID
    company_name: str
    vat_number: Optional[str] = None
    country: str
    sector: str
    employee_count: Optional[int] = None
    turnover: Optional[float] = None
    reporting_year: int

    class Config:
        from_attributes = True


class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    vat_number: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    employee_count: Optional[int] = None
    turnover: Optional[float] = None
    balance_sheet_total: Optional[float] = None


@router.get("/me", response_model=CompanyResponse)
def get_my_company(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's company profile."""
    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    return company


@router.patch("/me", response_model=CompanyResponse)
def update_my_company(
    data: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user's company profile."""
    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company
