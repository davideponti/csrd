"""CSRD Comply — Emissions Data & Carbon Calculator endpoints (Steps 12-16)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User, Company, EmissionsData
from ai_engine.carbon_calculator.scope1 import Scope1Calculator
from ai_engine.carbon_calculator.scope2 import Scope2Calculator
from ai_engine.carbon_calculator.scope3 import Scope3Calculator
from ai_engine.carbon_calculator.data_collector import DataCollectorService
from ai_engine.carbon_calculator.validation_engine import ValidationEngine

router = APIRouter()

# ── Schemas ──────────────────────────────────────────────────────

class EmissionResponse(BaseModel):
    id: uuid.UUID
    reporting_year: int
    scope: str
    category: Optional[str] = None
    value: float
    unit: str
    calculation_method: Optional[str] = None
    emission_factor_source: Optional[str] = None
    verified: bool

    class Config:
        from_attributes = True


class EmissionCreate(BaseModel):
    reporting_year: int
    scope: str
    category: Optional[str] = None
    value: float
    unit: str = "tCO2eq"
    calculation_method: Optional[str] = None
    emission_factor_source: Optional[str] = None


class ProcessEmissionsInput(BaseModel):
    cement_tonnes: Optional[float] = None
    steel_tonnes_bf_bof: Optional[float] = None
    steel_tonnes_eaf: Optional[float] = None
    ammonia_tonnes: Optional[float] = None
    ethylene_tonnes: Optional[float] = None
    methanol_tonnes: Optional[float] = None
    aluminium_tonnes: Optional[float] = None
    glass_tonnes: Optional[float] = None
    paper_tonnes: Optional[float] = None
    food_tonnes: Optional[float] = None
    refrigerant_leak_kg: Optional[float] = None


class Scope1Input(BaseModel):
    natural_gas_kwh: Optional[float] = None
    natural_gas_m3: Optional[float] = None
    diesel_heating_litres: Optional[float] = None
    lpg_kwh: Optional[float] = None
    lpg_litres: Optional[float] = None
    biomass_kwh: Optional[float] = None
    diesel_km: Optional[float] = None
    petrol_km: Optional[float] = None
    diesel_van_km: Optional[float] = None
    diesel_truck_km: Optional[float] = None
    electric_km: Optional[float] = None
    r410a_kg: Optional[float] = None
    r134a_kg: Optional[float] = None
    r32_kg: Optional[float] = None
    r290_kg: Optional[float] = None


class Scope2Input(BaseModel):
    electricity_kwh: float
    country: str = "EU_avg"
    has_green_tariff: bool = False


class Scope3Input(BaseModel):
    spend_eur: Optional[float] = None
    supplier_nace: str = "DEFAULT"
    employees: Optional[int] = None
    avg_commute_km: Optional[float] = 20.0
    business_travel_km: Optional[float] = None
    waste_kg: Optional[float] = None
    # New fields for all 15 categories
    capital_goods_eur: Optional[float] = None
    capital_goods_nace: Optional[str] = None
    electricity_kwh: Optional[float] = None
    natural_gas_kwh_scope3: Optional[float] = None
    diesel_litres_scope3: Optional[float] = None
    upstream_tkm: Optional[float] = None
    upstream_transport_mode: Optional[str] = "truck"
    waste_type: Optional[str] = "mixed_waste"
    travel_mode: Optional[str] = "car_diesel"
    commuting_mode: Optional[str] = "car_alone"
    working_days: Optional[int] = 220
    leased_area_m2: Optional[float] = None
    lease_cost_eur: Optional[float] = None
    downstream_tkm: Optional[float] = None
    downstream_transport_mode: Optional[str] = "truck"
    distance_to_customer_km: Optional[float] = None
    product_weight_tonnes: Optional[float] = None
    product_value_eur: Optional[float] = None
    processing_type: Optional[str] = "default"
    products_sold: Optional[int] = None
    avg_energy_kwh_per_unit: Optional[float] = None
    product_type: Optional[str] = "default"
    product_weight_kg: Optional[float] = None
    disposal_method: Optional[str] = "landfill"
    downstream_leased_area_m2: Optional[float] = None
    lessees: Optional[int] = None
    num_franchises: Optional[int] = None
    avg_energy_kwh_per_franchise: Optional[float] = None
    franchise_revenue_eur: Optional[float] = None
    investment_eur: Optional[float] = None
    investment_type: Optional[str] = "equity"
    portfolio_company_revenue_eur: Optional[float] = None


class SaveEmissionsInput(BaseModel):
    reporting_year: int
    scope: str
    total_tco2e: float
    category: Optional[str] = None
    calculation_method: str = "calculator"
    breakdown: Optional[dict] = None


class ValidationInput(BaseModel):
    scope1_tco2e: float = 0
    scope2_tco2e: float = 0
    scope3_tco2e: float = 0
    employee_count: int = 1
    sector_code: str = "DEFAULT"
    has_stationary: bool = False
    has_mobile: bool = False
    has_scope2: bool = False
    has_scope3: bool = False
    has_fleet: bool = False


# ── Endpoints ────────────────────────────────────────────────────

@router.get("/", response_model=list[EmissionResponse])
def list_emissions(
    scope: Optional[str] = None,
    year: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List emissions data for the user's company with pagination."""
    query = db.query(EmissionsData).filter(
        EmissionsData.company_id == current_user.company_id
    )
    if scope:
        query = query.filter(EmissionsData.scope == scope)
    if year:
        query = query.filter(EmissionsData.reporting_year == year)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=EmissionResponse, status_code=201)
def create_emission(
    data: EmissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a new emissions data point."""
    emission = EmissionsData(
        company_id=current_user.company_id,
        **data.model_dump(),
    )
    db.add(emission)
    db.commit()
    db.refresh(emission)
    return emission


@router.get("/factors")
def get_emission_factors(
    current_user: User = Depends(get_current_user),
):
    """Get available emission factors."""
    company = None  # We'll get from DB in real scenario
    factors = Scope1Calculator.get_emission_factors()
    return factors


@router.post("/calculate/scope1")
def calculate_scope1(
    data: Scope1Input,
    current_user: User = Depends(get_current_user),
):
    """Calculate Scope 1 emissions from input activity data."""
    stationary = Scope1Calculator.calculate_stationary_combustion(
        natural_gas_kwh=data.natural_gas_kwh,
        natural_gas_m3=data.natural_gas_m3,
        diesel_heating_litres=data.diesel_heating_litres,
        lpg_kwh=data.lpg_kwh,
    )
    mobile = Scope1Calculator.calculate_mobile_combustion(
        diesel_km=data.diesel_km,
        petrol_km=data.petrol_km,
        diesel_van_km=data.diesel_van_km,
        diesel_truck_km=data.diesel_truck_km,
        electric_km=data.electric_km,
    )
    fugitive = Scope1Calculator.calculate_fugitive_emissions(
        r410a_kg=data.r410a_kg,
        r134a_kg=data.r134a_kg,
    )
    result = Scope1Calculator.calculate_total_scope1(stationary, mobile, fugitive)
    return result


@router.post("/calculate/scope1/process")
def calculate_scope1_process(
    data: ProcessEmissionsInput,
    current_user: User = Depends(get_current_user),
):
    """Calculate Scope 1 process emissions from industrial production data."""
    result = Scope1Calculator.calculate_process_emissions(
        cement_tonnes=data.cement_tonnes,
        steel_tonnes_bf_bof=data.steel_tonnes_bf_bof,
        steel_tonnes_eaf=data.steel_tonnes_eaf,
        ammonia_tonnes=data.ammonia_tonnes,
        ethylene_tonnes=data.ethylene_tonnes,
        methanol_tonnes=data.methanol_tonnes,
        aluminium_tonnes=data.aluminium_tonnes,
        glass_tonnes=data.glass_tonnes,
        paper_tonnes=data.paper_tonnes,
        food_tonnes=data.food_tonnes,
        refrigerant_leak_kg=data.refrigerant_leak_kg,
    )
    return result


@router.post("/calculate/scope2")
def calculate_scope2(
    data: Scope2Input,
    current_user: User = Depends(get_current_user),
):
    """Calculate Scope 2 emissions (both location and market based)."""
    result = Scope2Calculator.calculate_both_methods(
        electricity_kwh=data.electricity_kwh,
        country=data.country,
        has_green_tariff=data.has_green_tariff,
    )
    return result


@router.post("/calculate/scope3")
def calculate_scope3(
    data: Scope3Input,
    current_user: User = Depends(get_current_user),
):
    """Calculate Scope 3 emissions per tutte le 15 categorie."""
    upstream_categories = []
    downstream_categories = []

    # ── UPSTREAM: Category 1-8 ─────────────────────────────────

    # Cat.1: Purchased goods and services
    if data.spend_eur:
        upstream_categories.append(
            Scope3Calculator.category_1_purchased_goods_spend_based(
                spend_eur=data.spend_eur,
                supplier_nace=data.supplier_nace,
            )
        )

    # Cat.2: Capital goods
    if data.capital_goods_eur:
        upstream_categories.append(
            Scope3Calculator.category_2_capital_goods(
                spend_eur=data.capital_goods_eur,
                nace_code=data.capital_goods_nace or data.supplier_nace,
            )
        )

    # Cat.3: Fuel and energy related activities
    if data.electricity_kwh or data.natural_gas_kwh_scope3 or data.diesel_litres_scope3:
        upstream_categories.append(
            Scope3Calculator.category_3_fuel_and_energy_related(
                electricity_kwh=data.electricity_kwh or 0,
                natural_gas_kwh=data.natural_gas_kwh_scope3 or 0,
                diesel_litres=data.diesel_litres_scope3 or 0,
            )
        )

    # Cat.4: Upstream transportation
    if data.upstream_tkm:
        upstream_categories.append(
            Scope3Calculator.category_4_upstream_transportation(
                tkm=data.upstream_tkm,
                transport_mode=data.upstream_transport_mode or "truck",
            )
        )

    # Cat.5: Waste generated
    if data.waste_kg:
        upstream_categories.append(
            Scope3Calculator.category_5_waste_generated(
                waste_kg=data.waste_kg,
                waste_type=data.waste_type or "mixed_waste",
            )
        )

    # Cat.6: Business travel
    if data.business_travel_km:
        upstream_categories.append(
            Scope3Calculator.category_6_business_travel(
                km=data.business_travel_km,
                travel_mode=data.travel_mode or "car_diesel",
            )
        )

    # Cat.7: Employee commuting
    if data.employees:
        upstream_categories.append(
            Scope3Calculator.category_7_employee_commuting(
                employees=data.employees,
                avg_commute_km=data.avg_commute_km or 20.0,
                commuting_mode=data.commuting_mode or "car_alone",
                working_days=data.working_days or 220,
            )
        )

    # Cat.8: Upstream leased assets
    if data.leased_area_m2 or data.lease_cost_eur:
        upstream_categories.append(
            Scope3Calculator.category_8_upstream_leased_assets(
                leased_area_m2=data.leased_area_m2 or 0,
                energy_kwh=data.electricity_kwh or 0,
                lease_cost_eur=data.lease_cost_eur or 0,
            )
        )

    # ── DOWNSTREAM: Category 9-15 ───────────────────────────────

    # Cat.9: Downstream transportation
    if data.downstream_tkm or (data.distance_to_customer_km and data.product_weight_tonnes):
        downstream_categories.append(
            Scope3Calculator.category_9_downstream_transportation(
                tkm=data.downstream_tkm or 0,
                transport_mode=data.downstream_transport_mode or "truck",
                distance_to_customer_km=data.distance_to_customer_km or 0,
                product_weight_tonnes=data.product_weight_tonnes or 0,
            )
        )

    # Cat.10: Processing of sold products
    if data.product_value_eur:
        downstream_categories.append(
            Scope3Calculator.category_10_processing_of_sold_products(
                product_value_eur=data.product_value_eur,
                processing_type=data.processing_type or "default",
            )
        )

    # Cat.11: Use of sold products
    if data.products_sold or data.product_value_eur:
        downstream_categories.append(
            Scope3Calculator.category_11_use_of_sold_products(
                products_sold=data.products_sold or 0,
                avg_energy_kwh_per_unit=data.avg_energy_kwh_per_unit or 0,
                product_type=data.product_type or "default",
                product_value_eur=data.product_value_eur or 0,
            )
        )

    # Cat.12: End-of-life of sold products
    if data.product_weight_kg:
        downstream_categories.append(
            Scope3Calculator.category_12_end_of_life_sold_products(
                product_weight_kg=data.product_weight_kg,
                products_sold=data.products_sold or 0,
                disposal_method=data.disposal_method or "landfill",
            )
        )

    # Cat.13: Downstream leased assets
    if data.downstream_leased_area_m2 or data.lessees:
        downstream_categories.append(
            Scope3Calculator.category_13_downstream_leased_assets(
                leased_area_m2=data.downstream_leased_area_m2 or 0,
                lessees=data.lessees or 0,
                total_energy_kwh=data.electricity_kwh or 0,
            )
        )

    # Cat.14: Franchises
    if data.num_franchises or data.franchise_revenue_eur:
        downstream_categories.append(
            Scope3Calculator.category_14_franchises(
                num_franchises=data.num_franchises or 0,
                avg_energy_kwh_per_franchise=data.avg_energy_kwh_per_franchise or 0,
                franchise_revenue_eur=data.franchise_revenue_eur or 0,
            )
        )

    # Cat.15: Investments
    if data.investment_eur or data.portfolio_company_revenue_eur:
        downstream_categories.append(
            Scope3Calculator.category_15_investments(
                investment_eur=data.investment_eur or 0,
                investment_type=data.investment_type or "equity",
                portfolio_company_revenue_eur=data.portfolio_company_revenue_eur or 0,
            )
        )

    # ── TOTALS ──────────────────────────────────────────────────

    upstream_total = None
    if upstream_categories:
        upstream_total = Scope3Calculator.calculate_upstream_total(
            company_nace=data.supplier_nace,
            category_results=upstream_categories,
        )

    downstream_total = None
    if downstream_categories:
        downstream_total = Scope3Calculator.calculate_downstream_total(
            categories=downstream_categories,
        )

    # Total Scope 3
    total = Scope3Calculator.calculate_total_scope3(
        upstream=upstream_total,
        downstream=downstream_total,
    )

    return total



@router.post("/save-calculated")
def save_calculated_emissions(
    data: SaveEmissionsInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save calculated emissions to the database."""
    emission = EmissionsData(
        company_id=current_user.company_id,
        reporting_year=data.reporting_year,
        scope=data.scope,
        category=data.category,
        value=data.total_tco2e,
        unit="tCO2eq",
        calculation_method=data.calculation_method,
        emission_factor_source="carbon_calculator",
    )
    db.add(emission)
    db.commit()
    db.refresh(emission)
    return emission


@router.post("/validate")
def validate_emissions_data(
    data: ValidationInput,
    current_user: User = Depends(get_current_user),
):
    """Validate emissions data with AI checks."""
    result = ValidationEngine.validate_all(
        scope1_tco2e=data.scope1_tco2e,
        scope2_tco2e=data.scope2_tco2e,
        scope3_tco2e=data.scope3_tco2e,
        employee_count=data.employee_count,
        sector_code=data.sector_code,
        has_stationary=data.has_stationary,
        has_mobile=data.has_mobile,
        has_scope2=data.has_scope2,
        has_scope3=data.has_scope3,
        has_fleet=data.has_fleet,
    )
    return result


@router.post("/parse-bill")
def parse_utility_bill(
    text: str,
    current_user: User = Depends(get_current_user),
):
    """Parse utility bill text extracted via OCR."""
    result = DataCollectorService.parse_utility_bill_pdf_text(text)
    return result


@router.get("/summary")
def get_emissions_summary(
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get emissions summary by scope."""
    query = db.query(EmissionsData).filter(
        EmissionsData.company_id == current_user.company_id
    )
    if year:
        query = query.filter(EmissionsData.reporting_year == year)

    emissions = query.all()

    summary = {"scope1": 0.0, "scope2": 0.0, "scope3": 0.0, "total": 0.0}
    for e in emissions:
        key = f"scope{e.scope}"
        if e.scope in ["1", "2", "3"]:
            summary[key] += e.value
    summary["total"] = summary["scope1"] + summary["scope2"] + summary["scope3"]

    # Validation
    company = db.query(Company).filter(
        Company.company_id == current_user.company_id
    ).first()
    validation = None
    if company:
        validation = ValidationEngine.validate_all(
            scope1_tco2e=summary["scope1"],
            scope2_tco2e=summary["scope2"],
            scope3_tco2e=summary["scope3"],
            employee_count=company.employee_count or 1,
            sector_code=company.sector,
        )

    return {
        "summary": summary,
        "validation": validation,
    }
