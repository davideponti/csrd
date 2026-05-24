"""
CSRD Comply — GHG Protocol Scope 1 Calculator (Step 12)

Calcolo emissioni Scope 1: emissioni dirette da fonti possedute/controllate.
"""
from typing import Optional, Dict, List, Any

# ── Emission Factors ────────────────────────────────────────────
# Fonte: DEFRA UK 2025, EPA US 2025, IPCC 2025 Tier 1 defaults
# Unit: kg CO2e per unità di attività

EMISSION_FACTORS: Dict[str, Dict[str, float]] = {
    # Stationary Combustion
    "natural_gas": {
        "per_kwh": 0.184,          # kgCO2e/kWh
        "per_m3": 2.040,           # kgCO2e/m³
        "source": "DEFRA 2025",
    },
    "diesel_heating": {
        "per_litre": 2.680,        # kgCO2e/litro
        "source": "DEFRA 2025",
    },
    "lpg": {
        "per_kwh": 0.215,          # kgCO2e/kWh
        "per_litre": 1.510,        # kgCO2e/litro
        "source": "DEFRA 2025",
    },
    "biomass": {
        "per_kwh": 0.018,          # kgCO2e/kWh (biogenic excluded)
        "source": "IPCC 2025",
    },
    # Mobile Combustion
    "diesel_vehicle": {
        "per_km": 0.170,           # kgCO2e/km (car - average)
        "source": "DEFRA 2025",
    },
    "petrol_vehicle": {
        "per_km": 0.155,           # kgCO2e/km (car - average)
        "source": "DEFRA 2025",
    },
    "diesel_van": {
        "per_km": 0.260,           # kgCO2e/km (light commercial)
        "source": "DEFRA 2025",
    },
    "diesel_truck": {
        "per_km": 0.870,           # kgCO2e/km (heavy truck)
        "source": "DEFRA 2025",
    },
    "electric_vehicle": {
        "per_km": 0.050,           # kgCO2e/km (using EU grid avg)
        "source": "DEFRA 2025",
    },
    # Fugitive Emissions - Refrigerants
    "r410a": {
        "per_kg": 2088.0,          # kgCO2e/kg - GWP = 2088
        "source": "IPCC AR6 2025",
    },
    "r134a": {
        "per_kg": 1430.0,          # kgCO2e/kg - GWP = 1430
        "source": "IPCC AR6 2025",
    },
    "r32": {
        "per_kg": 675.0,           # kgCO2e/kg - GWP = 675
        "source": "IPCC AR6 2025",
    },
    "r290": {
        "per_kg": 3.0,             # kgCO2e/kg - GWP = 3 (propane)
        "source": "IPCC AR6 2025",
    },
    # Process Emissions (industrial production)
    "cement_production": {
        "per_tonne": 0.540,          # tCO2e/tonne clinker (calcination process)
        "source": "IPCC 2025 Guidelines",
    },
    "steel_production": {
        "per_tonne": 1.850,          # tCO2e/tonne crude steel (BF-BOF)
        "per_tonne_eaf": 0.400,      # tCO2e/tonne steel (Electric Arc Furnace)
        "source": "World Steel Association / IPCC 2025",
    },
    "chemical_process": {
        "per_tonne_ammonia": 1.600,  # tCO2e/tonne ammonia
        "per_tonne_ethylene": 0.750, # tCO2e/tonne ethylene
        "per_tonne_methanol": 0.670, # tCO2e/tonne methanol
        "source": "IPCC 2025 / Ecoinvent 3.10",
    },
    "aluminium_production": {
        "per_tonne": 1.670,          # tCO2e/tonne primary aluminium
        "source": "IAI / IPCC 2025",
    },
    "glass_production": {
        "per_tonne": 0.560,          # tCO2e/tonne glass
        "source": "IPCC 2025 / Ecoinvent 3.10",
    },
    "paper_production": {
        "per_tonne": 0.380,          # tCO2e/tonne paper
        "source": "IPCC 2025 / CEPI",
    },
    "food_processing": {
        "per_tonne": 0.250,          # tCO2e/tonne processed food (generic)
        "source": "Ecoinvent 3.10 / DEFRA 2025",
    },
    "refrigeration_process": {
        "per_kg_leak": 0.150,        # kgCO2e/kg refrigerant leaked (avg)
        "source": "IPCC AR6 / EN 378",
    },
    # Country-specific grid factors (kgCO2e/kWh) — per national grid
    "grid_electricity": {
        "IT": 0.290,               # Italy
        "DE": 0.380,               # Germany
        "FR": 0.060,               # France
        "ES": 0.230,               # Spain
        "UK": 0.210,               # United Kingdom
        "NL": 0.350,               # Netherlands
        "BE": 0.200,               # Belgium
        "AT": 0.180,               # Austria
        "EU_avg": 0.280,           # EU average
        "source": "AIE/Eurostat 2025",
    },
    # ISPRA (Italy-specific) - Supplement to DEFRA/Eurostat
    "ispra_italy": {
        "natural_gas_factor": 0.201,   # kgCO2e/kWh — specifico per mix gas IT
        "electricity_factor": 0.322,   # kgCO2e/kWh — ISPRA 2025 fattore rete IT
        "source": "ISPRA 2025 — Fattori di emissione nazionali",
    },
}


class Scope1Calculator:
    """Calcolatore emissioni Scope 1."""

    # Categorie Scope 1
    CATEGORIES = {
        "stationary_combustion": {
            "name": "Stationary Combustion",
            "description": "Combustione da fonti fisse (riscaldamento, generatori)",
            "subcategories": ["natural_gas", "diesel_heating", "lpg", "biomass"],
        },
        "mobile_combustion": {
            "name": "Mobile Combustion",
            "description": "Combustione da veicoli aziendali",
            "subcategories": ["diesel_vehicle", "petrol_vehicle", "diesel_van", "diesel_truck", "electric_vehicle"],
        },
        "fugitive_emissions": {
            "name": "Fugitive Emissions",
            "description": "Emissioni fuggitive da refrigeranti e processi",
            "subcategories": ["r410a", "r134a", "r32", "r290"],
        },
    }

    @staticmethod
    def calculate_stationary_combustion(
        natural_gas_kwh: Optional[float] = None,
        natural_gas_m3: Optional[float] = None,
        diesel_heating_litres: Optional[float] = None,
        lpg_kwh: Optional[float] = None,
        lpg_litres: Optional[float] = None,
        biomass_kwh: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Calcola emissioni da combustione stazionaria."""
        total = 0.0
        breakdown = {}

        if natural_gas_kwh:
            kg = natural_gas_kwh * EMISSION_FACTORS["natural_gas"]["per_kwh"]
            total += kg
            breakdown["natural_gas"] = {"value": natural_gas_kwh, "unit": "kWh", "kgCO2e": kg}

        if natural_gas_m3:
            kg = natural_gas_m3 * EMISSION_FACTORS["natural_gas"]["per_m3"]
            total += kg
            breakdown["natural_gas_m3"] = {"value": natural_gas_m3, "unit": "m³", "kgCO2e": kg}

        if diesel_heating_litres:
            kg = diesel_heating_litres * EMISSION_FACTORS["diesel_heating"]["per_litre"]
            total += kg
            breakdown["diesel_heating"] = {"value": diesel_heating_litres, "unit": "litres", "kgCO2e": kg}

        if lpg_kwh:
            kg = lpg_kwh * EMISSION_FACTORS["lpg"]["per_kwh"]
            total += kg
            breakdown["lpg_kwh"] = {"value": lpg_kwh, "unit": "kWh", "kgCO2e": kg}

        if lpg_litres:
            kg = lpg_litres * EMISSION_FACTORS["lpg"]["per_litre"]
            total += kg
            breakdown["lpg_litres"] = {"value": lpg_litres, "unit": "litres", "kgCO2e": kg}

        if biomass_kwh:
            kg = biomass_kwh * EMISSION_FACTORS["biomass"]["per_kwh"]
            total += kg
            breakdown["biomass"] = {"value": biomass_kwh, "unit": "kWh", "kgCO2e": kg}

        tCO2e = round(total / 1000, 4)

        return {
            "category": "stationary_combustion",
            "total_tco2e": tCO2e,
            "total_kgco2e": round(total, 2),
            "breakdown": breakdown,
            "unit": "tCO2eq",
        }

    @staticmethod
    def calculate_mobile_combustion(
        diesel_km: Optional[float] = None,
        petrol_km: Optional[float] = None,
        diesel_van_km: Optional[float] = None,
        diesel_truck_km: Optional[float] = None,
        electric_km: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Calcola emissioni da combustione mobile (veicoli aziendali)."""
        total = 0.0
        breakdown = {}

        if diesel_km:
            kg = diesel_km * EMISSION_FACTORS["diesel_vehicle"]["per_km"]
            total += kg
            breakdown["diesel_car"] = {"value": diesel_km, "unit": "km", "kgCO2e": kg}

        if petrol_km:
            kg = petrol_km * EMISSION_FACTORS["petrol_vehicle"]["per_km"]
            total += kg
            breakdown["petrol_car"] = {"value": petrol_km, "unit": "km", "kgCO2e": kg}

        if diesel_van_km:
            kg = diesel_van_km * EMISSION_FACTORS["diesel_van"]["per_km"]
            total += kg
            breakdown["diesel_van"] = {"value": diesel_van_km, "unit": "km", "kgCO2e": kg}

        if diesel_truck_km:
            kg = diesel_truck_km * EMISSION_FACTORS["diesel_truck"]["per_km"]
            total += kg
            breakdown["diesel_truck"] = {"value": diesel_truck_km, "unit": "km", "kgCO2e": kg}

        if electric_km:
            kg = electric_km * EMISSION_FACTORS["electric_vehicle"]["per_km"]
            total += kg
            breakdown["electric_vehicle"] = {"value": electric_km, "unit": "km", "kgCO2e": kg}

        tCO2e = round(total / 1000, 4)

        return {
            "category": "mobile_combustion",
            "total_tco2e": tCO2e,
            "total_kgco2e": round(total, 2),
            "breakdown": breakdown,
            "unit": "tCO2eq",
        }

    @staticmethod
    def calculate_fugitive_emissions(
        r410a_kg: Optional[float] = None,
        r134a_kg: Optional[float] = None,
        r32_kg: Optional[float] = None,
        r290_kg: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Calcola emissioni fuggitive da refrigeranti."""
        total = 0.0
        breakdown = {}

        if r410a_kg:
            kg = r410a_kg * EMISSION_FACTORS["r410a"]["per_kg"]
            total += kg
            breakdown["R410A"] = {"value": r410a_kg, "unit": "kg", "kgCO2e": kg}

        if r134a_kg:
            kg = r134a_kg * EMISSION_FACTORS["r134a"]["per_kg"]
            total += kg
            breakdown["R134a"] = {"value": r134a_kg, "unit": "kg", "kgCO2e": kg}

        if r32_kg:
            kg = r32_kg * EMISSION_FACTORS["r32"]["per_kg"]
            total += kg
            breakdown["R32"] = {"value": r32_kg, "unit": "kg", "kgCO2e": kg}

        if r290_kg:
            kg = r290_kg * EMISSION_FACTORS["r290"]["per_kg"]
            total += kg
            breakdown["R290"] = {"value": r290_kg, "unit": "kg", "kgCO2e": kg}

        tCO2e = round(total / 1000, 4)

        return {
            "category": "fugitive_emissions",
            "total_tco2e": tCO2e,
            "total_kgco2e": round(total, 2),
            "breakdown": breakdown,
            "unit": "tCO2eq",
        }

    # ── Process Emissions ───────────────────────────────────────
    @staticmethod
    def calculate_process_emissions(
        cement_tonnes: Optional[float] = None,
        steel_tonnes_bf_bof: Optional[float] = None,
        steel_tonnes_eaf: Optional[float] = None,
        ammonia_tonnes: Optional[float] = None,
        ethylene_tonnes: Optional[float] = None,
        methanol_tonnes: Optional[float] = None,
        aluminium_tonnes: Optional[float] = None,
        glass_tonnes: Optional[float] = None,
        paper_tonnes: Optional[float] = None,
        food_tonnes: Optional[float] = None,
        refrigerant_leak_kg: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calcola emissioni da processi industriali (process emissions).
        
        Questa categoria include emissioni che non derivano da combustione
        ma da reazioni chimiche o fisiche durante la produzione industriale.
        Applicabile solo per aziende manifatturiere.
        """
        total = 0.0
        breakdown = {}

        if cement_tonnes:
            t = cement_tonnes * EMISSION_FACTORS["cement_production"]["per_tonne"]
            total += t
            breakdown["cement_production"] = {"value": cement_tonnes, "unit": "tonnes", "tCO2e": t}

        if steel_tonnes_bf_bof:
            t = steel_tonnes_bf_bof * EMISSION_FACTORS["steel_production"]["per_tonne"]
            total += t
            breakdown["steel_bf_bof"] = {"value": steel_tonnes_bf_bof, "unit": "tonnes", "tCO2e": t}

        if steel_tonnes_eaf:
            t = steel_tonnes_eaf * EMISSION_FACTORS["steel_production"]["per_tonne_eaf"]
            total += t
            breakdown["steel_eaf"] = {"value": steel_tonnes_eaf, "unit": "tonnes", "tCO2e": t}

        if ammonia_tonnes:
            t = ammonia_tonnes * EMISSION_FACTORS["chemical_process"]["per_tonne_ammonia"]
            total += t
            breakdown["ammonia_production"] = {"value": ammonia_tonnes, "unit": "tonnes", "tCO2e": t}

        if ethylene_tonnes:
            t = ethylene_tonnes * EMISSION_FACTORS["chemical_process"]["per_tonne_ethylene"]
            total += t
            breakdown["ethylene_production"] = {"value": ethylene_tonnes, "unit": "tonnes", "tCO2e": t}

        if methanol_tonnes:
            t = methanol_tonnes * EMISSION_FACTORS["chemical_process"]["per_tonne_methanol"]
            total += t
            breakdown["methanol_production"] = {"value": methanol_tonnes, "unit": "tonnes", "tCO2e": t}

        if aluminium_tonnes:
            t = aluminium_tonnes * EMISSION_FACTORS["aluminium_production"]["per_tonne"]
            total += t
            breakdown["aluminium_production"] = {"value": aluminium_tonnes, "unit": "tonnes", "tCO2e": t}

        if glass_tonnes:
            t = glass_tonnes * EMISSION_FACTORS["glass_production"]["per_tonne"]
            total += t
            breakdown["glass_production"] = {"value": glass_tonnes, "unit": "tonnes", "tCO2e": t}

        if paper_tonnes:
            t = paper_tonnes * EMISSION_FACTORS["paper_production"]["per_tonne"]
            total += t
            breakdown["paper_production"] = {"value": paper_tonnes, "unit": "tonnes", "tCO2e": t}

        if food_tonnes:
            t = food_tonnes * EMISSION_FACTORS["food_processing"]["per_tonne"]
            total += t
            breakdown["food_processing"] = {"value": food_tonnes, "unit": "tonnes", "tCO2e": t}

        if refrigerant_leak_kg:
            kg = refrigerant_leak_kg * EMISSION_FACTORS["refrigeration_process"]["per_kg_leak"]
            total += kg / 1000  # Convert kg to tCO2e
            breakdown["refrigerant_leak"] = {"value": refrigerant_leak_kg, "unit": "kg", "tCO2e": round(kg / 1000, 4)}

        tCO2e = round(total, 4)

        return {
            "category": "process_emissions",
            "name": "Process Emissions",
            "description": "Emissioni da processi industriali (produzione)",
            "total_tco2e": tCO2e,
            "breakdown": breakdown,
            "unit": "tCO2eq",
        }

    @staticmethod
    def calculate_total_scope1(
        stationary: Optional[Dict] = None,
        mobile: Optional[Dict] = None,
        fugitive: Optional[Dict] = None,
        process: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Calcola il totale Scope 1 da tutte le categorie."""
        categories = []
        total_tco2e = 0.0

        if stationary:
            categories.append(stationary)
            total_tco2e += stationary["total_tco2e"]
        if mobile:
            categories.append(mobile)
            total_tco2e += mobile["total_tco2e"]
        if fugitive:
            categories.append(fugitive)
            total_tco2e += fugitive["total_tco2e"]
        if process:
            categories.append(process)
            total_tco2e += process["total_tco2e"]

        return {
            "scope": "1",
            "total_tco2e": round(total_tco2e, 4),
            "categories": categories,
            "method": "activity_data_x_emission_factors",
        }

    @staticmethod
    def get_emission_factors(country: str = "EU_avg") -> Dict[str, Any]:
        """Restituisce i fattori di emissione disponibili."""
        grid_factor = EMISSION_FACTORS["grid_electricity"].get(
            country, EMISSION_FACTORS["grid_electricity"]["EU_avg"]
        )
        return {
            "stationary_combustion": {
                "natural_gas": EMISSION_FACTORS["natural_gas"],
                "diesel_heating": EMISSION_FACTORS["diesel_heating"],
                "lpg": EMISSION_FACTORS["lpg"],
            },
            "mobile_combustion": {
                "diesel_vehicle": EMISSION_FACTORS["diesel_vehicle"],
                "petrol_vehicle": EMISSION_FACTORS["petrol_vehicle"],
                "diesel_van": EMISSION_FACTORS["diesel_van"],
                "electric_vehicle": EMISSION_FACTORS["electric_vehicle"],
            },
            "fugitive_emissions": {
                "r410a": EMISSION_FACTORS["r410a"],
                "r134a": EMISSION_FACTORS["r134a"],
                "r32": EMISSION_FACTORS["r32"],
            },
            "grid_electricity_factor": {
                "country": country,
                "kgCO2e_per_kWh": grid_factor,
            },
        }
