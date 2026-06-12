"""
CSRD Comply — Template Engine per Report CSRD (Step 17)

Motore di template per la generazione di report CSRD conformi.
Architettura a blocchi: ogni sezione del report è composta da blocchi
riutilizzabili contenenti HTML, riferimenti ESRS e tag iXBRL.

Struttura report:
1. General Information (ESRS 1 & 2)
2. Environmental (E1-E5) — solo se materiale
3. Social (S1-S4) — solo se materiale
4. Governance (G1)
5. Dichiarazione di conformità
6. Note e assurance
"""
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import json


# ── Logging ──────────────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ── Enums ─────────────────────────────────────────────────────────

class SectionType(str, Enum):
    """Tipologia di sezione del report."""
    GENERAL = "general"
    ENVIRONMENTAL = "environmental"
    SOCIAL = "social"
    GOVERNANCE = "governance"
    COMPLIANCE = "compliance"
    ASSURANCE = "assurance"


class SubSectionType(str, Enum):
    """Sottosezioni fisse per ogni Disclosure Requirement."""
    GOVERNANCE = "governance"
    STRATEGY = "strategy"
    IRO_MANAGEMENT = "iro_management"
    METRICS_TARGETS = "metrics_targets"


class MaterialityFilter(str, Enum):
    """Filtro di materialità per una sezione."""
    ALWAYS = "always"            # Sempre inclusa (es. ESRS 2)
    IF_MATERIAL = "if_material"  # Solo se topic materiale
    CONDITIONAL = "conditional"  # Dipende da condizioni specifiche


# ── Data Classes ──────────────────────────────────────────────────

@dataclass
class XBRLTag:
    """
    Tag iXBRL per un datapoint nel report.
    
    Attributes:
        concept: Nome del concetto XBRL (es. "esrs:E1-6_Scope1")
        unit_ref: Riferimento all'unità di misura
        context_ref: Riferimento al contesto (periodo + scenario)
        scale: Scala del valore (0 = unit, 3 = thousand, 6 = million)
        decimals: Numero di decimali (INF = intero)
        format_attr: Formato opzionale (es. "#,##0.00")
    """
    concept: str
    unit_ref: str = "u_tCO2eq"
    context_ref: str = "c_current"
    scale: int = 0
    decimals: str = "INF"
    format_attr: Optional[str] = None


@dataclass
class ContentBlock:
    """
    Blocco di contenuto atomico del report.
    
    Ogni blocco rappresenta un singolo elemento di disclosure:
    - Un paragrafo narrativo
    - Una tabella di dati
    - Un grafico
    - Una lista di metriche
    
    Attributes:
        block_id: Identificativo univoco del blocco
        standard_ref: Riferimento ESRS (es. "ESRS E1-6")
        paragraph_ref: Riferimento paragrafo (es. "44(a)")
        title: Titolo del blocco
        content_html: Contenuto HTML renderizzato
        content_type: Tipo di contenuto (narrative, table, chart, list)
        datapoint_refs: Lista di riferimenti a datapoint coperti
        xbrl_tags: Lista di tag iXBRL associati
        order: Ordine di visualizzazione
        is_material: Se il blocco è materiale per l'azienda
    """
    block_id: str
    standard_ref: str
    paragraph_ref: str = ""
    title: str = ""
    content_html: str = ""
    content_type: str = "narrative"  # narrative, table, chart, list
    datapoint_refs: List[str] = field(default_factory=list)
    xbrl_tags: List[XBRLTag] = field(default_factory=list)
    order: int = 0
    is_material: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Converte il blocco in dizionario serializzabile."""
        return {
            "block_id": self.block_id,
            "standard_ref": self.standard_ref,
            "paragraph_ref": self.paragraph_ref,
            "title": self.title,
            "content_html": self.content_html,
            "content_type": self.content_type,
            "datapoint_refs": self.datapoint_refs,
            "xbrl_tags": [{
                "concept": t.concept,
                "unit_ref": t.unit_ref,
                "context_ref": t.context_ref,
                "scale": t.scale,
                "decimals": t.decimals,
            } for t in self.xbrl_tags],
            "order": self.order,
            "is_material": self.is_material,
        }


@dataclass
class DisclosureRequirement:
    """
    Disclosure Requirement (DR) ESRS.
    
    Ogni DR corrisponde a un paragrafo specifico degli ESRS
    e contiene uno o più ContentBlock.
    
    Attributes:
        dr_id: Identificativo del DR (es. "E1-6")
        title: Titolo del DR
        paragraph_ref: Riferimento paragrafo
        description: Descrizione testuale
        blocks: Lista di blocchi di contenuto
        sub_sections: Sottosezioni (Governance, Strategy, etc.)
        is_mandatory: Se il DR è obbligatorio
    """
    dr_id: str
    title: str
    paragraph_ref: str = ""
    description: str = ""
    blocks: List[ContentBlock] = field(default_factory=list)
    sub_sections: Dict[SubSectionType, List[ContentBlock]] = field(default_factory=dict)
    is_mandatory: bool = True


@dataclass
class ReportSection:
    """
    Sezione del report CSRD.
    
    Una sezione raggruppa più Disclosure Requirement sotto
    uno stesso standard ESRS (es. "ESRS E1").
    
    Attributes:
        section_id: Identificativo della sezione
        standard_ref: Riferimento standard ESRS
        title: Titolo della sezione
        section_type: Tipologia (general, environmental, etc.)
        materiality_filter: Filtro di materialità
        disclosure_requirements: Lista di DR
        order: Ordine di visualizzazione
        is_material: Se la sezione è materiale per l'azienda
    """
    section_id: str
    standard_ref: str
    title: str
    section_type: SectionType = SectionType.GENERAL
    materiality_filter: MaterialityFilter = MaterialityFilter.IF_MATERIAL
    disclosure_requirements: List[DisclosureRequirement] = field(default_factory=list)
    order: int = 0
    is_material: bool = True


@dataclass
class CoverPage:
    """Dati per la copertina del report."""
    company_name: str = ""
    report_title: str = ""
    reporting_year: int = 2026
    report_date: str = ""
    language: str = "en"
    logo_base64: Optional[str] = None
    company_vat: str = ""
    company_country: str = ""
    company_sector: str = ""
    employee_count: int = 0
    reporting_period: str = ""


class ReportTemplate:
    """
    Template principale per il report CSRD.
    
    Gestisce la struttura completa del report incluse:
    - Copertina e metadati
    - Sezioni ESRS con blocchi di contenuto
    - Tagging iXBRL
    - Multi-lingua
    
    Usage:
        template = ReportTemplate(
            company_name="ACME Srl",
            reporting_year=2026,
            language="it",
        )
        template.add_section(section)
        html = template.render_to_xhtml()
        xbrl = template.render_to_ixbrl()
    """

    # URI tassonomia XBRL ESRS
    XBRL_TAXONOMY_URI = "https://xbrl.efrag.org/esrs-set1-2023"

    # Template HTML base per la struttura del report
    HTML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:ixt="http://www.xbrl.org/inlineXBRL/transformation/2015-07-21"
      xmlns:xlink="http://www.w3.org/1999/xlink"
      xmlns:xbrli="http://www.xbrl.org/2003/instance">
<head>
    <meta charset="UTF-8"/>
    <title>{report_title}</title>
    <link rel="schema.esrs" href="{xbrl_taxonomy_uri}"/>
    <style>
        body {{ font-family: 'Arial', sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #1a365d; font-size: 24px; border-bottom: 2px solid #2b6cb0; padding-bottom: 8px; }}
        h2 {{ color: #2c5282; font-size: 20px; margin-top: 24px; }}
        h3 {{ color: #2d3748; font-size: 16px; margin-top: 16px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
        th, td {{ border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; }}
        th {{ background-color: #edf2f7; font-weight: 600; }}
        .cover-page {{ text-align: center; padding: 80px 40px; }}
        .cover-title {{ font-size: 28px; font-weight: bold; color: #1a365d; margin-bottom: 8px; }}
        .cover-subtitle {{ font-size: 18px; color: #4a5568; margin-bottom: 40px; }}
        .cover-meta {{ font-size: 14px; color: #718096; margin: 4px 0; }}
        .section-header {{ background-color: #ebf8ff; padding: 12px 16px; border-left: 4px solid #3182ce; margin: 24px 0 12px 0; }}
        .block-narrative {{ margin: 12px 0; }}
        .block-table {{ overflow-x: auto; }}
        .footnote {{ font-size: 12px; color: #718096; border-top: 1px solid #e2e8f0; margin-top: 40px; padding-top: 12px; }}
        .compliance-statement {{ border: 2px solid #38a169; padding: 20px; margin: 24px 0; border-radius: 8px; background-color: #f0fff4; }}
    </style>
</head>
<body>
{content_html}
</body>
</html>"""

    def __init__(
        self,
        company_name: str = "",
        reporting_year: int = 2026,
        language: str = "en",
        report_title: Optional[str] = None,
    ):
        """
        Inizializza il template del report.
        
        Args:
            company_name: Nome dell'azienda
            reporting_year: Anno di rendicontazione
            language: Lingua del report (en, it, de, fr, es)
            report_title: Titolo personalizzato del report
        """
        self.company_name = company_name
        self.reporting_year = reporting_year
        self.language = language
        self.report_title = report_title or self._default_title()

        # Copertina
        self.cover_page = CoverPage(
            company_name=company_name,
            report_title=self.report_title,
            reporting_year=reporting_year,
            language=language,
        )

        # Sezioni del report
        self.sections: List[ReportSection] = []

        # Metadati
        self.xbrl_taxonomy_uri = self.XBRL_TAXONOMY_URI
        self.generated_at: Optional[str] = None
        self.generated_by: str = "CSRD Comply AI Engine v1.0"
        self.esrs_version: str = "ESRS Set 1 — 2023"
        self.software_version: str = "1.0.0"

        # Contesto aziendale
        self.company_sector: str = ""
        self.employee_count: int = 0
        self.company_country: str = ""
        self.company_vat: str = ""
        self.currency: str = "EUR"  # Valuta predefinita per il report

        # Materiality tracking — populated by set_materiality()
        self.material_standards: List[str] = []
        self.non_material_standards: List[str] = []
        # Emissions data for narrative context
        self._emissions_data: Dict[str, Any] = {}

        # Company context data for placeholder resolution
        # Populated from CompanyContextSettings before rendering.
        # Each key maps to a value string. Empty/missing values keep [TBC:key].
        self.company_context: Dict[str, str] = {}

    # ── Field Registry: type, expected unit, magnitude hints ────────────
    # Used to validate injected values belong to conceptually matching fields.
    # Keys MUST match the keys used in the context_data dict in reports.py
    # so that company_context can be looked up and validated.
    #
    # Strict magnitude rules (per task requirements):
    #   - facilities_count must be < 10,000
    #   - years/timeline must be between 1 and 10
    #   - EUR investment must include thousands/millions qualifier (via currency display)
    #   - employee_count → only workforce headcount fields
    #   - revenue → only financial fields with EUR unit
    #   - ghg_emissions → only GHG/emissions fields (E1 section)
    #   - sector → only descriptive text fields, never numeric fields
    # Valid status values for action plan / Status columns (S1-4, etc.)
    VALID_STATUS_VALUES = {
        "In progress", "Planned", "Completed", "Not started",
        "Delayed", "Cancelled", "On hold", "Not applicable",
    }

    FIELD_REGISTRY: Dict[str, Dict[str, object]] = {
        # Company Profile — textual / identity fields
        "company_name":               {"section": "profile",       "type": "string",    "unit": None,             "magnitude": None},
        "country":                    {"section": "profile",       "type": "string",    "unit": None,             "magnitude": None},
        "sector":                     {"section": "profile",       "type": "string",    "unit": None,             "magnitude": None},
        # Action plan Status fields — text-only, reject numeric/percentage values
        "status_s1":                  {"section": "action_plan",   "type": "status_text","unit": None,            "magnitude": None},
        "status_s2":                  {"section": "action_plan",   "type": "status_text","unit": None,            "magnitude": None},
        "status_s3":                  {"section": "action_plan",   "type": "status_text","unit": None,            "magnitude": None},
        "status_s4":                  {"section": "action_plan",   "type": "status_text","unit": None,            "magnitude": None},
        "status_e1":                  {"section": "action_plan",   "type": "status_text","unit": None,            "magnitude": None},
        "status_e2":                  {"section": "action_plan",   "type": "status_text","unit": None,            "magnitude": None},
        "status_e3":                  {"section": "action_plan",   "type": "status_text","unit": None,            "magnitude": None},
        "status_e4":                  {"section": "action_plan",   "type": "status_text","unit": None,            "magnitude": None},
        "status_e5":                  {"section": "action_plan",   "type": "status_text","unit": None,            "magnitude": None},
        "status_g1":                  {"section": "action_plan",   "type": "status_text","unit": None,            "magnitude": None},
        "reporting_year":             {"section": "profile",       "type": "year",      "unit": None,             "magnitude": (2000, 2100)},
        "employee_count_total":       {"section": "workforce",     "type": "count",     "unit": "employees",      "magnitude": (1, 1_000_000)},
        "employee_count_permanent":   {"section": "workforce",     "type": "count",     "unit": "employees",      "magnitude": (0, 1_000_000)},
        "employee_count_temporary":   {"section": "workforce",     "type": "count",     "unit": "employees",      "magnitude": (0, 1_000_000)},
        "employee_count_male":        {"section": "workforce",     "type": "count",     "unit": "employees",      "magnitude": (0, 1_000_000)},
        "employee_count_female":      {"section": "workforce",     "type": "count",     "unit": "employees",      "magnitude": (0, 1_000_000)},
        "employee_count_other":       {"section": "workforce",     "type": "count",     "unit": "employees",      "magnitude": (0, 1_000_000)},
        "annual_revenue_eur":         {"section": "profile",       "type": "currency",  "unit": "EUR",            "magnitude": (0, 1e12)},
        "operational_sites_count":    {"section": "profile",       "type": "count",     "unit": "sites",          "magnitude": (1, 100_000)},
        # GHG Emissions — keys must match context dict in reports.py
        "scope1_emissions":           {"section": "emissions",     "type": "float",     "unit": "tCO2e",          "magnitude": (0, 1e9)},
        "scope2_location_emissions":  {"section": "emissions",     "type": "float",     "unit": "tCO2e",          "magnitude": (0, 1e9)},
        "scope2_market_emissions":    {"section": "emissions",     "type": "float",     "unit": "tCO2e",          "magnitude": (0, 1e9)},
        "scope3_total_emissions":     {"section": "emissions",     "type": "float",     "unit": "tCO2e",          "magnitude": (0, 1e9)},
        "scope3_material_categories": {"section": "emissions",     "type": "string",    "unit": None,             "magnitude": None},
        "emissions_baseline_year":    {"section": "emissions",     "type": "year",      "unit": None,             "magnitude": (2000, 2100)},
        "emissions_methodology":      {"section": "emissions",     "type": "string",    "unit": None,             "magnitude": None},
        # Supply Chain
        "tier1_suppliers_count":       {"section": "supply_chain", "type": "count",     "unit": "suppliers",      "magnitude": (0, 1_000_000)},
        "tier2_suppliers_estimated":   {"section": "supply_chain", "type": "count",     "unit": "suppliers",      "magnitude": (0, 10_000_000)},
        "value_chain_countries":       {"section": "supply_chain", "type": "string",    "unit": None,             "magnitude": None},
        "high_risk_countries":         {"section": "supply_chain", "type": "string",    "unit": None,             "magnitude": None},
        "suppliers_code_of_conduct_pct": {"section": "supply_chain","type": "percentage","unit": "%",             "magnitude": (0, 100)},
        "supplier_audits_last_year":   {"section": "supply_chain", "type": "count",     "unit": "audits",         "magnitude": (0, 1_000_000)},
        # Workforce KPIs
        "ltifr":                      {"section": "workforce",     "type": "float",     "unit": "per_1000",        "magnitude": (0, 500)},
        "fatal_accidents":            {"section": "workforce",     "type": "count",     "unit": "accidents",       "magnitude": (0, 1_000)},
        "voluntary_turnover_pct":     {"section": "workforce",     "type": "percentage","unit": "%",              "magnitude": (0, 100)},
        "total_turnover_pct":         {"section": "workforce",     "type": "percentage","unit": "%",              "magnitude": (0, 100)},
        "new_hires_count":            {"section": "workforce",     "type": "count",     "unit": "employees",       "magnitude": (0, 1_000_000)},
        "avg_training_hours_per_employee": {"section": "workforce","type": "float",     "unit": "hours",           "magnitude": (0, 10_000)},
        "women_in_management_pct":    {"section": "workforce",     "type": "percentage","unit": "%",              "magnitude": (0, 100)},
        "gender_pay_gap_pct":         {"section": "workforce",     "type": "percentage","unit": "%",              "magnitude": (-100, 100)},
        "union_coverage_pct":         {"section": "workforce",     "type": "percentage","unit": "%",              "magnitude": (0, 100)},
        "employee_engagement_score":  {"section": "workforce",     "type": "float",     "unit": "score",           "magnitude": (-100, 100)},
        "employees_with_disabilities_pct": {"section": "workforce","type": "percentage","unit": "%",              "magnitude": (0, 100)},
        "avg_tenure_years":           {"section": "workforce",     "type": "float",     "unit": "years",           "magnitude": (0, 60)},
        "avg_age_years":              {"section": "workforce",     "type": "float",     "unit": "years",           "magnitude": (15, 80)},
        # Payment Practices
        "standard_payment_terms_days":    {"section": "governance","type": "count",     "unit": "days",            "magnitude": (0, 365)},
        "avg_actual_payment_time_days":   {"section": "governance","type": "count",     "unit": "days",            "magnitude": (0, 365)},
        "invoices_paid_within_terms_pct": {"section": "governance","type": "percentage","unit": "%",              "magnitude": (0, 100)},
        "invoices_paid_late_pct":         {"section": "governance","type": "percentage","unit": "%",              "magnitude": (0, 100)},
        # Governance / Anti-corruption
        "anti_corruption_training_pct":   {"section": "governance","type": "percentage","unit": "%",              "magnitude": (0, 100)},
        "corruption_incidents_count":     {"section": "governance","type": "count",     "unit": "incidents",      "magnitude": (0, 100_000)},
        "whistleblowing_reports_count":   {"section": "governance","type": "count",     "unit": "reports",        "magnitude": (0, 1_000_000)},
        # Pollution-specific (ESRS E2) — strict magnitudes per task rules
        "substitution_timeline_years":    {"section": "pollution", "type": "count",     "unit": "years",          "magnitude": (1, 10)},        # timeline must be 1-10
        "pollution_facilities_count":     {"section": "pollution", "type": "count",     "unit": "facilities",     "magnitude": (0, 9_999)},     # must be < 10,000
        "air_emissions_pm_reduction_pct": {"section": "pollution", "type": "percentage","unit": "%",             "magnitude": (0, 100)},
        "air_emissions_voc_reduction_pct":{"section": "pollution", "type": "percentage","unit": "%",             "magnitude": (0, 100)},
        "hazardous_waste_treated_pct":    {"section": "pollution", "type": "percentage","unit": "%",             "magnitude": (0, 100)},
        "hazardous_waste_recovered_pct":  {"section": "pollution", "type": "percentage","unit": "%",             "magnitude": (0, 100)},
        "environmental_fte_count":        {"section": "pollution", "type": "count",     "unit": "FTE",            "magnitude": (0, 100_000)},
        "cems_facilities_count":          {"section": "pollution", "type": "count",     "unit": "facilities",     "magnitude": (0, 9_999)},     # must be < 10,000
        "svhc_substances_count":          {"section": "pollution", "type": "count",     "unit": "substances",     "magnitude": (0, 10_000)},
        "soil_remediation_sites_count":   {"section": "pollution", "type": "count",     "unit": "sites",          "magnitude": (0, 100_000)},
        "external_stakeholders_engaged":  {"section": "pollution", "type": "count",     "unit": "stakeholders",   "magnitude": (0, 1_000_000)},
        "financial_resources_eur":        {"section": "general",   "type": "currency",  "unit": "EUR",            "magnitude": (0, 1e12)},
        "opex_pollution_eur":             {"section": "pollution", "type": "currency",  "unit": "EUR",            "magnitude": (0, 1e12)},
        "capex_pollution_eur":            {"section": "pollution", "type": "currency",  "unit": "EUR",            "magnitude": (0, 1e12)},
        # Supply chain specific
        "tier1_workers_estimated":        {"section": "supply_chain","type": "count",   "unit": "workers",        "magnitude": (0, 100_000_000)},
        "tier2_workers_estimated":        {"section": "supply_chain","type": "count",   "unit": "workers",        "magnitude": (0, 100_000_000)},
        "supplier_countries_count":       {"section": "supply_chain","type": "count",   "unit": "countries",      "magnitude": (0, 250)},
        "suppliers_audited_count":        {"section": "supply_chain","type": "count",   "unit": "suppliers",      "magnitude": (0, 1_000_000)},
        "suppliers_with_cap_count":       {"section": "supply_chain","type": "count",   "unit": "suppliers",      "magnitude": (0, 1_000_000)},
        "suppliers_terminated_count":     {"section": "supply_chain","type": "count",   "unit": "suppliers",      "magnitude": (0, 1_000_000)},
        "grievance_languages_count":      {"section": "supply_chain","type": "count",   "unit": "languages",      "magnitude": (0, 200)},
        # Workforce grievances
        "grievances_received":            {"section": "workforce", "type": "count",     "unit": "grievances",     "magnitude": (0, 1_000_000)},
        "grievances_resolved":            {"section": "workforce", "type": "count",     "unit": "grievances",     "magnitude": (0, 1_000_000)},
        "grievance_resolution_days":      {"section": "workforce", "type": "count",     "unit": "days",           "magnitude": (0, 365)},
        "grievance_satisfaction_pct":     {"section": "workforce", "type": "percentage","unit": "%",             "magnitude": (0, 100)},
        # Countries / databases / text
        "database_name":                  {"section": "general",   "type": "string",    "unit": None,             "magnitude": None},
        "regulatory_database_name":       {"section": "general",   "type": "string",    "unit": None,             "magnitude": None},
        "substance_name":                 {"section": "pollution", "type": "string",    "unit": None,             "magnitude": None},
        "site_name":                      {"section": "general",   "type": "string",    "unit": None,             "magnitude": None},
        "target_year":                    {"section": "general",   "type": "year",      "unit": None,             "magnitude": (2000, 2100)},
        # Additional emission fields from template placeholders (non-context, but used in validation)
        "scope1_baseline":                {"section": "emissions", "type": "float",     "unit": "tCO2e",          "magnitude": (0, 1e9)},
        "scope2_location_baseline":       {"section": "emissions", "type": "float",     "unit": "tCO2e",          "magnitude": (0, 1e9)},
        "scope2_market_baseline":         {"section": "emissions", "type": "float",     "unit": "tCO2e",          "magnitude": (0, 1e9)},
        "scope3_baseline":                {"section": "emissions", "type": "float",     "unit": "tCO2e",          "magnitude": (0, 1e9)},
        # Generic stakeholder/target related fields used in templates
        "stakeholders_engaged_count":     {"section": "pollution", "type": "count",     "unit": "stakeholders",   "magnitude": (0, 1_000_000)},
    }

    def _validate_placeholder_value(self, key: str, value: str) -> bool:
        """
        Validate that *value* is plausible for the field identified by *key*.
        Checks:
          1. Type correctness (string fields reject bare numeric-looking values)
          2. Numeric magnitude against FIELD_REGISTRY ranges
          3. Section-awareness — the field's section is validated implicitly
             through FIELD_REGISTRY. A value that passes magnitude checks
             for its own section will be accepted; mismatching sections are
             caught by magnitude mismatches.
        Returns True if the value passes validation (or no metadata exists).
        """
        meta = self.FIELD_REGISTRY.get(key)
        if not meta:
            return True  # unknown field — allow passthrough

        field_type = meta.get("type")
        magnitude = meta.get("magnitude")

        # ── Status text fields (action plan Status column) ────────
        if field_type == "status_text":
            # Only accept valid status values — never percentages or numbers
            stripped = value.strip().lower()
            valid_lower = {s.lower() for s in self.VALID_STATUS_VALUES}
            if stripped in valid_lower:
                return True
            # Reject numeric/percentage values entirely
            cleaned_num = value.strip().replace(",", "").replace(" ", "").replace("%", "")
            try:
                float(cleaned_num)
                return False  # Numeric/percentage — reject
            except ValueError:
                pass
            # Unknown text value — still reject to avoid garbage injection
            return False

        # ── String-type fields ─────────────────────────────────────
        if field_type in ("string",):
            # Reject bare numeric-looking strings for string fields that
            # expect names (e.g. database_name, substance_name, site_name).
            # Also reject percentage-looking strings (e.g. "72.0%").
            # Allow if the value contains non-digit characters (i.e., real text).
            cleaned = value.strip().replace(",", "").replace(".", "").replace("%", "")
            if cleaned.isdigit():
                return False
            # Check if the value is a pure number with decimal or percentage
            try:
                float(value.strip().replace(",", "").replace(" ", "").replace("%", ""))
                # If the whole cleaned string is numeric, reject
                if cleaned.strip().isdigit():
                    return False
            except ValueError:
                pass
            return True  # Non-numeric text is fine for string fields

        # ── Numeric fields — try to parse ──────────────────────────
        # Strip % suffix before parsing for percentage fields
        cleaned_num = value.replace(",", "").replace(" ", "").replace("%", "")
        try:
            num_val = float(cleaned_num)
        except (ValueError, AttributeError):
            # Non-numeric value for numeric field — reject (keep TBC)
            return False

        # Year fields: must be integer and within plausible range
        if field_type == "year":
            if not value.replace(",", "").strip().isdigit():
                return False
            year_int = int(float(value))
            lo, hi = magnitude if magnitude else (1900, 2150)
            return lo <= year_int <= hi

        # Percentage fields: 0-100 range
        if field_type == "percentage":
            lo, hi = magnitude if magnitude else (0, 100)
            return lo <= num_val <= hi

        # Count fields: non-negative, within magnitude range
        if field_type == "count":
            lo, hi = magnitude if magnitude else (0, 1e12)
            return lo <= num_val <= hi

        # Currency: non-negative
        if field_type == "currency":
            lo, hi = magnitude if magnitude else (0, 1e12)
            return lo <= num_val <= hi

        # Float: within magnitude range
        if field_type == "float":
            lo, hi = magnitude if magnitude else (-1e12, 1e12)
            return lo <= num_val <= hi

        return True

    def _get_currency_display(self, key: str, value: str) -> str:
        """
        Format a currency value with appropriate unit annotation
        (EUR thousands / EUR millions / EUR billions) based on magnitude.
        
        Rules:
          - 0–999 → no unit annotation (but flag as suspicious for EUR)
          - 1,000–999,999 → EUR thousands
          - 1,000,000–999,999,999 → EUR millions
          - >= 1,000,000,000 → EUR billions
        
        Per task requirements: EUR investment MUST include thousands/millions qualifier.
        Values below 1,000 are flagged as suspicious but still formatted as bare EUR.
        """
        try:
            num_val = float(value.replace(",", "").replace(" ", ""))
        except (ValueError, AttributeError):
            return value

        if abs(num_val) < 1000:
            return f"{num_val:,.2f} EUR"
        elif abs(num_val) < 1_000_000:
            val_k = num_val / 1000
            return f"{val_k:,.2f} (EUR thousands)"
        elif abs(num_val) < 1_000_000_000:
            val_m = num_val / 1_000_000
            return f"{val_m:,.2f} (EUR millions)"
        else:
            val_b = num_val / 1_000_000_000
            return f"{val_b:,.2f} (EUR billions)"


    def set_company_context(self, ctx: Dict[str, str]) -> None:
        """
        Set company context data used to replace [TBC:key] placeholders
        throughout the report. Only non-empty values that pass semantic
        validation are stored; for any missing, empty, or invalid keys the
        placeholder [TBC:key] is preserved and renders as [TO BE CONFIRMED].

        Validation rules applied per FIELD_REGISTRY:
        - status_text fields: only accept whitelisted status strings
          (e.g. "In progress", "Planned", "Completed"), reject numeric
          and percentage values.
        - string fields: reject bare numeric-looking values.
        - numeric fields: reject non-numeric values.
        - percentage fields: ensure 0-100 range.
        - count/currency/float fields: ensure within magnitude bounds.
        """
        validated = {}
        for k, v in ctx.items():
            if not v:
                continue  # skip empty strings
            if not self._validate_placeholder_value(k, v):
                # Value fails semantic validation — skip it so the
                # placeholder renders as [TO BE CONFIRMED]
                logger.debug("set_company_context: value for '%s'='%s' "
                             "failed validation, skipping", k, v)
                continue
            validated[k] = v
        self.company_context = validated

    def _resolve_placeholder(self, text: str, key: str) -> str:
        """
        Replace occurrences of ``[TBC:<key>]`` in *text*
        with the value stored under *key* in ``company_context``, if one exists
        AND passes validation. If the key is missing, empty, or fails validation,
        the placeholder becomes '[TO BE CONFIRMED]'.

        For currency fields, the value is formatted with appropriate unit
        annotation (EUR thousands / EUR millions / EUR billions).
        """
        import re
        if not self.company_context:
            return text
        value = self.company_context.get(key)
        if not value:
            # No value supplied — leave as [TO BE CONFIRMED]
            return text.replace(f"[TBC:{key}]", "[TO BE CONFIRMED]")

        # Validation step: check unit/magnitude plausibility
        if not self._validate_placeholder_value(key, value):
            # Value exists but fails validation — keep [TO BE CONFIRMED]
            return text.replace(f"[TBC:{key}]", "[TO BE CONFIRMED]")

        # Check if this is a currency field — apply unit formatting
        meta = self.FIELD_REGISTRY.get(key, {})
        if meta.get("type") == "currency":
            formatted = self._get_currency_display(key, value)
            return text.replace(f"[TBC:{key}]", formatted)

        return text.replace(f"[TBC:{key}]", str(value))


    def resolve_placeholders(self, html: str) -> str:
        """
        Walk through all known company-context keys and replace
        ``[TBC:<key>]`` placeholders with the corresponding value
        wherever possible. If a key is missing in the context, the
        placeholder becomes '[TO BE CONFIRMED]'. Validation ensures
        the injected value is plausible for the target field.

        IMPORTANT: Only named placeholders [TBC:<key>] are resolved.
        Bare [TO BE CONFIRMED] placeholders are NEVER filled automatically
        because they have no semantic type information. This prevents
        nonsense like injecting an employee count into a timeline field.
        Any template HTML that uses bare [TO BE CONFIRMED] must be
        converted to use [TBC:<key>] placeholders instead.
        """
        result = html

        # Phase 1: per-key named placeholders ── [TBC:<key>] ────
        for key in self.FIELD_REGISTRY:
            if f"[TBC:{key}]" not in result:
                continue
            result = self._resolve_placeholder(result, key)

        return result

    def _default_title(self) -> str:
        """Genera il titolo predefinito del report."""
        return f"CSRD Sustainability Report {self.reporting_year}"

    # ── Sezioni predefinite del report ───────────────────────────

    # ── IRO-2 Table Builder ──────────────────────────────────────

    def _build_iro2_table_html(self) -> str:
        """
        Genera la tabella IRO-2 in modo DINAMICO basandosi sulla materialità
        effettiva delle sezioni (set_materiality()). I topic non materiali
        vengono mostrati con "—" (non material) invece di "✓".
        Per ESRS 1 Chapter 3.2 compliance, i topic non materiali elencati
        nella tabella rinviano alla sezione di giustificazione.
        """
        std_order = [
            "ESRS 2", "ESRS E1", "ESRS E2", "ESRS E3", "ESRS E4", "ESRS E5",
            "ESRS S1", "ESRS S2", "ESRS S3", "ESRS S4", "ESRS G1",
        ]

        rows = []
        for std in std_order:
            name = self.STANDARD_NAMES.get(std, std)
            dr_range = self.STANDARD_DR_RANGES.get(std, "")

            is_material = std in self.material_standards
            is_always = (std == "ESRS 2")

            # Determine materiality indicators
            if is_always:
                imp_mat = "Always"
                fin_mat = "Always"
            elif is_material:
                imp_mat = "✓"
                fin_mat = "✓"
            else:
                imp_mat = "—"
                fin_mat = "—"

            # Build DR column: if material, show DR range; if not, show pointer
            if is_material or is_always:
                dr_display = dr_range
            else:
                dr_display = (
                    f'Excluded — see '
                    f'<a href="#non-material-justifications" style="color:#2b6cb0;">'
                    f'Non-Material Topics Justifications</a>'
                )

            rows.append(f"""
            <tr{" style=\"background-color:#f0fff4;\"" if is_material else ""}{" style=\"background-color:#f0f0f0;color:#999;\"" if not is_material and not is_always else ""}>
                <td><strong>{std}</strong></td>
                <td>{name}</td>
                <td style="text-align:center;">{imp_mat}</td>
                <td style="text-align:center;">{fin_mat}</td>
                <td style="font-size:13px;">{dr_display}</td>
            </tr>""")

        rows_html = "\n".join(rows)

        # Counts
        material_count = len(self.material_standards)
        non_material_count = len(self.non_material_standards)

        return f"""<div class="iro-2-content">
    <h4>IRO-2 — Disclosure Requirements in ESRS covered by the undertaking</h4>
    <p>The following table lists the ESRS topics and sub-topics that have been identified as material for <strong>{self.company_name}</strong> through the double materiality assessment process described under IRO-1. Only the Disclosure Requirements corresponding to material topics are included in this sustainability statement.</p>
    <p>This list is subject to annual review and may be updated as the undertaking's activities, value chain, and stakeholder expectations evolve.</p>
    <h5>List of ESRS topics and Disclosure Requirements</h5>
    <table class="material-topics-table" style="width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;">
        <thead>
            <tr style="background-color:#1a365d;color:white;">
                <th style="padding:10px 12px;text-align:left;border:1px solid #2b6cb0;">ESRS Standard</th>
                <th style="padding:10px 12px;text-align:left;border:1px solid #2b6cb0;">Topic / Sub-topic</th>
                <th style="padding:10px 12px;text-align:center;border:1px solid #2b6cb0;">Impact Materiality</th>
                <th style="padding:10px 12px;text-align:center;border:1px solid #2b6cb0;">Financial Materiality</th>
                <th style="padding:10px 12px;text-align:left;border:1px solid #2b6cb0;">Material DRs included</th>
            </tr>
        </thead>
        <tbody>
{rows_html}
        </tbody>
    </table>
    <p style="font-size:12px;color:#718096;">
        <strong>Legend:</strong> "✓" = Material | "—" = Not material | "Always" = Mandatory (ESRS 2).
        Material topics: <strong>{material_count}</strong> | Non-material topics: <strong>{non_material_count}</strong>.
        For non-material topics, exclusion rationale is provided in the
        <a href="#non-material-justifications" style="color:#2b6cb0;">Non-Material Topics Justifications</a> section
        in accordance with ESRS 1 Chapter 3.2 and EFRAG IG 1 paragraphs 56-58.
    </p>
</div>"""

    # ── Non-Material Topics Justifications ──────────────────────

    def _build_non_material_justifications_html(self) -> str:
        """
        Genera la sezione di giustificazione per i topic non materiali,
        conforme a ESRS 1 Chapter 3.2 (par. 32) e EFRAG IG 1 (par. 56-58).

        Viene inclusa SOLO se ci sono topic non materiali.
        """
        if not self.non_material_standards:
            return ""

        # Exclusion rationale templates per standard (ESRS 1 Chapter 3.2 compliant)
        exclusion_rationale = {
            "ESRS E3": (
                "The undertaking's operations are not water-intensive. Water consumption is limited to "
                "domestic/civil use and no production processes require significant water withdrawals. "
                "The company does not operate in water-stressed areas and has no material impacts on "
                "marine resources."
            ),
            "ESRS E4": (
                "The undertaking's operations are not located in or near biodiversity-sensitive areas. "
                "No direct impact drivers on biodiversity loss have been identified. Dependencies on "
                "ecosystem services are limited to general services (e.g., water supply, air quality) "
                "that are not material to the business model."
            ),
            "ESRS E5": (
                "The undertaking generates limited waste volumes (predominantly non-hazardous municipal-type waste). "
                "Material sourcing does not involve critical or scarce resources. Circular economy opportunities "
                "were evaluated but did not meet the materiality threshold."
            ),
            "ESRS S3": (
                "The undertaking's operations and value chain do not have significant impacts on local communities. "
                "No production sites are located near vulnerable or indigenous communities. No material conflicts "
                "or grievances from affected communities have been identified."
            ),
            "ESRS S4": (
                "The undertaking's products and services do not pose material information-related impacts, "
                "personal safety risks, or social inclusion concerns for consumers and end-users. "
                "Marketing and information practices comply with sector regulations."
            ),
        }

        items_html = []
        for std in self.non_material_standards:
            name = self.STANDARD_NAMES.get(std, std)
            rationale = exclusion_rationale.get(std, (
                "This topic was assessed through the double materiality process and did not meet the "
                "materiality threshold for either impact materiality or financial materiality. "
                "The assessment will be reviewed annually."
            ))
            items_html.append(f"""
    <div class="non-material-topic" style="margin:16px 0;padding:12px 16px;border-left:4px solid #a0aec0;background-color:#f7fafc;">
        <h4 style="margin:0 0 4px 0;color:#4a5568;">{std} — {name}</h4>
        <p style="margin:4px 0;font-size:14px;color:#4a5568;">
            <strong>Exclusion rationale (ESRS 1 Ch. 3.2):</strong> {rationale}
        </p>
        <p style="margin:4px 0;font-size:13px;color:#718096;">
            <strong>ESRS reference:</strong> Per ESRS 1 paragraph 32, where the undertaking concludes that
            a sustainability topic is not material, it shall provide a brief explanation of the conclusions
            reached. This rationale is documented in accordance with EFRAG IG 1 paragraphs 56-58 and will be
            reassessed at least annually or when significant changes occur.
        </p>
    </div>""")

        return f"""<div class="non-material-section" id="non-material-justifications">
    <div class="section-header" style="background-color:#edf2f7;border-left-color:#a0aec0;">
        <h2>Non-Material Topics Justifications</h2>
        <p style="font-size:14px;color:#4a5568;">
            ESRS 1 Chapter 3.2 — Documented exclusion rationale for topics assessed as non-material
        </p>
    </div>
    <p>The following ESRS topics were assessed through the double materiality process and found to be
    <strong>not material</strong> for {self.company_name} for the reporting period. In accordance with
    ESRS 1 paragraph 32 and EFRAG IG 1 paragraphs 56-58, the undertaking provides a brief explanation
    of the conclusions reached for each topic.</p>
    <p style="font-size:13px;color:#718096;">
        <strong>Note:</strong> The materiality assessment will be reviewed at least annually. Changes in the
        company's business model, operations, value chain, regulatory environment, or stakeholder expectations
        may trigger a re-assessment of these topics.
    </p>
    {"".join(items_html)}
</div>
<hr/>"""

    def _build_cover_section(self) -> str:
        """Genera il blocco HTML della copertina."""
        return f"""
<div class="cover-page">
    <h1 class="cover-title">{self.cover_page.company_name}</h1>
    <p class="cover-subtitle">{self.cover_page.report_title}</p>
    <p class="cover-meta">Reporting Year: {self.cover_page.reporting_year}</p>
    <p class="cover-meta">Country: {self.cover_page.company_country or '[TO BE CONFIRMED]'}</p>
    <p class="cover-meta">Language: {self.cover_page.language.upper()}</p>
    <p class="cover-meta">Generated by: {self.generated_by}</p>
    <p class="cover-meta">ESRS Version: {self.esrs_version}</p>
</div>
<hr/>
"""

    def _build_toc_section(self) -> str:
        """Genera il blocco HTML del sommario."""
        toc_items = []
        for section in self.sections:
            if section.is_material:
                status = "Material" if section.is_material else "Not Material"
                toc_items.append(
                    f'<li><a href="#{section.section_id}">'
                    f'{section.title} ({section.standard_ref}) — {status}</a></li>'
                )

        # Add Non-Material Topics Justifications to TOC if any exist
        if self.non_material_standards:
            toc_items.append(
                f'<li><a href="#non-material-justifications">'
                f'Non-Material Topics Justifications (ESRS 1 Ch. 3.2) — Documented exclusion rationale for '
                f'{", ".join(self.non_material_standards)}</a></li>'
            )

        toc_html = "\n".join(toc_items)
        return f"""
<h2>Table of Contents</h2>
<ol>{toc_html}</ol>
<hr/>
"""

    def _build_compliance_statement(self) -> str:
        """Genera il blocco HTML della dichiarazione di conformità."""
        return f"""
<div class="compliance-statement">
    <h2>Compliance Statement</h2>
    <p>This sustainability report has been prepared in accordance with the
    European Sustainability Reporting Standards (ESRS) as adopted by the
    European Commission under the Corporate Sustainability Reporting
    Directive (CSRD) 2022/2464.</p>
    <p>The report covers the reporting period {self.cover_page.reporting_period or f"January 1, {self.reporting_year} to December 31, {self.reporting_year}"}
    for {self.company_name}.</p>
    <p><strong>ESRS Version:</strong> {self.esrs_version}</p>
    <p><strong>XBRL Taxonomy:</strong> <a href="{self.xbrl_taxonomy_uri}">{self.xbrl_taxonomy_uri}</a></p>
    <p><strong>Software:</strong> {self.generated_by}</p>
</div>
"""

    def _build_disclosure_requirement_html(
        self, dr: DisclosureRequirement
    ) -> str:
        """Genera HTML per un Disclosure Requirement."""
        blocks_html = []
        for block in sorted(dr.blocks, key=lambda b: b.order):
            if not block.is_material:
                continue

            block_html = ""

            if block.content_type == "narrative":
                block_html = f"""
<div class="block-narrative" id="{block.block_id}">
    <h3>{block.title}</h3>
    <p>{block.content_html}</p>
</div>"""

            elif block.content_type == "table":
                block_html = f"""
<div class="block-table" id="{block.block_id}">
    <h3>{block.title}</h3>
    {block.content_html}
</div>"""

            elif block.content_type == "list":
                block_html = f"""
<div class="block-list" id="{block.block_id}">
    <h3>{block.title}</h3>
    {block.content_html}
</div>"""

            blocks_html.append(block_html)

        # Sub-sections (Governance, Strategy, IRO Management, Metrics & Targets)
        for sub_type, sub_blocks in dr.sub_sections.items():
            sub_title = sub_type.value.replace("_", " ").title()
            blocks_html.append(f'<h3>{sub_title}</h3>')
            for block in sorted(sub_blocks, key=lambda b: b.order):
                if block.is_material:
                    blocks_html.append(
                        f'<div class="block-narrative" id="{block.block_id}">'
                        f'<p>{block.content_html}</p></div>'
                    )

        return f"""
<div class="disclosure-requirement">
    <h2>{dr.title} <small>({dr.dr_id})</small></h2>
    {''.join(blocks_html)}
</div>"""

    # ── GHG Emissions Section ───────────────────────────────────

    def _get_emissions_value(
        self,
        data: Any,
        key: str = "value",
        default: str = "—",
        fmt: Optional[str] = None,
    ) -> str:
        """
        Estrae un valore numerico da emissions_data, gestendo sia dict che scalar.

        Args:
            data: Valore o dict con chiave 'value'
            key: Chiave del dict da estrarre
            default: Valore di default se assente
            fmt: Formato opzionale (es. ",.1f" per 1 decimale)

        Returns:
            Valore formattato come stringa
        """
        if isinstance(data, dict):
            val = data.get(key, default)
        else:
            val = data if data is not None else default

        if val == "—" or val is None:
            return "—"

        try:
            num = float(val)
            if fmt:
                return f"{num:{fmt}}"
            return f"{num:,.1f}"
        except (TypeError, ValueError, KeyError):
            return str(val)

    def _build_ghg_table_html(
        self,
        emissions_data: Dict[str, Any],
    ) -> str:
        """
        Genera l'HTML della tabella GHG Emissions (ESRS E1-6, par. 54-61)
        leggendo i dati da emissions_data.

        La tabella include:
          - Scope 1 (tCO2e)
          - Scope 2 location-based (tCO2e)
          - Scope 2 market-based (tCO2e)
          - Scope 3 total (tCO2e) con breakdown per categoria (se disponibile)
          - Total GHG emissions (tCO2e)

        Args:
            emissions_data: Dict con dati emissioni.
                Campi attesi:
                  - scope1 / scope1_n1
                  - scope2_location / scope2_location_n1
                  - scope2_market / scope2_market_n1
                  - scope3 / scope3_n1
                  - scope3_categories: dict {category_name: value/dict}
                  - year (int): anno di rendicontazione

        Returns:
            Stringa HTML della tabella
        """
        year = emissions_data.get("year", self.reporting_year)
        year_n = str(year)
        year_n1 = str(year - 1)

        # Helper inline per estrarre valori
        def _val(data, key="value", default="—", fmt=".1f"):
            if isinstance(data, dict):
                v = data.get(key, default)
            else:
                v = data if data is not None else default
            if v == "—" or v is None:
                return "—"
            try:
                return f"{float(v):{fmt}}"
            except (TypeError, ValueError):
                return str(v)

        # Estrai dati
        scope1 = _val(emissions_data.get("scope1"))
        scope1_n1 = _val(emissions_data.get("scope1_n1"))

        scope2_loc = _val(emissions_data.get("scope2_location"))
        scope2_loc_n1 = _val(emissions_data.get("scope2_location_n1"))

        scope2_mkt = _val(emissions_data.get("scope2_market"))
        scope2_mkt_n1 = _val(emissions_data.get("scope2_market_n1"))

        scope3 = _val(emissions_data.get("scope3"))
        scope3_n1 = _val(emissions_data.get("scope3_n1"))

        # Calcola totali numerici
        def _safe_float(v: str) -> float:
            try:
                return float(v.replace(",", ""))
            except (ValueError, AttributeError):
                return 0.0

        s1_n = _safe_float(scope1)
        s2l_n = _safe_float(scope2_loc)
        s2m_n = _safe_float(scope2_mkt)
        s3_n = _safe_float(scope3)
        total_n = s1_n + s2l_n + s3_n
        s2_used = "market" if s2m_n else "location"

        s1_n1 = _safe_float(scope1_n1)
        s2l_n1 = _safe_float(scope2_loc_n1)
        s2m_n1 = _safe_float(scope2_mkt_n1)
        s3_n1 = _safe_float(scope3_n1)
        total_n1 = s1_n1 + s2l_n1 + s3_n1

        # Calcola variazioni percentuali
        def _pct_change(current: float, previous: float) -> str:
            if previous > 0:
                return f"{((current - previous) / previous * 100):+.1f}%"
            return "N/A"

        # Costruisci righe tabella
        rows_html = f"""
            <tr>
                <td style="font-weight:500;">Scope 1 (tCO₂e)</td>
                <td style="text-align:right;">{scope1_n1}</td>
                <td style="text-align:right;">{scope1}</td>
                <td style="text-align:right;">{_pct_change(s1_n, s1_n1)}</td>
            </tr>
            <tr>
                <td style="font-weight:500;">Scope 2 location-based (tCO₂e)</td>
                <td style="text-align:right;">{scope2_loc_n1}</td>
                <td style="text-align:right;">{scope2_loc}</td>
                <td style="text-align:right;">{_pct_change(s2l_n, s2l_n1)}</td>
            </tr>
            <tr>
                <td style="font-weight:500;">Scope 2 market-based (tCO₂e)</td>
                <td style="text-align:right;">{scope2_mkt_n1}</td>
                <td style="text-align:right;">{scope2_mkt}</td>
                <td style="text-align:right;">{_pct_change(s2m_n, s2m_n1)}</td>
            </tr>
            <tr>
                <td style="font-weight:500;">Scope 3 total (tCO₂e)</td>
                <td style="text-align:right;">{scope3_n1}</td>
                <td style="text-align:right;">{scope3}</td>
                <td style="text-align:right;">{_pct_change(s3_n, s3_n1)}</td>
            </tr>"""

        # Scope 3 breakdown per categoria (se disponibile)
        scope3_categories = emissions_data.get("scope3_categories", {})
        if scope3_categories:
            for cat_name, cat_data in scope3_categories.items():
                cat_val_n = _val(cat_data, "value") if isinstance(cat_data, dict) else _val(cat_data)
                cat_val_n1 = _val(cat_data.get("year_n1", {}), "value") if isinstance(cat_data, dict) else "—"
                cat_n = _safe_float(cat_val_n)
                cat_n1 = _safe_float(cat_val_n1)
                rows_html += f"""
            <tr>
                <td style="padding-left:32px;font-size:13px;color:#4a5568;">  {cat_name}</td>
                <td style="text-align:right;">{cat_val_n1}</td>
                <td style="text-align:right;">{cat_val_n}</td>
                <td style="text-align:right;">{_pct_change(cat_n, cat_n1)}</td>
            </tr>"""

        # Riga totale
        total_n_str = f"{total_n:,.1f}" if total_n > 0 else "—"
        total_n1_str = f"{total_n1:,.1f}" if total_n1 > 0 else "—"
        rows_html += f"""
            <tr style="font-weight:bold;background-color:#edf2f7;">
                <td><strong>Total GHG emissions (tCO₂e)</strong></td>
                <td style="text-align:right;"><strong>{total_n1_str}</strong></td>
                <td style="text-align:right;"><strong>{total_n_str}</strong></td>
                <td style="text-align:right;"><strong>{_pct_change(total_n, total_n1)}</strong></td>
            </tr>"""

        # Se c'è un solo valore non nullo per Scope 2, indica quale è stato usato
        scope2_note = ""
        if s2_used == "market" and s2l_n == 0:
            scope2_note = " (market-based used for total)"
        elif s2_used == "location" and s2m_n == 0:
            scope2_note = " (location-based used for total)"

        table_html = f"""
<table class="ghg-table" style="width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;">
    <thead>
        <tr style="background-color:#1a365d;color:white;">
            <th style="padding:10px 12px;text-align:left;border:1px solid #2b6cb0;">GHG Emissions</th>
            <th style="padding:10px 12px;text-align:right;border:1px solid #2b6cb0;width:120px;">{year_n1}</th>
            <th style="padding:10px 12px;text-align:right;border:1px solid #2b6cb0;width:120px;">{year_n}</th>
            <th style="padding:10px 12px;text-align:right;border:1px solid #2b6cb0;width:100px;">Change (%)</th>
        </tr>
    </thead>
    <tbody>
{rows_html}
    </tbody>
</table>
<p style="font-size:12px;color:#718096;margin-top:4px;">
    * Gross Scopes 1, 2{scope2_note}, 3 and Total GHG emissions (ESRS E1-6, par. 54-61).
    Methodology: GHG Protocol Corporate Standard.
</p>"""

        return table_html

    def build_ghg_emissions_block(
        self,
        emissions_data: Dict[str, Any],
        block_id: str = "ghg-emissions-table",
    ) -> ContentBlock:
        """
        Crea un ContentBlock completo per la sezione GHG Emissions.

        Args:
            emissions_data: Dict con dati emissioni Scope 1, 2, 3
            block_id: ID del blocco

        Returns:
            ContentBlock di tipo "table" con la tabella GHG popolata
        """
        table_html = self._build_ghg_table_html(emissions_data)

        return ContentBlock(
            block_id=block_id,
            standard_ref="ESRS E1",
            paragraph_ref="54-61",
            title="GHG Emissions Summary",
            content_html=table_html,
            content_type="table",
            datapoint_refs=[
                "ESRS E1-6.54(a)",
                "ESRS E1-6.54(b)",
                "ESRS E1-6.55",
            ],
            order=1,
        )

    def populate_ghg_section(
        self,
        emissions_data: Dict[str, Any],
        section_id: str = "env-e1",
        dr_id: str = "E1-6",
    ) -> bool:
        """
        Popola il DR E1-6 della sezione ambientale con dati GHG reali.

        Cerca il ContentBlock 'e1-6-ghg-table' nella sezione specificata
        e lo sostituisce con la tabella generata da emissions_data.

        Args:
            emissions_data: Dict con dati emissioni
            section_id: ID della sezione (default: "env-e1")
            dr_id: ID del Disclosure Requirement (default: "E1-6")

        Returns:
            True se il blocco è stato aggiornato, False altrimenti
        """
        ghg_block = self.build_ghg_emissions_block(emissions_data)

        for section in self.sections:
            if section.section_id == section_id:
                for dr in section.disclosure_requirements:
                    if dr.dr_id == dr_id:
                        for i, block in enumerate(dr.blocks):
                            if block.block_id == "e1-6-ghg-table":
                                dr.blocks[i] = ghg_block
                                return True
                        # Se non trovato, aggiungi il blocco
                        dr.blocks.append(ghg_block)
                        dr.blocks.sort(key=lambda b: b.order)
                        return True
        return False

    # ── Metodi principali ───────────────────────────────────────

    def add_section(self, section: ReportSection) -> None:
        """
        Aggiunge una sezione al report.
        
        Args:
            section: La sezione da aggiungere
        """
        self.sections.append(section)
        # Mantieni ordinamento per order
        self.sections.sort(key=lambda s: s.order)

    def add_block(
        self,
        section_id: str,
        dr_id: str,
        block: ContentBlock,
    ) -> bool:
        """
        Aggiunge un blocco di contenuto a una sezione/DR esistente.
        
        Args:
            section_id: ID della sezione
            dr_id: ID del Disclosure Requirement
            block: Il blocco di contenuto da aggiungere
            
        Returns:
            True se trovato e aggiunto, False altrimenti
        """
        for section in self.sections:
            if section.section_id == section_id:
                for dr in section.disclosure_requirements:
                    if dr.dr_id == dr_id:
                        dr.blocks.append(block)
                        dr.blocks.sort(key=lambda b: b.order)
                        return True
        return False

    def remove_non_material_sections(self) -> int:
        """
        Rimuove le sezioni/blocchi non materiali dal report.
        
        Returns:
            Numero di elementi rimossi
        """
        removed = 0
        self.sections = [s for s in self.sections if s.is_material]
        removed += 1

        for section in self.sections:
            section.disclosure_requirements = [
                dr for dr in section.disclosure_requirements
                if dr.is_mandatory or any(b.is_material for b in dr.blocks)
            ]
            for dr in section.disclosure_requirements:
                dr.blocks = [b for b in dr.blocks if b.is_material]
                removed += len(dr.blocks)

        return removed

    # ── Standard names and subtopics for IRO-2 table ─────────────
    STANDARD_NAMES = {
        "ESRS 2": "General Information",
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

    # DR ranges per standard for the IRO-2 table
    STANDARD_DR_RANGES = {
        "ESRS 2": "BP-1, BP-2, GOV-1, SBM-1, IRO-1, IRO-2",
        "ESRS E1": "E1-1 to E1-9 (as applicable)",
        "ESRS E2": "E2-1 to E2-5 (as applicable)",
        "ESRS E3": "E3-1 to E3-5 (as applicable)",
        "ESRS E4": "E4-1 to E4-5 (as applicable)",
        "ESRS E5": "E5-1 to E5-5 (as applicable)",
        "ESRS S1": "S1-1 to S1-6 (as applicable)",
        "ESRS S2": "S2-1 to S2-5 (as applicable)",
        "ESRS S3": "S3-1 to S3-5 (as applicable)",
        "ESRS S4": "S4-1 to S4-5 (as applicable)",
        "ESRS G1": "G1-1 to G1-6 (as applicable)",
    }

    def set_materiality(
        self,
        material_standards: List[str],
    ) -> None:
        """
        Imposta la materialità delle sezioni in base agli standard materiali.
        Also updates material_standards and non_material_standards tracking lists.
        
        Args:
            material_standards: Lista di standard_ref materiali (es. ["ESRS E1", "ESRS S1"])
        """
        self.material_standards = sorted(set(material_standards))
        self.non_material_standards = sorted(
            set(self.STANDARD_NAMES.keys()) - set(self.material_standards) - {"ESRS 2"}
        )

        for section in self.sections:
            if section.materiality_filter == MaterialityFilter.ALWAYS:
                section.is_material = True
            elif section.materiality_filter == MaterialityFilter.IF_MATERIAL:
                section.is_material = section.standard_ref in material_standards

    # ── Rendering ───────────────────────────────────────────────

    def _build_ghg_narrative_html(self, emissions_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Genera la narrativa GHG Emissions (ESRS E1-6, par. 56).
        Se è il primo anno di rendicontazione (ossia non ci sono dati
        dell'anno precedente), include una dichiarazione esplicita
        sull'assenza di dati comparativi, come richiesto da ESRS E1-6.

        Args:
            emissions_data: Dati emissioni opzionali per rilevare
                            il primo anno di rendicontazione.

        Returns:
            Stringa HTML della narrativa.
        """
        data = emissions_data or self._emissions_data
        scope1_n1 = data.get("scope1_n1")
        scope2_loc_n1 = data.get("scope2_location_n1")
        scope2_mkt_n1 = data.get("scope2_market_n1")
        scope3_n1 = data.get("scope3_n1")

        # Detect first reporting year: if all prior-year values are None/0/empty
        has_comparative_data = any(
            v not in (None, 0, 0.0, "0.0", "0", "—", "")
            for v in [scope1_n1, scope2_loc_n1, scope2_mkt_n1, scope3_n1]
        )

        comparative_statement = ""
        if not has_comparative_data:
            comparative_statement = f"""
    <div class="first-year-notice" style="margin:16px 0;padding:12px 16px;border-left:4px solid #ed8936;background-color:#fffaf0;">
        <p style="margin:0;font-size:14px;color:#744210;">
            <strong>First Reporting Year — No Comparative Data.</strong>
            As disclosed under ESRS E1-6 (paragraph 56), this is the first year in which
            <strong>{self.company_name}</strong> reports GHG emissions in accordance with the ESRS.
            Therefore, no prior-year comparative figures are available.
            Consistent with the transitional provisions under ESRS 1 Appendix C and ESRS E1-6,
            comparative information will be provided in the next reporting period.
            The undertaking has established internal data collection processes that will enable
            the reporting of comparative figures from the financial year {self.reporting_year}
            onwards.
        </p>
    </div>"""

        return f"""<div class="e1-6-narrative">
    <h4>GHG Emissions Narrative (ESRS E1-6, par. 56)</h4>
    {comparative_statement}
    <p>The GHG emissions disclosed in this section include Scope 1 (direct emissions from owned or controlled sources),
    Scope 2 (indirect emissions from the generation of purchased energy), and Scope 3 (other indirect emissions
    in the value chain) in accordance with the GHG Protocol Corporate Accounting and Reporting Standard.</p>
    <p>The organisational boundary has been defined using the operational control approach, consistent with the
    consolidation scope adopted for the financial statements. Emissions factors used for the calculation are
    sourced from recognised databases (e.g., DEFRA, IPCC, IEA).</p>
    <p>For Scope 3 emissions, the undertaking has identified and measured the material categories in accordance
    with the GHG Protocol Corporate Value Chain (Scope 3) Standard.</p>
    <p>Methodology refinements and data quality improvements are ongoing. The undertaking is committed to
    enhancing the completeness and accuracy of its emissions inventory over successive reporting cycles.</p>
</div>"""

    def _resolve_iro2_placeholder(self, content_html: str) -> str:
        """Sostituisce PLACEHOLDER_DYNAMIC_IRO2_TABLE con la tabella IRO-2 dinamica."""
        result = content_html
        if "PLACEHOLDER_DYNAMIC_IRO2_TABLE" in result:
            result = result.replace(
                "PLACEHOLDER_DYNAMIC_IRO2_TABLE",
                self._build_iro2_table_html()
            )
        if "PLACEHOLDER_E1_6_NARRATIVE" in result:
            result = result.replace(
                "PLACEHOLDER_E1_6_NARRATIVE",
                self._build_ghg_narrative_html()
            )
        return result

    def render_content_html(
        self,
        include_cover: bool = True,
        include_toc: bool = True,
        include_compliance: bool = True,
    ) -> str:
        """
        Renderizza il contenuto del report in HTML (senza header/body).
        
        Args:
            include_cover: Includi copertina
            include_toc: Includi sommario
            include_compliance: Includi dichiarazione di conformità
            
        Returns:
            HTML del contenuto del report
        """
        parts = []

        # Copertina
        if include_cover:
            parts.append(self._build_cover_section())

        # Sommario
        if include_toc:
            parts.append(self._build_toc_section())

        # Sezioni
        for section in self.sections:
            if not section.is_material:
                continue

            drs_html = []
            for dr in section.disclosure_requirements:
                drs_html.append(self._build_disclosure_requirement_html(dr))

            section_html = f"""
<div class="report-section" id="{section.section_id}">
    <div class="section-header">
        <h2>{section.title}</h2>
        <p>Standard: {section.standard_ref}</p>
    </div>
    {''.join(drs_html)}
</div>"""
            parts.append(section_html)

        # Non-Material Topics Justifications (ESRS 1 Chapter 3.2)
        non_mat = self._build_non_material_justifications_html()
        if non_mat:
            parts.append(non_mat)

        # Dichiarazione di conformità
        if include_compliance:
            parts.append(self._build_compliance_statement())

        # Note a piè di pagina
        parts.append(f"""
<div class="footnote">
    <p>Report generated by {self.generated_by} | {self.generated_at or ''}</p>
    <p>ESRS Taxonomy: {self.xbrl_taxonomy_uri}</p>
    <p>Software Version: {self.software_version} | Report Format: XHTML + iXBRL</p>
</div>""")

        raw = "\n".join(parts)
        resolved = self._resolve_iro2_placeholder(raw)
        return self.resolve_placeholders(resolved)

    def render_to_xhtml(self) -> str:
        """
        Renderizza il report completo in formato XHTML.
        
        Returns:
            Report completo in XHTML
        """
        content_html = self.render_content_html()

        return self.HTML_TEMPLATE.format(
            report_title=self.report_title,
            xbrl_taxonomy_uri=self.xbrl_taxonomy_uri,
            content_html=content_html,
        )

    def render_to_ixbrl(
        self,
        include_ixbrl_tags: bool = True,
    ) -> str:
        """
        Renderizza il report in formato iXBRL (XHTML + tag XBRL).
        
        Args:
            include_ixbrl_tags: Se includere i tag iXBRL inline
            
        Returns:
            Report in formato iXBRL
        """
        # Per ora genera XHTML di base; l'aggiunta dei tag iXBRL
        # verrà gestita da ixbrl_tagger.py (Step 20)
        return self.render_to_xhtml()

    def to_dict(self) -> Dict[str, Any]:
        """
        Converte il template in dizionario per serializzazione API.
        
        Returns:
            Dizionario con struttura completa del template
        """
        return {
            "meta": {
                "company_name": self.company_name,
                "report_title": self.report_title,
                "reporting_year": self.reporting_year,
                "language": self.language,
                "xbrl_taxonomy_uri": self.xbrl_taxonomy_uri,
                "esrs_version": self.esrs_version,
                "generated_by": self.generated_by,
                "generated_at": self.generated_at,
            },
            "cover_page": {
                "company_name": self.cover_page.company_name,
                "report_title": self.cover_page.report_title,
                "reporting_year": self.cover_page.reporting_year,
                "language": self.cover_page.language,
                "company_vat": self.cover_page.company_vat,
                "company_country": self.cover_page.company_country,
                "company_sector": self.cover_page.company_sector,
                "employee_count": self.cover_page.employee_count,
            },
            "sections": [
                {
                    "section_id": s.section_id,
                    "standard_ref": s.standard_ref,
                    "title": s.title,
                    "section_type": s.section_type.value,
                    "is_material": s.is_material,
                    "disclosure_requirements": [
                        {
                            "dr_id": dr.dr_id,
                            "title": dr.title,
                            "paragraph_ref": dr.paragraph_ref,
                            "is_mandatory": dr.is_mandatory,
                            "blocks": [b.to_dict() for b in dr.blocks],
                        }
                        for dr in s.disclosure_requirements
                    ],
                }
                for s in self.sections
            ],
        }

    def to_json(self, indent: int = 2) -> str:
        """
        Converte il template in JSON.
        
        Args:
            indent: Indentazione JSON
            
        Returns:
            Stringa JSON del template
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    # ── Factory methods per sezioni predefinite ──────────────────

    @classmethod
    def create_default_template(
        cls,
        company_name: str = "",
        reporting_year: int = 2026,
        language: str = "en",
    ) -> "ReportTemplate":
        """
        Crea un template predefinito con tutte le sezioni ESRS.
        
        Crea il template base con la struttura standard del report
        CSRD: General Information (ESRS 2), Environmental (E1-E5),
        Social (S1-S4), Governance (G1).
        
        Args:
            company_name: Nome dell'azienda
            reporting_year: Anno di rendicontazione
            language: Lingua del report
            
        Returns:
            ReportTemplate preconfigurato
        """
        template = cls(
            company_name=company_name,
            reporting_year=reporting_year,
            language=language,
        )

        # ── Sezione 1: General Information (ESRS 2) ──────────────
        general = ReportSection(
            section_id="general-info",
            standard_ref="ESRS 2",
            title="General Information",
            section_type=SectionType.GENERAL,
            materiality_filter=MaterialityFilter.ALWAYS,
            order=1,
            is_material=True,
            disclosure_requirements=[
                DisclosureRequirement(
                    dr_id="BP-1",
                    title="General basis for preparation of sustainability statements",
                    paragraph_ref="1-9",
                    is_mandatory=True,
                    blocks=[
                        ContentBlock(
                            block_id="bp-1-narrative",
                            standard_ref="ESRS 2",
                            paragraph_ref="1",
                            title="Basis of Preparation",
                            content_html=f"""<div class="bp-1-content">
    <h4>BP-1 — General basis for preparation of the sustainability statement</h4>
    <p>This sustainability statement has been prepared for <strong>{template.company_name}</strong> for the financial year ending <strong>{template.reporting_year}</strong> in accordance with the European Sustainability Reporting Standards (ESRS) as adopted by the European Commission under the Corporate Sustainability Reporting Directive (CSRD) 2022/2464.</p>
    <p>The statement covers the same scope and reporting perimeter as the financial statements of <strong>{template.company_name}</strong>. All consolidated subsidiaries and entities over which the undertaking exercises control or significant influence are included. No material entities have been excluded from the scope of this sustainability statement.</p>
    <p>This report has been prepared on a standalone basis using ESRS-compliant taxonomy (ESRS 2023). All disclosures marked as mandatory under ESRS 2 — General Information are included. For topic-specific standards, only those identified as material through the double materiality assessment (as described under IRO-1) are presented.</p>
    <p>The information presented herein has been prepared using reasonable and supportable assumptions, consistent with the financial reporting period and the undertaking's internal control framework. Where estimates have been used, these are clearly identified and described in accordance with ESRS 2 BP-2 — Disclosures in relation to specific circumstances.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ),
                    ],
                ),
                DisclosureRequirement(
                    dr_id="BP-2",
                    title="Disclosures in relation to specific circumstances",
                    paragraph_ref="10-17",
                    is_mandatory=True,
                    blocks=[
                        ContentBlock(
                            block_id="bp-2-narrative",
                            standard_ref="ESRS 2",
                            paragraph_ref="10",
                            title="Specific Circumstances",
                            content_html=f"""<div class="bp-2-content">
    <h4>BP-2 — Disclosures in relation to specific circumstances</h4>
    <p>In preparing this sustainability statement, <strong>{template.company_name}</strong> has exercised judgement and made estimates where precise data was not available, in accordance with ESRS 2 BP-2 (paragraphs 10-17). The following sections describe the key areas where estimates, assumptions, and forward-looking information have been used, as well as any departures from the standard disclosure requirements.</p>

    <h5>Estimates and measurement uncertainty</h5>
    <p>The preparation of sustainability information in accordance with ESRS requires management to make estimates and assumptions that affect the reported amounts and disclosures. Key areas of estimation include:</p>
    <ul>
        <li><strong>GHG emissions (Scope 3):</strong> Where direct data from value chain partners is not available, emissions have been estimated using spend-based and average-data methodologies, in accordance with the GHG Protocol Corporate Value Chain (Scope 3) Standard. The associated estimation uncertainty is described in ESRS E1-6.</li>
        <li><strong>Pollutant emissions (ESRS E2):</strong> Emissions of pollutants to air, water, and soil have been estimated using emission factors from technical literature and regulatory databases where direct monitoring data was not available for all sources.</li>
        <li><strong>Water consumption (ESRS E3):</strong> Water withdrawal and consumption data for certain non-metered facilities has been estimated based on industry benchmarks and operational parameters.</li>
        <li><strong>Biodiversity impacts (ESRS E4):</strong> The assessment of dependencies and impacts on biodiversity and ecosystems relies on spatial analysis tools and proxy data, as direct site-level surveys were not conducted at all locations.</li>
        <li><strong>Workforce metrics (ESRS S1):</strong> Certain workforce composition data, particularly for part-time and temporary employees across non-consolidated entities, has been estimated based on available payroll records and management information systems.</li>
    </ul>
    <p>All estimates are based on the most reliable information available at the time of reporting. Estimates are reviewed and updated annually as more accurate data becomes available. Actual results may differ from these estimates due to changes in circumstances, assumptions, or data quality improvements.</p>

    <h5>Forward-looking information and assumptions</h5>
    <p>This sustainability statement contains forward-looking information, including targets, transition plans, and anticipated financial effects. Such information is based on reasonable and supportable assumptions about future events and conditions, including:</p>
    <ul>
        <li>Projected regulatory and policy developments (including EU Taxonomy criteria and national transpositions of CSRD requirements).</li>
        <li>Expected technological advancements and their associated costs (e.g., renewable energy capacity, low-carbon production processes).</li>
        <li>Forecasted market conditions and stakeholder expectations.</li>
        <li>Climate scenarios aligned with the Paris Agreement (1.5°C and 2°C pathways) used for resilience analysis under ESRS E1.</li>
    </ul>
    <p>Forward-looking statements reflect management's best judgement at the reporting date and are subject to inherent uncertainties. Actual outcomes may differ materially from those projected. The undertaking does not undertake any obligation to update forward-looking statements except as required by applicable law or regulations.</p>

    <h5>Changes in preparation or presentation</h5>
    <p>Where there have been changes in the methods used to prepare or present sustainability information compared to the previous reporting period — including changes in scope, measurement methodologies, or data sources — these are clearly identified and explained in the relevant disclosure notes. The undertaking aims to maintain consistency in its reporting methodologies and will restate comparative figures where practicable to ensure comparability.</p>

    <h5>Errors and restatements</h5>
    <p>Any material errors identified in prior period disclosures are corrected and disclosed in accordance with ESRS 2 BP-2 (paragraph 17). The nature of the error, the amount of the correction, and the reason for the correction are described in the relevant disclosure note.</p>

    <h5>Sources of estimation uncertainty</h5>
    <table>
        <thead>
            <tr>
                <th>Area of estimation</th>
                <th>Nature of uncertainty</th>
                <th>Key assumptions used</th>
                <th>Sensitivity</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Scope 3 GHG emissions (Category 1 — Purchased goods and services)</td>
                <td>Spend-based methodology uses industry-average emission factors</td>
                <td>EEIO factors from [TBC:database_name] database; supplier spend classification accuracy &plusmn;10%</td>
                <td>A &plusmn;10% change in emission factors would result in a variation of approximately [TO BE CONFIRMED] tCO2e</td>
            </tr>
            <tr>
                <td>Pollutant emissions to air (NOx, SOx, PM)</td>
                <td>Emission factors based on equipment type and fuel consumption</td>
                <td>Factors sourced from [TBC:regulatory_database_name] regulatory database; operating hours estimated</td>
                <td>A &plusmn;15% change in operating hours would affect reported emissions by [TBC:air_emissions_pm_reduction_pct] kg/year</td>
            </tr>
            <tr>
                <td>Workforce gender pay gap</td>
                <td>Partially estimated for bonus and variable compensation components</td>
                <td>Bonus accrual rates based on historical data; estimated error margin &plusmn;2%</td>
                <td>Sensitivity analysis indicates a &plusmn;2% variation in total pay gap figures</td>
            </tr>
        </tbody>
    </table>

    <h5>Use of alternative measures and additional disclosures</h5>
    <p>Where a specific ESRS disclosure requirement has not been applied because the undertaking considers the matter not material, or because a transitional provision has been used, this is explicitly stated in the relevant section of this sustainability statement. The justification for non-disclosure follows the principles set out in ESRS 1 Chapter 3.2.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ),
                    ],
                ),
                DisclosureRequirement(
                    dr_id="GOV-1",
                    title="The role of the administrative, management and supervisory bodies",
                    paragraph_ref="18-23",
                    is_mandatory=True,
                    blocks=[
                        ContentBlock(
                            block_id="gov-1-narrative",
                            standard_ref="ESRS 2",
                            paragraph_ref="18",
                            title="Governance Structure",
                            content_html=f"""<div class="gov-1-content">
    <h4>GOV-1 — Role of administrative, management and supervisory bodies</h4>
    <p>The sustainability governance structure of <strong>{template.company_name}</strong> is designed to ensure effective oversight of sustainability-related impacts, risks and opportunities (IROs) at the highest level of the organisation. The administrative, management and supervisory bodies collectively bear responsibility for the undertaking's sustainability strategy, its alignment with the business model, and the integrity of the sustainability statement.</p>

    <h5>Board composition and expertise</h5>
    <p>The Board of Directors comprises individuals with collective competence in sustainability matters, including climate science, environmental management, social policy, and business ethics. At least one board member holds specific expertise in ESG (Environmental, Social and Governance) topics. The board composition is reviewed periodically against the sustainability competencies required to effectively oversee the undertaking's material IROs.</p>

    <h5>Roles and responsibilities</h5>
    <p>The following governance bodies have defined responsibilities in relation to sustainability:</p>
    <ul>
        <li><strong>Board of Directors:</strong> Approves the sustainability strategy, materiality assessment, and the sustainability statement. Reviews progress against sustainability targets at least annually.</li>
        <li><strong>Sustainability Committee (Board-level):</strong> Oversees the double materiality assessment process, monitors sustainability performance, and advises the board on sustainability-related risks and opportunities.</li>
        <li><strong>Audit Committee:</strong> Reviews the effectiveness of internal controls over sustainability reporting, including the verification and assurance processes.</li>
        <li><strong>Executive Management Team:</strong> Implements the sustainability strategy, allocates resources, and manages day-to-day sustainability performance across business units.</li>
        <li><strong>Chief Sustainability Officer (CSO):</strong> Reports directly to the CEO and coordinates cross-functional sustainability initiatives, including stakeholder engagement and disclosure preparation.</li>
    </ul>

    <h5>Information flow and reporting</h5>
    <p>Management reports to the Board on sustainability matters on a quarterly basis, or more frequently if material issues arise. The Sustainability Committee receives detailed updates on IRO identification, risk assessments, and progress toward targets. The internal audit function provides independent assurance on the accuracy of sustainability data reported to the Board.</p>

    <h5>Remuneration and incentives</h5>
    <p>Sustainability performance metrics are integrated into the variable remuneration framework for executive management. Key Performance Indicators (KPIs) linked to climate targets, workforce metrics, and business conduct are included in the annual bonus and long-term incentive plans, aligned with the undertaking's material sustainability priorities.</p>

    <h5>Skills and capacity building</h5>
    <p>Board members receive regular training on evolving sustainability regulations, including the CSRD and ESRS requirements. A formal sustainability competency matrix is maintained and updated annually to identify gaps and plan development activities. External advisors are engaged as needed to supplement internal expertise.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ),
                    ],
                ),
                DisclosureRequirement(
                    dr_id="SBM-1",
                    title="Strategy, business model and value chain",
                    paragraph_ref="24-31",
                    is_mandatory=True,
                    blocks=[
                        ContentBlock(
                            block_id="sbm-1-narrative",
                            standard_ref="ESRS 2",
                            paragraph_ref="24",
                            title="Strategy and Business Model",
                            content_html=f"""<div class="sbm-1-content">
    <h4>SBM-1 — Strategy, business model and value chain</h4>
    <p><strong>{template.company_name}</strong> operates in the <strong>{template.company_sector or '[TO BE CONFIRMED]'}</strong> sector, serving customers primarily in {template.company_country or '[TO BE CONFIRMED]'} and internationally. The undertaking's business model is centred on creating sustainable value through responsible operations, innovation, and stakeholder engagement.</p>

    <h5>Business model overview</h5>
    <p>The undertaking's business model is built on the following key pillars:</p>
    <ul>
        <li><strong>Value creation:</strong> Delivering products and services that meet customer needs while minimising environmental footprint and promoting social well-being.</li>
        <li><strong>Operational excellence:</strong> Continuous improvement of processes to enhance resource efficiency, reduce waste, and optimise energy consumption across all operations.</li>
        <li><strong>Innovation and digitalisation:</strong> Leveraging technology to develop sustainable solutions, improve supply chain transparency, and enable data-driven decision-making.</li>
        <li><strong>Stakeholder partnerships:</strong> Collaborating with suppliers, customers, employees, communities, and regulators to address shared sustainability challenges.</li>
    </ul>

    <h5>Value chain description</h5>
    <p>The undertaking's value chain encompasses the following stages:</p>
    <ul>
        <li><strong>Upstream:</strong> Sourcing of raw materials and components from suppliers, assessed for environmental and social performance through the undertaking's supplier due diligence process (<strong>{template.employee_count or '[TO BE CONFIRMED]'}</strong> employees are involved in procurement and supply chain management).</li>
        <li><strong>Direct operations:</strong> Manufacturing, service delivery, and corporate functions managed with a focus on reducing GHG emissions, promoting workforce health and safety, and upholding ethical business conduct.</li>
        <li><strong>Downstream:</strong> Distribution, product use, and end-of-life management. The undertaking engages with customers to promote circular economy principles and responsible consumption.</li>
    </ul>

    <h5>Key business relationships</h5>
    <p>The undertaking's key business relationships include B2B and B2C customers, long-term suppliers, joint venture partners, financial institutions, and local communities. These relationships are managed through dedicated account management, supplier codes of conduct, community engagement programmes, and regular stakeholder dialogues.</p>

    <h5>Products, services and markets</h5>
    <p>The undertaking offers a diversified portfolio of products and services tailored to the evolving needs of its target markets. Revenue is generated primarily through direct sales, recurring service contracts, and long-term customer relationships. The geographic footprint spans {template.company_country or 'multiple jurisdictions'}, with growth opportunities identified in sectors aligned with the sustainability transition.</p>

    <h5>Employees by geography and segment</h5>
    <p>As of the reporting date, <strong>{template.company_name}</strong> employs approximately <strong>{template.employee_count or '[TO BE CONFIRMED]'}</strong> people. The workforce is distributed across operational functions (production, logistics, sales) and support functions (administration, R&D, management). Employee engagement, training, and well-being are prioritised as key enablers of the sustainability strategy.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ),
                    ],
                ),
                DisclosureRequirement(
                    dr_id="IRO-1",
                    title="Description of the process to identify and assess material impacts, risks and opportunities",
                    paragraph_ref="32-41",
                    is_mandatory=True,
                    blocks=[
                        ContentBlock(
                            block_id="iro-1-narrative",
                            standard_ref="ESRS 2",
                            paragraph_ref="32",
                            title="IRO Identification Process",
                            content_html=f"""<div class="iro-1-content">
    <h4>IRO-1 — Description of the process to identify and assess material impacts, risks and opportunities</h4>
    <p><strong>{template.company_name}</strong> has established a structured double materiality assessment process to identify, assess, and prioritise sustainability-related impacts, risks and opportunities (IROs). This process is aligned with the requirements of ESRS 2 IRO-1 (paragraphs 32-41) and the EFRAG Implementation Guidance (IG 1).</p>

    <h5>Step 1: Context understanding and stakeholder identification</h5>
    <p>The process begins with an analysis of the undertaking's operating context, including regulatory trends, market developments, sector-specific sustainability issues, and stakeholder expectations. Key stakeholder groups are identified, including employees, customers, suppliers, investors, regulators, local communities, and civil society organisations. Stakeholder engagement activities are conducted through surveys, interviews, workshops, and ongoing dialogue channels.</p>

    <h5>Step 2: IRO identification</h5>
    <p>A comprehensive list of potential sustainability-related IROs is compiled drawing on:</p>
    <ul>
        <li>The full list of ESRS topics and sub-topics (ESRS 1, Appendix A)</li>
        <li>Sector-specific sustainability benchmarks and frameworks (e.g., SASB, GRI)</li>
        <li>Internal risk registers and enterprise risk management (ERM) data</li>
        <li>Stakeholder feedback and engagement outcomes</li>
        <li>Regulatory intelligence from sustainability regulations, including CSRD, EU Taxonomy, and Sector-specific ESRS</li>
        <li>Media and reputational analysis</li>
    </ul>
    <p>Each IRO is classified as either an <strong>impact</strong> (actual or potential, positive or negative) or a <strong>risk/opportunity</strong> (financial or strategic) in accordance with the double materiality principle.</p>

    <h5>Step 3: Impact materiality assessment</h5>
    <p>Impact materiality is assessed by evaluating the severity and likelihood of actual and potential impacts connected with the undertaking's operations and value chain:</p>
    <ul>
        <li><strong>Severity</strong> is determined by: (a) scale — how grave the impact is; (b) scope — how widespread the impact is; (c) irremediable character — whether and to what extent the impact can be remediated.</li>
        <li><strong>Likelihood</strong> is assessed for potential impacts using a probability scale.</li>
        <li><strong>Value chain</strong> impacts are assessed across upstream, direct operations, and downstream activities.</li>
    </ul>
    <p>Impacts are scored on a 1-5 scale and plotted on a materiality matrix. An impact is considered material if it exceeds a predefined materiality threshold, calibrated with reference to sector benchmarks and stakeholder perspectives.</p>

    <h5>Step 4: Financial materiality assessment</h5>
    <p>Financial materiality is assessed by evaluating the potential financial effects of sustainability-related risks and opportunities on the undertaking's development, performance, and position. This includes:</p>
    <ul>
        <li><strong>Risk assessment:</strong> Identification of physical, transition, and liability risks, evaluated using scenario analysis where appropriate (e.g., climate scenarios for ESRS E1).</li>
        <li><strong>Opportunity assessment:</strong> Identification of strategic opportunities arising from sustainability trends, regulatory changes, and market shifts.</li>
        <li><strong>Quantification:</strong> Where feasible, financial effects are quantified using risk models, discounted cash flow analysis, and sensitivity analysis. Qualitative assessments are used where quantification is not practicable.</li>
    </ul>

    <h5>Step 5: Aggregation and materiality determination</h5>
    <p>The results of the impact and financial materiality assessments are aggregated in a double materiality matrix. An IRO is deemed material if it meets the materiality threshold on either the impact dimension, the financial dimension, or both. The Board and Sustainability Committee review and validate the materiality determination annually.</p>

    <h5>Step 6: Update and review cycle</h5>
    <p>The materiality assessment is updated at least annually, or more frequently if significant changes in the operating context, regulatory environment, or stakeholder expectations occur. The process is documented and subject to internal audit review to ensure consistency, completeness, and adherence to ESRS requirements.</p>

    <h5>Key assumptions and limitations</h5>
    <p>The assessment relies on reasonable and supportable information available at the time of assessment. Where data gaps exist, estimates are used and disclosed. External factors, including regulatory changes and market volatility, may affect the accuracy of forward-looking assessments. The undertaking continues to refine its data collection and assessment methodologies in line with evolving ESRS guidance and emerging best practices.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ),
                    ],
                ),
                DisclosureRequirement(
                    dr_id="IRO-2",
                    title="Disclosure Requirements in ESRS covered by the undertaking",
                    paragraph_ref="42-48",
                    is_mandatory=True,
                    blocks=[
                        ContentBlock(
                            block_id="iro-2-table",
                            standard_ref="ESRS 2",
                            paragraph_ref="42",
                            title="Material ESRS Topics",
                            content_html="PLACEHOLDER_DYNAMIC_IRO2_TABLE",
                            content_type="table",
                            order=1,
                        ),
                    ],
                ),
            ],
        )

        # ── Sezione 2: Environmental (E1) ───────────────────────
        environmental_e1 = ReportSection(
            section_id="env-e1",
            standard_ref="ESRS E1",
            title="Climate Change",
            section_type=SectionType.ENVIRONMENTAL,
            materiality_filter=MaterialityFilter.IF_MATERIAL,
            order=2,
            is_material=False,  # Will be set based on materiality assessment
            disclosure_requirements=[
                DisclosureRequirement(
                    dr_id="E1-1",
                    title="Transition plan for climate change mitigation",
                    paragraph_ref="1-16",
                    is_mandatory=True,
                ),
                DisclosureRequirement(
                    dr_id="E1-2",
                    title="Policies related to climate change mitigation and adaptation",
                    paragraph_ref="17-23",
                    is_mandatory=True,
                ),
                DisclosureRequirement(
                    dr_id="E1-3",
                    title="Actions and resources in relation to climate change policies",
                    paragraph_ref="24-31",
                    is_mandatory=True,
                ),
                DisclosureRequirement(
                    dr_id="E1-4",
                    title="Targets related to climate change mitigation and adaptation",
                    paragraph_ref="32-45",
                    is_mandatory=True,
                ),
                DisclosureRequirement(
                    dr_id="E1-5",
                    title="Energy consumption and mix",
                    paragraph_ref="46-53",
                    is_mandatory=True,
                ),
                DisclosureRequirement(
                    dr_id="E1-6",
                    title="Gross Scopes 1, 2, 3 and Total GHG emissions",
                    paragraph_ref="54-61",
                    is_mandatory=True,
                    blocks=[
                        ContentBlock(
                            block_id="e1-6-ghg-table",
                            standard_ref="ESRS E1",
                            paragraph_ref="54",
                            title="GHG Emissions Summary",
                            content_html="""
<table>
    <thead>
        <tr>
            <th>GHG Emissions</th>
            <th>Year N-1</th>
            <th>Year N</th>
        </tr>
    </thead>
    <tbody>
        <tr><td>Scope 1 (tCO2e)</td><td>—</td><td>—</td></tr>
        <tr><td>Scope 2 location-based (tCO2e)</td><td>—</td><td>—</td></tr>
        <tr><td>Scope 2 market-based (tCO2e)</td><td>—</td><td>—</td></tr>
        <tr><td>Scope 3 total (tCO2e)</td><td>—</td><td>—</td></tr>
        <tr><td><strong>Total GHG emissions (tCO2e)</strong></td><td><strong>—</strong></td><td><strong>—</strong></td></tr>
    </tbody>
</table>""",
                            content_type="table",
                            datapoint_refs=[
                                "ESRS E1-6.54(a)",
                                "ESRS E1-6.54(b)",
                                "ESRS E1-6.55",
                            ],
                            order=1,
                        ),
                        ContentBlock(
                            block_id="e1-6-narrative",
                            standard_ref="ESRS E1",
                            paragraph_ref="56",
                            title="GHG Emissions Narrative",
                            content_html="PLACEHOLDER_E1_6_NARRATIVE",
                            content_type="narrative",
                            order=2,
                        ),
                    ],
                ),
                DisclosureRequirement(
                    dr_id="E1-7",
                    title="GHG removals and GHG mitigation projects financed through carbon credits",
                    paragraph_ref="62-68",
                    is_mandatory=False,
                ),
                DisclosureRequirement(
                    dr_id="E1-8",
                    title="Internal carbon pricing",
                    paragraph_ref="69-73",
                    is_mandatory=False,
                ),
                DisclosureRequirement(
                    dr_id="E1-9",
                    title="Anticipated financial effects from material physical and transition risks",
                    paragraph_ref="74-82",
                    is_mandatory=False,
                ),
            ],
        )

        # Sezioni E2-E5
        for std_code, title in [
            ("E2", "Pollution"),
            ("E3", "Water and Marine Resources"),
            ("E4", "Biodiversity and Ecosystems"),
            ("E5", "Resource Use and Circular Economy"),
        ]:
            # Build DRs with blocks for E2 only (others keep empty blocks)
            drs = []
            for dr_code_suffix, dr_title_suffix, pref in [
                ("1", f"Policies related to {title.lower()}", "1-8"),
                ("2", "Actions and resources", "9-15"),
                ("3", f"Targets related to {title.lower()}", "16-24"),
                ("4", f"Metrics related to {title.lower()}", "25-35"),
                ("5", "Anticipated financial effects", "36-42"),
            ]:
                dr_id = f"{std_code}-{dr_code_suffix}"
                blocks = []
                is_mandatory = dr_code_suffix != "5"

                if std_code == "E2":
                    if dr_id == "E2-1":
                        blocks.append(ContentBlock(
                            block_id="e2-1-policies",
                            standard_ref="ESRS E2",
                            paragraph_ref="1-8",
                            title="Pollution Management Policies",
                            content_html=f"""<div class="e2-1-content">
    <h4>E2-1 — Policies related to pollution</h4>
    <p><strong>{template.company_name}</strong> has established a comprehensive policy framework to prevent, control, and remediate pollution from its operations and throughout the value chain. These policies are aligned with applicable regulatory requirements, including Directive 2010/75/EU (Industrial Emissions Directive), REACH Regulation (EC) No 1907/2006, and national transpositions of EU environmental legislation.</p>

    <h5>Pollution Prevention and Control Policy</h5>
    <p>The undertaking's Pollution Prevention and Control Policy sets out the principles and operational requirements for managing emissions to air, water, and soil. The policy applies to all wholly-owned facilities and operational sites and is communicated to all employees through the environmental management system (certified to ISO 14001:2015). Key commitments include:</p>
    <ul>
        <li>Compliance with all applicable emission limit values (ELVs) and discharge permit conditions.</li>
        <li>Adoption of Best Available Techniques (BAT) for pollution prevention and control, as defined in the relevant BREF documents under the Industrial Emissions Directive.</li>
        <li>Continuous reduction of pollutant emissions through process optimisation, equipment upgrades, and cleaner production methods.</li>
        <li>Prevention of soil and groundwater contamination through secondary containment, leak detection, and spill response procedures.</li>
        <li>Safe handling, storage, and disposal of hazardous substances and waste in accordance with REACH and CLP Regulation (EC) No 1272/2008.</li>
    </ul>

    <h5>Substances of Concern Policy</h5>
    <p>In accordance with ESRS E2 paragraph 6, the undertaking maintains a Substances of Concern Policy that governs the use, substitution, and phase-out of substances of very high concern (SVHCs) as defined under REACH Article 57. The policy requires:</p>
    <ul>
        <li>Regular screening of all materials and chemical inputs against the Candidate List of SVHCs and the Authorisation List (Annex XIV).</li>
        <li>Proactive substitution of SVHCs with safer alternatives where technically and economically feasible, with a target substitution timeline of [TBC:substitution_timeline_years] years.</li>
        <li>Full disclosure of substances of concern in products to downstream customers and end-users in compliance with the SCIP database requirements under the Waste Framework Directive.</li>
        <li>Restriction on the use of substances restricted under REACH Annex XVII and POPs Regulation (EU) 2019/1021.</li>
    </ul>

    <h5>Water Quality Management Policy</h5>
    <p>The undertaking's Water Quality Management Policy addresses discharges to water bodies and groundwater protection. It requires all facilities to:</p>
    <ul>
        <li>Monitor effluent quality in accordance with discharge permits and applicable water quality standards.</li>
        <li>Implement wastewater treatment (primary, secondary, and tertiary as required) before discharge.</li>
        <li>Report any exceedances of permit conditions to the competent authority and take immediate corrective action.</li>
    </ul>

    <h5>Air Emissions Management Policy</h5>
    <p>Emissions to air are managed through the Air Emissions Management Policy, which sets emission limits for key pollutants including nitrogen oxides (NOx), sulphur oxides (SOx), particulate matter (PM), volatile organic compounds (VOCs), and heavy metals. The policy requires:</p>
    <ul>
        <li>Continuous or periodic monitoring of stack emissions as required by the facility's environmental permit.</li>
        <li>Optimisation of combustion processes and installation of abatement equipment (e.g., scrubbers, bag filters, catalytic converters) to achieve compliance with ELVs.</li>
        <li>Reduction of fugitive emissions through equipment maintenance, leak detection and repair (LDAR) programmes.</li>
    </ul>

    <h5>Policy governance and review</h5>
    <p>All pollution-related policies are approved by the Chief Operations Officer and reviewed at least annually, or more frequently following significant operational changes, regulatory updates, or pollution incidents. The Environmental Manager is responsible for policy implementation, monitoring, and reporting. Compliance with pollution policies is verified through internal audits and regulatory inspections.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ))
                    elif dr_id == "E2-2":
                        blocks.append(ContentBlock(
                            block_id="e2-2-actions",
                            standard_ref="ESRS E2",
                            paragraph_ref="9-15",
                            title="Actions and Resources on Pollution",
                            content_html=f"""<div class="e2-2-content">
    <h4>E2-2 — Actions and resources related to pollution</h4>
    <p><strong>{template.company_name}</strong> has allocated financial, human, and technical resources to implement its pollution prevention and control policies. The following actions have been undertaken during the reporting period to manage material pollution-related impacts, risks, and opportunities.</p>

    <h5>Key actions implemented or planned</h5>
    <table>
        <thead>
            <tr>
                <th>Action</th>
                <th>Scope</th>
                <th>Status</th>
                <th>Timeline</th>
                <th>Estimated investment</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Installation of upgraded bag filter systems at [TBC:pollution_facilities_count] facilities</td>
                <td>Air emissions (PM)</td>
                <td>[TBC:air_emissions_pm_reduction_pct]%</td>
                <td>[TBC:substitution_timeline_years] years</td>
                <td>[TBC:capex_pollution_eur]</td>
            </tr>
            <tr>
                <td>Implementation of solvent recovery system for VOC abatement</td>
                <td>Air emissions (VOCs)</td>
                <td>[TBC:air_emissions_voc_reduction_pct]%</td>
                <td>[TBC:substitution_timeline_years] years</td>
                <td>[TBC:opex_pollution_eur]</td>
            </tr>
            <tr>
                <td>Upgrade of industrial wastewater treatment plant at [TBC:site_name] site</td>
                <td>Water pollution</td>
                <td>[TBC:hazardous_waste_treated_pct]%</td>
                <td>[TBC:substitution_timeline_years] years</td>
                <td>[TBC:financial_resources_eur]</td>
            </tr>
            <tr>
                <td>Phase-out of [TBC:substance_name] substance of concern from product formulation</td>
                <td>Substances of concern</td>
                <td>[TBC:hazardous_waste_recovered_pct]%</td>
                <td>[TBC:target_year]</td>
                <td>[TBC:financial_resources_eur]</td>
            </tr>
            <tr>
                <td>Soil remediation programme at [TBC:site_name] former industrial site</td>
                <td>Soil contamination</td>
                <td>[TBC:soil_remediation_sites_count]%</td>
                <td>[TBC:target_year]</td>
                <td>[TBC:financial_resources_eur]</td>
            </tr>
        </tbody>
    </table>

    <h5>Resources allocated</h5>
    <p><strong>Financial resources:</strong> Total capital expenditure allocated to pollution prevention and control in the reporting period amounted to [TBC:capex_pollution_eur]. Operating expenditure for pollution management (including monitoring, waste treatment, and environmental compliance) was [TBC:opex_pollution_eur].</p>
    <p><strong>Human resources:</strong> The environmental management function comprises [TBC:environmental_fte_count] full-time equivalents (FTEs), including environmental engineers, compliance specialists, and laboratory technicians. All operational staff receive annual training on pollution prevention and spill response procedures.</p>
    <p><strong>Technical resources:</strong> Continuous emissions monitoring systems (CEMS) are installed at [TBC:cems_facilities_count] facilities. The undertaking maintains an ISO 14001:2015 certified environmental management system across all operational sites.</p>

    <h5>Outcome of actions</h5>
    <p>During the reporting period, the following outcomes were achieved:</p>
    <ul>
        <li>Reduction of PM emissions by [TBC:air_emissions_pm_reduction_pct]% through upgraded abatement equipment.</li>
        <li>Reduction of VOC emissions by [TBC:air_emissions_voc_reduction_pct]% through solvent recovery and process optimisation.</li>
        <li>Zero non-compliance events related to water discharge permits across all operational sites.</li>
        <li>[TBC:hazardous_waste_treated_pct]% of hazardous waste was sent to licensed treatment facilities; [TBC:hazardous_waste_recovered_pct]% was recovered or recycled.</li>
    </ul>
</div>""",
                            content_type="narrative",
                            order=1,
                        ))
                    elif dr_id == "E2-3":
                        blocks.append(ContentBlock(
                            block_id="e2-3-targets",
                            standard_ref="ESRS E2",
                            paragraph_ref="16-24",
                            title="Pollution Reduction Targets",
                            content_html=f"""<div class="e2-3-content">
    <h4>E2-3 — Targets related to pollution</h4>
    <p><strong>{template.company_name}</strong> has established quantitative and qualitative targets to manage its material pollution-related impacts, consistent with ESRS E2 paragraphs 16-24. Progress against these targets is monitored at least annually and reported to the Board. Targets are reviewed and updated as new scientific data, regulatory requirements, and best available techniques evolve.</p>

    <h5>Air emission reduction targets</h5>
    <table>
        <thead>
            <tr>
                <th>Pollutant</th>
                <th>Baseline year</th>
                <th>Baseline value</th>
                <th>2030 target</th>
                <th>2050 target</th>
                <th>Progress (% achieved)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Nitrogen oxides (NOx)</td>
                <td>[TBC:emissions_baseline_year]</td>
                <td>[TBC:air_emissions_pm_reduction_pct] kg/year</td>
                <td>&minus;[TBC:air_emissions_pm_reduction_pct]%</td>
                <td>&minus;[TBC:air_emissions_pm_reduction_pct]%</td>
                <td>[TBC:air_emissions_pm_reduction_pct]%</td>
            </tr>
            <tr>
                <td>Sulphur oxides (SOx)</td>
                <td>[TBC:emissions_baseline_year]</td>
                <td>[TBC:air_emissions_voc_reduction_pct] kg/year</td>
                <td>&minus;[TBC:air_emissions_voc_reduction_pct]%</td>
                <td>&minus;[TBC:air_emissions_voc_reduction_pct]%</td>
                <td>[TBC:air_emissions_voc_reduction_pct]%</td>
            </tr>
            <tr>
                <td>Particulate matter (PM10/PM2.5)</td>
                <td>[TBC:emissions_baseline_year]</td>
                <td>[TBC:air_emissions_pm_reduction_pct] kg/year</td>
                <td>&minus;[TBC:air_emissions_pm_reduction_pct]%</td>
                <td>&minus;[TBC:air_emissions_pm_reduction_pct]%</td>
                <td>[TBC:air_emissions_pm_reduction_pct]%</td>
            </tr>
            <tr>
                <td>Volatile organic compounds (VOCs)</td>
                <td>[TBC:emissions_baseline_year]</td>
                <td>[TBC:air_emissions_voc_reduction_pct] kg/year</td>
                <td>&minus;[TBC:air_emissions_voc_reduction_pct]%</td>
                <td>&minus;[TBC:air_emissions_voc_reduction_pct]%</td>
                <td>[TBC:air_emissions_voc_reduction_pct]%</td>
            </tr>
        </tbody>
    </table>

    <h5>Water pollution targets</h5>
    <ul>
        <li><strong>Effluent quality:</strong> 100% compliance with all discharge permit conditions throughout the reporting period. Target: zero non-compliance events.</li>
        <li><strong>Chemical Oxygen Demand (COD) load:</strong> Reduction of COD in wastewater discharges by [TBC:air_emissions_pm_reduction_pct]% by 2030 (baseline: [TBC:air_emissions_pm_reduction_pct] kg/year).</li>
        <li><strong>Heavy metal concentrations:</strong> Reduction of heavy metal content (lead, cadmium, mercury) in effluent by [TBC:air_emissions_pm_reduction_pct]% by 2030.</li>
    </ul>

    <h5>Substances of concern targets</h5>
    <ul>
        <li><strong>SVHC substitution:</strong> Phase-out of [TBC:svhc_substances_count] substances of very high concern from product formulations by [TBC:target_year].</li>
        <li><strong>SCIP notification:</strong> 100% compliance with SCIP database notification obligations for all articles containing substances of concern above threshold.</li>
        <li><strong>Reduction target:</strong> Reduction in the total weight of substances of concern used in production by [TBC:air_emissions_pm_reduction_pct]% by [TBC:target_year].</li>
    </ul>

    <h5>Soil contamination targets</h5>
    <ul>
        <li><strong>Remediation:</strong> Completion of soil remediation at [TBC:soil_remediation_sites_count] identified contaminated sites by [TBC:target_year].</li>
        <li><strong>Prevention:</strong> Zero new soil contamination incidents through enhanced secondary containment and leak detection at all fuel and chemical storage facilities.</li>
    </ul>

    <h5>Target governance</h5>
    <p>These targets are approved by the Board of Directors and reviewed annually. Progress is reported in the annual sustainability statement. The undertaking engaged [TBC:external_stakeholders_engaged] external stakeholders in the target-setting process to ensure alignment with societal expectations and regulatory requirements.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ))
                    elif dr_id == "E2-4":
                        blocks.append(ContentBlock(
                            block_id="e2-4-metrics",
                            standard_ref="ESRS E2",
                            paragraph_ref="25-35",
                            title="Pollution Metrics and Data",
                            content_html=f"""<div class="e2-4-content">
    <h4>E2-4 — Metrics related to pollution</h4>
    <p><strong>{template.company_name}</strong> discloses the following metrics on pollutants released to air, water, and soil in accordance with ESRS E2 paragraphs 25-35. Data is reported for all operational sites under operational control. Measurement methods include continuous monitoring (for major point sources), periodic sampling, and emission factor estimation (for diffuse/fugitive sources).</p>

    <h5>Emissions to air</h5>
    <table>
        <thead>
            <tr>
                <th>Pollutant</th>
                <th>Year N-1</th>
                <th>Year N</th>
                <th>Unit</th>
                <th>Measurement method</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Nitrogen oxides (NOx)</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED]</td>
                <td>kg/year</td>
                <td>Continuous monitoring / emission factor</td>
            </tr>
            <tr>
                <td>Sulphur oxides (SOx)</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED]</td>
                <td>kg/year</td>
                <td>Continuous monitoring / emission factor</td>
            </tr>
            <tr>
                <td>Particulate matter (PM10)</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED]</td>
                <td>kg/year</td>
                <td>Periodic sampling + emission factor</td>
            </tr>
            <tr>
                <td>Particulate matter (PM2.5)</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED]</td>
                <td>kg/year</td>
                <td>Periodic sampling + emission factor</td>
            </tr>
            <tr>
                <td>Volatile organic compounds (VOCs)</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED]</td>
                <td>kg/year</td>
                <td>Mass balance / LDAR programme</td>
            </tr>
            <tr>
                <td>Heavy metals (total)</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED]</td>
                <td>kg/year</td>
                <td>Periodic stack sampling</td>
            </tr>
        </tbody>
    </table>

    <h5>Emissions to water</h5>
    <table>
        <thead>
            <tr>
                <th>Parameter</th>
                <th>Year N-1</th>
                <th>Year N</th>
                <th>Unit</th>
                <th>Measurement method</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Chemical Oxygen Demand (COD)</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED]</td>
                <td>kg/year</td>
                <td>Periodic effluent sampling</td>
            </tr>
            <tr>
                <td>Total nitrogen</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED]</td>
                <td>kg/year</td>
                <td>Periodic effluent sampling</td>
            </tr>
            <tr>
                <td>Total phosphorus</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED]</td>
                <td>kg/year</td>
                <td>Periodic effluent sampling</td>
            </tr>
            <tr>
                <td>Heavy metals (total)</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED]</td>
                <td>kg/year</td>
                <td>Periodic effluent sampling</td>
            </tr>
            <tr>
                <td>Suspended solids (TSS)</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED]</td>
                <td>kg/year</td>
                <td>Periodic effluent sampling</td>
            </tr>
        </tbody>
    </table>

    <h5>Substances of concern</h5>
    <table>
        <thead>
            <tr>
                <th>Indicator</th>
                <th>Year N-1</th>
                <th>Year N</th>
                <th>Unit</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Total weight of substances of concern used</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED]</td>
                <td>tonnes/year</td>
                <td>Continuous monitoring / emission factor</td>
            </tr>
            <tr>
                <td>Total weight of SVHCs used</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED]</td>
                <td>tonnes/year</td>
                <td>Continuous monitoring / emission factor</td>
            </tr>
            <tr>
                <td>Number of SVHCs in product portfolio</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED]</td>
                <td>count</td>
                <td>Continuous monitoring / emission factor</td>
            </tr>
            <tr>
                <td>SCIP notifications submitted</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED]</td>
                <td>count</td>
                <td>Continuous monitoring / emission factor</td>
            </tr>
        </tbody>
    </table>

    <h5>Microplastics</h5>
    <p>In accordance with ESRS E2 paragraph 31, the undertaking has assessed the potential generation of microplastics from its operations. [TO BE CONFIRMED] — Description of whether and how microplastics are generated, relevant mitigation measures applied, and any related monitoring data.</p>

    <h5>Measurement and estimation methodology</h5>
    <p>Pollutant emissions data is compiled using the following hierarchy of methods:</p>
    <ol>
        <li><strong>Continuous monitoring:</strong> For major point sources equipped with CEMS, data is recorded and reported directly.</li>
        <li><strong>Periodic sampling:</strong> For sources not equipped with CEMS, periodic stack or effluent sampling is conducted by accredited laboratories.</li>
        <li><strong>Emission factor estimation:</strong> For diffuse, fugitive, or minor sources, emission factors from recognised sources (e.g., EEA/EMEP Guidebook, IPPC BREF) are used.</li>
        <li><strong>Mass balance:</strong> For VOCs and certain substances, mass balance calculations based on material inputs and product outputs are applied.</li>
    </ol>
    <p>Data quality is assessed using a 3-tier system (high/medium/low). Where estimation uncertainty is significant, this is disclosed in the relevant notes.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ))

                drs.append(DisclosureRequirement(
                    dr_id=dr_id,
                    title=f"{dr_title_suffix}",
                    paragraph_ref=pref,
                    is_mandatory=is_mandatory,
                    blocks=blocks,
                ))

            setattr(
                template, f"env_{std_code.lower()}",
                ReportSection(
                    section_id=f"env-{std_code.lower()}",
                    standard_ref=f"ESRS {std_code}",
                    title=title,
                    section_type=SectionType.ENVIRONMENTAL,
                    materiality_filter=MaterialityFilter.IF_MATERIAL,
                    order={
                        "E2": 3, "E3": 4, "E4": 5, "E5": 6,
                    }[std_code],
                    is_material=False,
                    disclosure_requirements=drs,
                ),
            )
            template.add_section(getattr(template, f"env_{std_code.lower()}"))


        # ── Sezione 3: Social (S1-S4) ───────────────────────────
        for std_code, title in [
            ("S1", "Own Workforce"),
            ("S2", "Workers in the Value Chain"),
            ("S3", "Affected Communities"),
            ("S4", "Consumers and End-users"),
        ]:
            # Build DRs with blocks for S1 and S2 only (S3, S4 keep empty blocks)
            drs = []
            for dr_suffix, dr_title_prefix, dr_pref in [
                ("1", f"Policies related to {title.lower()}", "1-10"),
                ("2", "Processes for engaging with stakeholders", "11-18"),
                ("3", "Processes to remediate negative impacts", "19-25"),
                ("4", "Taking action on material impacts and managing risks", "26-35"),
                ("5", "Targets related to managing material impacts", "36-44"),
            ]:
                dr_id = f"{std_code}-{dr_suffix}"
                blocks = []
                is_mandatory = True

                if std_code == "S1":
                    if dr_id == "S1-1":
                        blocks.append(ContentBlock(
                            block_id="s1-1-policies",
                            standard_ref="ESRS S1",
                            paragraph_ref="1-10",
                            title="Own Workforce Policies",
                            content_html=f"""<div class="s1-1-content">
    <h4>S1-1 — Policies related to own workforce</h4>
    <p><strong>{template.company_name}</strong> has established comprehensive policies governing the management of its own workforce, in accordance with ESRS S1 paragraphs 1-10 and applicable labour laws, including EU directives on working conditions, health and safety, equal treatment, and information/consultation of workers.</p>

    <h5>Employment and working conditions policy</h5>
    <p>The undertaking's Employment and Working Conditions Policy ensures that all workers receive fair, transparent, and lawful terms of employment. Key commitments include:</p>
    <ul>
        <li>Providing written employment contracts in accordance with Directive (EU) 2019/1152 on transparent and predictable working conditions.</li>
        <li>Ensuring fair remuneration that meets or exceeds applicable minimum wage standards and collective bargaining agreements.</li>
        <li>Respecting working time regulations, including limits on maximum working hours, rest periods, and annual leave entitlements.</li>
        <li>Offering adequate social protection coverage, including sickness, maternity/paternity, and pension benefits.</li>
        <li>Providing access to training and career development opportunities for all employees.</li>
    </ul>

    <h5>Health and safety policy</h5>
    <p><strong>{template.company_name}</strong> is committed to providing a safe and healthy working environment for all employees in accordance with Directive 89/391/EEC (Framework Directive on Safety and Health at Work) and national transpositions. The Health and Safety Policy includes:</p>
    <ul>
        <li>Risk assessments conducted at all workplaces, updated annually or after significant changes.</li>
        <li>Provision of personal protective equipment (PPE) and safety training to all employees exposed to occupational hazards.</li>
        <li>Reporting and investigation of all workplace accidents, near misses, and occupational diseases.</li>
        <li>Employee participation in health and safety matters through designated safety representatives and joint health and safety committees.</li>
        <li>Mental health and well-being programmes, including access to counselling services and flexible working arrangements.</li>
    </ul>
    <p>During the reporting period, the workplace accident rate (lost-time injury frequency rate) was [TBC:ltifr] per 1,000 employees. No fatal accidents occurred.</p>

    <h5>Equal treatment and non-discrimination policy</h5>
    <p>The undertaking maintains a zero-tolerance policy towards discrimination, harassment, and violence in the workplace. The Equal Treatment and Non-Discrimination Policy covers all protected characteristics under Directive 2006/54/EC (Equal Treatment Directive) and national legislation, including age, disability, gender reassignment, marriage and civil partnership, pregnancy and maternity, race, religion or belief, sex, and sexual orientation. The policy:</p>
    <ul>
        <li>Prohibits direct and indirect discrimination in recruitment, promotion, remuneration, training, and termination of employment.</li>
        <li>Establishes procedures for reporting and investigating complaints of discrimination and harassment.</li>
        <li>Provides for reasonable accommodations for workers with disabilities.</li>
        <li>Promotes gender equality, including equal pay for equal work and measures to address the gender pay gap.</li>
    </ul>

    <h5>Diversity and inclusion policy</h5>
    <p><strong>{template.company_name}</strong> values diversity and strives to create an inclusive workplace where all employees can thrive. The Diversity and Inclusion Policy includes measurable objectives for:</p>
    <ul>
        <li>Gender balance at all levels of the organisation, including management and leadership positions.</li>
        <li>Representation of underrepresented groups in the workforce.</li>
        <li>Diversity awareness training for all employees and managers.</li>
        <li>Workforce composition monitoring and reporting to the Board annually.</li>
    </ul>

    <h5>Training and skills development policy</h5>
    <p>The undertaking supports the continuous professional development of its workforce through the Training and Skills Development Policy, which provides:</p>
    <ul>
        <li>Minimum annual training hours per employee (target: [TBC:avg_training_hours_per_employee] hours/year).</li>
        <li>Regular performance and career development reviews.</li>
        <li>Access to upskilling and reskilling programmes, particularly in relation to the green and digital transitions.</li>
        <li>Support for vocational qualifications and professional certifications.</li>
    </ul>

    <h5>Human rights policy commitments</h5>
    <p>In accordance with ESRS S1 paragraph 10, the undertaking has policy commitments to respect human rights of its own workforce, including:</p>
    <ul>
        <li>Zero tolerance for child labour, forced labour, and modern slavery in any form.</li>
        <li>Freedom of association and the right to collective bargaining, as recognised by ILO Conventions 87 and 98.</li>
        <li>Protection of workers' privacy and data protection in accordance with GDPR and applicable national laws.</li>
        <li>Grievance mechanisms for workers to raise human rights concerns without fear of retaliation.</li>
    </ul>

    <h5>Policy governance</h5>
    <p>All workforce-related policies are approved by the Board of Directors and reviewed at least annually. The Human Resources Director is responsible for policy implementation and monitoring. Policies are communicated to all employees through the employee handbook, intranet, and mandatory onboarding training. Social partners (trade unions and works councils) are consulted on policy changes affecting workers' rights and working conditions.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ))
                    elif dr_id == "S1-2":
                        blocks.append(ContentBlock(
                            block_id="s1-2-engagement",
                            standard_ref="ESRS S1",
                            paragraph_ref="11-18",
                            title="Stakeholder Engagement — Own Workforce",
                            content_html=f"""<div class="s1-2-content">
    <h4>S1-2 — Processes for engaging with own workforce and workers' representatives about impacts</h4>
    <p><strong>{template.company_name}</strong> recognises that regular, transparent, and meaningful engagement with its workforce and their representatives is essential to identify, understand, and address material impacts on employees. The undertaking has established multiple engagement channels and processes in accordance with ESRS S1 paragraphs 11-18.</p>

    <h5>Direct employee engagement channels</h5>
    <table>
        <thead>
            <tr>
                <th>Engagement channel</th>
                <th>Frequency</th>
                <th>Scope</th>
                <th>Participation rate</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Annual employee engagement survey</td>
                <td>Annual</td>
                <td>All employees</td>
                <td>[TBC:employee_engagement_score]%</td>
            </tr>
            <tr>
                <td>Quarterly town hall meetings</td>
                <td>Quarterly</td>
                <td>All employees (in-person and virtual)</td>
                <td>[TBC:employee_engagement_score]% average attendance</td>
            </tr>
            <tr>
                <td>Pulse surveys on specific topics</td>
                <td>As needed (minimum 2/year)</td>
                <td>Selected employee groups</td>
                <td>[TBC:employee_engagement_score]%</td>
            </tr>
            <tr>
                <td>Exit interviews</td>
                <td>On voluntary termination</td>
                <td>All departing employees</td>
                <td>[TBC:employee_engagement_score]% completion</td>
            </tr>
            <tr>
                <td>Departmental meetings with direct supervisors</td>
                <td>Monthly</td>
                <td>All departments</td>
                <td>Ongoing</td>
            </tr>
            <tr>
                <td>Open-door policy with senior management</td>
                <td>Ongoing</td>
                <td>All employees</td>
                <td>Ongoing</td>
            </tr>
        </tbody>
    </table>

    <h5>Workers' representation and collective bargaining</h5>
    <p>The undertaking respects the right of all employees to join trade unions and to be represented by worker representatives in accordance with national laws and EU directives. As of the reporting date:</p>
    <ul>
        <li><strong>Union representation:</strong> [TBC:union_coverage_pct]% of the workforce is covered by collective bargaining agreements.</li>
        <li><strong>Works councils / employee representatives:</strong> [TBC:employee_count_total] bodies are active at [TBC:operational_sites_count] locations.</li>
        <li><strong>European Works Council (EWC):</strong> [TO BE CONFIRMED — describe if applicable].</li>
        <li><strong>Health and safety committees:</strong> Joint health and safety committees operate at all sites with more than [TBC:employee_count_total] employees.</li>
    </ul>

    <h5>Purpose and outcomes of engagement</h5>
    <p>The primary purposes of workforce engagement are to:</p>
    <ul>
        <li>Identify actual and potential negative impacts on workers (e.g., excessive workload, health and safety concerns, discrimination).</li>
        <li>Assess the effectiveness of existing policies and mitigation measures.</li>
        <li>Gather input for the development of new policies, targets, and action plans.</li>
        <li>Monitor progress toward workforce-related targets.</li>
        <li>Understand employee satisfaction, engagement, and well-being.</li>
    </ul>
    <p>Key outcomes from the most recent engagement cycle include: [TO BE CONFIRMED — summarise main findings, e.g., "improved work-life balance initiatives introduced, enhanced mental health support, revised performance management framework"].</p>

    <h5>Engagement with vulnerable groups</h5>
    <p>The undertaking takes specific measures to engage with potentially vulnerable worker groups, including:</p>
    <ul>
        <li><strong>Young workers:</strong> Dedicated onboarding and mentorship programmes.</li>
        <li><strong>Workers with disabilities:</strong> Individual accommodation assessments and regular check-ins.</li>
        <li><strong>Migrant workers:</strong> Language support and cultural integration programmes.</li>
        <li><strong>Women:</strong> Women's leadership network and gender equality working group.</li>
    </ul>

    <h5>Feedback integration and decision-making</h5>
    <p>Feedback from workforce engagement is systematically collected, analysed, and reported to the Human Resources Director and the Board. Key themes and action items are tracked through a dedicated action tracker, with progress reviewed quarterly. Employee representatives are consulted on decisions that may significantly affect the workforce, including organisational restructuring, changes to working conditions, and policy updates.</p>

    <h5>Effectiveness assessment</h5>
    <p>The effectiveness of workforce engagement processes is evaluated through:</p>
    <ul>
        <li>Survey participation rates and trend analysis.</li>
        <li>Employee satisfaction scores (e.g., eNPS: [TBC:employee_engagement_score]).</li>
        <li>Grievance resolution rates and timeliness.</li>
        <li>Feedback from worker representatives on the quality of dialogue.</li>
        <li>Third-party assessments or audits where applicable.</li>
    </ul>
</div>""",
                            content_type="narrative",
                            order=1,
                        ))
                    elif dr_id == "S1-3":
                        blocks.append(ContentBlock(
                            block_id="s1-3-remediation",
                            standard_ref="ESRS S1",
                            paragraph_ref="19-25",
                            title="Remediation Processes — Own Workforce",
                            content_html=f"""<div class="s1-3-content">
    <h4>S1-3 — Processes to remediate negative impacts and channels for own workforce to raise concerns</h4>
    <p><strong>{template.company_name}</strong> has established processes to remediate negative impacts on its workforce and provides accessible channels through which workers can raise concerns, report grievances, or seek remedy, in accordance with ESRS S1 paragraphs 19-25.</p>

    <h5>Grievance mechanisms</h5>
    <p>The undertaking provides the following channels for workers to raise concerns or report grievances:</p>
    <table>
        <thead>
            <tr>
                <th>Channel</th>
                <th>Description</th>
                <th>Accessibility</th>
                <th>Confidentiality</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>HR department / People team</td>
                <td>Direct reporting to HR manager or dedicated People partner</td>
                <td>All employees during working hours</td>
                <td>Confidential (within HR)</td>
            </tr>
            <tr>
                <td>Line manager / supervisor</td>
                <td>Workers can report concerns to their direct manager</td>
                <td>All employees</td>
                <td>Confidential (escalated to HR)</td>
            </tr>
            <tr>
                <td>Whistleblowing hotline (independent third party)</td>
                <td>Confidential, anonymous reporting channel for serious concerns (harassment, fraud, human rights violations)</td>
                <td>24/7, online and phone</td>
                <td>Fully anonymous option available</td>
            </tr>
            <tr>
                <td>Trade union / worker representative</td>
                <td>Reporting through elected worker representatives or trade union officials</td>
                <td>All unionised employees</td>
                <td>Confidential</td>
            </tr>
            <tr>
                <td>Ethics Committee</td>
                <td>For Code of Conduct violations and ethical concerns</td>
                <td>All employees</td>
                <td>Confidential</td>
            </tr>
            <tr>
                <td>Employee survey (open-text)</td>
                <td>Anonymous feedback through engagement surveys</td>
                <td>All employees during survey periods</td>
                <td>Anonymous</td>
            </tr>
        </tbody>
    </table>

    <h5>Remediation process</h5>
    <p>When a negative impact is identified or a grievance is raised, the undertaking follows a structured remediation process:</p>
    <ol>
        <li><strong>Receipt and acknowledgement:</strong> The concern is logged and acknowledged within [TBC:grievance_resolution_days] working days.</li>
        <li><strong>Initial assessment:</strong> The nature, severity, and scope of the impact are assessed. For serious concerns (e.g., discrimination, harassment, safety violations), an investigation is initiated within [TBC:grievance_resolution_days] working days.</li>
        <li><strong>Investigation:</strong> An impartial investigation is conducted by the HR department or an external investigator. Affected workers are interviewed, and relevant evidence is reviewed.</li>
        <li><strong>Determination:</strong> Findings are documented and a determination is made on whether remediation is required.</li>
        <li><strong>Remediation action:</strong> Appropriate remedial measures are implemented, which may include: corrective action, disciplinary measures against perpetrators, policy changes, training, compensation for harmed workers, and changes to processes or controls.</li>
        <li><strong>Follow-up and monitoring:</strong> The effectiveness of remediation is monitored, and the affected worker(s) are informed of the outcome and any actions taken.</li>
        <li><strong>Appeal:</strong> Workers have the right to appeal the determination through a higher-level review process.</li>
    </ol>

    <h5>Protection against retaliation</h5>
    <p>The undertaking strictly prohibits any form of retaliation, reprisal, or victimisation against workers who raise concerns in good faith or participate in investigations. Confidentiality is maintained throughout the process, and anonymous reporting is supported. Any employee found to have retaliated against a complainant is subject to disciplinary action, up to and including termination of employment.</p>

    <h5>Remediation of actual negative impacts</h5>
    <p>During the reporting period, the following negative impacts were identified and remediated:</p>
    <ul>
        <li><strong>Nature of impact:</strong> [TO BE CONFIRMED — e.g., "unpaid overtime in warehouse operations"].</li>
        <li><strong>Remediation provided:</strong> [TO BE CONFIRMED — e.g., "back payment of overtime compensation, revised scheduling system, additional training for supervisors"].</li>
        <li><strong>Status:</strong> [TO BE CONFIRMED — e.g., "Resolved / In progress"].</li>
    </ul>
    <p>The undertaking also provides for or cooperates in the remediation of negative impacts that it has caused or contributed to, in accordance with the OECD Due Diligence Guidance for Responsible Business Conduct and the UN Guiding Principles on Business and Human Rights.</p>

    <h5>Effectiveness of grievance mechanisms</h5>
    <p>During the reporting period:</p>
    <ul>
        <li><strong>Number of grievances received:</strong> [TBC:grievances_received]</li>
        <li><strong>Number of grievances resolved:</strong> [TBC:grievances_resolved]</li>
        <li><strong>Average resolution time:</strong> [TBC:grievance_resolution_days] working days</li>
        <li><strong>Most common grievance types:</strong> [TO BE CONFIRMED]</li>
        <li><strong>Worker satisfaction with the grievance process:</strong> [TBC:grievance_satisfaction_pct]% (from post-resolution surveys)</li>
    </ul>

    <h5>General availability of channels</h5>
    <p>Workers are informed of available grievance channels during onboarding, through the employee handbook, via posters in common areas, and on the company intranet. Regular reminders are sent to all employees. Channels are available in [TBC:grievance_languages_count] languages to accommodate the linguistic diversity of the workforce.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ))
                    elif dr_id == "S1-4":
                        blocks.append(ContentBlock(
                            block_id="s1-4-actions",
                            standard_ref="ESRS S1",
                            paragraph_ref="26-35",
                            title="Actions on Material Workforce Impacts",
                            content_html=f"""<div class="s1-4-content">
    <h4>S1-4 — Taking action on material impacts on own workforce and managing risks and opportunities</h4>
    <p><strong>{template.company_name}</strong> has implemented a range of actions to address material impacts on its workforce, reduce risks, and capitalise on opportunities related to human capital management, in accordance with ESRS S1 paragraphs 26-35.</p>

    <h5>Material impacts identified</h5>
    <p>Through the double materiality assessment process (see IRO-1), the following material impacts on own workforce were identified:</p>
    <ul>
        <li><strong>Negative actual/potential impacts:</strong> [TO BE CONFIRMED — e.g., "work-related stress and burnout in high-pressure roles, inadequate ergonomic conditions in production areas, risk of discrimination in promotion processes"].</li>
        <li><strong>Positive actual/potential impacts:</strong> [TO BE CONFIRMED — e.g., "skills development and career progression opportunities, competitive remuneration and benefits package, inclusive workplace culture"].</li>
    </ul>

    <h5>Action plan for managing workforce impacts</h5>
    <table>
        <thead>
            <tr>
                <th>Action</th>
                <th>Impact addressed</th>
                <th>Status</th>
                <th>Timeline</th>
                <th>Responsible</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Implementation of mental health and well-being programme</td>
                <td>Work-related stress and burnout</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED] years</td>
                <td>HR Director</td>
            </tr>
            <tr>
                <td>Ergonomic assessment and workstation redesign at production sites</td>
                <td>Physical strain and musculoskeletal disorders</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED] years</td>
                <td>Health & Safety Manager</td>
            </tr>
            <tr>
                <td>Blind recruitment pilot and bias training for hiring managers</td>
                <td>Discrimination risk in hiring and promotion</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED] years</td>
                <td>Diversity & Inclusion Lead</td>
            </tr>
            <tr>
                <td>Expansion of flexible working arrangements</td>
                <td>Work-life balance / well-being</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED] years</td>
                <td>HR Director</td>
            </tr>
            <tr>
                <td>Leadership development programme for women and underrepresented groups</td>
                <td>Gender diversity in management</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TO BE CONFIRMED] years</td>
                <td>Diversity & Inclusion Lead</td>
            </tr>
        </tbody>
    </table>

    <h5>Approach to managing material risks</h5>
    <p>The undertaking manages workforce-related risks through an integrated risk management framework. Key workforce risks identified include:</p>
    <ul>
        <li><strong>Talent attraction and retention:</strong> Addressed through competitive compensation, career development programmes, and employee engagement initiatives.</li>
        <li><strong>Skills gaps:</strong> Addressed through training needs analysis, upskilling programmes, and partnerships with educational institutions.</li>
        <li><strong>Workforce health and safety:</strong> Addressed through the health and safety management system, risk assessments, and incident prevention programmes.</li>
        <li><strong>Labour relations:</strong> Addressed through regular dialogue with worker representatives, collective bargaining, and dispute resolution mechanisms.</li>
        <li><strong>Regulatory compliance:</strong> Addressed through policy reviews, compliance audits, and legal monitoring.</li>
    </ul>

    <h5>Resources allocated</h5>
    <p>Total expenditure on workforce-related actions and programmes during the reporting period: [TBC:annual_revenue_eur], including:</p>
    <ul>
        <li>Training and development: [TBC:annual_revenue_eur]</li>
        <li>Health and safety programmes: [TBC:annual_revenue_eur]</li>
        <li>Well-being and mental health support: [TBC:annual_revenue_eur]</li>
        <li>Diversity and inclusion initiatives: [TBC:annual_revenue_eur]</li>
    </ul>

    <h5>Effectiveness tracking</h5>
    <p>The effectiveness of actions is monitored through key performance indicators (KPIs) including employee engagement scores, turnover rates, accident frequency rates, training completion rates, and grievance resolution rates. Progress is reported to the Board quarterly.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ))
                    elif dr_id == "S1-5":
                        blocks.append(ContentBlock(
                            block_id="s1-5-targets",
                            standard_ref="ESRS S1",
                            paragraph_ref="36-44",
                            title="Workforce-Related Targets",
                            content_html=f"""<div class="s1-5-content">
    <h4>S1-5 — Targets related to managing material negative impacts, advancing positive impacts, and managing material risks and opportunities</h4>
    <p><strong>{template.company_name}</strong> has established measurable, time-bound targets to manage material negative impacts, advance positive impacts, and manage risks and opportunities related to its own workforce, in accordance with ESRS S1 paragraphs 36-44.</p>

    <h5>Targets overview</h5>
    <table>
        <thead>
            <tr>
                <th>Target area</th>
                <th>Target</th>
                <th>Baseline (year)</th>
                <th>2026 target</th>
                <th>2030 target</th>
                <th>Current progress</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Employee engagement</td>
                <td>Employee Net Promoter Score (eNPS)</td>
                <td>[TBC:employee_engagement_score] ([TBC:emissions_baseline_year])</td>
                <td>[TBC:employee_engagement_score]</td>
                <td>[TBC:employee_engagement_score]</td>
                <td>[TBC:employee_engagement_score]</td>
            </tr>
            <tr>
                <td>Gender diversity in management</td>
                <td>Percentage of women in management positions</td>
                <td>[TBC:women_in_management_pct]% ([TBC:emissions_baseline_year])</td>
                <td>[TBC:women_in_management_pct]%</td>
                <td>[TBC:women_in_management_pct]%</td>
                <td>[TBC:women_in_management_pct]%</td>
            </tr>
            <tr>
                <td>Gender pay gap</td>
                <td>Reduction of unadjusted gender pay gap</td>
                <td>[TBC:gender_pay_gap_pct]% ([TBC:emissions_baseline_year])</td>
                <td>&minus;[TBC:gender_pay_gap_pct]%</td>
                <td>&minus;[TBC:gender_pay_gap_pct]%</td>
                <td>[TBC:gender_pay_gap_pct]% achieved</td>
            </tr>
            <tr>
                <td>Health and safety</td>
                <td>Lost-time injury frequency rate (LTIFR)</td>
                <td>[TBC:ltifr] ([TBC:emissions_baseline_year])</td>
                <td>[TBC:ltifr]</td>
                <td>Zero harm</td>
                <td>[TBC:ltifr]</td>
            </tr>
            <tr>
                <td>Training</td>
                <td>Average training hours per employee per year</td>
                <td>[TBC:avg_training_hours_per_employee] hrs ([TBC:emissions_baseline_year])</td>
                <td>[TBC:avg_training_hours_per_employee] hrs</td>
                <td>[TBC:avg_training_hours_per_employee] hrs</td>
                <td>[TBC:avg_training_hours_per_employee] hrs</td>
            </tr>
            <tr>
                <td>Voluntary turnover</td>
                <td>Voluntary employee turnover rate</td>
                <td>[TBC:voluntary_turnover_pct]% ([TBC:emissions_baseline_year])</td>
                <td>[TBC:voluntary_turnover_pct]%</td>
                <td>[TBC:voluntary_turnover_pct]%</td>
                <td>[TBC:voluntary_turnover_pct]%</td>
            </tr>
        </tbody>
    </table>

    <h5>Target-setting approach</h5>
    <p>Targets have been informed by:</p>
    <ul>
        <li>Baseline data from current workforce metrics (see S1-6).</li>
        <li>Benchmarking against sector peers and industry best practices.</li>
        <li>Stakeholder expectations, including feedback from employee engagement surveys and worker representatives.</li>
        <li>Regulatory requirements and policy commitments (e.g., gender equality directives, national labour laws).</li>
        <li>Internal strategic priorities and the undertaking's sustainability strategy.</li>
    </ul>

    <h5>Target governance</h5>
    <p>Targets are approved by the Board of Directors and reviewed annually. Progress is reported in the annual sustainability statement and to the Board on a quarterly basis. Targets may be revised if baseline data, regulatory requirements, or business circumstances change materially. The undertaking engaged with worker representatives and other relevant stakeholders in the target-setting process.</p>

    <h5>Stakeholder involvement</h5>
    <p>Trade unions and worker representatives were consulted in the development of workforce-related targets, particularly those related to working conditions, health and safety, and training. Employee survey data directly informed the engagement and well-being targets.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ))
                    elif dr_id == "S1-6":
                        blocks.append(ContentBlock(
                            block_id="s1-6-metrics",
                            standard_ref="ESRS S1",
                            paragraph_ref="45-55",
                            title="Workforce Metrics and Headcount Data",
                            content_html=f"""<div class="s1-6-content">
    <h4>S1-6 — Characteristics of the undertaking's employees</h4>
    <p><strong>{template.company_name}</strong> discloses the following workforce characteristics in accordance with ESRS S1 paragraphs 45-55. Data is reported as of 31 December {template.reporting_year}, unless otherwise stated.</p>

    <h5>Total headcount and workforce composition</h5>
    <table>
        <thead>
            <tr>
                <th>Category</th>
                <th>Female</th>
                <th>Male</th>
                <th>Not disclosed / Other</th>
                <th>Total</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Total employees</td>
                <td>[TBC:employee_count_female]</td>
                <td>[TBC:employee_count_male]</td>
                <td>[TBC:employee_count_other]</td>
                <td><strong>{template.employee_count or '[TBC:employee_count_total]'}</strong></td>
            </tr>
            <tr>
                <td>Permanent employees</td>
                <td>[TBC:employee_count_female]</td>
                <td>[TBC:employee_count_male]</td>
                <td>[TBC:employee_count_other]</td>
                <td>[TBC:employee_count_permanent]</td>
            </tr>
            <tr>
                <td>Fixed-term employees</td>
                <td>[TBC:employee_count_female]</td>
                <td>[TBC:employee_count_male]</td>
                <td>[TBC:employee_count_other]</td>
                <td>[TBC:employee_count_temporary]</td>
            </tr>
            <tr>
                <td>Full-time employees</td>
                <td>[TBC:employee_count_female]</td>
                <td>[TBC:employee_count_male]</td>
                <td>[TBC:employee_count_other]</td>
                <td>[TBC:employee_count_total]</td>
            </tr>
            <tr>
                <td>Part-time employees</td>
                <td>[TBC:employee_count_female]</td>
                <td>[TBC:employee_count_male]</td>
                <td>[TBC:employee_count_other]</td>
                <td>[TBC:employee_count_total]</td>
            </tr>
        </tbody>
    </table>

    <h5>Employees by region</h5>
    <table>
        <thead>
            <tr>
                <th>Region</th>
                <th>Employees</th>
                <th>% of total</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>[TBC:country] — primary</td>
                <td>[TBC:employee_count_total]</td>
                <td>[TBC:employee_engagement_score]%</td>
            </tr>
            <tr>
                <td>[TBC:country] — other</td>
                <td>[TBC:employee_count_total]</td>
                <td>[TBC:employee_engagement_score]%</td>
            </tr>
            <tr>
                <td>[TBC:country] — international</td>
                <td>[TBC:employee_count_total]</td>
                <td>[TBC:employee_engagement_score]%</td>
            </tr>
            <tr>
                <td><strong>Total</strong></td>
                <td><strong>{template.employee_count or '[TBC:employee_count_total]'}</strong></td>
                <td><strong>100%</strong></td>
            </tr>
        </tbody>
    </table>

    <h5>Employee turnover</h5>
    <p><strong>Voluntary turnover rate:</strong> [TBC:voluntary_turnover_pct]% (Year N-1: [TBC:voluntary_turnover_pct]%)</p>
    <p><strong>Total turnover rate:</strong> [TBC:total_turnover_pct]% (Year N-1: [TBC:total_turnover_pct]%)</p>
    <p><strong>New hires during the period:</strong> [TBC:new_hires_count]</p>

    <h5>Additional workforce metrics (S1-6 complementary disclosures)</h5>
    <table>
        <thead>
            <tr>
                <th>Metric</th>
                <th>Year N-1</th>
                <th>Year N</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Average tenure (years)</td>
                <td>[TBC:avg_tenure_years]</td>
                <td>[TBC:avg_tenure_years]</td>
            </tr>
            <tr>
                <td>Average age (years)</td>
                <td>[TBC:avg_age_years]</td>
                <td>[TBC:avg_age_years]</td>
            </tr>
            <tr>
                <td>Employees covered by collective bargaining agreements (%)</td>
                <td>[TBC:union_coverage_pct]%</td>
                <td>[TBC:union_coverage_pct]%</td>
            </tr>
            <tr>
                <td>Employees with disabilities (%)</td>
                <td>[TBC:employees_with_disabilities_pct]%</td>
                <td>[TBC:employees_with_disabilities_pct]%</td>
            </tr>
        </tbody>
    </table>

    <h5>Data source and methodology</h5>
    <p>Workforce data is sourced from the undertaking's human resources information system (HRIS). Headcount data is reported on a full-time equivalent (FTE) basis. Part-time employees are counted proportionally. Employees on long-term leave (including parental leave, sick leave, and sabbaticals) are included in headcount figures. Data is compiled in accordance with ESRS S1 datapoint definitions.</p>
    <p>Non-employee workers (agency workers, independent contractors) are not included in the above headcount figures. Information on non-employee workers is provided in [ESRS S1-6 paragraph 50 / separate disclosure] where material.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ))

                elif std_code == "S2":
                    if dr_id == "S2-1":
                        blocks.append(ContentBlock(
                            block_id="s2-1-policies",
                            standard_ref="ESRS S2",
                            paragraph_ref="1-10",
                            title="Value Chain Worker Policies",
                            content_html=f"""<div class="s2-1-content">
    <h4>S2-1 — Policies related to value chain workers</h4>
    <p><strong>{template.company_name}</strong> recognises its responsibility to respect the rights of workers throughout its value chain, including employees of suppliers, subcontractors, logistics partners, and other business partners. Policies have been established in accordance with ESRS S2 paragraphs 1-10, the OECD Due Diligence Guidance for Responsible Business Conduct, and the UN Guiding Principles on Business and Human Rights.</p>

    <h5>Supplier Code of Conduct</h5>
    <p>The Supplier Code of Conduct sets out the minimum standards and expectations for all suppliers, contractors, and business partners. The Code covers:</p>
    <ul>
        <li><strong>Labour rights:</strong> Prohibition of child labour, forced labour, and human trafficking. Compliance with ILO Core Conventions on freedom of association, collective bargaining, non-discrimination, and working hours.</li>
        <li><strong>Health and safety:</strong> Provision of a safe and healthy working environment, including occupational safety training, emergency preparedness, and access to clean water and sanitation facilities.</li>
        <li><strong>Fair wages and working conditions:</strong> Payment of at least the applicable minimum wage or living wage where required, compliance with working time regulations, and provision of legally mandated social protection.</li>
        <li><strong>Environmental responsibility:</strong> Compliance with applicable environmental laws and regulations, including pollution prevention, waste management, and GHG emissions reduction.</li>
        <li><strong>Ethical conduct:</strong> Zero tolerance for corruption, bribery, fraud, and unethical business practices.</li>
    </ul>
    <p>The Supplier Code of Conduct is incorporated into all supplier contracts. Suppliers are required to cascade these requirements to their own subcontractors and supply chain.</p>

    <h5>Human rights due diligence policy</h5>
    <p>The undertaking's Human Rights Due Diligence Policy establishes a systematic approach to identifying, preventing, mitigating, and accounting for adverse human rights impacts in the value chain. The policy requires:</p>
    <ul>
        <li>Risk-based due diligence for all new and existing suppliers, with enhanced due diligence for high-risk countries and sectors.</li>
        <li>Regular human rights impact assessments (HRIAs) for high-risk supply chain segments.</li>
        <li>Remediation of adverse impacts that the undertaking has caused or contributed to.</li>
        <li>Meaningful engagement with affected stakeholders and worker representatives.</li>
        <li>Public reporting on due diligence processes and outcomes.</li>
    </ul>

    <h5>Policy scope and applicability</h5>
    <p>Value chain worker policies apply to all:</p>
    <ul>
        <li>Direct suppliers (Tier 1) of goods and services.</li>
        <li>Subcontractors and contract labour providers.</li>
        <li>Logistics and transportation partners.</li>
        <li>Licensed manufacturers and franchisees (where applicable).</li>
        <li>Joint venture partners where the undertaking has operational control.</li>
    </ul>
    <p>The undertaking covers approximately [TBC:tier1_suppliers_count] Tier 1 suppliers and [TBC:tier2_suppliers_estimated] Tier 2 suppliers under its policy framework.</p>

    <h5>Alignment with international standards</h5>
    <p>These policies are aligned with:</p>
    <ul>
        <li>International Labour Organization (ILO) Declaration on Fundamental Principles and Rights at Work.</li>
        <li>OECD Guidelines for Multinational Enterprises.</li>
        <li>UN Guiding Principles on Business and Human Rights (UNGPs).</li>
        <li>EU Corporate Sustainability Due Diligence Directive (CSDDD) — where already transposed into national law.</li>
        <li>National legislation on supply chain due diligence (e.g., German Supply Chain Due Diligence Act, French Duty of Vigilance Law).</li>
    </ul>

    <h5>Policy governance and review</h5>
    <p>Value chain policies are approved by the Chief Procurement Officer and reviewed at least annually. The Head of Sustainability and Human Rights is responsible for monitoring implementation and effectiveness. Policies are communicated to suppliers through the procurement portal, onboarding processes, and periodic training sessions. Non-compliance may result in corrective action plans, increased audit frequency, or termination of the business relationship.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ))
                    elif dr_id == "S2-2":
                        blocks.append(ContentBlock(
                            block_id="s2-2-engagement",
                            standard_ref="ESRS S2",
                            paragraph_ref="11-18",
                            title="Engagement with Value Chain Workers",
                            content_html=f"""<div class="s2-2-content">
    <h4>S2-2 — Processes for engaging with value chain workers about impacts</h4>
    <p><strong>{template.company_name}</strong> engages with workers in its value chain, directly or through their legitimate representatives, to understand their perspectives, identify actual and potential impacts, and develop effective mitigation and remediation measures, in accordance with ESRS S2 paragraphs 11-18.</p>

    <h5>Engagement approach</h5>
    <p>Given the scale and geographical diversity of the value chain, the undertaking uses a combination of direct and indirect engagement methods:</p>
    <table>
        <thead>
            <tr>
                <th>Engagement method</th>
                <th>Description</th>
                <th>Frequency</th>
                <th>Coverage</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Supplier self-assessment questionnaires</td>
                <td>Standardised questionnaires covering labour rights, health and safety, environmental management, and ethics</td>
                <td>Annual (for all Tier 1 suppliers)</td>
                <td>[TBC:tier1_suppliers_count] suppliers</td>
            </tr>
            <tr>
                <td>Supplier audits (on-site)</td>
                <td>Audits conducted by internal teams or accredited third-party auditors, including worker interviews</td>
                <td>Risk-based (high-risk suppliers: annual; other: biennial)</td>
                <td>[TBC:supplier_audits_last_year] audits in reporting period</td>
            </tr>
            <tr>
                <td>Worker grievance channels at supplier sites</td>
                <td>Confidential reporting channels (phone, email, web portal) accessible to workers at supplier facilities</td>
                <td>Ongoing</td>
                <td>All Tier 1 suppliers</td>
            </tr>
            <tr>
                <td>Multi-stakeholder initiatives</td>
                <td>Participation in industry-wide initiatives that include worker representation and civil society organisations</td>
                <td>Ongoing</td>
                <td>[TO BE CONFIRMED — e.g., "Member of the Ethical Trading Initiative"]</td>
            </tr>
            <tr>
                <td>Supplier capability-building workshops</td>
                <td>Training sessions for supplier management and worker representatives on labour rights, health and safety, and environmental compliance</td>
                <td>Quarterly</td>
                <td>High-priority suppliers</td>
            </tr>
        </tbody>
    </table>

    <h5>Purpose of engagement</h5>
    <p>Engagement with value chain workers serves to:</p>
    <ul>
        <li>Identify actual and potential negative impacts on workers (e.g., unsafe working conditions, excessive working hours, wage violations).</li>
        <li>Assess the effectiveness of existing due diligence and mitigation measures.</li>
        <li>Understand workers' own priorities and perspectives.</li>
        <li>Build supplier capacity to manage labour and human rights issues.</li>
        <li>Inform the undertaking's responsible sourcing strategy and target-setting.</li>
    </ul>

    <h5>Barriers and challenges</h5>
    <p>The undertaking recognises that engaging directly with workers in the value chain presents challenges, particularly in multi-tier supply chains, informal labour settings, and regions where freedom of association is restricted. The following measures are taken to address these barriers:</p>
    <ul>
        <li>Use of confidential and anonymous worker voice tools (e.g., mobile surveys, hotlines).</li>
        <li>Engagement with trade unions and civil society organisations as intermediaries.</li>
        <li>Third-party audits that include anonymous worker interviews.</li>
        <li>Collaboration with industry peers and multi-stakeholder initiatives to amplify engagement reach.</li>
    </ul>

    <h5>Feedback integration</h5>
    <p>Findings from value chain worker engagement are reported to the Chief Procurement Officer and the Sustainability Committee. Key findings inform supplier corrective action plans, training programmes, and updates to the Supplier Code of Conduct. Worker perspectives are considered in the double materiality assessment (see IRO-1).</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ))
                    elif dr_id == "S2-3":
                        blocks.append(ContentBlock(
                            block_id="s2-3-remediation",
                            standard_ref="ESRS S2",
                            paragraph_ref="19-25",
                            title="Remediation — Value Chain Impacts",
                            content_html=f"""<div class="s2-3-content">
    <h4>S2-3 — Processes to remediate negative impacts and channels for value chain workers to raise concerns</h4>
    <p><strong>{template.company_name}</strong> has established processes to remediate negative impacts on value chain workers and provides accessible channels through which workers can raise concerns, in accordance with ESRS S2 paragraphs 19-25.</p>

    <h5>Grievance mechanisms for value chain workers</h5>
    <p>The following channels are available for workers in the value chain to raise concerns or report grievances:</p>
    <table>
        <thead>
            <tr>
                <th>Channel</th>
                <th>Description</th>
                <th>Languages</th>
                <th>Confidentiality</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Supplier grievance hotline</td>
                <td>Independent, third-party-operated hotline accessible by phone and web portal</td>
                <td>[TBC:grievance_languages_count] languages</td>
                <td>Anonymous option available</td>
            </tr>
            <tr>
                <td>Supplier audit findings and corrective action plans</td>
                <td>Concerns identified during audits are documented, and suppliers are required to implement corrective actions</td>
                <td>Local language</td>
                <td>Confidential within audit process</td>
            </tr>
            <tr>
                <td>Direct communication with the undertaking's procurement team</td>
                <td>Workers or their representatives can contact the undertaking's responsible sourcing team</td>
                <td>[TBC:grievance_languages_count] languages</td>
                <td>Confidential</td>
            </tr>
            <tr>
                <td>Multi-stakeholder initiative grievance mechanisms</td>
                <td>Access to grievance mechanisms provided through industry initiatives in which the undertaking participates</td>
                <td>Varies by initiative</td>
                <td>As per initiative rules</td>
            </tr>
        </tbody>
    </table>

    <h5>Remediation process</h5>
    <p>When a negative impact on value chain workers is identified (through audits, grievances, or other channels), the following process applies:</p>
    <ol>
        <li><strong>Reporting and documentation:</strong> The issue is logged and assessed for severity and urgency.</li>
        <li><strong>Notification:</strong> The supplier is notified and required to investigate the issue and submit a root cause analysis.</li>
        <li><strong>Corrective action plan (CAP):</strong> A CAP is developed with clear milestones, timelines, and responsible parties. The supplier is required to implement remediation measures.</li>
        <li><strong>Verification:</strong> The undertaking verifies implementation through follow-up audits, document reviews, or worker interviews.</li>
        <li><strong>Escalation:</strong> If the supplier fails to implement the CAP within the agreed timeline, the matter is escalated to senior procurement management. Continued non-compliance may result in suspension or termination of the business relationship.</li>
        <li><strong>Remedy:</strong> Where workers have suffered harm, the undertaking seeks to provide or enable remediation (e.g., back payment of wages, compensation for injuries, reinstatement where appropriate).</li>
    </ol>

    <h5>Remediation cases during the reporting period</h5>
    <table>
        <thead>
            <tr>
                <th>Issue type</th>
                <th>Number of cases</th>
                <th>Resolved</th>
                <th>Remediation provided</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Wage / working hours violations</td>
                <td>[TBC:grievances_received]</td>
                <td>[TBC:grievances_resolved]</td>
                <td>[TO BE CONFIRMED]</td>
            </tr>
            <tr>
                <td>Health and safety issues</td>
                <td>[TBC:grievances_received]</td>
                <td>[TBC:grievances_resolved]</td>
                <td>[TO BE CONFIRMED]</td>
            </tr>
            <tr>
                <td>Discrimination / harassment</td>
                <td>[TBC:grievances_received]</td>
                <td>[TBC:grievances_resolved]</td>
                <td>[TO BE CONFIRMED]</td>
            </tr>
            <tr>
                <td>Other human rights issues</td>
                <td>[TBC:grievances_received]</td>
                <td>[TBC:grievances_resolved]</td>
                <td>[TO BE CONFIRMED]</td>
            </tr>
        </tbody>
    </table>

    <h5>Protection against retaliation</h5>
    <p>The undertaking prohibits any form of retaliation against value chain workers who raise concerns, use grievance channels, or participate in audits. Suppliers are required to include non-retaliation clauses in their employment policies. Workers who report violations anonymously are protected through the confidentiality of the reporting mechanism.</p>

    <h5>Effectiveness assessment</h5>
    <p>The effectiveness of remediation processes is evaluated through:</p>
    <ul>
        <li>Rate of corrective action plan closure within agreed timelines.</li>
        <li>Re-audit scores and recurrence rates of identified issues.</li>
        <li>Worker satisfaction surveys at remediated supplier sites (where feasible).</li>
        <li>Analysis of grievance data to identify systemic issues requiring broader policy or process changes.</li>
    </ul>
</div>""",
                            content_type="narrative",
                            order=1,
                        ))
                    elif dr_id == "S2-4":
                        blocks.append(ContentBlock(
                            block_id="s2-4-actions",
                            standard_ref="ESRS S2",
                            paragraph_ref="26-35",
                            title="Actions on Value Chain Material Impacts",
                            content_html=f"""<div class="s2-4-content">
    <h4>S2-4 — Taking action on material impacts on value chain workers</h4>
    <p><strong>{template.company_name}</strong> takes concrete actions to address material impacts on workers in its value chain, prevent potential adverse impacts, and promote positive outcomes, in accordance with ESRS S2 paragraphs 26-35.</p>

    <h5>Material impacts identified</h5>
    <p>Through the double materiality assessment and ongoing due diligence, the following material impacts on value chain workers have been identified:</p>
    <ul>
        <li><strong>Negative actual/potential impacts:</strong> [TO BE CONFIRMED — e.g., "health and safety risks in raw material extraction and processing, wage and working time compliance in manufacturing supply chain, limited freedom of association in certain jurisdictions"].</li>
        <li><strong>Positive actual/potential impacts:</strong> [TO BE CONFIRMED — e.g., "supplier capacity building on labour rights, long-term partnerships that provide stable demand and income for supplier workers"].</li>
    </ul>

    <h5>Action plan for managing value chain impacts</h5>
    <table>
        <thead>
            <tr>
                <th>Action</th>
                <th>Impact addressed</th>
                <th>Status</th>
                <th>Timeline</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Expansion of supplier audit programme to cover Tier 2 suppliers</td>
                <td>Health and safety, labour rights compliance</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TBC:substitution_timeline_years] years</td>
            </tr>
            <tr>
                <td>Implementation of worker voice technology platform at high-risk supplier sites</td>
                <td>Limited grievance access for workers</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TBC:substitution_timeline_years] years</td>
            </tr>
            <tr>
                <td>Supplier training programme on living wage and working time management</td>
                <td>Wage and working time violations</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TBC:substitution_timeline_years] years</td>
            </tr>
            <tr>
                <td>Integration of human rights criteria into strategic sourcing and procurement decisions</td>
                <td>Embedding human rights in procurement</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TBC:substitution_timeline_years] years</td>
            </tr>
            <tr>
                <td>Participation in industry-wide responsible sourcing initiative for [TBC:sector] sector/material</td>
                <td>Sector-level systemic issues</td>
                <td>[TO BE CONFIRMED]</td>
                <td>[TBC:substitution_timeline_years] years</td>
            </tr>
        </tbody>
    </table>

    <h5>Approach to preventing and mitigating negative impacts</h5>
    <p>The undertaking uses the following strategies to prevent and mitigate negative impacts on value chain workers:</p>
    <ul>
        <li><strong>Prevention:</strong> Supplier pre-qualification (human rights and environmental screening), contractual requirements (Supplier Code of Conduct), and capacity building (training, tools, and guidance).</li>
        <li><strong>Mitigation:</strong> Corrective action plans for identified non-compliances, enhanced monitoring of high-risk suppliers, and collaboration with industry peers and civil society organisations.</li>
        <li><strong>Remediation:</strong> Provision of remedy for actual adverse impacts, as described under S2-3.</li>
    </ul>

    <h5>Effectiveness tracking</h5>
    <p>The undertaking tracks the effectiveness of its actions through:</p>
    <ul>
        <li>Percentage of suppliers audited (target: [TBC:suppliers_code_of_conduct_pct]% of Tier 1 suppliers annually).</li>
        <li>Average audit score trend (target: improvement year-on-year).</li>
        <li>CAP closure rate (target: [TBC:suppliers_code_of_conduct_pct]% within agreed timeline).</li>
        <li>Reduction in severity and frequency of non-compliances over time.</li>
        <li>Number of workers reached through capacity-building programmes.</li>
    </ul>

    <h5>Resources allocated</h5>
    <p>Total expenditure on value chain worker-related actions during the reporting period: [TBC:annual_revenue_eur], including:</p>
    <ul>
        <li>Supplier auditing and monitoring: [TBC:annual_revenue_eur]</li>
        <li>Supplier training and capacity building: [TBC:annual_revenue_eur]</li>
        <li>Worker voice and grievance technology: [TBC:annual_revenue_eur]</li>
        <li>Multi-stakeholder initiative membership fees: [TBC:annual_revenue_eur]</li>
    </ul>
</div>""",
                            content_type="narrative",
                            order=1,
                        ))
                    elif dr_id == "S2-5":
                        blocks.append(ContentBlock(
                            block_id="s2-5-targets",
                            standard_ref="ESRS S2",
                            paragraph_ref="36-44",
                            title="Value Chain Worker Targets",
                            content_html=f"""<div class="s2-5-content">
    <h4>S2-5 — Targets related to managing material impacts on value chain workers</h4>
    <p><strong>{template.company_name}</strong> has established measurable targets to manage material negative and positive impacts on workers in the value chain, in accordance with ESRS S2 paragraphs 36-44.</p>

    <h5>Targets overview</h5>
    <table>
        <thead>
            <tr>
                <th>Target area</th>
                <th>Target</th>
                <th>Baseline (year)</th>
                <th>2026 target</th>
                <th>2030 target</th>
                <th>Current progress</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Supplier audit coverage</td>
                <td>% of Tier 1 suppliers audited annually</td>
                <td>[TBC:suppliers_code_of_conduct_pct]% ([TBC:emissions_baseline_year])</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
                <td>100%</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
            </tr>
            <tr>
                <td>Corrective action plan closure</td>
                <td>% of CAPs closed within agreed timeline</td>
                <td>[TBC:suppliers_code_of_conduct_pct]% ([TBC:emissions_baseline_year])</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
            </tr>
            <tr>
                <td>High-risk supplier engagement</td>
                <td>% of high-risk suppliers with active CAP or improvement programme</td>
                <td>[TBC:suppliers_code_of_conduct_pct]% ([TBC:emissions_baseline_year])</td>
                <td>100%</td>
                <td>100%</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
            </tr>
            <tr>
                <td>Worker grievance channels</td>
                <td>% of Tier 1 suppliers with operational worker grievance mechanism</td>
                <td>[TBC:suppliers_code_of_conduct_pct]% ([TBC:emissions_baseline_year])</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
                <td>100%</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
            </tr>
            <tr>
                <td>Supplier capacity building</td>
                <td>Number of supplier representatives trained on labour rights and human rights due diligence per year</td>
                <td>[TBC:tier1_suppliers_count] ([TBC:emissions_baseline_year])</td>
                <td>[TBC:tier1_suppliers_count]</td>
                <td>[TBC:tier1_suppliers_count]</td>
                <td>[TBC:tier1_suppliers_count]</td>
            </tr>
        </tbody>
    </table>

    <h5>Target-setting approach</h5>
    <p>Targets have been informed by:</p>
    <ul>
        <li>Supplier audit data and non-compliance trends.</li>
        <li>Human rights impact assessments conducted in high-risk segments of the value chain.</li>
        <li>Engagement with affected stakeholders, including trade unions and civil society organisations.</li>
        <li>Regulatory requirements (e.g., CSDDD, German Supply Chain Due Diligence Act).</li>
        <li>Industry benchmarks and multi-stakeholder initiative standards.</li>
    </ul>

    <h5>Target governance</h5>
    <p>Targets are approved by the Chief Procurement Officer and reviewed annually. Progress is reported to the Sustainability Committee and disclosed in the annual sustainability statement. Where targets are not on track to be met, the undertaking will disclose the reasons and any corrective actions taken.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ))

                drs.append(DisclosureRequirement(
                    dr_id=dr_id,
                    title=dr_title_prefix,
                    paragraph_ref=dr_pref,
                    is_mandatory=is_mandatory,
                    blocks=blocks,
                ))

            # Add the metrics DR (S1-6 or S2-7) with blocks
            metrics_dr_id = f"{std_code}-6" if std_code == "S1" else f"{std_code}-7"
            metrics_blocks = []

            if std_code == "S2" and metrics_dr_id == "S2-7":
                metrics_blocks.append(ContentBlock(
                    block_id="s2-7-metrics",
                    standard_ref="ESRS S2",
                    paragraph_ref="45-55",
                    title="Value Chain Worker Metrics",
                    content_html=f"""<div class="s2-7-content">
    <h4>S2-7 — Metrics related to workers in the value chain</h4>
    <p><strong>{template.company_name}</strong> discloses the following metrics on value chain workers in accordance with ESRS S2 paragraphs 45-55. Data is based on information collected through supplier self-assessments, audits, and due diligence processes.</p>

    <h5>Value chain profile</h5>
    <table>
        <thead>
            <tr>
                <th>Metric</th>
                <th>Value</th>
                <th>Notes</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Total number of Tier 1 suppliers</td>
                <td>[TBC:tier1_suppliers_count]</td>
                <td>Includes all direct suppliers of goods and services</td>
            </tr>
            <tr>
                <td>Total number of Tier 2 suppliers (estimated)</td>
                <td>[TBC:tier2_suppliers_estimated]</td>
                <td>Estimate based on spend analysis and industry data</td>
            </tr>
            <tr>
                <td>Estimated number of workers in Tier 1 supply chain</td>
                <td>[TBC:tier1_workers_estimated]</td>
                <td>Based on supplier-reported employment data (coverage: [TBC:suppliers_code_of_conduct_pct]% of suppliers)</td>
            </tr>
            <tr>
                <td>Estimated number of workers in Tier 2 supply chain</td>
                <td>[TBC:tier2_workers_estimated]</td>
                <td>Estimated using average workforce per supplier in relevant sectors</td>
            </tr>
            <tr>
                <td>Countries of operation in value chain</td>
                <td>[TBC:value_chain_countries]</td>
                <td>List countries: [TBC:value_chain_countries]</td>
            </tr>
            <tr>
                <td>High-risk countries in value chain</td>
                <td>[TBC:high_risk_countries]</td>
                <td>As defined by [TO BE CONFIRMED — e.g., "Amnesty International / ITUC Global Rights Index"]</td>
            </tr>
        </tbody>
    </table>

    <h5>Supplier due diligence coverage</h5>
    <table>
        <thead>
            <tr>
                <th>Indicator</th>
                <th>Year N-1</th>
                <th>Year N</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Suppliers covered by Code of Conduct</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
            </tr>
            <tr>
                <td>Suppliers assessed through self-assessment questionnaire</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
            </tr>
            <tr>
                <td>Suppliers audited on-site</td>
                <td>[TBC:supplier_audits_last_year]</td>
                <td>[TBC:supplier_audits_last_year]</td>
            </tr>
            <tr>
                <td>Suppliers with corrective action plan</td>
                <td>[TBC:suppliers_audited_count]</td>
                <td>[TBC:suppliers_audited_count]</td>
            </tr>
            <tr>
                <td>Suppliers terminated due to non-compliance</td>
                <td>[TBC:suppliers_terminated_count]</td>
                <td>[TBC:suppliers_terminated_count]</td>
            </tr>
        </tbody>
    </table>

    <h5>Audit results (most significant non-compliances identified)</h5>
    <table>
        <thead>
            <tr>
                <th>Non-compliance category</th>
                <th>% of audited suppliers affected</th>
                <th>Most common issues</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Health and safety</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
                <td>[TO BE CONFIRMED]</td>
            </tr>
            <tr>
                <td>Working hours</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
                <td>[TO BE CONFIRMED]</td>
            </tr>
            <tr>
                <td>Wages and benefits</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
                <td>[TO BE CONFIRMED]</td>
            </tr>
            <tr>
                <td>Freedom of association</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
                <td>[TO BE CONFIRMED]</td>
            </tr>
            <tr>
                <td>Environmental management</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
                <td>[TO BE CONFIRMED]</td>
            </tr>
        </tbody>
    </table>

    <h5>Data source and methodology</h5>
    <p>Data on value chain workers is collected through the undertaking's supplier due diligence platform. Supplier-reported data is subject to verification through audits and documentary review. Where direct data is not available (e.g., Tier 2 suppliers), estimates are used and clearly indicated. The undertaking is committed to improving data coverage and quality over successive reporting cycles.</p>
    <p><strong>Boundary:</strong> Data covers Tier 1 suppliers only, unless otherwise stated. Tier 2 and beyond are not systematically covered at this stage.</p>
    <p><strong>Limitations:</strong> The number of workers in the value chain is an estimate, as not all suppliers provide workforce data. The undertaking is working to increase data coverage through enhanced supplier onboarding and data collection processes.</p>
</div>""",
                    content_type="narrative",
                    order=1,
                ))

            drs.append(DisclosureRequirement(
                dr_id=metrics_dr_id,
                title=f"Metrics related to {title.lower()}",
                paragraph_ref="45-55",
                is_mandatory=True,
                blocks=metrics_blocks,
            ))

            section = ReportSection(
                section_id=f"soc-{std_code.lower()}",
                standard_ref=f"ESRS {std_code}",
                title=title,
                section_type=SectionType.SOCIAL,
                materiality_filter=MaterialityFilter.IF_MATERIAL,
                order={
                    "S1": 7, "S2": 8, "S3": 9, "S4": 10,
                }[std_code],
                is_material=False,
                disclosure_requirements=drs,
            )
            setattr(template, f"soc_{std_code.lower()}", section)


        # ── Sezione 4: Governance (G1) ──────────────────────────
        governance = ReportSection(
            section_id="gov-g1",
            standard_ref="ESRS G1",
            title="Business Conduct",
            section_type=SectionType.GOVERNANCE,
            materiality_filter=MaterialityFilter.IF_MATERIAL,
            order=11,
            is_material=False,
            disclosure_requirements=[
                DisclosureRequirement(
                    dr_id="G1-1",
                    title="Corporate culture and business conduct policies",
                    paragraph_ref="1-9",
                    is_mandatory=True,
                    blocks=[
                        ContentBlock(
                            block_id="g1-1-narrative",
                            standard_ref="ESRS G1",
                            paragraph_ref="1",
                            title="Business Conduct Policies",
                            content_html=f"""<div class="g1-1-content">
    <h4>G1-1 — Corporate culture and business conduct policies</h4>
    <p><strong>{template.company_name}</strong> is committed to maintaining the highest standards of business conduct, integrity, and ethical behaviour across all operations and throughout the value chain. The undertaking's corporate culture is underpinned by a clear set of policies, procedures, and training programmes designed to prevent misconduct, promote transparency, and foster a culture of accountability.</p>

    <h5>Corporate culture and values</h5>
    <p>The undertaking's corporate culture is defined by its core values: integrity, respect, responsibility, and transparency. These values are embedded in the Code of Conduct, which applies to all directors, officers, employees, and third parties acting on behalf of <strong>{template.company_name}</strong>. The Code of Conduct is available on the undertaking's intranet and website, and is communicated to all employees during onboarding and through annual refresher training.</p>

    <h5>Anti-corruption and anti-bribery policy</h5>
    <p><strong>{template.company_name}</strong> has a zero-tolerance policy towards corruption and bribery in all forms, including extortion, facilitation payments, and improper influence. The Anti-Corruption and Anti-Bribery Policy:</p>
    <ul>
        <li>Prohibits the offering, giving, soliciting, or accepting of any undue advantage (financial or otherwise) to or from any person, including public officials and private sector counterparts.</li>
        <li>Applies to all employees, directors, agents, consultants, contractors, and business partners worldwide.</li>
        <li>Establishes clear procedures for gifts, hospitality, donations, sponsorship, and conflicts of interest.</li>
        <li>Requires mandatory due diligence on third parties, including agents and intermediaries, before engagement.</li>
    </ul>

    <h5>Whistleblowing and reporting mechanisms</h5>
    <p>The undertaking maintains a confidential and anonymous whistleblowing channel (operated by an independent third party) through which employees and external stakeholders can report suspected violations of laws, regulations, or the Code of Conduct without fear of retaliation. All reports are investigated promptly, impartially, and confidentially by the Ethics Committee. The undertaking prohibits any form of retaliation against persons who raise concerns in good faith.</p>

    <h5>Training and awareness</h5>
    <p>Business conduct training is provided to all employees on an annual basis, with targeted modules for high-risk roles (e.g., procurement, sales, and management positions). Training covers: the Code of Conduct, anti-corruption and anti-bribery laws, conflicts of interest, competition law, data protection, and the whistleblowing procedure. Completion rates are tracked and reported to the Board annually.</p>

    <h5>Implementation and monitoring</h5>
    <p>The Compliance Officer is responsible for overseeing the implementation and effectiveness of business conduct policies. The internal audit function conducts periodic reviews of compliance with these policies, including transaction testing and control assessments. Findings are reported to the Audit Committee and Board, and remediation actions are tracked to completion.</p>

    <h5>Policy review and continuous improvement</h5>
    <p>All business conduct policies are reviewed at least annually and updated to reflect changes in laws, regulations, industry standards, and lessons learned from investigations or incidents. The Board approves material amendments to the Code of Conduct and the Anti-Corruption and Anti-Bribery Policy.</p>

    <h5>Business conduct in the value chain</h5>
    <p><strong>{template.company_name}</strong> requires its suppliers, contractors, and business partners to adhere to the Supplier Code of Conduct, which sets out minimum standards for ethical behaviour, human rights, labour practices, environmental responsibility, and anti-corruption. Compliance is monitored through audits, self-assessments, and contractual clauses.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ),
                    ],
                ),
                DisclosureRequirement(
                    dr_id="G1-2",
                    title="Management of relationships with suppliers",
                    paragraph_ref="10-16",
                    is_mandatory=True,
                    blocks=[
                        ContentBlock(
                            block_id="g1-2-supplier-relationships",
                            standard_ref="ESRS G1",
                            paragraph_ref="10-16",
                            title="Supplier Relationship Management",
                            content_html=f"""<div class="g1-2-content">
    <h4>G1-2 — Management of relationships with suppliers</h4>
    <p><strong>{template.company_name}</strong> manages supplier relationships through a structured procurement framework designed to ensure transparency, fairness, and alignment with the undertaking's values and sustainability commitments. Supplier relationship management is governed by the Procurement Policy, the Supplier Code of Conduct, and sector-specific procedures that cover the full procurement lifecycle: selection, onboarding, contracting, performance monitoring, and offboarding.</p>

    <h5>Supplier selection and onboarding</h5>
    <p>All suppliers are subject to a due diligence process before engagement, which includes: (i) assessment of financial stability and operational capability; (ii) review of compliance with applicable laws and regulations; (iii) evaluation of environmental, social, and governance (ESG) criteria; and (iv) anti-corruption screening. Suppliers in high-risk categories (based on geography, sector, or spend volume) undergo enhanced due diligence, including on-site audits where feasible.</p>

    <h5>Supplier Code of Conduct</h5>
    <p>The Supplier Code of Conduct sets out <strong>{template.company_name}</strong>'s minimum expectations for all suppliers, contractors, and business partners in the areas of: human rights and labour practices (including prohibition of child labour, forced labour, and discrimination); health and safety; environmental protection; anti-corruption and bribery; fair competition; data protection; and transparency. Suppliers are required to acknowledge and commit to the Code contractually. Non-compliance may result in corrective action plans, suspension, or termination of the business relationship.</p>

    <h5>ESG assessment in procurement</h5>
    <p><strong>{template.company_name}</strong> integrates ESG criteria into the procurement process. For strategic and high-value procurement categories, ESG performance is evaluated alongside price, quality, and delivery criteria. Suppliers with strong ESG performance are recognised through the Supplier Sustainability Awards programme, while underperforming suppliers are supported through capacity-building initiatives and corrective action plans.</p>

    <h5>Monitoring and evaluation</h5>
    <p>The performance of key suppliers is monitored through: (i) periodic self-assessment questionnaires covering ESG topics; (ii) on-site audits (conducted by internal teams or third-party auditors); (iii) ongoing review of key performance indicators (KPIs) and service-level agreements (SLAs); and (iv) annual business reviews. Findings from monitoring activities are shared with suppliers, and improvement plans are mutually agreed and tracked.</p>

    <h5>Supply chain transparency and traceability</h5>
    <p><strong>{template.company_name}</strong> is committed to improving transparency and traceability in its supply chain. The undertaking maps its Tier 1 suppliers and is progressively extending visibility to Tier 2 and beyond, focusing on high-risk categories. Supplier data — including information on ownership, locations, certifications, and workforce — is maintained in a centralised supplier management system.</p>

    <h5>Grievance mechanism for suppliers</h5>
    <p>Suppliers and their workers may report concerns or complaints through the undertaking's whistleblowing channel, which is accessible 24/7, anonymous, and available in multiple languages. Reports are investigated by the Ethics Committee, and no retaliation is tolerated against any party raising a concern in good faith.</p>

    <h5>Key supplier relationship metrics</h5>
    <table>
        <thead>
            <tr>
                <th>Metric</th>
                <th>Year N</th>
                <th>Year N-1</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Total number of active suppliers</td>
                <td>[TBC:tier1_suppliers_count]</td>
                <td>[TBC:tier1_suppliers_count]</td>
            </tr>
            <tr>
                <td>% of suppliers covered by Code of Conduct</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
            </tr>
            <tr>
                <td>% of suppliers assessed on ESG criteria</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
            </tr>
            <tr>
                <td>% of strategic suppliers with annual ESG review</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
            </tr>
            <tr>
                <td>Number of supplier audits conducted</td>
                <td>[TBC:supplier_audits_last_year]</td>
                <td>[TBC:supplier_audits_last_year]</td>
            </tr>
            <tr>
                <td>Suppliers terminated for non-compliance (ESG)</td>
                <td>[TBC:suppliers_terminated_count]</td>
                <td>[TBC:suppliers_terminated_count]</td>
            </tr>
        </tbody>
    </table>

    <h5>Social criteria in supply chain</h5>
    <p><strong>{template.company_name}</strong> considers the following social criteria in supplier selection and management: (i) compliance with labour laws and international labour standards (ILO Core Conventions); (ii) health and safety performance; (iii) respect for freedom of association and collective bargaining; (iv) prohibition of child labour and forced labour; (v) non-discrimination and equal opportunity; (vi) payment of living wages; and (vii) responsible working hours. These criteria are assessed through supplier self-declarations, audits, and third-party certifications (e.g., SA8000, Sedex SMETA, Fair Trade).</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ),
                    ],
                ),
                DisclosureRequirement(
                    dr_id="G1-3",
                    title="Prevention and detection of corruption and bribery",
                    paragraph_ref="17-23",
                    is_mandatory=True,
                    blocks=[
                        ContentBlock(
                            block_id="g1-3-anticorruption",
                            standard_ref="ESRS G1",
                            paragraph_ref="17-23",
                            title="Corruption and Bribery Prevention and Detection",
                            content_html=f"""<div class="g1-3-content">
    <h4>G1-3 — Prevention and detection of corruption and bribery</h4>
    <p><strong>{template.company_name}</strong> maintains a comprehensive anti-corruption and anti-bribery framework designed to prevent, detect, and respond to corruption and bribery risks across all operations and business relationships. The framework is aligned with applicable laws and regulations, including the UK Bribery Act 2010, the US Foreign Corrupt Practices Act (FCPA), and local anti-corruption legislation in all jurisdictions where the undertaking operates.</p>

    <h5>Prevention framework</h5>
    <p>The undertaking's prevention framework is based on a three-lines-of-defence model:</p>
    <ul>
        <li><strong>First line:</strong> Business units and functions implement controls embedded in day-to-day processes, including segregation of duties, approval limits, and mandatory due diligence on third parties.</li>
        <li><strong>Second line:</strong> The Compliance function sets policies, provides guidance and training, monitors compliance, and conducts risk assessments.</li>
        <li><strong>Third line:</strong> Internal Audit provides independent assurance on the design and effectiveness of the anti-corruption control framework.</li>
    </ul>

    <h5>Risk assessment</h5>
    <p>Corruption and bribery risk assessments are conducted annually at the entity level and at the process level for high-risk functions (e.g., procurement, sales, government affairs, and operations in high-risk jurisdictions). Risk assessments consider: (i) geographic risk (Transparency International Corruption Perceptions Index); (ii) sector risk; (iii) transaction complexity; (iv) third-party relationships (agents, intermediaries, joint venture partners); (v) interactions with public officials; and (vi) prior incidents or red flags. Risk ratings are used to calibrate the frequency and depth of controls and monitoring.</p>

    <h5>Key controls</h5>
    <p>The following controls are in place to prevent and detect corruption and bribery:</p>
    <ul>
        <li><strong>Third-party due diligence:</strong> All agents, intermediaries, consultants, and business partners are subject to tiered due diligence based on risk. High-risk third parties undergo enhanced due diligence, including beneficial ownership checks, sanctions screening, and reputational review.</li>
        <li><strong>Gifts, hospitality, and entertainment:</strong> Clear rules govern the offering and acceptance of gifts and hospitality, with defined monetary thresholds, pre-approval requirements, and mandatory recording in the Gifts and Hospitality Register.</li>
        <li><strong>Conflicts of interest:</strong> Employees must declare actual or potential conflicts of interest annually and on an ad hoc basis. Declarations are reviewed by the Compliance function.</li>
        <li><strong>Political and charitable contributions:</strong> Political contributions are prohibited unless approved by the Board. Charitable donations are subject to due diligence to avoid improper influence.</li>
        <li><strong>Financial controls:</strong> Anti-corruption controls are embedded in the financial control framework, including transaction monitoring, approval limits, and segregation of duties in payment processes.</li>
    </ul>

    <h5>Training and awareness</h5>
    <p>All employees receive mandatory annual anti-corruption training. High-risk roles (procurement, sales, finance, legal, and management) receive targeted training covering: (i) recognition of red flags; (ii) proper handling of gifts and hospitality; (iii) third-party due diligence procedures; (iv) reporting obligations; and (v) consequences of non-compliance. Training completion rates are tracked and reported to the Audit Committee.</p>

    <h5>Detection and monitoring</h5>
    <p>Detection mechanisms include: (i) confidential whistleblowing channel (operated by an independent third party, available 24/7 in all working languages); (ii) automated transaction monitoring for unusual patterns (e.g., payments to high-risk jurisdictions, round-dollar payments, split invoices); (iii) periodic compliance audits and reviews; (iv) enhanced monitoring of high-risk third parties; and (v) data analytics on expense reports and procurement data.</p>

    <h5>Investigation and remediation</h5>
    <p>All reported or detected allegations of corruption or bribery are investigated promptly by the Compliance function or, where appropriate, by external investigators. Investigations are conducted independently, impartially, and confidentially. Findings are reported to the Audit Committee and, where required, to relevant authorities. Remediation actions — including disciplinary measures, process improvements, and enhancements to controls — are tracked to completion.</p>

    <h5>Anti-corruption training metrics</h5>
    <table>
        <thead>
            <tr>
                <th>Indicator</th>
                <th>Year N</th>
                <th>Year N-1</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>% of employees who completed anti-corruption training</td>
                <td>[TBC:anti_corruption_training_pct]%</td>
                <td>[TBC:anti_corruption_training_pct]%</td>
            </tr>
            <tr>
                <td>% of high-risk employees who completed enhanced training</td>
                <td>[TBC:anti_corruption_training_pct]%</td>
                <td>[TBC:anti_corruption_training_pct]%</td>
            </tr>
            <tr>
                <td>% of Board members who completed training</td>
                <td>[TBC:anti_corruption_training_pct]%</td>
                <td>[TBC:anti_corruption_training_pct]%</td>
            </tr>
            <tr>
                <td>Number of third-party due diligence screenings conducted</td>
                <td>[TBC:corruption_incidents_count]</td>
                <td>[TBC:corruption_incidents_count]</td>
            </tr>
            <tr>
                <td>Number of investigations under anti-corruption policy</td>
                <td>[TBC:whistleblowing_reports_count]</td>
                <td>[TBC:whistleblowing_reports_count]</td>
            </tr>
        </tbody>
    </table>
</div>""",
                            content_type="narrative",
                            order=1,
                        ),
                    ],
                ),
                DisclosureRequirement(
                    dr_id="G1-4",
                    title="Incidents of corruption or bribery",
                    paragraph_ref="24-28",
                    is_mandatory=True,
                    blocks=[
                        ContentBlock(
                            block_id="g1-4-incidents",
                            standard_ref="ESRS G1",
                            paragraph_ref="24-28",
                            title="Corruption and Bribery Incidents",
                            content_html=f"""<div class="g1-4-content">
    <h4>G1-4 — Incidents of corruption or bribery</h4>
    <p><strong>{template.company_name}</strong> reports on incidents of corruption or bribery in accordance with ESRS G1 paragraphs 24-28. The undertaking maintains a zero-tolerance approach to corruption and bribery, and all confirmed incidents are disclosed transparently, including the nature of the incident, actions taken, and outcomes.</p>

    <p>For the reporting period [financial year N], the following incidents were recorded:</p>

    <h5>Incident summary</h5>
    <table>
        <thead>
            <tr>
                <th>Category</th>
                <th>Year N</th>
                <th>Year N-1</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Total number of reported incidents (whistleblowing channel)</td>
                <td>[TBC:whistleblowing_reports_count]</td>
                <td>[TBC:whistleblowing_reports_count]</td>
            </tr>
            <tr>
                <td>Incidents related to corruption or bribery</td>
                <td>[TBC:corruption_incidents_count]</td>
                <td>[TBC:corruption_incidents_count]</td>
            </tr>
            <tr>
                <td>Confirmed incidents of corruption</td>
                <td>[TBC:corruption_incidents_count]</td>
                <td>[TBC:corruption_incidents_count]</td>
            </tr>
            <tr>
                <td>Confirmed incidents of bribery</td>
                <td>[TBC:corruption_incidents_count]</td>
                <td>[TBC:corruption_incidents_count]</td>
            </tr>
            <tr>
                <td>Incidents involving public officials</td>
                <td>[TBC:corruption_incidents_count]</td>
                <td>[TBC:corruption_incidents_count]</td>
            </tr>
            <tr>
                <td>Incidents involving business partners or third parties</td>
                <td>[TBC:corruption_incidents_count]</td>
                <td>[TBC:corruption_incidents_count]</td>
            </tr>
        </tbody>
    </table>

    <h5>Legal and enforcement actions</h5>
    <table>
        <thead>
            <tr>
                <th>Indicator</th>
                <th>Year N</th>
                <th>Year N-1</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Convictions for corruption or bribery</td>
                <td>[TBC:corruption_incidents_count]</td>
                <td>[TBC:corruption_incidents_count]</td>
            </tr>
            <tr>
                <td>Fines or penalties imposed for corruption or bribery</td>
                <td>[TBC:annual_revenue_eur]</td>
                <td>[TBC:annual_revenue_eur]</td>
            </tr>
            <tr>
                <td>Pending legal actions related to corruption</td>
                <td>[TBC:corruption_incidents_count]</td>
                <td>[TBC:corruption_incidents_count]</td>
            </tr>
            <tr>
                <td>Contractual terminations due to corruption violations</td>
                <td>[TBC:suppliers_terminated_count]</td>
                <td>[TBC:suppliers_terminated_count]</td>
            </tr>
        </tbody>
    </table>

    <h5>Description of significant incidents</h5>
    <p>[TO BE CONFIRMED — Describe any significant incidents of corruption or bribery that occurred during the reporting period, including: (i) nature of the incident; (ii) jurisdictions affected; (iii) amounts involved; (iv) root causes; (v) remedial actions taken; (vi) disciplinary measures applied; (vii) improvements to the control framework implemented as a result.]</p>

    <h5>Contextual information</h5>
    <p>The number of reported incidents reflects the effectiveness of the whistleblowing channel and the awareness of employees and external stakeholders in reporting suspected misconduct. An increase in reported incidents may indicate greater awareness and trust in the reporting mechanism rather than an increase in actual misconduct. The undertaking monitors this trend and provides context to enable stakeholders to assess performance meaningfully.</p>

    <h5>Remediation and corrective actions</h5>
    <p>For each confirmed incident, <strong>{template.company_name}</strong> implements remediation actions appropriate to the nature and severity of the incident. Remediation may include: disciplinary action (up to and including termination of employment); termination of contracts with third parties; strengthening of internal controls; additional training; and reporting to relevant law enforcement or regulatory authorities. Lessons learned are shared across the organisation to prevent recurrence.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ),
                    ],
                ),
                DisclosureRequirement(
                    dr_id="G1-5",
                    title="Political influence and lobbying activities",
                    paragraph_ref="29-34",
                    is_mandatory=False,
                ),
                DisclosureRequirement(
                    dr_id="G1-6",
                    title="Payment practices",
                    paragraph_ref="35-40",
                    is_mandatory=True,
                    blocks=[
                        ContentBlock(
                            block_id="g1-6-payment-practices",
                            standard_ref="ESRS G1",
                            paragraph_ref="35-40",
                            title="Payment Practices",
                            content_html=f"""<div class="g1-6-content">
    <h4>G1-6 — Payment practices</h4>
    <p><strong>{template.company_name}</strong> discloses its payment practices in accordance with ESRS G1 paragraphs 35-40. The undertaking is committed to responsible payment practices that support a healthy and sustainable value chain, recognising that timely payment is critical to the financial well-being of suppliers, particularly small and medium-sized enterprises (SMEs).</p>

    <h5>Payment policy</h5>
    <p><strong>{template.company_name}</strong>'s standard payment terms are [TBC:standard_payment_terms_days] days from receipt of a valid invoice. Payment terms are agreed with suppliers on a case-by-case basis, taking into account the nature of the goods or services, market practice, and regulatory requirements. The undertaking does not systematically extend payment terms beyond [TBC:standard_payment_terms_days] days for SMEs unless specifically agreed in writing.</p>

    <p>All payment terms are clearly communicated to suppliers at the time of contracting and are reflected in purchase orders and contracts. The undertaking processes payments on the due date or earlier where possible, and does not engage in practices that would result in late payment without cause.</p>

    <h5>Standard payment terms by supplier category</h5>
    <table>
        <thead>
            <tr>
                <th>Supplier Category</th>
                <th>Standard Payment Term (days)</th>
                <th>% of Suppliers (by volume)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>SME suppliers</td>
                <td>[TBC:standard_payment_terms_days]</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
            </tr>
            <tr>
                <td>Large enterprise suppliers</td>
                <td>[TBC:standard_payment_terms_days]</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
            </tr>
            <tr>
                <td>Strategic/key suppliers</td>
                <td>[TBC:standard_payment_terms_days]</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
            </tr>
            <tr>
                <td>Public sector / institutional</td>
                <td>[TBC:standard_payment_terms_days]</td>
                <td>[TBC:suppliers_code_of_conduct_pct]%</td>
            </tr>
        </tbody>
    </table>

    <h5>Payment performance</h5>
    <table>
        <thead>
            <tr>
                <th>Indicator</th>
                <th>Year N</th>
                <th>Year N-1</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Average actual payment time (days from invoice receipt)</td>
                <td>[TBC:avg_actual_payment_time_days]</td>
                <td>[TBC:avg_actual_payment_time_days]</td>
            </tr>
            <tr>
                <td>% of invoices paid within standard terms</td>
                <td>[TBC:invoices_paid_within_terms_pct]%</td>
                <td>[TBC:invoices_paid_within_terms_pct]%</td>
            </tr>
            <tr>
                <td>% of invoices paid within 30 days</td>
                <td>[TBC:invoices_paid_within_terms_pct]%</td>
                <td>[TBC:invoices_paid_within_terms_pct]%</td>
            </tr>
            <tr>
                <td>% of invoices paid within 60 days</td>
                <td>[TBC:invoices_paid_within_terms_pct]%</td>
                <td>[TBC:invoices_paid_within_terms_pct]%</td>
            </tr>
            <tr>
                <td>% of invoices paid late (beyond agreed terms)</td>
                <td>[TBC:invoices_paid_late_pct]%</td>
                <td>[TBC:invoices_paid_late_pct]%</td>
            </tr>
            <tr>
                <td>Interest paid on late payments to suppliers</td>
                <td>[TBC:annual_revenue_eur]</td>
                <td>[TBC:annual_revenue_eur]</td>
            </tr>
            <tr>
                <td>Number of supplier disputes related to payment</td>
                <td>[TBC:suppliers_terminated_count]</td>
                <td>[TBC:suppliers_terminated_count]</td>
            </tr>
        </tbody>
    </table>

    <h5>Late payment statistics</h5>
    <p>In the reporting period, [TBC:invoices_paid_late_pct]% of invoices were paid after the agreed payment terms. The average delay for late payments was [TBC:avg_actual_payment_time_days] days. The main reasons for late payment were: (i) administrative delays (invoice discrepancies, processing backlog); (ii) system integration issues; and (iii) disputes over goods or services received. The undertaking is implementing process improvements to reduce the incidence of late payment, including automated invoice processing, enhanced supplier onboarding, and dedicated accounts payable support for suppliers.</p>

    <h5>Cross-border payment practices</h5>
    <p>For cross-border payments, <strong>{template.company_name}</strong> discloses the following practices:</p>
    <ul>
        <li>Standard cross-border payment terms: [TBC:standard_payment_terms_days] days from invoice.</li>
        <li>Currencies used: [TO BE CONFIRMED].</li>
        <li>Approach to currency exchange and hedging: [TO BE CONFIRMED].</li>
        <li>Any significant delays due to cross-border banking processes: [TO BE CONFIRMED].</li>
    </ul>

    <h5>Legal framework and voluntary commitments</h5>
    <p><strong>{template.company_name}</strong> complies with all applicable laws and regulations on payment practices in the jurisdictions where it operates, including the EU Late Payment Directive (2011/7/EU) and local transposition laws. The undertaking is a signatory to the [TO BE CONFIRMED — e.g., Prompt Payment Code, Supplier Charter, etc.] and reports annually on its payment performance.</p>

    <h5>Process for supplier feedback on payment practices</h5>
    <p>Suppliers can provide feedback on payment practices through the undertaking's supplier portal or by contacting the accounts payable team directly. Feedback is reviewed quarterly and used to improve payment processes. Any concerns raised by suppliers regarding payment terms or delays are escalated to the Procurement function and addressed on a case-by-case basis.</p>
</div>""",
                            content_type="narrative",
                            order=1,
                        ),
                    ],
                ),
            ],
        )

        # Aggiungi tutte le sezioni al template
        template.add_section(general)
        template.add_section(environmental_e1)
        # E2-E5 già aggiunte nel loop
        for std_code in ["S1", "S2", "S3", "S4"]:
            template.add_section(
                getattr(template, f"soc_{std_code.lower()}")
            )
        template.add_section(governance)

        return template


# ── Helper functions ──────────────────────────────────────────────

def create_table_block(
    block_id: str,
    standard_ref: str,
    paragraph_ref: str,
    title: str,
    headers: List[str],
    rows: List[List[str]],
    datapoint_refs: Optional[List[str]] = None,
) -> ContentBlock:
    """
    Helper per creare un ContentBlock di tipo tabella.
    
    Args:
        block_id: ID del blocco
        standard_ref: Riferimento ESRS
        paragraph_ref: Riferimento paragrafo
        title: Titolo della tabella
        headers: Intestazioni colonne
        rows: Righe della tabella
        datapoint_refs: Riferimenti datapoint opzionali
        
    Returns:
        ContentBlock configurato come tabella HTML
    """
    header_html = "".join(f"<th>{h}</th>" for h in headers)
    row_html = ""
    for row in rows:
        cells = "".join(f"<td>{c}</td>" for c in row)
        row_html += f"<tr>{cells}</tr>"

    table_html = f"""
<table>
    <thead><tr>{header_html}</tr></thead>
    <tbody>{row_html}</tbody>
</table>"""

    return ContentBlock(
        block_id=block_id,
        standard_ref=standard_ref,
        paragraph_ref=paragraph_ref,
        title=title,
        content_html=table_html,
        content_type="table",
        datapoint_refs=datapoint_refs or [],
        order=1,
    )


def create_narrative_block(
    block_id: str,
    standard_ref: str,
    paragraph_ref: str,
    title: str,
    content: str,
    datapoint_refs: Optional[List[str]] = None,
) -> ContentBlock:
    """
    Helper per creare un ContentBlock di tipo narrativo.
    
    Args:
        block_id: ID del blocco
        standard_ref: Riferimento ESRS
        paragraph_ref: Riferimento paragrafo
        title: Titolo del blocco
        content: Testo narrativo
        datapoint_refs: Riferimenti datapoint opzionali
        
    Returns:
        ContentBlock configurato come narrativa
    """
    return ContentBlock(
        block_id=block_id,
        standard_ref=standard_ref,
        paragraph_ref=paragraph_ref,
        title=title,
        content_html=content,
        content_type="narrative",
        datapoint_refs=datapoint_refs or [],
        order=1,
    )