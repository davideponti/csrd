"""
CSRD Comply — Data Collection Automation System (Step 15)

Sistema di raccolta automatica dati per emissioni.
Include: XERO/QuickBooks integration, PDF OCR, HR data, fleet data,
utility provider API, banking data import.

Refactored with OCR preprocessing per specifiche estrazione bollette.
Supporto multi-paese: IT, ES, DE, NL, UK, SE, PL.
Output conforme al formato richiesto per calcolo carbon footprint (GHG Protocol).
"""
from typing import Optional, Dict, Any, List, Tuple
import json
import re
from datetime import datetime, date
import calendar


class DataCollectorService:
    """Servizio di raccolta dati automatica per emissioni."""

    # ── OCR Pre-processing ────────────────────────────────────────

    @staticmethod
    def _preprocess_ocr_text(raw_text: str) -> str:
        """
        Pre-processing obbligatorio per testo proveniente da OCR.
        
        Nei contesti numerici (date, importi, consumi) sostituisci:
        - l → 1
        - O → 0  
        - I → 1
        
        Normalizza separatori decimali: sia "." che "," sono validi.
        Ignora caratteri non stampabili o spazi doppi.
        """
        if not raw_text:
            return ""

        text = raw_text

        # 1. Rimuovi caratteri non stampabili ma preserva caratteri Unicode europei
        #    Include lettere accentate, caratteri polacchi (Ł, ł), svedesi (Å, Ä, Ö), etc.
        text = re.sub(r'[^\x20-\x7E\x80-\xFF\n\r\t\u0100-\u024F\u00C0-\u00FF]', '', text)

        # 2. Sostituzioni OCR in contesto STRETTAMENTE numerico:
        #    Solo quando l -> 1, O -> 0, I -> 1 sono circondati da cifre
        #    o separatori numerici (., /, -), MAI da lettere o spazi.
        #    Questo evita di corrompere parole come "Vattenfall" o "Enel".
        #    Le sostituzioni sono iterate 3x per gestire catene come "OO", "ll".
        for _ in range(3):
            text_old = text
            # l → 1 (tra cifre o separatori)
            text = re.sub(r'(?<=[0-9])l(?=[0-9.,/\-\s\n\r])', '1', text)
            text = re.sub(r'(?<=[0-9.,/\-\s])l(?=[0-9])', '1', text)
            # l → 1 (tra separatore e altro carattere OCR sporco, o a fine stringa)
            text = re.sub(r'(?<=[.,/\-])l(?=[.,/\-lO\s\n\r]|$)', '1', text)
            # O → 0 (tra cifre, separatori, o in sequenze come "OO")
            text = re.sub(r'(?<=[0-9])O(?=[0-9.,/\-\s\n\r])', '0', text)
            text = re.sub(r'(?<=[0-9.,/\-\s])O(?=[0-9])', '0', text)
            # O → 0 (tra separatore e altro O/l, o a fine stringa)
            text = re.sub(r'(?<=[.,/\-])O(?=[.,/\-lO\s\n\r]|$)', '0', text)
            # O → 0 a fine stringa dopo cifra/separatore (es. ",OO" fine bolletta)
            text = re.sub(r'(?<=[0-9])O(?=\s*$)', '0', text)
            # I → 1 (tra cifre o separatori, o a fine stringa)
            text = re.sub(r'(?<=[0-9])I(?=[0-9.,/\-\s\n\r])', '1', text)
            text = re.sub(r'(?<=[0-9.,/\-\s])I(?=[0-9])', '1', text)
            text = re.sub(r'(?<=[.,/\-])I(?=[.,/\-lO\s\n\r]|$)', '1', text)
            text = re.sub(r'(?<=[0-9])I(?=\s*$)', '1', text)
            if text == text_old:
                break

        # 3. Normalizza separatori decimali: "3,5" o "3.5" entrambi validi
        #    Convertiamo la virgola decimale italiana in punto
        #    Pattern: cifra + virgola + 2 cifre = decimale
        text = re.sub(r'(\d),(\d{2})(?!\d)', r'\1.\2', text)

        # 4. Collassa spazi doppi e trim
        text = re.sub(r' {2,}', ' ', text)
        text = text.strip()

        return text

    @staticmethod
    def _parse_number(value_str: str) -> Optional[float]:
        """
        Converte una stringa numerica in float, gestendo formati italiani 
        (con virgola decimale) e formati internazionali (con punto decimale).
        Dopo il preprocessing le virgole decimali sono già state convertite in punti.
        
        - "1.234" → 1234 (migliaia, 3+ cifre dopo ultimo punto)
        - "1.234,56" → 1234.56 (con virgola decimale)
        - "1,234.56" → 1234.56 (formato internazionale)
        - "1.234.56" → 1234.56 (migliaia + decimale, da preprocessing)
        - "890.75" → 890.75 (decimale, da preprocessing "890,75")
        - "1234.56" → 1234.56 (punto decimale)
        - "450.00" → 450.0 (decimale, da preprocessing "450,00")
        """
        if not value_str:
            return None
        try:
            # Se contiene sia punto che virgola: formato internazionale
            if "." in value_str and "," in value_str:
                # "1,234.56" → rimuovi virgola
                value_str = value_str.replace(",", "")
                return float(value_str)
            # Se contiene solo virgola: formato italiano puro
            if "," in value_str:
                value_str = value_str.replace(",", ".")
                return float(value_str)
            # Se contiene solo punto
            if "." in value_str:
                parts = value_str.split(".")
                # 2 parti: X.YY o X.YYY
                if len(parts) == 2:
                    if len(parts[1]) == 2:
                        # "890.75" o "450.00" → decimale (da virgola italiana convertita)
                        return float(value_str)
                    else:
                        # "1.850" o "2.525" → migliaia (3+ cifre dopo punto)
                        return float(parts[0] + parts[1])
                elif len(parts) == 3:
                    # "1.850.00" → migliaia + decimale
                    return float(f"{parts[0]}{parts[1]}.{parts[2]}")
                else:
                    # Più parti → rimuovi tutti i punti
                    return float(value_str.replace(".", ""))
            # Nessun separatore
            return float(value_str)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _detect_ocr_noise(text: str, original: str) -> bool:
        """Rileva se il testo originale conteneva errori OCR significativi."""
        if not original:
            return False
        ocr_patterns = [
            r'\d+[lOI]\d+',
            r'\d+[lOI][A-Za-z]',
            r'[A-Za-z][lOI]\d+',
            r'[lOIl]{2,}\d',
            r'\d[lOIl]{2,}',
        ]
        for pat in ocr_patterns:
            if re.search(pat, original):
                return True
        return False

    # ════════════════════════════════════════════════════════════════
    #  MAIN PARSER — Multi-country utility bill extraction
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def parse_utility_bill_pdf_text(
        extracted_text: str,
    ) -> Dict[str, Any]:
        """
        Estrae dati da testo di bolletta elettrica/gas.
        Usato dopo OCR su PDF caricato dall'utente.
        
        Supporto multi-paese: IT, ES, DE, NL, UK, SE, PL.
        
        Include pre-processing OCR obbligatorio:
        - l→1, O→0, I→1 in contesti numerici
        - Normalizzazione separatori decimali
        - Rimozione caratteri non stampabili e spazi doppi
        
        Returns:
            JSON conforme allo schema specificato nel task.
        """
        # ── Output nel formato richiesto ───────────────────────
        result = {
            "paese": None,
            "fornitore": None,
            "tipo": None,
            "consumo_kwh": None,
            "consumo_originale": None,
            "unita_originale": None,
            "costo": None,
            "valuta": None,
            "periodo_inizio": None,
            "periodo_fine": None,
            "codice_utenza": None,
            "lettura_stimata": False,
            "confidenza": 0,
        }

        if not extracted_text:
            return result

        # ── Pre-process OCR text ──────────────────────────────
        raw_text = extracted_text
        text = DataCollectorService._preprocess_ocr_text(extracted_text)
        text_lower = text.lower()

        # ── Rileva OCR noise (sull'originale, prima preprocessing) ──
        has_ocr_noise = DataCollectorService._detect_ocr_noise(text, extracted_text)

        # ── Confidence tracking ───────────────────────────────
        conf = 100
        fields_found = 0
        total_fields = 7  # fornitore, tipo, consumo_kwh, costo, periodo (2), codice_utenza

        # ══════════════════════════════════════════════════════
        #  1. COUNTRY DETECTION
        # ══════════════════════════════════════════════════════
        paese, conf_paese = DataCollectorService._detect_country(text, text_lower)
        result["paese"] = paese
        if conf_paese == -1:
            # Paese non riconosciuto
            conf -= 10

        # ══════════════════════════════════════════════════════
        #  2. BILL TYPE DETECTION
        # ══════════════════════════════════════════════════════
        tipo = DataCollectorService._detect_bill_type(text_lower)
        result["tipo"] = tipo
        if tipo:
            fields_found += 1

        # ══════════════════════════════════════════════════════
        #  3. PROVIDER EXTRACTION
        # ══════════════════════════════════════════════════════
        fornitore = DataCollectorService._extract_provider(text, text_lower, paese)
        result["fornitore"] = fornitore
        if fornitore:
            fields_found += 1

        # ══════════════════════════════════════════════════════
        #  4. CONSUMPTION EXTRACTION (kWh + original unit)
        # ══════════════════════════════════════════════════════
        consumo_kwh, consumo_originale, unita_originale = \
            DataCollectorService._extract_consumption(text_lower, paese)
        result["consumo_kwh"] = consumo_kwh
        result["consumo_originale"] = consumo_originale
        result["unita_originale"] = unita_originale
        if consumo_kwh is not None:
            fields_found += 1

        # ══════════════════════════════════════════════════════
        #  5. TOTAL COST EXTRACTION
        # ══════════════════════════════════════════════════════
        costo, valuta = DataCollectorService._extract_total_cost(text_lower, text, paese)
        result["costo"] = costo
        result["valuta"] = valuta
        if costo is not None:
            fields_found += 1

        # ══════════════════════════════════════════════════════
        #  6. PERIOD EXTRACTION
        # ══════════════════════════════════════════════════════
        period = DataCollectorService._extract_period(text_lower)
        if period:
            start_iso = DataCollectorService._date_to_iso(period[0])
            end_iso = DataCollectorService._date_to_iso(period[1]) if period[1] else None
            if start_iso:
                result["periodo_inizio"] = start_iso
                fields_found += 1
            if end_iso:
                result["periodo_fine"] = end_iso
                fields_found += 1

        # ══════════════════════════════════════════════════════
        #  7. METER CODE EXTRACTION (country-specific)
        # ══════════════════════════════════════════════════════
        codice_utenza = DataCollectorService._extract_meter_code(text, paese)
        result["codice_utenza"] = codice_utenza
        if codice_utenza:
            fields_found += 1

        # ══════════════════════════════════════════════════════
        #  8. ESTIMATED READING DETECTION
        # ══════════════════════════════════════════════════════
        lettura_stimata = DataCollectorService._detect_estimated_reading(text_lower)
        result["lettura_stimata"] = lettura_stimata

        # ══════════════════════════════════════════════════════
        #  9. CONFIDENCE CALCULATION
        # ══════════════════════════════════════════════════════
        # -15 per ogni campo obbligatorio non trovato (fornitore, tipo, consumo_kwh, costo, periodo, codice_utenza)
        # Nota: periodo_inizio e periodo_fine contano come 1 campo
        # Nota: tipo è uno dei 6 campi obbligatori
        obbligatori = ["fornitore", "tipo", "consumo_kwh", "costo", "periodo_inizio", "codice_utenza"]
        for campo in obbligatori:
            if result.get(campo) is None:
                conf -= 15

        # -10 se testo presenta chiari segni di OCR sporco
        if has_ocr_noise:
            conf -= 10

        # -10 se paese non riconosciuto (già fatto)

        # -5 se lettura stimata
        if lettura_stimata:
            conf -= 5

        result["confidenza"] = max(0, min(100, int(conf)))

        return result

    # ════════════════════════════════════════════════════════════════
    #  COUNTRY DETECTION
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def _detect_country(text: str, text_lower: str) -> Tuple[Optional[str], int]:
        """
        Rileva il paese dal codice utenza, dalla lingua del testo o dal fornitore.
        
        Returns:
            (paese_iso, conf_level) dove conf_level -1 = non riconosciuto, 0 = riconosciuto
        """
        # ── Strategy 1: Meter code patterns ──────────────────
        # IT: POD (IT001E...) or PDR (IT...)
        if re.search(r'\bit\d{3}e\w+\b', text, re.IGNORECASE):
            return "IT", 0
        if re.search(r'\bit\d{3}g\w+\b', text, re.IGNORECASE):
            return "IT", 0

        # PL: PPE (first, since 11-digit PPE can match DE pattern)
        if re.search(r'\b(?:ppe)\s*[:=]\s*\d{5,}\b', text, re.IGNORECASE):
            return "PL", 0
        if re.search(r'\bppe\s+\d{5,}\b', text, re.IGNORECASE):
            return "PL", 0
        if re.search(r'\b(?:ppe)\d{5,}\b', text, re.IGNORECASE):
            return "PL", 0

        # ES: CUPS starts with ES
        if re.search(r'\bes\d{4,}\w+', text, re.IGNORECASE):
            return "ES", 0

        # SE: MELO or MPID
        if re.search(r'\b(?:melo|mpid)\b', text, re.IGNORECASE):
            return "SE", 0

        # DE: MaLo-ID (11 digits, but only with keyword context to avoid PL/SE conflicts)
        if re.search(r'(?:malo[-\s]?id|z[äa]hlernummer)[\s:]*\d{11}', text, re.IGNORECASE):
            return "DE", 0
        if re.search(r'\b\d{11}\b', text) and not re.search(r'\bmelo\b|\bmprn\b', text_lower):
            return "DE", 0

        # NL: EAN (18 digits)
        if re.search(r'\b\d{18}\b', text):
            return "NL", 0

        # UK: MPAN (13 digits) or MPRN (10 digits)
        if re.search(r'\b\d{13}\b', text):
            return "UK", 0
        if re.search(r'\b\d{10}\b', text):
            return "UK", 0

        # ── Strategy 2: Language keywords ────────────────────
        country_keywords = {
            "IT": [r'\bpod\b', r'\bpdr\b', r'\bpunto\s+di\s+riconsegna\b',
                   r'\bfornitore\b', r'\benergia\s+elettrica\b',
                   r'\bconsumato\b', r'\bimporto\s+dovuto\b',
                   r'\btotale\s+da\s+pagare\b'],
            "ES": [r'\bcups\b', r'\bpunto\s+de\s+suministro\b',
                   r'\bconsumo\s+total\b', r'\bimporte\s+total\b',
                   r'\btotal\s+a\s+pagar\b', r'\benerg[íi]a\s+activa\b',
                   r'\bpeaje\b', r'\bcomercializadora\b'],
            "DE": [r'\bnetzentgelte\b', r'\benergielieferung\b',
                   r'\bverbrauch\b', r'\bgesamtbetrag\b',
                   r'\bmalo[- ]?id\b', r'\bza[äa]hlernummer\b',
                   r'\barbeitspreis\b', r'\bgrundpreis\b'],
            "NL": [r'\bean\b', r'\benergieverbruik\b',
                   r'\btotaal\s+te\s+betalen\b', r'\bverbruik\b',
                   r'\bnetbeheer\b', r'\bleverancier\b',
                   r'\bkapitaal\b', r'\btransportkosten\b'],
            "UK": [r'\bmpan\b', r'\bmprn\b', r'\benergy\s+used\b',
                   r'\btotal\s+amount\s+due\b', r'\bsupply\s+number\b',
                   r'\belectricity\s+supply\b', r'\bgas\s+supply\b',
                   r'\bmeter\s+point\b', r'\bcalorific\s+value\b'],
            "SE": [r'\bmelo\b', r'\bmpid\b', r'\bf[öo]rbrukning\b',
                   r'\btotalt\s+att\s+betala\b', r'\benergif[öo]rbrukning\b',
                   r'\b[öo]verf[öo]ring\b', r'\beln[äa]t\b',
                   r'\bn[äa]tavgift\b'],
            "PL": [r'\bppe\b', r'\bzu[żz]ycie\s+energii\b',
                   r'\b[łl][aą]czna\s+kwota\b', r'\bdo\s+zap[łl]aty\b',
                   r'\bop[łl]ata\b', r'\bsprzedawca\b',
                   r'\bdystrybucja\b'],
        }

        for paese, keywords in country_keywords.items():
            for kw in keywords:
                if re.search(kw, text_lower):
                    return paese, 0

        # ── Strategy 3: Provider names ───────────────────────
        provider_country_map = {
            "IT": ["enel", "acea", "a2a", "hera", "iren", "sorgenia",
                   "estra", "dolomiti", "servizio elettrico nazionale",
                   "green network", "senova", "nen", "wekiwi", "plenitude"],
            "ES": ["iberdrola", "endesa", "naturgy", "repsol", "cepsa",
                   "factorenergia", "gas natural fenosa", "totalenergies",
                   "unedesa"],
            "DE": ["e.on", "rwe", "innogy", "enBW", "vattenfall",
                   "stadtwerke", "e wie einfach", "lichtblick", "yello",
                   "mainova", "entega", "naturstrom"],
            "NL": ["essent", "vandebron", "eneco", "greenchoice",
                   "nederlandse energie maatschappij", "budget energie",
                   "om", "powerpeers", "engie", "anode"],
            "UK": ["british gas", "e.on next", "ovo energy", "scottish power",
                   "edf energy", "npower", "shell energy", "utilita",
                   "octopus energy", "sse", "bulb"],
            "SE": ["vattenfall", "e.on", "skellefteå kraft", "telge energi",
                   "göteborg energi", "stockholm exergi", "fjärrvärme",
                   "kraftringen", "jönköping energi"],
            "PL": ["pge", "tauron", "energa", "eon", "innogy",
                   "orange energia", "pkp energetyka", "fortum"],
        }

        text_lower_for_search = text_lower
        for paese, providers in provider_country_map.items():
            for prov in providers:
                if prov in text_lower_for_search:
                    return paese, 0

        return None, -1

    # ════════════════════════════════════════════════════════════════
    #  BILL TYPE DETECTION
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def _detect_bill_type(text_lower: str) -> Optional[str]:
        """Rileva se la bolletta è di tipo gas o elettricità."""
        # Parole chiave esclusive del gas
        gas_exclusive = [
            "smc", "standard metri cubi", "pdr", "codice pdr",
            "gas naturale", "metano", "aardgas", "erdgas",
            "mprn", "calorific value",
            "verbruik gas", "gasverbruik", "förbrukning gas",
            "zużycie gazu",
            "gasrechnung", "gasverbrauch", "gaslieferung",
        ]
        # Parole chiave esclusive dell'elettricità
        electricity_exclusive = [
            "pod", "codice pod", "fasce f1", "fasce f2", "fasce f3",
            "fascia f1", "fascia f2", "fascia f3",
            "energia attiva", "mpan",
            "electricity supply", "electricité",
            "wirkarbeit", "blindarbeit",
            "electrische energie", "electriciteit",
            "aktiva energi", "elenergi",
            "energia elektryczna", "energia czynna",
            "netzentgelte",
        ]

        if any(kw in text_lower for kw in gas_exclusive):
            return "gas"
        if any(kw in text_lower for kw in electricity_exclusive):
            return "electricity"

        # Parole chiave generiche con contesto
        gas_generic = ["gas", "fornitura gas", "consumo gas"]
        electricity_generic = [
            "elettricità", "elettrica", "electricity", "strom",
            "kwh", "energia",
        ]

        gas_count = sum(1 for kw in gas_generic if kw in text_lower)
        elec_count = sum(1 for kw in electricity_generic if kw in text_lower)

        if gas_count > elec_count:
            return "gas"
        elif elec_count > gas_count:
            return "electricity"

        return None

    # ════════════════════════════════════════════════════════════════
    #  PROVIDER EXTRACTION (multi-country)
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def _extract_provider(text: str, text_lower: str, paese: Optional[str]) -> Optional[str]:
        """
        Extract provider name using multiple strategies.
        Supporta fornitori di IT, ES, DE, NL, UK, SE, PL.
        """
        # ── Provider names per paese ──────────────────────────
        all_providers = [
            # ITALIA
            (r'\benel\s+energia\b', "Enel Energia", "IT"),
            (r'\benel\s+italia\b', "Enel", "IT"),
            (r'\benel\b', "Enel", "IT"),
            (r'\bacea\b', "Acea", "IT"),
            (r'\ba\s*2\s*a\b', "A2A", "IT"),
            (r'\bher\s*comm\b', "Hera Comm", "IT"),
            (r'\biren\b', "Iren", "IT"),
            (r'\bsorgenia\b', "Sorgenia", "IT"),
            (r'\bestra\s+energie\b', "Estra Energie", "IT"),
            (r'\bdolomiti\s+energia\b', "Dolomiti Energia", "IT"),
            (r'\bservizio\s+elettrico\s+nazionale\b', "Servizio Elettrico Nazionale", "IT"),
            (r'\bgreen\s+network\b', "Green Network", "IT"),
            (r'\bsenova\b', "Senova", "IT"),
            (r'\bnen\b', "NeN", "IT"),
            (r'\bwekiwi\b', "Wekiwi", "IT"),
            (r'\bplenitude\b', "Plenitude", "IT"),
            # SPAGNA
            (r'\biberdrola\b', "Iberdrola", "ES"),
            (r'\bendesa\b', "Endesa", "ES"),
            (r'\bnaturgy\b', "Naturgy", "ES"),
            (r'\brepsol\b', "Repsol", "ES"),
            (r'\bcepsa\b', "Cepsa", "ES"),
            (r'\bfactorenergia\b', "Factorenergia", "ES"),
            (r'\bgas\s+natural\s+fenosa\b', "Gas Natural Fenosa", "ES"),
            (r'\btotalenergies\b', "TotalEnergies", "ES"),
            (r'\bunedesa\b', "Unedesa", "ES"),
            # GERMANIA
            (r'\bein\s*\.?\s*on\b', "E.ON", "DE"),
            (r'\brwe\b', "RWE", "DE"),
            (r'\binnogy\b', "Innogy", "DE"),
            (r'\benbw\b', "EnBW", "DE"),
            (r'\bvattenfall\b', "Vattenfall", "DE"),
            (r'\bstadtwerke\b', "Stadtwerke", "DE"),
            (r'\blichtblick\b', "LichtBlick", "DE"),
            (r'\byello\b', "Yello", "DE"),
            (r'\bmainova\b', "Mainova", "DE"),
            (r'\bentega\b', "Entega", "DE"),
            (r'\bnaturstrom\b', "Naturstrom", "DE"),
            (r'\be\s*\.?\s*wie\s+einfach\b', "E Wie Einfach", "DE"),
            # PAESI BASSI
            (r'\bessent\b', "Essent", "NL"),
            (r'\bvandebron\b', "Vandebron", "NL"),
            (r'\beneco\b', "Eneco", "NL"),
            (r'\bgreenchoice\b', "Greenchoice", "NL"),
            (r'\bbudget\s+energie\b', "Budget Energie", "NL"),
            (r'\bpowerpeers\b', "Powerpeers", "NL"),
            (r'\bengie\b', "Engie", "NL"),
            (r'\banode\b', "Anode", "NL"),
            # UK
            (r'\bbritish\s+gas\b', "British Gas", "UK"),
            (r'\bovo\s+energy\b', "OVO Energy", "UK"),
            (r'\beon\s+next\b', "E.ON Next", "UK"),
            (r'\bscottish\s+power\b', "Scottish Power", "UK"),
            (r'\bedf\s+energy\b', "EDF Energy", "UK"),
            (r'\bnpower\b', "npower", "UK"),
            (r'\bshell\s+energy\b', "Shell Energy", "UK"),
            (r'\butilita\b', "Utilita", "UK"),
            (r'\boctopus\s+energy\b', "Octopus Energy", "UK"),
            (r'\bsse\b', "SSE", "UK"),
            (r'\bbulb\b', "Bulb", "UK"),
            # SVEZIA
            (r'\bvattenfall\b', "Vattenfall", "SE"),
            (r'\be\s*\.?\s*on\b', "E.ON", "SE"),
            (r'\bg[öo]teborg\s+energi\b', "Göteborg Energi", "SE"),
            (r'\btelge\s+energi\b', "Telge Energi", "SE"),
            (r'\bkraftringen\b', "Kraftringen", "SE"),
            (r'\bskellefte[åa]\s+kraft\b', "Skellefteå Kraft", "SE"),
            # POLONIA
            (r'\bpge\b', "PGE", "PL"),
            (r'\btauron\b', "Tauron", "PL"),
            (r'\benerga\b', "Energa", "PL"),
            (r'\borange\s+energia\b', "Orange Energia", "PL"),
            (r'\bpkp\s+energetyka\b', "PKP Energetyka", "PL"),
            (r'\bfortum\b', "Fortum", "PL"),
        ]

        for pattern, name, _ in all_providers:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return name

        # ── Fallback: "Fornitore:" / "Provider:" / "Lieferant:" patterns ──
        provider_prefixes = [
            r'fornitore\s*[:;]\s*([A-Za-zÀ-ÿ\s.\']{2,})',
            r'provider\s*[:;]\s*([A-Za-zÀ-ÿ\s.\']{2,})',
            r'lieferant\s*[:;]\s*([A-Za-zÀ-ÿ\s.\']{2,})',
            r'leverancier\s*[:;]\s*([A-Za-zÀ-ÿ\s.\']{2,})',
            r'sprzedawca\s*[:;]\s*([A-Za-zÀ-ÿ\s.\']{2,})',
            r'comercializadora\s*[:;]\s*([A-Za-zÀ-ÿ\s.\']{2,})',
            r'supplier\s*[:;]\s*([A-Za-zÀ-ÿ\s.\']{2,})',
            r'company\s*[:;]\s*([A-Za-zÀ-ÿ\s.\']{2,})',
            r'societ[àa]\s*[:;]\s*([A-Za-zÀ-ÿ\s.\']{2,})',
            r'venditore\s*[:;]\s*([A-Za-zÀ-ÿ\s.\']{2,})',
        ]

        for pattern in provider_prefixes:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2 and name.lower() not in ['il', 'la', 'le', 'di', 'del', 'della', '-', 'fornitore']:
                    return name.title()

        return None

    # ════════════════════════════════════════════════════════════════
    #  CONSUMPTION EXTRACTION (kWh + original unit)
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def _extract_consumption(text_lower: str, paese: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """
        Estrae il consumo in kWh e in unità originale.
        
        Cerca in ordine:
        - "Energia consumata" (IT), "Energía consumida" (ES), "Verbrauch kWh" (DE)
        - "Energieverbruik" (NL), "Energy used" (UK), "Förbrukning" (SE), "Zużycie energii" (PL)
        
        Esclude valori seguiti da "/Smc", "/mc", "/Nm³" (sono poteri calorifici).
        
        Returns:
            (consumo_kwh, consumo_originale, unita_originale)
        """
        # ── Pattern consumo in kWh ────────────────────────────
        kwh_patterns = [
            # IT: "Energia consumata: 2.525,40 kWh"
            r'energia\s+consumata\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh',
            # IT: "Energia termica: 12.850,OO kWh"
            r'energia\s+termica\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh',
            # IT: "Consumo totale: 1.200,50 Smc" -> salva come originale, cerca kWh altrove
            r'consumo\s+totale\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh',
            # DE: "Verbrauch kWh"
            r'verbrauch\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh',
            # DE: "Wirkarbeit"
            r'wirkarbeit\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh',
            # NL: "Energieverbruik" / "Verbruik"
            r'energieverbruik\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh',
            r'verbruik\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh',
            # UK: "Energy used"
            r'energy\s+used\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh',
            r'energy\s+consumption\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh',
            r'consumption\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh',
            # SE: "Förbrukning"
            r'f[öo]rbrukning\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh',
            r'energif[öo]rbrukning\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh',
            # PL: "Zużycie energii"
            r'zu[żz]ycie\s+energii\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh',
            # ES: "Energía consumida"
            r'energ[íi]a\s+consumida\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh',
            r'consumo\s+total\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh',
        ]

        consumo_kwh = None
        for pattern in kwh_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                value = DataCollectorService._parse_number(match.group(1))
                if value is not None and value >= 10:
                    consumo_kwh = value
                    break

        # ── Pattern consumo in MWh (SE, PL, DE) ───────────────
        if consumo_kwh is None:
            mwh_patterns = [
                r'f[öo]rbrukning\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*mwh',
                r'energif[öo]rbrukning\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*mwh',
                r'zu[żz]ycie\s+energii\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*mwh',
                r'verbrauch\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*mwh',
                r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*mwh',
            ]
            for pattern in mwh_patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    value = DataCollectorService._parse_number(match.group(1))
                    if value is not None and value >= 1:
                        consumo_kwh = value * 1000  # MWh → kWh
                        break

        # ── Pattern consumo in unità originale (Smc, mc, Nm³, MWh) ──
        consumo_originale = None
        unita_originale = None

        # Escludi poteri calorifici (valori seguiti da "/Smc", "/mc", "/Nm³")
        original_patterns = [
            # Smc (IT gas)
            (r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*smc\b(?!\/)', "Smc"),
            (r'consumo\s*gas\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*smc', "Smc"),
            # Standard metri cubi (IT)
            (r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*standard\s*metri\s*cubi', "Smc"),
            # m³ / mc (ES, NL, DE)
            (r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*m[³3]\b(?!\/)', "m³"),
            (r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*mc\b(?!\/)', "mc"),
            # Nm³ (DE gas)
            (r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*nm[³3]\b(?!\/)', "Nm³"),
            # MWh (SE, PL, DE)
            (r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*mwh', "MWh"),
        ]

        for pattern, unit in original_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                value = DataCollectorService._parse_number(match.group(1))
                if value is not None and value > 0:
                    consumo_originale = value
                    unita_originale = unit
                    break

        # ── Fallback: Generic kWh con valore >= 10 ────────────
        if consumo_kwh is None:
            generic_kwh = [
                r'(\d{1,3}[.,]\d{3}[.,]?\d*)\s*kwh',
                r'(\d{4,})\s*kwh',
            ]
            for pattern in generic_kwh:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    value = DataCollectorService._parse_number(match.group(1))
                    if value is not None and value >= 10:
                        consumo_kwh = value
                        break

        # ── Se abbiamo consumo_originale in Smc/mc/Nm³ ma non kWh calcolalo ──
        if consumo_kwh is None and consumo_originale is not None and unita_originale in ("Smc", "m³", "mc", "Nm³"):
            # Stima approssimativa: 1 Smc ≈ 10.69 kWh (metano)
            # Nota: in realtà dipende dal potere calorifico, ma usiamo una stima
            if unita_originale == "MWh":
                consumo_kwh = consumo_originale * 1000
            # Per gas, lasciamo kWh = None se non trovato esplicitamente
            # perché il fattore di conversione varia

        return consumo_kwh, consumo_originale, unita_originale

    # ════════════════════════════════════════════════════════════════
    #  TOTAL COST EXTRACTION (multi-currency)
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def _extract_total_cost(text_lower: str, text: str, paese: str) -> Tuple[Optional[float], Optional[str]]:
        """
        Estrae il costo totale e la valuta.
        
        Cerca keyword per lingua:
        - IT: "TOTALE DA PAGARE", "TOTALE FATTURA"
        - ES: "TOTAL A PAGAR", "IMPORTE TOTAL"
        - DE: "Gesamtbetrag", "Rechnungsbetrag"
        - NL: "Totaal te betalen", "Totaalbedrag"
        - UK: "Total amount due", "Total to pay"
        - SE: "Totalt att betala", "Att betala"
        - PL: "Łączna kwota", "Do zapłaty"
        
        Returns:
            (costo, valuta)
        """
        # ── Currency per country ──────────────────────────────
        currency_map = {
            "IT": "EUR", "ES": "EUR", "DE": "EUR", "NL": "EUR",
            "UK": "GBP", "SE": "SEK", "PL": "PLN",
        }
        default_currency = currency_map.get(paese, "EUR")

        # ── Total amount keywords per language ────────────────
        total_patterns = [
            # IT
            r'totale\s+da\s+pagare\s*[:=]?\s*[€e]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'totale\s+fattura\s*[:=]?\s*[€e]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'totale\s+dovuto\s*[:=]?\s*[€e]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'totale\s+documento\s*[:=]?\s*[€e]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'totale\s+complessivo\s*[:=]?\s*[€e]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'importo\s+totale\s*[:=]?\s*[€e]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'importo\s+dovuto\s*[:=]?\s*[€e]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            # ES
            r'total\s+a\s+pagar\s*[:=]?\s*[€e]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'importe\s+total\s*[:=]?\s*[€e]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'total\s+factura\s*[:=]?\s*[€e]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            # DE
            r'gesamtbetrag\s*[:=]?\s*[€e]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'rechnungsbetrag\s*[:=]?\s*[€e]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'rechnungssumme\s*[:=]?\s*[€e]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'zu\s+zahlen\s*[:=]?\s*[€e]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            # NL
            r'totaal\s+te\s+betalen\s*[:=]?\s*[€e]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'totaalbedrag\s*[:=]?\s*[€e]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'totaal\s+factuur\s*[:=]?\s*[€e]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            # UK
            r'total\s+amount\s+due\s*[:=]?\s*[£€]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'total\s+to\s+pay\s*[:=]?\s*[£€]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'total\s+invoice\s*[:=]?\s*[£€]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'amount\s+due\s*[:=]?\s*[£€]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            # SE
            r'totalt\s+att\s+betala\s*[:=]?\s*([\dkr.,\s]+)\s*kr',
            r'att\s+betala\s*[:=]?\s*([\dkr.,\s]+)\s*kr',
            r'totalt\s*[:=]?\s*([\dkr.,\s]+)\s*kr',
            r'belopp\s+att\s+betala\s*[:=]?\s*([\dkr.,\s]+)\s*kr',
            # PL
            r'[łl][aą]czna\s+kwota\s*[:=]?\s*([\d.,\s]+)\s*zł',
            r'do\s+zap[łl]aty\s*[:=]?\s*([\d.,\s]+)\s*zł',
            r'kwota\s+do\s+zap[łl]aty\s*[:=]?\s*([\d.,\s]+)\s*zł',
            r'razem\s*[:=]?\s*([\d.,\s]+)\s*zł',
        ]

        # ── Raccogli tutti i match ────────────────────────────
        all_matches = []
        for pattern in total_patterns:
            for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                val_str = match.group(1).strip()
                # Pulisci spazi interni nei numeri
                val_str = re.sub(r'\s+', '', val_str)
                value = DataCollectorService._parse_number(val_str)
                if value is not None and 1 <= value <= 1000000:
                    all_matches.append((match.start(), value))

        if all_matches:
            # Prendi l'ultimo match (più in basso nel documento = più probabile totale finale)
            all_matches.sort(key=lambda x: x[0], reverse=True)
            return all_matches[0][1], default_currency

        # ── Fallback: pattern con valuta ──────────────────────
        # Simboli di valuta: €, £, kr, zł
        currency_patterns = [
            (r'[€€]\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))', default_currency),
            (r'[££]\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))', "GBP"),
            (r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))\s*kr', "SEK"),
            (r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))\s*zł', "PLN"),
            (r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))\s*zl', "PLN"),
        ]

        currency_matches = []
        for pattern, currency in currency_patterns:
            for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                value = DataCollectorService._parse_number(match.group(1))
                if value is not None and 10 <= value <= 100000:
                    currency_matches.append((match.start(), value, currency))

        if currency_matches:
            currency_matches.sort(key=lambda x: x[0], reverse=True)
            return currency_matches[0][1], currency_matches[0][2]

        # ── Fallback: "euro" / "eur" text ─────────────────────
        euro_matches = list(re.finditer(
            r'(?:euro|eur)\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))',
            text_lower, re.IGNORECASE
        ))
        if euro_matches:
            last_match = euro_matches[-1]
            value = DataCollectorService._parse_number(last_match.group(1))
            if value is not None and 10 <= value <= 100000:
                return value, "EUR"

        return None, default_currency

    # ════════════════════════════════════════════════════════════════
    #  PERIOD EXTRACTION
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def _extract_period(text: str) -> Optional[Tuple[str, str]]:
        """
        Extract billing period start and end dates.
        Supporta formati data in più lingue.
        Returns date strings in gg/mm/aaaa format for _date_to_iso.
        """
        period_patterns = [
            # "Periodo dal ... al ..." (Italian)
            r'periodo\s*(?:di\s*)?(?:riferimento\s*)?(?:dal|dall[ae]?)\s*[:]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*(?:al|a\s*)\s*[:]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            # "dal ... al ..." (generic Italian)
            r'(?<!\w)(?:dal|dall[ae]?)\s*[:]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*(?:al|a\s*)\s*[:]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            # "Dal:" e "Al:" su righe separate
            r'(?:periodo\s*(?:di\s*)?fatturazion[ae]\s*)?\n?dal\s*[:]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\n.*?al\s*[:]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            # "from ... to/until ..." (English)
            r'(?<!\w)(?:from)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*(?:to|until|through)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            # "du ... au ..." (French)
            r'(?<!\w)(?:du)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*(?:au)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            # "vom ... bis ..." (German)
            r'(?<!\w)(?:vom)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*(?:bis)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            # "van ... tot ..." (Dutch)
            r'(?<!\w)(?:van)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*(?:tot|t\/m)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            # Period with generic separator
            r'period(?:o)?\s*[:=]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*[–\-]\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            # Date range with just a dash between two dates
            r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})\s*[–\-]\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})',
            # "Mese" with month name + year (Italian)
            r'mese\s*(?:di\s*)?riferimento\s*[:=]?\s*(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s*(\d{4})',
            # "Month" (English)
            r'month\s*[:=]?\s*(january|february|march|april|may|june|july|august|september|october|november|december|\w+)\s*(\d{4})',
            # "Mes" (Spanish)
            r'mes\s*(?:de\s*)?(?:referencia\s*)?[:=]?\s*(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s*(?:de\s*)?(\d{4})',
            # "Monat" (German)
            r'monat\s*[:=]?\s*(januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember)\s*(\d{4})',
            # "Maand" (Dutch)
            r'maand\s*[:=]?\s*(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s*(\d{4})',
            # "Månad" (Swedish)
            r'm[nåa]nad\s*[:=]?\s*(januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december)\s*(\d{4})',
            # "Miesiąc" (Polish)
            r'miesi[ąa]c\s*[:=]?\s*(stycze[ńn]|luty|marzec|kwiecie[ńn]|maj|czerwiec|lipiec|sierpie[ńn]|wrzesie[ńn]|pa[źz]dziernik|listopad|grudzie[ńn])\s*(\d{4})',
        ]

        month_map_it = {
            'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4,
            'maggio': 5, 'giugno': 6, 'luglio': 7, 'agosto': 8,
            'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12,
        }
        month_map_en = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
        }
        month_map_es = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
        }
        month_map_de = {
            'januar': 1, 'februar': 2, 'märz': 3, 'april': 4,
            'mai': 5, 'juni': 6, 'juli': 7, 'august': 8,
            'september': 9, 'oktober': 10, 'november': 11, 'dezember': 12,
        }
        month_map_nl = {
            'januari': 1, 'februari': 2, 'maart': 3, 'april': 4,
            'mei': 5, 'juni': 6, 'juli': 7, 'augustus': 8,
            'september': 9, 'oktober': 10, 'november': 11, 'december': 12,
        }
        month_map_sv = {
            'januari': 1, 'februari': 2, 'mars': 3, 'april': 4,
            'maj': 5, 'juni': 6, 'juli': 7, 'augusti': 8,
            'september': 9, 'oktober': 10, 'november': 11, 'december': 12,
        }
        month_map_pl = {
            'styczeń': 1, 'styczen': 1, 'luty': 2, 'marzec': 3,
            'kwiecień': 4, 'kwiecien': 4, 'maj': 5, 'czerwiec': 6,
            'lipiec': 7, 'sierpień': 8, 'sierpien': 8,
            'wrzesień': 9, 'wrzesien': 9,
            'październik': 10, 'pazdziernik': 10,
            'listopad': 11, 'grudzień': 12, 'grudzien': 12,
        }

        # Unisci tutte le mappe dei mesi
        all_month_maps = {
            **month_map_it, **month_map_en, **month_map_es,
            **month_map_de, **month_map_nl, **month_map_sv, **month_map_pl,
        }

        for pattern in period_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                # Pattern con mese testuale
                if len(groups) == 2 and not re.match(r'^\d', groups[0].strip()):
                    month_name = groups[0].strip().lower()
                    year = int(groups[1])
                    month = all_month_maps.get(month_name)
                    if month:
                        start = f"01/{month:02d}/{year}"
                        last_day = calendar.monthrange(year, month)[1]
                        end = f"{last_day:02d}/{month:02d}/{year}"
                        return (start, end)
                else:
                    start = groups[0]
                    end = groups[1] if len(groups) > 1 and groups[1] else None

                    start = start.replace("-", "/").replace(".", "/")
                    
                    if end:
                        end = end.replace("-", "/").replace(".", "/")
                        return (start, end)
                    else:
                        # Single date: estimate end as end of month
                        try:
                            parts = start.split("/")
                            if len(parts) == 3:
                                dt = datetime(
                                    int(parts[2]) if len(parts[2]) == 4 else 2000 + int(parts[2]),
                                    int(parts[1]), int(parts[0])
                                )
                                last_day = calendar.monthrange(dt.year, dt.month)[1]
                                end_str = f"{last_day:02d}/{dt.month:02d}/{dt.year}"
                                return (start, end_str)
                        except (ValueError, IndexError):
                            pass
                        return (start, start)

        return None

    @staticmethod
    def _date_to_iso(date_str: str) -> Optional[str]:
        """Converte data in formato gg/mm/aaaa → YYYY-MM-DD ISO."""
        if not date_str:
            return None
        try:
            parts = date_str.replace("-", "/").replace(".", "/").split("/")
            if len(parts) == 3:
                day = int(parts[0])
                month = int(parts[1])
                year = int(parts[2])
                if year < 100:
                    year += 2000
                dt = datetime(year, month, day)
                return dt.strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            pass
        return None

    # ════════════════════════════════════════════════════════════════
    #  METER CODE EXTRACTION (country-specific)
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def _extract_meter_code(text: str, paese: Optional[str]) -> Optional[str]:
        """
        Estrae il codice utenza specifico per paese.
        
        - IT: POD (IT001E...) / PDR (IT...)
        - ES: CUPS (ES...)
        - DE: MaLo-ID (11 cifre)
        - NL: EAN (18 cifre)
        - UK: MPAN (13 cifre) / MPRN (10 cifre)
        - SE: MELO / MPID
        - PL: PPE
        """
        if not paese:
            # Prova tutti i formati
            for p in ["IT", "ES", "DE", "NL", "UK", "SE", "PL"]:
                code = DataCollectorService._extract_meter_code(text, p)
                if code:
                    return code
            return None

        if paese == "IT":
            return DataCollectorService._extract_it_code(text)
        elif paese == "ES":
            return DataCollectorService._extract_es_code(text)
        elif paese == "DE":
            return DataCollectorService._extract_de_code(text)
        elif paese == "NL":
            return DataCollectorService._extract_nl_code(text)
        elif paese == "UK":
            return DataCollectorService._extract_uk_code(text)
        elif paese == "SE":
            return DataCollectorService._extract_se_code(text)
        elif paese == "PL":
            return DataCollectorService._extract_pl_code(text)

        return None

    @staticmethod
    def _extract_it_code(text: str) -> Optional[str]:
        """Estrae POD (elettricità) o PDR (gas) da bollette italiane."""
        # Normalizza OCR: l→1, O→0, I→1 in contesti tecnici
        text_lower = text.lower()

        patterns = [
            # "Codice POD:" / "Codice PDR:" patterns
            r'(?:codice\s+)?(?:pod|pdr)\s*[:;=]\s*([a-z0-9]{6,})',
            r'(?<!\w)(?:pod|pdr)\s*[:;]\s*([a-z0-9]{6,})',
            # Italian format ITxxxE... (POD) or ITxxxG... (PDR)
            r'(it\d{3,}[a-z]\d+)',
            # "Punto di riconsegna"
            r'punto\s+di\s+riconsegna\s*[:;=]?\s*([a-z0-9]{6,})',
            # "POD " or "PDR " followed by code
            r'(?:pod|pdr)\s+([a-z0-9]{6,})',
            # Meter / contatore
            r'(?:meter|matricola|contatore)\s*[:;=]?\s*([a-z0-9]{5,})',
            r'n[°o]\s*(?:matricola|contatore)\s*[:;=]?\s*([a-z0-9]{5,})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                code = match.group(1) if match.lastindex and match.group(1) else match.group(0)
                code = code.strip().upper()
                if len(code) >= 5:
                    return code

        return None

    @staticmethod
    def _extract_es_code(text: str) -> Optional[str]:
        """Estrae CUPS (20-22 caratteri, inizia con ES) da bollette spagnole."""
        text_lower = text.lower()

        patterns = [
            r'(?:cups|codigo\s+cup)\s*[:;=]\s*([a-z0-9]{6,})',
            r'(?:cups|codigo\s+cup)\s+([a-z0-9]{6,})',
            r'(es\d{4,}[a-z0-9]{5,})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                code = match.group(1).strip().upper()
                if len(code) >= 5:
                    return code

        return None

    @staticmethod
    def _extract_de_code(text: str) -> Optional[str]:
        """Estrae MaLo-ID (11 cifre) da bollette tedesche."""
        patterns = [
            r'(?:malo[-\s]?id|z[äa]hlernummer|malo)\s*[:;=]?\s*(\d{11})',
            r'(?:malo[-\s]?id|z[äa]hlernummer|malo)\s+(\d{11})',
            r'\b(\d{11})\b',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(1).strip()
                if len(code) == 11 and code.isdigit():
                    return code

        return None

    @staticmethod
    def _extract_nl_code(text: str) -> Optional[str]:
        """Estrae EAN (18 cifre) da bollette olandesi."""
        patterns = [
            r'(?:ean\s*(?:code|nummer)?)\s*[:;=]?\s*(\d{18})',
            r'(?:ean\s*(?:code|nummer)?)\s+(\d{18})',
            r'\b(\d{18})\b',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(1).strip()
                if len(code) == 18 and code.isdigit():
                    return f"EAN{code}"

        return None

    @staticmethod
    def _extract_uk_code(text: str) -> Optional[str]:
        """Estrae MPAN (13 cifre, elettricità) o MPRN (10 cifre, gas) da bollette UK."""
        text_lower = text.lower()

        # MPAN (electricity, 13 digits)
        mpan_patterns = [
            r'(?:mpan|supply\s+number|meter\s+point)\s*[:;=]?\s*(\d{13})',
            r'(?:mpan|supply\s+number|meter\s+point)\s+(\d{13})',
            r'\b(\d{13})\b(?!.*\b\d{10}\b)',
        ]
        for pattern in mpan_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(1).strip()
                if len(code) == 13 and code.isdigit():
                    return f"MPAN{code}"

        # MPRN (gas, 10 digits)
        mprn_patterns = [
            r'(?:mprn|meter\s+point\s+ref|mpr)\s*[:;=]?\s*(\d{10})',
            r'(?:mprn|meter\s+point\s+ref|mpr)\s+(\d{10})',
            r'\b(\d{10})\b',
        ]
        for pattern in mprn_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(1).strip()
                if len(code) == 10 and code.isdigit():
                    return f"MPRN{code}"

        return None

    @staticmethod
    def _extract_se_code(text: str) -> Optional[str]:
        """Estrae MELO o MPID da bollette svedesi."""
        patterns = [
            r'(?:melo|mpid)\s*[:;=]?\s*([a-z0-9]{5,})',
            r'(?:melo|mpid)\s+([a-z0-9]{5,})',
            r'\b(melo\d{4,})\b',
            r'\b(mpid\d{4,})\b',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(1).strip().upper()
                if len(code) >= 5:
                    return code

        return None

    @staticmethod
    def _extract_pl_code(text: str) -> Optional[str]:
        """Estrae PPE da bollette polacche."""
        patterns = [
            r'(?:ppe|punkt\s+poboru\s+energii)\s*[:;=]?\s*([a-z0-9]{5,})',
            r'(?:ppe|punkt\s+poboru\s+energii)\s+([a-z0-9]{5,})',
            r'\b(\d{5,})\b',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(1).strip().upper()
                if len(code) >= 5:
                    return f"PPE{code}" if not code.startswith("PPE") else code

        return None

    # ════════════════════════════════════════════════════════════════
    #  ESTIMATED READING DETECTION
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def _detect_estimated_reading(text_lower: str) -> bool:
        """
        Rileva se la lettura è stimata (true) o effettiva (false).
        
        Cerca keyword per lingua:
        - IT: "stimata", "calcolata", "presunta", "letta stimata"
        - ES: "estimada", "calculada", "lectura estimada"
        - DE: "geschätzt", "errechnet", "hochgerechnet", "Schätzung"
        - NL: "geschat", "berekend", "geschatte"
        - UK: "estimated", "calculated", "est."
        - SE: "beräknad", "uppskattad", "estim."
        - PL: "szacowane", "obliczone", "szacunkowe"
        """
        estimated_kw = [
            "stimata", "calcolata", "presunta", "calcolato", "stimato",
            "letta stimata", "stima",
            "estimada", "calculada", "lectura estimada", "lectura calculada",
            "geschätzt", "errechnet", "hochgerechnet", "schätzung", "schätzwert",
            "geschat", "berekend", "geschatte", "berekende",
            "estimated", "calculated", "est.", "estimated reading",
            "beräknad", "uppskattad", "estim.", "beräknad avläsning",
            "szacowane", "obliczone", "szacunkowe", "odczyt szacunkowy",
        ]

        for kw in estimated_kw:
            if kw in text_lower:
                return True

        return False

    # ════════════════════════════════════════════════════════════════
    #  LEGACY METHODS (unchanged)
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def process_accounting_data(
        transactions: List[Dict],
        nace_code: str,
    ) -> Dict[str, Any]:
        """
        Processa dati contabili da XERO/QuickBooks per calcolo spend-based.
        
        Input: lista di transazioni con {category, amount_eur, description, date}
        Output: spese aggregate per categoria NACE
        """
        # Mapping from accounting categories to NACE codes
        CATEGORY_MAP = {
            "raw_materials": "C",
            "office_supplies": "M69",
            "it_services": "J62",
            "consulting": "M70",
            "travel": "H",
            "logistics": "H49",
            "rent": "L",
            "utilities": "D35",
            "marketing": "M73",
            "insurance": "K65",
            "maintenance": "F43",
            "legal": "M69",
            "training": "P85",
            "catering": "I56",
            "security": "N80",
            "cleaning": "N81",
            "telecom": "J61",
            "hardware": "C26",
            "software": "J62",
            "packaging": "C17",
            "transport": "H49",
        }

        total_spend = 0.0
        spend_by_category: Dict[str, float] = {}
        aggregated_categories: Dict[str, dict] = {}

        for tx in transactions:
            amount = tx.get("amount_eur", 0)
            category = tx.get("category", "").lower()
            description = tx.get("description", "")
            tx_date = tx.get("date", "")

            total_spend += amount

            mapped_nace = CATEGORY_MAP.get(category, nace_code)
            spend_by_category[mapped_nace] = (
                spend_by_category.get(mapped_nace, 0) + amount
            )

            # Track by accounting category too
            if category:
                if category not in aggregated_categories:
                    aggregated_categories[category] = {
                        "nace_code": mapped_nace,
                        "total_spend_eur": 0,
                        "transaction_count": 0,
                    }
                aggregated_categories[category]["total_spend_eur"] += amount
                aggregated_categories[category]["transaction_count"] += 1

        return {
            "total_spend_eur": round(total_spend, 2),
            "transaction_count": len(transactions),
            "spend_by_nace": spend_by_category,
            "spend_by_accounting_category": aggregated_categories,
            "method": "accounting_integration",
            "integration_type": "xero_quickbooks",
        }

    @staticmethod
    def process_hr_data(
        employee_count: int,
        full_time_pct: float = 100.0,
        remote_workers_pct: float = 0.0,
        avg_commute_km: float = 20.0,
        commuting_mode: str = "car_alone",
    ) -> Dict[str, Any]:
        """
        Processa dati HR per calcoli commuting e workforce.
        """
        full_time = int(employee_count * full_time_pct / 100)
        part_time = employee_count - full_time
        remote_workers = int(employee_count * remote_workers_pct / 100)
        on_site = employee_count - remote_workers

        return {
            "employee_count": employee_count,
            "full_time": full_time,
            "part_time": part_time,
            "remote_workers_pct": remote_workers_pct,
            "remote_workers": remote_workers,
            "on_site_workers": on_site,
            "avg_commute_km": avg_commute_km,
            "commuting_mode": commuting_mode,
            "estimated_commuting_annual_km": on_site * avg_commute_km * 220,
            "method": "hr_integration",
        }

    @staticmethod
    def process_fleet_data(
        vehicles: List[Dict],
    ) -> Dict[str, Any]:
        """
        Processa dati flotta aziendale.
        
        Input esempio:
        [
            {"type": "diesel_car", "count": 5, "annual_km_per_vehicle": 15000},
            {"type": "electric_car", "count": 2, "annual_km_per_vehicle": 12000},
        ]
        """
        total_km = 0
        fleet_summary = []
        fuel_totals: Dict[str, float] = {}

        for v in vehicles:
            v_type = v.get("type", "unknown")
            count = v.get("count", 1)
            km_per_vehicle = v.get("annual_km_per_vehicle", 10000)
            fuel_type = v.get("fuel_type", v_type.split("_")[0] if "_" in v_type else "unknown")
            total_vehicle_km = count * km_per_vehicle
            total_km += total_vehicle_km

            fleet_summary.append({
                "type": v_type,
                "fuel_type": fuel_type,
                "count": count,
                "annual_km_per_vehicle": km_per_vehicle,
                "total_annual_km": total_vehicle_km,
            })

            if fuel_type:
                fuel_totals[fuel_type] = fuel_totals.get(fuel_type, 0) + total_vehicle_km

        return {
            "total_vehicles": sum(v.get("count", 1) for v in vehicles),
            "total_annual_km": total_km,
            "fleet_breakdown": fleet_summary,
            "km_by_fuel_type": fuel_totals,
            "method": "fleet_integration",
        }

    @staticmethod
    def integrate_utility_provider_api(
        api_response: Dict[str, Any],
        provider: str = "generic",
    ) -> Dict[str, Any]:
        """
        Integra dati da API di fornitori energia.
        
        Supporta formati standardizzati per provider EU:
        - electricity: consumo attivo kWh, prezzo, periodo
        - gas: consumo Smc/m³, potere calorifico, periodo
        
        Provider supportati: generic, enel, edf, eon, iberdrola, engie
        """
        result = {
            "success": False,
            "provider": provider,
            "bill_type": None,
            "consumption_kwh": None,
            "consumption_smc": None,
            "period_start": None,
            "period_end": None,
            "total_cost_eur": None,
            "contract_type": None,  # fixed, variable, green
            "pod_pdr": None,
            "data_points": [],
        }

        if not api_response:
            return result

        # Try to extract from various API response formats
        data = api_response.get("data", api_response)

        # Consumption
        consumption = (
            data.get("consumption_kwh") or
            data.get("consumption") or
            data.get("total_consumption") or
            data.get("energy_consumption")
        )
        if consumption:
            result["consumption_kwh"] = float(consumption)

        # Bill type
        raw_data = json.dumps(data).lower()
        if any(kw in raw_data for kw in ["electricity", "elettricità", "energia"]):
            result["bill_type"] = "electricity"
        elif any(kw in raw_data for kw in ["gas", "natural_gas"]):
            result["bill_type"] = "gas"

        # Cost
        cost = (
            data.get("total_cost") or
            data.get("amount") or
            data.get("total_amount") or
            data.get("price")
        )
        if cost:
            result["total_cost_eur"] = float(cost)

        # Period
        result["period_start"] = data.get("period_start") or data.get("from_date")
        result["period_end"] = data.get("period_end") or data.get("to_date")

        # Contract type
        contract = data.get("contract_type", "").lower()
        if "green" in contract or "renewable" in contract or "verde" in contract:
            result["contract_type"] = "green"
        elif "fixed" in contract:
            result["contract_type"] = "fixed"
        else:
            result["contract_type"] = "variable"

        # POD/PDR
        result["pod_pdr"] = data.get("pod") or data.get("pdr") or data.get("meter_id")

        result["success"] = result["consumption_kwh"] is not None

        # Add monthly data points if available
        if "monthly_data" in data:
            result["data_points"] = data["monthly_data"]

        return result

    @staticmethod
    def process_csv_upload(
        csv_data: List[Dict[str, str]],
        data_type: str = "transactions",
    ) -> Dict[str, Any]:
        """
        Processa dati caricati tramite CSV upload.
        
        Tipi supportati:
        - "transactions": spese contabili
        - "fleet": dati flotta
        - "energy": consumi energetici
        - "waste": dati rifiuti
        - "travel": viaggi di lavoro
        """
        result = {
            "success": False,
            "data_type": data_type,
            "records_processed": 0,
            "total_amount_eur": 0.0,
            "records": [],
        }

        if not csv_data:
            return result

        records = []
        total_amount = 0.0

        for row in csv_data:
            record = {}
            if data_type == "transactions":
                amount = float(row.get("amount_eur", row.get("amount", row.get("importo", 0))))
                record = {
                    "category": row.get("category", row.get("categoria", "other")),
                    "amount_eur": amount,
                    "description": row.get("description", row.get("descrizione", "")),
                    "date": row.get("date", row.get("data", "")),
                }
                total_amount += amount

            elif data_type == "fleet":
                record = {
                    "type": row.get("type", row.get("tipo", "car")),
                    "count": int(float(row.get("count", row.get("numero", 1)))),
                    "annual_km_per_vehicle": float(row.get("km_per_vehicle", row.get("km_annui", 10000))),
                    "fuel_type": row.get("fuel_type", row.get("carburante", "diesel")),
                }

            elif data_type == "energy":
                record = {
                    "month": row.get("month", row.get("mese", "")),
                    "consumption_kwh": float(row.get("consumption_kwh", row.get("consumo", 0))),
                    "cost_eur": float(row.get("cost_eur", row.get("costo", 0))),
                    "type": row.get("type", row.get("tipo", "electricity")),
                }
                total_amount += record["cost_eur"]

            records.append(record)

        result["records_processed"] = len(records)
        result["total_amount_eur"] = round(total_amount, 2)
        result["records"] = records
        result["success"] = len(records) > 0

        return result

    @staticmethod
    def process_bank_data(
        transactions: List[Dict],
        nace_code: str,
    ) -> Dict[str, Any]:
        """
        Processa transazioni bancarie (estratto conto) per mapping spese.
        
        Cerca nelle descrizioni delle transazioni parole chiave
        per mappare automaticamente le spese a categorie NACE.
        """
        KEYWORD_MAP = [
            (r'(elettric|enel|edf|eon|energia|gas)', "utilities", "D35"),
            (r'(affitto|rent|locazione|lease)', "rent", "L"),
            (r'(consulenza|consulting|advisor)', "consulting", "M70"),
            (r'(software|cloud|server|hosting|saas)', "it_services", "J62"),
            (r'(assicurazion|insurance)', "insurance", "K65"),
            (r'(manutenzion|maintenance|riparazion|repair)', "maintenance", "F43"),
            (r'(marketing|pubblicità|advertising|pubblicita)', "marketing", "M73"),
            (r'(trasporto|transport|spedizione|shipping|logistic)', "logistics", "H49"),
            (r'(forniture|office|supplies|cancelleria)', "office_supplies", "M69"),
            (r'(formazione|training|corso|course)', "training", "P85"),
            (r'(viaggio|travel|hotel|volo|flight|albergo)', "travel", "H"),
            (r'(materie prime|raw material|componenti)', "raw_materials", "C"),
        ]

        mapped = []
        unmapped = []
        total_spend = 0.0

        for tx in transactions:
            description = tx.get("description", tx.get("descrizione", "")).lower()
            amount = abs(float(tx.get("amount_eur", tx.get("amount", 0))))
            total_spend += amount

            matched = False
            for pattern, category, nace in KEYWORD_MAP:
                if re.search(pattern, description):
                    mapped.append({
                        "description": tx.get("description", ""),
                        "amount_eur": amount,
                        "date": tx.get("date", tx.get("data", "")),
                        "category": category,
                        "nace_code": nace,
                    })
                    matched = True
                    break

            if not matched:
                unmapped.append({
                    "description": tx.get("description", ""),
                    "amount_eur": amount,
                    "date": tx.get("date", tx.get("data", "")),
                })

        return {
            "total_transactions": len(transactions),
            "mapped": len(mapped),
            "unmapped": len(unmapped),
            "total_spend_eur": round(total_spend, 2),
            "mapped_spend_eur": round(sum(t["amount_eur"] for t in mapped), 2),
            "unmapped_spend_eur": round(sum(t["amount_eur"] for t in unmapped), 2),
            "mapped_transactions": mapped,
            "unmapped_transactions": unmapped,
            "method": "bank_integration",
            "mapping_coverage_pct": round(len(mapped) / len(transactions) * 100, 1) if transactions else 0,
        }

    @staticmethod
    def get_integration_options() -> Dict[str, Any]:
        """Restituisce le opzioni di integrazione disponibili."""
        return {
            "accounting": {
                "name": "Contabilità",
                "providers": ["XERO", "QuickBooks", "SAP", "Zoho Books"],
                "description": "Importa spese per calcolo spend-based Scope 3",
            },
            "utility_provider": {
                "name": "Fornitore Energia",
                "providers": ["Enel", "EDF", "E.ON", "Iberdrola", "Engie", "Altro"],
                "description": "Importa consumi elettricità e gas da API fornitore",
            },
            "hr": {
                "name": "HR / Payroll",
                "providers": ["Manual input", "CSV upload"],
                "description": "Dati dipendenti per calcolo commuting Scope 3 Cat.7",
            },
            "fleet": {
                "name": "Flotta Aziendale",
                "providers": ["Manual input", "CSV upload", "API telematics"],
                "description": "Dati veicoli per calcolo Scope 1 mobile combustion",
            },
            "bank": {
                "name": "Banca / Estratto Conto",
                "providers": ["CSV upload", "CAMT.053 (ISO 20022)"],
                "description": "Importa transazioni bancarie per mapping spese automatico",
            },
            "waste": {
                "name": "Rifiuti",
                "providers": ["Manual input", "CSV upload"],
                "description": "Dati rifiuti per calcolo Scope 3 Cat.5",
            },
            "travel": {
                "name": "Viaggi Aziendali",
                "providers": ["Manual input", "CSV upload", "Expense report API"],
                "description": "Dati viaggi per calcolo Scope 3 Cat.6",
            },
        }
