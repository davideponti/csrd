"""Build company context dict for report template placeholder resolution."""
from __future__ import annotations

from typing import Any

from app.models import CompanyContextSettings


def _s(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        import json
        return json.dumps(value)
    return str(value)


def build_report_context_data(ctx: CompanyContextSettings | None) -> dict[str, str]:
    """Map CompanyContextSettings (+ extended_kpis JSON) to FIELD_REGISTRY keys."""
    if not ctx:
        return {}

    data: dict[str, str] = {
        "company_name": ctx.company_name or "",
        "country": ctx.country or "",
        "sector": ctx.sector or "",
        "reporting_year": _s(ctx.reporting_year),
        "employee_count_total": _s(ctx.employee_count_total),
        "employee_count_permanent": _s(ctx.employee_count_permanent),
        "employee_count_temporary": _s(ctx.employee_count_temporary),
        "employee_count_male": _s(ctx.employee_count_male),
        "employee_count_female": _s(ctx.employee_count_female),
        "employee_count_other": _s(ctx.employee_count_other),
        "annual_revenue_eur": _s(ctx.annual_revenue_eur),
        "operational_sites_count": _s(ctx.operational_sites_count),
        "scope1_emissions": _s(ctx.scope1_emissions),
        "scope2_location_emissions": _s(ctx.scope2_location_based),
        "scope2_market_emissions": _s(ctx.scope2_market_based),
        "scope3_total_emissions": _s(ctx.scope3_total),
        "scope3_material_categories": _s(ctx.scope3_material_categories),
        "emissions_baseline_year": _s(ctx.emissions_baseline_year),
        "emissions_methodology": ctx.emissions_methodology or "",
        "tier1_suppliers_count": _s(ctx.tier1_suppliers_count),
        "tier2_suppliers_estimated": _s(ctx.tier2_suppliers_count),
        "value_chain_countries": _s(ctx.value_chain_countries),
        "high_risk_countries": _s(ctx.high_risk_countries),
        "suppliers_code_of_conduct_pct": _s(ctx.suppliers_code_of_conduct_pct),
        "supplier_audits_last_year": _s(ctx.supplier_audits_last_year),
        "ltifr": _s(ctx.ltifr),
        "fatal_accidents": _s(ctx.fatal_accidents),
        "voluntary_turnover_pct": _s(ctx.voluntary_turnover_pct),
        "avg_training_hours_per_employee": _s(ctx.avg_training_hours_per_year),
        "women_in_management_pct": _s(ctx.women_in_management_pct),
        "gender_pay_gap_pct": _s(ctx.gender_pay_gap_pct),
        "union_coverage_pct": _s(ctx.union_coverage_pct),
        "employee_engagement_score": _s(ctx.employee_engagement_score),
        "standard_payment_terms_days": _s(ctx.standard_payment_terms_days),
        "avg_actual_payment_time_days": _s(ctx.avg_actual_payment_time_days),
        "invoices_paid_within_terms_pct": _s(ctx.invoices_paid_within_terms_pct),
        "invoices_paid_late_pct": _s(ctx.invoices_paid_late_pct),
        "anti_corruption_training_pct": _s(ctx.anti_corruption_training_pct),
        "corruption_incidents_count": _s(ctx.corruption_incidents_last_year),
        "whistleblowing_reports_count": _s(ctx.whistleblowing_reports_received),
    }

    extended = ctx.extended_kpis or {}
    for key, value in extended.items():
        if value is not None and value != "":
            data[key] = _s(value)

    return data
