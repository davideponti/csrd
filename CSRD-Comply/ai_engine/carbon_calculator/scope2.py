"""
CSRD Comply — GHG Protocol Scope 2 Calculator (Step 13)

Calcolo emissioni Scope 2: energia elettrica acquistata.
Due approcci: Location-based e Market-based (entrambi richiesti da ESRS E1-6).
"""
from typing import Optional, Dict, Any

# ── Country-specific grid emission factors ──────────────────────
# Fonte: AIE/Eurostat 2025, AIB Residual Mix 2025
# Unit: kg CO2e/kWh

LOCATION_BASED_FACTORS: Dict[str, float] = {
    "IT": 0.286,   # Italy
    "DE": 0.374,   # Germany
    "FR": 0.055,   # France
    "ES": 0.226,   # Spain
    "UK": 0.205,   # United Kingdom
    "NL": 0.345,   # Netherlands
    "BE": 0.194,   # Belgium
    "AT": 0.172,   # Austria
    "PT": 0.201,   # Portugal
    "PL": 0.654,   # Poland
    "SE": 0.008,   # Sweden
    "DK": 0.134,   # Denmark
    "FI": 0.078,   # Finland
    "IE": 0.348,   # Ireland
    "GR": 0.524,   # Greece
    "RO": 0.271,   # Romania
    "CZ": 0.432,   # Czech Republic
    "HU": 0.254,   # Hungary
    "SK": 0.196,   # Slovakia
    "SI": 0.231,   # Slovenia
    "HR": 0.194,   # Croatia
    "BG": 0.452,   # Bulgaria
    "LT": 0.168,   # Lithuania
    "LV": 0.128,   # Latvia
    "EE": 0.402,   # Estonia
    "LU": 0.159,   # Luxembourg
    "CY": 0.632,   # Cyprus
    "MT": 0.442,   # Malta
    "EU_avg": 0.276,  # EU average
}

# Market-based: AIB Residual Mix 2025
MARKET_BASED_FACTORS: Dict[str, float] = {
    "IT": 0.342,
    "DE": 0.341,
    "FR": 0.052,
    "ES": 0.252,
    "UK": 0.217,
    "NL": 0.387,
    "BE": 0.156,
    "AT": 0.160,
    "EU_avg": 0.289,
}

# Green tariff factors (if company has certified renewable contract)
GREEN_TARIFF_FACTOR = 0.0  # 0 kgCO2e/kWh for certified renewable energy (GOs)


class Scope2Calculator:
    """Calcolatore emissioni Scope 2."""

    @staticmethod
    def calculate_location_based(
        electricity_kwh: float,
        country: str = "EU_avg",
    ) -> Dict[str, Any]:
        """
        Calcola emissioni con approccio location-based.
        Usa il fattore medio della rete nazionale.
        """
        factor = LOCATION_BASED_FACTORS.get(
            country, LOCATION_BASED_FACTORS["EU_avg"]
        )
        kgCO2e = electricity_kwh * factor
        tCO2e = round(kgCO2e / 1000, 4)

        return {
            "method": "location_based",
            "electricity_kwh": electricity_kwh,
            "country": country,
            "emission_factor_kgco2e_per_kwh": factor,
            "total_kgco2e": round(kgCO2e, 2),
            "total_tco2e": tCO2e,
            "unit": "tCO2eq",
        }

    @staticmethod
    def calculate_market_based(
        electricity_kwh: float,
        country: str = "EU_avg",
        has_green_tariff: bool = False,
    ) -> Dict[str, Any]:
        """
        Calcola emissioni con approccio market-based.
        Usa i fattori AIB Residual Mix.
        Se l'azienda ha un contratto green certificato, usa fattore 0.
        """
        if has_green_tariff:
            factor = GREEN_TARIFF_FACTOR
            source = "green_tariff_certified"
        else:
            factor = MARKET_BASED_FACTORS.get(
                country, MARKET_BASED_FACTORS["EU_avg"]
            )
            source = "aib_residual_mix"

        kgCO2e = electricity_kwh * factor
        tCO2e = round(kgCO2e / 1000, 4)

        return {
            "method": "market_based",
            "electricity_kwh": electricity_kwh,
            "country": country,
            "has_green_tariff": has_green_tariff,
            "emission_factor_source": source,
            "emission_factor_kgco2e_per_kwh": factor,
            "total_kgco2e": round(kgCO2e, 2),
            "total_tco2e": tCO2e,
            "unit": "tCO2eq",
        }

    @staticmethod
    def calculate_both_methods(
        electricity_kwh: float,
        country: str = "EU_avg",
        has_green_tariff: bool = False,
    ) -> Dict[str, Any]:
        """
        Calcola entrambi gli approcci (richiesto da ESRS E1-6).
        La differenza tra location-based e market-based è un'informazione
        obbligatoria nel report.
        """
        location = Scope2Calculator.calculate_location_based(electricity_kwh, country)
        market = Scope2Calculator.calculate_market_based(electricity_kwh, country, has_green_tariff)

        # Usa il location-based come default per il totale (conservativo)
        default_tco2e = location["total_tco2e"]

        return {
            "scope": "2",
            "electricity_kwh": electricity_kwh,
            "country": country,
            "location_based": location,
            "market_based": market,
            "total_tco2e": default_tco2e,
            "difference_tco2e": round(
                abs(location["total_tco2e"] - market["total_tco2e"]), 4
            ),
            "method": "dual_reporting",
            "note": "ESRS E1-6 requires both location-based and market-based reporting",
        }

    @staticmethod
    def calculate_steam_heating_cooling(
        energy_kwh: float,
        factor_kgco2e_per_kwh: float = 0.120,
    ) -> Dict[str, Any]:
        """Calcola emissioni da vapore/riscaldamento/raffreddamento acquistato."""
        kgCO2e = energy_kwh * factor_kgco2e_per_kwh
        return {
            "scope": "2",
            "type": "steam_heating_cooling",
            "energy_kwh": energy_kwh,
            "total_tco2e": round(kgCO2e / 1000, 4),
            "unit": "tCO2eq",
        }
