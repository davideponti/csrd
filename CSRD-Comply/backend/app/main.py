"""CSRD Comply — FastAPI Application Entry Point."""
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine
from app.core.logging import setup_logging, set_correlation_id, generate_correlation_id
from app.core.monitoring import setup_monitoring
from app.api.router import router

# ── Initialize logging & monitoring ─────────────────────────────
setup_logging()
setup_monitoring()

logger = logging.getLogger(__name__)

# ── Rate Limiter ────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="CSRD Comply API",
    description="SaaS di conformità CSRD/ESG per PMI Europee",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — only specific headers, no wildcards
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings._parse_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# ── Correlation ID Middleware ────────────────────────────────────
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Inject correlation ID for request tracing into structured logs."""
    correlation_id = request.headers.get("X-Correlation-ID", generate_correlation_id())
    set_correlation_id(correlation_id)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


# ── Security Headers Middleware ──────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Aggiunge header di sicurezza a tutte le risposte, incluso Content-Security-Policy."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "frame-ancestors 'none';"
    )
    return response


# ── Request Logging Middleware ───────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log each request with method, path, status, and duration."""
    start_time = time.monotonic()
    response = await call_next(request)
    duration_ms = (time.monotonic() - start_time) * 1000
    logger.info(
        "Request processed",
        extra={
            "request_method": request.method,
            "request_path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        },
    )
    return response


# ── Request Size Limit Middleware (DoS Protection) ──────────────
class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limita la dimensione massima delle richieste per prevenire DoS."""
    
    def __init__(self, app, max_size_mb: int = 10):
        super().__init__(app)
        self.max_size_bytes = max_size_mb * 1024 * 1024
    
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request too large. Maximum size: {self.max_size_bytes // (1024*1024)}MB"},
            )
        return await call_next(request)

app.add_middleware(RequestSizeLimitMiddleware, max_size_mb=settings.MAX_REQUEST_SIZE_MB)


# Multitenancy Middleware (Step 29) — optional, enabled by ENABLE_MULTITENANCY
if settings.ENABLE_MULTITENANCY:
    from app.core.multitenancy import MultitenancyMiddleware
    app.add_middleware(MultitenancyMiddleware)

# API Router
app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def run_migrations():
    """Run database migrations on startup."""
    import subprocess
    import sys
    try:
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info("Database migrations completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed: {e.stderr}")


@app.get("/")
@limiter.limit("30/minute")
async def root(request: Request):
    return {
        "message": "CSRD Comply API",
        "version": "1.0.0",
        "multitenancy_enabled": settings.ENABLE_MULTITENANCY,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
@limiter.limit("10/minute")
async def health(request: Request):
    """Health endpoint with real service dependency checks."""
    health_status = {"status": "healthy", "checks": {}}

    # Check database connectivity
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = f"error: {str(e)}"

    health_status["multitenancy"] = settings.ENABLE_MULTITENANCY

    return health_status
