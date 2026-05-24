"""
CSRD Comply — Step 30: Unit tests for Regulatory Intelligence.

Tests: Web scraping, update analysis, AI advisory.
"""
import pytest
from datetime import date, timedelta


class TestRegulatoryScraper:
    """Test scraper di aggiornamenti normativi."""

    def test_scraper_initialization(self):
        """Verifica inizializzazione scraper."""
        from ai_engine.regulatory_intelligence.scraper import RegulatoryScraper

        scraper = RegulatoryScraper()
        assert scraper is not None

    def test_scraper_sources(self):
        """Verifica che le fonti siano configurate."""
        from ai_engine.regulatory_intelligence.scraper import RegulatoryScraper

        scraper = RegulatoryScraper()
        sources = scraper.get_sources()
        assert sources is not None
        if isinstance(sources, list):
            assert len(sources) > 0

    def test_parse_regulation_update(self):
        """Parsing di un aggiornamento normativo."""
        from ai_engine.regulatory_intelligence.scraper import RegulatoryScraper

        scraper = RegulatoryScraper()
        sample_data = {
            "title": "ESRS E1 Updated Disclosure Requirements 2026",
            "body": "The European Commission has updated the disclosure requirements for ESRS E1...",
            "date": "2026-01-15",
            "source": "EUR-Lex",
        }
        result = scraper.parse_update(sample_data)
        assert result is not None
        assert "regulation" in result or "standard" in result
        assert "effective_date" in result or "date" in result


class TestUpdateAnalyzer:
    """Test analizzatore di aggiornamenti normativi."""

    def test_analyze_update_impact(self):
        """Analisi impatto di un aggiornamento normativo."""
        from ai_engine.regulatory_intelligence.update_analyzer import UpdateAnalyzer

        analyzer = UpdateAnalyzer()
        update = {
            "regulation": "ESRS E1",
            "title": "Updated emission reporting thresholds",
            "summary": "The threshold for mandatory Scope 3 reporting has been lowered to 250 employees.",
            "effective_date": str(date.today() + timedelta(days=180)),
            "affected_standards": ["ESRS E1", "ESRS E1-6"],
        }
        company = {
            "sector": "C10",
            "employee_count": 300,
            "country": "IT",
        }
        result = analyzer.analyze_impact(update, company)
        assert result is not None
        assert "impact_level" in result
        assert result["impact_level"] in ("high", "medium", "low", "none")

    def test_analyze_high_impact(self):
        """Aggiornamento con alto impatto."""
        from ai_engine.regulatory_intelligence.update_analyzer import UpdateAnalyzer

        analyzer = UpdateAnalyzer()
        # Update che richiede nuovi datapoint rilevanti per l'azienda
        update = {
            "regulation": "ESRS S1",
            "title": "New workforce disclosure requirements",
            "summary": "All companies with >50 employees must report detailed workforce metrics...",
            "affected_standards": ["ESRS S1"],
        }
        company = {"sector": "M69", "employee_count": 150, "country": "IT"}
        result = analyzer.analyze_impact(update, company)
        assert result["impact_level"] in ("high", "medium")

    def test_analyze_no_impact(self):
        """Aggiornamento senza impatto per l'azienda."""
        from ai_engine.regulatory_intelligence.update_analyzer import UpdateAnalyzer

        analyzer = UpdateAnalyzer()
        update = {
            "regulation": "EU Taxonomy",
            "title": "Nuclear energy classification updated",
            "summary": "Updated technical screening criteria for nuclear energy.",
            "affected_standards": ["EU Taxonomy"],
        }
        company = {"sector": "M69", "activities": ["legal services"], "employee_count": 10}
        result = analyzer.analyze_impact(update, company)
        # Legal services shouldn't be impacted by nuclear energy taxonomy
        assert result["impact_level"] in ("low", "none")

    def test_compare_updates(self):
        """Comparazione tra due aggiornamenti normativi."""
        from ai_engine.regulatory_intelligence.update_analyzer import UpdateAnalyzer

        analyzer = UpdateAnalyzer()
        old = {"regulation": "ESRS E1", "title": "Old version"}
        new = {"regulation": "ESRS E1", "title": "New version", "summary": "Updated"}
        diff = analyzer.compare_updates(old, new)
        assert diff is not None
        assert "changes" in diff or "differences" in diff


class TestRegulatoryAdvisor:
    """Test consulente normativo AI-based."""

    def test_advisor_initialization(self):
        """Verifica inizializzazione advisor."""
        from ai_engine.regulatory_intelligence.advisor import RegulatoryAdvisor

        advisor = RegulatoryAdvisor()
        assert advisor is not None

    def test_generate_recommendation(self):
        """Generazione raccomandazione normativa."""
        from ai_engine.regulatory_intelligence.advisor import RegulatoryAdvisor

        advisor = RegulatoryAdvisor()
        company = {
            "company_name": "Test Srl",
            "sector": "C10",
            "employee_count": 50,
            "turnover": 5_000_000,
            "reporting_year": 2026,
        }
        result = advisor.generate_recommendation(company)
        assert result is not None
        assert "recommendations" in result or "advice" in result or "actions" in result

    def test_advisor_pending_deadlines(self):
        """Verifica scadenze imminenti."""
        from ai_engine.regulatory_intelligence.advisor import RegulatoryAdvisor

        advisor = RegulatoryAdvisor()
        deadlines = advisor.get_upcoming_deadlines()
        assert deadlines is not None
        if isinstance(deadlines, list):
            for d in deadlines:
                assert "deadline" in d
                assert "description" in d

    def test_advisor_company_specific_checklist(self):
        """Checklist specifica per azienda."""
        from ai_engine.regulatory_intelligence.advisor import RegulatoryAdvisor

        advisor = RegulatoryAdvisor()
        checklist = advisor.get_compliance_checklist(
            sector="C10",
            employee_count=50,
            country="IT",
        )
        assert checklist is not None
        if isinstance(checklist, list):
            assert len(checklist) > 0
            for item in checklist:
                assert "task" in item or "description" in item
                assert "status" in item or "required" in item
