"""
CSRD Comply — Stripe Payment Integration.

Handles:
- Creating Stripe Checkout Sessions for subscription plans
- Stripe webhook events (checkout.session.completed, invoice.*)
- Mapping Stripe products/plans to CSRD Comply subscription tiers
- Manual invoice fallback for early clients (<10 clients)

Environment variables required:
- STRIPE_SECRET_KEY: sk_live_xxx or sk_test_xxx
- STRIPE_WEBHOOK_SECRET: whsec_xxx for webhook signature verification
- STRIPE_PRICE_FREE: price_id for Free plan
- STRIPE_PRICE_PRO: price_id for Pro plan
- STRIPE_PRICE_TEAM: price_id for Team plan
- STRIPE_PRICE_ENTERPRISE: price_id for Enterprise plan
"""
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.config import settings
from app.models import User, Subscription, Company
from app.core.subscriptions import (
    SubscriptionService, PlanTier, SubscriptionStatus,
    BillingCycle, SubscriptionInfo, PLAN_CONFIG,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Try to import Stripe — it may not be installed yet for early clients
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("Stripe library not installed. Install with: pip install stripe")


# ── Schemas ──────────────────────────────────────────────────

class CreateCheckoutRequest(BaseModel):
    """Request to create a Stripe Checkout Session."""
    plan: str  # free, pro, team, enterprise
    billing_cycle: str = "monthly"  # monthly, yearly
    success_url: str = ""
    cancel_url: str = ""


class CreateBillingPortalRequest(BaseModel):
    """Request to create a Stripe Customer Portal session."""
    return_url: str = ""


class InvoiceRequest(BaseModel):
    """Manual invoice creation for early clients."""
    plan: str
    billing_cycle: str = "monthly"
    notes: str = ""


# ── Helper Functions ─────────────────────────────────────────

def _get_stripe_price_id(plan: PlanTier, billing_cycle: BillingCycle) -> Optional[str]:
    """Get Stripe Price ID for a plan and billing cycle."""
    mapping = {
        PlanTier.FREE: settings.STRIPE_PRICE_FREE,
        PlanTier.PRO: settings.STRIPE_PRICE_PRO,
        PlanTier.TEAM: settings.STRIPE_PRICE_TEAM,
        PlanTier.ENTERPRISE: settings.STRIPE_PRICE_ENTERPRISE,
    }
    return mapping.get(plan)


def _get_stripe_customer(
    company: Company,
    subscription: Optional[Subscription] = None,
) -> Optional[str]:
    """Get or create a Stripe Customer for a company."""
    if not STRIPE_AVAILABLE:
        return None

    # If subscription already has a Stripe customer ID, return it
    if subscription and subscription.stripe_customer_id:
        return subscription.stripe_customer_id

    try:
        # Search for existing customer by email
        existing = stripe.Customer.list(
            email=company.email or f"company-{company.company_id}@placeholder.com",
            limit=1,
        )
        if existing.data:
            customer = existing.data[0]
        else:
            # Create new customer
            customer = stripe.Customer.create(
                name=company.company_name,
                email=company.email or None,
                metadata={
                    "company_id": str(company.company_id),
                    "company_name": company.company_name,
                },
            )
        return customer.id
    except Exception as e:
        logger.error(f"Stripe customer error: {e}")
        return None


# ── Endpoints ────────────────────────────────────────────────

@router.post("/create-checkout-session")
def create_checkout_session(
    data: CreateCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a Stripe Checkout Session for subscription payment.
    Falls back to manual invoice info if Stripe is not configured.
    """
    if not STRIPE_AVAILABLE:
        return {
            "status": "manual_invoice",
            "message": "Stripe not configured. A manual invoice will be generated.",
            "plan": data.plan,
            "billing_cycle": data.billing_cycle,
            "contact": "billing@csrdcomply.io",
        }

    # Validate plan
    try:
        plan_tier = PlanTier(data.plan.lower())
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"Invalid plan: {data.plan}")
    
    try:
        billing_cycle = BillingCycle(data.billing_cycle.lower())
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"Invalid billing cycle: {data.billing_cycle}")

    # Free plan doesn't need checkout
    if plan_tier == PlanTier.FREE:
        return {
            "status": "free",
            "message": "Free plan is automatically activated.",
            "plan": "free",
        }

    company = current_user.company
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    subscription = db.query(Subscription).filter(
        Subscription.company_id == company.company_id,
    ).first()

    # Get or create Stripe customer
    customer_id = _get_stripe_customer(company, subscription)
    if not customer_id:
        # Fallback to manual
        return {
            "status": "manual_invoice",
            "message": "Unable to create Stripe customer. A manual invoice will be generated.",
            "plan": data.plan,
            "contact": "billing@csrdcomply.io",
        }

    # Save Stripe customer ID
    if subscription:
        subscription.stripe_customer_id = customer_id
        db.commit()

    # Get price ID from settings
    price_id = _get_stripe_price_id(plan_tier, billing_cycle)
    if not price_id:
        # Generic fallback: try to look up price by plan metadata
        try:
            prices = stripe.Price.list(
                active=True,
                limit=100,
            )
            for price in prices.data:
                metadata = price.get("metadata", {})
                if metadata.get("plan") == data.plan and metadata.get("billing_cycle") == data.billing_cycle:
                    price_id = price.id
                    break
        except Exception as e:
            logger.warning(f"Stripe price lookup error: {e}")

    if not price_id:
        # No price configured — return manual invoice info
        plan_config = PLAN_CONFIG.get(plan_tier, {})
        return {
            "status": "manual_invoice",
            "message": "Stripe price not configured for this plan. Contact billing@csrdcomply.io for a manual invoice.",
            "plan": data.plan,
            "price_monthly": plan_config.get("price_month", 0),
            "price_yearly": plan_config.get("price_year", 0),
            "contact": "billing@csrdcomply.io",
        }

    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=data.success_url or f"https://{settings.DEPLOYMENT_DOMAIN}/dashboard?checkout=success",
            cancel_url=data.cancel_url or f"https://{settings.DEPLOYMENT_DOMAIN}/pricing?checkout=canceled",
            metadata={
                "company_id": str(company.company_id),
                "plan": data.plan,
                "billing_cycle": data.billing_cycle,
            },
            subscription_data={
                "metadata": {
                    "company_id": str(company.company_id),
                    "plan": data.plan,
                },
            },
        )

        logger.info(f"Stripe checkout session created: {session.id} for company {company.company_id}")
        return {
            "status": "checkout_created",
            "session_id": session.id,
            "url": session.url,
            "plan": data.plan,
        }

    except Exception as e:
        logger.error(f"Stripe checkout session error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")


@router.post("/create-billing-portal")
def create_billing_portal(
    data: CreateBillingPortalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a Stripe Customer Portal session for managing subscription.
    """
    if not STRIPE_AVAILABLE:
        return {
            "status": "unavailable",
            "message": "Stripe not configured. Contact billing@csrdcomply.io for billing changes.",
        }

    company = current_user.company
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    subscription = db.query(Subscription).filter(
        Subscription.company_id == company.company_id,
    ).first()

    if not subscription or not subscription.stripe_customer_id:
        raise HTTPException(status_code=404, detail="No Stripe customer found. Subscribe first.")

    try:
        session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=data.return_url or f"https://{settings.DEPLOYMENT_DOMAIN}/settings/billing",
        )
        return {"status": "portal_created", "url": session.url}
    except Exception as e:
        logger.error(f"Stripe billing portal error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create billing portal: {str(e)}")


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Stripe webhook events.
    
    Events handled:
    - checkout.session.completed: Subscription created
    - invoice.paid: Subscription renewed
    - invoice.payment_failed: Payment issue
    - customer.subscription.updated: Plan change
    - customer.subscription.deleted: Cancellation
    """
    if not STRIPE_AVAILABLE:
        return {"status": "ignored", "message": "Stripe not configured"}

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event.type
    data = event.data.object

    logger.info(f"Stripe webhook received: {event_type}")

    try:
        if event_type == "checkout.session.completed":
            await _handle_checkout_completed(data, db)
        elif event_type == "invoice.paid":
            await _handle_invoice_paid(data, db)
        elif event_type == "invoice.payment_failed":
            await _handle_payment_failed(data, db)
        elif event_type == "customer.subscription.updated":
            await _handle_subscription_updated(data, db)
        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(data, db)
        else:
            logger.info(f"Unhandled webhook event: {event_type}")
    except Exception as e:
        logger.error(f"Webhook handler error for {event_type}: {e}", exc_info=True)
        # Don't raise — Stripe will retry; log and return 200 to acknowledge receipt

    return {"status": "received", "event_type": event_type}


async def _handle_checkout_completed(data: Any, db: Session) -> None:
    """Handle checkout.session.completed — activate subscription."""
    metadata = data.get("metadata", {})
    company_id = metadata.get("company_id")
    plan_str = metadata.get("plan", "pro")

    if not company_id:
        logger.error("No company_id in checkout metadata")
        return

    # Map plan string to PlanTier
    try:
        plan = PlanTier(plan_str.lower())
    except (ValueError, AttributeError):
        plan = PlanTier.PRO

    # Map billing cycle from subscription
    subscription_data = data.get("subscription", {})
    if isinstance(subscription_data, str):
        # Expand subscription object
        try:
            subscription_data = stripe.Subscription.retrieve(subscription_data)
        except Exception:
            subscription_data = {}

    interval = "monthly"
    if hasattr(subscription_data, "items"):
        items = subscription_data.items.data if subscription_data.items else []
        if items:
            price = items[0].price
            interval = price.recurring.interval if price.recurring else "month"

    billing_cycle = BillingCycle.YEARLY if interval == "year" else BillingCycle.MONTHLY

    # Update local subscription
    subscription = db.query(Subscription).filter(
        Subscription.company_id == company_id,
    ).first()

    now = datetime.utcnow()
    period_end = date(now.year + 1, now.month, now.day) if billing_cycle == BillingCycle.YEARLY else date(now.year, now.month + 1, now.day)

    if subscription:
        subscription.plan = plan
        subscription.is_active = True
        subscription.stripe_subscription_id = data.get("subscription", "")
        subscription.stripe_customer_id = data.get("customer", subscription.stripe_customer_id)
        subscription.current_period_start = now.date()
        subscription.current_period_end = period_end
        subscription.billing_cycle = billing_cycle.value
    else:
        subscription = Subscription(
            company_id=company_id,
            plan=plan,
            is_active=True,
            billing_cycle=billing_cycle.value,
            current_period_start=now.date(),
            current_period_end=period_end,
            stripe_customer_id=data.get("customer", ""),
            stripe_subscription_id=data.get("subscription", ""),
            auto_renew=True,
        )
        db.add(subscription)

    db.commit()
    logger.info(f"Subscription activated for company {company_id}: {plan.value}")


async def _handle_invoice_paid(data: Any, db: Session) -> None:
    """Handle invoice.paid — confirm subscription is active."""
    subscription_id = data.get("subscription")
    if not subscription_id:
        return

    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription_id,
    ).first()

    if subscription:
        subscription.is_active = True
        db.commit()
        logger.info(f"Invoice paid for subscription {subscription_id}")


async def _handle_payment_failed(data: Any, db: Session) -> None:
    """Handle invoice.payment_failed — warn about payment issue."""
    subscription_id = data.get("subscription")
    if not subscription_id:
        return

    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription_id,
    ).first()

    if subscription:
        logger.warning(f"Payment failed for company {subscription.company_id}")
        # Don't deactivate immediately — Stripe will retry


async def _handle_subscription_updated(data: Any, db: Session) -> None:
    """Handle customer.subscription.updated — sync plan changes."""
    subscription_id = data.get("id")
    if not subscription_id:
        return

    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription_id,
    ).first()

    if subscription:
        status = data.get("status", "")
        if status == "active":
            subscription.is_active = True
        elif status in ("past_due", "unpaid"):
            subscription.is_active = False

        # Update periods
        current_period_start = data.get("current_period_start")
        current_period_end = data.get("current_period_end")
        if current_period_start:
            subscription.current_period_start = datetime.fromtimestamp(current_period_start).date()
        if current_period_end:
            subscription.current_period_end = datetime.fromtimestamp(current_period_end).date()

        db.commit()
        logger.info(f"Subscription updated for {subscription_id}, status={status}")


async def _handle_subscription_deleted(data: Any, db: Session) -> None:
    """Handle customer.subscription.deleted — cancel subscription."""
    subscription_id = data.get("id")
    if not subscription_id:
        return

    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription_id,
    ).first()

    if subscription:
        subscription.is_active = False
        subscription.auto_renew = False
        subscription.canceled_at = datetime.utcnow()
        db.commit()
        logger.info(f"Subscription canceled: {subscription_id}")


# ── Manual Invoice (for early clients) ───────────────────────

@router.post("/manual-invoice")
def create_manual_invoice(
    data: InvoiceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a manual invoice reference for early clients (<10 clients).
    
    This generates a placeholder that will be replaced by Stripe automation
    once the payment integration is fully set up.
    """
    company = current_user.company
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    try:
        plan = PlanTier(data.plan.lower())
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"Invalid plan: {data.plan}")

    plan_config = PLAN_CONFIG.get(plan, {})
    price = plan_config.get("price_month", 0) if data.billing_cycle == "monthly" else plan_config.get("price_year", 0)

    invoice_data = {
        "company_id": str(company.company_id),
        "company_name": company.company_name,
        "company_email": current_user.email,
        "plan": data.plan,
        "billing_cycle": data.billing_cycle,
        "amount": price,
        "currency": "EUR",
        "status": "pending",
        "notes": data.notes or "",
        "contact": "billing@csrdcomply.io",
        "created_at": datetime.utcnow().isoformat(),
    }

    logger.info(f"Manual invoice created for company {company.company_id}: {data.plan}")

    return {
        "status": "invoice_created",
        "message": "Manual invoice created. You will receive payment instructions via email.",
        "invoice": invoice_data,
    }


@router.get("/status")
def get_payment_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get payment integration status."""
    return {
        "stripe_configured": STRIPE_AVAILABLE and bool(settings.STRIPE_SECRET_KEY),
        "stripe_available": STRIPE_AVAILABLE,
        "stripe_prices_configured": bool(
            getattr(settings, "STRIPE_PRICE_PRO", None)
        ),
        "manual_invoice": True,
        "contact": "billing@csrdcomply.io",
    }
