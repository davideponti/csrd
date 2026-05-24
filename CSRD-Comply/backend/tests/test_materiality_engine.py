"""
CSRD Comply — Step 30: Unit tests for Materiality Engine.

Tests: IRO generation, scoring logic, materiality matrix.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestIROGenerator:
    """Test IRO (Impact, Risk, Opportunity) generation logic."""

    def test_iro_scaffold_structure(self):
        """Verifica che uno scaffold IRO abbia la struttura corretta."""
        from ai_engine.materiality_engine.iro_generator import IROGenerator

        iro = IROGenerator.generate_iro_scaffold(
            topic="ESRS E1",
            subtopic="Climate change mitigation",
        )
        assert iro is not None
        assert "id" in iro
        # The scaffold sets esrs_standard from matched topic
        assert iro.get("esrs_standard") == "ESRS E1"
        assert "impacts" in iro
        assert "risks" in iro
        assert "opportunities" in iro

    def test_iro_with_context(self):
        """IRO generation with company context."""
        from ai_engine.materiality_engine.iro_generator import IROGenerator

        context = {
            "sector": "C10",
            "activities": ["food manufacturing"],
            "countries": ["IT"],
            "employee_count": 50,
            "turnover": 5_000_000,
        }
        iro = IROGenerator.generate_iro_scaffold(
            topic="ESRS E1",
            subtopic="Energy consumption",
            context=context,
        )
        assert iro is not None
        assert iro.get("esrs_standard") == "ESRS E1"

    def test_get_sector_code(self):
        """Estrae la lettera del settore NACE."""
        from ai_engine.materiality_engine.iro_generator import IROGenerator

        assert IROGenerator.get_sector_code("C10") == "C"
        assert IROGenerator.get_sector_code("M70") == "M"
        assert IROGenerator.get_sector_code("") == ""

    def test_get_sector_benchmark(self):
        """Recupera benchmark di settore."""
        from ai_engine.materiality_engine.iro_generator import IROGenerator

        benchmark = IROGenerator.get_sector_benchmark("C10")
        assert benchmark["name"] == "Manifatturiero"
        assert benchmark["carbon_intensity"] == "high"

    def test_generate_iros_for_company(self):
        """Genera IRO completi per un'azienda."""
        from ai_engine.materiality_engine.iro_generator import IROGenerator

        iros = IROGenerator.generate_iros_for_company(
            company_sector="C10",
            employee_count=100,
        )
        assert len(iros) > 0
        # Should have sector IROs + generic IROs
        types = set(i.get("type") for i in iros)
        assert "impact" in types

    def test_iro_by_topic_filter(self):
        """Filtra IRO per topic."""
        from ai_engine.materiality_engine.iro_generator import IROGenerator

        iros = IROGenerator.generate_iros_for_company("C10")
        e1_iros = IROGenerator.get_iros_by_topic(iros, "ESRS E1")
        assert len(e1_iros) > 0
        for i in e1_iros:
            assert i["topic"] == "ESRS E1"

    def test_iro_summary(self):
        """Riepilogo degli IRO generati."""
        from ai_engine.materiality_engine.iro_generator import IROGenerator

        iros = IROGenerator.generate_iros_for_company("C10", employee_count=100)
        summary = IROGenerator.get_summary(iros)
        assert summary["total_iros"] == len(iros)
        assert "by_type" in summary
        assert "by_topic" in summary


class TestScoringEngine:
    """Test double materiality scoring logic."""

    def test_calculate_impact_score_basic(self):
        """Calcolo del punteggio di impatto con likelihood (EFRAG)."""
        from ai_engine.materiality_engine.scoring_engine import ScoringEngine

        # Formula EFRAG: weighted_severity * likelihood / 5
        # severity = (3*0.3 + 2*0.3 + 1*0.2) / (0.3+0.3+0.2) = 1.7/0.8 = 2.125
        # score = 2.125 * 4 / 5 = 1.7
        score = ScoringEngine.calculate_impact_score(
            scale=3, scope=2, irremediability=1, likelihood=4,
        )
        assert score == 1.7

    def test_calculate_impact_score_no_likelihood(self):
        """Calcolo del punteggio di impatto senza likelihood (EFRAG)."""
        from ai_engine.materiality_engine.scoring_engine import ScoringEngine

        # Without likelihood: weighted severity in scala 1-5
        # severity = (3*0.3 + 2*0.3 + 1*0.2) / 0.8 = 2.125 rounded to 2 dec = 2.12
        score = ScoringEngine.calculate_impact_score(
            scale=3, scope=2, irremediability=1, likelihood=None,
        )
        assert score == 2.12

    def test_calculate_impact_score_empty(self):
        """Punteggio zero quando tutti i parametri sono None."""
        from ai_engine.materiality_engine.scoring_engine import ScoringEngine

        score = ScoringEngine.calculate_impact_score(
            scale=None, scope=None, irremediability=None, likelihood=None,
        )
        assert score == 0.0

    def test_calculate_financial_score_weighted(self):
        """Calcolo del punteggio finanziario come media pesata."""
        from ai_engine.materiality_engine.scoring_engine import ScoringEngine

        # Formula: (magnitude*0.6 + likelihood*0.4) / (0.6+0.4)
        score = ScoringEngine.calculate_financial_score(
            magnitude=4, likelihood=3,
        )
        # (4*0.6 + 3*0.4) / 1.0 = (2.4 + 1.2) / 1.0 = 3.6
        assert score == 3.6

    def test_calculate_financial_score_only_magnitude(self):
        """Calcolo del punteggio finanziario con solo magnitudo."""
        from ai_engine.materiality_engine.scoring_engine import ScoringEngine

        score = ScoringEngine.calculate_financial_score(
            magnitude=4, likelihood=None,
        )
        # Only magnitude: 4*0.6/0.6 = 4.0
        assert score == 4.0

    def test_is_material_both_high(self):
        """Verifica che valori alti siano considerati materiali."""
        from ai_engine.materiality_engine.scoring_engine import ScoringEngine

        assert ScoringEngine.is_material(impact_score=15, financial_score=12) is True

    def test_is_material_both_low(self):
        """Verifica che valori bassi NON siano materiali."""
        from ai_engine.materiality_engine.scoring_engine import ScoringEngine

        assert ScoringEngine.is_material(impact_score=2, financial_score=1) is False

    def test_is_material_one_high_one_low(self):
        """Un valore alto basta per essere materiali (max >= 3)."""
        from ai_engine.materiality_engine.scoring_engine import ScoringEngine

        assert ScoringEngine.is_material(impact_score=14, financial_score=1) is True

    def test_is_material_custom_threshold(self):
        """Threshold di materialità personalizzato."""
        from ai_engine.materiality_engine.scoring_engine import ScoringEngine

        # Custom threshold: need max >= 8
        assert ScoringEngine.is_material(
            impact_score=9, financial_score=7, threshold=8
        ) is True  # max=9 >= 8

        assert ScoringEngine.is_material(
            impact_score=7, financial_score=7, threshold=8
        ) is False  # max=7 < 8

    def test_get_matrix_position_high_high(self):
        """Entrambi sopra 3 -> high_high."""
        from ai_engine.materiality_engine.scoring_engine import ScoringEngine

        pos = ScoringEngine.get_matrix_position(impact_score=15, financial_score=14)
        assert pos == "high_high"

    def test_get_matrix_position_low_low(self):
        """Entrambi sotto 3 -> low_low."""
        from ai_engine.materiality_engine.scoring_engine import ScoringEngine

        pos = ScoringEngine.get_matrix_position(impact_score=2, financial_score=1)
        assert pos == "low_low"

    def test_get_matrix_position_high_low(self):
        """Solo impact sopra 3 -> high_low."""
        from ai_engine.materiality_engine.scoring_engine import ScoringEngine

        pos = ScoringEngine.get_matrix_position(impact_score=5, financial_score=1)
        assert pos == "high_low"

    def test_calculate_double_materiality(self):
        """Verifica il calcolo del double materiality score."""
        from ai_engine.materiality_engine.scoring_engine import ScoringEngine

        result = ScoringEngine.calculate_double_materiality(
            impact_score=4.5, financial_score=2.0,
        )
        assert result["total_impact_score"] == 4.5
        assert result["total_financial_score"] == 2.0
        assert result["double_materiality_score"] == 4.5  # max
        assert result["is_material"] is True
        assert result["quadrant"] == "impact_material"


class TestMaterialityReport:
    """Test generazione report di materialità."""

    def test_report_generator_exists(self):
        """Verifica che il generatore di report esista."""
        from ai_engine.materiality_engine.materiality_report import MaterialityReportGenerator
        assert hasattr(MaterialityReportGenerator, 'generate_iro1_section')
        assert hasattr(MaterialityReportGenerator, 'generate_iro2_section')
        assert hasattr(MaterialityReportGenerator, 'generate_full_materiality_report')

    def test_generate_narrative_for_iro(self):
        """Genera narrativa testuale per un IRO."""
        from ai_engine.materiality_engine.materiality_report import MaterialityReportGenerator

        iro_data = {
            "topic": "ESRS E1",
            "name": "Emissioni dirette GHG",
            "type": "impact",
            "severity": "high",
        }
        narrative = MaterialityReportGenerator.generate_narrative_for_iro(
            iro_data, scores=[]
        )
        assert "ESRS E1" in narrative
        assert "impact" in narrative
        assert "high" in narrative
