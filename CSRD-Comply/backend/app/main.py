"""CSRD Comply — FastAPI Application Entry Point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import router

app = FastAPI(
    title="CSRD Comply API",
    description="SaaS di conformità CSRD/ESG per PMI Europee",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Multitenancy Middleware (Step 29) — optional, enabled by ENABLE_MULTITENANCY
if settings.ENABLE_MULTITENANCY:
    from app.core.multitenancy import MultitenancyMiddleware
    app.add_middleware(MultitenancyMiddleware)

# API Router
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "CSRD Comply API",
        "version": "1.0.0",
        "multitenancy_enabled": settings.ENABLE_MULTITENANCY,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "multitenancy": settings.ENABLE_MULTITENANCY,
    }
