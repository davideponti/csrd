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
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import json


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

        # Materiality tracking — populated by set_materiality()
        self.material_standards: List[str] = []
        self.non_material_standards: List[str] = []
        # Emissions data for narrative context
        self._emissions_data: Dict[str, Any] = {}

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
    <p class="cover-meta">Country: {self.cover_page.company_country}</p>
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
            set(self.STANDARD_NAMES.keys()) - set(self.material_standards)
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
        return self._resolve_iro2_placeholder(raw)

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
                            content_html="To be completed: Describe specific circumstances and estimations used.",
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
    <p><strong>{template.company_name}</strong> operates in the <strong>{template.company_sector or 'designated'}</strong> sector, serving customers primarily in {template.company_country or 'its home market'} and internationally. The undertaking's business model is centred on creating sustainable value through responsible operations, innovation, and stakeholder engagement.</p>

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
        <li><strong>Upstream:</strong> Sourcing of raw materials and components from suppliers, assessed for environmental and social performance through the undertaking's supplier due diligence process (<strong>{template.employee_count or 'X'}</strong> employees are involved in procurement and supply chain management).</li>
        <li><strong>Direct operations:</strong> Manufacturing, service delivery, and corporate functions managed with a focus on reducing GHG emissions, promoting workforce health and safety, and upholding ethical business conduct.</li>
        <li><strong>Downstream:</strong> Distribution, product use, and end-of-life management. The undertaking engages with customers to promote circular economy principles and responsible consumption.</li>
    </ul>

    <h5>Key business relationships</h5>
    <p>The undertaking's key business relationships include B2B and B2C customers, long-term suppliers, joint venture partners, financial institutions, and local communities. These relationships are managed through dedicated account management, supplier codes of conduct, community engagement programmes, and regular stakeholder dialogues.</p>

    <h5>Products, services and markets</h5>
    <p>The undertaking offers a diversified portfolio of products and services tailored to the evolving needs of its target markets. Revenue is generated primarily through direct sales, recurring service contracts, and long-term customer relationships. The geographic footprint spans {template.company_country or 'multiple jurisdictions'}, with growth opportunities identified in sectors aligned with the sustainability transition.</p>

    <h5>Employees by geography and segment</h5>
    <p>As of the reporting date, <strong>{template.company_name}</strong> employs approximately <strong>{template.employee_count or 'X'}</strong> people. The workforce is distributed across operational functions (production, logistics, sales) and support functions (administration, R&D, management). Employee engagement, training, and well-being are prioritised as key enablers of the sustainability strategy.</p>
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

        # Sezioni E2-E5 (placeholder, leggere)
        for std_code, title in [
            ("E2", "Pollution"),
            ("E3", "Water and Marine Resources"),
            ("E4", "Biodiversity and Ecosystems"),
            ("E5", "Resource Use and Circular Economy"),
        ]:
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
                    disclosure_requirements=[
                        DisclosureRequirement(
                            dr_id=f"{std_code}-1",
                            title=f"Policies related to {title.lower()}",
                            paragraph_ref="1-8",
                            is_mandatory=True,
                        ),
                        DisclosureRequirement(
                            dr_id=f"{std_code}-2",
                            title=f"Actions and resources",
                            paragraph_ref="9-15",
                            is_mandatory=True,
                        ),
                        DisclosureRequirement(
                            dr_id=f"{std_code}-3",
                            title=f"Targets related to {title.lower()}",
                            paragraph_ref="16-24",
                            is_mandatory=True,
                        ),
                        DisclosureRequirement(
                            dr_id=f"{std_code}-4",
                            title=f"Metrics related to {title.lower()}",
                            paragraph_ref="25-35",
                            is_mandatory=True,
                        ),
                        DisclosureRequirement(
                            dr_id=f"{std_code}-5",
                            title="Anticipated financial effects",
                            paragraph_ref="36-42",
                            is_mandatory=False,
                        ),
                    ],
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
                disclosure_requirements=[
                    DisclosureRequirement(
                        dr_id=f"{std_code}-1",
                        title=f"Policies related to {title.lower()}",
                        paragraph_ref="1-10",
                        is_mandatory=True,
                    ),
                    DisclosureRequirement(
                        dr_id=f"{std_code}-2",
                        title="Processes for engaging with stakeholders",
                        paragraph_ref="11-18",
                        is_mandatory=True,
                    ),
                    DisclosureRequirement(
                        dr_id=f"{std_code}-3",
                        title="Processes to remediate negative impacts",
                        paragraph_ref="19-25",
                        is_mandatory=True,
                    ),
                    DisclosureRequirement(
                        dr_id=f"{std_code}-4",
                        title="Taking action on material impacts and managing risks",
                        paragraph_ref="26-35",
                        is_mandatory=True,
                    ),
                    DisclosureRequirement(
                        dr_id=f"{std_code}-5",
                        title="Targets related to managing material impacts",
                        paragraph_ref="36-44",
                        is_mandatory=True,
                    ),
                    DisclosureRequirement(
                        dr_id=f"{std_code}-6" if std_code == "S1" else f"{std_code}-7",
                        title=f"Metrics related to {title.lower()}",
                        paragraph_ref="45-55",
                        is_mandatory=True,
                    ),
                ],
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
                ),
                DisclosureRequirement(
                    dr_id="G1-3",
                    title="Prevention and detection of corruption and bribery",
                    paragraph_ref="17-23",
                    is_mandatory=True,
                ),
                DisclosureRequirement(
                    dr_id="G1-4",
                    title="Incidents of corruption or bribery",
                    paragraph_ref="24-28",
                    is_mandatory=True,
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
