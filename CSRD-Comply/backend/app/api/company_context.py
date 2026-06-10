"""
CSRD Comply — Company Context Settings API

CRUD endpoints for CompanyContextSettings. This data is automatically
injected into every report generation prompt to replace [TO BE CONFIRMED]
placeholders with real company data wherever possible.

All fields are optional. When empty, [TO BE CONFIRMED] remains in the report.
"""
import logging
import uuid
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User, CompanyContextSettings

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Pydantic Schemas ────────────────────────────────────────────

class CompanyProfileSchema(BaseModel):
    company_name: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    reporting_year: Optional[int] = None
    employee_count_total: Optional[int] = None
    employee_count_permanent: Optional[int] = None
    employee_count_temporary: Optional[int] = None
    employee_count_male: Optional[int] = None
    employee_count_female: Optional[int] = None
    employee_count_other: Optional[int] = None
    employee_count_by_geography: Optional[Dict[str, int]] = None
    annual_revenue_eur: Optional[float] = None
    operational_sites_count: Optional[int] = None


class GhgEmissionsSchema(BaseModel):
    scope1_emissions: Optional[float] = None
    scope2_location_based: Optional[float] = None
    scope2_market_based: Optional[float] = None
    scope3_total: Optional[float] = None
    scope3_material_categories: Optional[List[str]] = None
    emissions_baseline_year: Optional[int] = None
    emissions_methodology: Optional[str] = None


class SupplyChainSchema(BaseModel):
    tier1_suppliers_count: Optional[int] = None
    tier2_suppliers_count: Optional[int] = None
    value_chain_countries: Optional[List[str]] = None
    high_risk_countries: Optional[List[str]] = None
    suppliers_code_of_conduct_pct: Optional[float] = None
    supplier_audits_last_year: Optional[int] = None


class WorkforceKpisSchema(BaseModel):
    ltifr: Optional[float] = None
    fatal_accidents: Optional[int] = None
    voluntary_turnover_pct: Optional[float] = None
    avg_training_hours_per_year: Optional[float] = None
    women_in_management_pct: Optional[float] = None
    gender_pay_gap_pct: Optional[float] = None
    union_coverage_pct: Optional[float] = None
    employee_engagement_score: Optional[float] = None


class PaymentPracticesSchema(BaseModel):
    standard_payment_terms_days: Optional[int] = None
    avg_actual_payment_time_days: Optional[float] = None
    invoices_paid_within_terms_pct: Optional[float] = None
    invoices_paid_late_pct: Optional[float] = None


class GovernanceSchema(BaseModel):
    anti_corruption_training_pct: Optional[float] = None
    corruption_incidents_last_year: Optional[int] = None
    whistleblowing_reports_received: Optional[int] = None


class CompanyContextSettingsSchema(BaseModel):
    """Full company context settings payload."""
    company_profile: Optional[CompanyProfileSchema] = None
    ghg_emissions: Optional[GhgEmissionsSchema] = None
    supply_chain: Optional[SupplyChainSchema] = None
    workforce_kpis: Optional[WorkforceKpisSchema] = None
    payment_practices: Optional[PaymentPracticesSchema] = None
    governance: Optional[GovernanceSchema] = None


class CompanyContextSettingsResponse(BaseModel):
    """Response model for company context settings."""
    id: str
    company_id: str

    # Company Profile
    company_name: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    reporting_year: Optional[int] = None
    employee_count_total: Optional[int] = None
    employee_count_permanent: Optional[int] = None
    employee_count_temporary: Optional[int] = None
    employee_count_male: Optional[int] = None
    employee_count_female: Optional[int] = None
    employee_count_other: Optional[int] = None
    employee_count_by_geography: Optional[Dict[str, int]] = None
    annual_revenue_eur: Optional[float] = None
    operational_sites_count: Optional[int] = None

    # GHG Emissions
    scope1_emissions: Optional[float] = None
    scope2_location_based: Optional[float] = None
    scope2_market_based: Optional[float] = None
    scope3_total: Optional[float] = None
    scope3_material_categories: Optional[List[str]] = None
    emissions_baseline_year: Optional[int] = None
    emissions_methodology: Optional[str] = None

    # Supply Chain
    tier1_suppliers_count: Optional[int] = None
    tier2_suppliers_count: Optional[int] = None
    value_chain_countries: Optional[List[str]] = None
    high_risk_countries: Optional[List[str]] = None
    suppliers_code_of_conduct_pct: Optional[float] = None
    supplier_audits_last_year: Optional[int] = None

    # Workforce KPIs
    ltifr: Optional[float] = None
    fatal_accidents: Optional[int] = None
    voluntary_turnover_pct: Optional[float] = None
    avg_training_hours_per_year: Optional[float] = None
    women_in_management_pct: Optional[float] = None
    gender_pay_gap_pct: Optional[float] = None
    union_coverage_pct: Optional[float] = None
    employee_engagement_score: Optional[float] = None

    # Payment Practices
    standard_payment_terms_days: Optional[int] = None
    avg_actual_payment_time_days: Optional[float] = None
    invoices_paid_within_terms_pct: Optional[float] = None
    invoices_paid_late_pct: Optional[float] = None

    # Governance
    anti_corruption_training_pct: Optional[float] = None
    corruption_incidents_last_year: Optional[int] = None
    whistleblowing_reports_received: Optional[int] = None

    class Config:
        from_attributes = True


# ── Helper: Convert ORM model to dict (only non-None values) ────

def _model_to_dict(model: CompanyContextSettings) -> Dict[str, Any]:
    """Convert CompanyContextSettings ORM to dict, excluding None values."""
    result = {}
    for column in model.__table__.columns:
        value = getattr(model, column.name)
        if value is not None:
            result[column.name] = value
    return result


def _dict_to_model(settings: CompanyContextSettings, data: Dict[str, Any]) -> None:
    """Update a CompanyContextSettings ORM instance from a flat dict."""
    for key, value in data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)


# ── Endpoints ───────────────────────────────────────────────────

@router.get("/company-context", response_model=CompanyContextSettingsResponse)
def get_company_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the company context settings for the current user's company."""
    settings = db.query(CompanyContextSettings).filter(
        CompanyContextSettings.company_id == current_user.company_id
    ).first()

    if not settings:
        # Return empty settings with defaults
        return CompanyContextSettingsResponse(
            id=str(uuid.uuid4()),
            company_id=str(current_user.company_id),
        )

    return settings


@router.put("/company-context", response_model=CompanyContextSettingsResponse)
def update_company_context(
    data: CompanyContextSettingsSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update company context settings."""
    settings = db.query(CompanyContextSettings).filter(
        CompanyContextSettings.company_id == current_user.company_id
    ).first()

    if not settings:
        settings = CompanyContextSettings(
            company_id=current_user.company_id,
        )
        db.add(settings)

    # Flatten the nested schema into the model
    updates = {}
    if data.company_profile:
        for key, value in data.company_profile.model_dump(exclude_none=True).items():
            updates[key] = value
    if data.ghg_emissions:
        for key, value in data.ghg_emissions.model_dump(exclude_none=True).items():
            updates[key] = value
    if data.supply_chain:
        for key, value in data.supply_chain.model_dump(exclude_none=True).items():
            updates[key] = value
    if data.workforce_kpis:
        for key, value in data.workforce_kpis.model_dump(exclude_none=True).items():
            updates[key] = value
    if data.payment_practices:
        for key, value in data.payment_practices.model_dump(exclude_none=True).items():
            updates[key] = value
    if data.governance:
        for key, value in data.governance.model_dump(exclude_none=True).items():
            updates[key] = value

    _dict_to_model(settings, updates)
    db.commit()
    db.refresh(settings)

    logger.info(
        "Company context settings updated for company %s",
        current_user.company_id,
    )

    return settings


@router.patch("/company-context", response_model=CompanyContextSettingsResponse)
def patch_company_context(
    data: CompanyContextSettingsSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Partially update company context settings (only provided fields)."""
    settings = db.query(CompanyContextSettings).filter(
        CompanyContextSettings.company_id == current_user.company_id
    ).first()

    if not settings:
        settings = CompanyContextSettings(
            company_id=current_user.company_id,
        )
        db.add(settings)

    # Flatten the nested schema into the model, only updating provided fields
    updates = {}
    if data.company_profile:
        updates.update(data.company_profile.model_dump(exclude_none=True))
    if data.ghg_emissions:
        updates.update(data.ghg_emissions.model_dump(exclude_none=True))
    if data.supply_chain:
        updates.update(data.supply_chain.model_dump(exclude_none=True))
    if data.workforce_kpis:
        updates.update(data.workforce_kpis.model_dump(exclude_none=True))
    if data.payment_practices:
        updates.update(data.payment_practices.model_dump(exclude_none=True))
    if data.governance:
        updates.update(data.governance.model_dump(exclude_none=True))

    _dict_to_model(settings, updates)
    db.commit()
    db.refresh(settings)

    logger.info(
        "Company context settings partially updated for company %s",
        current_user.company_id,
    )

    return settings


@router.delete("/company-context", status_code=204)
def delete_company_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete company context settings (reset to empty)."""
    settings = db.query(CompanyContextSettings).filter(
        CompanyContextSettings.company_id == current_user.company_id
    ).first()

    if settings:
        db.delete(settings)
        db.commit()
        logger.info(
            "Company context settings deleted for company %s",
            current_user.company_id,
        )

    return None
