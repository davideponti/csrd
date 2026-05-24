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
        """
        result = {
            "success": False,
            "provider": None,
            "consumption_kwh": None,
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

        # Detect bill type (multilingual)
        electricity_kw = ["electricità", "elettrica", "electricity", "energia elettrica",
                         "electricité", "strom", "electrische", "electricidad"]
        gas_kw = ["gas", "gas naturale", "metano", "natural gas", "gaz naturel",
                  "erdgas", "aardgas"]

        if any(kw in text for kw in electricity_kw):
            result["bill_type"] = "electricity"
        elif any(kw in text for kw in gas_kw):
            result["bill_type"] = "gas"

        # Extract consumption (kWh) - various formats
        kwh_patterns = [
            r'(\d+[.,]?\d*)\s*kwh',
            r'consumo\s*[:]?\s*(\d+[.,]?\d*)\s*kwh',
            r'energia\s*attiva\s*[:]?\s*(\d+[.,]?\d*)',
            r'consumption\s*[:]?\s*(\d+[.,]?\d*)\s*kwh',
            r'consommation\s*[:]?\s*(\d+[.,]?\d*)\s*kwh',
        ]
        for pattern in kwh_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(",", ".")
                result["consumption_kwh"] = float(value)
                result["confidence"] += 0.3
                break

        # Extract total cost (EUR)
        cost_patterns = [
            r'totale\s*[:]?\s*[€euro]?\s*(\d+[.,]?\d*)',
            r'total\s*[:]?\s*[€euro]?\s*(\d+[.,]?\d*)',
            r'importo\s*[:]?\s*[€euro]?\s*(\d+[.,]?\d*)',
            r'€\s*(\d+[.,]?\d*)',
            r'eur\s*(\d+[.,]?\d*)',
        ]
        for pattern in cost_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(",", ".")
                result["total_cost_eur"] = float(value)
                result["confidence"] += 0.2
                break

        # Extract provider name
        provider_patterns = [
            r'fornitore\s*[:]?\s*([A-Za-z\s.]+)',
            r'provider\s*[:]?\s*([A-Za-z\s.]+)',
            r'società\s*[:]?\s*([A-Za-z\s.]+)',
            r'company\s*[:]?\s*([A-Za-z\s.]+)',
            r'fournisseur\s*[:]?\s*([A-Za-z\s.]+)',
        ]
        for pattern in provider_patterns:
            match = re.search(pattern, text)
            if match:
                result["provider"] = match.group(1).strip()
                result["confidence"] += 0.1
                break

        # Extract period
        period_patterns = [
            r'periodo\s*dal\s*(\d{2}[/-]\d{2}[/-]\d{4})\s*al\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'dal\s*(\d{2}[/-]\d{2}[/-]\d{4})\s*al\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'from\s*(\d{2}[/-]\d{2}[/-]\d{4})\s*to\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'period\s*(\d{2}[/-]\d{2}[/-]\d{4})\s*-\s*(\d{2}[/-]\d{2}[/-]\d{4})',
        ]
        for pattern in period_patterns:
            match = re.search(pattern, text)
            if match:
                result["period_start"] = match.group(1)
                result["period_end"] = match.group(2)
                result["confidence"] += 0.2
                break

        # Extract meter number / POD / PDR
        meter_patterns = [
            r'(?:pod|pdr)\s*[:]?\s*([a-z0-9]{6,})',
            r'(?:meter|matricola)\s*[:]?\s*([a-z0-9]{5,})',
        ]
        for pattern in meter_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if not result.get("pod_pdr_code"):
                    result["pod_pdr_code"] = match.group(1).upper()
                    result["confidence"] += 0.1
                break

        result["success"] = result["confidence"] > 0.3
        return result

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
