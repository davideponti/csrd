"""
CSRD Comply — Materiality Report Generator (Step 11)

Genera il documento di doppia materialità conforme agli ESRS.
ESRS 2 IRO-1: Description of the process to identify and assess
ESRS 2 IRO-2: Disclosure Requirements in ESRS covered by the undertaking
"""
from ai_engine.materiality_engine.scoring_engine import ScoringEngine
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from app.models import (
    Company, CompanyContext, MaterialityAssessment, MaterialityScore,
    EsrsDatapoint, SustainabilityMatter,
)
class MaterialityReportGenerator:
    """Generatore del report di doppia materialità conforme ESRS."""

    @staticmethod
    def generate_iro1_section(
        company: Company,
        context: Optional[CompanyContext],
        assessment: MaterialityAssessment,
        db: Session,
    ) -> Dict[str, Any]:
        """
        ESRS 2 IRO-1: Description of the process to identify and assess
        material impacts, risks and opportunities.
        """
        matrix_data = ScoringEngine.get_materiality_matrix(db, str(assessment.id))

        # Determina i topic materiali
        material_items = [m for m in matrix_data if m["is_material"]]
        material_standards = list(set(m["standard_ref"] for m in material_items))

        return {
            "section": "ESRS 2 IRO-1",
            "title": "Description of the process to identify and assess material impacts, risks and opportunities",
            "content": {
                "methodology": (
                    f"The double materiality assessment was conducted following EFRAG IG 1 "
                    f"Materiality Assessment implementation guidance. The process involved: "
                    f"(1) understanding the company context through value chain analysis, "
                    f"(2) identification of actual and potential impacts, risks and opportunities (IROs), "
                    f"(3) assessment of impact materiality using scale, scope, irremediability and likelihood criteria, "
                    f"(4) assessment of financial materiality using magnitude and likelihood criteria. "
                    f"The materiality threshold was set at {ScoringEngine.MATERIALITY_THRESHOLD} out of 5."
                ),
                "company_context": {
                    "value_chain": context.value_chain_description if context else "Not provided",
                    "key_activities": context.key_activities if context else [],
                    "geographical_scope": context.geographical_scope if context else [],
                    "stakeholder_groups": context.stakeholder_groups if context else [],
                } if context else {"value_chain": "Not provided"},
                "assessment_date": str(assessment.assessment_date),
                "methodology_version": assessment.methodology_version,
            },
            "material_topics": material_standards,
            "total_iro_evaluated": len(matrix_data),
            "total_material_iro": len(material_items),
        }

    @staticmethod
    def generate_iro2_section(
        assessment: MaterialityAssessment,
        db: Session,
    ) -> Dict[str, Any]:
        """
        ESRS 2 IRO-2: Disclosure Requirements in ESRS covered by the undertaking.
        """
        scores = db.query(MaterialityScore).filter(
            MaterialityScore.assessment_id == assessment.id,
            MaterialityScore.is_material == True,
        ).all()

        # Raggruppa per standard ESRS
        standards_data: Dict[str, List] = {}
        for score in scores:
            datapoint = db.query(EsrsDatapoint).filter(
                EsrsDatapoint.id == score.datapoint_id
            ).first()
            if datapoint:
                standard = datapoint.standard_ref.split("-")[0] if "-" in datapoint.standard_ref else datapoint.standard_ref
                if standard not in standards_data:
                    standards_data[standard] = []
                standards_data[standard].append({
                    "datapoint": datapoint.disclosure_requirement,
                    "reference": datapoint.standard_ref,
                    "paragraph": datapoint.paragraph_ref,
                    "impact_score": score.total_impact_score,
                    "financial_score": score.total_financial_score,
                })

        return {
            "section": "ESRS 2 IRO-2",
            "title": "Disclosure Requirements in ESRS covered by the undertaking",
            "content": {
                "introduction": (
                    "The following disclosure requirements have been identified as material "
                    "based on the double materiality assessment conducted."
                ),
                "material_disclosure_requirements": [
                    {
                        "standard": standard,
                        "datapoints": datapoints,
                        "count": len(datapoints),
                    }
                    for standard, datapoints in sorted(standards_data.items())
                ],
            },
            "total_material_standards": len(standards_data),
            "total_material_datapoints": len(scores),
        }

    @staticmethod
    def generate_full_materiality_report(
        company: Company,
        context: Optional[CompanyContext],
        assessment: MaterialityAssessment,
        db: Session,
    ) -> Dict[str, Any]:
        """Genera il report completo di doppia materialità."""
        iro1 = MaterialityReportGenerator.generate_iro1_section(company, context, assessment, db)
        iro2 = MaterialityReportGenerator.generate_iro2_section(assessment, db)
        scores_summary = ScoringEngine.calculate_assessment_scores(db, str(assessment.id))

        return {
            "report_title": f"Double Materiality Assessment - {company.company_name}",
            "company_name": company.company_name,
            "reporting_year": company.reporting_year,
            "assessment_id": str(assessment.id),
            "assessment_date": str(assessment.assessment_date),
            "executive_summary": (
                f"The double materiality assessment for {company.company_name} evaluated "
                f"{scores_summary['total_datapoints']} datapoints across all ESRS standards. "
                f"Of these, {scores_summary['material_datapoints']} were identified as material "
                f"({scores_summary['completion_percentage']}% completion rate). "
                f"Material topics identified: {', '.join(scores_summary['material_topics'])}."
            ),
            "sections": [iro1, iro2],
            "scores_summary": scores_summary,
            "generated_at": "auto-generated",
        }

    @staticmethod
    def generate_narrative_for_iro(
        iro_data: Dict[str, Any],
        scores: List[MaterialityScore],
    ) -> str:
        """
        Genera narrativa testuale per un IRO specifico.
        Trasforma i dati numerici in descrizione conforme ESRS.
        """
        topic = iro_data.get("topic", "")
        name = iro_data.get("name", "")
        iro_type = iro_data.get("type", "impact")
        severity = iro_data.get("severity", "medium")

        type_labels = {
            "impact": "impact",
            "risk": "risk",
            "opportunity": "opportunity",
        }

        narrative = (
            f"Regarding {topic}, the company identified a {type_labels.get(iro_type, 'impact')} "
            f"related to '{name}'. "
            f"This was assessed with {severity} priority level. "
        )

        if scores:
            avg_impact = sum(s.total_impact_score or 0 for s in scores) / len(scores)
            avg_financial = sum(s.total_financial_score or 0 for s in scores) / len(scores)
            narrative += (
                f"The impact materiality score was {avg_impact:.1f}/5.0 "
                f"and the financial materiality score was {avg_financial:.1f}/5.0. "
            )

        return narrative


# Alias for backward compatibility with tests
MaterialityReport = MaterialityReportGenerator
