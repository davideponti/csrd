"""
CSRD Comply — iXBRL Tagging Engine (Step 20)

Implementa il tagging iXBRL conforme alla tassonomia ESRS.
iXBRL = Inline XBRL = XHTML + tag XML embedded.

Ogni datapoint nel report deve essere "taggato" con l'elemento
XBRL corrispondente dalla tassonomia ESRS.

Architettura:
1. Prende il report XHTML generato dal TemplateEngine
2. Identifica i valori numerici e testuali da taggare
3. Applica i tag iXBRL corretti (<ix:nonFraction>, <ix:nonNumeric>, ecc.)
4. Genera il documento iXBRL finale pronto per validazione

Integration:
    POST /api/v1/reports/generate-ixbrl
    Input: report_id
    Output: file .xhtml con tagging iXBRL completo
"""

import re
import json
import logging
from typing import Optional, Dict, Any, List, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from lxml import etree
from copy import deepcopy

logger = logging.getLogger(__name__)


# ── Namespaces iXBRL / XBRL ──────────────────────────────────────

NSMAP = {
    "ix": "http://www.xbrl.org/2013/inlineXBRL",
    "ixt": "http://www.xbrl.org/inlineXBRL/transformation/2015-07-21",
    "xlink": "http://www.w3.org/1999/xlink",
    "xbrli": "http://www.xbrl.org/2003/instance",
    "link": "http://www.xbrl.org/2003/linkbase",
    "xsd": "http://www.w3.org/2001/XMLSchema",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

# URI base della tassonomia ESRS
ESRS_TAXONOMY_BASE = "https://xbrl.efrag.org/esrs-set1-2023"


# ── Mapping Datapoint → XBRL Concept ─────────────────────────────

# Mapping dei principali datapoint ESRS ai concetti XBRL.
# In produzione, caricato dalla tassonomia .xsd/.xml
ESRS_DATAPOINT_MAP: Dict[str, Dict[str, Any]] = {
    # ESRS 2 — General
    "ESRS 2.BP-1": {"concept": "esrs:GeneralBasisOfPreparation", "type": "nonNumeric"},
    "ESRS 2.GOV-1": {"concept": "esrs:GovernanceBodyRole", "type": "nonNumeric"},
    "ESRS 2.SBM-1": {"concept": "esrs:StrategyBusinessModel", "type": "nonNumeric"},
    "ESRS 2.IRO-1": {"concept": "esrs:IROIdentificationProcess", "type": "nonNumeric"},
    # ESRS E1 — Climate
    "ESRS E1-6.Scope1": {"concept": "esrs:GHGScope1Emissions", "type": "nonFraction", "unit": "tCO2eq"},
    "ESRS E1-6.Scope2Location": {"concept": "esrs:GHGScope2LocationEmissions", "type": "nonFraction", "unit": "tCO2eq"},
    "ESRS E1-6.Scope2Market": {"concept": "esrs:GHGScope2MarketEmissions", "type": "nonFraction", "unit": "tCO2eq"},
    "ESRS E1-6.Scope3": {"concept": "esrs:GHGScope3Emissions", "type": "nonFraction", "unit": "tCO2eq"},
    "ESRS E1-6.Total": {"concept": "esrs:GHGTotalEmissions", "type": "nonFraction", "unit": "tCO2eq"},
    # ESRS E1-5 — Energy
    "ESRS E1-5.Fossil": {"concept": "esrs:EnergyFossilConsumption", "type": "nonFraction", "unit": "MWh"},
    "ESRS E1-5.Nuclear": {"concept": "esrs:EnergyNuclearConsumption", "type": "nonFraction", "unit": "MWh"},
    "ESRS E1-5.Renewable": {"concept": "esrs:EnergyRenewableConsumption", "type": "nonFraction", "unit": "MWh"},
    "ESRS E1-5.Total": {"concept": "esrs:EnergyTotalConsumption", "type": "nonFraction", "unit": "MWh"},
    # ESRS S1 — Own Workforce
    "ESRS S1-6.TotalEmployees": {"concept": "esrs:TotalEmployees", "type": "nonFraction", "unit": "employees"},
    "ESRS S1-6.FemaleEmployees": {"concept": "esrs:FemaleEmployees", "type": "nonFraction", "unit": "employees"},
    "ESRS S1-6.MaleEmployees": {"concept": "esrs:MaleEmployees", "type": "nonFraction", "unit": "employees"},
}


# ── Data Classes ──────────────────────────────────────────────────

@dataclass
class XBRLContext:
    """
    Contesto XBRL per un fatto (periodo + entity + scenario).

    Attributes:
        context_id: ID univoco del contesto (es. "c_2026")
        entity_identifier: Identificatore dell'entità (es. LEI o VAT)
        entity_scheme: Schema dell'identificatore (es. "http://www.company.com/id")
        period_start: Inizio periodo (ISO 8601)
        period_end: Fine periodo (ISO 8601)
        instant: Data puntuale (es. per stock measures)
        scenario: Scenario opzionale (es. "actual", "projected")
    """
    context_id: str
    entity_identifier: str = ""
    entity_scheme: str = "http://www.company.com/id"
    period_start: str = ""
    period_end: str = ""
    instant: str = ""
    scenario: str = "actual"

    def to_xml(self) -> str:
        """Genera il tag XML <xbrli:context>."""
        entity = (
            f'<xbrli:entity>'
            f'<xbrli:identifier scheme="{self.entity_scheme}">'
            f'{self.entity_identifier}</xbrli:identifier>'
            f'</xbrli:entity>'
        )
        if self.instant:
            period = f'<xbrli:period><xbrli:instant>{self.instant}</xbrli:instant></xbrli:period>'
        else:
            period = (
                f'<xbrli:period>'
                f'<xbrli:startDate>{self.period_start}</xbrli:startDate>'
                f'<xbrli:endDate>{self.period_end}</xbrli:endDate>'
                f'</xbrli:period>'
            )
        scenario_xml = ""
        if self.scenario and self.scenario != "actual":
            scenario_xml = f'<xbrli:scenario><xbrli:scenarioDescription>{self.scenario}</xbrli:scenarioDescription></xbrli:scenario>'
        return (
            f'<xbrli:context id="{self.context_id}">'
            f'{entity}{period}{scenario_xml}'
            f'</xbrli:context>'
        )


@dataclass
class XBRLUnit:
    """
    Unit di misura XBRL.

    Attributes:
        unit_id: ID dell'unità (es. "u_tCO2eq")
        numerator: Numeratore (es. "tCO2eq")
        denominator: Denominatore (opzionale, es. "employees")
    """
    unit_id: str
    numerator: str
    denominator: Optional[str] = None

    def to_xml(self) -> str:
        """Genera il tag XML <xbrli:unit>."""
        measure = (
            f'<xbrli:measure>{self.numerator}</xbrli:measure>'
            if not self.denominator
            else f'<xbrli:divide><xbrli:unitNumerator><xbrli:measure>{self.numerator}</xbrli:measure></xbrli:unitNumerator>'
                 f'<xbrli:unitDenominator><xbrli:measure>{self.denominator}</xbrli:measure></xbrli:unitDenominator></xbrli:divide>'
        )
        return f'<xbrli:unit id="{self.unit_id}">{measure}</xbrli:unit>'


@dataclass
class XBRLFact:
    """
    Fatto XBRL da inserire nel report.

    Attributes:
        concept: Nome del concetto XBRL (es. "esrs:GHGScope1Emissions")
        value: Valore del fatto
        unit_ref: Riferimento all'unità di misura
        context_ref: Riferimento al contesto
        decimals: Numero di decimali (INF = intero)
        scale: Scala (0 = unità, 3 = migliaia, 6 = milioni)
        format_attr: Formato opzionale per ix:nonFraction
        precision: Precisione opzionale
        is_numeric: Se è un fatto numerico (nonFraction) o testuale (nonNumeric)
        footnotes: Eventuali note a piè di colore
    """
    concept: str
    value: Any
    unit_ref: str = "u_tCO2eq"
    context_ref: str = "c_current"
    decimals: str = "INF"
    scale: int = 0
    format_attr: Optional[str] = None
    precision: Optional[str] = None
    is_numeric: bool = True
    footnotes: List[str] = field(default_factory=list)

    def to_ixbrl_tag(self) -> str:
        """
        Genera il tag iXBRL per questo fatto.

        Returns:
            Tag iXBRL come stringa (es. <ix:nonFraction ...>valore</ix:nonFraction>)
        """
        if self.is_numeric:
            # Formatta il valore numerico
            if isinstance(self.value, float):
                formatted = f"{self.value:.2f}"
            else:
                formatted = str(self.value)

            # Attributi opzionali
            fmt_attr = f' format="{self.format_attr}"' if self.format_attr else ""
            prec_attr = f' precision="{self.precision}"' if self.precision else ""

            return (
                f'<ix:nonFraction'
                f' name="{self.concept}"'
                f' unitRef="{self.unit_ref}"'
                f' contextRef="{self.context_ref}"'
                f' scale="{self.scale}"'
                f' decimals="{self.decimals}"'
                f'{fmt_attr}{prec_attr}>'
                f'{formatted}'
                f'</ix:nonFraction>'
            )
        else:
            # Testo narrativo (nonNumeric)
            escaped_value = str(self.value).replace("&", "&").replace("<", "<").replace(">", ">")
            return (
                f'<ix:nonNumeric'
                f' name="{self.concept}"'
                f' contextRef="{self.context_ref}"'
                f'>'
                f'{escaped_value}'
                f'</ix:nonNumeric>'
            )


# ── ESRS Taxonomy Loader ──────────────────────────────────────────

class ESRSXBRLTaxonomy:
    """
    Carica e gestisce la tassonomia XBRL ESRS.

    In produzione, carica i file .xsd + .xml dalla tassonomia ufficiale EFRAG.
    In sviluppo/mock, usa un mapping predefinito.

    Attributes:
        taxonomy_path: Percorso alla tassonomia XBRL ESRS
        concepts: Dict dei concetti caricati
        loaded: Se la tassonomia è stata caricata
    """

    def __init__(self, taxonomy_path: Optional[str] = None):
        """
        Args:
            taxonomy_path: Percorso al file .xsd della tassonomia ESRS
        """
        self.taxonomy_path = taxonomy_path
        self.concepts: Dict[str, Dict[str, Any]] = {}
        self.units: Dict[str, XBRLUnit] = {}
        self.loaded = False

    def load(self) -> bool:
        """
        Carica la tassonomia XBRL ESRS.

        Prova a caricare da file .xsd. Se non disponibile, usa mapping predefinito.

        Returns:
            True se caricata con successo
        """
        if self.taxonomy_path:
            try:
                self._load_from_xsd(self.taxonomy_path)
                self.loaded = True
                logger.info(f"Loaded ESRS taxonomy from {self.taxonomy_path}")
                return True
            except Exception as e:
                logger.warning(f"Cannot load taxonomy from {self.taxonomy_path}: {e}")

        # Fallback: usa mapping predefinito
        self._load_default_mapping()
        self.loaded = True
        logger.info("Loaded ESRS taxonomy from default mapping")
        return True

    def _load_from_xsd(self, path: str) -> None:
        """
        Carica concetti da file .xsd della tassonomia ESRS.
        Usa lxml per parsare lo schema XSD.

        Args:
            path: Percorso al file .xsd
        """
        tree = etree.parse(path)
        root = tree.getroot()
        ns = {"xsd": "http://www.w3.org/2001/XMLSchema"}

        for elem in root.iter(f"{{{ns['xsd']}}}element"):
            name = elem.get("name")
            if name and name.startswith("esrs:"):
                concept_type = elem.get("type", "")
                substitution = elem.get("substitutionGroup", "")
                self.concepts[name] = {
                    "name": name,
                    "type": concept_type,
                    "substitutionGroup": substitution,
                    "periodType": elem.get("periodType", "duration"),
                    "nillable": elem.get("nillable", "true") == "true",
                }

        logger.info(f"Loaded {len(self.concepts)} concepts from XSD taxonomy")

    def _load_default_mapping(self) -> None:
        """Carica il mapping predefinito dei datapoint ESRS."""
        for ref, mapping in ESRS_DATAPOINT_MAP.items():
            concept_name = mapping["concept"]
            self.concepts[concept_name] = {
                "name": concept_name,
                "datapoint_ref": ref,
                "type": mapping["type"],
                "unit": mapping.get("unit", ""),
                "periodType": "duration",
                "nillable": True,
            }

        # Unit predefinite
        self.units = {
            "u_tCO2eq": XBRLUnit(unit_id="u_tCO2eq", numerator="tCO2eq"),
            "u_MWh": XBRLUnit(unit_id="u_MWh", numerator="MWh"),
            "u_employees": XBRLUnit(unit_id="u_employees", numerator="employees"),
            "u_EUR": XBRLUnit(unit_id="u_EUR", numerator="EUR"),
            "u_percentage": XBRLUnit(unit_id="u_percentage", numerator="percentage"),
            "u_kg": XBRLUnit(unit_id="u_kg", numerator="kg"),
            "u_m3": XBRLUnit(unit_id="u_m3", numerator="m3"),
        }

    def get_concept(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """
        Restituisce un concetto dalla tassonomia.

        Args:
            concept_name: Nome del concetto (es. "esrs:GHGScope1Emissions")

        Returns:
            Dict con dettagli del concetto o None
        """
        return self.concepts.get(concept_name)

    def get_unit(self, unit_id: str) -> Optional[XBRLUnit]:
        """
        Restituisce un'unità di misura.

        Args:
            unit_id: ID dell'unità

        Returns:
            XBRLUnit o None
        """
        return self.units.get(unit_id)

    def map_datapoint(self, datapoint_ref: str) -> Optional[Dict[str, Any]]:
        """
        Mappa un riferimento datapoint ESRS a un concetto XBRL.

        Args:
            datapoint_ref: Riferimento ESRS (es. "ESRS E1-6.Scope1")

        Returns:
            Dict con concept, type, unit, ecc. o None
        """
        mapping = ESRS_DATAPOINT_MAP.get(datapoint_ref)
        if mapping:
            concept = self.concepts.get(mapping["concept"])
            if concept:
                return {**mapping, **concept}
        return None

    def get_all_concepts(self) -> Dict[str, Dict[str, Any]]:
        """Restituisce tutti i concetti caricati."""
        return self.concepts

    def get_all_units(self) -> Dict[str, XBRLUnit]:
        """Restituisce tutte le unità caricate."""
        return self.units


# ── iXBRL Tagger ──────────────────────────────────────────────────

class iXBRLError(Exception):
    """Errore nel tagging iXBRL."""
    pass


class IXBRLTaggerConfig:
    """
    Configurazione del tagger iXBRL.

    Attributes:
        taxonomy: Tassonomia ESRS XBRL da utilizzare
        entity_identifier: Identificatore dell'entità (LEI/VAT)
        entity_scheme: Schema dell'identificatore
        reporting_year: Anno di rendicontazione
        language: Lingua del report
        include_footnotes: Se includere note a piè di pagina come fatti
        validate_before_output: Se validare il documento prima dell'output
    """
    def __init__(
        self,
        taxonomy: Optional[ESRSXBRLTaxonomy] = None,
        entity_identifier: str = "",
        entity_scheme: str = "http://www.company.com/id",
        reporting_year: int = 2026,
        language: str = "en",
        include_footnotes: bool = True,
        validate_before_output: bool = False,
    ):
        self.taxonomy = taxonomy or ESRSXBRLTaxonomy()
        self.entity_identifier = entity_identifier
        self.entity_scheme = entity_scheme
        self.reporting_year = reporting_year
        self.language = language
        self.include_footnotes = include_footnotes
        self.validate_before_output = validate_before_output


class IXBRLTagger:
    """
    Motore di tagging iXBRL per report CSRD.

    Prende un report XHTML dal TemplateEngine e applica i tag iXBRL
    conformi alla tassonomia ESRS. Supporta:

    - Tagging automatico di valori numerici (<ix:nonFraction>)
    - Tagging di blocchi narrativi (<ix:nonNumeric>)
    - Generazione header iXBRL con context/unit
    - Mapping datapoint → concetto XBRL via tassonomia ESRS
    - Supporto multi-unità e multi-periodo

    Usage:
        tagger = IXBRLTagger(config)
        tagger.load_taxonomy()

        xbrl_facts = [
            XBRLFact(concept="esrs:GHGScope1Emissions", value=105.0, ...),
        ]
        ixbrl_html = tagger.tag_report(xhtml_content, xbrl_facts)
    """

    def __init__(self, config: Optional[IXBRLTaggerConfig] = None):
        """
        Inizializza il tagger iXBRL.

        Args:
            config: Configurazione del tagger
        """
        self.config = config or IXBRLTaggerConfig()
        self.taxonomy = self.config.taxonomy
        self.contexts: Dict[str, XBRLContext] = {}
        self.units: Dict[str, XBRLUnit] = {}
        self.load_taxonomy()

    def load_taxonomy(self) -> bool:
        """
        Carica la tassonomia ESRS XBRL.

        Returns:
            True se caricata con successo
        """
        return self.taxonomy.load()

    def _create_contexts(self) -> None:
        """Crea i contesti XBRL per il report."""
        year = self.config.reporting_year
        entity_id = self.config.entity_identifier or f"company_{year}"

        # Contesto per l'anno corrente (duration)
        self.contexts["c_current"] = XBRLContext(
            context_id="c_current",
            entity_identifier=entity_id,
            entity_scheme=self.config.entity_scheme,
            period_start=f"{year}-01-01",
            period_end=f"{year}-12-31",
            scenario="actual",
        )

        # Contesto per l'anno precedente
        self.contexts["c_previous"] = XBRLContext(
            context_id="c_previous",
            entity_identifier=entity_id,
            entity_scheme=self.config.entity_scheme,
            period_start=f"{year - 1}-01-01",
            period_end=f"{year - 1}-12-31",
            scenario="actual",
        )

        # Contesto instantaneo (es. per workforce count a fine anno)
        self.contexts["c_instant"] = XBRLContext(
            context_id="c_instant",
            entity_identifier=entity_id,
            entity_scheme=self.config.entity_scheme,
            instant=f"{year}-12-31",
        )

    def _create_default_units(self) -> None:
        """Crea le unità di misura predefinite."""
        self.units = {
            "u_tCO2eq": XBRLUnit(unit_id="u_tCO2eq", numerator="tCO2eq"),
            "u_MWh": XBRLUnit(unit_id="u_MWh", numerator="MWh"),
            "u_employees": XBRLUnit(unit_id="u_employees", numerator="employees"),
            "u_EUR": XBRLUnit(unit_id="u_EUR", numerator="EUR"),
            "u_percentage": XBRLUnit(unit_id="u_percentage", numerator="percentage"),
            "u_kg": XBRLUnit(unit_id="u_kg", numerator="kg"),
        }

    def _build_ixbrl_header(self) -> str:
        """
        Costruisce l'header iXBRL con context e unit.

        Returns:
            Blocco XML con header iXBRL
        """
        parts = ['<ix:header>', '<ix:references>', '</ix:references>']

        # Contexts
        parts.append('<ix:resources>')
        for ctx in self.contexts.values():
            parts.append(ctx.to_xml())

        # Units
        for unit in self.units.values():
            parts.append(unit.to_xml())

        parts.append('</ix:resources>')
        parts.append('</ix:header>')

        return '\n'.join(parts)

    def _inject_ixbrl_namespaces(self, html: str) -> str:
        """
        Inietta i namespace iXBRL nel tag <html>.

        Args:
            html: Documento XHTML

        Returns:
            XHTML con namespace iXBRL
        """
        ns_attrs = ' '.join(
            f'xmlns:{prefix}="{uri}"'
            for prefix, uri in NSMAP.items()
        )
        # Aggiungi anche il reference allo schema ESRS
        ns_attrs += f' xmlns:esrs="{ESRS_TAXONOMY_BASE}"'

        # Inject nel tag <html>
        html = re.sub(
            r'<html\b',
            f'<html {ns_attrs}',
            html,
            count=1,
        )
        return html

    def _inject_link_schema(self, html: str) -> str:
        """
        Inietta il link alla tassonomia ESRS nel <head>.

        Args:
            html: Documento XHTML

        Returns:
            XHTML con link allo schema
        """
        schema_link = (
            f'<link rel="schema.esrs" href="{ESRS_TAXONOMY_BASE}"/>'
        )
        html = re.sub(
            r'</head>',
            f'    {schema_link}\n</head>',
            html,
            count=1,
        )
        return html

    def _tag_numeric_value(
        self,
        html_fragment: str,
        fact: XBRLFact,
    ) -> str:
        """
        Sostituisce un valore numerico nel frammento HTML con il tag iXBRL.

        Cerca il valore nel testo e lo avvolge con <ix:nonFraction>.

        Args:
            html_fragment: Frammento HTML contenente il valore
            fact: Fatto XBRL da applicare

        Returns:
            Frammento con tag iXBRL
        """
        value_str = str(fact.value)
        if isinstance(fact.value, float):
            value_str = f"{fact.value:.2f}"

        ix_tag = fact.to_ixbrl_tag()

        # Cerca e sostituisci il valore nel frammento
        # Cerchiamo il valore esatto con boundaries di parola
        pattern = re.escape(value_str)
        replacement = ix_tag

        # Se il valore è un numero semplice, cerchiamo con boundaries
        if re.match(r'^\d+[,.]?\d*$', value_str):
            pattern = r'\b' + re.escape(value_str) + r'\b'

        return re.sub(pattern, replacement, html_fragment, count=1)

    def _tag_narrative_block(
        self,
        html_fragment: str,
        fact: XBRLFact,
    ) -> str:
        """
        Avvolge un blocco narrativo con tag <ix:nonNumeric>.

        Invece di sostituire un valore, aggiunge il tag all'inizio
        del blocco identificato dall'ID.

        Args:
            html_fragment: Frammento HTML
            fact: Fatto XBRL non numerico

        Returns:
            Frammento con tag iXBRL
        """
        ix_tag = fact.to_ixbrl_tag()

        # Aggiunge il tag iXBRL prima del contenuto del blocco
        # (l'output dovrà essere processato dal template engine)
        return f'{ix_tag}\n{html_fragment}'

    def tag_report(
        self,
        xhtml_content: str,
        xbrl_facts: List[XBRLFact],
    ) -> str:
        """
        Applica il tagging iXBRL a un documento XHTML.

        Args:
            xhtml_content: Contenuto XHTML del report
            xbrl_facts: Lista di fatti XBRL da taggare

        Returns:
            Documento XHTML con tagging iXBRL (formato .xhtml)

        Raises:
            iXBRLError: Se il tagging fallisce
        """
        if not xhtml_content.strip():
            raise iXBRLError("Empty XHTML content provided")

        # Crea contesti e unità
        self._create_contexts()
        self._create_default_units()

        # Inietta namespace e link alla tassonomia
        result = self._inject_ixbrl_namespaces(xhtml_content)
        result = self._inject_link_schema(result)

        # Inietta header iXBRL dopo il <body>
        ixbrl_header = self._build_ixbrl_header()

        # Inserisci header iXBRL dopo l'apertura del body
        result = result.replace('<body>', f'<body>\n{ixbrl_header}', 1)

        # Applica tagging per ogni fatto
        tagged_count = 0
        for fact in xbrl_facts:
            try:
                if fact.is_numeric:
                    result = self._tag_numeric_value(result, fact)
                else:
                    result = self._tag_narrative_block(result, fact)
                tagged_count += 1
            except Exception as e:
                logger.warning(
                    f"Failed to tag fact {fact.concept} = {fact.value}: {e}"
                )

        logger.info(
            f"Tagged {tagged_count}/{len(xbrl_facts)} facts with iXBRL"
        )
        return result

    def tag_report_from_template(
        self,
        template: Any,
        company_data: Dict[str, Any],
    ) -> str:
        """
        Metodo completo: prende un ReportTemplate e genera iXBRL.

        1. Renderizza il template in XHTML
        2. Crea i fatti XBRL dai dati aziendali
        3. Applica il tagging iXBRL

        Args:
            template: ReportTemplate da processare
            company_data: Dati aziendali strutturati (emissions, workforce, ecc.)

        Returns:
            Documento XHTML con tagging iXBRL completo
        """
        # Render XHTML base
        xhtml = template.render_to_xhtml()

        # Crea fatti XBRL dai dati aziendali
        facts = self._create_facts_from_company_data(company_data)

        # Applica tagging
        return self.tag_report(xhtml, facts)

    def _create_facts_from_company_data(
        self,
        company_data: Dict[str, Any],
    ) -> List[XBRLFact]:
        """
        Crea fatti XBRL dai dati aziendali.

        Args:
            company_data: Dati aziendali (emissions, workforce, ecc.)

        Returns:
            Lista di XBRLFact
        """
        facts = []

        # GHG Emissions
        emissions = company_data.get("emissions", {})
        if emissions:
            scope1 = emissions.get("scope1", {})
            if isinstance(scope1, dict):
                val = scope1.get("value")
            else:
                val = scope1
            if val is not None:
                facts.append(XBRLFact(
                    concept="esrs:GHGScope1Emissions",
                    value=val,
                    unit_ref="u_tCO2eq",
                    context_ref="c_current",
                ))

            scope2_loc = emissions.get("scope2_location", {})
            if isinstance(scope2_loc, dict):
                val = scope2_loc.get("value")
            else:
                val = scope2_loc
            if val is not None:
                facts.append(XBRLFact(
                    concept="esrs:GHGScope2LocationEmissions",
                    value=val,
                    unit_ref="u_tCO2eq",
                    context_ref="c_current",
                ))

            scope2_mkt = emissions.get("scope2_market", {})
            if isinstance(scope2_mkt, dict):
                val = scope2_mkt.get("value")
            else:
                val = scope2_mkt
            if val is not None:
                facts.append(XBRLFact(
                    concept="esrs:GHGScope2MarketEmissions",
                    value=val,
                    unit_ref="u_tCO2eq",
                    context_ref="c_current",
                ))

            scope3 = emissions.get("scope3", {})
            if isinstance(scope3, dict):
                val = scope3.get("value")
            else:
                val = scope3
            if val is not None:
                facts.append(XBRLFact(
                    concept="esrs:GHGScope3Emissions",
                    value=val,
                    unit_ref="u_tCO2eq",
                    context_ref="c_current",
                ))

        # Workforce
        workforce = company_data.get("workforce", {})
        if workforce:
            total = workforce.get("total")
            if total is not None:
                facts.append(XBRLFact(
                    concept="esrs:TotalEmployees",
                    value=total,
                    unit_ref="u_employees",
                    context_ref="c_instant",
                    decimals="INF",
                    scale=0,
                ))

        # Energy
        energy = company_data.get("energy", {})
        if energy:
            fossil = energy.get("fossil")
            if fossil is not None:
                facts.append(XBRLFact(
                    concept="esrs:EnergyFossilConsumption",
                    value=fossil,
                    unit_ref="u_MWh",
                    context_ref="c_current",
                ))
            renewable = energy.get("renewable")
            if renewable is not None:
                facts.append(XBRLFact(
                    concept="esrs:EnergyRenewableConsumption",
                    value=renewable,
                    unit_ref="u_MWh",
                    context_ref="c_current",
                ))
            total = energy.get("total")
            if total is not None:
                facts.append(XBRLFact(
                    concept="esrs:EnergyTotalConsumption",
                    value=total,
                    unit_ref="u_MWh",
                    context_ref="c_current",
                ))

        return facts

    def tag_template_blocks(
        self,
        template: Any,
    ) -> Any:
        """
        Applica tagging iXBRL ai singoli blocchi del template.

        Per ogni ContentBlock con xbrl_tags, genera i tag iXBRL
        e li aggiunge al content_html del blocco.

        Args:
            template: ReportTemplate da aggiornare

        Returns:
            ReportTemplate con blocchi taggati iXBRL
        """
        tagged_blocks = 0

        # Per ogni sezione, DR, e blocco
        for section in template.sections:
            for dr in section.disclosure_requirements:
                for block in dr.blocks:
                    if not block.xbrl_tags:
                        continue

                    # Genera tag per ogni XBRLTag nel blocco
                    for xbrl_tag_info in block.xbrl_tags:
                        # Il blocco ha XBRLTag objects dal template engine
                        fact = self._tag_from_block_tag(xbrl_tag_info)
                        if fact:
                            ix_tag = fact.to_ixbrl_tag()
                            # Aggiungi il tag iXBRL prima del contenuto
                            block.content_html = (
                                f'{ix_tag}\n{block.content_html}'
                            )
                            tagged_blocks += 1

        logger.info(f"Tagged {tagged_blocks} blocks with iXBRL")
        return template

    def _tag_from_block_tag(
        self,
        xbrl_tag_info: Any,
    ) -> Optional[XBRLFact]:
        """
        Converte un XBRLTag (template engine) in XBRLFact per iXBRL.

        Args:
            xbrl_tag_info: XBRLTag dal template engine

        Returns:
            XBRLFact o None se non può essere convertito
        """
        try:
            return XBRLFact(
                concept=xbrl_tag_info.concept,
                value="",  # Verrà popolato dal template engine
                unit_ref=xbrl_tag_info.unit_ref,
                context_ref=xbrl_tag_info.context_ref,
                scale=xbrl_tag_info.scale,
                decimals=xbrl_tag_info.decimals,
                is_numeric=xbrl_tag_info.concept.startswith("esrs:"),
            )
        except Exception as e:
            logger.warning(f"Cannot convert XBRLTag to fact: {e}")
            return None

    def tag_value(self, value: float, concept: str, unit_ref: str = "u_EUR", context_ref: str = "c_current", decimals: str = "INF", scale: int = 0, standard: str = "", unit: str = "") -> str:
        """
        Format and return a numeric fact wrapped in <ix:nonFraction> tag.

        Args:
            value: The numeric value to tag
            concept: XBRL concept name (e.g. "esrs:GHGScope1Emissions")
            unit_ref: Reference to a unit definition
            context_ref: Reference to a context definition
            decimals: Number of decimal places (INF = integer)
            scale: Scaling factor (0 = units, 3 = thousands, 6 = millions)
            standard: ESRS standard reference (e.g. "ESRS E1-6")
            unit: Alias for unit_ref

        Returns:
            iXBRL tag string
        """
        # Accept 'unit' as alias for 'unit_ref'
        if unit and not unit_ref.startswith("u_"):
            unit_ref = unit
        fact = XBRLFact(
            concept=concept,
            value=value,
            unit_ref=unit_ref,
            context_ref=context_ref,
            decimals=decimals,
            scale=scale,
            is_numeric=True,
        )
        return fact.to_ixbrl_tag()

    def tag_text(self, text: str, concept: str, context_ref: str = "c_current", standard: str = "") -> str:
        """
        Return a textual fact wrapped in <ix:nonNumeric> tag.

        Args:
            text: The text value to tag
            concept: XBRL concept name (e.g. "esrs:GovernanceBodyRole")
            context_ref: Reference to a context definition
            standard: ESRS standard reference (e.g. "ESRS S1-1")

        Returns:
            iXBRL tag string
        """
        fact = XBRLFact(
            concept=concept,
            value=text,
            context_ref=context_ref,
            is_numeric=False,
        )
        return fact.to_ixbrl_tag()

    def get_registered_concepts(self) -> List[Dict[str, Any]]:
        """
        Return list of concepts mapped to their standard name.

        Returns:
            List of dict with concept details
        """
        concepts = []
        for concept_name, concept_data in self.taxonomy.concepts.items():
            datapoint_ref = concept_data.get("datapoint_ref", "")
            # Extract standard name from datapoint_ref (e.g. "ESRS E1-6.Scope1" -> "ESRS E1-6")
            standard = ""
            if datapoint_ref:
                parts = datapoint_ref.split(".")
                standard = parts[0] if len(parts) > 1 else datapoint_ref
            elif "ESRS" in concept_name:
                standard = concept_name
            concepts.append({
                "name": concept_name,
                "datapoint_ref": datapoint_ref,
                "type": concept_data.get("type", ""),
                "unit": concept_data.get("unit", ""),
                "standard": standard,
            })
        return concepts

    def extract_facts_from_xhtml(
        self,
        ixbrl_content: str,
    ) -> List[Dict[str, Any]]:
        """
        Estrae i fatti iXBRL da un documento XHTML taggato.

        Utile per debug e verifica.

        Args:
            ixbrl_content: Documento XHTML con tagging iXBRL

        Returns:
            Lista di dict con concept, value, unitRef, contextRef
        """
        facts = []

        # Estrai <ix:nonFraction>
        for match in re.finditer(
            r'<ix:nonFraction\s+name="([^"]+)"\s+unitRef="([^"]+)"\s+contextRef="([^"]+)"[^>]*>([^<]+)</ix:nonFraction>',
            ixbrl_content,
        ):
            facts.append({
                "concept": match.group(1),
                "unit_ref": match.group(2),
                "context_ref": match.group(3),
                "value": match.group(4),
                "type": "nonFraction",
            })

        # Estrai <ix:nonNumeric>
        for match in re.finditer(
            r'<ix:nonNumeric\s+name="([^"]+)"\s+contextRef="([^"]+)"[^>]*>([^<]+)</ix:nonNumeric>',
            ixbrl_content,
        ):
            facts.append({
                "concept": match.group(1),
                "context_ref": match.group(2),
                "value": match.group(3),
                "type": "nonNumeric",
            })

        return facts


# ── Helper Functions ──────────────────────────────────────────────

def create_ixbrl_tagger(
    entity_identifier: str = "",
    reporting_year: int = 2026,
    language: str = "en",
) -> IXBRLTagger:
    """
    Factory per creare un IXBRLTagger preconfigurato.

    Args:
        entity_identifier: Identificatore dell'entità (LEI/VAT)
        reporting_year: Anno di rendicontazione
        language: Lingua del report

    Returns:
        IXBRLTagger configurato
    """
    config = IXBRLTaggerConfig(
        entity_identifier=entity_identifier,
        reporting_year=reporting_year,
        language=language,
    )
    tagger = IXBRLTagger(config)
    tagger.load_taxonomy()
    return tagger


# Alias for backward compatibility with tests
IxbrlTagger = IXBRLTagger


def generate_ixbrl_report_api(
    template: Any,
    company_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Helper per endpoint API: genera report iXBRL completo.

    Args:
        template: ReportTemplate da processare
        company_data: Dati aziendali

    Returns:
        Dict con report iXBRL e metadati
    """
    tagger = create_ixbrl_tagger(
        entity_identifier=company_data.get("company_vat", ""),
        reporting_year=company_data.get("reporting_year", 2026),
        language=company_data.get("language", "en"),
    )

    # Genera iXBRL
    ixbrl_content = tagger.tag_report_from_template(template, company_data)

    # Estrai facts per debug
    facts = tagger.extract_facts_from_xhtml(ixbrl_content)

    return {
        "ixbrl_content": ixbrl_content,
        "facts_count": len(facts),
        "facts": facts,
        "format": "iXBRL",
        "taxonomy": ESRS_TAXONOMY_BASE,
    }
