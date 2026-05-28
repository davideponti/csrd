"""
CSRD Comply — AI Intelligence Endpoints (Steps 6-7).

Endpoints:
- POST /ai/esrs-mapper      Map ESRS datapoints to company context (with 30-day cache)
- POST /ai/esrs-mapper/batch  Batch mapping of multiple datapoints simultaneously
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User, Company, EsrsDatapoint
from ai_engine.esrs_parser.esrs_nlp_mapper import ESMapper, CompanyProfile

router = APIRouter()

# ── Database-backed cache ───────────────────────────────────────
# Uses the EsrsDatapoint table to persist cached mapper results.
# This approach is:
# - Distributed: all workers/processes share the same cache via DB
# - Persistent: survives restarts
# - Scalable: works with serverless, horizontal scaling, etc.
# 
# For high-throughput scenarios, migrate to Redis.
CACHE_TTL_DAYS = 30
import json
from sqlalchemy import text as sa_text


def _get_cache_key(company_id: str, datapoint_id: str) -> str:
    return f"{company_id}:{datapoint_id}"


def _get_from_cache(key: str, db: Session = None) -> Optional[dict]:
    """Retrieve cached mapper result from the database."""
    if db is None:
        return None
    try:
        result = db.execute(
            sa_text("""
                SELECT cache_data, created_at 
                FROM esrs_datapoint_cache 
                WHERE cache_key = :key
            """),
            {"key": key}
        ).first()
        if result:
            cache_data, created_at = result
            if datetime.utcnow() - created_at < timedelta(days=CACHE_TTL_DAYS):
                return json.loads(cache_data)
            # Expired — delete stale entry
            db.execute(
                sa_text("DELETE FROM esrs_datapoint_cache WHERE cache_key = :key"),
                {"key": key}
            )
            db.commit()
    except Exception:
        # Table might not exist yet — fall through to compute
        pass
    return None


def _set_cache(key: str, data: dict, db: Session = None):
    """Store mapper result in the database cache."""
    if db is None:
        return
    try:
        # Upsert: insert or update
        db.execute(
            sa_text("""
                INSERT INTO esrs_datapoint_cache (cache_key, cache_data, created_at)
                VALUES (:key, :data, :now)
                ON CONFLICT (cache_key) 
                DO UPDATE SET cache_data = :data, created_at = :now
            """),
            {
                "key": key,
                "data": json.dumps(data),
                "now": datetime.utcnow(),
            }
        )
        db.commit()
    except Exception:
        db.rollback()
        # Table might not exist yet — silently continue
        pass


# ── Schemas ──────────────────────────────────────────────────────

class EsrsMapperInput(BaseModel):
    disclosure_text: str
    sector: str                     # NACE code
    activities: List[str]
    countries: List[str]
    employee_count: int
    turnover: Optional[float] = None


class EsrsMapperOutput(BaseModel):
    applicable: bool
    confidence: float
    data_source_suggestion: Optional[str] = None
    difficulty: Optional[int] = None
    priority: Optional[str] = None
    rationale: Optional[str] = None


class BatchMapperInput(BaseModel):
    datapoints: List[EsrsMapperInput]


class BatchMapperOutput(BaseModel):
    results: List[EsrsMapperOutput]
    total: int
    applicable_count: int


class MapperStatusOutput(BaseModel):
    cache_size: int
    cache_ttl_days: int
    provider: str


# ── Endpoints ────────────────────────────────────────────────────

@router.post("/esrs-mapper", response_model=EsrsMapperOutput)
def map_esrs_datapoint(
    data: EsrsMapperInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Map a single ESRS datapoint to the company's context using AI.

    Results are cached for 30 days (ESRS taxonomy is stable).
    """
    # Check cache first
    cache_key = _get_cache_key(str(current_user.company_id), data.disclosure_text[:100])
    cached = _get_from_cache(cache_key, db=db)
    if cached:
        cached["_cached"] = True
        return cached

    # Build company profile
    profile = CompanyProfile(
        sector=data.sector,
        activities=data.activities,
        countries=data.countries,
        employee_count=data.employee_count,
        turnover=data.turnover,
    )

    # Run mapper (fallback to rule-based if no LLM configured)
    mapper = ESMapper()
    result = mapper.map_datapoint(data.disclosure_text, profile)

    output = {
        "applicable": result.applicable,
        "confidence": result.confidence,
        "data_source_suggestion": result.data_source_suggestion,
        "difficulty": result.difficulty,
        "priority": result.priority,
        "rationale": result.rationale,
    }

    # Store in cache
    _set_cache(cache_key, output, db=db)

    return output


@router.post("/esrs-mapper/batch", response_model=BatchMapperOutput)
def batch_map_esrs_datapoints(
    data: BatchMapperInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Batch map multiple ESRS datapoints to company context.

    Processes up to 50 datapoints per request.
    Each result is cached individually.
    """
    if len(data.datapoints) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 datapoints per batch request.",
        )

    mapper = ESMapper()
    results = []
    applicable_count = 0

    for dp in data.datapoints:
        cache_key = _get_cache_key(
            str(current_user.company_id), dp.disclosure_text[:100]
        )
        cached = _get_from_cache(cache_key, db=db)
        if cached:
            results.append(EsrsMapperOutput(**cached))
            if cached.get("applicable"):
                applicable_count += 1
            continue

        profile = CompanyProfile(
            sector=dp.sector,
            activities=dp.activities,
            countries=dp.countries,
            employee_count=dp.employee_count,
            turnover=dp.turnover,
        )

        result = mapper.map_datapoint(dp.disclosure_text, profile)
        output = EsrsMapperOutput(
            applicable=result.applicable,
            confidence=result.confidence,
            data_source_suggestion=result.data_source_suggestion,
            difficulty=result.difficulty,
            priority=result.priority,
            rationale=result.rationale,
        )

        _set_cache(cache_key, output.model_dump(), db=db)
        results.append(output)

        if result.applicable:
            applicable_count += 1

    return BatchMapperOutput(
        results=results,
        total=len(results),
        applicable_count=applicable_count,
    )


@router.get("/esrs-mapper/status", response_model=MapperStatusOutput)
def get_mapper_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current status of the ESRS mapper (cache size, provider)."""
    # Count cached entries
    try:
        count = db.execute(
            sa_text("SELECT COUNT(*) FROM esrs_datapoint_cache")
        ).scalar() or 0
    except Exception:
        count = 0
    return MapperStatusOutput(
        cache_size=count,
        cache_ttl_days=CACHE_TTL_DAYS,
        provider="openai",  # or anthropic, depending on env
    )


@router.post("/esrs-mapper/clear-cache")
def clear_mapper_cache(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear the entire ESRS mapper cache (admin only)."""
    from app.models import UserRole
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    try:
        db.execute(sa_text("DELETE FROM esrs_datapoint_cache"))
        db.commit()
        return {"status": "cache_cleared", "size": 0}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")
