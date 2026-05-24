"""
CSRD Comply — Step 30: Unit tests for iXBRL Tagging and Validation.

Tests: iXBRL tag generation, output validation, XHTML structure.
"""
import pytest


class TestIxbrlTagger:
    """Test tagger iXBRL."""

    def test_tagger_initialization(self):
        """Verifica che il tagger si inizializzi correttamente."""
        from ai_engine.report_generator.ixbrl_tagger import IxbrlTagger

        tagger = IxbrlTagger()
        assert tagger is not None

    def test_tag_numeric_value(self):
        """Tagging di un valore numerico."""
        from ai_engine.report_generator.ixbrl_tagger import IxbrlTagger

        tagger = IxbrlTagger()
        result = tagger.tag_value(
            standard="ESRS E1-6",
            concept="GHGScope1Emissions",
            value=1500.50,
            unit="tCO2eq",
            decimals=2,
        )
        assert result is not None
        assert "ix:nonNumeric" in result or "ix:nonFraction" in result or "ixbrl" in result.lower()

    def test_tag_textual_disclosure(self):
        """Tagging di una disclosure testuale."""
        from ai_engine.report_generator.ixbrl_tagger import IxbrlTagger

        tagger = IxbrlTagger()
        result = tagger.tag_text(
            standard="ESRS S1-1",
            concept="WorkforcePolicies",
            text="Our company has implemented anti-discrimination policies...",
        )
        assert result is not None

    def test_esrs_concept_registry(self):
        """Verifica che i concept ESRS siano registrati."""
        from ai_engine.report_generator.ixbrl_tagger import IxbrlTagger

        tagger = IxbrlTagger()
        concepts = tagger.get_registered_concepts()
        assert concepts is not None
        if isinstance(concepts, list):
            assert len(concepts) > 0
            esrs_concepts = [c for c in concepts if "ESRS" in c.get("standard", "")]
            assert len(esrs_concepts) > 0


class TestIxbrlValidator:
    """Test validatore iXBRL."""

    def test_validate_valid_xhtml(self):
        """Validazione di XHTML valido."""
        from ai_engine.report_generator.ixbrl_validator import IxbrlValidator

        validator = IxbrlValidator()
        valid_xhtml = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:ix="http://www.xbrl.org/2008/inlineXBRL">
<head><title>Test Report</title></head>
<body>
  <p>Test content</p>
</body>
</html>"""
        result = validator.validate_xhtml(valid_xhtml)
        assert result["valid"] is True
        assert len(result.get("errors", [])) == 0

    def test_validate_invalid_xhtml(self):
        """Validazione di XHTML non valido."""
        from ai_engine.report_generator.ixbrl_validator import IxbrlValidator

        validator = IxbrlValidator()
        invalid_xhtml = """<html><head></head><body><unclosed>"""
        result = validator.validate_xhtml(invalid_xhtml)
        # Should report at least one error or warning
        assert result["valid"] is False

    def test_validator_detects_missing_namespace(self):
        """Rilevazione di namespace mancanti."""
        from ai_engine.report_generator.ixbrl_validator import IxbrlValidator

        validator = IxbrlValidator()
        missing_ns = """<html><head></head><body><p>No iXBRL namespace</p></body></html>"""
        result = validator.validate_xhtml(missing_ns)
        # May still be valid XML but missing iXBRL elements
        assert result["valid"] is False or "warning" in result.get("errors", [])

    def test_validate_ixbrl_facts(self):
        """Validazione di fatti iXBRL."""
        from ai_engine.report_generator.ixbrl_validator import IxbrlValidator

        validator = IxbrlValidator()
        facts = [
            {"concept": "GHGScope1Emissions", "value": "1500.50", "unit": "tCO2eq"},
            {"concept": "TotalEmployees", "value": "50", "unit": "employees"},
        ]
        result = validator.validate_facts(facts)
        assert result is not None
        assert "valid" in result
        assert "total_checks" in result

    def test_validate_facts_missing_concept(self):
        """Validazione: fatto con concept mancante."""
        from ai_engine.report_generator.ixbrl_validator import IxbrlValidator

        validator = IxbrlValidator()
        facts = [
            {"concept": "", "value": "100", "unit": "tCO2eq"},
        ]
        result = validator.validate_facts(facts)
        assert result["valid"] is False

    def test_validate_facts_negative_value(self):
        """Validazione: valori negativi per emissioni."""
        from ai_engine.report_generator.ixbrl_validator import IxbrlValidator

        validator = IxbrlValidator()
        facts = [
            {"concept": "GHGScope1Emissions", "value": "-100", "unit": "tCO2eq"},
        ]
        result = validator.validate_facts(facts)
        # Negative emissions might be a warning
        assert result["valid"] is True or any(
            "negative" in w.get("description", "").lower()
            for w in result.get("warnings", [])
        )

    def test_arelle_integration_check(self):
        """Verifica che sia presente la logica di integrazione con Arelle."""
        from ai_engine.report_generator.ixbrl_validator import IxbrlValidator

        validator = IxbrlValidator()
        # Should have a method or flag for Arelle validation
        has_arelle = hasattr(validator, "validate_with_arelle")
        accepts_arelle_path = hasattr(validator, "arelle_path")
        assert has_arelle or accepts_arelle_path
