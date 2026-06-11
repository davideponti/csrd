"""
ESRS S1-6 — Characteristics of the Undertaking's Employees
Full disclosure generator (ESRS S1 paragraphs 50-83)

Generates comprehensive workforce metrics including:
1. Workforce headcount table (permanent/temporary/non-guaranteed hours, by gender, by region, full-time/part-time, employees vs agency workers)
2. Employee turnover (hires, departures, voluntary/involuntary, rates)
3. Health and safety metrics (LTIFR, TRIR, fatalities, occupational diseases, days lost)
4. Training and development (average hours by gender, performance reviews, training expenditure)
5. Remuneration and pay gap (gender pay gap, CEO pay ratio, collective bargaining coverage)

All metrics reference the relevant ESRS S1-6 paragraphs and include measurement methodology.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def build_s1_6_disclosure(
    company_name: str,
    reporting_year: int,
    employee_count: int = 0,
    context: Optional[Dict[str, str]] = None,
) -> str:
    """
    Generate the complete ESRS S1-6 disclosure HTML block.

    Args:
        company_name: Name of the undertaking
        reporting_year: Reporting year (e.g., 2025)
        employee_count: Total employee headcount (if known)
        context: Dict of company context values to fill [TBC:*] placeholders

    Returns:
        HTML string with tables and narrative for ESRS S1-6 (paragraphs 50-83)
    """
    year_n = str(reporting_year)
    year_n1 = str(reporting_year - 1)

    ctx = context or {}

    def val(key: str, default: str = "[TO BE CONFIRMED]") -> str:
        """Get context value or return default."""
        v = ctx.get(key)
        return str(v) if v else default

    # ── 1. WORKFORCE HEADCOUNT TABLE ────────────────────────────
    workforce_table = f"""
    <h5>1(a). Workforce headcount — Contract type and gender (ESRS S1-6 par. 50(a), 50(b))</h5>
    <table>
        <thead>
            <tr>
                <th>Category</th>
                <th>Female</th>
                <th>Male</th>
                <th>Other / Not disclosed</th>
                <th>Total</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Total employees</strong></td>
                <td>{val("employee_count_female")}</td>
                <td>{val("employee_count_male")}</td>
                <td>{val("employee_count_other")}</td>
                <td><strong>{employee_count if employee_count else val("employee_count_total")}</strong></td>
            </tr>
            <tr>
                <td>Permanent employees</td>
                <td>{val("employee_count_female")}</td>
                <td>{val("employee_count_male")}</td>
                <td>{val("employee_count_other")}</td>
                <td>{val("permanent_count", val("employee_count_permanent"))}</td>
            </tr>
            <tr>
                <td>Temporary / fixed-term employees</td>
                <td>{val("employee_count_female")}</td>
                <td>{val("employee_count_male")}</td>
                <td>{val("employee_count_other")}</td>
                <td>{val("temporary_count", val("employee_count_temporary"))}</td>
            </tr>
            <tr>
                <td>Non-guaranteed hours employees</td>
                <td>{val("employee_count_female")}</td>
                <td>{val("employee_count_male")}</td>
                <td>{val("employee_count_other")}</td>
                <td>{val("non_guaranteed_hours_count")}</td>
            </tr>
            <tr style="background-color:#f7fafc;">
                <td><strong>Full-time employees</strong></td>
                <td>{val("employee_count_female")}</td>
                <td>{val("employee_count_male")}</td>
                <td>{val("employee_count_other")}</td>
                <td>{val("full_time_count")}</td>
            </tr>
            <tr style="background-color:#f7fafc;">
                <td><strong>Part-time employees</strong></td>
                <td>{val("employee_count_female")}</td>
                <td>{val("employee_count_male")}</td>
                <td>{val("employee_count_other")}</td>
                <td>{val("part_time_count")}</td>
            </tr>
        </tbody>
    </table>

    <h5>1(b). Employees by region / country (ESRS S1-6 par. 50(c))</h5>
    <table>
        <thead>
            <tr>
                <th>Region</th>
                <th>Headcount</th>
                <th>% of total workforce</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Europe (primary operations)</td>
                <td>{val("region_europe_count")}</td>
                <td>{val("employees_with_disabilities_pct")}%</td>
            </tr>
            <tr>
                <td>Americas</td>
                <td>{val("region_americas_count")}</td>
                <td>{val("employees_with_disabilities_pct")}%</td>
            </tr>
            <tr>
                <td>Asia-Pacific</td>
                <td>{val("region_asia_pacific_count")}</td>
                <td>{val("employees_with_disabilities_pct")}%</td>
            </tr>
            <tr>
                <td>Africa</td>
                <td>{val("region_africa_count")}</td>
                <td>{val("employees_with_disabilities_pct")}%</td>
            </tr>
            <tr>
                <td>Other regions</td>
                <td>{val("region_other_count")}</td>
                <td>{val("employees_with_disabilities_pct")}%</td>
            </tr>
            <tr style="font-weight:bold;background-color:#edf2f7;">
                <td><strong>Total</strong></td>
                <td><strong>{employee_count if employee_count else val("employee_count_total")}</strong></td>
                <td><strong>100%</strong></td>
            </tr>
        </tbody>
    </table>

    <h5>1(c). Non-employee workers (ESRS S1-6 par. 50(d))</h5>
    <table>
        <thead>
            <tr>
                <th>Category</th>
                <th>Headcount</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Agency workers / temporary agency staff</td>
                <td>{val("agency_workers_count")}</td>
            </tr>
            <tr>
                <td>Self-employed / independent contractors</td>
                <td>{val("self_employed_count")}</td>
            </tr>
        </tbody>
    </table>
"""

    # ── 2. EMPLOYEE TURNOVER ─────────────────────────────────────
    turnover_table = f"""
    <h5>2. Employee turnover (ESRS S1-6 par. 50(e), 50(f))</h5>
    <table>
        <thead>
            <tr>
                <th>Indicator</th>
                <th>{year_n1}</th>
                <th>{year_n}</th>
                <th>ESRS Reference</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Total number of employees at period start</td>
                <td>{val("employee_count_total")}</td>
                <td>{employee_count if employee_count else val("employee_count_total")}</td>
                <td>ESRS S1-6.50(e)</td>
            </tr>
            <tr>
                <td>New hires during the period (number)</td>
                <td>{val("new_hires_count")}</td>
                <td>{val("new_hires_count")}</td>
                <td>ESRS S1-6.50(f)</td>
            </tr>
            <tr>
                <td>New hire rate (%)</td>
                <td>{val("new_hires_rate")}%</td>
                <td>{val("new_hires_rate")}%</td>
                <td>ESRS S1-6.50(f)</td>
            </tr>
            <tr>
                <td>Total departures during the period (number)</td>
                <td>{val("total_departures_count")}</td>
                <td>{val("total_departures_count")}</td>
                <td>ESRS S1-6.50(e)</td>
            </tr>
            <tr>
                <td>&nbsp;&nbsp;— Voluntary departures</td>
                <td>{val("voluntary_departures_count")}</td>
                <td>{val("voluntary_departures_count")}</td>
                <td>ESRS S1-6.50(e)</td>
            </tr>
            <tr>
                <td>&nbsp;&nbsp;— Involuntary departures</td>
                <td>{val("involuntary_departures_count")}</td>
                <td>{val("involuntary_departures_count")}</td>
                <td>ESRS S1-6.50(e)</td>
            </tr>
            <tr>
                <td>Total departure rate (%)</td>
                <td>{val("departure_rate")}%</td>
                <td>{val("departure_rate")}%</td>
                <td>ESRS S1-6.50(e)</td>
            </tr>
            <tr>
                <td>Voluntary turnover rate (%)</td>
                <td>{val("voluntary_turnover_rate", val("voluntary_turnover_pct"))}%</td>
                <td>{val("voluntary_turnover_rate", val("voluntary_turnover_pct"))}%</td>
                <td>ESRS S1-6.50(e)</td>
            </tr>
            <tr>
                <td>Involuntary turnover rate (%)</td>
                <td>{val("involuntary_turnover_rate")}%</td>
                <td>{val("involuntary_turnover_rate")}%</td>
                <td>ESRS S1-6.50(e)</td>
            </tr>
        </tbody>
    </table>
    <p style="font-size:12px;color:#718096;">
        <strong>Methodology (ESRS S1-6 par. 50(e)-(f)):</strong> Turnover rates are calculated as the number
        of departures (or hires) during the period divided by the average headcount during the same period,
        expressed as a percentage. Voluntary departures include resignations, retirements, and mutually agreed
        terminations. Involuntary departures include dismissals, redundancies, and end-of-contract non-renewals.
        This methodology is consistent with paragraph AR 105 of the ESRS S1 Application Requirements.
    </p>
"""

    # ── 3. HEALTH AND SAFETY METRICS ─────────────────────────────
    h_and_s_table = f"""
    <h5>3. Health and safety metrics (ESRS S1-6 par. 60-69, ESRS S1-14)</h5>
    <table>
        <thead>
            <tr>
                <th>Indicator</th>
                <th>{year_n1}</th>
                <th>{year_n}</th>
                <th>Unit</th>
                <th>ESRS Reference</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Lost-time injury frequency rate (LTIFR)</td>
                <td>{val("ltifr")}</td>
                <td>{val("ltifr")}</td>
                <td>per 1,000 employees</td>
                <td>ESRS S1-14.60(e)</td>
            </tr>
            <tr>
                <td>Total recordable injury rate (TRIR)</td>
                <td>{val("trir")}</td>
                <td>{val("trir")}</td>
                <td>per 200,000 hours worked</td>
                <td>ESRS S1-14.60(e)</td>
            </tr>
            <tr>
                <td>Number of fatalities</td>
                <td>{val("fatalities_count", val("fatal_accidents"))}</td>
                <td>{val("fatalities_count", val("fatal_accidents"))}</td>
                <td>count</td>
                <td>ESRS S1-14.60(c)</td>
            </tr>
            <tr>
                <td>Number of recorded occupational diseases</td>
                <td>{val("occupational_diseases_count")}</td>
                <td>{val("occupational_diseases_count")}</td>
                <td>count</td>
                <td>ESRS S1-14.60(g)</td>
            </tr>
            <tr>
                <td>Days lost due to work-related injury</td>
                <td>{val("days_lost_injury")}</td>
                <td>{val("days_lost_injury")}</td>
                <td>days</td>
                <td>ESRS S1-14.60(e)</td>
            </tr>
        </tbody>
    </table>
    <p style="font-size:12px;color:#718096;">
        <strong>Methodology (ESRS S1-14 par. 60-69):</strong> LTIFR is calculated as (number of lost-time
        injuries × 1,000,000) / total hours worked. TRIR is calculated as (number of recordable injuries
        and illnesses × 200,000) / total hours worked. A lost-time injury is defined as a work-related
        injury resulting in at least one day away from work (excluding the day of the accident). A fatality
        is a work-related death occurring within one year of the incident. Occupational diseases include
        work-related illnesses diagnosed by a medical professional. Data covers all employees within the
        operational control scope and excludes contractors (reported separately where material).
        Consistent with ESRS S1-14 AR 111-115 and ILO framework.
    </p>
"""

    # ── 4. TRAINING AND DEVELOPMENT ──────────────────────────────
    training_table = f"""
    <h5>4. Training and development metrics (ESRS S1-6 par. 70-76, ESRS S1-13)</h5>
    <table>
        <thead>
            <tr>
                <th>Indicator</th>
                <th>{year_n1}</th>
                <th>{year_n}</th>
                <th>Unit</th>
                <th>ESRS Reference</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Average training hours per employee</td>
                <td>{val("avg_training_hours_per_employee")}</td>
                <td>{val("avg_training_hours_per_employee")}</td>
                <td>hours/year</td>
                <td>ESRS S1-13.70(a)</td>
            </tr>
            <tr>
                <td>&nbsp;&nbsp;— by gender: Female</td>
                <td>{val("training_hours_female")}</td>
                <td>{val("training_hours_female")}</td>
                <td>hours/year</td>
                <td>ESRS S1-13.70(a)</td>
            </tr>
            <tr>
                <td>&nbsp;&nbsp;— by gender: Male</td>
                <td>{val("training_hours_male")}</td>
                <td>{val("training_hours_male")}</td>
                <td>hours/year</td>
                <td>ESRS S1-13.70(a)</td>
            </tr>
            <tr>
                <td>Employees who received a performance / career development review (%)</td>
                <td>{val("performance_review_pct")}%</td>
                <td>{val("performance_review_pct")}%</td>
                <td>% of total employees</td>
                <td>ESRS S1-13.70(b)</td>
            </tr>
            <tr>
                <td>Total training expenditure</td>
                <td>{val("training_expenditure_eur")}</td>
                <td>{val("training_expenditure_eur")}</td>
                <td>EUR</td>
                <td>ESRS S1-13.70(a)</td>
            </tr>
        </tbody>
    </table>
    <p style="font-size:12px;color:#718096;">
        <strong>Methodology (ESRS S1-13 par. 70-76):</strong> Average training hours are calculated as total
        training hours delivered (including classroom, e-learning, on-the-job, and external training)
        divided by the total number of full-time equivalent (FTE) employees during the period.
        Performance reviews include formal annual or biennial appraisals as well as regular check-ins
        where career development is discussed. Training expenditure includes direct costs (course fees,
        trainer costs, materials, travel) and indirect costs (internal trainer time allocated to
        training delivery). Data disaggregated by gender uses the undertaking's HRIS classification.
        Consistent with ESRS S1-13 AR 116-118.
    </p>
"""

    # ── 5. REMUNERATION AND PAY GAP ──────────────────────────────
    pay_table = f"""
    <h5>5. Remuneration and pay gap metrics (ESRS S1-6 par. 77-83, ESRS S1-16)</h5>
    <table>
        <thead>
            <tr>
                <th>Indicator</th>
                <th>{year_n1}</th>
                <th>{year_n}</th>
                <th>Unit</th>
                <th>ESRS Reference</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Unadjusted gender pay gap (mean)</td>
                <td>{val("gender_pay_gap_pct")}%</td>
                <td>{val("gender_pay_gap_pct")}%</td>
                <td>%</td>
                <td>ESRS S1-16.77(a)</td>
            </tr>
            <tr>
                <td>CEO / highest-paid individual annual total compensation ratio</td>
                <td>{val("ceo_pay_ratio")}</td>
                <td>{val("ceo_pay_ratio")}</td>
                <td>ratio (x:1)</td>
                <td>ESRS S1-16.80</td>
            </tr>
            <tr>
                <td>Employees covered by collective bargaining agreements (%)</td>
                <td>{val("union_coverage_pct")}%</td>
                <td>{val("union_coverage_pct")}%</td>
                <td>% of total employees</td>
                <td>ESRS S1-8.50(a)</td>
            </tr>
        </tbody>
    </table>
    <p style="font-size:12px;color:#718096;">
        <strong>Methodology (ESRS S1-16 par. 77-83):</strong> The unadjusted gender pay gap is calculated
        as the difference between the average gross hourly earnings of male and female employees,
        expressed as a percentage of the average gross hourly earnings of male employees
        (mean calculation). The calculation includes all employees (full-time and part-time) on a
        full-time equivalent basis. Bonuses and variable pay are included in the reporting period
        in which they are earned. This methodology is consistent with Directive 2006/54/EC (Equal
        Treatment Directive) implementation requirements and ESRS S1-16 AR 119-122. The CEO pay
        ratio is calculated as the ratio of the annual total compensation of the highest-paid
        individual (CEO or equivalent) to the median annual total compensation of all employees
        (excluding the highest-paid individual). Collective bargaining agreement (CBA) coverage
        is calculated as the number of employees covered by one or more CBAs divided by the total
        number of employees, expressed as a percentage.
    </p>
"""

    # ── 6. NARRATIVE CONTEXT ────────────────────────────────────
    narrative = f"""
    <h5>6. Data sources and measurement context (ESRS S1-6 par. 50-83)</h5>
    <p><strong>{company_name}</strong> discloses workforce metrics in accordance with the requirements of
    ESRS S1 'Own Workforce', paragraphs 50 through 83 (ESRS S1-6, S1-13, S1-14, S1-16). The disclosures
    below cover the five dimensions required by the standard:</p>
    <ol>
        <li><strong>Characteristics of employees (par. 50-57):</strong> Headcount data by contract type
        (permanent, temporary, non-guaranteed hours), by gender (female, male, other/not disclosed),
        by region, by full-time/part-time status, and disclosure of non-employee workers
        (agency workers and self-employed). Data reported as of 31 December {year_n}.</li>
        <li><strong>Employee turnover (par. 50(e)-(f)):</strong> Number and rate of new hires and
        departures, disaggregated by voluntary and involuntary turnover. Rates calculated as
        a percentage of average headcount.</li>
        <li><strong>Health and safety (par. 60-69, ESRS S1-14):</strong> Lost-time injury frequency rate
        (LTIFR), total recordable injury rate (TRIR), fatalities, occupational diseases, and days
        lost due to injury. Metrics cover all employees under operational control.</li>
        <li><strong>Training and development (par. 70-76, ESRS S1-13):</strong> Average training hours
        per employee (overall and by gender), percentage of employees who received a regular
        performance and career development review, and total training expenditure.</li>
        <li><strong>Remuneration and pay equity (par. 77-83, ESRS S1-16):</strong> Unadjusted mean
        gender pay gap, CEO pay ratio (annual total compensation of highest-paid individual to
        median employee), and percentage of employees covered by collective bargaining agreements.</li>
    </ol>
    <p>Workforce data is sourced from the undertaking's Human Resources Information System (HRIS) and
    payroll systems. Headcount figures represent the number of individuals employed as of the balance
    sheet date, unless otherwise stated. Part-time employees are counted as full individuals (not
    FTEs) for headcount purposes, with FTE-adjusted figures provided where relevant. Employees on
    long-term leave (parental, sick, sabbatical) are included in headcount if the employment
    relationship continues. Data for non-employee workers is obtained from procurement and
    contractor management systems.</p>
    <p>Where exact data is not available, estimates have been used as noted in the relevant sections.
    The undertaking is committed to improving data completeness and quality across successive
    reporting cycles. Comparative figures for year {year_n1} are provided where available; the
    absence of comparative data for certain metrics is indicated with '—' (not available).</p>
    <p>This disclosure has been prepared in accordance with the ESRS S1 Application Requirements
    (AR 103-122) and the EFRAG IG 1 implementation guidance (paragraphs 89-112). The scope of
    workforce disclosures covers all employees of <strong>{company_name}</strong> over which the
    undertaking has operational control. Entities accounted for using the equity method are
    excluded unless separately disclosed.</p>
"""

    # ── ASSEMBLY ────────────────────────────────────────────────
    full_html = f"""<div class="s1-6-full-disclosure" style="margin:24px 0;">
    <h3 style="color:#1a365d;border-bottom:2px solid #2b6cb0;padding-bottom:8px;font-size:20px;">
        S1-6 — Metrics related to own workforce (ESRS S1 paragraphs 50-83)
    </h3>

    <div class="s1-6-narrative-intro" style="margin:16px 0;padding:12px 16px;border-left:4px solid #3182ce;background-color:#ebf8ff;">
        <p><strong>Disclosure Requirement S1-6</strong> — The undertaking shall disclose metrics related
        to its own workforce, including workforce characteristics, turnover, health and safety,
        training and development, and remuneration. This disclosure covers the reporting period
        {year_n} with comparative data for {year_n1} where available. All metrics marked
        <em>[TO BE CONFIRMED]</em> will be populated with verified data prior to finalisation.</p>
    </div>

    {workforce_table}

    <hr/>

    {turnover_table}

    <hr/>

    {h_and_s_table}

    <hr/>

    {training_table}

    <hr/>

    {pay_table}

    <hr/>

    {narrative}

</div>"""

    return full_html


def build_s1_6_content_block(
    company_name: str,
    reporting_year: int,
    employee_count: int = 0,
    context: Optional[Dict[str, str]] = None,
    block_id: str = "s1-6-full-metrics",
) -> 'ContentBlock':
    """
    Create a ContentBlock for the full ESRS S1-6 disclosure.

    Args:
        company_name: Name of the undertaking
        reporting_year: Reporting year
        employee_count: Total employee headcount
        context: Company context data for placeholder resolution
        block_id: Block ID for the content block

    Returns:
        ContentBlock of type 'narrative' with the full S1-6 disclosure HTML
    """
    # Late import to avoid circular dependencies
    from template_engine import ContentBlock

    html = build_s1_6_disclosure(
        company_name=company_name,
        reporting_year=reporting_year,
        employee_count=employee_count,
        context=context,
    )

    return ContentBlock(
        block_id=block_id,
        standard_ref="ESRS S1",
        paragraph_ref="50-83",
        title="S1-6 — Metrics Related to Own Workforce (Full Disclosure)",
        content_html=html,
        content_type="narrative",
        datapoint_refs=[
            "ESRS S1-6.50(a)",
            "ESRS S1-6.50(b)",
            "ESRS S1-6.50(c)",
            "ESRS S1-6.50(d)",
            "ESRS S1-6.50(e)",
            "ESRS S1-6.50(f)",
            "ESRS S1-13.70(a)",
            "ESRS S1-13.70(b)",
            "ESRS S1-14.60(c)",
            "ESRS S1-14.60(e)",
            "ESRS S1-14.60(g)",
            "ESRS S1-16.77(a)",
            "ESRS S1-16.80",
        ],
        order=1,
    )