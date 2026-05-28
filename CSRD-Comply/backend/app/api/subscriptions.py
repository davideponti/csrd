"""CSRD Comply — Subscription & Billing API Endpoints.

Allows:
- Listing available plans
- Getting current subscription info
- Changing plan (upgrade/downgrade)
- Viewing usage limits
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime
from decimal import Decimal

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.multitenancy import get_current_company
from app.core.subscriptions import (
    SubscriptionService,
    SubscriptionInfo,
    SubscriptionCreate,
    SubscriptionUpdate,
    PlanInfo,
    PlanTier,
    SubscriptionStatus,
    BillingCycle,
    UsageTracker,
    PLAN_CONFIG,
)
from app.models import User, Subscription, Company

router = APIRouter()


# ── Endpoints ───────────────────────────────────────────────────

@router.get("/plans", response_model=List[PlanInfo])
def list_plans():
    """List all available subscription plans with pricing and features."""
    return SubscriptionService.list_plans()


@router.get("/plans/{plan_tier}", response_model=PlanInfo)
def get_plan(plan_tier: str):
    """Get details for a specific plan tier."""
    try:
        tier = PlanTier(plan_tier.lower())
    except (ValueError, AttributeError):
        raise HTTPException(status_code=404, detail=f"Plan '{plan_tier}' not found")
    plan = SubscriptionService.get_plan_info(tier)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan '{plan_tier}' not found")
    return plan


@router.get("/current", response_model=SubscriptionInfo)
def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current subscription for the user's company."""
    company = current_user.company
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    subscription = db.query(Subscription).filter(
        Subscription.company_id == company.company_id
    ).first()

    if not subscription:
        # Return default free subscription
        today = date.today()
        return SubscriptionInfo(
            id="free",
            company_id=str(company.company_id),
            plan=PlanTier.FREE,
            status=SubscriptionStatus.ACTIVE,
            billing_cycle=BillingCycle.MONTHLY,
            current_period_start=today,
            current_period_end=date(today.year + 10, today.month, today.day),
            trial_end=None,
            auto_renew=True,
        )

    return SubscriptionInfo(
        id=str(subscription.id),
        company_id=str(subscription.company_id),
        plan=subscription.plan,
        status=SubscriptionStatus(subscription.status) if isinstance(subscription.status, str) else subscription.status,
        billing_cycle=subscription.billing_cycle,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        trial_end=subscription.trial_end,
        canceled_at=subscription.canceled_at,
        auto_renew=subscription.auto_renew,
    )


@router.post("/subscribe", response_model=SubscriptionInfo)
def create_subscription(
    data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or upgrade a subscription."""
    company = current_user.company
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Check existing subscription
    existing = db.query(Subscription).filter(
        Subscription.company_id == company.company_id
    ).first()

    if existing:
        # Upgrade existing subscription
        if not SubscriptionService.can_upgrade(existing.plan, data.plan):
            raise HTTPException(
                status_code=400,
                detail="Downgrade requires confirmation. Use PATCH endpoint instead.",
            )
        
        # Validate target plan exists
        target_config = PLAN_CONFIG.get(data.plan)
        if not target_config:
            raise HTTPException(status_code=400, detail=f"Invalid plan: {data.plan}")

        existing.plan = data.plan
        existing.billing_cycle = data.billing_cycle.value if hasattr(data.billing_cycle, 'value') else data.billing_cycle
        existing.is_active = True
        
        # Calculate new period
        period_start, period_end, _ = SubscriptionService.get_subscription_dates(
            data.billing_cycle
        )
        existing.current_period_start = period_start
        existing.current_period_end = period_end
        
        db.commit()
        db.refresh(existing)

        return SubscriptionInfo(
            id=str(existing.id),
            company_id=str(existing.company_id),
            plan=existing.plan,
            status=SubscriptionStatus.ACTIVE,
            billing_cycle=existing.billing_cycle,
            current_period_start=existing.current_period_start,
            current_period_end=existing.current_period_end,
            trial_end=existing.trial_end,
            canceled_at=existing.canceled_at,
            auto_renew=existing.auto_renew,
        )

    # Create new subscription
    period_start, period_end, trial_end = SubscriptionService.get_subscription_dates(
        data.billing_cycle
    )

    subscription = Subscription(
        company_id=company.company_id,
        plan=data.plan,
        is_active=True,
        billing_cycle=data.billing_cycle.value if hasattr(data.billing_cycle, 'value') else data.billing_cycle,
        current_period_start=period_start,
        current_period_end=period_end,
        trial_end=trial_end,
        auto_renew=True,
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return SubscriptionInfo(
        id=str(subscription.id),
        company_id=str(subscription.company_id),
        plan=subscription.plan,
        status=SubscriptionStatus.ACTIVE if subscription.is_active else SubscriptionStatus.PENDING,
        billing_cycle=subscription.billing_cycle,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        trial_end=subscription.trial_end,
        canceled_at=subscription.canceled_at,
        auto_renew=subscription.auto_renew,
    )


@router.patch("/current", response_model=SubscriptionInfo)
def update_subscription(
    data: SubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current subscription (change plan, billing cycle, auto-renew)."""
    company = current_user.company
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    subscription = db.query(Subscription).filter(
        Subscription.company_id == company.company_id
    ).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")

    # Update fields
    if data.plan is not None:
        subscription.plan = data.plan
    if data.billing_cycle is not None:
        subscription.billing_cycle = data.billing_cycle.value if hasattr(data.billing_cycle, 'value') else data.billing_cycle
    if data.auto_renew is not None:
        subscription.auto_renew = data.auto_renew

    db.commit()
    db.refresh(subscription)

    return SubscriptionInfo(
        id=str(subscription.id),
        company_id=str(subscription.company_id),
        plan=subscription.plan,
        status=SubscriptionStatus.ACTIVE if subscription.is_active else SubscriptionStatus.PENDING,
        billing_cycle=subscription.billing_cycle,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        trial_end=subscription.trial_end,
        canceled_at=subscription.canceled_at,
        auto_renew=subscription.auto_renew,
    )


@router.post("/cancel")
def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel subscription. It will remain active until period end."""
    company = current_user.company
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    subscription = db.query(Subscription).filter(
        Subscription.company_id == company.company_id
    ).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")

    subscription.is_active = False
    subscription.auto_renew = False
    subscription.canceled_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Subscription canceled successfully. Access remains until period end.",
        "access_until": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
    }


@router.post("/reactivate")
def reactivate_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reactivate a canceled subscription."""
    company = current_user.company
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    subscription = db.query(Subscription).filter(
        Subscription.company_id == company.company_id
    ).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found")

    if subscription.is_active:
        raise HTTPException(status_code=400, detail="Subscription is not canceled")

    subscription.is_active = True
    subscription.auto_renew = True
    subscription.canceled_at = None

    db.commit()

    return {"message": "Subscription reactivated successfully."}


@router.get("/usage")
def get_usage_limits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current usage and limits for the company."""
    company = current_user.company
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    subscription = db.query(Subscription).filter(
        Subscription.company_id == company.company_id
    ).first()

    plan = subscription.plan if subscription else PlanTier.FREE
    plan_config = PLAN_CONFIG.get(plan, PLAN_CONFIG[PlanTier.FREE])

    tracker = UsageTracker(db)
    
    current_year = date.today().year
    
    report_count = tracker.get_report_count(str(company.company_id), current_year)
    user_count = tracker.get_user_count(str(company.company_id))
    storage_mb = tracker.get_storage_usage(str(company.company_id))

    limits = plan_config["limits"]
    max_reports = plan_config["max_reports_per_year"]
    max_users = plan_config["max_users"]
    max_storage = limits["storage_mb"]

    return {
        "plan": plan.value,
        "plan_name": plan_config["name"],
        "usage": {
            "reports": {
                "current": report_count,
                "limit": max_reports,
                "remaining": max(0, max_reports - report_count),
                "percentage": round((report_count / max_reports) * 100, 1) if max_reports > 0 else 0,
            },
            "users": {
                "current": user_count,
                "limit": max_users,
                "remaining": max(0, max_users - user_count),
                "percentage": round((user_count / max_users) * 100, 1) if max_users > 0 else 0,
            },
            "storage": {
                "current_mb": storage_mb,
                "limit_mb": max_storage,
                "remaining_mb": max(0, max_storage - storage_mb),
                "percentage": round((storage_mb / max_storage) * 100, 1) if max_storage > 0 else 0,
            },
        },
        "features": plan_config["features"],
        "upgrade_options": [
            p.dict() for p in SubscriptionService.get_upgrade_path(plan)
        ],
    }


@router.get("/features")
def check_features(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check which features are available for the current plan."""
    company = current_user.company
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    subscription = db.query(Subscription).filter(
        Subscription.company_id == company.company_id
    ).first()

    plan = subscription.plan if subscription else PlanTier.FREE

    return {
        "plan": plan.value,
        "features": PLAN_CONFIG.get(plan, PLAN_CONFIG[PlanTier.FREE])["features"],
    }
