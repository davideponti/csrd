"""
CSRD Comply — Data Collection Automation System (Step 15)

Sistema di raccolta automatica dati per emissioni.
Include: XERO/QuickBooks integration, PDF OCR, HR data, fleet data,
utility provider API, banking data import.
"""
from typing import Optional, Dict, Any, List, Tuple
import json
import re
from datetime import datetime, date


class DataCollectorService:
    """Servizio di raccolta dati automatica per emissioni."""

    @staticmethod
    def parse_utility_bill_pdf_text(
        extracted_text: str,
    ) -> Dict[str, Any]:
        """
        Estrae dati da testo di bolletta elettrica/gas.
        Usato dopo OCR su PDF caricato dall'utente.
        
        Supporto multilingua: IT, EN, FR, DE, ES.
        
        Migliorato con estrazione context-aware:
        - Cerca valori associati a keyword specifiche (consumo, energia attiva, totale fattura)
        - Evita falsi positivi (potere calorifico, numeri contatore, ecc.)
        - Supporta formato data italiano (gg/mm/aaaa)
        - Riconosce fornitori italiani per nome diretto
        """
        result = {
            "success": False,
            "provider": None,
            "consumption_kwh": None,
            "consumption_smc": None,
            "period_start": None,
            "period_end": None,
            "total_cost_eur": None,
            "bill_type": None,  # electricity or gas
            "meter_number": None,
            "pod_pdr_code": None,
            "confidence": 0.0,
            "raw_text_snippet": extracted_text[:200] if extracted_text else "",
        }

        if not extracted_text:
            return result

        text = extracted_text.lower()

        # ── Detect bill type (multilingual) ────────────────────────
        electricity_kw = ["electricità", "elettrica", "electricity", "energia elettrica",
                         "electricité", "strom", "electrische", "electricidad",
                         "consumo elettrico", "fornitura elettrica"]
        gas_kw = ["gas", "gas naturale", "metano", "natural gas", "gaz naturel",
                  "erdgas", "aardgas", "consumo gas", "fornitura gas",
                  "smc", "standard metri cubi"]

        if any(kw in text for kw in electricity_kw):
            result["bill_type"] = "electricity"
        elif any(kw in text for kw in gas_kw):
            result["bill_type"] = "gas"

        # ── Extract PROVIDER (context-aware, not just "Fornitore:" prefix) ──
        provider = DataCollectorService._extract_provider(text, extracted_text)
        if provider:
            result["provider"] = provider
            result["confidence"] += 0.15

        # ── Extract CONSUMPTION (prioritized, context-aware) ───────
        consumption = DataCollectorService._extract_consumption(text, result["bill_type"])
        if consumption is not None:
            result["consumption_kwh"] = consumption
            result["confidence"] += 0.35

        # ── Extract SMC (gas bills often report Smc) ───────────────
        smc = DataCollectorService._extract_smc(text)
        if smc is not None:
            result["consumption_smc"] = smc

        # ── Extract TOTAL COST (prioritized by relevance) ──────────
        cost = DataCollectorService._extract_total_cost(text)
        if cost is not None:
            result["total_cost_eur"] = cost
            result["confidence"] += 0.25

        # ── Extract PERIOD (support dd/mm/yyyy Italian format) ─────
        period = DataCollectorService._extract_period(text)
        if period:
            result["period_start"] = period[0]
            result["period_end"] = period[1]
            result["confidence"] += 0.2

        # ── Extract POD/PDR ────────────────────────────────────────
        meter = DataCollectorService._extract_pod_pdr(text)
        if meter:
            result["pod_pdr_code"] = meter

        result["success"] = result["confidence"] > 0.3
        return result

    @staticmethod
    def _extract_provider(text: str, original_text: str) -> Optional[str]:
        """
        Extract provider name using multiple strategies:
        1. Specific Italian energy company names
        2. "Fornitore:" / "Provider:" prefix patterns
        3. Company/società keywords
        """
        # Strategy 1: Direct Italian energy company names
        italian_providers = [
            (r'\benel\s+energia\b', "Enel Energia"),
            (r'\benel\b(?!\s+energia)', "Enel"),
            (r'\b(?:ed[.]?\s*)?(?:en|n)el\b', "Enel"),
            (r'\bacea\b', "Acea"),
            (r'\ba[.]?2[.]?a\b', "A2A"),
            (r'\bher\s*comm\b', "Hera Comm"),
            (r'\bi[.]?ren\b', "Iren"),
            (r'\bsorgenia\b', "Sorgenia"),
            (r'\bengie\b', "Engie"),
            (r'\bedf\b', "EDF"),
            (r'\be[.]?on\b', "E.ON"),
            (r'\biberdrola\b', "Iberdrola"),
            (r'\bwekiwi\b', "Wekiwi"),
            (r'\bneN\b', "NeN"),
            (r'\bplenitude\b', "Plenitude"),
            (r'\b[ée]lectricit[ée]\s+de\s+france\b', "EDF"),
            (r'\bgas\s+natural\s+fenosa\b', "Gas Natural Fenosa"),
            (r'\bendesa\b', "Endesa"),
            (r'\bnaturgy\b', "Naturgy"),
            (r'\brepsol\b', "Repsol"),
            (r'\bcepsa\b', "Cepsa"),
            (r'\bfactorenergia\b', "Factorenergia"),
            (r'\btotalenergies\b', "TotalEnergies"),
            (r'\bshell\s+energy\b', "Shell Energy"),
            (r'\bbritish\s+gas\b', "British Gas"),
            (r'\bovo\s+energy\b', "OVO Energy"),
            (r'\beon\s+next\b', "E.ON Next"),
            (r'\bscottish\s+power\b', "Scottish Power"),
        ]
        
        for pattern, name in italian_providers:
            if re.search(pattern, text, re.IGNORECASE):
                return name

        # Strategy 2: "Fornitore:" prefix (Italian)
        match = re.search(r'fornitore\s*[:;]\s*([A-Za-zÀ-ÿ\s.]+(?:[A-Za-zÀ-ÿ][.\s][A-Za-zÀ-ÿ]+)*)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Strategy 3: Other language provider patterns
        provider_patterns = [
            r'provider\s*[:;]\s*([A-Za-zÀ-ÿ\s.]+)',
            r'societ[àa]\s*[:;]\s*([A-Za-zÀ-ÿ\s.]+)',
            r'company\s*[:;]\s*([A-Za-zÀ-ÿ\s.]+)',
            r'fournisseur\s*[:;]\s*([A-Za-zÀ-ÿ\s.]+)',
            r'venditore\s*[:;]\s*([A-Za-zÀ-ÿ\s.]+)',
        ]
        for pattern in provider_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Filter out generic words that aren't actual provider names
                if name.lower() not in ['il', 'la', 'le', 'di', 'del', 'della', '-', '']:
                    return name

        return None

    @staticmethod
    def _extract_consumption(text: str, bill_type: Optional[str]) -> Optional[float]:
        """
        Extract consumption in kWh using context-aware strategy.
        
        Priority order:
        1. "Consumo" or "Energia attiva" followed by a large number
        2. "consumo kWh" patterns
        3. Generic kWh patterns (only as fallback, avoid calorific value)
        
        Italian bills often report:
        - "Consumo: 2.525,40 kWh" (actual consumption)
        - "Potere calorifico: 10,35 kWh/Smc" (NOT consumption, skip this)
        - "Energia attiva: 2.525 kWh"
        """
        # High-priority: "consumo" or "energia attiva" followed by kWh value
        # IMPORTANT: exclude values followed by "/Smc" (calorific power ratio, NOT consumption)
        high_priority = [
            r'energia\s+consumata\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh(?!/smc)',
            r'consumo\s*(?:totale\s*)?[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh(?!/smc)',
            r'consumo\s*(?:totale\s*)?[:=]?\s*(\d+[.,]?\d*)\s*kwh(?!/smc)',
            r'energia\s+attiva\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'consumo\s*(?:annuo\s*)?[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh(?!/smc)',
            r'consumption\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh(?!/smc)',
            r'consommation\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*kwh(?!/smc)',
        ]
        
        for pattern in high_priority:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(".", "").replace(",", ".")
                value = float(value_str)
                # Sanity check: consumption should be reasonable (not a tiny calorific value)
                if value >= 100:  # Filter out small values like 10.35 (calorific power)
                    return value
                # If value < 100 but we got here via a specific "consumo" keyword, trust it
                return value

        # Medium-priority: blocks of text containing "consumo" with kWh numbers
        consumo_blocks = re.finditer(r'(?:consumo|consumption|consommation|verbrauch)[^.]*?(\d+[.,]?\d*)\s*kwh', text, re.IGNORECASE)
        values = []
        for match in consumo_blocks:
            value_str = match.group(1).replace(".", "").replace(",", ".")
            values.append(float(value_str))
        if values:
            # Take the largest consumption value (skip small calorific values)
            valid_values = [v for v in values if v >= 100]
            if valid_values:
                return max(valid_values)
            return max(values)

        # Low-priority: generic kWh pattern (potential false positive)
        # Look for numbers with thousands separators (more likely to be real consumption)
        generic_kwh = [
            r'(\d{1,3}[.,]\d{3}[.,]?\d*)\s*kwh',  # e.g., 2.525,40 or 2,525.40
            r'(\d{4,})\s*kwh',  # e.g., 2525 kWh (4+ digits)
        ]
        for pattern in generic_kwh:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(".", "").replace(",", ".")
                value = float(value_str)
                if value >= 100:  # Sanity check
                    return value

        return None

    @staticmethod
    def _extract_smc(text: str) -> Optional[float]:
        """Extract Smc (Standard metro cubo) from gas bills."""
        smc_patterns = [
            r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*smc',
            r'consumo\s*gas\s*[:=]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'(\d+[.,]?\d*)\s*standard\s*metri\s*cubi',
        ]
        for pattern in smc_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(".", "").replace(",", ".")
                return float(value_str)
        return None

    @staticmethod
    def _extract_total_cost(text: str) -> Optional[float]:
        """
        Extract total cost in EUR using prioritized patterns.
        
        Priority:
        1. "Totale fattura" / "Totale da pagare" / "Importo totale"
        2. "Totale" followed by € amount
        3. Last € amount in document (often the final total)
        4. First € amount (least reliable)
        """
        # High priority: explicit total keywords
        total_patterns = [
            r'totale\s*(?:fattura|da\s*pagare|documento|complessivo|netto|finale)?\s*[:=]?\s*[€euro]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'importo\s*(?:totale|complessivo|finale|da\s*pagare|dovuto)?\s*[:=]?\s*[€euro]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'total\s*(?:amount|invoice|due|cost|price|payment)?\s*[:=]?\s*[€euro]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'amount\s*(?:due|payable|total)?\s*[:=]?\s*[€euro]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'montant\s*(?:total|à\s*payer)?\s*[:=]?\s*[€euro]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'gesamtbetrag\s*[:=]?\s*[€euro]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
            r'total\s*[:=]?\s*[€euro]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',
        ]
        
        for pattern in total_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                # Take the LAST match (most likely the final total)
                match = matches[-1]
                value_str = match.group(1).replace(".", "").replace(",", ".")
                value = float(value_str)
                # Sanity check: total cost should be reasonable for a utility bill
                if 10 <= value <= 100000:
                    return value

        # Medium priority: "€" amount that looks like a total (3+ digits before decimal)
        euro_matches = list(re.finditer(r'[€€]\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))', text))
        if euro_matches:
            # Take the LAST € amount (invoices typically end with the total)
            last_match = euro_matches[-1]
            value_str = last_match.group(1).replace(".", "").replace(",", ".")
            value = float(value_str)
            if 10 <= value <= 100000:
                return value

        # Fallback: any "euro" or "eur" pattern
        euro_text_matches = list(re.finditer(r'(?:euro|eur)\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))', text, re.IGNORECASE))
        if euro_text_matches:
            last_match = euro_text_matches[-1]
            value_str = last_match.group(1).replace(".", "").replace(",", ".")
            value = float(value_str)
            if 10 <= value <= 100000:
                return value

        return None

    @staticmethod
    def _extract_period(text: str) -> Optional[Tuple[str, str]]:
        """
        Extract billing period start and end dates.
        Supports Italian date format (gg/mm/aaaa) and many language variants.
        """
        # Italian date formats with various prefix keywords
        period_patterns = [
            # "Periodo dal ... al ..." (Italian)
            r'periodo\s*(?:di\s*)?(?:riferimento\s*)?(?:dal|dall[ae]?)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*(?:al|a\s*)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            # "dal ... al ..." (generic Italian)
            r'(?<!\w)(?:dal|dall[ae]?)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*(?:al|a\s*)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            # "from ... to/until ..." (English)
            r'(?<!\w)(?:from)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*(?:to|until|through)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            # "du ... au ..." (French)
            r'(?<!\w)(?:du)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*(?:au)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            # "vom ... bis ..." (German)
            r'(?<!\w)(?:vom)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*(?:bis)\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            # Period / date range with generic separator
            r'period(?:o)?\s*[:=]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*[–\-]\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            # Date range with just a dash between two dates
            r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})\s*[–\-]\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})',
            # "Mese di riferimento" with single date
            r'mese\s*(?:di\s*)?riferimento\s*[:=]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})',
        ]

        for pattern in period_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                start = groups[0]
                end = groups[1] if len(groups) > 1 and groups[1] else None

                # Normalize date separators to /
                start = start.replace("-", "/").replace(".", "/")
                
                if end:
                    end = end.replace("-", "/").replace(".", "/")
                    return (start, end)
                else:
                    # Single date: estimate end as start + 1 month
                    try:
                        parts = start.split("/")
                        if len(parts) == 3:
                            from datetime import datetime
                            dt = datetime(int(parts[2]) if len(parts[2]) == 4 else 2000 + int(parts[2]),
                                          int(parts[1]), int(parts[0]))
                            # Estimate period end as end of month
                            import calendar
                            last_day = calendar.monthrange(dt.year, dt.month)[1]
                            end_str = f"{last_day:02d}/{dt.month:02d}/{dt.year}"
                            return (start, end_str)
                    except:
                        pass
                    return (start, start)

        return None

    @staticmethod
    def _extract_pod_pdr(text: str) -> Optional[str]:
        """Extract POD (electricity) or PDR (gas) code from Italian bills."""
        # Common Italian POD/PDR formats: ITxxxE... or numbers
        pod_pdr_patterns = [
            r'(?:pod|pdr)\s*[:;=]?\s*([a-z0-9]{6,})',
            r'(?:codice\s*(?:pod|pdr))\s*[:;=]?\s*([a-z0-9]{6,})',
            r'it\d{3,}[a-z]\d+',  # Italian format IT001E12345...
            r'(?:meter|matricola|contatore)\s*[:;=]?\s*([a-z0-9]{5,})',
            r'n[°o]\s*(?:matricola|contatore)\s*[:;=]?\s*([a-z0-9]{5,})',
        ]
        for pattern in pod_pdr_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(0) if match.group(0) != match.group(1) else match.group(1)
                # For the ITxxx pattern, the whole match is the code
                if re.match(r'it\d{3,}', code, re.IGNORECASE):
                    return code.upper()
                return match.group(1).upper()
        return None

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

        provider_map = {
            "enel": ["enel", "enel energia", "enel italia"],
            "edf": ["edf", "edf france"],
            "eon": ["eon", "eon germany"],
            "iberdrola": ["iberdrola", "iberdrola espana"],
            "engie": ["engie", "engie france"],
        }

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
