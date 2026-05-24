"""
CSRD Comply — GHG Protocol Scope 3 Calculator (Step 14)

Calcolo emissioni Scope 3: tutte le 15 categorie.
Metodo principale: spend-based (adatto per PMI).
Include downstream categories 8-15.
"""
from typing import Optional, Dict, Any, List


# ── Emission Factors per settore NACE (spend-based) ────────────
# Fonte: EXIOBASE 3 + Ecoinvent 3.10 aggregata per NACE 2-digit
# Unit: kgCO2e/EUR

SPEND_BASED_FACTORS: Dict[str, Dict[str, Any]] = {
    # Manufacturing
    "C10": {"name": "Food products", "factor": 0.45, "unit": "kgCO2e/EUR"},
    "C11": {"name": "Beverages", "factor": 0.38, "unit": "kgCO2e/EUR"},
    "C13": {"name": "Textiles", "factor": 0.52, "unit": "kgCO2e/EUR"},
    "C14": {"name": "Wearing apparel", "factor": 0.41, "unit": "kgCO2e/EUR"},
    "C16": {"name": "Wood products", "factor": 0.35, "unit": "kgCO2e/EUR"},
    "C17": {"name": "Paper products", "factor": 0.62, "unit": "kgCO2e/EUR"},
    "C18": {"name": "Printing", "factor": 0.28, "unit": "kgCO2e/EUR"},
    "C19": {"name": "Coke/petroleum", "factor": 1.20, "unit": "kgCO2e/EUR"},
    "C20": {"name": "Chemicals", "factor": 0.89, "unit": "kgCO2e/EUR"},
    "C21": {"name": "Pharmaceuticals", "factor": 0.34, "unit": "kgCO2e/EUR"},
    "C22": {"name": "Rubber/plastics", "factor": 0.75, "unit": "kgCO2e/EUR"},
    "C23": {"name": "Non-metallic minerals", "factor": 0.92, "unit": "kgCO2e/EUR"},
    "C24": {"name": "Basic metals", "factor": 1.45, "unit": "kgCO2e/EUR"},
    "C25": {"name": "Fabricated metals", "factor": 0.58, "unit": "kgCO2e/EUR"},
    "C26": {"name": "Computer/Electronic", "factor": 0.12, "unit": "kgCO2e/EUR"},
    "C27": {"name": "Electrical equipment", "factor": 0.32, "unit": "kgCO2e/EUR"},
    "C28": {"name": "Machinery", "factor": 0.38, "unit": "kgCO2e/EUR"},
    "C29": {"name": "Motor vehicles", "factor": 0.55, "unit": "kgCO2e/EUR"},
    "C30": {"name": "Other transport equip.", "factor": 0.48, "unit": "kgCO2e/EUR"},
    "C31": {"name": "Furniture", "factor": 0.36, "unit": "kgCO2e/EUR"},
    # Services
    "J62": {"name": "IT services", "factor": 0.07, "unit": "kgCO2e/EUR"},
    "J63": {"name": "Information services", "factor": 0.06, "unit": "kgCO2e/EUR"},
    "M69": {"name": "Legal/Accounting", "factor": 0.05, "unit": "kgCO2e/EUR"},
    "M70": {"name": "Management consulting", "factor": 0.05, "unit": "kgCO2e/EUR"},
    "M71": {"name": "Architecture/Engineering", "factor": 0.06, "unit": "kgCO2e/EUR"},
    "M72": {"name": "R&D", "factor": 0.08, "unit": "kgCO2e/EUR"},
    "M73": {"name": "Advertising/Marketing", "factor": 0.07, "unit": "kgCO2e/EUR"},
    "N78": {"name": "Employment services", "factor": 0.04, "unit": "kgCO2e/EUR"},
    "N79": {"name": "Travel services", "factor": 0.15, "unit": "kgCO2e/EUR"},
    # Trade
    "G45": {"name": "Wholesale motor vehicles", "factor": 0.12, "unit": "kgCO2e/EUR"},
    "G46": {"name": "Wholesale trade", "factor": 0.10, "unit": "kgCO2e/EUR"},
    "G47": {"name": "Retail trade", "factor": 0.14, "unit": "kgCO2e/EUR"},
    # Transport
    "H49": {"name": "Land transport", "factor": 0.65, "unit": "kgCO2e/EUR"},
    "H50": {"name": "Water transport", "factor": 0.85, "unit": "kgCO2e/EUR"},
    "H51": {"name": "Air transport", "factor": 1.10, "unit": "kgCO2e/EUR"},
    "H52": {"name": "Warehousing/Support", "factor": 0.25, "unit": "kgCO2e/EUR"},
    # Agriculture
    "A01": {"name": "Crop/Animal production", "factor": 0.72, "unit": "kgCO2e/EUR"},
    "A02": {"name": "Forestry", "factor": 0.18, "unit": "kgCO2e/EUR"},
    "A03": {"name": "Fishing", "factor": 0.55, "unit": "kgCO2e/EUR"},
    # Construction
    "F41": {"name": "Building construction", "factor": 0.28, "unit": "kgCO2e/EUR"},
    "F42": {"name": "Civil engineering", "factor": 0.38, "unit": "kgCO2e/EUR"},
    "F43": {"name": "Specialised construction", "factor": 0.32, "unit": "kgCO2e/EUR"},
    # Generic default
    "DEFAULT": {"name": "Generic", "factor": 0.25, "unit": "kgCO2e/EUR"},
}

# ── Business travel factors ─────────────────────────────────────
TRAVEL_FACTORS: Dict[str, float] = {
    "flight_short_haul": 0.156,   # kgCO2e/passenger-km
    "flight_medium_haul": 0.115,
    "flight_long_haul": 0.098,
    "train": 0.006,
    "bus": 0.027,
    "car_diesel": 0.170,
    "car_petrol": 0.155,
    "taxi": 0.180,
}

# ── Commuting factors ───────────────────────────────────────────
COMMUTING_FACTORS: Dict[str, float] = {
    "car_alone": 0.170,       # kgCO2e/km
    "car_carpool": 0.085,
    "public_transport": 0.050,
    "train": 0.006,
    "bus": 0.027,
    "bike": 0.0,
    "walking": 0.0,
    "motorcycle": 0.100,
}

# ── Waste factors ───────────────────────────────────────────────
WASTE_FACTORS: Dict[str, float] = {
    "mixed_waste": 0.420,     # kgCO2e/kg waste
    "paper_cardboard": 0.084,
    "plastic": 0.650,
    "glass": 0.160,
    "metal": 0.042,
    "organic": 0.310,
    "hazardous": 1.200,
    "construction": 0.090,
}

# ── End-of-life factors ─────────────────────────────────────────
END_OF_LIFE_FACTORS: Dict[str, float] = {
    "landfill": 0.580,        # kgCO2e/kg product
    "incineration": 0.420,
    "recycling": 0.050,
    "composting": 0.110,
}

# ── Product use phase factors ───────────────────────────────────
PRODUCT_USE_FACTORS: Dict[str, float] = {
    "electronics": 0.015,     # kgCO2e/EUR of product value (energy consumption)
    "appliances": 0.022,
    "machinery": 0.018,
    "vehicles": 0.035,
    "default": 0.010,
}

# ── Processing of sold products factors ─────────────────────────
PROCESSING_FACTORS: Dict[str, float] = {
    "basic_metals": 0.150,    # kgCO2e/EUR of sold product
    "chemicals": 0.120,
    "food": 0.080,
    "textiles": 0.065,
    "default": 0.050,
}


class Scope3Calculator:
    """Calcolatore emissioni Scope 3 con metodi spend-based e activity-based."""

    @staticmethod
    def get_factor(nace_code: str) -> float:
        """Ottiene il fattore di emissione per un codice NACE."""
        clean_code = nace_code.strip().upper()[:3]
        entry = SPEND_BASED_FACTORS.get(clean_code)
        if entry:
            return entry["factor"]
        # Prova con la lettera del settore
        sector = clean_code[0]
        sector_defaults = {
            "A": 0.72, "B": 0.89, "C": 0.45, "D": 0.35,
            "E": 0.40, "F": 0.30, "G": 0.12, "H": 0.65,
            "I": 0.08, "J": 0.07, "K": 0.05, "L": 0.06,
            "M": 0.06, "N": 0.10, "O": 0.12, "P": 0.08,
            "Q": 0.15, "R": 0.12, "S": 0.10,
        }
        return sector_defaults.get(sector, 0.25)

    @staticmethod
    def get_available_factors() -> Dict[str, Dict[str, Any]]:
        """Restituisce tutti i fattori di emissione disponibili."""
        return {
            "spend_based": SPEND_BASED_FACTORS,
            "travel": TRAVEL_FACTORS,
            "commuting": COMMUTING_FACTORS,
            "waste": WASTE_FACTORS,
            "end_of_life": END_OF_LIFE_FACTORS,
            "product_use": PRODUCT_USE_FACTORS,
            "processing": PROCESSING_FACTORS,
        }

    # ═══════════════════════════════════════════════════════════════
    # UPSTREAM CATEGORIES (1-8)
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def category_1_purchased_goods_spend_based(
        spend_eur: float,
        supplier_nace: str = "DEFAULT",
    ) -> Dict[str, Any]:
        """Cat.1: Purchased goods and services - metodo spend-based."""
        factor = Scope3Calculator.get_factor(supplier_nace)
        kgCO2e = spend_eur * factor
        return {
            "category": 1,
            "name": "Purchased goods and services",
            "method": "spend_based",
            "spend_eur": spend_eur,
            "supplier_sector": supplier_nace,
            "emission_factor": factor,
            "total_tco2e": round(kgCO2e / 1000, 4),
            "unit": "tCO2eq",
        }

    @staticmethod
    def category_2_capital_goods(
        spend_eur: float,
        nace_code: str = "DEFAULT",
    ) -> Dict[str, Any]:
        """Cat.2: Capital goods - spend-based."""
        # Same logic as Cat.1 with different label
        result = Scope3Calculator.category_1_purchased_goods_spend_based(
            spend_eur, nace_code
        )
        result["category"] = 2
        result["name"] = "Capital goods"
        return result

    @staticmethod
    def category_3_fuel_and_energy_related(
        electricity_kwh: float = 0,
        natural_gas_kwh: float = 0,
        diesel_litres: float = 0,
    ) -> Dict[str, Any]:
        """Cat.3: Fuel and energy related activities (WTT emissions)."""
        # Well-to-Tank: ~20% of direct emissions
        total_wtt = 0.0

        if electricity_kwh:
            wtt_electricity = electricity_kwh * 0.032  # kgCO2e/kWh WTT factor
            total_wtt += wtt_electricity
        if natural_gas_kwh:
            wtt_gas = natural_gas_kwh * 0.031  # kgCO2e/kWh WTT factor
            total_wtt += wtt_gas
        if diesel_litres:
            wtt_diesel = diesel_litres * 0.540  # kgCO2e/litre WTT factor
            total_wtt += wtt_diesel

        return {
            "category": 3,
            "name": "Fuel and energy related activities",
            "method": "wtt_calculation",
            "electricity_kwh": electricity_kwh,
            "natural_gas_kwh": natural_gas_kwh,
            "diesel_litres": diesel_litres,
            "total_tco2e": round(total_wtt / 1000, 4),
            "unit": "tCO2eq",
        }

    @staticmethod
    def category_4_upstream_transportation(
        tkm: float = 0,
        transport_mode: str = "truck",
    ) -> Dict[str, Any]:
        """Cat.4: Upstream transportation and distribution."""
        factors = {
            "truck": 0.062,     # kgCO2e/tkm
            "train": 0.022,
            "ship": 0.015,
            "air": 0.650,
            "van": 0.145,
        }
        factor = factors.get(transport_mode, 0.062)
        kgCO2e = tkm * factor

        return {
            "category": 4,
            "name": "Upstream transportation",
            "method": "distance_based",
            "tkm": tkm,
            "transport_mode": transport_mode,
            "emission_factor": factor,
            "total_tco2e": round(kgCO2e / 1000, 4),
            "unit": "tCO2eq",
        }

    @staticmethod
    def category_5_waste_generated(
        waste_kg: float,
        waste_type: str = "mixed_waste",
    ) -> Dict[str, Any]:
        """Cat.5: Waste generated in operations."""
        factor = WASTE_FACTORS.get(waste_type, WASTE_FACTORS["mixed_waste"])
        kgCO2e = waste_kg * factor

        return {
            "category": 5,
            "name": "Waste generated in operations",
            "method": "waste_type_specific",
            "waste_kg": waste_kg,
            "waste_type": waste_type,
            "emission_factor": factor,
            "total_tco2e": round(kgCO2e / 1000, 4),
            "unit": "tCO2eq",
        }

    @staticmethod
    def category_6_business_travel(
        km: float,
        travel_mode: str = "car_diesel",
    ) -> Dict[str, Any]:
        """Cat.6: Business travel."""
        factor = TRAVEL_FACTORS.get(travel_mode, 0.170)
        kgCO2e = km * factor

        return {
            "category": 6,
            "name": "Business travel",
            "method": "distance_based",
            "km": km,
            "travel_mode": travel_mode,
            "emission_factor": factor,
            "total_tco2e": round(kgCO2e / 1000, 4),
            "unit": "tCO2eq",
        }

    @staticmethod
    def category_7_employee_commuting(
        employees: int,
        avg_commute_km: float = 20.0,
        commuting_mode: str = "car_alone",
        working_days: int = 220,
    ) -> Dict[str, Any]:
        """Cat.7: Employee commuting."""
        factor = COMMUTING_FACTORS.get(commuting_mode, 0.170)
        total_km = employees * avg_commute_km * working_days
        kgCO2e = total_km * factor

        return {
            "category": 7,
            "name": "Employee commuting",
            "method": "average_data",
            "employees": employees,
            "avg_commute_km": avg_commute_km,
            "commuting_mode": commuting_mode,
            "working_days": working_days,
            "total_km": total_km,
            "total_tco2e": round(kgCO2e / 1000, 4),
            "unit": "tCO2eq",
        }

    @staticmethod
    def category_8_upstream_leased_assets(
        leased_area_m2: float = 0,
        energy_kwh: float = 0,
        lease_cost_eur: float = 0,
    ) -> Dict[str, Any]:
        """Cat.8: Upstream leased assets."""
        # Metodo ibrido: area-based + energy-based
        kgCO2e = 0.0
        if leased_area_m2:
            kgCO2e += leased_area_m2 * 25.0  # ~25 kgCO2e/m2 for office space
        if energy_kwh:
            kgCO2e += energy_kwh * 0.276  # EU avg grid factor
        if lease_cost_eur and kgCO2e == 0:
            kgCO2e = lease_cost_eur * 0.15  # spend-based fallback

        return {
            "category": 8,
            "name": "Upstream leased assets",
            "method": "hybrid",
            "leased_area_m2": leased_area_m2,
            "energy_kwh": energy_kwh,
            "lease_cost_eur": lease_cost_eur,
            "total_tco2e": round(kgCO2e / 1000, 4),
            "unit": "tCO2eq",
        }

    # ═══════════════════════════════════════════════════════════════
    # DOWNSTREAM CATEGORIES (9-15)
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def category_9_downstream_transportation(
        tkm: float = 0,
        transport_mode: str = "truck",
        distance_to_customer_km: float = 0,
        product_weight_tonnes: float = 0,
    ) -> Dict[str, Any]:
        """Cat.9: Downstream transportation and distribution."""
        kgCO2e = 0.0
        factors = {
            "truck": 0.062, "train": 0.022,
            "ship": 0.015, "air": 0.650, "van": 0.145,
        }
        if tkm:
            factor = factors.get(transport_mode, 0.062)
            kgCO2e = tkm * factor
        elif distance_to_customer_km and product_weight_tonnes:
            kgCO2e = distance_to_customer_km * product_weight_tonnes * 0.062

        return {
            "category": 9,
            "name": "Downstream transportation",
            "method": "distance_based",
            "tkm": tkm,
            "transport_mode": transport_mode,
            "total_tco2e": round(kgCO2e / 1000, 4),
            "unit": "tCO2eq",
        }

    @staticmethod
    def category_10_processing_of_sold_products(
        product_value_eur: float = 0,
        processing_type: str = "default",
    ) -> Dict[str, Any]:
        """Cat.10: Processing of sold products."""
        factor = PROCESSING_FACTORS.get(processing_type, PROCESSING_FACTORS["default"])
        kgCO2e = product_value_eur * factor

        return {
            "category": 10,
            "name": "Processing of sold products",
            "method": "value_based",
            "product_value_eur": product_value_eur,
            "processing_type": processing_type,
            "emission_factor": factor,
            "total_tco2e": round(kgCO2e / 1000, 4),
            "unit": "tCO2eq",
        }

    @staticmethod
    def category_11_use_of_sold_products(
        products_sold: int = 0,
        avg_energy_kwh_per_unit: float = 0,
        product_type: str = "default",
        product_value_eur: float = 0,
    ) -> Dict[str, Any]:
        """Cat.11: Use of sold products."""
        kgCO2e = 0.0
        if products_sold and avg_energy_kwh_per_unit:
            # Energy-based: products × kWh/unit × grid factor
            total_kwh = products_sold * avg_energy_kwh_per_unit
            kgCO2e = total_kwh * 0.276  # EU avg grid factor
        elif product_value_eur:
            # Value-based fallback
            factor = PRODUCT_USE_FACTORS.get(product_type, PRODUCT_USE_FACTORS["default"])
            kgCO2e = product_value_eur * factor

        return {
            "category": 11,
            "name": "Use of sold products",
            "method": "energy_based" if (products_sold and avg_energy_kwh_per_unit) else "value_based",
            "products_sold": products_sold,
            "avg_energy_kwh_per_unit": avg_energy_kwh_per_unit,
            "product_type": product_type,
            "total_tco2e": round(kgCO2e / 1000, 4),
            "unit": "tCO2eq",
        }

    @staticmethod
    def category_12_end_of_life_sold_products(
        product_weight_kg: float = 0,
        products_sold: int = 0,
        disposal_method: str = "landfill",
    ) -> Dict[str, Any]:
        """Cat.12: End-of-life treatment of sold products."""
        factor = END_OF_LIFE_FACTORS.get(disposal_method, END_OF_LIFE_FACTORS["landfill"])
        total_weight_kg = product_weight_kg * products_sold if products_sold else product_weight_kg
        kgCO2e = total_weight_kg * factor

        return {
            "category": 12,
            "name": "End-of-life of sold products",
            "method": "disposal_method_specific",
            "total_weight_kg": total_weight_kg,
            "disposal_method": disposal_method,
            "emission_factor": factor,
            "total_tco2e": round(kgCO2e / 1000, 4),
            "unit": "tCO2eq",
        }

    @staticmethod
    def category_13_downstream_leased_assets(
        leased_area_m2: float = 0,
        lessees: int = 0,
        total_energy_kwh: float = 0,
    ) -> Dict[str, Any]:
        """Cat.13: Downstream leased assets."""
        kgCO2e = 0.0
        if leased_area_m2:
            kgCO2e += leased_area_m2 * 30.0  # kgCO2e/m2 for leased property
        if total_energy_kwh:
            kgCO2e += total_energy_kwh * 0.276
        if lessees and kgCO2e == 0:
            kgCO2e = lessees * 500.0  # ~500 kgCO2e/lessee average

        return {
            "category": 13,
            "name": "Downstream leased assets",
            "method": "area_based" if leased_area_m2 else "estimate",
            "leased_area_m2": leased_area_m2,
            "lessees": lessees,
            "total_tco2e": round(kgCO2e / 1000, 4),
            "unit": "tCO2eq",
        }

    @staticmethod
    def category_14_franchises(
        num_franchises: int = 0,
        avg_energy_kwh_per_franchise: float = 0,
        franchise_revenue_eur: float = 0,
    ) -> Dict[str, Any]:
        """Cat.14: Franchises."""
        kgCO2e = 0.0
        if num_franchises and avg_energy_kwh_per_franchise:
            total_kwh = num_franchises * avg_energy_kwh_per_franchise
            kgCO2e = total_kwh * 0.276
        elif franchise_revenue_eur:
            kgCO2e = franchise_revenue_eur * 0.08  # spend-based estimate

        return {
            "category": 14,
            "name": "Franchises",
            "method": "energy_based" if (num_franchises and avg_energy_kwh_per_franchise) else "revenue_based",
            "num_franchises": num_franchises,
            "avg_energy_kwh_per_franchise": avg_energy_kwh_per_franchise,
            "total_tco2e": round(kgCO2e / 1000, 4),
            "unit": "tCO2eq",
        }

    @staticmethod
    def category_15_investments(
        investment_eur: float = 0,
        investment_type: str = "equity",
        portfolio_company_revenue_eur: float = 0,
    ) -> Dict[str, Any]:
        """Cat.15: Investments (for banks, insurance, investment firms)."""
        kgCO2e = 0.0
        if investment_eur:
            # Simple factor: ~0.10 kgCO2e/EUR invested (varies by sector)
            kgCO2e = investment_eur * 0.10
        if portfolio_company_revenue_eur:
            kgCO2e = portfolio_company_revenue_eur * 0.15

        return {
            "category": 15,
            "name": "Investments",
            "method": "investment_based",
            "investment_eur": investment_eur,
            "investment_type": investment_type,
            "total_tco2e": round(kgCO2e / 1000, 4),
            "unit": "tCO2eq",
        }

    # ═══════════════════════════════════════════════════════════════
    # TOTAL CALCULATORS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def calculate_upstream_total(
        company_nace: str,
        total_spend_eur: float = 0,
        category_results: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Calcola totale Scope 3 upstream (categorie 1-8)."""
        total_tco2e = 0.0
        categories = category_results or []

        # Se solo spend totale, usa metodo semplificato
        if total_spend_eur > 0 and not categories:
            factor = Scope3Calculator.get_factor(company_nace)
            kgCO2e = total_spend_eur * factor
            total_tco2e = round(kgCO2e / 1000, 4)
            categories = [{
                "category": 0,
                "name": "Simplified upstream estimate",
                "method": "total_spend_based",
                "total_spend_eur": total_spend_eur,
                "emission_factor": factor,
                "total_tco2e": total_tco2e,
            }]
        else:
            total_tco2e = sum(c.get("total_tco2e", 0) for c in categories)

        return {
            "scope": "3",
            "scope3_type": "upstream",
            "total_tco2e": round(total_tco2e, 4),
            "categories": categories,
            "methodology": "GHG Protocol Scope 3 Standard",
        }

    @staticmethod
    def calculate_downstream_total(
        categories: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Calcola totale Scope 3 downstream (categorie 9-15)."""
        total_tco2e = sum(c.get("total_tco2e", 0) for c in (categories or []))
        return {
            "scope": "3",
            "scope3_type": "downstream",
            "total_tco2e": round(total_tco2e, 4),
            "categories": categories or [],
            "methodology": "GHG Protocol Scope 3 Standard",
        }

    @staticmethod
    def calculate_total_scope3(
        upstream: Optional[Dict] = None,
        downstream: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Calcola il totale Scope 3 aggregato (upstream + downstream)."""
        upstream_tco2e = upstream.get("total_tco2e", 0) if upstream else 0
        downstream_tco2e = downstream.get("total_tco2e", 0) if downstream else 0
        total = upstream_tco2e + downstream_tco2e

        all_categories = []
        if upstream:
            all_categories.extend(upstream.get("categories", []))
        if downstream:
            all_categories.extend(downstream.get("categories", []))

        return {
            "scope": "3",
            "total_tco2e": round(total, 4),
            "upstream_total": round(upstream_tco2e, 4),
            "downstream_total": round(downstream_tco2e, 4),
            "categories": all_categories,
            "method": "ghg_protocol_scope3",
            "methodology": "GHG Protocol Scope 3 Standard (all 15 categories)",
        }
