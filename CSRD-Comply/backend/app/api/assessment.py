"""CSRD Comply — Materiality Assessment endpoints (Steps 8-11)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
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


# ── Endpoints ────────────────────────────────────────────────────

@router.get("/", response_model=list[AssessmentResponse])
def list_assessments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all materiality assessments for the user's company."""
    return db.query(MaterialityAssessment).filter(
        MaterialityAssessment.company_id == current_user.company_id
    ).all()


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
    assessment = db.query(MaterialityAssessment).filter(
        MaterialityAssessment.id == assessment_id,
        MaterialityAssessment.company_id == current_user.company_id,
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


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
    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    questions = ContextQuestionnaireService.get_all_questions(company.sector)
    return {"phases": questions, "sector": company.sector}


@router.get("/{assessment_id}/iros")
def get_generated_iros(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get generated IROs for the company (read-only)."""
    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

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
    Genera IRO con scoring iniziale automatico.
    Se use_ai=True, tenta generazione LLM per IRO custom.
    """
    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

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
    Generate MaterialityScore entries for each ESRS datapoint
    based on the generated IROs.
    """
    assessment = db.query(MaterialityAssessment).filter(
        MaterialityAssessment.id == assessment_id,
        MaterialityAssessment.company_id == current_user.company_id,
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

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

    # Create score entries for each IRO
    created_count = 0
    for iro in iros:
        # Find matching datapoint using topic directly (e.g. "ESRS E1" to match "ESRS E1-6")
        topic_prefix = iro['topic']
        datapoint = db.query(EsrsDatapoint).filter(
            EsrsDatapoint.standard_ref.like(f"{topic_prefix}%")
        ).first()

        if datapoint:
            existing = db.query(MaterialityScore).filter(
                MaterialityScore.assessment_id == assessment.id,
                MaterialityScore.datapoint_id == datapoint.id,
            ).first()

            if not existing:
                # Converti initial_impact_score (1-5) in dimensioni
                impact_val = int(round(iro.get("initial_impact_score") or 3))
                financial_val = int(round(iro.get("initial_financial_score") or 2))
                score = MaterialityScore(
                    assessment_id=assessment.id,
                    datapoint_id=datapoint.id,
                    impact_scale=impact_val,
                    impact_scope=impact_val,
                    impact_irremediability=max(1, impact_val - 1),
                    impact_likelihood=impact_val,
                    financial_magnitude=financial_val,
                    financial_likelihood=financial_val,
                )
                db.add(score)
                created_count += 1

    if created_count > 0:
        db.commit()

    return {
        "assessment_id": assessment_id,
        "total_iros": len(iros),
        "score_entries_created": created_count,
    }


# ── Step 10: Interactive Scoring Endpoints ───────────────────

@router.get("/{assessment_id}/scores")
def list_scores(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all scores for an assessment (Step 10)."""
    assessment = db.query(MaterialityAssessment).filter(
        MaterialityAssessment.id == assessment_id,
        MaterialityAssessment.company_id == current_user.company_id,
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

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
    Aggiorna un singolo score con le valutazioni dell'utente (Step 10).
    Le dimensioni valutate sono: impact_scale, impact_scope, impact_irremediability,
    impact_likelihood, financial_magnitude, financial_likelihood.
    Il calcolo del Double Materiality Score è automatico.
    """
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
    Genera domande AI di approfondimento basate sulle valutazioni correnti (Step 10).
    Se l'utente ha valutato Scale=5, l'AI chiede se ha considerato la value chain.
    Se l'utente ha dato punteggi bassi, l'AI suggerisce benchmark di settore.
    """
    score = db.query(MaterialityScore).filter(
        MaterialityScore.id == score_id,
        MaterialityScore.assessment_id == assessment_id,
    ).first()
    if not score:
        raise HTTPException(status_code=404, detail="Score not found")

    datapoint = db.query(EsrsDatapoint).filter(
        EsrsDatapoint.id == score.datapoint_id
    ).first()

    # Genera follow-up basati sui punteggi correnti
    followups = []
    context_info = {
        "standard": datapoint.standard_ref if datapoint else "Unknown",
        "requirement": datapoint.disclosure_requirement if datapoint else "",
    }

    # Se Scale è alto, chiedi conferma e approfondimento value chain
    if score.impact_scale and score.impact_scale >= 4:
        followups.append({
            "type": "deep_dive",
            "question": f"Hai considerato l'impatto sull'intera catena del valore? "
                        f"Per '{context_info['requirement']}', l'impatto potrebbe estendersi "
                        f"anche a fornitori e clienti.",
            "suggestion": "Considera se l'impatto si estende oltre l'operatività diretta.",
        })

    # Se Scope è basso ma Scale è alto, chiedi revisione
    if score.impact_scale and score.impact_scope and score.impact_scale >= 4 and score.impact_scope <= 2:
        followups.append({
            "type": "inconsistency",
            "question": f"Hai valutato Scale={score.impact_scale} ma Scope={score.impact_scope}. "
                        f"Un impatto di questa portata tipicamente ha uno scope più ampio. "
                        f"Confermi la valutazione?",
            "suggestion": "Considera se l'impatto potrebbe interessare un'area geografica più vasta.",
        })

    # Se tutti i punteggi sono bassi, suggerisci benchmark
    if score.impact_scale and score.financial_magnitude and score.impact_scale <= 2 and score.financial_magnitude <= 2:
        followups.append({
            "type": "benchmark_check",
            "question": f"Tutti i punteggi sono bassi per '{context_info['requirement']}'. "
                        f"I dati di settore suggeriscono una rilevanza maggiore per aziende comparabili. "
                        f"Confermi la valutazione?",
            "suggestion": "Verifica con dati di benchmark di settore prima di confermare.",
        })

    # Pattern analysis dopo valutazioni estreme
    if score.impact_scale == 5 or score.financial_magnitude == 5:
        followups.append({
            "type": "pattern_analysis",
            "question": f"Hai assegnato il punteggio massimo. "
                        f"Quali evidenze supportano questa valutazione? "
                        f"Documentazione, dati misurati, o stime?",
            "suggestion": "Documenta le evidenze a supporto del punteggio massimo.",
        })

    # Se likelihood finanziaria è alta, chiedi dettagli
    if score.financial_likelihood and score.financial_likelihood >= 4:
        followups.append({
            "type": "financial_detail",
            "question": f"Alta probabilità finanziaria rilevata. "
                        f"Quale impatto economico stimi? (es. aumento costi del 10-20%, "
                        f"sanzioni, perdita clienti)",
            "suggestion": "Quantifica l'impatto finanziario atteso in EUR dove possibile.",
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
    # First recalculate individual datapoint scores
    scores = db.query(MaterialityScore).filter(
        MaterialityScore.assessment_id == assessment_id,
    ).all()

    for score in scores:
        # Recalculate if ANY dimension has a value (impact or financial)
        if score.impact_scale is not None or score.financial_magnitude is not None:
            ScoringEngine.score_single_datapoint(
                db, str(score.id),
                impact_scale=score.impact_scale,
                impact_scope=score.impact_scope,
                impact_irremediability=score.impact_irremediability,
                impact_likelihood=score.impact_likelihood,
                financial_magnitude=score.financial_magnitude,
                financial_likelihood=score.financial_likelihood,
            )

    # Then calculate aggregate
    summary = ScoringEngine.calculate_assessment_scores(db, assessment_id)
    return summary


@router.get("/{assessment_id}/matrix")
def get_materiality_matrix(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get materiality matrix data (scatter plot)."""
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
    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    context = db.query(CompanyContext).filter(
        CompanyContext.company_id == current_user.company_id
    ).first()

    assessment = db.query(MaterialityAssessment).filter(
        MaterialityAssessment.id == assessment_id,
        MaterialityAssessment.company_id == current_user.company_id,
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

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
    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    gap_analyzer = GapAnalyzer(db)
    result = gap_analyzer.get_summary(str(company.company_id))
    return result
