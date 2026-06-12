"""
Profilo aziendale demo coerente per report CSRD (S1, S2, G1, E2).

Genera KPI scalati su dipendenti/fatturato/settore con valori distinti
per ogni placeholder — evita clonazioni irrealistiche (es. 500 works councils).
"""
from __future__ import annotations

import math
from typing import Any

from sqlalchemy.orm import Session

from app.models import Company, CompanyContext, CompanyContextSettings

BASE_EMPLOYEES = 150
BASE_TURNOVER_EUR = 18_500_000
DEMO_COMPANY_NAME = "Alimentari Nord S.r.l."
PLACEHOLDER_NAMES = frozenset({"ciao", "test", "demo", "company", "azienda", "my company", ""})


def _is_placeholder_name(name: str | None) -> bool:
    if not name or not name.strip():
        return True
    return name.strip().lower() in PLACEHOLDER_NAMES


def _country_code(country: str | None) -> str:
    if not country:
        return "IT"
    c = country.strip().upper()
    if c in {"IT", "ITALY", "ITALIA"}:
        return "IT"
    if len(c) <= 5:
        return c[:5]
    return "IT"


def build_demo_company_record(company: Company, reporting_year: int) -> dict[str, Any]:
    """Profilo anagrafico PMI manifatturiera italiana (tab Impostazioni > Azienda)."""
    scale = _scale(company)
    employees = max(BASE_EMPLOYEES, company.employee_count or BASE_EMPLOYEES)
    if employees > 400 and _is_placeholder_name(company.company_name):
        employees = BASE_EMPLOYEES
    turnover = company.turnover if company.turnover and company.turnover > 0 else BASE_TURNOVER_EUR * scale
    name = company.company_name if not _is_placeholder_name(company.company_name) else DEMO_COMPANY_NAME
    sector = (company.sector or "C10").split("—")[0].split("-")[0].strip()[:10] or "C10"

    company_fields = {
        "company_name": name,
        "vat_number": company.vat_number or "IT01234567890",
        "country": _country_code(company.country),
        "sector": sector,
        "employee_count": employees,
        "turnover": turnover,
        "reporting_year": reporting_year,
        "balance_sheet_total": round(turnover * 0.72, 2),
    }

    profile_extras = {
        "legal_form": "S.r.l.",
        "fiscal_year": reporting_year,
        "address": "Via dell'Industria, 12",
        "city": "Parma",
        "province": "PR",
        "zip_code": "43122",
        "website": "https://www.alimentarinord.it",
        "phone": "+39 0521 123456",
        "pec": "alimentarinord@pec.it",
        "sdi_code": "SUBM70N",
        "country_display": "Italia",
    }

    return {"company": company_fields, "profile_extras": profile_extras}


def sync_demo_company_record(
    db: Session,
    company: Company,
    reporting_year: int,
    *,
    overwrite: bool = True,
) -> dict[str, Any]:
    """Aggiorna la tabella companies con dati demo realistici."""
    record = build_demo_company_record(company, reporting_year)
    for key, value in record["company"].items():
        if not overwrite and getattr(company, key, None) not in (None, "", 0):
            continue
        setattr(company, key, value)
    return record


def sync_demo_assessment_context(db: Session, company: Company) -> dict[str, Any]:
    """Popola company_context per assessment / doppia materialità."""
    ctx = db.query(CompanyContext).filter(
        CompanyContext.company_id == company.company_id,
    ).first()
    if not ctx:
        ctx = CompanyContext(company_id=company.company_id)
        db.add(ctx)

    sector = company.sector or "C10"
    name = company.company_name or DEMO_COMPANY_NAME
    employees = company.employee_count or BASE_EMPLOYEES

    data = {
        "value_chain_description": (
            f"{name} è una PMI manifatturiera del settore alimentare (NACE {sector}) "
            f"con {employees} dipendenti. La catena del valore comprende approvvigionamento "
            f"di materie prime agricole, trasformazione e confezionamento, distribuzione B2B "
            f"verso GDO e clienti industriali in Italia e nell'UE."
        ),
        "key_activities": [
            "Trasformazione e confezionamento prodotti alimentari",
            "Controllo qualità e sicurezza alimentare (HACCP)",
            "Logistica e distribuzione nazionale",
            "Ricerca e sviluppo formulazioni a minor impatto ambientale",
        ],
        "business_relationships": {
            "suppliers": "85 fornitori Tier 1 (materie prime, packaging, servizi)",
            "customers": "GDO, distributori B2B, clienti food service",
            "partners": "Consorzi di filiera, enti di certificazione, utility energetiche",
        },
        "geographical_scope": ["Italia", "Germania", "Spagna", "Romania"],
        "stakeholder_groups": [
            "Dipendenti e rappresentanti sindacali",
            "Fornitori e lavoratori della filiera",
            "Clienti e consumatori finali",
            "Comunità locali e autorità ambientali",
            "Investitori e istituti di credito",
        ],
    }

    ctx.value_chain_description = data["value_chain_description"]
    ctx.key_activities = data["key_activities"]
    ctx.business_relationships = data["business_relationships"]
    ctx.geographical_scope = data["geographical_scope"]
    ctx.stakeholder_groups = data["stakeholder_groups"]
    return data


def auto_fill_company_profile(
    db: Session,
    company: Company,
    reporting_year: int,
    *,
    fill_emissions: bool = True,
    overwrite: bool = True,
) -> dict[str, Any]:
    """
    Compila in un'unica operazione:
    - Dati azienda (companies)
    - Contesto report (company_context_settings + extended_kpis)
    - Contesto assessment (company_context)
    - Emissioni GHG (opzionale)
    """
    company_record = sync_demo_company_record(db, company, reporting_year, overwrite=overwrite)
    db.flush()

    emissions_result = None
    if fill_emissions:
        from app.services.demo_emissions import auto_fill_emissions
        emissions_result = auto_fill_emissions(
            db,
            company,
            reporting_year,
            include_previous_year=True,
            replace_existing=overwrite,
        )
    else:
        sync_full_demo_context(db, company, reporting_year, overwrite=overwrite)

    assessment_context = sync_demo_assessment_context(db, company)
    db.commit()

    ctx = db.query(CompanyContextSettings).filter(
        CompanyContextSettings.company_id == company.company_id,
    ).first()

    extended_count = len((ctx.extended_kpis or {}) if ctx else {})

    return {
        "message": (
            "Profilo aziendale demo compilato: dati azienda, contesto report, "
            "contesto assessment ed emissioni GHG."
        ),
        "company": company_record["company"],
        "profile_extras": company_record["profile_extras"],
        "context_settings_id": str(ctx.id) if ctx else None,
        "extended_kpis_count": extended_count,
        "assessment_context": assessment_context,
        "emissions": emissions_result,
    }


def _scale(company: Company) -> float:
    employees = company.employee_count or BASE_EMPLOYEES
    emp_scale = employees / BASE_EMPLOYEES
    if company.turnover and company.turnover > 0:
        turnover_scale = company.turnover / BASE_TURNOVER_EUR
        return (emp_scale + turnover_scale) / 2
    return emp_scale


def _r(value: float, decimals: int = 1) -> float:
    return round(value, decimals)


def _ri(value: float) -> int:
    return int(round(value))


def build_demo_kpis(company: Company, reporting_year: int) -> dict[str, Any]:
    """Restituisce tutti i KPI demo (colonne DB + extended_kpis) coerenti tra loro."""
    scale = _scale(company)
    employees = company.employee_count or BASE_EMPLOYEES
    turnover = company.turnover or BASE_TURNOVER_EUR * scale
    country = (company.country or "Italy").strip()
    sector = company.sector or "C10 — Food manufacturing"
    baseline_year = reporting_year - 1

    sites = max(1, _ri(2 * math.sqrt(scale)))
    tier1 = max(12, _ri(85 * scale))
    tier2 = max(40, _ri(420 * scale ** 0.85))
    works_councils = max(1, min(sites, _ri(sites * 0.8)))
    permanent = _ri(employees * 0.88)
    temporary = employees - permanent
    female = _ri(employees * 0.42)
    other = max(0, _ri(employees * 0.01))
    male = employees - female - other

    revenue = turnover
    training_spend = revenue * 0.008
    hs_spend = revenue * 0.004
    wellbeing_spend = revenue * 0.002
    dei_spend = revenue * 0.0015
    workforce_spend = training_spend + hs_spend + wellbeing_spend + dei_spend

    audit_spend = revenue * 0.0012
    supplier_training_spend = revenue * 0.0008
    grievance_tech_spend = revenue * 0.0003
    msi_fees = revenue * 0.00015
    value_chain_spend = audit_spend + supplier_training_spend + grievance_tech_spend + msi_fees

    enps_current = _r(28 + 4 * min(scale, 2))
    enps_baseline = _r(enps_current - 4)
    enps_2026 = _r(enps_current + 6)
    enps_2030 = _r(enps_current + 14)

    women_mgmt = _r(32 + 3 * min(scale, 2))
    women_baseline = _r(women_mgmt - 4)
    women_2026 = _r(women_mgmt + 4)
    women_2030 = _r(women_mgmt + 10)

    pay_gap = _r(8.5 - 0.5 * min(scale, 2))
    pay_gap_baseline = _r(pay_gap + 1.2)
    pay_gap_2026 = _r(pay_gap - 1.5)
    pay_gap_2030 = _r(pay_gap - 3.5)

    ltifr = _r(2.4 - 0.2 * min(scale, 2))
    ltifr_baseline = _r(ltifr + 0.4)
    ltifr_2026 = _r(max(0.8, ltifr - 0.5))

    training_hours = _r(28 + 2 * min(scale, 2))
    training_baseline = _r(training_hours - 3)
    training_2026 = _r(training_hours + 4)
    training_2030 = _r(training_hours + 10)

    coc_pct = _r(72 + 2 * min(scale, 1.5))
    audit_coverage = _r(38 + 4 * min(scale, 2))
    audit_baseline = _r(audit_coverage - 8)
    audit_2026 = _r(audit_coverage + 12)
    cap_closure = _r(65 + 3 * min(scale, 2))
    cap_baseline = _r(cap_closure - 10)
    cap_2026 = _r(cap_closure + 8)
    cap_2030 = _r(min(98, cap_closure + 22))
    high_risk_engagement = _r(82 + 2 * min(scale, 1))
    grievance_channel = _r(55 + 5 * min(scale, 2))
    grievance_baseline = _r(grievance_channel - 12)
    grievance_2026 = _r(grievance_channel + 15)
    reps_trained = max(8, _ri(18 * scale))
    reps_baseline = max(6, _ri(reps_trained * 0.75))
    reps_2026 = _ri(reps_trained * 1.2)
    reps_2030 = _ri(reps_trained * 1.6)

    pm_reduction = _r(18 + 2 * min(scale, 2))
    voc_reduction = _r(12 + 1.5 * min(scale, 2))
    cod_reduction = _r(22 + 2 * min(scale, 2))
    heavy_metals_reduction = _r(15 + 1.5 * min(scale, 2))
    soc_reduction = _r(25 + 3 * min(scale, 2))
    pm_kg = _ri(840 * scale)
    sensitivity_kg = _ri(pm_kg * 0.15)

    capex_pollution = _ri(revenue * 0.006)
    opex_pollution = _ri(revenue * 0.003)
    capex_wastewater = _ri(capex_pollution * 0.35)
    capex_substance = _ri(capex_pollution * 0.25)
    capex_soil = _ri(capex_pollution * 0.15)

    site_name = f"{country.split(',')[0].strip()} production site"

    db_fields: dict[str, Any] = {
        "company_name": company.company_name,
        "country": country,
        "sector": sector,
        "reporting_year": reporting_year,
        "employee_count_total": employees,
        "employee_count_permanent": permanent,
        "employee_count_temporary": temporary,
        "employee_count_male": male,
        "employee_count_female": female,
        "employee_count_other": other,
        "employee_count_by_geography": {country: employees},
        "annual_revenue_eur": revenue,
        "operational_sites_count": sites,
        "emissions_baseline_year": baseline_year,
        "emissions_methodology": "GHG Protocol Corporate Standard (Scope 1, 2, 3)",
        "scope3_material_categories": [
            "Purchased goods and services",
            "Upstream transportation",
            "Business travel",
            "Employee commuting",
            "Waste generated in operations",
        ],
        "tier1_suppliers_count": tier1,
        "tier2_suppliers_count": tier2,
        "value_chain_countries": [country, "Germany", "Spain", "Romania", "Turkey"],
        "high_risk_countries": ["Turkey", "Bangladesh"],
        "suppliers_code_of_conduct_pct": coc_pct,
        "supplier_audits_last_year": max(4, _ri(tier1 * audit_coverage / 100)),
        "ltifr": ltifr,
        "fatal_accidents": 0,
        "voluntary_turnover_pct": _r(9.5 - 0.5 * min(scale, 2)),
        "avg_training_hours_per_year": training_hours,
        "women_in_management_pct": women_mgmt,
        "gender_pay_gap_pct": pay_gap,
        "union_coverage_pct": _r(58 + 2 * min(scale, 2)),
        "employee_engagement_score": enps_current,
        "standard_payment_terms_days": 60,
        "avg_actual_payment_time_days": _r(52 + 2 * min(scale, 1)),
        "invoices_paid_within_terms_pct": _r(91 - 1 * min(scale, 2)),
        "invoices_paid_late_pct": _r(6 + 0.5 * min(scale, 1)),
        "anti_corruption_training_pct": _r(96 + min(scale, 1)),
        "corruption_incidents_last_year": 0,
        "whistleblowing_reports_received": max(0, _ri(2 * scale)),
    }

    extended: dict[str, Any] = {
        "workforce_baseline_year": str(baseline_year),
        "works_councils_count": works_councils,
        "hs_committee_min_employees": 50,
        "survey_participation_pct": 68,
        "focus_group_attendance_pct": 55,
        "consultation_response_rate_pct": 61,
        "training_completion_pct": 87,
        "enps_baseline": enps_baseline,
        "enps_target_2026": enps_2026,
        "enps_target_2030": enps_2030,
        "women_mgmt_baseline_pct": women_baseline,
        "women_mgmt_target_2026_pct": women_2026,
        "women_mgmt_target_2030_pct": women_2030,
        "gender_pay_gap_baseline_pct": pay_gap_baseline,
        "gender_pay_gap_target_2026_pct": pay_gap_2026,
        "gender_pay_gap_target_2030_pct": pay_gap_2030,
        "ltifr_baseline": ltifr_baseline,
        "ltifr_target_2026": ltifr_2026,
        "training_hours_baseline": training_baseline,
        "training_hours_target_2026": training_2026,
        "training_hours_target_2030": training_2030,
        "total_turnover_pct": _r(12 + min(scale, 2)),
        "new_hires_count": _ri(employees * 0.11),
        "employees_with_disabilities_pct": _r(3.2 + 0.3 * min(scale, 1)),
        "avg_tenure_years": _r(6.8 + 0.2 * min(scale, 1)),
        "avg_age_years": _r(41 + min(scale, 2)),
        "tier1_workers_estimated": _ri(tier1 * 45 * scale ** 0.3),
        "tier2_workers_estimated": _ri(tier2 * 38 * scale ** 0.25),
        "supplier_countries_count": 12,
        "suppliers_audited_count": db_fields["supplier_audits_last_year"],
        "suppliers_with_cap_count": max(1, _ri(tier1 * 0.08)),
        "suppliers_terminated_count": max(0, _ri(2 * scale)),
        "grievance_languages_count": 5,
        "grievances_received": max(3, _ri(8 * scale)),
        "grievances_resolved": max(2, _ri(7 * scale)),
        "grievance_resolution_days": 28,
        "grievance_satisfaction_pct": _r(74 + 2 * min(scale, 1)),
        "workforce_expenditure_total_eur": workforce_spend,
        "workforce_expenditure_training_eur": training_spend,
        "workforce_expenditure_health_safety_eur": hs_spend,
        "workforce_expenditure_wellbeing_eur": wellbeing_spend,
        "workforce_expenditure_diversity_eur": dei_spend,
        "value_chain_expenditure_total_eur": value_chain_spend,
        "value_chain_expenditure_auditing_eur": audit_spend,
        "value_chain_expenditure_training_eur": supplier_training_spend,
        "value_chain_expenditure_grievance_eur": grievance_tech_spend,
        "value_chain_expenditure_msi_fees_eur": msi_fees,
        "corruption_fines_eur": 0,
        "late_payment_interest_eur": _ri(revenue * 0.00002),
        "payment_disputes_count": max(0, _ri(1 * scale)),
        "supplier_audit_coverage_baseline_pct": audit_baseline,
        "supplier_audit_coverage_target_2026_pct": audit_2026,
        "supplier_audit_coverage_current_pct": audit_coverage,
        "supplier_cap_closure_baseline_pct": cap_baseline,
        "supplier_cap_closure_target_2026_pct": cap_2026,
        "supplier_cap_closure_target_2030_pct": cap_2030,
        "supplier_cap_closure_current_pct": cap_closure,
        "supplier_high_risk_engagement_current_pct": high_risk_engagement,
        "supplier_grievance_channel_baseline_pct": grievance_baseline,
        "supplier_grievance_channel_target_2026_pct": grievance_2026,
        "supplier_grievance_channel_current_pct": grievance_channel,
        "supplier_reps_trained_per_year": reps_trained,
        "supplier_reps_trained_baseline": reps_baseline,
        "supplier_reps_trained_target_2026": reps_2026,
        "supplier_reps_trained_target_2030": reps_2030,
        "supplier_self_assessment_pct": _r(68 + 3 * min(scale, 1)),
        "supplier_esg_assessment_pct": _r(45 + 4 * min(scale, 1)),
        "supplier_strategic_review_pct": _r(100),
        "supplier_workers_data_coverage_pct": _r(52 + 5 * min(scale, 1)),
        "anti_corruption_training_high_risk_pct": _r(98 + min(scale, 1)),
        "anti_corruption_training_board_pct": 100,
        "due_diligence_screenings_count": max(10, _ri(45 * scale)),
        "due_diligence_screenings_prior_year": max(8, _ri(38 * scale)),
        "corruption_investigations_count": max(0, _ri(1 * scale)),
        "corruption_investigations_prior_year": 0,
        "confirmed_corruption_count": 0,
        "confirmed_bribery_count": 0,
        "corruption_public_officials_count": 0,
        "corruption_business_partners_count": 0,
        "corruption_convictions_count": 0,
        "corruption_pending_actions_count": 0,
        "suppliers_terminated_corruption_count": 0,
        "substitution_timeline_years": 3,
        "pollution_facilities_count": sites,
        "air_emissions_pm_reduction_pct": pm_reduction,
        "air_emissions_voc_reduction_pct": voc_reduction,
        "cod_reduction_pct": cod_reduction,
        "heavy_metals_reduction_pct": heavy_metals_reduction,
        "soc_reduction_pct": soc_reduction,
        "pm_emissions_kg_year": pm_kg,
        "sensitivity_emissions_delta_kg": sensitivity_kg,
        "nox_baseline_kg_year": _ri(pm_kg * 1.8),
        "sox_baseline_kg_year": _ri(pm_kg * 0.6),
        "voc_baseline_kg_year": _ri(pm_kg * 2.2),
        "nox_reduction_2030_pct": _r(20 + min(scale, 2)),
        "sox_reduction_2030_pct": _r(18 + min(scale, 2)),
        "supplier_audit_nc_health_safety_pct": _r(22 - min(scale, 1)),
        "supplier_audit_nc_working_hours_pct": _r(18 - min(scale, 1)),
        "supplier_audit_nc_wages_pct": _r(14 - min(scale, 1)),
        "supplier_audit_nc_freedom_pct": _r(8),
        "supplier_audit_nc_environment_pct": _r(11 - min(scale, 1)),
        "workforce_geo_primary_pct": _r(78),
        "workforce_geo_secondary_pct": _r(15),
        "workforce_geo_intl_pct": _r(7),
        "workforce_geo_primary_count": _ri(employees * 0.78),
        "workforce_geo_secondary_count": _ri(employees * 0.15),
        "workforce_geo_intl_count": employees - _ri(employees * 0.78) - _ri(employees * 0.15),
        "payment_volume_sme_pct": 35,
        "payment_volume_large_pct": 45,
        "payment_volume_strategic_pct": 15,
        "payment_volume_public_pct": 5,
        "procurement_staff_count": max(3, _ri(employees * 0.035)),
        "scope3_sensitivity_tco2e": max(50, _ri(revenue * 0.000012)),
        "ewc_status_text": (
            f"Non applicabile: l'organico UE è inferiore a 1.000 dipendenti (D.Lgs. 265/1999). "
            f"Sono attivi RSU e rappresentanti di lavoratori sui {works_councils} siti produttivi."
        ),
        "engagement_cycle_findings": (
            "Priorità emerse: miglioramento turni e carichi di lavoro in produzione; "
            "potenziamento formazione sicurezza alimentare; maggiore trasparenza su criteri di progressione. "
            "Azioni avviate: revisione pianificazione turni, 12 ore aggiuntive di formazione HACCP, "
            "incontri trimestrali RSU-direzione."
        ),
        "microplastics_assessment_text": (
            "Le operazioni di confezionamento utilizzano film plastico riciclabile; "
            "non sono identificate emissioni significative di microplastiche primarie. "
            "Monitoraggio annuale su perdite di pellet e scarti di packaging."
        ),
        "nox_kg_n": _ri(pm_kg * 1.8),
        "nox_kg_n1": _ri(pm_kg * 1.9),
        "sox_kg_n": _ri(pm_kg * 0.55),
        "sox_kg_n1": _ri(pm_kg * 0.58),
        "pm10_kg_n": pm_kg,
        "pm10_kg_n1": _ri(pm_kg * 1.04),
        "pm25_kg_n": _ri(pm_kg * 0.72),
        "pm25_kg_n1": _ri(pm_kg * 0.75),
        "voc_kg_n": _ri(pm_kg * 2.1),
        "voc_kg_n1": _ri(pm_kg * 2.3),
        "heavy_metals_air_kg_n": _ri(pm_kg * 0.08),
        "heavy_metals_air_kg_n1": _ri(pm_kg * 0.09),
        "cod_kg_n": _ri(pm_kg * 3.2),
        "cod_kg_n1": _ri(pm_kg * 3.4),
        "nitrogen_kg_n": _ri(pm_kg * 0.9),
        "nitrogen_kg_n1": _ri(pm_kg * 0.95),
        "phosphorus_kg_n": _ri(pm_kg * 0.15),
        "phosphorus_kg_n1": _ri(pm_kg * 0.16),
        "heavy_metals_water_kg_n": _ri(pm_kg * 0.04),
        "heavy_metals_water_kg_n1": _ri(pm_kg * 0.05),
        "tss_kg_n": _ri(pm_kg * 1.1),
        "tss_kg_n1": _ri(pm_kg * 1.15),
        "soc_weight_tonnes_n": _r(2.4 * scale, 1),
        "soc_weight_tonnes_n1": _r(2.6 * scale, 1),
        "svhc_weight_tonnes_n": _r(0.3 * scale, 2),
        "svhc_weight_tonnes_n1": _r(0.35 * scale, 2),
        "scip_notifications_n": max(1, _ri(2 * scale)),
        "scip_notifications_n1": max(1, _ri(2 * scale)),
        "remediation_wage_cases": max(1, _ri(3 * scale)),
        "remediation_wage_resolved": max(1, _ri(2 * scale)),
        "remediation_wage_remedy": "Retrocessione straordinaria per 14 lavoratori presso 2 fornitori (EUR 11.200)",
        "remediation_hs_cases": max(1, _ri(2 * scale)),
        "remediation_hs_resolved": max(1, _ri(2 * scale)),
        "remediation_hs_remedy": "Fornitura DPI e protezioni macchina verificate in re-audit entro 90 giorni",
        "remediation_discrimination_cases": 1,
        "remediation_discrimination_resolved": 1,
        "remediation_discrimination_remedy": "Formazione anti-discriminazione obbligatoria per il management del fornitore",
        "remediation_hr_cases": max(0, _ri(1 * scale)),
        "remediation_hr_resolved": max(0, _ri(1 * scale)),
        "remediation_hr_remedy": "Canale whistleblowing attivato presso fornitore ad alto rischio",
        "hazardous_waste_treated_pct": _r(94 + min(scale, 1)),
        "hazardous_waste_recovered_pct": _r(38 + 3 * min(scale, 1)),
        "environmental_fte_count": max(2, _ri(4 * scale)),
        "cems_facilities_count": max(1, sites - 1),
        "svhc_substances_count": max(1, _ri(3 * scale)),
        "soil_remediation_sites_count": 1 if scale >= 1 else 0,
        "external_stakeholders_engaged": max(5, _ri(18 * scale)),
        "financial_resources_eur": capex_pollution,
        "opex_pollution_eur": opex_pollution,
        "capex_pollution_eur": capex_pollution,
        "capex_wastewater_eur": capex_wastewater,
        "capex_substance_phaseout_eur": capex_substance,
        "capex_soil_remediation_eur": capex_soil,
        "database_name": "Ecoinvent 3.9",
        "regulatory_database_name": "ECHA REACH Candidate List",
        "substance_name": "formaldehyde",
        "site_name": site_name,
        "target_year": reporting_year + 4,
        "stakeholders_engaged_count": max(8, _ri(24 * scale)),
        "status_e2": "In progress",
        "status_s1": "In progress",
        "status_s2": "In progress",
        "status_g1": "Completed",
    }

    return {"db": db_fields, "extended": extended}


def sync_full_demo_context(
    db: Session,
    company: Company,
    reporting_year: int,
    *,
    overwrite: bool = True,
) -> dict[str, Any]:
    """Popola CompanyContextSettings con profilo demo completo (non solo GHG)."""
    profile = build_demo_kpis(company, reporting_year)
    db_fields = profile["db"]
    extended = profile["extended"]

    ctx = db.query(CompanyContextSettings).filter(
        CompanyContextSettings.company_id == company.company_id,
    ).first()
    if not ctx:
        ctx = CompanyContextSettings(company_id=company.company_id)
        db.add(ctx)

    for key, value in db_fields.items():
        if value is None:
            continue
        if not overwrite and getattr(ctx, key, None) not in (None, "", []):
            continue
        setattr(ctx, key, value)

    if overwrite or not ctx.extended_kpis:
        ctx.extended_kpis = extended
    else:
        merged = dict(ctx.extended_kpis or {})
        merged.update({k: v for k, v in extended.items() if k not in merged})
        ctx.extended_kpis = merged

    return profile
