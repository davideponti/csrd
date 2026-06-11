"""
Tests for the CSRD Report Template Engine.

Covers:
- Population of GHG section with real data (add vs replace mode)
- Complete end-to-end rendering with default template
- Scope 3 categories breakdown in GHG block
- Empty data edge case handling
- Company context injection with semantic validation
- Phase 2 fallback removal (bare [TO BE CONFIRMED] preserved)
- Magnitude validation (facilities < 10k, years 1-10, EUR qualifier)
"""
import pytest
from ai_engine.report_generator.template_engine import (
    ReportTemplate,
    ReportSection,
    DisclosureRequirement,
    SectionType,
    MaterialityFilter,
)


class TestGHGE1_6:
    """Tests for ESRS E1-6 GHG Emissions disclosure."""

    def test_populate_section_no_existing_block(self):
        """
        TEST 1: populate_ghg_section su una sezione senza blocco esistente (add mode).
        Il metodo deve aggiungere il blocco quando non trova 'e1-6-ghg-table'.
        """
        template = ReportTemplate(company_name="Test Corp", reporting_year=2025)
        sec = ReportSection(
            section_id="env-e1",
            standard_ref="ESRS E1",
            title="Climate Change",
            section_type=SectionType.ENVIRONMENTAL,
            materiality_filter=MaterialityFilter.IF_MATERIAL,
            order=2,
            is_material=True,
            disclosure_requirements=[
                DisclosureRequirement(
                    dr_id="E1-6",
                    title="Gross Scopes 1, 2, 3 and Total GHG emissions",
                    paragraph_ref="54-61",
                    is_mandatory=True,
                    blocks=[],
                ),
            ],
        )
        template.add_section(sec)
        result = template.populate_ghg_section({
            "year": 2025,
            "scope1": 1250.5,
            "scope1_n1": 1300.0,
            "scope2_location": 850.3,
            "scope2_location_n1": 900.1,
            "scope2_market": 780.0,
            "scope2_market_n1": 820.0,
            "scope3": 4500.0,
            "scope3_n1": 4800.0,
        })
        assert result is True
        for s in template.sections:
            if s.section_id == "env-e1":
                for dr in s.disclosure_requirements:
                    if dr.dr_id == "E1-6":
                        assert len(dr.blocks) == 1
                        assert dr.blocks[0].block_id == "ghg-emissions-table"

    def test_complete_render_default_template(self):
        """
        TEST 2: Render finale completo con create_default_template.
        Verifica che tutti i dati GHG siano presenti nell'XHTML.
        """
        template2 = ReportTemplate.create_default_template(
            company_name="ACME SpA",
            reporting_year=2025,
            language="it",
        )
        template2.set_materiality(["ESRS E1"])
        template2.populate_ghg_section({
            "year": 2025,
            "scope1": 1250.0,
            "scope2_location": 850.0,
            "scope3": 4500.0,
        })
        xhtml = template2.render_to_xhtml()

        # Real data presence
        assert "1250.0" in xhtml, "Real data in XHTML"
        # Column labels
        assert "Scope 1" in xhtml
        assert "Scope 2" in xhtml
        assert "Scope 3" in xhtml
        # Total row
        assert "Total GHG" in xhtml
        # Section title
        assert "GHG Emissions Summary" in xhtml

    def test_build_ghg_block_with_scope3_categories(self):
        """
        TEST 3: build_ghg_emissions_block con scope3_categories.
        Le categorie Scope 3 devono apparire nella tabella.
        """
        emissions_data = {
            "year": 2025,
            "scope1": 1250.5,
            "scope1_n1": 1300.0,
            "scope2_location": 850.3,
            "scope2_location_n1": 900.1,
            "scope2_market": 780.0,
            "scope2_market_n1": 820.0,
            "scope3": 4500.0,
            "scope3_n1": 4800.0,
            "scope3_categories": {
                "Purchased goods": 2000.0,
                "Transportation": {"value": 800.5, "year_n1": {"value": 750.0}},
            },
        }
        block = ReportTemplate().build_ghg_emissions_block(emissions_data)
        assert block.content_type == "table"
        assert "Purchased goods" in block.content_html
        assert "Transportation" in block.content_html

    def test_empty_data_edge_case(self):
        """
        TEST 4: Empty data edge case.
        Con dati vuoti, la tabella deve mostrare '—' (em dash).
        """
        empty_block = ReportTemplate().build_ghg_emissions_block({})
        assert "—" in empty_block.content_html

    # ── Context Validation Tests ─────────────────────────────────

    def test_phase2_fallback_removed(self):
        """
        TEST 5: Bare [TO BE CONFIRMED] placeholders are NEVER replaced.
        Phase 2 fallback was the root cause of nonsense injection.
        """
        t = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        html_in = "<td>[TO BE CONFIRMED]</td><p>[TO BE CONFIRMED]</p>"
        t.set_company_context({"employee_count_total": "500", "annual_revenue_eur": "12500000"})
        result = t.resolve_placeholders(html_in)
        assert "[TO BE CONFIRMED]" in result, "Bare [TO BE CONFIRMED] was replaced!"
        assert "500" not in result, "Employee count leaked into bare placeholder!"
        assert "12,500,000" not in result, "Revenue leaked into bare placeholder!"

    def test_named_placeholders_resolve(self):
        """
        TEST 6: Named [TBC:key] placeholders still resolve with validation.
        """
        t = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        html_in = "<td>[TBC:employee_count_total]</td><td>[TBC:annual_revenue_eur]</td>"
        t.set_company_context({"employee_count_total": "500", "annual_revenue_eur": "12500000"})
        result = t.resolve_placeholders(html_in)
        assert "500" in result, "employee_count_total not injected"
        assert "EUR millions" in result or "12,500,000" in result, "EUR qualifier missing"

    def test_string_value_rejected_for_numeric_field(self):
        """
        TEST 7: String values must not be injected into numeric fields.
        """
        html_in = "<td>[TBC:employee_count_total]</td>"
        t = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        t.set_company_context({"employee_count_total": "not-a-number"})
        result = t.resolve_placeholders(html_in)
        assert "[TO BE CONFIRMED]" in result, "String value injected into numeric field!"
        assert "not-a-number" not in result, "String leaked into numeric field!"

    def test_numeric_value_rejected_for_string_field(self):
        """
        TEST 8: Numeric-looking values must not be injected into text fields.
        """
        html_in = "<td>[TBC:database_name]</td>"
        t = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        t.set_company_context({"database_name": "12345"})
        result = t.resolve_placeholders(html_in)
        assert "[TO BE CONFIRMED]" in result, "Numeric value injected into string field!"
        assert "12345" not in result, "Numeric leaked into string field!"

    def test_facilities_count_magnitude(self):
        """
        TEST 9: Facilities count must be < 10,000.
        """
        html_in = "<td>[TBC:pollution_facilities_count]</td>"
        t = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        t.set_company_context({"pollution_facilities_count": "12500"})
        result = t.resolve_placeholders(html_in)
        assert "[TO BE CONFIRMED]" in result, "12500 facilities was not rejected!"

        t2 = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        t2.set_company_context({"pollution_facilities_count": "5"})
        result = t2.resolve_placeholders(html_in)
        assert "5" in result, "5 facilities was not accepted"

    def test_timeline_years_magnitude(self):
        """
        TEST 10: Timeline years must be between 1 and 10.
        """
        html_in = "<td>[TBC:substitution_timeline_years]</td>"
        t = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        t.set_company_context({"substitution_timeline_years": "500"})
        result = t.resolve_placeholders(html_in)
        assert "[TO BE CONFIRMED]" in result, "500 years was not rejected!"

        t2 = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        t2.set_company_context({"substitution_timeline_years": "3"})
        result = t2.resolve_placeholders(html_in)
        assert "3" in result, "3 years was not accepted"

    def test_eur_investment_qualifier(self):
        """
        TEST 11: EUR investment must include thousands/millions qualifier.
        """
        html_in = "<td>[TBC:annual_revenue_eur]</td>"
        t = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        t.set_company_context({"annual_revenue_eur": "5000"})
        result = t.resolve_placeholders(html_in)
        assert "EUR thousands" in result, "EUR thousands qualifier missing"

        t2 = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        t2.set_company_context({"annual_revenue_eur": "5000000"})
        result = t2.resolve_placeholders(html_in)
        assert "EUR millions" in result, "EUR millions qualifier missing"

    def test_sector_text_only(self):
        """
        TEST 12: Sector field must only accept descriptive text, never numeric values.
        """
        html_in = "<td>[TBC:sector]</td>"
        t = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        t.set_company_context({"sector": "Manufacturing"})
        result = t.resolve_placeholders(html_in)
        assert "Manufacturing" in result, "Text sector value was rejected"

        t2 = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        t2.set_company_context({"sector": "12345"})
        result = t2.resolve_placeholders(html_in)
        assert "[TO BE CONFIRMED]" in result, "Numeric sector value was not rejected!"

    def test_e2_2_table_uses_named_placeholders(self):
        """
        TEST 13: E2-2 actions table must use [TBC:key] placeholders instead of bare [TO BE CONFIRMED].
        """
        t = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        t.set_company_context({
            "pollution_facilities_count": "5",
            "air_emissions_pm_reduction_pct": "25",
            "substitution_timeline_years": "3",
            "capex_pollution_eur": "1500000",
        })
        html_in = (
            "<td>Installation at [TBC:pollution_facilities_count] facilities</td>"
            "<td>[TBC:substitution_timeline_years] years</td>"
            "<td>[TBC:capex_pollution_eur]</td>"
        )
        result = t.resolve_placeholders(html_in)
        assert "5" in result, "Facilities count not injected"
        assert "3 years" in result, "Timeline not injected"
        assert "EUR" in result, "EUR qualifier not present"

    def test_bp2_sensitivity_table_uses_named_placeholders(self):
        """
        TEST 14: BP-2 sensitivity table must use [TBC:key] placeholders for database references.
        """
        html_in = "EEIO factors from [TBC:database_name] database; Factors sourced from [TBC:regulatory_database_name]"
        t = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        t.set_company_context({"database_name": "EEIO v2.0", "regulatory_database_name": "EEA/EMEP"})
        result = t.resolve_placeholders(html_in)
        assert "EEIO v2.0" in result, "database_name not injected into BP-2 table"
        assert "EEA/EMEP" in result, "regulatory_database_name not injected into BP-2 table"

    def test_empty_context_preserves_placeholders(self):
        """
        TEST 15: With empty company_context, all placeholders should remain.
        """
        html_in = "<td>[TBC:employee_count_total]</td><td>[TBC:annual_revenue_eur]</td>"
        t = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        # No context set
        result = t.resolve_placeholders(html_in)
        assert "[TO BE CONFIRMED]" in result, "Placeholders not preserved when no context"
        assert "[TBC:" not in result, "Raw TBC tag preserved but should have been replaced with [TO BE CONFIRMED]"

    def test_ghg_emissions_only_e1_fields(self):
        """
        TEST 16: GHG emissions values should only go into emission fields.
        """
        html_in = "<td>[TBC:scope1_emissions]</td>"
        t = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        t.set_company_context({"scope1_emissions": "2500.5"})
        result = t.resolve_placeholders(html_in)
        assert "2500.5" in result, "Emission float value not accepted"

        t2 = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        t2.set_company_context({"scope1_emissions": "not-numeric"})
        result = t2.resolve_placeholders(html_in)
        assert "[TO BE CONFIRMED]" in result, "Non-numeric emission value not rejected"

    def test_revenue_only_financial_fields(self):
        """
        TEST 17: Revenue values should only go into financial/currency fields.
        """
        html_in = "<td>[TBC:annual_revenue_eur]</td>"
        t = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        t.set_company_context({"annual_revenue_eur": "5000000"})
        result = t.resolve_placeholders(html_in)
        assert "EUR millions" in result, "Revenue not formatted with EUR qualifier"

        # Revenue should NOT be injectable into string fields
        html_in2 = "<td>[TBC:database_name]</td>"
        t2 = ReportTemplate(company_name="TestCorp", reporting_year=2025)
        t2.set_company_context({"database_name": "5000000"})
        result2 = t2.resolve_placeholders(html_in2)
        assert "[TO BE CONFIRMED]" in result2, "Numeric value (revenue-like) injected into string field!"