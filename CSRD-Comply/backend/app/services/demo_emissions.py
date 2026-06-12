"""
Profilo emissioni realistico per PMI manifatturiera italiana (NACE C10).

Usa i calculator GHG Protocol esistenti con dati di attività plausibili,
scalati in base a dipendenti e fatturato dell'azienda.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import Company, EmissionsData, CompanyContextSettings
from ai_engine.carbon_calculator.scope1 import Scope1Calculator
from ai_engine.carbon_calculator.scope2 import Scope2Calculator
from ai_engine.carbon_calculator.scope3 import Scope3Calculator

# Profilo base: PMI alimentare italiana, ~150 dipendenti, 1 sito produttivo
BASE_EMPLOYEES = 150
BASE_TURNOVER_EUR = 18_500_000


def _scale(company: Company) -> float:
    employees = company.employee_count or BASE_EMPLOYEES
    emp_scale = employees / BASE_EMPLOYEES
    if company.turnover and company.turnover > 0:
        turnover_scale = company.turnover / BASE_TURNOVER_EUR
        return (emp_scale + turnover_scale) / 2
    return emp_scale


def _round_activity(value: float) -> float:
    return round(value, 2)


def build_activity_profile(company: Company, year_factor: float = 1.0) -> dict[str, Any]:
    """Costruisce input di attività realistici per i tre scope."""
    scale = _scale(company) * year_factor
    employees = int((company.employee_count or BASE_EMPLOYEES) * year_factor)
    country = (company.country or "IT").upper()
    if len(country) > 2:
        country = "IT"
    sector = company.sector or "C10"
    turnover = company.turnover or BASE_TURNOVER_EUR * _scale(company)

    scope1_input = {
        "natural_gas_kwh": _round_activity(720_000 * scale),
        "diesel_heating_litres": _round_activity(8_500 * scale),
        "diesel_km": _round_activity(42_000 * scale),
        "diesel_van_km": _round_activity(31_000 * scale),
        "petrol_km": _round_activity(12_000 * scale),
        "r410a_kg": _round_activity(6.5 * scale),
        "r134a_kg": _round_activity(2.0 * scale),
    }

    process_input = {}
    if sector.startswith("C"):
        process_input["food_tonnes"] = _round_activity(1_200 * scale)

    scope2_input = {
        "electricity_kwh": _round_activity(1_150_000 * scale),
        "country": country if country in {"IT", "DE", "FR", "ES", "UK", "NL", "BE", "AT"} else "IT",
        "has_green_tariff": True,
    }

    scope3_input = {
        "spend_eur": _round_activity(turnover * 0.34),
        "supplier_nace": sector,
        "capital_goods_eur": _round_activity(380_000 * scale),
        "electricity_kwh": _round_activity(95_000 * scale),
        "natural_gas_kwh_scope3": _round_activity(72_000 * scale),
        "diesel_litres_scope3": _round_activity(4_500 * scale),
        "upstream_tkm": _round_activity(118_000 * scale),
        "upstream_transport_mode": "truck",
        "waste_kg": _round_activity(38_000 * scale),
        "waste_type": "mixed_waste",
        "business_travel_km": _round_activity(145_000 * scale),
        "travel_mode": "car_diesel",
        "employees": employees,
        "avg_commute_km": 18.5,
        "commuting_mode": "car_alone",
        "working_days": 220,
        "leased_area_m2": _round_activity(2_400 * scale),
        "downstream_tkm": _round_activity(82_000 * scale),
        "downstream_transport_mode": "truck",
        "distance_to_customer_km": 450,
        "product_weight_tonnes": _round_activity(720 * scale),
        "product_value_eur": _round_activity(turnover * 0.78),
        "products_sold": int(2_400_000 * scale),
        "product_weight_kg": _round_activity(0.85 * scale),
        "disposal_method": "landfill",
    }

    return {
        "scope1_input": scope1_input,
        "process_input": process_input,
        "scope2_input": scope2_input,
        "scope3_input": scope3_input,
        "profile_label": f"PMI manifatturiera {country} — {employees} dipendenti, settore {sector}",
    }


def calculate_emissions_from_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Esegue i calculator sui dati di attività."""
    s1 = profile["scope1_input"]
    stationary = Scope1Calculator.calculate_stationary_combustion(
        natural_gas_kwh=s1.get("natural_gas_kwh"),
        diesel_heating_litres=s1.get("diesel_heating_litres"),
    )
    mobile = Scope1Calculator.calculate_mobile_combustion(
        diesel_km=s1.get("diesel_km"),
        petrol_km=s1.get("petrol_km"),
        diesel_van_km=s1.get("diesel_van_km"),
    )
    fugitive = Scope1Calculator.calculate_fugitive_emissions(
        r410a_kg=s1.get("r410a_kg"),
        r134a_kg=s1.get("r134a_kg"),
    )
    process = None
    if profile["process_input"]:
        process = Scope1Calculator.calculate_process_emissions(**profile["process_input"])

    scope1 = Scope1Calculator.calculate_total_scope1(stationary, mobile, fugitive, process)

    s2 = profile["scope2_input"]
    scope2 = Scope2Calculator.calculate_both_methods(
        electricity_kwh=s2["electricity_kwh"],
        country=s2["country"],
        has_green_tariff=s2["has_green_tariff"],
    )

    s3 = profile["scope3_input"]
    upstream_categories = []
    downstream_categories = []

    upstream_categories.append(
        Scope3Calculator.category_1_purchased_goods_spend_based(
            spend_eur=s3["spend_eur"],
            supplier_nace=s3["supplier_nace"],
        )
    )
    upstream_categories.append(
        Scope3Calculator.category_2_capital_goods(
            spend_eur=s3["capital_goods_eur"],
            nace_code=s3["supplier_nace"],
        )
    )
    upstream_categories.append(
        Scope3Calculator.category_3_fuel_and_energy_related(
            electricity_kwh=s3["electricity_kwh"],
            natural_gas_kwh=s3["natural_gas_kwh_scope3"],
            diesel_litres=s3["diesel_litres_scope3"],
        )
    )
    upstream_categories.append(
        Scope3Calculator.category_4_upstream_transportation(
            tkm=s3["upstream_tkm"],
            transport_mode=s3["upstream_transport_mode"],
        )
    )
    upstream_categories.append(
        Scope3Calculator.category_5_waste_generated(
            waste_kg=s3["waste_kg"],
            waste_type=s3["waste_type"],
        )
    )
    upstream_categories.append(
        Scope3Calculator.category_6_business_travel(
            km=s3["business_travel_km"],
            travel_mode=s3["travel_mode"],
        )
    )
    upstream_categories.append(
        Scope3Calculator.category_7_employee_commuting(
            employees=s3["employees"],
            avg_commute_km=s3["avg_commute_km"],
            commuting_mode=s3["commuting_mode"],
            working_days=s3["working_days"],
        )
    )
    upstream_categories.append(
        Scope3Calculator.category_8_upstream_leased_assets(
            leased_area_m2=s3["leased_area_m2"],
            energy_kwh=s3["electricity_kwh"] * 0.15,
        )
    )
    downstream_categories.append(
        Scope3Calculator.category_9_downstream_transportation(
            distance_to_customer_km=s3["distance_to_customer_km"],
            product_weight_tonnes=s3["product_weight_tonnes"],
            transport_mode=s3["downstream_transport_mode"],
        )
    )
    downstream_categories.append(
        Scope3Calculator.category_10_processing_of_sold_products(
            product_value_eur=s3["product_value_eur"],
        )
    )
    downstream_categories.append(
        Scope3Calculator.category_11_use_of_sold_products(
            products_sold=s3["products_sold"],
            product_value_eur=s3["product_value_eur"],
        )
    )
    downstream_categories.append(
        Scope3Calculator.category_12_end_of_life_sold_products(
            product_weight_kg=s3["product_weight_kg"],
            products_sold=min(s3["products_sold"], 500_000),
            disposal_method=s3["disposal_method"],
        )
    )

    upstream_total = Scope3Calculator.calculate_upstream_total(
        company_nace=s3["supplier_nace"],
        category_results=upstream_categories,
    )
    downstream_total = Scope3Calculator.calculate_downstream_total(
        categories=downstream_categories,
    )
    scope3 = Scope3Calculator.calculate_total_scope3(
        upstream=upstream_total,
        downstream=downstream_total,
    )

    return {
        "scope1": scope1,
        "scope2": scope2,
        "scope3": scope3,
    }


def _save_emission(
    db: Session,
    company_id,
    reporting_year: int,
    scope: str,
    value: float,
    category: str | None,
    calculation_method: str,
) -> EmissionsData:
    record = EmissionsData(
        company_id=company_id,
        reporting_year=reporting_year,
        scope=scope,
        category=category,
        value=value,
        unit="tCO2eq",
        calculation_method=calculation_method,
        emission_factor_source="carbon_calculator",
        verified=False,
    )
    db.add(record)
    return record


def persist_calculated_emissions(
    db: Session,
    company: Company,
    reporting_year: int,
    calculated: dict[str, Any],
) -> list[EmissionsData]:
    """Salva i risultati calcolati nel DB."""
    records: list[EmissionsData] = []

    scope1 = calculated["scope1"]
    records.append(_save_emission(
        db, company.company_id, reporting_year, "1",
        scope1["total_tco2e"], "scope1_total", "activity_data_x_emission_factors",
    ))

    scope2 = calculated["scope2"]
    records.append(_save_emission(
        db, company.company_id, reporting_year, "2",
        scope2["location_based"]["total_tco2e"], "scope2_location_based", "location_based",
    ))
    records.append(_save_emission(
        db, company.company_id, reporting_year, "2",
        scope2["market_based"]["total_tco2e"], "scope2_market_based", "market_based",
    ))

    scope3 = calculated["scope3"]
    records.append(_save_emission(
        db, company.company_id, reporting_year, "3",
        scope3["total_tco2e"], "scope3_total", "ghg_protocol_scope3",
    ))

    return records


def sync_company_context_ghg(
    db: Session,
    company: Company,
    reporting_year: int,
    calculated: dict[str, Any],
) -> None:
    """Allinea CompanyContextSettings per i placeholder del report."""
    ctx = db.query(CompanyContextSettings).filter(
        CompanyContextSettings.company_id == company.company_id,
    ).first()
    if not ctx:
        ctx = CompanyContextSettings(company_id=company.company_id)
        db.add(ctx)

    scope1 = calculated["scope1"]["total_tco2e"]
    scope2_loc = calculated["scope2"]["location_based"]["total_tco2e"]
    scope2_mkt = calculated["scope2"]["market_based"]["total_tco2e"]
    scope3 = calculated["scope3"]["total_tco2e"]

    ctx.company_name = ctx.company_name or company.company_name
    ctx.country = ctx.country or company.country
    ctx.sector = ctx.sector or company.sector
    ctx.reporting_year = reporting_year
    ctx.employee_count_total = ctx.employee_count_total or company.employee_count
    ctx.annual_revenue_eur = ctx.annual_revenue_eur or company.turnover
    ctx.scope1_emissions = scope1
    ctx.scope2_location_based = scope2_loc
    ctx.scope2_market_based = scope2_mkt
    ctx.scope3_total = scope3
    ctx.emissions_baseline_year = reporting_year - 1
    ctx.emissions_methodology = ctx.emissions_methodology or "GHG Protocol Corporate Standard"


def auto_fill_emissions(
    db: Session,
    company: Company,
    reporting_year: int,
    *,
    include_previous_year: bool = True,
    replace_existing: bool = True,
) -> dict[str, Any]:
    """
    Compila automaticamente Scope 1, 2 e 3 con dati realistici calcolati.
    """
    years = [reporting_year]
    if include_previous_year:
        years.insert(0, reporting_year - 1)

    if replace_existing:
        db.query(EmissionsData).filter(
            EmissionsData.company_id == company.company_id,
            EmissionsData.reporting_year.in_(years),
        ).delete(synchronize_session=False)

    summaries: dict[int, dict[str, float]] = {}
    total_records = 0
    latest_profile = None
    latest_calculated = None

    for year in years:
        # Anno precedente leggermente più alto (miglioramento YoY realistico)
        year_factor = 1.08 if year < reporting_year else 1.0
        profile = build_activity_profile(company, year_factor=year_factor)
        calculated = calculate_emissions_from_profile(profile)
        persist_calculated_emissions(db, company, year, calculated)

        if year == reporting_year:
            sync_company_context_ghg(db, company, year, calculated)
            latest_profile = profile
            latest_calculated = calculated

        s1 = calculated["scope1"]["total_tco2e"]
        s2 = calculated["scope2"]["location_based"]["total_tco2e"]
        s3 = calculated["scope3"]["total_tco2e"]
        summaries[year] = {
            "scope1": s1,
            "scope2": s2,
            "scope3": s3,
            "total": round(s1 + s2 + s3, 4),
        }
        total_records += 4

    db.commit()

    return {
        "message": "Dati emissioni compilati automaticamente con profilo PMI realistico.",
        "profile": latest_profile["profile_label"] if latest_profile else "",
        "years_filled": years,
        "summaries": summaries,
        "inputs": {
            "scope1": latest_profile["scope1_input"] if latest_profile else {},
            "process": latest_profile["process_input"] if latest_profile else {},
            "scope2": latest_profile["scope2_input"] if latest_profile else {},
            "scope3": latest_profile["scope3_input"] if latest_profile else {},
        },
        "records_created": total_records,
        "calculated": {
            "scope1_tco2e": latest_calculated["scope1"]["total_tco2e"] if latest_calculated else 0,
            "scope2_location_tco2e": latest_calculated["scope2"]["location_based"]["total_tco2e"] if latest_calculated else 0,
            "scope2_market_tco2e": latest_calculated["scope2"]["market_based"]["total_tco2e"] if latest_calculated else 0,
            "scope3_tco2e": latest_calculated["scope3"]["total_tco2e"] if latest_calculated else 0,
        },
    }
