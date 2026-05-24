"""
CSRD Comply — Table Generator (Step 19)

Genera tabelle ESRS-compliant e grafici interattivi per il report CSRD.
Ogni Disclosure Requirement quantitativo richiede una tabella con formati
specifici per ogni datapoint.

Tipi tabella supportati:
- Standard: GHG, Energy, Water, Waste, Workforce
- Comparative: N vs N-1
- Multi-year: ultimi 3-5 anni
- Breakdown: per paese/settore/subsidiary

Integrazione:
- Popola tabelle con dati da emissions_data
- Applica formattazione iXBRL-ready
- Genera dati per grafici Chart.js / Recharts
"""

import json
import logging
from typing import Optional, Dict, Any, List, Tuple, Literal
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


# ── Enums & Types ─────────────────────────────────────────────────

TableType = Literal[
    "ghg",              # GHG emissions table (ESRS E1-6)
    "energy",           # Energy consumption & mix (ESRS E1-5)
    "water",            # Water consumption (ESRS E3-4)
    "waste",            # Waste metrics (ESRS E5-5)
    "workforce",        # Workforce demographics (ESRS S1-6)
    "comparative",      # N vs N-1 comparison
    "multi_year",       # Multiple years trend
    "breakdown",        # Breakdown by country/sector/subsidiary
    "custom",           # Custom table from arbitrary data
]

ChartType = Literal[
    "bar",              # Bar chart
    "line",             # Line chart
    "pie",              # Pie chart
    "doughnut",         # Doughnut chart
    "stacked_bar",      # Stacked bar chart
    "scatter",          # Scatter plot
]


# ── Data Classes ──────────────────────────────────────────────────

@dataclass
class TableColumn:
    """
    Colonna di una tabella ESRS.
    
    Attributes:
        header: Intestazione della colonna
        field: Nome del campo dati
        unit: Unit di misura (opzionale)
        format: Formato di visualizzazione (es. "#,##0.00", "0.0%")
        alignment: Allineamento (left, center, right)
        width: Larghezza opzionale (es. "150px")
    """
    header: str
    field: str
    unit: str = ""
    format: str = ""
    alignment: str = "left"
    width: str = ""


@dataclass
class TableRow:
    """
    Riga di una tabella ESRS.
    
    Attributes:
        label: Etichetta della riga (es. "Scope 1 (tCO2e)")
        values: Dizionario field -> valore
        is_header: Se è una riga di intestazione di gruppo
        is_total: Se è una riga di totale
        indent: Livello di indentazione (0 = nessuna)
    """
    label: str
    values: Dict[str, Any] = field(default_factory=dict)
    is_header: bool = False
    is_total: bool = False
    indent: int = 0


@dataclass
class ChartData:
    """
    Dati per la generazione di un grafico.
    
    Attributes:
        chart_type: Tipo di grafico
        labels: Etichette per l'asse X
        datasets: Lista di serie dati
        title: Titolo del grafico
        x_label: Etichetta asse X
        y_label: Etichetta asse Y
        unit: Unit di misura
    """
    chart_type: ChartType
    labels: List[str] = field(default_factory=list)
    datasets: List[Dict[str, Any]] = field(default_factory=list)
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    unit: str = ""


@dataclass
class ESRSDataTable:
    """
    Tabella ESRS completa.
    
    Attributes:
        table_type: Tipo di tabella
        table_id: Identificativo univoco
        title: Titolo della tabella
        standard_ref: Riferimento ESRS (es. "ESRS E1-6")
        paragraph_ref: Riferimento paragrafo
        description: Descrizione opzionale
        columns: Lista di colonne
        rows: Lista di righe
        footnotes: Note a piè di pagina
        chart: Dati per grafico opzionale (se richiesto)
        xbrl_ready: Se la tabella è pronta per tagging iXBRL
        source: Fonte dei dati (es. "emissions_data", "materiality_scores")
    """
    table_type: TableType
    table_id: str
    title: str
    standard_ref: str
    paragraph_ref: str = ""
    description: str = ""
    columns: List[TableColumn] = field(default_factory=list)
    rows: List[TableRow] = field(default_factory=list)
    footnotes: List[str] = field(default_factory=list)
    chart: Optional[ChartData] = None
    xbrl_ready: bool = False
    source: str = ""


# ── Table Generator ──────────────────────────────────────────────

class TableGenerator:
    """
    Generatore di tabelle ESRS-compliant per report CSRD.
    
    Genera tabelle HTML formattate secondo gli standard ESRS,
    con supporto per tagging iXBRL e grafici.
    
    Usage:
        generator = TableGenerator()
        
        # Tabella GHG
        ghg_table = generator.generate_ghg_table(emissions_data)
        
        # Render HTML
        html = generator.render_table_html(ghg_table)
        
        # Con grafico
        ghg_table = generator.generate_ghg_table(
            emissions_data, include_chart=True
        )
    """

    # Template CSS per le tabelle
    TABLE_CSS = """
    .esrs-table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px; }
    .esrs-table th { background-color: #1a365d; color: white; padding: 10px 12px; text-align: left; font-weight: 600; border: 1px solid #2b6cb0; }
    .esrs-table td { padding: 8px 12px; border: 1px solid #e2e8f0; }
    .esrs-table tr:nth-child(even) { background-color: #f7fafc; }
    .esrs-table tr:hover { background-color: #ebf8ff; }
    .esrs-table .row-total { font-weight: bold; background-color: #edf2f7 !important; }
    .esrs-table .row-header { font-weight: 600; background-color: #e2e8f0 !important; }
    .esrs-table .indent-1 { padding-left: 24px; }
    .esrs-table .indent-2 { padding-left: 40px; }
    .esrs-table .align-right { text-align: right; }
    .esrs-table .align-center { text-align: center; }
    .esrs-table-caption { font-size: 12px; color: #718096; margin-top: 4px; }
    """

    def __init__(self, language: str = "en"):
        """
        Inizializza il Table Generator.
        
        Args:
            language: Lingua per intestazioni tabelle
        """
        self.language = language
        self._labels = self._get_labels(language)

    def _get_labels(self, language: str) -> Dict[str, str]:
        """Restituisce le etichette localizzate per le tabelle."""
        labels = {
            "en": {
                "scope1": "Scope 1 (tCO2e)",
                "scope2_location": "Scope 2 location-based (tCO2e)",
                "scope2_market": "Scope 2 market-based (tCO2e)",
                "scope3": "Scope 3 total (tCO2e)",
                "total": "Total GHG emissions (tCO2e)",
                "year_n": "Year N",
                "year_n1": "Year N-1",
                "year_n2": "Year N-2",
                "change": "Change (%)",
                "category": "Category",
                "value": "Value",
                "unit": "Unit",
                "source": "Source",
                "methodology": "Methodology",
                "verified": "Verified",
                "not_available": "N/A",
            },
            "it": {
                "scope1": "Scope 1 (tCO2e)",
                "scope2_location": "Scope 2 location-based (tCO2e)",
                "scope2_market": "Scope 2 market-based (tCO2e)",
                "scope3": "Scope 3 totale (tCO2e)",
                "total": "Emissioni GHG totali (tCO2e)",
                "year_n": "Anno N",
                "year_n1": "Anno N-1",
                "year_n2": "Anno N-2",
                "change": "Variazione (%)",
                "category": "Categoria",
                "value": "Valore",
                "unit": "Unità",
                "source": "Fonte",
                "methodology": "Metodologia",
                "verified": "Verificato",
                "not_available": "N/D",
            },
        }
        return labels.get(language, labels["en"])

    # ── Generators per tipo tabella ──────────────────────────────

    def generate_ghg_table(
        self,
        emissions_data: Dict[str, Any],
        include_chart: bool = False,
        table_id: str = "ghg-emissions",
    ) -> ESRSDataTable:
        """
        Genera tabella GHG emissions (ESRS E1-6).
        
        Args:
            emissions_data: Dati emissioni con campi:
                - scope1: Dict con "value", "year_n", "year_n1"
                - scope2_location: Dict
                - scope2_market: Dict  
                - scope3: Dict o Dict per categoria
                - year: Anno corrente
            include_chart: Se includere dati per grafico
            table_id: ID della tabella
            
        Returns:
            ESRSDataTable con dati GHG
        """
        year = emissions_data.get("year", datetime.now().year)
        year_n = str(year)
        year_n1 = str(year - 1)
        
        # Helper per estrarre valori
        def get_val(data: Any, key: str = "value", default: Any = "—") -> Any:
            if isinstance(data, dict):
                return data.get(key, default)
            return data if data is not None else default
        
        # Prepara dati
        scope1 = get_val(emissions_data.get("scope1"))
        scope1_n1 = get_val(emissions_data.get("scope1_n1"))
        
        scope2_loc = get_val(emissions_data.get("scope2_location"))
        scope2_loc_n1 = get_val(emissions_data.get("scope2_location_n1"))
        
        scope2_mkt = get_val(emissions_data.get("scope2_market"))
        scope2_mkt_n1 = get_val(emissions_data.get("scope2_market_n1"))
        
        scope3 = get_val(emissions_data.get("scope3"))
        scope3_n1 = get_val(emissions_data.get("scope3_n1"))
        
        # Calcola totali
        total_n = "—"
        total_n1 = "—"
        
        try:
            s1 = float(scope1) if scope1 != "—" else 0
            s2l = float(scope2_loc) if scope2_loc != "—" else 0
            s3 = float(scope3) if scope3 != "—" else 0
            total_n = s1 + s2l + s3
        except (TypeError, ValueError):
            pass
        
        try:
            s1_n1 = float(scope1_n1) if scope1_n1 != "—" else 0
            s2l_n1 = float(scope2_loc_n1) if scope2_loc_n1 != "—" else 0
            s3_n1 = float(scope3_n1) if scope3_n1 != "—" else 0
            total_n1 = s1_n1 + s2l_n1 + s3_n1
        except (TypeError, ValueError):
            pass
        
        # Calcola variazioni
        def calc_change(current, previous):
            try:
                c, p = float(current), float(previous)
                if p > 0:
                    return f"{((c - p) / p * 100):.1f}%"
            except (TypeError, ValueError, ZeroDivisionError):
                pass
            return "—"
        
        # Crea colonne
        columns = [
            TableColumn(header="GHG Emissions", field="label", width="300px"),
            TableColumn(header=year_n1, field="year_n1", format="#,##0.0", alignment="right"),
            TableColumn(header=year_n, field="year_n", format="#,##0.0", alignment="right"),
            TableColumn(header=self._labels["change"], field="change", format="0.0%", alignment="right"),
        ]
        
        # Crea righe
        rows = [
            TableRow(
                label=self._labels["scope1"],
                values={"year_n1": scope1_n1, "year_n": scope1, "change": calc_change(scope1, scope1_n1)},
            ),
            TableRow(
                label=self._labels["scope2_location"],
                values={"year_n1": scope2_loc_n1, "year_n": scope2_loc, "change": calc_change(scope2_loc, scope2_loc_n1)},
            ),
            TableRow(
                label=self._labels["scope2_market"],
                values={"year_n1": scope2_mkt_n1, "year_n": scope2_mkt, "change": calc_change(scope2_mkt, scope2_mkt_n1)},
            ),
            TableRow(
                label=self._labels["scope3"],
                values={"year_n1": scope3_n1, "year_n": scope3, "change": calc_change(scope3, scope3_n1)},
            ),
            TableRow(
                label=self._labels["total"],
                values={
                    "year_n1": total_n1 if total_n1 != "—" else "—",
                    "year_n": total_n if total_n != "—" else "—",
                    "change": calc_change(total_n, total_n1),
                },
                is_total=True,
            ),
        ]
        
        # Dati per grafico (opzionale)
        chart = None
        if include_chart:
            labels = [year_n1, year_n]
            chart = ChartData(
                chart_type="bar",
                labels=labels,
                datasets=[
                    {"label": "Scope 1", "data": [scope1_n1, scope1], "backgroundColor": "#e53e3e"},
                    {"label": "Scope 2 (location)", "data": [scope2_loc_n1, scope2_loc], "backgroundColor": "#3182ce"},
                    {"label": "Scope 3", "data": [scope3_n1, scope3], "backgroundColor": "#38a169"},
                ],
                title="GHG Emissions by Scope",
                y_label="tCO2e",
                unit="tCO2e",
            )
        
        # Scope 3 breakdown per categoria (se disponibile)
        scope3_categories = emissions_data.get("scope3_categories", {})
        if scope3_categories:
            for cat_name, cat_data in scope3_categories.items():
                cat_val_n = get_val(cat_data, "value")
                cat_val_n1 = get_val(cat_data.get("year_n1", {}), "value") if isinstance(cat_data, dict) else "—"
                rows.append(
                    TableRow(
                        label=f"  {cat_name}",
                        values={
                            "year_n1": cat_val_n1,
                            "year_n": cat_val_n,
                            "change": calc_change(cat_val_n, cat_val_n1),
                        },
                        indent=1,
                    )
                )
        
        return ESRSDataTable(
            table_type="ghg",
            table_id=table_id,
            title="GHG Emissions Summary",
            standard_ref="ESRS E1",
            paragraph_ref="54-61",
            description="Gross Scopes 1, 2, 3 and Total GHG emissions (ESRS E1-6)",
            columns=columns,
            rows=rows,
            footnotes=[
                "Scope 1: Direct emissions from owned/controlled sources",
                "Scope 2 location-based: National grid average emission factors",
                "Scope 2 market-based: Supplier-specific emission factors",
                "Scope 3: Value chain emissions calculated using spend-based methodology",
                "Methodology: GHG Protocol Corporate Standard",
            ],
            chart=chart,
            xbrl_ready=True,
            source="emissions_data",
        )
    
    def generate_energy_table(
        self,
        energy_data: Dict[str, Any],
        table_id: str = "energy-consumption",
    ) -> ESRSDataTable:
        """
        Genera tabella Energy Consumption (ESRS E1-5).
        
        Args:
            energy_data: Dati energetici con consumi per fonte
            table_id: ID della tabella
            
        Returns:
            ESRSDataTable con dati energetici
        """
        year = energy_data.get("year", datetime.now().year)
        year_n = str(year)
        year_n1 = str(year - 1)
        
        def get_val(data, key="value", default="—"):
            if isinstance(data, dict):
                return data.get(key, default)
            return data if data is not None else default
        
        columns = [
            TableColumn(header="Energy Source", field="label", width="300px"),
            TableColumn(header=year_n1, field="year_n1", format="#,##0", alignment="right"),
            TableColumn(header=year_n, field="year_n", format="#,##0", alignment="right"),
            TableColumn(header="Unit", field="unit", alignment="center"),
        ]
        
        rows = [
            TableRow(
                label="Total fossil energy consumption",
                values={
                    "year_n1": get_val(energy_data.get("fossil_n1")),
                    "year_n": get_val(energy_data.get("fossil")),
                    "unit": "MWh",
                },
            ),
            TableRow(
                label="  Natural gas",
                values={
                    "year_n1": get_val(energy_data.get("gas_n1")),
                    "year_n": get_val(energy_data.get("gas")),
                    "unit": "MWh",
                },
                indent=1,
            ),
            TableRow(
                label="Nuclear energy consumption",
                values={
                    "year_n1": get_val(energy_data.get("nuclear_n1")),
                    "year_n": get_val(energy_data.get("nuclear")),
                    "unit": "MWh",
                },
            ),
            TableRow(
                label="Renewable energy consumption",
                values={
                    "year_n1": get_val(energy_data.get("renewable_n1")),
                    "year_n": get_val(energy_data.get("renewable")),
                    "unit": "MWh",
                },
            ),
            TableRow(
                label="  Purchased electricity (renewable)",
                values={
                    "year_n1": get_val(energy_data.get("renewable_electricity_n1")),
                    "year_n": get_val(energy_data.get("renewable_electricity")),
                    "unit": "MWh",
                },
                indent=1,
            ),
            TableRow(
                label="Total energy consumption",
                values={
                    "year_n1": get_val(energy_data.get("total_n1")),
                    "year_n": get_val(energy_data.get("total")),
                    "unit": "MWh",
                },
                is_total=True,
            ),
        ]
        
        return ESRSDataTable(
            table_type="energy",
            table_id=table_id,
            title="Energy Consumption and Mix",
            standard_ref="ESRS E1",
            paragraph_ref="46-53",
            description="Energy consumption and mix (ESRS E1-5)",
            columns=columns,
            rows=rows,
            footnotes=["Energy data sourced from utility bills and supplier declarations"],
            xbrl_ready=True,
            source="emissions_data",
        )
    
    def generate_workforce_table(
        self,
        workforce_data: Dict[str, Any],
        table_id: str = "workforce-demographics",
    ) -> ESRSDataTable:
        """
        Genera tabella Workforce Demographics (ESRS S1-6).
        
        Args:
            workforce_data: Dati forza lavoro
            table_id: ID della tabella
            
        Returns:
            ESRSDataTable con dati workforce
        """
        def get_val(data, key="value", default="—"):
            if isinstance(data, dict):
                return data.get(key, default)
            return data if data is not None else default
        
        columns = [
            TableColumn(header="Workforce Category", field="label", width="300px"),
            TableColumn(header="Female", field="female", format="#,##0", alignment="right"),
            TableColumn(header="Male", field="male", format="#,##0", alignment="right"),
            TableColumn(header="Total", field="total", format="#,##0", alignment="right"),
        ]
        
        total_f = get_val(workforce_data.get("female_total"))
        total_m = get_val(workforce_data.get("male_total"))
        total_all = get_val(workforce_data.get("total"))
        
        rows = [
            TableRow(
                label="Total employees",
                values={"female": total_f, "male": total_m, "total": total_all},
                is_total=True,
            ),
        ]
        
        # Breakdown per contratto
        contract_data = workforce_data.get("contract_type", {})
        for contract_type in ["permanent", "temporary", "part_time"]:
            ct = contract_data.get(contract_type, {})
            if ct:
                rows.append(
                    TableRow(
                        label=f"  {contract_type.replace('_', ' ').title()}",
                        values={
                            "female": get_val(ct.get("female")),
                            "male": get_val(ct.get("male")),
                            "total": get_val(ct),
                        },
                        indent=1,
                    )
                )
        
        return ESRSDataTable(
            table_type="workforce",
            table_id=table_id,
            title="Workforce Demographics",
            standard_ref="ESRS S1",
            paragraph_ref="45-55",
            description="Characteristics of the undertaking's employees (ESRS S1-6)",
            columns=columns,
            rows=rows,
            footnotes=["Data as of reporting year-end"],
            xbrl_ready=True,
            source="hr_data",
        )
    
    def generate_comparative_table(
        self,
        data: Dict[str, Any],
        metric_name: str,
        years: List[int],
        table_id: str = "comparative",
    ) -> ESRSDataTable:
        """
        Genera tabella comparativa multi-anno.
        
        Args:
            data: Dati per anno. Dict { "label1": {year: value, ...}, ... }
            metric_name: Nome della metrica
            years: Lista di anni da includere
            table_id: ID della tabella
            
        Returns:
            ESRSDataTable comparativa
        """
        columns = [
            TableColumn(header="Metric", field="label", width="300px"),
        ]
        for y in sorted(years, reverse=True):
            columns.append(
                TableColumn(
                    header=str(y),
                    field=f"year_{y}",
                    format="#,##0.0",
                    alignment="right",
                )
            )
        
        rows = []
        for label, values in data.items():
            row_values = {}
            for y in years:
                row_values[f"year_{y}"] = values.get(y, "—")
            rows.append(TableRow(label=label, values=row_values))
        
        return ESRSDataTable(
            table_type="comparative",
            table_id=table_id,
            title=f"{metric_name} — Multi-year Comparison",
            standard_ref="ESRS E1",
            paragraph_ref="",
            description=f"Comparativa {metric_name}",
            columns=columns,
            rows=rows,
            xbrl_ready=True,
        )
    
    def generate_breakdown_table(
        self,
        data: Dict[str, Any],
        dimension: str,
        metric_name: str,
        table_id: str = "breakdown",
    ) -> ESRSDataTable:
        """
        Genera tabella di breakdown per paese/settore/subsidiary.
        
        Args:
            data: Dict { "segmento": value, ... }
            dimension: Dimensione di breakdown (country, sector, subsidiary)
            metric_name: Nome della metrica
            table_id: ID della tabella
            
        Returns:
            ESRSDataTable con breakdown
        """
        columns = [
            TableColumn(
                header=dimension.replace("_", " ").title(),
                field="label",
                width="300px",
            ),
            TableColumn(
                header=f"{metric_name} ({self._labels['year_n']})",
                field="value",
                format="#,##0.0",
                alignment="right",
            ),
            TableColumn(
                header="Share (%)",
                field="share",
                format="0.0%",
                alignment="right",
            ),
        ]
        
        total = sum(v for v in data.values() if isinstance(v, (int, float)))
        
        rows = []
        for segment, value in data.items():
            share = f"{(value / total * 100):.1f}%" if total > 0 else "—"
            rows.append(
                TableRow(
                    label=segment,
                    values={"value": value, "share": share},
                )
            )
        
        rows.append(
            TableRow(
                label="Total",
                values={"value": total, "share": "100%"},
                is_total=True,
            )
        )
        
        return ESRSDataTable(
            table_type="breakdown",
            table_id=table_id,
            title=f"{metric_name} by {dimension.replace('_', ' ').title()}",
            standard_ref="ESRS E1",
            paragraph_ref="",
            columns=columns,
            rows=rows,
            xbrl_ready=True,
        )
    
    def generate_custom_table(
        self,
        title: str,
        headers: List[str],
        rows_data: List[List[Any]],
        standard_ref: str = "",
        paragraph_ref: str = "",
        table_id: str = "custom",
    ) -> ESRSDataTable:
        """
        Genera una tabella personalizzata da dati arbitrari.
        
        Args:
            title: Titolo della tabella
            headers: Intestazioni colonne
            rows_data: Dati righe (lista di liste)
            standard_ref: Riferimento ESRS (opzionale)
            paragraph_ref: Riferimento paragrafo (opzionale)
            table_id: ID della tabella
            
        Returns:
            ESRSDataTable custom
        """
        columns = [
            TableColumn(header=h, field=f"col_{i}", alignment="right" if i > 0 else "left")
            for i, h in enumerate(headers)
        ]
        
        rows = []
        for row_data in rows_data:
            label = str(row_data[0]) if row_data else ""
            values = {f"col_{i}": v for i, v in enumerate(row_data)}
            rows.append(TableRow(label=label, values=values))
        
        return ESRSDataTable(
            table_type="custom",
            table_id=table_id,
            title=title,
            standard_ref=standard_ref,
            paragraph_ref=paragraph_ref,
            columns=columns,
            rows=rows,
            xbrl_ready=True,
        )
    
    # ── HTML Rendering ───────────────────────────────────────────
    
    def render_table_html(
        self,
        table: ESRSDataTable,
        include_xbrl_attrs: bool = False,
    ) -> str:
        """
        Renderizza una tabella ESRS in HTML.
        
        Args:
            table: ESRSDataTable da renderizzare
            include_xbrl_attrs: Se includere attributi per iXBRL
            
        Returns:
            HTML della tabella
        """
        html_parts = []
        
        # Intestazione tabella
        html_parts.append(f'<table class="esrs-table" id="{table.table_id}">')
        
        # Colonna headers
        html_parts.append('<thead><tr>')
        for col in table.columns:
            align = col.alignment if col.alignment != "left" else ""
            style = f' style="text-align: {align}; width: {col.width};"' if col.width or align else ""
            html_parts.append(f'<th{style}>{col.header}</th>')
        html_parts.append('</tr></thead>')
        
        # Corpo tabella
        html_parts.append('<tbody>')
        for row in table.rows:
            row_class = ""
            if row.is_total:
                row_class = ' class="row-total"'
            elif row.is_header:
                row_class = ' class="row-header"'
            
            html_parts.append(f'<tr{row_class}>')
            
            # Label cell
            label_style = f' style="padding-left: {row.indent * 16 + 12}px;"' if row.indent > 0 else ""
            html_parts.append(f'<td{label_style}>{row.label}</td>')
            
            # Value cells
            for col in table.columns[1:]:  # Skip label column
                field = col.field
                value = row.values.get(field, "—")
                align = f' class="align-{col.alignment}"' if col.alignment != "left" else ""
                
                # Formatta valore
                if isinstance(value, (int, float)):
                    if col.format == "#,##0.0":
                        value_str = f"{value:,.1f}"
                    elif col.format == "#,##0":
                        value_str = f"{value:,.0f}"
                    elif col.format == "0.0%":
                        value_str = f"{value}"
                    else:
                        value_str = str(value)
                else:
                    value_str = str(value)
                
                # Attributi iXBRL (opzionale)
                xbrl_attrs = ""
                if include_xbrl_attrs:
                    concept = f"esrs:{table.standard_ref.replace(' ', '_')}_{field}"
                    xbrl_attrs = (
                        f' data-ixbrl-concept="{concept}"'
                        f' data-ixbrl-unit="tCO2eq"'
                        f' data-ixbrl-period="current"'
                        f' data-ixbrl-scale="0"'
                        f' data-ixbrl-decimals="INF"'
                    )
                
                html_parts.append(
                    f'<td{align}{xbrl_attrs}>{value_str}</td>'
                )
            
            html_parts.append('</tr>')
        html_parts.append('</tbody>')
        html_parts.append('</table>')
        
        # Descrizione
        if table.description:
            html_parts.append(
                f'<p class="esrs-table-caption">{table.description}</p>'
            )
        
        # Footnotes
        if table.footnotes:
            html_parts.append('<div class="esrs-table-footnotes">')
            for note in table.footnotes:
                html_parts.append(f'<p class="esrs-table-caption">* {note}</p>')
            html_parts.append('</div>')
        
        # Dati grafico come JSON (per frontend)
        if table.chart:
            chart_json = json.dumps({
                "chart_type": table.chart.chart_type,
                "labels": table.chart.labels,
                "datasets": table.chart.datasets,
                "title": table.chart.title,
                "x_label": table.chart.x_label,
                "y_label": table.chart.y_label,
                "unit": table.chart.unit,
            }, ensure_ascii=False)
            html_parts.append(
                f'<script type="application/json" class="chart-data">'
                f'{chart_json}</script>'
            )
        
        return "\n".join(html_parts)
    
    def render_table_css(self) -> str:
        """Restituisce il CSS per le tabelle ESRS."""
        return self.TABLE_CSS
    
    def table_to_dict(self, table: ESRSDataTable) -> Dict[str, Any]:
        """Converte una tabella in dizionario per API JSON."""
        return {
            "table_type": table.table_type,
            "table_id": table.table_id,
            "title": table.title,
            "standard_ref": table.standard_ref,
            "paragraph_ref": table.paragraph_ref,
            "description": table.description,
            "columns": [
                {
                    "header": c.header,
                    "field": c.field,
                    "unit": c.unit,
                    "format": c.format,
                    "alignment": c.alignment,
                }
                for c in table.columns
            ],
            "rows": [
                {
                    "label": r.label,
                    "values": r.values,
                    "is_total": r.is_total,
                    "indent": r.indent,
                }
                for r in table.rows
            ],
            "footnotes": table.footnotes,
            "chart": {
                "chart_type": table.chart.chart_type,
                "labels": table.chart.labels,
                "datasets": table.chart.datasets,
                "title": table.chart.title,
            } if table.chart else None,
            "source": table.source,
        }
    
    def render_all_tables(
        self,
        data: Dict[str, Any],
        table_types: Optional[List[TableType]] = None,
    ) -> Dict[str, str]:
        """
        Renderizza tutte le tabelle richieste in HTML.
        
        Args:
            data: Dataset completo (emissions, workforce, energy)
            table_types: Tipi di tabella da generare. None = tutti.
            
        Returns:
            Dict { table_id: HTML }
        """
        if table_types is None:
            table_types = ["ghg", "energy", "workforce"]
        
        result = {}
        
        if "ghg" in table_types and "emissions" in data:
            ghg_table = self.generate_ghg_table(
                data["emissions"], include_chart=True
            )
            result[ghg_table.table_id] = self.render_table_html(ghg_table)
        
        if "energy" in table_types and "energy" in data:
            energy_table = self.generate_energy_table(data["energy"])
            result[energy_table.table_id] = self.render_table_html(energy_table)
        
        if "workforce" in table_types and "workforce" in data:
            workforce_table = self.generate_workforce_table(data["workforce"])
            result[workforce_table.table_id] = self.render_table_html(workforce_table)
        
        return result


# ── Helper Functions ──────────────────────────────────────────────

def generate_report_tables_api(
    company_data: Dict[str, Any],
    table_types: Optional[List[TableType]] = None,
    language: str = "en",
) -> Dict[str, Any]:
    """
    Helper per endpoint API: genera tutte le tabelle per un report.
    
    Args:
        company_data: Dati aziendali completi
        table_types: Tipi di tabella da generare
        language: Lingua delle tabelle
        
    Returns:
        Dict con tabelle renderizzate e dati strutturati
    """
    generator = TableGenerator(language=language)
    
    tables_html = generator.render_all_tables(company_data, table_types)
    
    # Versione strutturata (dict) per elaborazione backend
    tables_data = {}
    if "emissions" in company_data:
        ghg_table = generator.generate_ghg_table(company_data["emissions"])
        tables_data["ghg"] = generator.table_to_dict(ghg_table)
    
    return {
        "tables_html": tables_html,
        "tables_data": tables_data,
        "css": generator.render_table_css(),
    }


def update_template_with_tables(
    template: Any,
    company_data: Dict[str, Any],
    language: str = "en",
) -> Any:
    """
    Aggiorna un ReportTemplate con le tabelle generate.
    
    Cerca i ContentBlock di tipo "table" con placeholder e li popola
    con i dati reali.
    
    Args:
        template: ReportTemplate da aggiornare
        company_data: Dati aziendali
        language: Lingua
        
    Returns:
        ReportTemplate aggiornato
    """
    generator = TableGenerator(language=language)
    updated_count = 0
    
    for section in template.sections:
        for dr in section.disclosure_requirements:
            for block in dr.blocks:
                if block.content_type != "table":
                    continue
                
                # Determina tipo tabella dal block_id
                if "ghg" in block.block_id or "e1-6" in block.block_id:
                    if "emissions" in company_data:
                        ghg_table = generator.generate_ghg_table(
                            company_data["emissions"],
                            table_id=block.block_id,
                        )
                        block.content_html = generator.render_table_html(ghg_table)
                        updated_count += 1
                
                elif "energy" in block.block_id or "e1-5" in block.block_id:
                    if "energy" in company_data:
                        energy_table = generator.generate_energy_table(
                            company_data["energy"],
                            table_id=block.block_id,
                        )
                        block.content_html = generator.render_table_html(energy_table)
                        updated_count += 1
    
    logger.info(f"Updated {updated_count} table blocks in template")
    return template
