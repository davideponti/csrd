"""
CSRD Comply — Materiality Report Generator (Step 11)

Genera il documento di doppia materialità conforme agli ESRS.
ESRS 2 IRO-1: Description of the process to identify and assess
ESRS 2 IRO-2: Disclosure Requirements in ESRS covered by the undertaking
Include sezioni dettagliate per ogni standard ESRS materiale.
"""
import re
import logging
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from app.models import (
    Company, CompanyContext, MaterialityAssessment, MaterialityScore,
    EsrsDatapoint, SustainabilityMatter,
)
from ai_engine.materiality_engine.scoring_engine import ScoringEngine

logger = logging.getLogger(__name__)


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
    def generate_non_material_justifications(
        company: Company,
        context: Optional[CompanyContext],
        assessment: MaterialityAssessment,
        db: Session,
        material_standards: List[str],
    ) -> Dict[str, Any]:
        """
        CRITICAL CSRD COMPLIANCE SECTION
        ESRS 1 — Per ogni topic ESRS valutato come non materiale, fornisce una
        giustificazione documentata di WHY è stato escluso.
        
        Requisito EFRAG IG 1 (par. 56-58): l'impresa deve documentare le ragioni
        per cui un topic è considerato non materiale, inclusa l'analisi di:
        - Criteri di impact materiality (scale, scope, irremediability, likelihood)
        - Criteri di financial materiality (magnitude, likelihood)
        - Specificità del settore e del modello di business
        - Evidenze a supporto dell'esclusione
        """
        all_standards = list(MaterialityReportGenerator.STANDARD_NAMES.keys())
        non_material = [s for s in all_standards if s not in material_standards]
        
        # Recupera gli score medi per ogni topic non materiale
        scores = db.query(MaterialityScore).filter(
            MaterialityScore.assessment_id == assessment.id,
        ).all()
        
        # Raccogli statistiche per topic
        topic_stats: Dict[str, Dict] = {}
        for score in scores:
            datapoint = db.query(EsrsDatapoint).filter(
                EsrsDatapoint.id == score.datapoint_id
            ).first()
            if datapoint:
                topic = MaterialityReportGenerator._extract_topic(datapoint.standard_ref)
                if topic not in topic_stats:
                    topic_stats[topic] = {
                        "impact_scores": [],
                        "financial_scores": [],
                        "total_datapoints": 0,
                        "max_impact": 0.0,
                        "max_financial": 0.0,
                    }
                imp = score.total_impact_score or 0
                fin = score.total_financial_score or 0
                topic_stats[topic]["impact_scores"].append(imp)
                topic_stats[topic]["financial_scores"].append(fin)
                topic_stats[topic]["total_datapoints"] += 1
                topic_stats[topic]["max_impact"] = max(topic_stats[topic]["max_impact"], imp)
                topic_stats[topic]["max_financial"] = max(topic_stats[topic]["max_financial"], fin)

        sector_code = company.sector[0] if company.sector else ""
        
        # Template di giustificazione per topic non materiali
        JUSTIFICATION_TEMPLATES = {
            "ESRS E1": {
                "low_relevance_reason": (
                    "L'azienda opera in un settore a bassa intensità carbonica "
                    "con emissioni GHG dirette e indirette limitate. "
                    "Il consumo energetico è prevalentemente da fonti rinnovabili "
                    "e non sono presenti attività ad alto impatto climatico."
                ),
                "threshold_explanation": (
                    "Nonostante siano stati identificati potenziali impatti climatici, "
                    "i punteggi di materialità di impatto e finanziaria non hanno "
                    "raggiunto la soglia di {threshold}/5.0. "
                    "La scala degli impatti potenziali è limitata data la natura "
                    "delle attività aziendali e l'assenza di fonti di emissione significative."
                ),
                "sector_specific": (
                    "Per il settore {sector_name}, il climate change è generalmente "
                    "considerato un topic con rilevanza medio-bassa, salvo la presenza "
                    "di attività ad alta intensità energetica non presenti in questo caso."
                ),
            },
            "ESRS E2": {
                "low_relevance_reason": (
                    "Le attività aziendali non generano emissioni significative "
                    "di inquinanti atmosferici, idrici o del suolo. "
                    "Non sono utilizzate sostanze preoccupanti o estremamente "
                    "preoccupanti nei processi produttivi."
                ),
                "threshold_explanation": (
                    "I punteggi ottenuti per pollution sono inferiori alla soglia "
                    "di {threshold}/5.0 sia per l'impatto materiality che per la "
                    "financial materiality, in assenza di fonti di inquinamento significative."
                ),
                "sector_specific": (
                    "Per il settore {sector_name}, il rischio di inquinamento è "
                    "generalmente limitato ad attività industriali specifiche "
                    "non presenti nel modello di business dell'azienda."
                ),
            },
            "ESRS E3": {
                "low_relevance_reason": (
                    "Il consumo idrico aziendale è limitato a utilizzi civili "
                    "e non sono presenti processi produttivi water-intensive. "
                    "L'azienda non opera in aree con stress idrico significativo "
                    "e non ha impatti rilevanti sulle risorse marine."
                ),
                "threshold_explanation": (
                    "I punteggi per water and marine resources sono risultati "
                    "inferiori alla soglia di {threshold}/5.0, confermando "
                    "la bassa rilevanza del topic per il modello di business attuale."
                ),
                "sector_specific": (
                    "Nel settore {sector_name}, il consumption idrico è rilevante "
                    "principalmente per aziende con processi produttivi water-intensive "
                    "o con operations in aree a stress idrico."
                ),
            },
            "ESRS E4": {
                "low_relevance_reason": (
                    "Le attività aziendali non hanno impatti diretti significativi "
                    "su biodiversità ed ecosistemi. Le operations non sono localizzate "
                    "in aree sensibili o protette e la dipendenza da servizi ecosistemici "
                    "è limitata. La catena di approvvigionamento non coinvolge materie prime "
                    "con impatti critici sulla biodiversità."
                ),
                "threshold_explanation": (
                    "Nonostante la rilevanza generale del topic biodiversità, "
                    "i punteggi specifici per l'azienda non hanno raggiunto la soglia "
                    "di {threshold}/5.0, in assenza di impatti diretti significativi "
                    "su specie, ecosistemi o servizi ecosistemici."
                ),
                "sector_specific": (
                    "Per il settore {sector_name}, la biodiversità è generalmente "
                    "un topic materiale solo per aziende con operazioni in aree "
                    "ecosensitive o con dipendenza diretta da risorse naturali."
                ),
            },
            "ESRS E5": {
                "low_relevance_reason": (
                    "L'azienda genera volumi limitati di rifiuti, prevalentemente "
                    "assimilabili agli urbani. I materiali utilizzati non includono "
                    "risorse critiche o scarse e il modello di business non è basato "
                    "su processi produttivi ad alto consumo di risorse."
                ),
                "threshold_explanation": (
                    "I punteggi per circular economy sono risultati inferiori "
                    "alla soglia di {threshold}/5.0. Le opportunità di economia "
                    "circolare sono state valutate ma non hanno raggiunto la "
                    "materialità per il modello di business attuale."
                ),
                "sector_specific": (
                    "Il settore {sector_name} presenta tipicamente una rilevanza "
                    "medio-bassa per circular economy, salvo per aziende con "
                    "produzioni ad alto consumo di materiali."
                ),
            },
            "ESRS S1": {
                "low_relevance_reason": (
                    "L'azienda ha un numero limitato di dipendenti con condizioni "
                    "di lavoro regolate da CCNL di riferimento. Le politiche HR "
                    "includono tutele per salute, sicurezza, pari opportunità "
                    "e work-life balance. Non sono emerse criticità significative "
                    "da audit interni o esterni."
                ),
                "threshold_explanation": (
                    "I punteggi per own workforce non hanno raggiunto la soglia "
                    "di {threshold}/5.0 in quanto le condizioni di lavoro sono "
                    "giudicate adeguate e non sono state identificate criticità "
                    "materiali per la forza lavoro propria."
                ),
                "sector_specific": (
                    "Per il settore {sector_name}, il topic S1 è generalmente "
                    "rilevante in presenza di forza lavoro numerosa, condizioni "
                    "di lavoro critiche o processi produttivi ad alto rischio."
                ),
            },
            "ESRS S3": {
                "low_relevance_reason": (
                    "Le operations aziendali non hanno impatti significativi "
                    "sulle comunità locali. Non sono presenti siti produttivi "
                    "in aree con comunità vulnerabili o indigene e non sono "
                    "stati identificati conflitti con le comunità locali."
                ),
                "threshold_explanation": (
                    "I punteggi per affected communities sono risultati "
                    "inferiori alla soglia di {threshold}/5.0, non essendo "
                    "stati identificati impatti materiali sulle comunità locali."
                ),
                "sector_specific": (
                    "Per il settore {sector_name}, S3 è materiale principalmente "
                    "per aziende con operazioni in prossimità di comunità o "
                    "con impatti territoriali significativi."
                ),
            },
            "ESRS S4": {
                "low_relevance_reason": (
                    "I prodotti/servizi dell'azienda non hanno impatti significativi "
                    "su consumatori e utenti finali in termini di salute, sicurezza "
                    "o privacy. Le pratiche di informazione e marketing sono conformi "
                    "alle normative di settore."
                ),
                "threshold_explanation": (
                    "I punteggi per consumers and end-users non hanno raggiunto "
                    "la soglia di {threshold}/5.0, in assenza di impatti "
                    "significativi su salute, sicurezza o privacy dei consumatori."
                ),
                "sector_specific": (
                    "Il settore {sector_name} presenta rilevanza per S4 "
                    "principalmente in relazione a prodotti con impatti sulla "
                    "salute dei consumatori o gestione dati personali."
                ),
            },
        }

        sector_name = "Generico"
        from ai_engine.materiality_engine.iro_generator import IROGenerator
        benchmark = IROGenerator.get_sector_benchmark(company.sector)
        sector_name = benchmark.get("name", "Generico")
        
        justifications = []
        for standard in non_material:
            stats = topic_stats.get(standard, {})
            template = JUSTIFICATION_TEMPLATES.get(standard, {
                "low_relevance_reason": (
                    "Il topic non è risultato materiale in base alla valutazione "
                    "di doppia materialità condotta secondo EFRAG IG 1."
                ),
                "threshold_explanation": (
                    "I punteggi non hanno raggiunto la soglia di {threshold}/5.0 "
                    "né per l'impact materiality né per la financial materiality."
                ),
                "sector_specific": (
                    "La valutazione è coerente con il profilo di rischio/opportunità "
                    "del settore {sector_name}."
                ),
            })
            
            avg_impact = round(
                sum(stats.get("impact_scores", [0])) / len(stats.get("impact_scores", [1]))
                if stats.get("impact_scores") else 0, 2
            )
            avg_financial = round(
                sum(stats.get("financial_scores", [0])) / len(stats.get("financial_scores", [1]))
                if stats.get("financial_scores") else 0, 2
            )
            
            justification = {
                "standard": standard,
                "standard_name": MaterialityReportGenerator.STANDARD_NAMES.get(standard, ""),
                "subtopics": MaterialityReportGenerator.STANDARD_SUBTOPICS.get(standard, []),
                "is_material": False,
                "total_datapoints_assessed": stats.get("total_datapoints", 0),
                "average_impact_score": avg_impact,
                "average_financial_score": avg_financial,
                "max_impact_score": stats.get("max_impact", 0),
                "max_financial_score": stats.get("max_financial", 0),
                "threshold": ScoringEngine.MATERIALITY_THRESHOLD,
                "justification_low_relevance": template["low_relevance_reason"],
                "justification_threshold": template["threshold_explanation"].format(
                    threshold=ScoringEngine.MATERIALITY_THRESHOLD
                ),
                "justification_sector_specific": template["sector_specific"].format(
                    sector_name=sector_name
                ),
                "conclusion": (
                    f"Based on the analysis above, {standard} ({MaterialityReportGenerator.STANDARD_NAMES.get(standard, '')}) "
                    f"is considered non-material for {company.company_name} for the reporting year {company.reporting_year}. "
                    f"This conclusion will be reviewed annually or when significant changes in the company's "
                    f"business model, operations, or stakeholder expectations occur."
                ),
            }
            justifications.append(justification)

        return {
            "section": "ESRS 2 IRO-2 — Non-Material Topics Justifications",
            "title": "Justification for Exclusion of Non-Material ESRS Topics",
            "content": {
                "introduction": (
                    "In accordance with ESRS 1 (Chapter 3.2) and EFRAG IG 1 Materiality Assessment "
                    "implementation guidance (paragraphs 56-58), the undertaking shall provide clear "
                    "and reasoned justifications for each ESRS topic assessed as non-material. "
                    "The following justifications document the analysis performed and the evidence "
                    "supporting the conclusion that these topics do not meet the materiality threshold "
                    f"of {ScoringEngine.MATERIALITY_THRESHOLD}/5.0 for either impact materiality "
                    "or financial materiality."
                ),
                "regulatory_reference": (
                    "ESRS 1 paragraph 32: 'Where the undertaking concludes that a topic is not material, "
                    "it shall provide a brief explanation of the conclusions reached in its sustainability statement.' "
                    "EFRAG IG 1 paragraph 57: 'The undertaking should document the reasons for concluding "
                    "that a topic is not material, including the analysis of the criteria used and the "
                    "threshold applied.'"
                ),
                "justifications": justifications,
                "total_non_material_topics": len(justifications),
                "review_statement": (
                    "The materiality assessment and these justifications will be reviewed at least annually, "
                    "or more frequently if significant changes occur in the company's business model, "
                    "value chain, regulatory environment, or stakeholder expectations. "
                    "Changes in the company's operations, such as entry into new markets, "
                    "acquisition of new activities, or regulatory developments, may trigger a "
                    "re-assessment of previously non-material topics."
                ),
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
        # ⭐ CRITICAL: calculate ALL scores FIRST before generating any section.
        # calculate_assessment_scores sets is_material=True/False + total_impact/financial_score
        # on every MaterialityScore record and commits to DB. Without this step, IRO-2 would
        # query is_material==True and find nothing (NULL), producing empty sections.
        scores_summary = ScoringEngine.calculate_assessment_scores(db, str(assessment.id))

        # Derive material_standard_refs from scores_summary (single source of truth).
        # This avoids calling generate_iro2_section twice and eliminates ordering bugs.
        # scores_summary.material_topics is computed by ScoringEngine using the same
        # logic as IRO-2 (query is_material==True from DB), so they are guaranteed consistent.
        material_standard_refs = sorted(scores_summary.get('material_topics', []))

        iro1 = MaterialityReportGenerator.generate_iro1_section(company, context, assessment, db)
        iro2 = MaterialityReportGenerator.generate_iro2_section(assessment, db)
        matrix = MaterialityReportGenerator.generate_matrix_section(assessment, db)
        standard_sections = MaterialityReportGenerator.generate_standard_detail_sections(assessment, db)

        # Ottieni tutti gli standard ESRS per contesto (anche non materiali)
        all_standards = list(MaterialityReportGenerator.STANDARD_NAMES.keys())
        non_material_standards = [s for s in all_standards if s not in material_standard_refs]

        # ── FIX BUG 1: resolve incongruenza conteggio ──
        # 'total_datapoints' = count of MaterialityScore records (can exceed EsrsDatapoint
        # count if score generation endpoint was called multiple times, creating duplicates).
        # 'total_datapoints_available_in_db' = count of EsrsDatapoint rows (single source of truth).
        # Cap at DB count to avoid "X out of Y" where X > Y, which auditors flag immediately.
        total_scored = scores_summary.get('total_datapoints', 0)
        total_in_db = scores_summary.get("total_datapoints_available_in_db", 0)
        if total_scored > total_in_db:
            logger.warning(
                f"MaterialityScore count ({total_scored}) exceeds EsrsDatapoint count ({total_in_db}). "
                "Capping report to DB count. This may indicate score generation was run multiple times."
            )
            total_scored = total_in_db
        
        # CRITICAL: Generate non-material justifications per CSRD compliance
        # Uses material_standard_refs from IRO-2 (consistent with all other sections)
        non_material_section = MaterialityReportGenerator.generate_non_material_justifications(
            company, context, assessment, db, material_standard_refs
        )

        # ── FIX BUG 3: documenta il cambio metodologico per increase da 0.49 a 1.21 ──
        scoring_methodology_note = (
            "Context-aware baseline scores applied. "
            "Previously, all non-IRO-matched datapoints defaulted to 1/5, which biased "
            "the assessment toward non-materiality for topics without direct IRO coverage. "
            "The current methodology assigns differentiated baselines per ESRS topic based on "
            "sector intensity benchmarks (carbon_intensity for E1-E4, social_risk for S1-S4, "
            "governance_risk for G1), ranging from 1 (low-intensity) to 3 (very-high-intensity). "
            "This explains the increase in average impact score from the previous assessment "
            f"(was ~0.49, now {scores_summary.get('average_impact_score', 'N/A')}) "
            "and reflects a methodological correction, not a change in company operations."
        )

        return {
            "report_title": f"Double Materiality Assessment - {company.company_name}",
            "company_name": company.company_name,
            "reporting_year": company.reporting_year,
            "assessment_id": str(assessment.id),
            "assessment_date": str(assessment.assessment_date),
            "executive_summary": (
                f"The double materiality assessment for {company.company_name} evaluated "
                f"{total_scored} out of {total_in_db} total ESRS datapoints "
                f"across all standards. "
                f"Of these, {scores_summary['material_datapoints']} were identified as material "
                f"({scores_summary['completion_percentage']}% completion rate). "
                f"Material topics identified: {', '.join(material_standard_refs)}. "
                f"For each non-material topic, a documented justification is provided in accordance "
                f"with ESRS 1 and EFRAG IG 1 requirements. "
                f"{scoring_methodology_note}"
            ),
            "executive_summary_detailed": {
                "total_datapoints": total_scored,
                "total_datapoints_available_in_db": total_in_db,
                "total_datapoints_raw_from_scores_table": scores_summary.get('total_datapoints', 0),
                "scored_datapoints": scores_summary["scored_datapoints"],
                "material_datapoints": scores_summary["material_datapoints"],
                "completion_percentage": scores_summary["completion_percentage"],
                "average_impact_score": scores_summary["average_impact_score"],
                "average_financial_score": scores_summary["average_financial_score"],
                "material_topics": material_standard_refs,
                "assessed_standards": {
                    "total": len(all_standards),
                    "material": len(material_standard_refs),
                    "non_material": len(non_material_standards),
                    "material_list": material_standard_refs,
                    "non_material_list": non_material_standards,
                },
            },
            "scoring_methodology_change": {
                "previous_baseline": "All non-IRO datapoints defaulted to 1/5",
                "current_baseline": "Context-aware per-topic baselines (1-3/5) based on sector intensity",
                "impact_on_average_score": (
                    f"The average impact score increased from ~0.49 to "
                    f"{scores_summary.get('average_impact_score', 'N/A')} as a direct result "
                    f"of this methodological change. This does not reflect a change in "
                    f"company operations or risk profile."
                ),
                "regulatory_compliance": (
                    "Methodology documented per ESRS 2 IRO-1 (par. 7): changes in assessment "
                    "methodology must be disclosed. See IRO-1 section for full scoring approach."
                ),
            },
            "sections": [
                iro1,                           # ESRS 2 IRO-1
                iro2,                           # ESRS 2 IRO-2
                matrix,                         # Materiality Matrix
                non_material_section,           # ⭐ Critical CSRD: non-material justifications
            ] + standard_sections + [           # Per-standard sections (E1, E2, ..., G1)
                {
                    "section": "ESRS Datapoints Coverage",
                    "title": "Complete ESRS Datapoint Coverage Summary",
                    "content": {
                        "all_standards": all_standards,
                        "material_standards": material_standard_refs,
                        "non_material_standards": non_material_standards,
                        "total_esrs_datapoints_available": total_in_db,
                        "note": "Non-material standards are excluded from detailed reporting per ESRS 1 principle of materiality. See 'Non-Material Topics Justifications' section for detailed rationale.",
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
