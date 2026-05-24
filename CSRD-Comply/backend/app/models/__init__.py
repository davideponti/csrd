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

    company = relationship("Company")

# Alias per compatibilità
Assessment = MaterialityAssessment
EmissionData = EmissionsData
