"""
CSRD Comply — AI Validation Engine per Dati Emissioni (Step 16)

Validazione automatica dei dati con range check, benchmark, e anomaly detection.
"""
from typing import Optional, Dict, Any, List
from statistics import mean, stdev

# ── Benchmark di settore (kgCO2e/dipendente per anno) ──────────
# Fonte: dataset aggregato anonimizzato di PMI europee
SECTOR_BENCHMARKS: Dict[str, Dict[str, float]] = {
    "C": {  # Manufacturing
        "scope1_per_employee": 2500.0,
        "scope2_per_employee": 1800.0,
        "scope3_per_employee": 8500.0,
    },
    "M": {  # Professional Services
        "scope1_per_employee": 400.0,
        "scope2_per_employee": 600.0,
        "scope3_per_employee": 2500.0,
    },
    "H": {  # Logistics
        "scope1_per_employee": 4500.0,
        "scope2_per_employee": 1200.0,
        "scope3_per_employee": 12000.0,
    },
    "A": {  # Agriculture
        "scope1_per_employee": 5500.0,
        "scope2_per_employee": 800.0,
        "scope3_per_employee": 6000.0,
    },
    "F": {  # Construction
        "scope1_per_employee": 3000.0,
        "scope2_per_employee": 1000.0,
        "scope3_per_employee": 9000.0,
    },
    "G": {  # Trade
        "scope1_per_employee": 600.0,
        "scope2_per_employee": 1500.0,
        "scope3_per_employee": 4000.0,
    },
    "J": {  # IT
        "scope1_per_employee": 200.0,
        "scope2_per_employee": 800.0,
        "scope3_per_employee": 1800.0,
    },
    "DEFAULT": {
        "scope1_per_employee": 1000.0,
        "scope2_per_employee": 1000.0,
        "scope3_per_employee": 5000.0,
    },
}

# ── Limiti di range per PMI ─────────────────────────────────────
RANGE_LIMITS = {
    "scope1_per_employee_min": 10.0,    # kgCO2e
    "scope1_per_employee_max": 20000.0,
    "scope2_per_employee_min": 50.0,
    "scope2_per_employee_max": 15000.0,
    "scope3_per_employee_min": 100.0,
    "scope3_per_employee_max": 50000.0,
    "yoy_change_max_pct": 50.0,          # Max year-over-year change %
}


class ValidationEngine:
    """Motore di validazione dati emissioni."""

    @staticmethod
    def get_sector_benchmark(sector_code: str) -> Dict[str, float]:
        """Ottiene i benchmark per il settore."""
        sector_letter = sector_code[0] if sector_code else "DEFAULT"
        return SECTOR_BENCHMARKS.get(sector_letter, SECTOR_BENCHMARKS["DEFAULT"])

    @staticmethod
    def check_range(
        scope1_tco2e: float = 0,
        scope2_tco2e: float = 0,
        scope3_tco2e: float = 0,
        employee_count: int = 1,
        sector_code: str = "DEFAULT",
    ) -> List[Dict]:
        """Range check: verifica se i dati sono nel range atteso."""
        alerts = []

        if employee_count <= 0:
            return alerts

        scope1_per_emp = (scope1_tco2e * 1000) / employee_count
        scope2_per_emp = (scope2_tco2e * 1000) / employee_count
        scope3_per_emp = (scope3_tco2e * 1000) / employee_count
        benchmark = ValidationEngine.get_sector_benchmark(sector_code)

        # Scope 1 check
        if scope1_tco2e > 0 and scope1_per_emp > RANGE_LIMITS["scope1_per_employee_max"]:
            alerts.append({
                "type": "range_error",
                "scope": "1",
                "severity": "high",
                "message": f"Scope 1 ({scope1_tco2e} tCO2e) è molto alto per {employee_count} dipendenti",
                "detail": f"Valore per dipendente: {scope1_per_emp:.0f} kgCO2e. "
                          f"Benchmark settoriale: {benchmark.get('scope1_per_employee', 0):.0f} kgCO2e",
                "suggestion": "Verifica i dati inseriti. Possibile errore nelle unità di misura.",
            })
        elif scope1_tco2e > 0 and scope1_per_emp < RANGE_LIMITS["scope1_per_employee_min"]:
            alerts.append({
                "type": "range_warning",
                "scope": "1",
                "severity": "low",
                "message": f"Scope 1 ({scope1_tco2e} tCO2e) è insolitamente basso",
                "suggestion": "Potresti aver dimenticato di includere qualche fonte di emissione.",
            })

        # Scope 2 check
        if scope2_tco2e > 0 and scope2_per_emp > RANGE_LIMITS["scope2_per_employee_max"]:
            alerts.append({
                "type": "range_error",
                "scope": "2",
                "severity": "high",
                "message": f"Scope 2 ({scope2_tco2e} tCO2e) sembra eccessivo",
                "suggestion": "Controlla che il consumo elettrico sia in kWh, non MWh.",
            })

        # Scope 3 check
        if scope3_tco2e > 0 and scope3_per_emp > RANGE_LIMITS["scope3_per_employee_max"]:
            alerts.append({
                "type": "range_warning",
                "scope": "3",
                "severity": "medium",
                "message": f"Scope 3 ({scope3_tco2e} tCO2e) è significativamente alto",
                "suggestion": "Verifica le spese utilizzate per il calcolo spend-based.",
            })

        return alerts

    @staticmethod
    def check_year_over_year(
        current_year_tco2e: Dict[str, float],
        previous_year_tco2e: Optional[Dict[str, float]],
    ) -> List[Dict]:
        """Year-over-year comparison: verifica variazioni anomale."""
        alerts = []

        if not previous_year_tco2e:
            return alerts

        for scope in ["1", "2", "3"]:
            current = current_year_tco2e.get(f"scope{scope}", 0)
            previous = previous_year_tco2e.get(f"scope{scope}", 0)

            if previous <= 0:
                continue

            change_pct = abs((current - previous) / previous) * 100

            if change_pct > RANGE_LIMITS["yoy_change_max_pct"]:
                alerts.append({
                    "type": "yoy_anomaly",
                    "scope": scope,
                    "severity": "medium",
                    "message": f"Scope {scope} è cambiato del {change_pct:.0f}% rispetto all'anno precedente",
                    "current_value": current,
                    "previous_value": previous,
                    "change_pct": round(change_pct, 1),
                    "suggestion": "Variazioni >50% richiedono una spiegazione nel report ESRS.",
                })

        return alerts

    @staticmethod
    def check_sector_benchmark(
        scope1_tco2e: float,
        scope2_tco2e: float,
        scope3_tco2e: float,
        employee_count: int,
        sector_code: str,
    ) -> List[Dict]:
        """Confronta con benchmark di settore."""
        alerts = []

        if employee_count <= 0:
            return alerts

        benchmark = ValidationEngine.get_sector_benchmark(sector_code)

        scope1_per_emp = (scope1_tco2e * 1000) / employee_count
        scope2_per_emp = (scope2_tco2e * 1000) / employee_count
        scope3_per_emp = (scope3_tco2e * 1000) / employee_count

        # Confronto Scope 1
        b1 = benchmark.get("scope1_per_employee", 1000)
        if scope1_tco2e > 0 and b1 > 0:
            ratio = scope1_per_emp / b1
            if ratio > 3:
                alerts.append({
                    "type": "benchmark_alert",
                    "scope": "1",
                    "severity": "high",
                    "message": f"Scope 1 è {ratio:.0f}x il benchmark di settore",
                    "company_value": round(scope1_per_emp),
                    "benchmark": b1,
                    "unit": "kgCO2e/dipendente",
                    "suggestion": "Il settore di appartenenza potrebbe avere emissioni tipiche diverse.",
                })

        # Confronto Scope 2
        b2 = benchmark.get("scope2_per_employee", 1000)
        if scope2_tco2e > 0 and b2 > 0:
            ratio = scope2_per_emp / b2
            if ratio > 3:
                alerts.append({
                    "type": "benchmark_alert",
                    "scope": "2",
                    "severity": "medium",
                    "message": f"Scope 2 è {ratio:.0f}x il benchmark di settore",
                    "suggestion": "Verifica che il fattore di emissione usato sia corretto per il tuo paese.",
                })

        return alerts

    @staticmethod
    def check_missing_data(
        has_stationary_combustion: bool = False,
        has_mobile_combustion: bool = False,
        has_fugitive_emissions: bool = False,
        has_scope2: bool = False,
        has_scope3_upstream: bool = False,
        has_fleet: bool = False,
        sector_code: str = "DEFAULT",
    ) -> List[Dict]:
        """Missing data detection: alert per dati mancanti."""
        alerts = []
        sector_letter = sector_code[0] if sector_code else "DEFAULT"

        # Scope 1 - Stationary combustion (sempre richiesto)
        if not has_stationary_combustion:
            alerts.append({
                "type": "missing_data",
                "severity": "high",
                "message": "Dati combustione stazionaria (riscaldamento) mancanti",
                "suggestion": "Inserisci il consumo di gas naturale o gasolio per riscaldamento.",
            })

        # Fleet check per settori con veicoli
        fleet_sectors = ["H", "F", "A", "C"]
        if sector_letter in fleet_sectors and not has_fleet and not has_mobile_combustion:
            alerts.append({
                "type": "missing_data",
                "severity": "high",
                "message": "Dati flotta veicoli non inseriti",
                "suggestion": "Il tuo settore tipicamente utilizza veicoli. Inserisci i km percorsi.",
            })

        # Scope 2 (sempre richiesto)
        if not has_scope2:
            alerts.append({
                "type": "missing_data",
                "severity": "high",
                "message": "Dati Scope 2 (energia elettrica) mancanti",
                "suggestion": "Inserisci il consumo elettrico annuo dalla bolletta.",
            })

        # Scope 3 (sempre richiesto per CSRD)
        if not has_scope3_upstream:
            alerts.append({
                "type": "missing_data",
                "severity": "medium",
                "message": "Dati Scope 3 (beni acquistati) non inseriti",
                "suggestion": "Inserisci la spesa totale per beni e servizi per il calcolo spend-based.",
            })

        return alerts

    @staticmethod
    def check_unit_consistency(value: float, declared_unit: str) -> Optional[Dict]:
        """Unit consistency check."""
        if value > 1000000 and declared_unit == "tCO2eq":
            return {
                "type": "unit_warning",
                "severity": "medium",
                "message": f"Valore {value} tCO2eq è molto alto. Possibile errore di unità (kg vs t)?",
                "suggestion": "Conferma che il valore sia in tonnellate (tCO2eq) e non in kg.",
            }
        # Se il valore è molto piccolo in t ma potrebbe essere in kg
        if 0 < value < 0.01 and declared_unit == "tCO2eq":
            return {
                "type": "unit_warning",
                "severity": "low",
                "message": f"Valore {value} tCO2eq è molto basso. Verifica l'unità di misura.",
                "suggestion": "Potresti aver inserito kg invece di tonnellate.",
            }
        return None

    @staticmethod
    def validate_all(
        scope1_tco2e: float = 0,
        scope2_tco2e: float = 0,
        scope3_tco2e: float = 0,
        employee_count: int = 1,
        sector_code: str = "DEFAULT",
        previous_year_data: Optional[Dict[str, float]] = None,
        has_stationary: bool = False,
        has_mobile: bool = False,
        has_fugitive: bool = False,
        has_scope2: bool = False,
        has_scope3: bool = False,
        has_fleet: bool = False,
    ) -> Dict[str, Any]:
        """Esegue tutte le validazioni e restituisce un report completo."""
        all_alerts = []

        # Range check
        all_alerts.extend(
            ValidationEngine.check_range(
                scope1_tco2e, scope2_tco2e, scope3_tco2e,
                employee_count, sector_code,
            )
        )

        # YoY comparison
        if previous_year_data:
            current = {"scope1": scope1_tco2e, "scope2": scope2_tco2e, "scope3": scope3_tco2e}
            all_alerts.extend(
                ValidationEngine.check_year_over_year(current, previous_year_data)
            )

        # Sector benchmark
        all_alerts.extend(
            ValidationEngine.check_sector_benchmark(
                scope1_tco2e, scope2_tco2e, scope3_tco2e,
                employee_count, sector_code,
            )
        )

        # Missing data
        all_alerts.extend(
            ValidationEngine.check_missing_data(
                has_stationary, has_mobile, has_fugitive,
                has_scope2, has_scope3, has_fleet, sector_code,
            )
        )

        # Score (0-100)
        score = ValidationEngine._calculate_validation_score(all_alerts)

        return {
            "validation_score": score,
            "total_alerts": len(all_alerts),
            "high_severity": len([a for a in all_alerts if a.get("severity") == "high"]),
            "medium_severity": len([a for a in all_alerts if a.get("severity") == "medium"]),
            "low_severity": len([a for a in all_alerts if a.get("severity") == "low"]),
            "alerts": all_alerts,
            "recommendation": (
                "Dati validati con successo" if score >= 80
                else "Verifica i dati segnalati prima di procedere"
            ),
        }

    @staticmethod
    def _calculate_validation_score(alerts: List[Dict]) -> int:
        """Calcola un punteggio di validazione da 0 a 100."""
        if not alerts:
            return 100

        penalty = 0
        for alert in alerts:
            severity = alert.get("severity", "low")
            if severity == "high":
                penalty += 25
            elif severity == "medium":
                penalty += 10
            else:
                penalty += 3

        return max(0, min(100, 100 - penalty))
