"""
CSRD Comply — Scoring Engine (Step 10)

Calcola i punteggi di doppia materialità secondo EFRAG IG 1.
"""
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import (
    MaterialityAssessment, MaterialityScore, EsrsDatapoint,
    SustainabilityMatter, AssessmentStatus,
)


class ScoringEngine:
    """Motore di calcolo dei punteggi di doppia materialità."""

    # Threshold per materialità
    MATERIALITY_THRESHOLD = 3.0

    # Pesi per il calcolo Impact Score
    IMPACT_WEIGHTS = {
        "scale": 0.3,
        "scope": 0.3,
        "irremediability": 0.2,
        "likelihood": 0.2,
    }

    # Pesi per il calcolo Financial Score
    FINANCIAL_WEIGHTS = {
        "magnitude": 0.6,
        "likelihood": 0.4,
    }

    @staticmethod
    def calculate_impact_score(
        scale: Optional[int],
        scope: Optional[int],
        irremediability: Optional[int],
        likelihood: Optional[int],
    ) -> float:
        """
        Calcola Impact Materiality Score secondo EFRAG IG 1.
        
        Formula EFRAG:
        - Per impatti attuali (likelihood non fornita): 
            severity = (scale × weight_scale + scope × weight_scope + irremediability × weight_irremediability) / total_weight
            Valore normalizzato in scala 1-5.
        - Per impatti potenziali (likelihood fornita): 
            impact_score = severity × likelihood / 5
            Valore normalizzato in scala 1-5.
        """
        scores = []
        weights = []

        if scale is not None:
            scores.append(scale)
            weights.append(ScoringEngine.IMPACT_WEIGHTS["scale"])
        if scope is not None:
            scores.append(scope)
            weights.append(ScoringEngine.IMPACT_WEIGHTS["scope"])
        if irremediability is not None:
            scores.append(irremediability)
            weights.append(ScoringEngine.IMPACT_WEIGHTS["irremediability"])

        if not scores:
            return 0.0

        # Calcolo weighted severity
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0
        severity = sum(s * w for s, w in zip(scores, weights)) / total_weight

        if likelihood is not None:
            # Normalizza likelihood in scala 1-5: severity × likelihood / 5
            return round(severity * likelihood / 5, 2)
        else:
            return round(severity, 2)

    @staticmethod
    def calculate_financial_score(
        magnitude: Optional[int],
        likelihood: Optional[int],
    ) -> float:
        """
        Calcola Financial Materiality Score.
        
        Formula: (Magnitude × 0.6) + (Likelihood × 0.4)
        """
        scores = []
        weights = []

        if magnitude is not None:
            scores.append(magnitude)
            weights.append(ScoringEngine.FINANCIAL_WEIGHTS["magnitude"])
        if likelihood is not None:
            scores.append(likelihood)
            weights.append(ScoringEngine.FINANCIAL_WEIGHTS["likelihood"])

        if not scores:
            return 0.0

        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        return round(weighted_sum / total_weight, 2)

    @staticmethod
    def calculate_double_materiality(
        impact_score: float,
        financial_score: float,
    ) -> Dict[str, Any]:
        """Calcola il Double Materiality Score finale."""
        double_materiality_score = max(impact_score, financial_score)
        is_material = double_materiality_score >= ScoringEngine.MATERIALITY_THRESHOLD

        # Determina il quadrante
        if impact_score >= 3.0 and financial_score >= 3.0:
            quadrant = "double_material"  # Entrambi materiali
        elif impact_score >= 3.0:
            quadrant = "impact_material"  # Solo impact material
        elif financial_score >= 3.0:
            quadrant = "financial_material"  # Solo financial material
        else:
            quadrant = "non_material"  # Nessuno materiale

        return {
            "total_impact_score": impact_score,
            "total_financial_score": financial_score,
            "double_materiality_score": double_materiality_score,
            "is_material": is_material,
            "quadrant": quadrant,
        }

    @staticmethod
    def score_single_datapoint(
        db: Session,
        score_id: str,
        impact_scale: Optional[int] = None,
        impact_scope: Optional[int] = None,
        impact_irremediability: Optional[int] = None,
        impact_likelihood: Optional[int] = None,
        financial_magnitude: Optional[int] = None,
        financial_likelihood: Optional[int] = None,
        rationale: Optional[str] = None,
    ) -> MaterialityScore:
        """Calcola e aggiorna il punteggio per un singolo datapoint."""
        score = db.query(MaterialityScore).filter(
            MaterialityScore.id == score_id
        ).first()

        if not score:
            raise ValueError(f"Score {score_id} not found")

        # Aggiorna i valori se forniti
        if impact_scale is not None:
            score.impact_scale = impact_scale
        if impact_scope is not None:
            score.impact_scope = impact_scope
        if impact_irremediability is not None:
            score.impact_irremediability = impact_irremediability
        if impact_likelihood is not None:
            score.impact_likelihood = impact_likelihood
        if financial_magnitude is not None:
            score.financial_magnitude = financial_magnitude
        if financial_likelihood is not None:
            score.financial_likelihood = financial_likelihood
        if rationale is not None:
            score.rationale = rationale

        # Ricalcola i punteggi
        impact_score = ScoringEngine.calculate_impact_score(
            score.impact_scale, score.impact_scope,
            score.impact_irremediability, score.impact_likelihood,
        )
        financial_score = ScoringEngine.calculate_financial_score(
            score.financial_magnitude, score.financial_likelihood,
        )

        score.total_impact_score = impact_score
        score.total_financial_score = financial_score
        result = ScoringEngine.calculate_double_materiality(impact_score, financial_score)
        score.is_material = result["is_material"]

        db.commit()
        db.refresh(score)
        return score

    @staticmethod
    def calculate_assessment_scores(
        db: Session,
        assessment_id: str,
    ) -> Dict[str, Any]:
        """Calcola tutti i punteggi per un assessment completo."""
        scores = db.query(MaterialityScore).filter(
            MaterialityScore.assessment_id == assessment_id
        ).all()

        if not scores:
            return {
                "total_datapoints": 0,
                "scored_datapoints": 0,
                "material_datapoints": 0,
                "average_impact_score": 0.0,
                "average_financial_score": 0.0,
                "material_topics": [],
            }

        # Ricalcola tutti i punteggi
        for score in scores:
            if score.impact_scale is not None or score.financial_magnitude is not None:
                impact_score = ScoringEngine.calculate_impact_score(
                    score.impact_scale, score.impact_scope,
                    score.impact_irremediability, score.impact_likelihood,
                )
                financial_score = ScoringEngine.calculate_financial_score(
                    score.financial_magnitude, score.financial_likelihood,
                )
                result = ScoringEngine.calculate_double_materiality(impact_score, financial_score)
                score.total_impact_score = impact_score
                score.total_financial_score = financial_score
                score.is_material = result["is_material"]

        db.commit()

        # Considera scored se ha almeno uno dei due punteggi calcolati
        scored = [s for s in scores if s.total_impact_score is not None or s.total_financial_score is not None]
        material = [s for s in scores if s.is_material]

        # Calcola medie separatamente per impact e financial
        scored_impact = [s.total_impact_score for s in scored if s.total_impact_score is not None]
        scored_financial = [s.total_financial_score for s in scored if s.total_financial_score is not None]

        avg_impact = sum(scored_impact) / len(scored_impact) if scored_impact else 0.0
        avg_financial = sum(scored_financial) / len(scored_financial) if scored_financial else 0.0

        # Determina i topic materiali
        material_datapoint_ids = [s.datapoint_id for s in material]
        material_topics = []
        if material_datapoint_ids:
            topics = (
                db.query(SustainabilityMatter)
                .join(EsrsDatapoint, SustainabilityMatter.standard == func.split_part(EsrsDatapoint.standard_ref, ' ', 1))
                .filter(EsrsDatapoint.id.in_(material_datapoint_ids))
                .distinct()
                .all()
            )
            material_topics = [t.standard for t in topics]

        return {
            "total_datapoints": len(scores),
            "scored_datapoints": len(scored),
            "material_datapoints": len(material),
            "average_impact_score": round(avg_impact, 2),
            "average_financial_score": round(avg_financial, 2),
            "material_topics": list(set(material_topics)),
            "completion_percentage": round(len(scored) / len(scores) * 100) if scores else 0,
        }

    @staticmethod
    def is_material(impact_score: float, financial_score: float, threshold: float = None) -> bool:
        """Determine if material based on double materiality."""
        t = threshold if threshold is not None else ScoringEngine.MATERIALITY_THRESHOLD
        return max(impact_score, financial_score) >= t

    @staticmethod
    def get_matrix_position(impact_score: float, financial_score: float) -> str:
        """Get quadrant position in the double materiality matrix."""
        if impact_score >= 3.0 and financial_score >= 3.0:
            return "high_high"
        elif impact_score >= 3.0:
            return "high_low"
        elif financial_score >= 3.0:
            return "low_high"
        else:
            return "low_low"

    @staticmethod
    def get_materiality_matrix(
        db: Session,
        assessment_id: str,
    ) -> List[Dict]:
        """Restituisce i dati per la matrice di materialità (scatter plot)."""
        scores = db.query(MaterialityScore).filter(
            MaterialityScore.assessment_id == assessment_id
        ).all()

        matrix_data = []
        for score in scores:
            if score.total_impact_score is not None and score.total_financial_score is not None:
                datapoint = db.query(EsrsDatapoint).filter(
                    EsrsDatapoint.id == score.datapoint_id
                ).first()

                matrix_data.append({
                    "datapoint_id": str(score.datapoint_id),
                    "datapoint_name": datapoint.disclosure_requirement if datapoint else "Unknown",
                    "standard_ref": datapoint.standard_ref if datapoint else "",
                    "impact_score": score.total_impact_score,
                    "financial_score": score.total_financial_score,
                    "is_material": score.is_material,
                    "rationale": score.rationale,
                })

        return matrix_data
