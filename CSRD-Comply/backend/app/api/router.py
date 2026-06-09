"""CSRD Comply — API Router aggregation."""
from fastapi import APIRouter
from app.api import (
    auth, companies, assessment, emissions, reports, ai,
    subscriptions, stripe, emails, admin, dashboard,
)

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(companies.router, prefix="/companies", tags=["companies"])
router.include_router(assessment.router, prefix="/assessment", tags=["assessment"])
router.include_router(emissions.router, prefix="/emissions", tags=["emissions"])
router.include_router(reports.router, prefix="/reports", tags=["reports"])
router.include_router(ai.router, prefix="/ai", tags=["ai"])
router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
router.include_router(stripe.router, prefix="/stripe", tags=["stripe"])
router.include_router(emails.router, prefix="/emails", tags=["emails"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
