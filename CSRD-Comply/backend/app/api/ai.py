"""
CSRD Comply — AI Intelligence Endpoints (Steps 6-7).

Endpoints:
- POST /ai/esrs-mapper      Mappa ESRS datapoint a contesto aziendale (con cache 30gg)
- POST /ai/esrs-mapper/batch  Batch mapping di più datapoint contemporaneamente
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

# ── Simple in-memory cache ──────────────────────────────────────
# In production, use Redis with TTL-based expiry
_mapper_cache: dict[str, tuple[datetime, dict]] = {}
CACHE_TTL_DAYS = 30


def _get_cache_key(company_id: str, datapoint_id: str) -> str:
    return f"{company_id}:{datapoint_id}"


def _get_from_cache(key: str) -> Optional[dict]:
    if key in _mapper_cache:
        timestamp, data = _mapper_cache[key]
        if datetime.utcnow() - timestamp < timedelta(days=CACHE_TTL_DAYS):
            return data
        del _mapper_cache[key]
    return None


def _set_cache(key: str, data: dict):
    _mapper_cache[key] = (datetime.utcnow(), data)


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
    cached = _get_from_cache(cache_key)
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
    _set_cache(cache_key, output)

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
        cached = _get_from_cache(cache_key)
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

        _set_cache(cache_key, output.model_dump())
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
):
    """Get the current status of the ESRS mapper (cache size, provider)."""
    return MapperStatusOutput(
        cache_size=len(_mapper_cache),
        cache_ttl_days=CACHE_TTL_DAYS,
        provider="openai",  # or anthropic, depending on env
    )


@router.post("/esrs-mapper/clear-cache")
def clear_mapper_cache(
    current_user: User = Depends(get_current_user),
):
    """Clear the entire ESRS mapper cache (admin only)."""
    from app.models import UserRole
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    _mapper_cache.clear()
    return {"status": "cache_cleared", "size": 0}
