"""CSRD Comply — Materiality Assessment endpoints (Steps 8-11)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
import logging
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import (
    User, Company, CompanyContext, MaterialityAssessment, MaterialityScore,
    EsrsDatapoint, AssessmentStatus,
)
from app.services.context_questionnaire import ContextQuestionnaireService
from ai_engine.materiality_engine.iro_generator import IROGenerator
from ai_engine.materiality_engine.scoring_engine import ScoringEngine
from ai_engine.materiality_engine.materiality_report import MaterialityReportGenerator
from ai_engine.esrs_parser.gap_analyzer import GapAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Schemas ──────────────────────────────────────────────────────

class AssessmentResponse(BaseModel):
    id: uuid.UUID
    assessment_date: date
    status: str
    methodology_version: Optional[str] = None

    class Config:
        from_attributes = True


class AssessmentCreate(BaseModel):
    methodology_version: Optional[str] = None


class IroGenerateRequest(BaseModel):
    use_ai: bool = False
    context_override: Optional[dict] = None


class IroGenerateResponse(BaseModel):
    iros: list
    total: int
    summary: dict
    benchmark: dict


class ContextResponse(BaseModel):
    value_chain_description: Optional[str] = None
    key_activities: Optional[List[str]] = None
    business_relationships: Optional[dict] = None
    geographical_scope: Optional[List[str]] = None
    stakeholder_groups: Optional[List[str]] = None


class ContextUpdate(BaseModel):
    value_chain_description: Optional[str] = None
    key_activities: Optional[List[str]] = None
    business_relationships: Optional[dict] = None
    geographical_scope: Optional[List[str]] = None
    stakeholder_groups: Optional[List[str]] = None
    questionnaire_responses: Optional[dict] = None


class IroResponse(BaseModel):
    id: uuid.UUID
    type: str
    topic: str
    name: str
    description: str
    default_impact_scale: int
    default_financial_magnitude: int
    severity: str
    sector_applicable: bool = True


class ScoreCreate(BaseModel):
    score_id: str
    impact_scale: Optional[int] = None
    impact_scope: Optional[int] = None
    impact_irremediability: Optional[int] = None
    impact_likelihood: Optional[int] = None
    financial_magnitude: Optional[int] = None
    financial_likelihood: Optional[int] = None
    rationale: Optional[str] = None


# ── Helper ────────────────────────────────────────────────────────

def _get_company_or_404(current_user: User, db: Session) -> Company:
    """Helper to get the user's company or 404."""

    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


def _get_assessment_or_404(assessment_id: str, company_id: uuid.UUID, db: Session) -> MaterialityAssessment:
    """Helper to get an assessment verifying company ownership."""

    assessment = db.query(MaterialityAssessment).filter(
        MaterialityAssessment.id == assessment_id,
        MaterialityAssessment.company_id == company_id,
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


# ── Endpoints ────────────────────────────────────────────────────

@router.get("/", response_model=list[AssessmentResponse])
def list_assessments(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List materiality assessments for the user's company with pagination."""
    return db.query(MaterialityAssessment).filter(
        MaterialityAssessment.company_id == current_user.company_id
    ).offset(skip).limit(limit).all()


@router.post("/", response_model=AssessmentResponse, status_code=201)
def create_assessment(
    data: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new materiality assessment."""
    assessment = MaterialityAssessment(
        company_id=current_user.company_id,
        methodology_version=data.methodology_version or "1.0",
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


@router.get("/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific materiality assessment."""
    return _get_assessment_or_404(assessment_id, current_user.company_id, db)


@router.get("/{assessment_id}/context", response_model=ContextResponse)
def get_assessment_context(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get company context for an assessment."""
    context = db.query(CompanyContext).filter(
        CompanyContext.company_id == current_user.company_id
    ).first()
    if not context:
        return ContextResponse()
    return context


@router.put("/{assessment_id}/context", response_model=ContextResponse)
def update_assessment_context(
    assessment_id: str,
    data: ContextUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update company context for an assessment."""
    context = ContextQuestionnaireService.save_context(
        db=db,
        company_id=str(current_user.company_id),
        value_chain_description=data.value_chain_description,
        key_activities=data.key_activities,
        business_relationships=data.business_relationships,
        geographical_scope=data.geographical_scope,
        stakeholder_groups=data.stakeholder_groups,
        questionnaire_responses=data.questionnaire_responses,
    )
    return context


@router.get("/{assessment_id}/questionnaire")
def get_questionnaire(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the AI-adaptive questionnaire for the company's sector."""
    company = _get_company_or_404(current_user, db)
    questions = ContextQuestionnaireService.get_all_questions(company.sector)
    return {"phases": questions, "sector": company.sector}


@router.get("/{assessment_id}/iros")
def get_generated_iros(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get generated IROs for the company (read-only)."""
    company = _get_company_or_404(current_user, db)

    context = db.query(CompanyContext).filter(
        CompanyContext.company_id == current_user.company_id
    ).first()

    context_dict = None
    if context:
        context_dict = {
            "value_chain": context.value_chain_description,
            "key_activities": context.key_activities or [],
            "geographical_scope": context.geographical_scope or [],
            "stakeholder_groups": context.stakeholder_groups or [],
        }

    iros = IROGenerator.generate_iros_for_company(
        company_sector=company.sector,
        employee_count=company.employee_count,
        turnover=company.turnover,
        company_context=context_dict,
    )
    summary = IROGenerator.get_summary(iros)
    benchmark = IROGenerator.get_sector_benchmark(company.sector)

    return {"iros": iros, "total": len(iros), "summary": summary, "benchmark": benchmark}


@router.post("/{assessment_id}/iros/generate")
def generate_new_iros(
    assessment_id: str,
    data: IroGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate IROs with automatic initial scoring.
    If use_ai=True, attempts LLM generation for custom IROs.

    """
    company = _get_company_or_404(current_user, db)

    context = db.query(CompanyContext).filter(
        CompanyContext.company_id == current_user.company_id
    ).first()

    context_dict = None
    if context:
        context_dict = {
            "value_chain": context.value_chain_description,
            "key_activities": context.key_activities or [],
            "business_relationships": context.business_relationships or {},
            "geographical_scope": context.geographical_scope or [],
            "stakeholder_groups": context.stakeholder_groups or [],
        }

    # Allow context override
    if data.context_override:
        if context_dict:
            context_dict.update(data.context_override)
        else:
            context_dict = data.context_override

    iros = IROGenerator.generate_iros_for_company(
        company_sector=company.sector,
        employee_count=company.employee_count,
        turnover=company.turnover,
        company_context=context_dict,
        use_ai=data.use_ai,
    )
    summary = IROGenerator.get_summary(iros)
    benchmark = IROGenerator.get_sector_benchmark(company.sector)

    return {
        "iros": iros,
        "total": len(iros),
        "summary": summary,
        "benchmark": benchmark,
        "generated_at": "auto-generated",
        "ai_generation": data.use_ai,
    }


@router.post("/{assessment_id}/scores/generate")
def generate_score_entries(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate MaterialityScore entries for ALL ESRS datapoints.
    
    First, creates scored entries for datapoints matching IRO topics (with IRO-based scoring).
    Then, creates neutral score entries (default 1/5) for ALL remaining datapoints
    so the full 1,000+ ESRS datapoint set is covered in the assessment.
    """
    # ⚠️ SECURITY FIX: verify assessment belongs to user's company
    assessment = _get_assessment_or_404(assessment_id, current_user.company_id, db)
    company = _get_company_or_404(current_user, db)

    context = db.query(CompanyContext).filter(
        CompanyContext.company_id == current_user.company_id
    ).first()

    context_dict = None
    if context:
        context_dict = {
            "value_chain": context.value_chain_description,
            "key_activities": context.key_activities or [],
            "geographical_scope": context.geographical_scope or [],
            "stakeholder_groups": context.stakeholder_groups or [],
        }

    iros = IROGenerator.generate_iros_for_company(
        company_sector=company.sector,
        employee_count=company.employee_count,
        turnover=company.turnover,
        company_context=context_dict,
    )

    # If ESRS datapoints are fewer than expected, try full Excel seeding
    esrs_count = db.query(EsrsDatapoint).count()
    MIN_EXPECTED_DATAPOINTS = 100
    if esrs_count < MIN_EXPECTED_DATAPOINTS:
        try:
            from app.seed_esrs_datapoints import get_all_datapoints, seed_to_db
            logger.info(f"Only {esrs_count} ESRS datapoints found — triggering full seeding from Excel...")
            datapoints = get_all_datapoints(use_excel=True)
            seeded = seed_to_db(db, datapoints)
            logger.info(f"Auto-seeded {seeded} ESRS datapoints for score generation")
        except Exception as e:
            logger.warning(f"Auto-seed fallback failed: {e}")

    total_available = db.query(EsrsDatapoint).count()
    logger.info(f"Total ESRS datapoints in DB: {total_available}")

    # ── Phase 1: DELETE all existing scores for this assessment first ──
    # This ensures a clean regeneration every time (handles re-runs, new datapoints, etc.)
    existing_scores_count = db.query(MaterialityScore).filter(
        MaterialityScore.assessment_id == assessment.id,
    ).delete()
    db.commit()
    logger.info(f"Deleted {existing_scores_count} existing scores for assessment {assessment.id}")

    # ── Phase 2: Create IRO-matched scores (ONE per datapoint) ──
    # Critical fix: skip if this datapoint already has a score from a previous IRO
    # (multiple IROs for the same topic, e.g. 2 x ESRS E1, would otherwise
    # create duplicate scores for the same datapoint, inflating counts).
    iro_created = 0
    iro_matched_datapoint_ids = set()

    for iro in iros:
        topic_prefix = iro['topic']
        matching_datapoints = db.query(EsrsDatapoint).filter(
            EsrsDatapoint.standard_ref.like(f"{topic_prefix}%")
        ).all()

        if not matching_datapoints:
            continue

        for datapoint in matching_datapoints:
            dp_id_str = str(datapoint.id)
            # ⭐ Skip if this datapoint already matched by a previous IRO
            if dp_id_str in iro_matched_datapoint_ids:
                continue

            impact_val = int(round(iro.get("initial_impact_score") or 3))
            financial_val = int(round(iro.get("initial_financial_score") or 2))

            # Calcola subito i punteggi aggregati (total_impact_score, etc.)
            # così non restano NULL e il report/materialità funziona subito.
            impact_score = ScoringEngine.calculate_impact_score(
                impact_val,              # scale
                impact_val,              # scope
                max(1, impact_val - 1),  # irremediability
                impact_val,              # likelihood
            )
            financial_score = ScoringEngine.calculate_financial_score(
                financial_val,  # magnitude
                financial_val,  # likelihood
            )
            dm_result = ScoringEngine.calculate_double_materiality(impact_score, financial_score)

            score = MaterialityScore(
                assessment_id=assessment.id,
                datapoint_id=datapoint.id,
                impact_scale=impact_val,
                impact_scope=impact_val,
                impact_irremediability=max(1, impact_val - 1),
                impact_likelihood=impact_val,
                financial_magnitude=financial_val,
                financial_likelihood=financial_val,
                total_impact_score=impact_score,
                total_financial_score=financial_score,
                is_material=dm_result["is_material"],
            )
            db.add(score)
            iro_matched_datapoint_ids.add(dp_id_str)
            iro_created += 1

    # ── Phase 3: Create neutral baseline scores for ALL remaining datapoints ──
    # ⚠  METHODOLOGY CHANGE (IRO-Primary Approach):
    # Topic-level materiality is driven PRIMARILY by IRO scores. Baseline scores
    # for non-IRO datapoints serve only as a neutral secondary input (1/5).
    #
    # Previously, this phase applied differentiated sector benchmark baselines
    # (1-3 depending on sector intensity) to all remaining datapoints. This
    # could unintentionally drive topic-level materiality through many neutral
    # datapoints rather than through identified IROs — inconsistent with the
    # principle that materiality should originate from specific IRO assessment.
    #
    # Revised approach per ESRS 2 IRO-1 (documented methodology change):
    # - IRO-matched datapoints → scored based on IRO assessment (primary driver)
    # - Non-IRO datapoints → flat neutral baseline (1/5), requiring explicit user
    #   adjustment (manual scoring override) to contribute to materiality.
    # - Sector benchmarks remain available as reference context in the UI but
    #   no longer auto-apply as scoring baselines.
    #
    # The neutral baseline (1/5) ensures:
    #   1) IROs are the sole origin of materiality signals
    #   2) No topic can appear material purely from baseline aggregation
    #   3) Auditable traceability: every material datapoint maps to an IRO
    #      or an explicit user override documented in the scoring rationale.
    # ==============================================================

    def _get_topic_baseline(standard_ref: str) -> tuple:
        """Restituisce baseline neutra (1, 1) per ogni topic ESRS non coperto da IRO.
        
        IRO-Primary Approach:
        I punteggi IRO sono il driver principale della materialità a livello di topic.
        Le baseline per datapoint non coperti da IRO specifici sono neutre (1/5)
        e fungono solo da input secondario. Per superare la soglia di materialità
        (3.0/5.0), è necessario un intervento esplicito dell'utente (scoring manuale)
        o la presenza di IRO sufficientemente alti nel topic.
        """
        # Flat neutral baseline: 1/5 per tutti i topic non coperti da IRO
        return (1, 1)

    all_datapoints = db.query(EsrsDatapoint).all()
    neutral_created = 0
    neutral_datapoint_ids = set()

    for datapoint in all_datapoints:
        dp_id_str = str(datapoint.id)
        if dp_id_str in iro_matched_datapoint_ids:
            continue

        # Determina baseline contestuale per questo datapoint
        impact_bl, financial_bl = _get_topic_baseline(datapoint.standard_ref)

        # Calcola subito i punteggi aggregati, come per IRO-matched
        impact_score = ScoringEngine.calculate_impact_score(
            impact_bl,                         # scale
            impact_bl,                         # scope
            max(1, impact_bl - 1),             # irremediability
            impact_bl,                         # likelihood
        )
        financial_score = ScoringEngine.calculate_financial_score(
            financial_bl,                      # magnitude
            financial_bl,                      # likelihood
        )
        dm_result = ScoringEngine.calculate_double_materiality(impact_score, financial_score)

        score = MaterialityScore(
            assessment_id=assessment.id,
            datapoint_id=datapoint.id,
            impact_scale=impact_bl,
            impact_scope=impact_bl,
            impact_irremediability=max(1, impact_bl - 1),
            impact_likelihood=impact_bl,
            financial_magnitude=financial_bl,
            financial_likelihood=financial_bl,
            total_impact_score=impact_score,
            total_financial_score=financial_score,
            is_material=dm_result["is_material"],
        )
        db.add(score)
        neutral_datapoint_ids.add(dp_id_str)
        neutral_created += 1

    total_created = iro_created + neutral_created
    if total_created > 0:
        db.commit()
        logger.info(f"Created {total_created} MaterialityScore entries ({iro_created} IRO-based + {neutral_created} neutral)")

    return {
        "assessment_id": assessment_id,
        "total_iros": len(iros),
        "total_datapoints_available": total_available,
        "score_entries_created": total_created,
        "iro_matched_created": iro_created,
        "neutral_default_created": neutral_created,
        "iro_matched_total_unique_datapoints": len(iro_matched_datapoint_ids),
    }


# ── Step 10: Interactive Scoring Endpoints ───────────────────

@router.get("/{assessment_id}/scores")
def list_scores(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all scores for an assessment (Step 10)."""
    # ⚠️ SECURITY FIX: verify assessment belongs to user's company
    assessment = _get_assessment_or_404(assessment_id, current_user.company_id, db)

    scores = db.query(MaterialityScore).filter(
        MaterialityScore.assessment_id == assessment_id,
    ).all()

    result = []
    for score in scores:
        datapoint = db.query(EsrsDatapoint).filter(
            EsrsDatapoint.id == score.datapoint_id
        ).first()
        result.append({
            "id": str(score.id),
            "datapoint_id": str(score.datapoint_id),
            "standard_ref": datapoint.standard_ref if datapoint else "",
            "disclosure_requirement": datapoint.disclosure_requirement if datapoint else "",
            "impact_scale": score.impact_scale,
            "impact_scope": score.impact_scope,
            "impact_irremediability": score.impact_irremediability,
            "impact_likelihood": score.impact_likelihood,
            "financial_magnitude": score.financial_magnitude,
            "financial_likelihood": score.financial_likelihood,
            "total_impact_score": score.total_impact_score,
            "total_financial_score": score.total_financial_score,
            "is_material": score.is_material,
            "rationale": score.rationale,
        })

    return {"scores": result, "total": len(result)}


@router.patch("/{assessment_id}/scores/{score_id}", status_code=200)
def update_score(
    assessment_id: str,
    score_id: str,
    data: ScoreCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a single score with user assessments (Step 10).
    The evaluated dimensions are: impact_scale, impact_scope, impact_irremediability,
    impact_likelihood, financial_magnitude, financial_likelihood.
    The Double Materiality Score calculation is automatic.

    """
    # ⚠️ SECURITY FIX: verify assessment belongs to user's company FIRST
    assessment = _get_assessment_or_404(assessment_id, current_user.company_id, db)

    score = db.query(MaterialityScore).filter(
        MaterialityScore.id == score_id,
        MaterialityScore.assessment_id == assessment_id,
    ).first()
    if not score:
        raise HTTPException(status_code=404, detail="Score not found")

    try:
        updated = ScoringEngine.score_single_datapoint(
            db=db,
            score_id=score_id,
            impact_scale=data.impact_scale,
            impact_scope=data.impact_scope,
            impact_irremediability=data.impact_irremediability,
            impact_likelihood=data.impact_likelihood,
            financial_magnitude=data.financial_magnitude,
            financial_likelihood=data.financial_likelihood,
            rationale=data.rationale,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "id": str(updated.id),
        "impact_scale": updated.impact_scale,
        "impact_scope": updated.impact_scope,
        "impact_irremediability": updated.impact_irremediability,
        "impact_likelihood": updated.impact_likelihood,
        "financial_magnitude": updated.financial_magnitude,
        "financial_likelihood": updated.financial_likelihood,
        "total_impact_score": updated.total_impact_score,
        "total_financial_score": updated.total_financial_score,
        "is_material": updated.is_material,
        "rationale": updated.rationale,
    }


@router.post("/{assessment_id}/scores/{score_id}/ai-followup")
def get_ai_followup(
    assessment_id: str,
    score_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate AI follow-up questions based on current assessments (Step 10).

    """
    # ⚠️ SECURITY FIX: verify assessment belongs to user's company
    assessment = _get_assessment_or_404(assessment_id, current_user.company_id, db)

    score = db.query(MaterialityScore).filter(
        MaterialityScore.id == score_id,
        MaterialityScore.assessment_id == assessment_id,
    ).first()
    if not score:
        raise HTTPException(status_code=404, detail="Score not found")

    datapoint = db.query(EsrsDatapoint).filter(
        EsrsDatapoint.id == score.datapoint_id
    ).first()

    # Generate follow-ups based on current scores

    followups = []
    context_info = {
        "standard": datapoint.standard_ref if datapoint else "Unknown",
        "requirement": datapoint.disclosure_requirement if datapoint else "",
    }

    # When Scale is high, ask for confirmation and value chain deep dive

    if score.impact_scale and score.impact_scale >= 4:
        followups.append({
            "type": "deep_dive",
            "question": f"Have you considered the impact on the entire value chain? "

                        f"For '{context_info['requirement']}', the impact could extend "
                        f"to suppliers and customers.",
            "suggestion": "Consider whether the impact extends beyond direct operations.",

        })

    # When Scope is low but Scale is high, ask for revision
    if score.impact_scale and score.impact_scope and score.impact_scale >= 4 and score.impact_scope <= 2:
        followups.append({
            "type": "inconsistency",
            "question": f"You rated Scale={score.impact_scale} but Scope={score.impact_scope}. "
                        f"An impact of this magnitude typically has a broader scope. "
                        f"Would you like to review your assessment?",
            "suggestion": "Consider whether the impact could affect a wider geographical area.",

        })

    # When all scores are low, suggest benchmark
    if score.impact_scale and score.financial_magnitude and score.impact_scale <= 2 and score.financial_magnitude <= 2:
        followups.append({
            "type": "benchmark_check",
            "question": f"All scores are low for '{context_info['requirement']}'. "
                        f"Sector data suggests higher relevance for comparable companies. "
                        f"Do you confirm your assessment?",
            "suggestion": "Verify with sector benchmark data before confirming.",

        })

    # Pattern analysis after extreme assessments
    if score.impact_scale == 5 or score.financial_magnitude == 5:
        followups.append({
            "type": "pattern_analysis",
            "question": f"You assigned the maximum score. "
                        f"What evidence supports this assessment? "
                        f"Documentation, measured data, or estimates?",
            "suggestion": "Document the evidence supporting the maximum score.",

        })

    # When financial likelihood is high, ask for details
    if score.financial_likelihood and score.financial_likelihood >= 4:
        followups.append({
            "type": "financial_detail",
            "question": f"High financial likelihood detected. "
                        f"What economic impact do you estimate? (e.g., 10-20% cost increase, "
                        f"penalties, customer loss)",
            "suggestion": "Quantify the expected financial impact in EUR where possible.",

        })

    return {
        "score_id": score_id,
        "datapoint": context_info,
        "followup_questions": followups,
        "total": len(followups),
    }


@router.post("/{assessment_id}/scores/calculate")
def calculate_all_scores(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculate all materiality scores for the assessment."""
    # ⚠️ SECURITY FIX: verify assessment belongs to user's company
    assessment = _get_assessment_or_404(assessment_id, current_user.company_id, db)

    # First recalculate individual datapoint scores
    scores = db.query(MaterialityScore).filter(
        MaterialityScore.assessment_id == assessment_id,
    ).all()

    for score in scores:
        # Recalculate always — the ScoringEngine handles None values (returns 0.0)
        ScoringEngine.score_single_datapoint(
            db, str(score.id),
            impact_scale=score.impact_scale,
            impact_scope=score.impact_scope,
            impact_irremediability=score.impact_irremediability,
            impact_likelihood=score.impact_likelihood,
            financial_magnitude=score.financial_magnitude,
            financial_likelihood=score.financial_likelihood,
        )

    # Then calculate aggregate (sets is_material on all, commits)
    summary = ScoringEngine.calculate_assessment_scores(db, assessment_id)
    return summary


@router.get("/{assessment_id}/matrix")
def get_materiality_matrix(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get materiality matrix data (scatter plot)."""
    # ⚠️ SECURITY FIX: verify assessment belongs to user's company
    assessment = _get_assessment_or_404(assessment_id, current_user.company_id, db)

    matrix = ScoringEngine.get_materiality_matrix(db, assessment_id)
    return {
        "matrix": matrix,
        "total": len(matrix),
    }


@router.get("/{assessment_id}/report")
def generate_materiality_report(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate the full double materiality report."""
    company = _get_company_or_404(current_user, db)

    context = db.query(CompanyContext).filter(
        CompanyContext.company_id == current_user.company_id
    ).first()

    # ⚠️ SECURITY FIX: verify assessment belongs to user's company
    assessment = _get_assessment_or_404(assessment_id, current_user.company_id, db)

    report = MaterialityReportGenerator.generate_full_materiality_report(
        company, context, assessment, db,
    )
    return report


@router.get("/{assessment_id}/gap-analysis")
def get_gap_analysis(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run gap analysis and return results comparing ESRS requirements vs company data."""
    company = _get_company_or_404(current_user, db)

    assessment = _get_assessment_or_404(assessment_id, current_user.company_id, db)
    gap_analyzer = GapAnalyzer(db)
    # Pass assessment_id so the analyzer can check MaterialityScores for this assessment
    result = gap_analyzer.get_summary(company.company_id, assessment_id=str(assessment.id))
    return result
