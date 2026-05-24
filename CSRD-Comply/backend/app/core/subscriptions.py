"""CSRD Comply — Subscriptions Model & Billing Utilities.

Gestisce piani di abbonamento, fatturazione e limiti di utilizzo
per il modello SaaS multitenant.

Piani disponibili:
  - Free:    1 utente, 1 report/anno, no AI
  - Pro:     3 utenti, 10 report/anno, AI base, iXBRL
  - Team:    10 utenti, report illimitati, AI avanzata
  - Enterprise: utenti illimitati, tutto incluso, white-label
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List
from enum import Enum
import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ── Enums ───────────────────────────────────────────────────────

class PlanTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"
    PENDING = "pending"


class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"


# ── Plan Configuration ──────────────────────────────────────────

PLAN_CONFIG: Dict[PlanTier, Dict[str, Any]] = {
    PlanTier.FREE: {
        "name": "Free",
        "description": "Per micro-imprese che iniziano il percorso CSRD",
        "price_monthly": Decimal("0.00"),
        "price_yearly": Decimal("0.00"),
        "max_users": 1,
        "max_reports_per_year": 1,
        "max_companies": 1,
        "features": {
            "basic_assessment": True,
            "materiality_matrix": True,
            "emissions_tracking": True,
            "ai_assistant": False,
            "ixbrl_filing": False,
            "regulatory_intelligence": False,
            "multi_user": False,
            "api_access": False,
            "custom_branding": False,
            "priority_support": False,
            "csv_export": True,
            "pdf_export": True,
            "gap_analysis_basic": True,
            "gap_analysis_advanced": False,
        },
        "limits": {
            "storage_mb": 100,
            "api_calls_per_day": 0,
            "ai_queries_per_month": 0,
        },
    },
    PlanTier.PRO: {
        "name": "Pro",
        "description": "Per PMI che necessitano di reportistica completa",
        "price_monthly": Decimal("49.00"),
        "price_yearly": Decimal("499.00"),
        "max_users": 3,
        "max_reports_per_year": 10,
        "max_companies": 1,
        "features": {
            "basic_assessment": True,
            "materiality_matrix": True,
            "emissions_tracking": True,
            "ai_assistant": True,
            "ixbrl_filing": True,
            "regulatory_intelligence": False,
            "multi_user": True,
            "api_access": True,
            "custom_branding": False,
            "priority_support": False,
            "csv_export": True,
            "pdf_export": True,
            "gap_analysis_basic": True,
            "gap_analysis_advanced": True,
        },
        "limits": {
            "storage_mb": 1024,
            "api_calls_per_day": 1000,
            "ai_queries_per_month": 500,
        },
    },
    PlanTier.TEAM: {
        "name": "Team",
        "description": "Per team che collaborano sulla conformità ESG",
        "price_monthly": Decimal("149.00"),
        "price_yearly": Decimal("1499.00"),
        "max_users": 10,
        "max_reports_per_year": 999,
        "max_companies": 1,
        "features": {
            "basic_assessment": True,
            "materiality_matrix": True,
            "emissions_tracking": True,
            "ai_assistant": True,
            "ixbrl_filing": True,
            "regulatory_intelligence": True,
            "multi_user": True,
            "api_access": True,
            "custom_branding": False,
            "priority_support": True,
            "csv_export": True,
            "pdf_export": True,
            "gap_analysis_basic": True,
            "gap_analysis_advanced": True,
        },
        "limits": {
            "storage_mb": 5120,
            "api_calls_per_day": 5000,
            "ai_queries_per_month": 2000,
        },
    },
    PlanTier.ENTERPRISE: {
        "name": "Enterprise",
        "description": "Soluzione completa per grandi aziende e consulenti",
        "price_monthly": Decimal("499.00"),
        "price_yearly": Decimal("4999.00"),
        "max_users": 999,
        "max_reports_per_year": 9999,
        "max_companies": 10,
        "features": {
            "basic_assessment": True,
            "materiality_matrix": True,
            "emissions_tracking": True,
            "ai_assistant": True,
            "ixbrl_filing": True,
            "regulatory_intelligence": True,
            "multi_user": True,
            "api_access": True,
            "custom_branding": True,
            "priority_support": True,
            "csv_export": True,
            "pdf_export": True,
            "gap_analysis_basic": True,
            "gap_analysis_advanced": True,
        },
        "limits": {
            "storage_mb": 51200,
            "api_calls_per_day": 50000,
            "ai_queries_per_month": 10000,
        },
    },
}


# ── Pydantic Schemas ────────────────────────────────────────────

class PlanInfo(BaseModel):
    tier: PlanTier
    name: str
    description: str
    price_monthly: float
    price_yearly: float
    max_users: int
    max_reports_per_year: int
    max_companies: int
    features: Dict[str, bool]
    limits: Dict[str, int]


class SubscriptionInfo(BaseModel):
    id: str
    company_id: str
    plan: PlanTier
    status: SubscriptionStatus
    billing_cycle: BillingCycle
    current_period_start: date
    current_period_end: date
    trial_end: Optional[date] = None
    canceled_at: Optional[datetime] = None
    auto_renew: bool = True


class SubscriptionCreate(BaseModel):
    plan: PlanTier
    billing_cycle: BillingCycle = BillingCycle.MONTHLY


class SubscriptionUpdate(BaseModel):
    plan: Optional[PlanTier] = None
    billing_cycle: Optional[BillingCycle] = None
    auto_renew: Optional[bool] = None


# ── Service ─────────────────────────────────────────────────────

class SubscriptionService:
    """Business logic for subscription management."""

    @staticmethod
    def get_plan_info(tier: PlanTier) -> Optional[PlanInfo]:
        """Get full plan configuration."""
        config = PLAN_CONFIG.get(tier)
        if not config:
            return None
        return PlanInfo(
            tier=tier,
            name=config["name"],
            description=config["description"],
            price_monthly=float(config["price_monthly"]),
            price_yearly=float(config["price_yearly"]),
            max_users=config["max_users"],
            max_reports_per_year=config["max_reports_per_year"],
            max_companies=config["max_companies"],
            features=config["features"],
            limits=config["limits"],
        )

    @staticmethod
    def list_plans() -> List[PlanInfo]:
        """List all available plans."""
        return [
            SubscriptionService.get_plan_info(tier)
            for tier in PlanTier
        ]

    @staticmethod
    def check_feature_access(
        plan: PlanTier,
        feature: str,
    ) -> bool:
        """Check if a plan has access to a specific feature."""
        config = PLAN_CONFIG.get(plan)
        if not config:
            return False
        return config.get("features", {}).get(feature, False)

    @staticmethod
    def check_usage_limit(
        plan: PlanTier,
        limit_name: str,
        current_usage: int,
    ) -> tuple[bool, int]:
        """Check if usage is within plan limits.
        
        Returns:
            Tuple of (is_within_limit, max_allowed)
        """
        config = PLAN_CONFIG.get(plan)
        if not config:
            return False, 0
        
        max_allowed = config.get("limits", {}).get(limit_name, 0)
        return current_usage < max_allowed, max_allowed

    @staticmethod
    def get_subscription_dates(
        billing_cycle: BillingCycle,
        trial_days: int = 14,
    ) -> tuple[date, date, Optional[date]]:
        """Calculate subscription period dates.
        
        Returns:
            Tuple of (period_start, period_end, trial_end)
        """
        today = date.today()
        
        if billing_cycle == BillingCycle.MONTHLY:
            period_end = today + timedelta(days=30)
        elif billing_cycle == BillingCycle.YEARLY:
            period_end = today + timedelta(days=365)
        else:  # LIFETIME
            period_end = date(2099, 12, 31)
        
        trial_end = today + timedelta(days=trial_days) if trial_days > 0 else None
        
        return today, period_end, trial_end

    @staticmethod
    def can_upgrade(current_plan: PlanTier, target_plan: PlanTier) -> bool:
        """Check if a plan upgrade is valid.
        
        Upgrades: free -> pro -> team -> enterprise
        Downgrades are allowed but with feature loss warnings.
        """
        tiers = list(PlanTier)
        current_idx = tiers.index(current_plan)
        target_idx = tiers.index(target_plan)
        
        # Allow upgrade or same tier
        if target_idx >= current_idx:
            return True
        
        return False  # Downgrade needs explicit confirmation

    @staticmethod
    def get_upgrade_path(current_plan: PlanTier) -> List[PlanInfo]:
        """Get available upgrade options from current plan."""
        tiers = list(PlanTier)
        current_idx = tiers.index(current_plan)
        
        available = []
        for i in range(current_idx + 1, len(tiers)):
            info = SubscriptionService.get_plan_info(tiers[i])
            if info:
                available.append(info)
        
        return available

    @staticmethod
    def calculate_prorated_amount(
        current_plan: PlanTier,
        target_plan: PlanTier,
        days_remaining_in_period: int,
        total_period_days: int = 30,
    ) -> Decimal:
        """Calculate prorated amount for plan upgrade."""
        current_price = PLAN_CONFIG[current_plan]["price_monthly"]
        target_price = PLAN_CONFIG[target_plan]["price_monthly"]
        
        if current_price >= target_price:
            return Decimal("0.00")
        
        daily_rate = (target_price - current_price) / Decimal(str(total_period_days))
        return daily_rate * Decimal(str(days_remaining_in_period))

    @staticmethod
    def format_price(amount: Decimal, currency: str = "EUR") -> str:
        """Format price for display."""
        if currency == "EUR":
            return f"€{amount:.2f}"
        return f"{currency} {amount:.2f}"


# ── Usage Tracking ──────────────────────────────────────────────

class UsageTracker:
    """Track and enforce usage limits per tenant."""

    def __init__(self, db_session):
        self.db = db_session

    def get_report_count(self, company_id: str, year: int) -> int:
        """Count reports generated by a company in a year."""
        from app.models import Report
        return self.db.query(Report).filter(
            Report.company_id == company_id,
            Report.reporting_year == year,
        ).count()

    def get_user_count(self, company_id: str) -> int:
        """Count active users in a company."""
        from app.models import User
        return self.db.query(User).filter(
            User.company_id == company_id,
            User.is_active == True,
        ).count()

    def get_storage_usage(self, company_id: str) -> int:
        """Get total storage usage in MB for a company."""
        from app.models import Report, Assessment
        # Sum report storage
        report_size = self.db.query(Report).filter(
            Report.company_id == company_id
        ).with_entities(
            # Approximate: count * avg size per report
        ).count() * 5  # ~5MB per report avg
        
        assessment_size = self.db.query(Assessment).filter(
            Assessment.company_id == company_id
        ).count() * 2  # ~2MB per assessment avg
        
        return report_size + assessment_size
