"""
CSRD Comply — Real Dashboard Data Endpoint
Aggrega dati reali da DB per la dashboard principale.
Niente fallback hardcoded — se non ci sono dati, restituisce 0 / array vuoti.
"""
import logging
import traceback
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import (
    User, Company, EmissionsData, MaterialityAssessment,
    MaterialityScore, EsrsDatapoint, Report
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggrega dati reali per la dashboard dal DB. Nessun fallback fittizio."""
    try:
        return _get_dashboard_data_impl(current_user, db)
    except HTTPException:
        # Rilancia HTTPException così com'è (es. 401 da get_current_user)
        raise
    except Exception as e:
        logger.exception("Dashboard load error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dashboard load error: {str(e)}",
        )


def _get_dashboard_data_impl(current_user: User, db: Session) -> dict:
    """Implementazione interna della dashboard con gestione errori robusta."""
    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    if not company:
        return {"error": "Company not found"}

    # ── 1. Readiness Score ────────────────────────────────────
    total_datapoints = db.query(EsrsDatapoint).count()

    scored_datapoints = _safe_count(
        db.query(MaterialityScore).join(
            MaterialityAssessment,
            MaterialityScore.assessment_id == MaterialityAssessment.id
        ).filter(
            MaterialityAssessment.company_id == company.company_id
        )
    )

    emissions_count = _safe_count(
        db.query(EmissionsData).filter(
            EmissionsData.company_id == company.company_id
        )
    )

    reports_with_content = _safe_count(
        db.query(Report).filter(
            Report.company_id == company.company_id,
            Report.xhtml_content.isnot(None)
        )
    )

    # Readiness = weighted average of completeness
    if total_datapoints > 0:
        readiness_raw = (
            min(scored_datapoints / max(total_datapoints, 1) * 0.4, 0.4) +
            min(emissions_count / 4 * 0.3, 0.3) +
            min(reports_with_content * 0.3, 0.3)
        ) * 100
        readiness_score = round(readiness_raw)
    else:
        readiness_score = 0

    readiness_color = 'red' if readiness_score < 30 else 'yellow' if readiness_score < 70 else 'green'

    # ── 2. Emissions Summary ──────────────────────────────────
    try:
        emissions = db.query(EmissionsData).filter(
            EmissionsData.company_id == company.company_id
        ).all()
    except Exception as e:
        logger.warning("Emissions query failed: %s", e)
        emissions = []

    scope1_total = sum(e.value for e in emissions if hasattr(e, 'scope') and e.scope == "1")
    scope2_total = sum(e.value for e in emissions if hasattr(e, 'scope') and e.scope == "2")
    scope3_total = sum(e.value for e in emissions if hasattr(e, 'scope') and e.scope == "3")
    total = scope1_total + scope2_total + scope3_total

    current_year = datetime.now().year
    prev_year = current_year - 1

    prev_emissions = []
    try:
        prev_emissions = db.query(EmissionsData).filter(
            EmissionsData.company_id == company.company_id,
            EmissionsData.reporting_year == prev_year,
        ).all()
    except Exception as e:
        logger.warning("Previous year emissions query failed: %s", e)

    prev_total = sum(e.value for e in prev_emissions)
    yoy_change = round(((total - prev_total) / max(prev_total, 1)) * 100, 1) if prev_total > 0 else 0

    if abs(yoy_change) < 2:
        trend = 'stable'
    elif yoy_change < 0:
        trend = 'down'
    else:
        trend = 'up'

    # Last years — solo dati reali
    last_years = []
    for y in range(prev_year - 1, current_year + 1):
        try:
            ye = db.query(EmissionsData).filter(
                EmissionsData.company_id == company.company_id,
                EmissionsData.reporting_year == y,
            ).all()
            total_y = sum(e.value for e in ye)
            if total_y > 0:
                last_years.append(round(total_y, 1))
        except Exception as e:
            logger.warning("Year %d emissions query failed: %s", y, e)

    # ── 3. Deadlines — calcolate giorno per giorno ────────────
    today = date.today()
    deadlines = []

    try:
        assessment_count = db.query(MaterialityAssessment).filter(
            MaterialityAssessment.company_id == company.company_id,
            MaterialityAssessment.status != 'completed'
        ).count()
        if assessment_count > 0:
            target = date(2026, 6, 15)
            deadlines.append({
                "id": "d1",
                "title": "Completamento Assessment Materialità",
                "date": target.isoformat(),
                "daysRemaining": (target - today).days,
                "severity": "critical",
                "category": "Assessment",
            })
    except Exception as e:
        logger.warning("Assessment count query failed: %s", e)

    try:
        scope3_count = db.query(EmissionsData).filter(
            EmissionsData.company_id == company.company_id,
            EmissionsData.scope == "3",
        ).count()
        if scope3_count == 0:
            target = date(2026, 7, 31)
            deadlines.append({
                "id": "d2",
                "title": "Raccolta Dati Emissioni Scope 3",
                "date": target.isoformat(),
                "daysRemaining": (target - today).days,
                "severity": "warning",
                "category": "Emissions",
            })
    except Exception as e:
        logger.warning("Scope3 count query failed: %s", e)

    target = date(2026, 9, 30)
    deadlines.append({
        "id": "d3",
        "title": "Generazione Report CSRD Annuale",
        "date": target.isoformat(),
        "daysRemaining": (target - today).days,
        "severity": "info",
        "category": "Reporting",
    })
    target = date(2027, 4, 30)
    deadlines.append({
        "id": "d4",
        "title": "Filing Report a ESAP",
        "date": target.isoformat(),
        "daysRemaining": (target - today).days,
        "severity": "info",
        "category": "Filing",
    })

    # ── 4. Materiality Matrix — solo dati reali ──────────────
    matrix_data = []
    try:
        latest_assessment = db.query(MaterialityAssessment).filter(
            MaterialityAssessment.company_id == company.company_id
        ).order_by(MaterialityAssessment.created_at.desc()).first()

        if latest_assessment:
            scores = db.query(MaterialityScore).filter(
                MaterialityScore.assessment_id == latest_assessment.id
            ).all()
            for score in scores:
                dp = db.query(EsrsDatapoint).filter(
                    EsrsDatapoint.id == score.datapoint_id
                ).first()
                impact_val = 1
                financial_val = 1

                if score.total_impact_score is not None:
                    impact_val = round(score.total_impact_score / 5, 1)
                elif score.impact_scale is not None and score.impact_likelihood is not None:
                    impact_val = round((score.impact_scale * score.impact_likelihood) / 5, 1)

                if score.total_financial_score is not None:
                    financial_val = round(score.total_financial_score / 5, 1)
                elif score.financial_magnitude is not None and score.financial_likelihood is not None:
                    financial_val = round((score.financial_magnitude * score.financial_likelihood) / 5, 1)

                topic = "ESRS E1"
                if dp and dp.standard_ref:
                    topic = dp.standard_ref.split("-")[0].strip()

                matrix_data.append({
                    "impactScore": impact_val,
                    "financialScore": financial_val,
                    "isMaterial": score.is_material if score.is_material is not None else False,
                    "topic": topic,
                    "count": 1,
                })
    except Exception as e:
        logger.warning("Materiality matrix query failed: %s", e)

    # ── 5. Quick Actions — basate sui dati reali ─────────────
    quick_actions = []
    has_no_emissions = emissions_count == 0
    has_no_assessment = False

    try:
        latest_assessment_check = db.query(MaterialityAssessment).filter(
            MaterialityAssessment.company_id == company.company_id
        ).order_by(MaterialityAssessment.created_at.desc()).first()
        has_no_assessment = latest_assessment_check is None
    except Exception:
        has_no_assessment = True

    if has_no_emissions or scored_datapoints == 0:
        quick_actions.append({
            "id": "qa1",
            "label": "Completa Gap Analysis",
            "description": "Identifica i datapoint ESRS mancanti",
            "href": "/assessment",
            "icon": "AlertTriangle",
            "priority": "high",
            "completed": scored_datapoints > 0,
        })

    quick_actions.append({
        "id": "qa2",
        "label": "Inserisci Dati Emissioni",
        "description": "Scope 1, 2 e 3 per l'anno corrente",
        "href": "/emissions",
        "icon": "Leaf",
        "priority": "high",
        "completed": emissions_count >= 3,
    })

    quick_actions.append({
        "id": "qa3",
        "label": "Avvia Assessment Materialità",
        "description": "Valutazione IRO e doppia materialità",
        "href": "/assessment",
        "icon": "ClipboardCheck",
        "priority": "medium",
        "completed": not has_no_assessment,
    })

    quick_actions.append({
        "id": "qa4",
        "label": "Genera Report CSRD",
        "description": "Report annuale con tagging iXBRL",
        "href": "/reports",
        "icon": "FileText",
        "priority": "medium",
        "completed": reports_with_content > 0,
    })

    # ── 6. Gap Analysis Status — dal GapAnalyzer (con fallback) ─
    complete = 0
    partial_count = 0
    missing = 0
    total_gap = 0

    try:
        from ai_engine.esrs_parser.gap_analyzer import GapAnalyzer
        gap_analyzer = GapAnalyzer(db)
        gap_result = gap_analyzer.get_summary(str(company.company_id))
        complete = gap_result.get('complete', 0)
        partial_count = gap_result.get('partial', 0)
        missing = gap_result.get('missing', 0)
        total_gap = gap_result.get('total_required', 0)
    except ImportError as e:
        logger.warning("GapAnalyzer not available (ai_engine not installed): %s", e)
    except Exception as e:
        logger.warning("GapAnalyzer failed: %s", e)

    completion_pct = round((complete / max(total_gap, 1)) * 100) if total_gap > 0 else 0

    return {
        "readinessScore": readiness_score,
        "readinessColor": readiness_color,
        "emissionsSummary": {
            "scope1": round(scope1_total, 1),
            "scope2": round(scope2_total, 1),
            "scope3": round(scope3_total, 1),
            "total": round(total, 1),
            "trend": trend,
            "yoyChange": abs(yoy_change),
            "lastYears": last_years,
        },
        "deadlines": deadlines,
        "materialityMatrix": matrix_data,
        "quickActions": quick_actions,
        "regulatoryUpdates": [],
        "gapAnalysisStatus": {
            "total": total_gap,
            "complete": complete,
            "partial": partial_count,
            "missing": missing,
            "completionPercentage": completion_pct,
        },
    }


def _safe_count(query) -> int:
    """Esegue query.count() con fallback a 0 se la tabella/colonna non esiste."""
    try:
        return query.count()
    except Exception as e:
        logger.warning("Database count query failed: %s", e)
        return 0
