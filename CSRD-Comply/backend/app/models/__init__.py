"""
CSRD Comply — Database Models (SQLAlchemy)

All entities for CSRD/ESG compliance management.
"""
import uuid
from datetime import date, datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, Date, DateTime,
    ForeignKey, JSON, Enum as SAEnum, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


# ── Mixin ──────────────────────────────────────────────────────
class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)


# ── Companies ──────────────────────────────────────────────────
class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    company_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(255), nullable=False)
    vat_number = Column(String(50), nullable=True, unique=True)
    country = Column(String(5), nullable=False)
    sector = Column(String(10), nullable=False)          # NACE code (e.g. "C10")
    employee_count = Column(Integer, nullable=True)
    turnover = Column(Float, nullable=True)
    balance_sheet_total = Column(Float, nullable=True)
    csrd_wave = Column(Integer, nullable=False, default=3)   # 1=2025, 2=2026, 3=2027
    reporting_year = Column(Integer, nullable=False)

    users = relationship("User", back_populates="company")
    context = relationship("CompanyContext", uselist=False, back_populates="company")
    assessments = relationship("MaterialityAssessment", back_populates="company")
    emissions = relationship("EmissionsData", back_populates="company")
    reports = relationship("Report", back_populates="company")


# ── Users ──────────────────────────────────────────────────────
class UserRole(str, enum.Enum):
    admin = "admin"
    contributor = "contributor"
    viewer = "viewer"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.company_id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.contributor, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    token_version = Column(Integer, default=0, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    otp_code = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    otp_attempts = Column(Integer, default=0, nullable=False)
    reset_password_token = Column(String(255), nullable=True)
    reset_password_expires_at = Column(DateTime, nullable=True)

    company = relationship("Company", back_populates="users")


# ── Company Context (Double Materiality) ────────────────────────
class CompanyContext(TimestampMixin, Base):
    __tablename__ = "company_context"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.company_id"),
                        unique=True, nullable=False)
    value_chain_description = Column(Text, nullable=True)
    key_activities = Column(JSON, nullable=True)             # list of main activities
    business_relationships = Column(JSON, nullable=True)     # suppliers, customers, partners
    geographical_scope = Column(JSON, nullable=True)         # operating countries
    stakeholder_groups = Column(JSON, nullable=True)         # stakeholder mapping

    company = relationship("Company", back_populates="context")


# ── Company Context Settings (CSRD Reporting Data) ──────────────
class CompanyContextSettings(TimestampMixin, Base):
    """
    Comprehensive company context data that gets automatically injected
    into every report generation prompt to replace [TO BE CONFIRMED]
    placeholders with real company data wherever possible.

    All fields are optional. When empty, [TO BE CONFIRMED] remains.
    """
    __tablename__ = "company_context_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.company_id"),
                        unique=True, nullable=False)

    # ── COMPANY PROFILE ─────────────────────────────────────────
    company_name = Column(String(255), nullable=True)
    country = Column(String(255), nullable=True)
    sector = Column(String(255), nullable=True)
    reporting_year = Column(Integer, nullable=True)
    employee_count_total = Column(Integer, nullable=True)
    employee_count_permanent = Column(Integer, nullable=True)
    employee_count_temporary = Column(Integer, nullable=True)
    employee_count_male = Column(Integer, nullable=True)
    employee_count_female = Column(Integer, nullable=True)
    employee_count_other = Column(Integer, nullable=True)
    employee_count_by_geography = Column(JSON, nullable=True)  # {"Italy": 50, "Germany": 30}
    annual_revenue_eur = Column(Float, nullable=True)
    operational_sites_count = Column(Integer, nullable=True)

    # ── GHG EMISSIONS ───────────────────────────────────────────
    scope1_emissions = Column(Float, nullable=True)
    scope2_location_based = Column(Float, nullable=True)
    scope2_market_based = Column(Float, nullable=True)
    scope3_total = Column(Float, nullable=True)
    scope3_material_categories = Column(JSON, nullable=True)   # ["Purchased goods", "Transportation", ...]
    emissions_baseline_year = Column(Integer, nullable=True)
    emissions_methodology = Column(String(255), nullable=True)  # GHG Protocol / ISO 14064 / other

    # ── SUPPLY CHAIN ────────────────────────────────────────────
    tier1_suppliers_count = Column(Integer, nullable=True)
    tier2_suppliers_count = Column(Integer, nullable=True)
    value_chain_countries = Column(JSON, nullable=True)        # ["Italy", "Germany", ...]
    high_risk_countries = Column(JSON, nullable=True)           # ["Country A", "Country B"]
    suppliers_code_of_conduct_pct = Column(Float, nullable=True)
    supplier_audits_last_year = Column(Integer, nullable=True)

    # ── WORKFORCE KPIs ─────────────────────────────────────────
    ltifr = Column(Float, nullable=True)                       # Lost-time injury frequency rate
    fatal_accidents = Column(Integer, nullable=True)
    voluntary_turnover_pct = Column(Float, nullable=True)
    avg_training_hours_per_year = Column(Float, nullable=True)
    women_in_management_pct = Column(Float, nullable=True)
    gender_pay_gap_pct = Column(Float, nullable=True)
    union_coverage_pct = Column(Float, nullable=True)
    employee_engagement_score = Column(Float, nullable=True)

    # ── PAYMENT PRACTICES ───────────────────────────────────────
    standard_payment_terms_days = Column(Integer, nullable=True)
    avg_actual_payment_time_days = Column(Float, nullable=True)
    invoices_paid_within_terms_pct = Column(Float, nullable=True)
    invoices_paid_late_pct = Column(Float, nullable=True)

    # ── GOVERNANCE ──────────────────────────────────────────────
    anti_corruption_training_pct = Column(Float, nullable=True)
    corruption_incidents_last_year = Column(Integer, nullable=True)
    whistleblowing_reports_received = Column(Integer, nullable=True)

    company = relationship("Company", backref="context_settings")


# ── Sustainability Matters (ESRS Topic Registry) ────────────────
class SustainabilityMatter(Base):
    __tablename__ = "sustainability_matters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    standard = Column(String(20), nullable=False, index=True)   # ESRS E1, E2, ... S1, G1
    topic_name = Column(String(255), nullable=False)
    sub_topic = Column(String(255), nullable=True)
    sub_sub_topic = Column(String(255), nullable=True)
    category = Column(String(20), nullable=False)               # environmental / social / governance
    mandatory = Column(Boolean, default=False, nullable=False)


# ── ESRS Datapoints (1.191+ individual datapoints) ──────────────
class EsrsDatapoint(Base):
    __tablename__ = "esrs_datapoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    standard_ref = Column(String(50), nullable=False, index=True)   # "ESRS E1-6"
    paragraph_ref = Column(String(50), nullable=True)               # "44(a)"
    disclosure_requirement = Column(Text, nullable=False)
    data_type = Column(String(20), nullable=False)                  # numerical/boolean/narrative/semi-narrative
    unit = Column(String(50), nullable=True)                        # tCO2eq, %, EUR, etc.
    is_mandatory = Column(Boolean, default=False, nullable=False)
    is_conditional = Column(Boolean, default=False, nullable=False)
    phase_in_year = Column(Integer, nullable=True)                  # None=always, 2026, 2027
    sfd_ref = Column(String(100), nullable=True)


# ── Materiality Assessment ──────────────────────────────────────
class AssessmentStatus(str, enum.Enum):
    draft = "draft"
    in_progress = "in_progress"
    completed = "completed"
    audited = "audited"


class MaterialityAssessment(TimestampMixin, Base):
    __tablename__ = "materiality_assessment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.company_id"), nullable=False)
    assessment_date = Column(Date, nullable=False, default=date.today)
    status = Column(SAEnum(AssessmentStatus), default=AssessmentStatus.draft, nullable=False)
    methodology_version = Column(String(20), nullable=True)

    company = relationship("Company", back_populates="assessments")
    scores = relationship("MaterialityScore", back_populates="assessment",
                          cascade="all, delete-orphan")


# ── Materiality Scores ──────────────────────────────────────────
class MaterialityScore(TimestampMixin, Base):
    __tablename__ = "materiality_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True),
                           ForeignKey("materiality_assessment.id"), nullable=False)
    datapoint_id = Column(UUID(as_uuid=True),
                          ForeignKey("esrs_datapoints.id"), nullable=False)

    # Impact dimensions (1-5)
    impact_scale = Column(Integer, nullable=True)
    impact_scope = Column(Integer, nullable=True)
    impact_irremediability = Column(Integer, nullable=True)
    impact_likelihood = Column(Integer, nullable=True)

    # Financial dimensions (1-5)
    financial_magnitude = Column(Integer, nullable=True)
    financial_likelihood = Column(Integer, nullable=True)

    # Calculated scores
    total_impact_score = Column(Float, nullable=True)
    total_financial_score = Column(Float, nullable=True)
    is_material = Column(Boolean, default=False, nullable=False)
    rationale = Column(Text, nullable=True)

    assessment = relationship("MaterialityAssessment", back_populates="scores")
    datapoint = relationship("EsrsDatapoint")


# ── Emissions Data ──────────────────────────────────────────────
class EmissionsData(TimestampMixin, Base):
    __tablename__ = "emissions_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.company_id"), nullable=False)
    reporting_year = Column(Integer, nullable=False)
    scope = Column(String(10), nullable=False)                    # 1/2/3
    category = Column(String(50), nullable=True)                  # For scope 3 sub-categories
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False, default="tCO2eq")
    calculation_method = Column(String(50), nullable=True)        # supplier_specific/spend_based/...
    emission_factor_source = Column(String(50), nullable=True)    # DEFRA, EPA, IPCC, etc.
    verified = Column(Boolean, default=False, nullable=False)
    verification_date = Column(Date, nullable=True)

    company = relationship("Company", back_populates="emissions")


# ── Company Report Context (Settings for report generation) ─────
# ── Reports ─────────────────────────────────────────────────────
class ReportStatus(str, enum.Enum):
    draft = "draft"
    review = "review"
    final = "final"
    filed = "filed"


class Report(TimestampMixin, Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.company_id"), nullable=False)
    reporting_year = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    status = Column(SAEnum(ReportStatus), default=ReportStatus.draft, nullable=False)
    table_data = Column(JSON, nullable=True)                     # Pre-computed tables/charts data
    xhtml_content = Column(Text, nullable=True)                  # Generated iXBRL report
    xbrl_validation_passed = Column(Boolean, nullable=True)
    filed_at = Column(DateTime, nullable=True)
    filed_to = Column(String(100), nullable=True)                # ESAP, national authority

    company = relationship("Company", back_populates="reports")


# ── Regulatory Updates ──────────────────────────────────────────
class RegulatoryUpdate(TimestampMixin, Base):
    __tablename__ = "regulatory_updates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    regulation = Column(String(50), nullable=False)               # CSRD, ESRS, EU Taxonomy, Omnibus
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    effective_date = Column(Date, nullable=False)
    affected_standards = Column(JSON, nullable=True)              # list of impacted ESRS
    source_url = Column(String(500), nullable=True)
    ai_summary = Column(Text, nullable=True)                      # AI-generated summary


# ── Subscriptions ───────────────────────────────────────────────
class SubscriptionTier(str, enum.Enum):
    free = "free"
    pro = "pro"
    team = "team"
    enterprise = "enterprise"

class Subscription(TimestampMixin, Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.company_id"), nullable=False, unique=True)
    tier = Column(SAEnum(SubscriptionTier), default=SubscriptionTier.free, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String(100), nullable=True)
    stripe_subscription_id = Column(String(100), nullable=True)
    # ── NEW: Subscription metadata columns (previously in-memory only) ──
    billing_cycle = Column(String(20), default="monthly", nullable=False)
    current_period_start = Column(Date, nullable=True)
    current_period_end = Column(Date, nullable=True)
    trial_end = Column(Date, nullable=True)
    canceled_at = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=True, nullable=False)

    company = relationship("Company")

    # ── Compatibility alias: API uses `plan`, DB stores `tier` ──
    @property
    def plan(self) -> SubscriptionTier:
        return self.tier

    @plan.setter
    def plan(self, value: SubscriptionTier) -> None:
        self.tier = value

    @property
    def billing_cycle_enum(self) -> str:
        return self.billing_cycle

    @billing_cycle_enum.setter
    def billing_cycle_enum(self, value: str) -> None:
        self.billing_cycle = value

    @property
    def status(self) -> str:
        return 'active' if self.is_active else 'inactive'

    @status.setter
    def status(self, value) -> None:
        if isinstance(value, str):
            self.is_active = (value == 'active' or value == 'trialing')
        else:
            # Handle SubscriptionStatus enum
            self.is_active = (value.value in ('active', 'trialing'))

# Alias per compatibilità
Assessment = MaterialityAssessment
EmissionData = EmissionsData
