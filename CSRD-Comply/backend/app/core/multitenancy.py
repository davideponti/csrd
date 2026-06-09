"""CSRD Comply — Multitenancy Middleware & Utilities.

Manages data isolation between tenants (companies) via:
- Middleware that extracts tenant_id from JWT token
- Automatic injection of company_id filter in queries
- Schema-based isolation (optional, for enterprise deployment)
"""
from contextvars import ContextVar
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import event, text
from sqlalchemy.orm import Session, joinedload
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Callable, Awaitable
import logging
import time
import re

from app.core.config import settings
from app.core.database import get_db, SessionLocal
from app.models import User, Company

logger = logging.getLogger(__name__)

# ── Tenant Context ──────────────────────────────────────────────

# ContextVar per tenant context thread-safe (ASGI-compatible)
_tenant_id_var: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)
_schema_var: ContextVar[Optional[str]] = ContextVar("schema", default=None)


class TenantContext:
    """Thread/async-safe tenant context storage.
    
    Uses contextvars for proper isolation in ASGI/async contexts.
    Populated by middleware for each request.
    Used by automatic SQLAlchemy query filters.
    """

    @classmethod
    def set(cls, tenant_id: Optional[str], schema: Optional[str] = None):
        _tenant_id_var.set(tenant_id)
        _schema_var.set(schema)

    @classmethod
    def get_tenant_id(cls) -> Optional[str]:
        return _tenant_id_var.get()

    @classmethod
    def get_schema(cls) -> Optional[str]:
        return _schema_var.get()

    @classmethod
    def clear(cls):
        _tenant_id_var.set(None)
        _schema_var.set(None)


_VALID_SCHEMA_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$')

def _validate_schema_name(schema: str) -> bool:
    """Validate that a schema name contains only safe characters."""
    return bool(_VALID_SCHEMA_RE.match(schema))


# ── Middleware ──────────────────────────────────────────────────

class MultitenancyMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts tenant context from JWT token.
    
    For each request:
    1. Extracts Bearer token from Authorization header
    2. Decodes the token to get company_id and schema
    3. Sets the TenantContext
    4. Logs request with tenant info
    5. Cleans up context after request
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable]
    ):
        # Paths that don't require tenant isolation
        public_paths = {
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/",
            "/health",
            "/docs",
            "/openapi.json",
        }
        
        tenant_id = None
        schema = None

        # Extract tenant from JWT if present
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from app.core.security import decode_token
                token = auth_header.split(" ")[1]
                payload = decode_token(token)
                if payload:
                    tenant_id = payload.get("company_id")
                    schema = payload.get("schema", "public")
            except Exception as e:
                # Do not log error content that might contain token parts
                logger.warning(f"Failed to decode token: {type(e).__name__}")
                # Do not block the request, leave context empty

        # Set tenant context for this request
        TenantContext.set(tenant_id, schema)

        # Log request with tenant info
        start_time = time.time()
        logger.info(
            f"[TENANT:{tenant_id or 'anonymous'}] "
            f"{request.method} {request.url.path}"
        )

        try:
            response = await call_next(request)
            
            # Add tenant header to response
            if tenant_id:
                response.headers["X-Tenant-ID"] = tenant_id
            
            # Log response time
            elapsed = time.time() - start_time
            logger.debug(f"Request completed in {elapsed:.3f}s")
            
            return response
        finally:
            # Always clean up tenant context
            TenantContext.clear()


# ── Automatic Query Filtering ──────────────────────────────────

def apply_tenant_filter(query, model, db_session=None):
    """Apply automatic tenant filter to a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        model: SQLAlchemy model class
        db_session: Optional session for relation loading
        
    Returns:
        Filtered query with company_id constraint
    """
    tenant_id = TenantContext.get_tenant_id()
    
    if tenant_id and hasattr(model, "company_id"):
        # Apply filter for most models
        return query.filter(model.company_id == tenant_id)
    
    return query


def get_current_company(db: Session = Depends(get_db)) -> Optional[Company]:
    """Get the current tenant's company object.
    
    Dependency to be used in endpoints that need company context.
    """
    tenant_id = TenantContext.get_tenant_id()
    if not tenant_id:
        return None
    
    return db.query(Company).filter(Company.id == tenant_id).first()


def get_tenant_db() -> Session:
    """Get a database session with tenant context pre-applied.
    
    Returns a session that can be used for tenant-isolated queries.
    """
    db = SessionLocal()
    try:
        tenant_id = TenantContext.get_tenant_id()
        if tenant_id and tenant_id != "public":
            # Set PostgreSQL schema/search_path for schema-based isolation
            # ⚠️ SECURITY: validate schema name to prevent SQL injection
            schema = TenantContext.get_schema() or f"tenant_{tenant_id[:8].replace('-', '_')}"
            if not _validate_schema_name(schema):
                logger.warning(f"Invalid schema name rejected: {schema[:30]}")
                schema = "public"
            db.execute(
                text("SET search_path TO :schema, public"),
                {"schema": schema}
            )
        yield db
    finally:
        db.close()


# ── Tenant Utilities ───────────────────────────────────────────

def is_multitenancy_enabled() -> bool:
    """Check if multitenancy is enabled in settings."""
    return settings.ENABLE_MULTITENANCY


def get_tenant_config(tenant_id: str, db: Session) -> dict:
    """Get configuration for a specific tenant.
    
    Args:
        tenant_id: The tenant's company ID
        db: Database session
        
    Returns:
        Dictionary with tenant configuration
    """
    from app.models import Company
    
    company = db.query(Company).filter(Company.id == tenant_id).first()
    if not company:
        return {}
    
    return {
        "company_id": str(company.id),
        "company_name": company.company_name,
        "schema": f"tenant_{str(company.id)[:8].replace('-', '_')}",
        "is_active": company.is_active,
        "features": _get_feature_flags(company),
    }


def _get_feature_flags(company) -> dict:
    """Determine feature flags based on company subscription."""
    # Get subscription from company (lazy import to avoid circular)
    try:
        sub = company.subscription
        plan = sub.plan if sub else "free"
    except Exception:
        plan = "free"

    return {
        "ai_assistant": plan in {"pro", "enterprise"},
        "ixbrl_filing": plan in {"pro", "enterprise"},
        "regulatory_intelligence": plan in {"enterprise"},
        "multi_user": plan in {"team", "enterprise"},
        "api_access": plan in {"pro", "team", "enterprise"},
        "custom_branding": plan in {"enterprise"},
        "priority_support": plan in {"enterprise"},
    }
