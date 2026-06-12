"""CSRD Comply — FastAPI Application Entry Point."""
import logging
import time
import uuid

from fastapi import FastAPI, Request, HTTPException
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

# ── HTTPException handler ─────────────────────────────────────
# IMPORTANTE: Questo handler DEVE stare PRIMA del global 500 handler.
# FastAPI esegue gli exception handler nell'ordine inverso di registrazione,
# quindi HTTPException viene registrato dopo Exception (prima in risoluzione).
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Rilancia HTTPException con lo status code originale (401, 403, 404, 409, 422, ecc.)
    invece di essere catturato e trasformato in 500 dal global handler.
    
    Fix per: dashboard che restituiva 500 invece di 401 quando il token è scaduto.
    """
    # Non loggare come errore le 401/403/404 — sono comportamenti normali
    if exc.status_code >= 500:
        logger.error("HTTP %d on %s: %s", exc.status_code, request.url.path, exc.detail)
    else:
        logger.info("HTTP %d on %s: %s", exc.status_code, request.url.path, exc.detail)
    
    origin = request.headers.get("origin", "")
    allowed = settings._parse_origins()
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
    if origin in allowed or "*" in allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


# ── Global 500 exception handler (con header CORS) ──────────────
# Questo handler cattura SOLO eccezioni NON-HTTP (es. errore DB, ValueError, ecc.)
# Le HTTPException (401, 403, 404) sono gestite dal handler sopra.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions to return a safe JSON response with CORS headers."""
    logger.error("Unhandled exception", exc_info=exc, extra={"path": request.url.path})
    # Determina l'origine per CORS
    origin = request.headers.get("origin", "")
    allowed = settings._parse_origins()
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
    if origin in allowed or "*" in allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


# ── CORS Middleware ──────────────────────────────────────────────
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
    """Aggiunge header di sicurezza a tutte le risposte, incluso Content-Security-Policy.
    
    Salta CSP per endpoint di export/download binario (PDF, XLSX, DOCX)
    per evitare interferenze con il download di blob.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # Skip CSP for export/download endpoints to avoid blocking blob fetches
    path = request.url.path
    if not ("export" in path or "ixbrl" in path or path.endswith((".pdf", ".xlsx", ".docx"))):
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
    """Limita la dimensione massima delle richieste per prevenire DoS.
    
    Legge il body effettivo per bypassare lo spoofing di Content-Length
    (es. chunked Transfer-Encoding con Content-Length falso).
    """
    
    def __init__(self, app, max_size_mb: int = 10):
        super().__init__(app)
        self.max_size_bytes = max_size_mb * 1024 * 1024
    
    async def dispatch(self, request: Request, call_next):
        # Check both Content-Length and actual body size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request too large. Maximum size: {self.max_size_bytes // (1024*1024)}MB"},
            )
        
        # Read body to enforce actual size limit (catches chunked encoding bypass)
        try:
            body = await request.body()
            if len(body) > self.max_size_bytes:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Request too large. Maximum size: {self.max_size_bytes // (1024*1024)}MB"},
                )
        except Exception:
            pass
        
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
    """Create/update database tables on startup.
    
    Crea tabelle se non esistono, e aggiunge colonne mancanti
    a tabelle già esistenti (es. users con email_verified, ecc.).
    """
    from app.models import Base
    from app.core.database import engine
    from sqlalchemy import text

    # Add missing columns to existing tables (create_all doesn't do this)
    # 🔴 ATTENZIONE: Mantieni sincronizzato con il modello User in models/__init__.py
    with engine.connect() as conn:
        for col, col_type in [
            ("email_verified", "BOOLEAN DEFAULT FALSE"),
            ("otp_code", "VARCHAR(6)"),
            ("otp_expires_at", "TIMESTAMP"),
            ("otp_attempts", "INTEGER DEFAULT 0"),
            ("reset_password_token", "VARCHAR(255)"),
            ("reset_password_expires_at", "TIMESTAMP"),
            ("token_version", "INTEGER DEFAULT 0"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {col_type}"))
            except Exception:
                pass
        # 🔴 Add missing columns to reports table (colonne aggiunte al modello
        #    ma mai migrate). RIMUOVI quando 

        #    la migration d2d4919460f10 è stata eseguita.
        for col, col_type in [
            ("review_comments", "JSON"),
            ("gap_analysis_results", "JSON"),
            ("narrative_content", "JSON"),
            ("ixbrl_tags_applied", "BOOLEAN DEFAULT FALSE"),
            ("ixbrl_metadata", "JSON"),
            ("approved_at", "TIMESTAMP"),
            ("approved_by", "UUID"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE reports ADD COLUMN IF NOT EXISTS {col} {col_type}"))
            except Exception:
                pass
        conn.commit()

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables updated successfully")

    # Auto-seed ESRS datapoints if DB is empty
    try:
        from app.seed_esrs_datapoints import get_all_datapoints, seed_to_db
        from sqlalchemy.orm import Session
        with Session(engine) as session:
            from app.models import EsrsDatapoint
            count = session.query(EsrsDatapoint).count()
            if count < 10:
                logger.info("ESRS datapoints empty — auto-seeding...")
                datapoints = get_all_datapoints(use_excel=False)
                created = seed_to_db(session, datapoints)
                logger.info(f"Auto-seed completato: {created} nuovi datapoint")
            else:
                logger.info(f"ESRS datapoints già presenti ({count}), salto seed")
    except Exception as e:
        logger.warning(f"Auto-seed ESRS saltato: {e}")


@app.get("/")
@limiter.limit("30/minute")
async def root(request: Request):
    return {
        "message": "CSRD Comply API",
        "version": "1.0.0",
    }


@app.get("/health")
@limiter.limit("10/minute")
async def health(request: Request):
    """Health endpoint with real service dependency checks.
    
    Note: Returns only boolean/status info, no internal details
    that could aid infrastructure fingerprinting.
    """
    health_status = {"status": "healthy", "checks": {}}

    # Check database connectivity
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "ok"
    except Exception:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = "error"

    return health_status
