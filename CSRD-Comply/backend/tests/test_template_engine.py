"""
Tests for the CSRD Report Template Engine.

Covers:
- Population of GHG section with real data (add vs replace mode)
- Complete end-to-end rendering with default template
- Scope 3 categories breakdown in GHG block
- Empty data edge case handling
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
