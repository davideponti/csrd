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

    def _default_title(self) -> str:
        """Genera il titolo predefinito del report."""
        return f"CSRD Sustainability Report {self.reporting_year}"

    # ── Sezioni predefinite del report ───────────────────────────

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
            return "—"

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

    def set_materiality(
        self,
        material_standards: List[str],
    ) -> None:
        """
        Imposta la materialità delle sezioni in base agli standard materiali.
        
        Args:
            material_standards: Lista di standard_ref materiali (es. ["ESRS E1", "ESRS S1"])
        """
        for section in self.sections:
            if section.materiality_filter == MaterialityFilter.ALWAYS:
                section.is_material = True
            elif section.materiality_filter == MaterialityFilter.IF_MATERIAL:
                section.is_material = section.standard_ref in material_standards

    # ── Rendering ───────────────────────────────────────────────

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

        return "\n".join(parts)

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
                            content_html="To be completed: Describe the general basis for preparation of the sustainability statement.",
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
                            content_html="To be completed: Describe the composition and roles of governance bodies regarding sustainability matters.",
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
                            content_html="To be completed: Describe the strategy, business model and value chain.",
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
                            content_html="To be completed: Describe the double materiality assessment process.",
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
                            content_html="<p>To be completed: List of material ESRS topics and Disclosure Requirements.</p>",
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
                            content_html="To be completed: Describe GHG emissions methodology, sources and changes.",
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
                            content_html="To be completed: Describe corporate culture, anti-corruption and anti-bribery policies.",
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
