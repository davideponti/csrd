"""
CSRD Comply — Materiality Report Generator (Step 11)

Genera il documento di doppia materialità conforme agli ESRS.
ESRS 2 IRO-1: Description of the process to identify and assess
ESRS 2 IRO-2: Disclosure Requirements in ESRS covered by the undertaking
Include sezioni dettagliate per ogni standard ESRS materiale.
"""
import re
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from app.models import (
    Company, CompanyContext, MaterialityAssessment, MaterialityScore,
    EsrsDatapoint, SustainabilityMatter,
)
from ai_engine.materiality_engine.scoring_engine import ScoringEngine


class MaterialityReportGenerator:
    """Generatore del report di doppia materialità completo conforme ESRS."""

    # Nomi descrittivi per ogni standard ESRS
    STANDARD_NAMES = {
        "ESRS E1": "Climate Change",
        "ESRS E2": "Pollution",
        "ESRS E3": "Water and Marine Resources",
        "ESRS E4": "Biodiversity and Ecosystems",
        "ESRS E5": "Resource Use and Circular Economy",
        "ESRS S1": "Own Workforce",
        "ESRS S2": "Workers in the Value Chain",
        "ESRS S3": "Affected Communities",
        "ESRS S4": "Consumers and End-users",
        "ESRS G1": "Business Conduct",
    }

    # Sotto-temi per ogni standard (ESRS 1 AR 16)
    STANDARD_SUBTOPICS = {
        "ESRS E1": ["Climate change adaptation", "Climate change mitigation", "Energy"],
        "ESRS E2": ["Air pollution", "Water pollution", "Soil pollution", "Substances of concern", "Substances of very high concern"],
        "ESRS E3": ["Water consumption", "Water withdrawals", "Water discharges", "Marine resources"],
        "ESRS E4": ["Direct impact drivers of biodiversity loss", "Impacts on species and ecosystems", "Impacts and dependencies on ecosystem services"],
        "ESRS E5": ["Resource inflows (material sourcing)", "Resource outflows (products & services)", "Waste"],
        "ESRS S1": ["Working conditions", "Equal treatment and opportunities", "Other work-related rights"],
        "ESRS S2": ["Working conditions", "Equal treatment and opportunities", "Other work-related rights"],
        "ESRS S3": ["Economic, social and cultural rights", "Civil and political rights", "Rights of indigenous peoples"],
        "ESRS S4": ["Information-related impacts", "Personal safety", "Social inclusion"],
        "ESRS G1": ["Corporate culture", "Supplier relationships", "Corruption and bribery", "Political engagement"],
    }

    @staticmethod
    def _extract_topic(standard_ref: str) -> str:
        """Extract ESRS topic prefix: 'ESRS E1-6' -> 'ESRS E1'."""
        match = re.match(r'(ESRS [A-Z]\d+)', standard_ref)
        if match:
            return match.group(1)
        return standard_ref

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
        material_standards = list(set(
            MaterialityReportGenerator._extract_topic(m["standard_ref"])
            for m in material_items
        ))

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
                "scoring_approach": {
                    "impact_materiality": {
                        "dimensions": ["Scale (30%)", "Scope (30%)", "Irremediability (20%)", "Likelihood (20%)"],
                        "formula": "For actual impacts: severity = Σ(dimension × weight) / total_weight. For potential impacts: impact_score = severity × likelihood / 5",
                    },
                    "financial_materiality": {
                        "dimensions": ["Magnitude (60%)", "Likelihood (40%)"],
                        "formula": "financial_score = magnitude × 0.6 + likelihood × 0.4",
                    },
                    "double_materiality": "max(impact_score, financial_score) >= 3.0/5.0",
                },
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
        Include elenco completo dei datapoint materiali per ogni standard.
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
                standard = MaterialityReportGenerator._extract_topic(datapoint.standard_ref)
                if standard not in standards_data:
                    standards_data[standard] = []
                standards_data[standard].append({
                    "datapoint": datapoint.disclosure_requirement,
                    "reference": datapoint.standard_ref,
                    "paragraph": datapoint.paragraph_ref,
                    "impact_score": score.total_impact_score,
                    "financial_score": score.total_financial_score,
                    "data_type": datapoint.data_type,
                    "unit": datapoint.unit,
                    "is_mandatory": datapoint.is_mandatory,
                    "phase_in_year": datapoint.phase_in_year,
                    "sfd_ref": datapoint.sfd_ref,
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
                        "standard_name": MaterialityReportGenerator.STANDARD_NAMES.get(standard, ""),
                        "subtopics": MaterialityReportGenerator.STANDARD_SUBTOPICS.get(standard, []),
                        "datapoints": datapoints,
                        "count": len(datapoints),
                        "average_impact": round(sum(d["impact_score"] or 0 for d in datapoints) / len(datapoints), 2) if datapoints else 0,
                        "average_financial": round(sum(d["financial_score"] or 0 for d in datapoints) / len(datapoints), 2) if datapoints else 0,
                    }
                    for standard, datapoints in sorted(standards_data.items())
                ],
            },
            "total_material_standards": len(standards_data),
            "total_material_datapoints": len(scores),
        }

    @staticmethod
    def generate_standard_detail_sections(
        assessment: MaterialityAssessment,
        db: Session,
    ) -> List[Dict[str, Any]]:
        """
        Genera sezioni di dettaglio per ogni standard ESRS con datapoint materiali.
        Include:
        - Perché lo standard è materiale per l'azienda
        - Elenco dei disclosure requirement con punteggi
        - Dettaglio dei datapoint
        """
        scores = db.query(MaterialityScore).filter(
            MaterialityScore.assessment_id == assessment.id,
            MaterialityScore.is_material == True,
        ).all()

        # Raggruppa per standard
        standards_data: Dict[str, List[Dict]] = {}
        for score in scores:
            datapoint = db.query(EsrsDatapoint).filter(
                EsrsDatapoint.id == score.datapoint_id
            ).first()
            if datapoint:
                standard = MaterialityReportGenerator._extract_topic(datapoint.standard_ref)
                if standard not in standards_data:
                    standards_data[standard] = []
                standards_data[standard].append({
                    "score": score,
                    "datapoint": datapoint,
                })

        sections = []
        for standard, items in sorted(standards_data.items()):
            standard_name = MaterialityReportGenerator.STANDARD_NAMES.get(standard, standard)
            subtopics = MaterialityReportGenerator.STANDARD_SUBTOPICS.get(standard, [])

            # Calcola statistiche
            impact_scores = [item["score"].total_impact_score for item in items if item["score"].total_impact_score is not None]
            financial_scores = [item["score"].total_financial_score for item in items if item["score"].total_financial_score is not None]
            avg_impact = round(sum(impact_scores) / len(impact_scores), 2) if impact_scores else 0
            avg_financial = round(sum(financial_scores) / len(financial_scores), 2) if financial_scores else 0

            # Raggruppa per disclosure requirement (standard_ref)
            dr_groups: Dict[str, List] = {}
            for item in items:
                ref = item["datapoint"].standard_ref
                if ref not in dr_groups:
                    dr_groups[ref] = []
                dr_groups[ref].append(item)

            dr_details = []
            for dr_ref, dr_items in sorted(dr_groups.items()):
                dr_item = dr_items[0]
                dr_impact = [i["score"].total_impact_score for i in dr_items if i["score"].total_impact_score is not None]
                dr_financial = [i["score"].total_financial_score for i in dr_items if i["score"].total_financial_score is not None]
                dr_details.append({
                    "reference": dr_ref,
                    "description": dr_item["datapoint"].disclosure_requirement,
                    "paragraph": dr_item["datapoint"].paragraph_ref,
                    "avg_impact": round(sum(dr_impact) / len(dr_impact), 2) if dr_impact else 0,
                    "avg_financial": round(sum(dr_financial) / len(dr_financial), 2) if dr_financial else 0,
                    "is_material": any(i["score"].is_material for i in dr_items),
                    "datapoints": [
                        {
                            "paragraph": i["datapoint"].paragraph_ref,
                            "data_type": i["datapoint"].data_type,
                            "unit": i["datapoint"].unit,
                            "impact_score": i["score"].total_impact_score,
                            "financial_score": i["score"].total_financial_score,
                            "is_material": i["score"].is_material,
                            "rationale": i["score"].rationale,
                        }
                        for i in dr_items
                    ],
                })

            sections.append({
                "section": standard,
                "title": f"{standard}: {standard_name}",
                "content": {
                    "standard_name": standard_name,
                    "material_subtopics": subtopics,
                    "summary": (
                        f"This standard was identified as material with an average impact score "
                        f"of {avg_impact}/5.0 and an average financial score of {avg_financial}/5.0. "
                        f"A total of {len(items)} datapoints were assessed across "
                        f"{len(dr_groups)} disclosure requirements."
                    ),
                    "disclosure_requirements": dr_details,
                },
                "statistics": {
                    "total_datapoints": len(items),
                    "total_drs": len(dr_groups),
                    "average_impact_score": avg_impact,
                    "average_financial_score": avg_financial,
                    "material_datapoints": sum(1 for i in items if i["score"].is_material),
                },
            })

        return sections

    @staticmethod
    def generate_matrix_section(
        assessment: MaterialityAssessment,
        db: Session,
    ) -> Dict[str, Any]:
        """Genera la sezione della matrice di materialità."""
        matrix_data = ScoringEngine.get_materiality_matrix(db, str(assessment.id))

        material_items = [m for m in matrix_data if m["is_material"]]
        non_material = [m for m in matrix_data if not m["is_material"]]

        # Calcola distribuzione quadranti
        quadrants = {"high_high": 0, "high_low": 0, "low_high": 0, "low_low": 0}
        for m in matrix_data:
            pos = ScoringEngine.get_matrix_position(m["impact_score"], m["financial_score"])
            quadrants[pos] = quadrants.get(pos, 0) + 1

        return {
            "section": "Materiality Matrix",
            "title": "Double Materiality Matrix",
            "content": {
                "description": (
                    "The materiality matrix visualizes the position of each datapoint based on "
                    "its impact materiality score (x-axis) and financial materiality score (y-axis). "
                    "Datapoints above the threshold (3.0/5.0) in either dimension are considered material."
                ),
                "materiality_threshold": ScoringEngine.MATERIALITY_THRESHOLD,
                "quadrant_distribution": {
                    "double_material": quadrants["high_high"],
                    "impact_material": quadrants["high_low"],
                    "financial_material": quadrants["low_high"],
                    "non_material": quadrants["low_low"],
                },
                "material_datapoints": [
                    {
                        "reference": m["standard_ref"],
                        "name": m["datapoint_name"],
                        "impact_score": m["impact_score"],
                        "financial_score": m["financial_score"],
                        "quadrant": ScoringEngine.get_matrix_position(m["impact_score"], m["financial_score"]),
                    }
                    for m in material_items
                ],
                "non_material_count": len(non_material),
                "total_evaluated": len(matrix_data),
            },
        }

    @staticmethod
    def generate_full_materiality_report(
        company: Company,
        context: Optional[CompanyContext],
        assessment: MaterialityAssessment,
        db: Session,
    ) -> Dict[str, Any]:
        """Genera il report completo di doppia materialità con tutte le sezioni ESRS."""
        iro1 = MaterialityReportGenerator.generate_iro1_section(company, context, assessment, db)
        iro2 = MaterialityReportGenerator.generate_iro2_section(assessment, db)
        matrix = MaterialityReportGenerator.generate_matrix_section(assessment, db)
        standard_sections = MaterialityReportGenerator.generate_standard_detail_sections(assessment, db)
        scores_summary = ScoringEngine.calculate_assessment_scores(db, str(assessment.id))

        # Determina quali standard sono nel report
        material_standard_refs = list(set(
            MaterialityReportGenerator._extract_topic(m["standard_ref"])
            for m in matrix.get("content", {}).get("material_datapoints", [])
        ))

        # Ottieni tutti gli standard ESRS per contesto (anche non materiali)
        all_standards = list(MaterialityReportGenerator.STANDARD_NAMES.keys())
        non_material_standards = [s for s in all_standards if s not in material_standard_refs]

        total_in_db = scores_summary.get("total_datapoints_available_in_db", 0)
        
        return {
            "report_title": f"Double Materiality Assessment - {company.company_name}",
            "company_name": company.company_name,
            "reporting_year": company.reporting_year,
            "assessment_id": str(assessment.id),
            "assessment_date": str(assessment.assessment_date),
            "executive_summary": (
                f"The double materiality assessment for {company.company_name} evaluated "
                f"{scores_summary['total_datapoints']} out of {total_in_db} total ESRS datapoints "
                f"across all standards. "
                f"Of these, {scores_summary['material_datapoints']} were identified as material "
                f"({scores_summary['completion_percentage']}% completion rate). "
                f"Material topics identified: {', '.join(scores_summary['material_topics'])}."
            ),
            "executive_summary_detailed": {
                "total_datapoints": scores_summary["total_datapoints"],
                "total_datapoints_available_in_db": total_in_db,
                "scored_datapoints": scores_summary["scored_datapoints"],
                "material_datapoints": scores_summary["material_datapoints"],
                "completion_percentage": scores_summary["completion_percentage"],
                "average_impact_score": scores_summary["average_impact_score"],
                "average_financial_score": scores_summary["average_financial_score"],
                "material_topics": scores_summary["material_topics"],
                "assessed_standards": {
                    "total": len(all_standards),
                    "material": len(material_standard_refs),
                    "non_material": len(non_material_standards),
                    "material_list": material_standard_refs,
                    "non_material_list": non_material_standards,
                },
            },
            "sections": [
                iro1,                           # ESRS 2 IRO-1
                iro2,                           # ESRS 2 IRO-2
                matrix,                         # Materiality Matrix
            ] + standard_sections + [           # Per-standard sections (E1, E2, ..., G1)
                {
                    "section": "ESRS Datapoints Coverage",
                    "title": "Complete ESRS Datapoint Coverage Summary",
                    "content": {
                        "all_standards": all_standards,
                        "material_standards": material_standard_refs,
                        "non_material_standards": non_material_standards,
                        "total_esrs_datapoints_available": scores_summary["total_datapoints"],
                        "note": "Non-material standards are excluded from detailed reporting per ESRS 1 principle of materiality.",
                    },
                },
            ],
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
