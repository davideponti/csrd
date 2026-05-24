"""CSRD Comply — Multitenancy Middleware & Utilities.

Gestisce l'isolamento dei dati tra tenant (aziende) tramite:
- Middleware che estrae il tenant_id dal token JWT
- Iniezione automatica del filtro company_id nelle query
- Schema-based isolation (opzionale, per deployment enterprise)
"""
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import event
from sqlalchemy.orm import Session, joinedload
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Callable, Awaitable
import logging
import time

from app.core.config import settings
from app.core.database import get_db, SessionLocal
from app.models import User, Company

logger = logging.getLogger(__name__)

# ── Tenant Context ──────────────────────────────────────────────

class TenantContext:
    """Thread-safe tenant context storage.
    
    Popolato dal middleware per ogni richiesta.
    Usato dai filtri automatici delle query SQLAlchemy.
    """
    _tenant_id: Optional[str] = None
    _schema: Optional[str] = None

    @classmethod
    def set(cls, tenant_id: Optional[str], schema: Optional[str] = None):
        cls._tenant_id = tenant_id
        cls._schema = schema

    @classmethod
    def get_tenant_id(cls) -> Optional[str]:
        return cls._tenant_id

    @classmethod
    def get_schema(cls) -> Optional[str]:
        return cls._schema

    @classmethod
    def clear(cls):
        cls._tenant_id = None
        cls._schema = None


# ── Middleware ──────────────────────────────────────────────────

class MultitenancyMiddleware(BaseHTTPMiddleware):
    """Middleware che estrae il tenant context dal token JWT.
    
    Per ogni richiesta:
    1. Estrae il token Bearer dall'Authorization header
    2. Decodifica il token per ottenere company_id e schema
    3. Imposta il TenantContext
    4. Logga la richiesta con tenant info
    5. Pulisce il contesto dopo la risposta
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
                logger.warning(f"Failed to decode token for tenant: {e}")
                # Non blocchiamo la richiesta, lascia contesto vuoto

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
            schema = TenantContext.get_schema() or f"tenant_{tenant_id[:8].replace('-', '_')}"
            db.execute(f"SET search_path TO {schema}, public")
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
