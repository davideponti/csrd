"""
ESRS E1 — Climate Change Mitigation and Adaptation
Full disclosure generator (ESRS E1 paragraphs 1-48)

Generates comprehensive climate-related disclosures including:
1. E1-1: Transition plan for climate change mitigation (par. 1-16)
2. E1-2: Policies related to climate change mitigation and adaptation (par. 17-24)
3. E1-3: Actions and resources in relation to climate change policies (par. 25-32)
4. E1-4: Targets related to climate change mitigation and adaptation (par. 33-40)
5. E1-5: Energy consumption and mix (par. 41-48)

All metrics reference the relevant ESRS E1 paragraphs and include measurement methodology.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def build_e1_1_transition_plan(
    company_name: str,
    reporting_year: int,
    context: Optional[Dict[str, str]] = None,
) -> str:
    """
    Generate ESRS E1-1 — Transition plan for climate change mitigation (par. 1-16).

    Args:
        company_name: Name of the undertaking
        reporting_year: Reporting year (e.g., 2025)
        context: Dict of company context values to fill [TBC:*] placeholders

    Returns:
        HTML string with narrative for ESRS E1-1 (paragraphs 1-16)
    """
    ctx = context or {}
    year_n = str(reporting_year)
    year_n1 = str(reporting_year - 1)

    def val(key: str, default: str = "[TO BE CONFIRMED]") -> str:
        v = ctx.get(key)
        return str(v) if v else default

    return f"""
    <div class="e1-1-transition-plan" style="margin:24px 0;">
        <h4 style="color:#1a365d;font-size:18px;border-bottom:1px solid #2b6cb0;padding-bottom:6px;">
            E1-1 — Transition Plan for Climate Change Mitigation (ESRS E1 paragraphs 1-16)
        </h4>

        <div class="section-intro" style="margin:12px 0;padding:10px 14px;border-left:4px solid #38a169;background-color:#f0fff4;">
            <p style="margin:4px 0;">
                <strong>Disclosure Requirement E1-1</strong> — In accordance with ESRS E1 paragraph 1,
                the undertaking shall disclose its transition plan for climate change mitigation, describing
                how its strategy and business model are compatible with the transition to a sustainable economy,
                with the goal of limiting global warming to 1.5°C above pre-industrial levels in line with the
                Paris Agreement, and with the objective of achieving climate neutrality by 2050 as established
                in Regulation (EU) 2021/1119 (European Climate Law).
            </p>
        </div>

        <h5 style="color:#2d3748;margin-top:16px;">1. Compatibility with the Paris Agreement and Climate Neutrality (ESRS E1 par. 1-2)</h5>
        <p>
            <strong>{company_name}</strong> acknowledges the scientific consensus on climate change as
            represented by the Intergovernmental Panel on Climate Change (IPCC) and supports the objectives
            of the Paris Agreement and the European Climate Law (Regulation (EU) 2021/1119). The undertaking
            has developed a transition plan that outlines the pathway for aligning its business model and
            strategy with the goal of limiting global warming to 1.5°C above pre-industrial levels and
            achieving climate neutrality by 2050.
        </p>
        <p>
            As of the reporting date, the transition plan covers the following elements in accordance with
            ESRS E1 paragraph 2:
        </p>
        <ul style="margin:8px 0;padding-left:20px;">
            <li><strong>Decarbonisation levers (par. 2(a)):</strong> Identification of key decarbonisation
            levers including energy efficiency improvements, renewable energy sourcing, electrification
            of processes, supply chain engagement, and — where applicable — nature-based carbon removal
            solutions. Details on the expected GHG emission reduction for each lever are provided in
            Section 3 below.</li>
            <li><strong>Quantified emission reduction targets (par. 2(b)):</strong> The undertaking has set
            science-based emission reduction targets for Scope 1, Scope 2, and Scope 3 GHG emissions,
            aligned with a 1.5°C pathway. These targets are disclosed under E1-4 and are approved at the
            highest governance level.</li>
            <li><strong>Investment and funding plan (par. 2(c)):</strong> The transition plan is supported
            by an investment and funding plan covering the key capital expenditures (CapEx) and operational
            expenditures (OpEx) required for the decarbonisation levers identified. The plan covers the
            current reporting period through {val("e1_transition_plan_horizon_year", "2050")}.</li>
            <li><strong>Just transition considerations (par. 2(d)):</strong> The undertaking has assessed
            the social implications of its transition plan, including potential impacts on employment,
            skills development, and affected communities. A just transition framework has been adopted
            to ensure that the transition to a low-carbon economy is inclusive and equitable.</li>
            <li><strong>Governance oversight (par. 2(e)):</strong> The transition plan has been endorsed by
            the administrative, management, and supervisory bodies of the undertaking. Progress against
            the plan is reviewed at least annually by the board (or equivalent governance body).</li>
        </ul>

        <h5 style="color:#2d3748;margin-top:16px;">2. Alignment with EU Taxonomy and CSRD (ESRS E1 par. 3-5)</h5>
        <p>
            In accordance with ESRS E1 paragraph 3, <strong>{company_name}</strong> has assessed the
            compatibility of its economic activities with the criteria established under Regulation (EU)
            2020/852 (EU Taxonomy Regulation). The proportion of Taxonomy-eligible and Taxonomy-aligned
            turnover, CapEx, and OpEx is disclosed in the undertaking's EU Taxonomy reporting, which forms
            an integral part of this sustainability statement.
        </p>
        <p>
            The transition plan takes into account the requirements of ESRS E1 paragraph 4 regarding the
            disclosure of information that enables an understanding of the undertaking's exposure to
            coal-, oil-, and gas-related activities. The undertaking has identified {val("e1_coal_oil_gas_activities", "any")} significant
            exposure to fossil fuel-related assets and activities, and has developed specific phase-out
            pathways for these activities in line with the 1.5°C scenario (see Section 3 below).
        </p>
        <p>
            The plan is updated at least every {val("e1_plan_update_frequency_years", "2")} years, or more frequently if
            material changes occur in the regulatory environment, technological landscape, or the
            undertaking's business model (ESRS E1 paragraph 5).
        </p>

        <h5 style="color:#2d3748;margin-top:16px;">3. Decarbonisation Levers and GHG Emission Reduction Pathway (ESRS E1 par. 6-9)</h5>
        <p>
            The following table presents the key decarbonisation levers identified by the undertaking,
            their expected contribution to emission reductions, and the implementation timeline.
        </p>
        <table style="width:100%;border-collapse:collapse;margin:12px 0;">
            <thead>
                <tr style="background-color:#edf2f7;">
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Decarbonisation Lever</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Scope Addressed</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">Expected Reduction (tCO₂e/year by {val("e1_target_year_2030", "2030")})</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">Expected Reduction (tCO₂e/year by 2050)</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Implementation Timeline</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Energy efficiency — facilities</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Scope 1, 2</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_ee_reduction_2030")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_ee_reduction_2050")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Ongoing — annual targets</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Renewable energy procurement (PPAs, on-site generation)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Scope 2</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_re_reduction_2030")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_re_reduction_2050")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_re_timeline")}</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Electrification of vehicle fleet and processes</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Scope 1</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_elec_reduction_2030")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_elec_reduction_2050")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_elec_timeline")}</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Supply chain decarbonisation engagement</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Scope 3</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_sc_reduction_2030")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_sc_reduction_2050")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_sc_timeline")}</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Carbon removal solutions (nature-based and technological)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Residual emissions</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_cr_reduction_2030")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_cr_reduction_2050")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_cr_timeline")}</td>
                </tr>
            </tbody>
        </table>
        <p style="font-size:12px;color:#718096;">
            <strong>Note (ESRS E1 par. 7-9):</strong> The emission reduction estimates for each lever are
            based on internal feasibility studies, industry benchmarks, and scenario analysis consistent
            with the IEA Net Zero Emissions by 2050 Scenario (NZE). Decarbonisation levers are reviewed
            at least every {val("e1_lever_review_years", "3")} years to reflect technological advancements and changes
            in regulatory requirements. The pathway to climate neutrality by 2050 includes a residual
            emissions estimate of {val("e1_residual_emissions_2050")} tCO₂e, which the undertaking plans to address through
            certified carbon removal solutions in accordance with the EU Carbon Removals Certification
            Framework.
        </p>

        <h5 style="color:#2d3748;margin-top:16px;">4. Locked-in GHG Emissions Assessment (ESRS E1 par. 10-12)</h5>
        <p>
            In accordance with ESRS E1 paragraph 10, <strong>{company_name}</strong> has assessed the
            potential for locked-in GHG emissions arising from its key assets and products. Locked-in
            emissions refer to future GHG emissions that are expected to occur as a result of existing
            assets with long useful lives.
        </p>
        <p>
            The assessment covers the following categories (ESRS E1 paragraphs 10-12):
        </p>
        <ul style="margin:8px 0;padding-left:20px;">
            <li><strong>Physical assets (par. 10(a)):</strong> The undertaking's portfolio of owned and
            leased facilities, including manufacturing plants, warehouses, and office buildings. The
            total estimated locked-in Scope 1 and 2 emissions from existing assets over their remaining
            useful life is {val("e1_locked_in_physical_assets")} tCO₂e.</li>
            <li><strong>Vehicle fleet (par. 10(b)):</strong> The undertaking's owned and leased vehicle
            fleet. Estimated locked-in emissions from the existing fleet are {val("e1_locked_in_fleet")} tCO₂e over
            the fleet's expected replacement cycle. The fleet electrification roadmap addresses these
            emissions.</li>
            <li><strong>Product portfolio (par. 10(c)):</strong> The estimated use-phase emissions of
            products sold during the reporting period. The locked-in emissions from products placed
            on the market in {year_n} are estimated at {val("e1_locked_in_products")} tCO₂e over their expected
            lifetime. This estimate is based on product lifecycle assessments (LCAs) and expected
            use patterns.</li>
        </ul>
        <p>
            The locked-in emissions assessment is used to inform the decarbonisation levers and to
            prioritise asset replacement and retrofit decisions (ESRS E1 paragraph 11). The undertaking
            has identified {val("e1_locked_in_high_risk_assets", "a limited number of")} assets that represent a material risk
            of stranded value under a 1.5°C scenario, and has included specific decommissioning or
            repurposing pathways for these assets in the transition plan (ESRS E1 paragraph 12).
        </p>

        <h5 style="color:#2d3748;margin-top:16px;">5. Scenario Analysis and Climate Resilience (ESRS E1 par. 13-16)</h5>
        <p>
            <strong>{company_name}</strong> has conducted climate scenario analysis to assess the resilience
            of its strategy and business model under different climate scenarios, in accordance with ESRS
            E1 paragraph 13. The scenarios used include:
        </p>
        <table style="width:100%;border-collapse:collapse;margin:12px 0;">
            <thead>
                <tr style="background-color:#edf2f7;">
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Scenario</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Source</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Key Assumptions</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Resilience Assessment Outcome</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">1.5°C aligned (Net Zero by 2050)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">IEA NZE / IPCC SSP1-1.9</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Rapid decarbonisation, carbon pricing >{val("e1_carbon_price_2050")}/tCO₂ by 2050, high renewable energy penetration</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_resilience_outcome_15c")}</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">2°C aligned (Delayed transition)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">IPCC SSP2-2.6 / NGFS Delayed Transition</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Moderate decarbonisation, carbon pricing >{val("e1_carbon_price_2c")}/tCO₂ by 2050, gradual policy tightening</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_resilience_outcome_2c")}</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">High warming (>3°C, business-as-usual)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">IPCC SSP5-8.5 / NGFS Hot House World</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Limited additional climate policy, high physical climate risk impacts</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_resilience_outcome_bau")}</td>
                </tr>
            </tbody>
        </table>
        <p>
            The scenario analysis covers a time horizon to {val("e1_scenario_horizon_year", "2050")}, in accordance with ESRS
            E1 paragraph 14. The analysis considers both transition risks (policy, legal, technology,
            market, and reputation) and physical risks (acute and chronic) as defined by the TCFD
            framework and referred to in ESRS E1 paragraph 15.
        </p>
        <p>
            Based on the scenario analysis, the undertaking has identified the following key climate-related
            risks and opportunities (ESRS E1 paragraph 16):
        </p>
        <ul style="margin:8px 0;padding-left:20px;">
            <li><strong>Transition risks:</strong> Carbon pricing exposure ({val("e1_carbon_price_current")}/tCO₂),
            regulatory compliance costs, technology substitution risk, and potential changes in market
            demand for carbon-intensive products.</li>
            <li><strong>Physical risks:</strong> Exposure of facilities to extreme weather events (flooding,
            heatwaves, storms) under different warming scenarios. The undertaking has identified
            {val("e1_physical_risk_sites")} sites as being at material risk under a high warming scenario.</li>
            <li><strong>Climate opportunities:</strong> Development of low-carbon products and services,
            access to green finance, operational efficiency gains, and improved positioning in
            sustainability-sensitive markets.</li>
        </ul>
        <p style="font-size:12px;color:#718096;">
            <strong>Methodology (ESRS E1 par. 13-16):</strong> Climate scenario analysis is conducted using
            a combination of quantitative financial modelling (discounted cash flow analysis under different
            scenario assumptions) and qualitative assessment. The analysis is updated at least every
            {val("e1_scenario_update_years", "3")} years or when material changes occur. The undertaking follows the scenario
            analysis guidance of the TCFD, the IPCC AR6 framework, and the EFRAG IG 1 implementation
            guidance (paragraphs 45-52). The analysis has been reviewed by the undertaking's risk management
            function and approved by the board.
        </p>
    </div>
    """


def build_e1_2_policies(
    company_name: str,
    reporting_year: int,
    context: Optional[Dict[str, str]] = None,
) -> str:
    """
    Generate ESRS E1-2 — Policies related to climate change mitigation and adaptation (par. 17-24).

    Args:
        company_name: Name of the undertaking
        reporting_year: Reporting year (e.g., 2025)
        context: Dict of company context values to fill [TBC:*] placeholders

    Returns:
        HTML string with narrative for ESRS E1-2 (paragraphs 17-24)
    """
    ctx = context or {}
    year_n = str(reporting_year)

    def val(key: str, default: str = "[TO BE CONFIRMED]") -> str:
        v = ctx.get(key)
        return str(v) if v else default

    return f"""
    <div class="e1-2-policies" style="margin:24px 0;">
        <h4 style="color:#1a365d;font-size:18px;border-bottom:1px solid #2b6cb0;padding-bottom:6px;">
            E1-2 — Policies Related to Climate Change Mitigation and Adaptation (ESRS E1 paragraphs 17-24)
        </h4>

        <div class="section-intro" style="margin:12px 0;padding:10px 14px;border-left:4px solid #38a169;background-color:#f0fff4;">
            <p style="margin:4px 0;">
                <strong>Disclosure Requirement E1-2</strong> — In accordance with ESRS E1 paragraph 17,
                the undertaking shall disclose its policies adopted to manage its material impacts, risks,
                and opportunities related to climate change mitigation and adaptation. This disclosure
                covers the policy framework, scope, governance, and implementation mechanisms.
            </p>
        </div>

        <h5 style="color:#2d3748;margin-top:16px;">1. Climate Policy Framework (ESRS E1 par. 17-18)</h5>
        <p>
            <strong>{company_name}</strong> has adopted a comprehensive climate policy framework that
            addresses both climate change mitigation (reducing GHG emissions) and climate change
            adaptation (building resilience to physical climate risks). The framework consists of the
            following key policies, each approved by the relevant governance body:
        </p>
        <table style="width:100%;border-collapse:collapse;margin:12px 0;">
            <thead>
                <tr style="background-color:#edf2f7;">
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Policy Name</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Scope</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Approval Date</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Review Cycle</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">ESRS Reference</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Climate Change Policy</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Group-wide (all operations)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_climate_policy_date")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Annual</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-2.17</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Energy and Renewable Energy Policy</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Group-wide (all operations)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_energy_policy_date")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Biennial</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-2.17</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Climate Adaptation and Resilience Policy</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Group-wide (all operations)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_adaptation_policy_date")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Biennial</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-2.17</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Sustainable Procurement and Supply Chain Policy</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Value chain (Scope 3)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_procurement_policy_date")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Annual</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-2.17</td>
                </tr>
            </tbody>
        </table>

        <h5 style="color:#2d3748;margin-top:16px;">2. Policy Content and Objectives (ESRS E1 par. 19-21)</h5>
        <p>
            In accordance with ESRS E1 paragraph 19, each policy within the climate policy framework
            addresses the following elements:
        </p>
        <ul style="margin:8px 0;padding-left:20px;">
            <li><strong>Climate change mitigation (par. 19(a)):</strong> The policies commit the undertaking to
            reducing its GHG emissions in line with the Paris Agreement goals. The Climate Change Policy
            establishes a quantitative emission reduction target pathway consistent with limiting global
            warming to 1.5°C, with intermediate milestones for 2030, 2040, and 2050. The policy covers
            all Scope 1, Scope 2, and material Scope 3 emission sources.</li>
            <li><strong>Climate change adaptation (par. 19(b)):</strong> The Climate Adaptation and Resilience
            Policy addresses the undertaking's physical climate risk exposure. It requires the systematic
            identification, assessment, and management of climate-related physical risks (both acute
            and chronic) across all operations. The policy sets minimum resilience standards for new
            facilities and requires adaptation plans for existing facilities identified as high-risk.</li>
            <li><strong>Decarbonisation levers (par. 19(c)):</strong> The policies define the specific
            decarbonisation levers to be pursued, including energy efficiency improvements, renewable
            energy sourcing, electrification, supply chain engagement, and carbon removal. Each lever
            has associated targets, timelines, and accountability.</li>
            <li><strong>Policy alignment (par. 20):</strong> The policies are aligned with the latest
            climate science (IPCC), the Paris Agreement, the European Climate Law, and relevant
            national and sectoral climate policies in the jurisdictions where the undertaking operates.</li>
        </ul>

        <h5 style="color:#2d3748;margin-top:16px;">3. Governance and Accountability (ESRS E1 par. 22-23)</h5>
        <p>
            The climate policy framework is governed as follows (ESRS E1 paragraph 22):
        </p>
        <ul style="margin:8px 0;padding-left:20px;">
            <li><strong>Board-level oversight:</strong> The board of directors (or equivalent governance body)
            has ultimate responsibility for the climate policy framework. A dedicated sustainability
            committee (or the audit committee, as applicable) reviews policy implementation, progress
            against targets, and material climate-related risks at least quarterly.</li>
            <li><strong>Management responsibility:</strong> The Chief Sustainability Officer (CSO) or equivalent
            senior management position is responsible for the day-to-day implementation of climate policies
            and reports directly to the board on a quarterly basis.</li>
            <li><strong>Policy ownership:</strong> Each policy has a designated policy owner from the relevant
            business function (e.g., operations, procurement, facilities management) who is responsible
            for implementation, monitoring, and reporting.</li>
            <li><strong>Employee accountability:</strong> Climate-related performance metrics are integrated
            into the variable compensation criteria for senior management and relevant operational
            roles (ESRS E1 paragraph 23). The weight of climate-related metrics in the annual
            variable compensation is {val("e1_climate_comp_weight")}% for executive management.</li>
        </ul>

        <h5 style="color:#2d3748;margin-top:16px;">4. Policy Implementation Mechanisms (ESRS E1 par. 24)</h5>
        <p>
            In accordance with ESRS E1 paragraph 24, the undertaking has established the following
            mechanisms to ensure effective implementation of its climate policies:
        </p>
        <ul style="margin:8px 0;padding-left:20px;">
            <li><strong>Internal carbon pricing:</strong> The undertaking operates an internal carbon pricing
            mechanism with a current price of EUR {val("e1_internal_carbon_price")} per tonne of CO₂ equivalent. The
            internal carbon price is applied to all material investment decisions (CapEx above
            EUR {val("e1_capex_threshold")}) and is reviewed annually. The price trajectory is aligned with the
            IEA NZE scenario projection, reaching EUR {val("e1_internal_cp_2030")}/tCO₂ by 2030.</li>
            <li><strong>Environmental management system (EMS):</strong> Climate-related policies are integrated
            into the undertaking's certified environmental management system (ISO 14001 or equivalent),
            covering {val("e1_ems_coverage_pct")}% of operations.</li>
            <li><strong>Training and awareness:</strong> Mandatory climate change awareness training is
            provided to all employees. In {year_n}, {val("e1_training_completion_pct")}% of employees completed the
            training programme.</li>
            <li><strong>Monitoring and reporting:</strong> Policy implementation is monitored through a
            dedicated climate dashboard that tracks key performance indicators (KPIs) including
            emission reductions, energy consumption, renewable energy share, and adaptation
            progress. Performance is reported to management monthly and to the board quarterly.</li>
        </ul>
        <p style="font-size:12px;color:#718096;">
            <strong>Methodology (ESRS E1 par. 17-24):</strong> The climate policy framework is reviewed
            at least annually to ensure continued alignment with scientific developments, regulatory
            requirements, and stakeholder expectations. Policy updates are approved by the board.
            The policies are publicly available on the undertaking's website and are communicated to
            all employees through the internal communication platform. This disclosure is prepared
            in accordance with ESRS E1 Application Requirements (AR 1-8) and EFRAG IG 1 paragraphs
            32-38.
        </p>
    </div>
    """


def build_e1_3_actions_and_resources(
    company_name: str,
    reporting_year: int,
    context: Optional[Dict[str, str]] = None,
) -> str:
    """
    Generate ESRS E1-3 — Actions and resources in relation to climate change policies (par. 25-32).

    Args:
        company_name: Name of the undertaking
        reporting_year: Reporting year (e.g., 2025)
        context: Dict of company context values to fill [TBC:*] placeholders

    Returns:
        HTML string with narrative for ESRS E1-3 (paragraphs 25-32)
    """
    ctx = context or {}
    year_n = str(reporting_year)
    year_n1 = str(reporting_year - 1)

    def val(key: str, default: str = "[TO BE CONFIRMED]") -> str:
        v = ctx.get(key)
        return str(v) if v else default

    return f"""
    <div class="e1-3-actions-resources" style="margin:24px 0;">
        <h4 style="color:#1a365d;font-size:18px;border-bottom:1px solid #2b6cb0;padding-bottom:6px;">
            E1-3 — Actions and Resources in Relation to Climate Change Policies (ESRS E1 paragraphs 25-32)
        </h4>

        <div class="section-intro" style="margin:12px 0;padding:10px 14px;border-left:4px solid #38a169;background-color:#f0fff4;">
            <p style="margin:4px 0;">
                <strong>Disclosure Requirement E1-3</strong> — In accordance with ESRS E1 paragraph 25,
                the undertaking shall disclose its climate-related actions and the resources allocated
                for their implementation. This disclosure covers the key actions taken or planned,
                the associated CapEx and OpEx, and the expected emission reduction outcomes.
            </p>
        </div>

        <h5 style="color:#2d3748;margin-top:16px;">1. Key Climate Actions (ESRS E1 par. 25-27)</h5>
        <p>
            <strong>{company_name}</strong> has identified and implemented a set of climate actions
            to deliver on its climate change mitigation and adaptation objectives. The following table
            summarises the key actions undertaken during the reporting period and planned for future
            periods, in accordance with ESRS E1 paragraph 25.
        </p>
        <table style="width:100%;border-collapse:collapse;margin:12px 0;">
            <thead>
                <tr style="background-color:#edf2f7;">
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Action / Initiative</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Scope</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Status</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">Estimated Emission Reduction (tCO₂e/year)</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Timeline</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">ESRS Reference</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Energy efficiency retrofits — major facilities</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Scope 1 & 2</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_action_ee_status")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_action_ee_reduction")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_action_ee_timeline")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-3.25(a)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Renewable energy PPAs and on-site solar installations</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Scope 2</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_action_re_status")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_action_re_reduction")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_action_re_timeline")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-3.25(b)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Vehicle fleet electrification</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Scope 1</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_action_ev_status")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_action_ev_reduction")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_action_ev_timeline")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-3.25(c)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Supplier engagement programme — Science Based Targets</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Scope 3</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_action_supplier_status")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_action_supplier_reduction")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_action_supplier_timeline")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-3.25(d)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Climate adaptation — facility resilience upgrades</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Physical risk</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_action_adaptation_status")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">N/A (risk reduction)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_action_adaptation_timeline")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-3.25(e)</td>
                </tr>
            </tbody>
        </table>

        <h5 style="color:#2d3748;margin-top:16px;">2. Capital Expenditure (CapEx) and Operational Expenditure (OpEx) Allocation (ESRS E1 par. 28-29)</h5>
        <p>
            In accordance with ESRS E1 paragraph 28, the following table presents the financial resources
            allocated to climate-related actions during the reporting period. All figures are presented
            in EUR.
        </p>
        <table style="width:100%;border-collapse:collapse;margin:12px 0;">
            <thead>
                <tr style="background-color:#edf2f7;">
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Action Category</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">CapEx {year_n} (EUR)</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">OpEx {year_n} (EUR)</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">Planned CapEx {year_n1} (EUR)</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">ESRS Reference</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Energy efficiency improvements</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_capex_ee")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_opex_ee")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_capex_ee_planned")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-3.28(a)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Renewable energy (PPAs, on-site generation)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_capex_re")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_opex_re")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_capex_re_planned")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-3.28(b)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Fleet electrification and low-emission vehicles</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_capex_fleet")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_opex_fleet")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_capex_fleet_planned")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-3.28(c)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Supply chain decarbonisation programme</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_capex_sc")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_opex_sc")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_capex_sc_planned")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-3.28(d)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Climate adaptation and resilience measures</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_capex_adapt")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_opex_adapt")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_capex_adapt_planned")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-3.28(e)</td>
                </tr>
                <tr style="font-weight:bold;background-color:#edf2f7;">
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;"><strong>Total climate-related expenditure</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"><strong>{val("e1_capex_total")}</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"><strong>{val("e1_opex_total")}</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"><strong>{val("e1_capex_total_planned")}</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-3.29</td>
                </tr>
            </tbody>
        </table>
        <p>
            The share of CapEx allocated to climate-related actions represents {val("e1_climate_capex_share")}% of the
            undertaking's total CapEx for the reporting period. The share of OpEx allocated to
            climate-related actions represents {val("e1_climate_opex_share")}% of the undertaking's total OpEx for
            the reporting period (ESRS E1 paragraph 29).
        </p>

        <h5 style="color:#2d3748;margin-top:16px;">3. Enabling Actions and Capacity Building (ESRS E1 par. 30-31)</h5>
        <p>
            In addition to the direct emission reduction actions described above, the undertaking has
            implemented the following enabling actions in accordance with ESRS E1 paragraph 30:
        </p>
        <ul style="margin:8px 0;padding-left:20px;">
            <li><strong>Carbon accounting system enhancement:</strong> Implementation of an upgraded GHG
            emission data management system to improve Scope 1, 2, and 3 data quality, collection
            frequency, and assurance readiness.</li>
            <li><strong>Internal carbon pricing mechanism:</strong> Operation and expansion of the internal
            carbon pricing mechanism across all material investment decisions (see E1-2 for details).</li>
            <li><strong>Climate risk assessment tool:</strong> Development and deployment of a climate risk
            assessment tool covering physical and transition risks across all operational sites.</li>
            <li><strong>Employee climate training programme:</strong> Ongoing delivery of climate awareness
            and skills development training to employees, with a focus on energy management,
            sustainable procurement, and climate risk management.</li>
            <li><strong>Research and development:</strong> Investment in low-carbon product and process
            innovation, including {val("e1_rd_description", "specific R&D projects for low-carbon product development")}.</li>
        </ul>

        <h5 style="color:#2d3748;margin-top:16px;">4. Partnership and Collaborative Initiatives (ESRS E1 par. 32)</h5>
        <p>
            In accordance with ESRS E1 paragraph 32, the undertaking participates in the following
            partnerships and collaborative initiatives related to climate action:
        </p>
        <ul style="margin:8px 0;padding-left:20px;">
            <li>Science Based Targets initiative (SBTi) — committed to 1.5°C-aligned target validation</li>
            <li>CDP (formerly Carbon Disclosure Project) — annual disclosure of climate-related data</li>
            <li>{val("e1_initiative_1", "Industry-specific decarbonisation initiative")}</li>
            <li>{val("e1_initiative_2", "Supply chain collaboration on emission reduction (e.g., Together for Sustainability)")}</li>
            <li>{val("e1_initiative_3", "Participation in sectoral climate working groups and policy dialogues")}</li>
        </ul>
        <p style="font-size:12px;color:#718096;">
            <strong>Methodology (ESRS E1 par. 25-32):</strong> CapEx and OpEx are tracked through
            the undertaking's financial management system using dedicated cost centres for climate-related
            activities. Emission reductions are estimated based on ex-ante calculations using recognised
            methodologies (ISO 50004 for energy efficiency, emission factors from recognised sources
            for renewable energy displacement, etc.) and are subject to internal verification.
            Expenditure data is audited as part of the statutory financial audit. This disclosure is
            prepared in accordance with ESRS E1 Application Requirements (AR 9-18) and EFRAG IG 1
            paragraphs 39-44.
        </p>
    </div>
    """


def build_e1_4_targets(
    company_name: str,
    reporting_year: int,
    context: Optional[Dict[str, str]] = None,
) -> str:
    """
    Generate ESRS E1-4 — Targets related to climate change mitigation and adaptation (par. 33-40).

    Args:
        company_name: Name of the undertaking
        reporting_year: Reporting year (e.g., 2025)
        context: Dict of company context values to fill [TBC:*] placeholders

    Returns:
        HTML string with narrative for ESRS E1-4 (paragraphs 33-40)
    """
    ctx = context or {}
    year_n = str(reporting_year)
    year_n1 = str(reporting_year - 1)

    def val(key: str, default: str = "[TO BE CONFIRMED]") -> str:
        v = ctx.get(key)
        return str(v) if v else default

    return f"""
    <div class="e1-4-targets" style="margin:24px 0;">
        <h4 style="color:#1a365d;font-size:18px;border-bottom:1px solid #2b6cb0;padding-bottom:6px;">
            E1-4 — Targets Related to Climate Change Mitigation and Adaptation (ESRS E1 paragraphs 33-40)
        </h4>

        <div class="section-intro" style="margin:12px 0;padding:10px 14px;border-left:4px solid #38a169;background-color:#f0fff4;">
            <p style="margin:4px 0;">
                <strong>Disclosure Requirement E1-4</strong> — In accordance with ESRS E1 paragraph 33,
                the undertaking shall disclose its climate-related targets, including GHG emission reduction
                targets, energy efficiency targets, renewable energy targets, and adaptation targets. All
                targets are set in alignment with the undertaking's transition plan (E1-1) and are consistent
                with the goal of achieving climate neutrality by 2050.
            </p>
        </div>

        <h5 style="color:#2d3748;margin-top:16px;">1. GHG Emission Reduction Targets (ESRS E1 par. 33-36)</h5>
        <p>
            <strong>{company_name}</strong> has set the following GHG emission reduction targets, which
            have been approved by the board and are subject to annual review. The targets are expressed
            as absolute emission reductions against a defined base year, in accordance with ESRS E1
            paragraph 34.
        </p>
        <table style="width:100%;border-collapse:collapse;margin:12px 0;">
            <thead>
                <tr style="background-color:#edf2f7;">
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Target</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Scope</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Base Year</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Base Year Emissions (tCO₂e)</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">2030 Reduction Target</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">2040 Reduction Target</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">2050 Target (Climate Neutrality)</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">ESRS Reference</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Absolute Scope 1 & 2 reduction</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Scope 1 + 2 (market-based)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_ghg_base_year")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_ghg_base_scope12")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_target_2030_scope12")}% reduction</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_target_2040_scope12")}% reduction</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_target_2050_scope12")}% reduction (net zero)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-4.34(a)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Absolute Scope 3 reduction</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Scope 3 (material categories)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_ghg_base_year")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_ghg_base_scope3")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_target_2030_scope3")}% reduction</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_target_2040_scope3")}% reduction</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_target_2050_scope3")}% reduction (net zero)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-4.34(b)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Combined absolute reduction (all scopes)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Scope 1 + 2 + 3</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_ghg_base_year")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_ghg_base_total")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_target_2030_total")}% reduction</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_target_2040_total")}% reduction</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_target_2050_total")}% reduction (net zero)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-4.34(c)</td>
                </tr>
            </tbody>
        </table>

        <h5 style="color:#2d3748;margin-top:16px;">2. Target Methodology and Alignment with SBTi (ESRS E1 par. 35-36)</h5>
        <p>
            The GHG emission reduction targets have been developed in accordance with the following
            methodology (ESRS E1 paragraph 35):
        </p>
        <ul style="margin:8px 0;padding-left:20px;">
            <li><strong>Base year selection:</strong> The base year {val("e1_ghg_base_year")} was selected as it represents
            a year for which comprehensive and verified GHG emission data is available for all
            material scopes (ESRS E1 paragraph 35(a)).</li>
            <li><strong>Scope Coverage:</strong> Targets cover Scope 1 (direct emissions), Scope 2 (market-based
            method for indirect energy emissions), and Scope 3 (material upstream and downstream
            categories) in accordance with the GHG Protocol Corporate Accounting and Reporting
            Standard (Revised Edition) and the GHG Protocol Scope 3 Standard (ESRS E1 paragraph 35(b)).</li>
            <li><strong>Science-based alignment:</strong> The targets are aligned with the criteria of the
            Science Based Targets initiative (SBTi) for a 1.5°C pathway. The undertaking has submitted
            its targets to the SBTi for formal validation (ESRS E1 paragraph 35(c)).</li>
            <li><strong>Base year recalculations:</strong> Base year emissions will be recalculated in the
            event of structural changes (acquisitions, divestments, mergers), methodology changes,
            or significant changes in emission factors. The undertaking's base year recalculation
            policy follows the GHG Protocol Corporate Standard (Section 5.3) and the SBTi criteria
            (ESRS E1 paragraph 36).</li>
        </ul>

        <h5 style="color:#2d3748;margin-top:16px;">3. Energy Efficiency and Renewable Energy Targets (ESRS E1 par. 37-38)</h5>
        <table style="width:100%;border-collapse:collapse;margin:12px 0;">
            <thead>
                <tr style="background-color:#edf2f7;">
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Target</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Base Year</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Current Value ({year_n})</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">2030 Target</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">2050 Target</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">ESRS Reference</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Energy intensity reduction (MWh/€ revenue)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_energy_base_year")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_energy_intensity_current")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_energy_intensity_2030")}% reduction</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_energy_intensity_2050")}% reduction</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-4.37(a)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Renewable energy share of total energy consumption</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_re_base_year")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_re_share_current")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_re_share_2030")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_re_share_2050")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-4.37(b)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">On-site renewable energy generation capacity</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_re_base_year")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_on_site_re_capacity_current")} MW</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_on_site_re_capacity_2030")} MW</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_on_site_re_capacity_2050")} MW</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-4.37(c)</td>
                </tr>
            </tbody>
        </table>

        <h5 style="color:#2d3748;margin-top:16px;">4. Climate Adaptation Targets (ESRS E1 par. 38)</h5>
        <p>
            In accordance with ESRS E1 paragraph 38, the undertaking has established the following
            targets for climate change adaptation:
        </p>
        <ul style="margin:8px 0;padding-left:20px;">
            <li><strong>Physical risk assessment coverage:</strong> {val("e1_adapt_target_coverage")}% of operational sites assessed
            for physical climate risks by {val("e1_adapt_target_year")}.</li>
            <li><strong>Resilience improvement:</strong> Implementation of climate adaptation measures at
            {val("e1_adapt_target_sites")} high-risk sites by {val("e1_adapt_target_milestone_year")}.</li>
            <li><strong>Business continuity:</strong> Integration of climate-related physical risk scenarios
            into {val("e1_adapt_target_bcp")}% of site-level business continuity plans (BCPs).</li>
        </ul>

        <h5 style="color:#2d3748;margin-top:16px;">5. Target Progress Tracking and Review (ESRS E1 par. 39-40)</h5>
        <p>
            Progress against each target is tracked annually and reported to the board. The following
            table presents the current progress status for the key emission reduction targets
            (ESRS E1 paragraph 39).
        </p>
        <table style="width:100%;border-collapse:collapse;margin:12px 0;">
            <thead>
                <tr style="background-color:#edf2f7;">
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Target</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">Most Recent Value ({year_n})</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">Value ({year_n1})</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">Target ({val('e1_target_year_2030', '2030')})</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">% Achieved</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">On Track?</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Scope 1 & 2 absolute reduction (vs base year)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_progress_scope12_current")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_progress_scope12_n1")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_target_2030_scope12")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_progress_scope12_pct_achieved")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_ontrack_scope12")}</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Scope 3 absolute reduction (vs base year)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_progress_scope3_current")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_progress_scope3_n1")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_target_2030_scope3")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_progress_scope3_pct_achieved")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_ontrack_scope3")}</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Renewable energy share of total consumption</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_re_share_current")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_re_share_n1")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_re_share_2030")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_re_share_pct_achieved")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">{val("e1_ontrack_re")}</td>
                </tr>
            </tbody>
        </table>
        <p>
            Targets are reviewed at least annually by the board. In the event of significant
            underperformance against any target (defined as more than {val("e1_target_deviation_threshold", "20%")} deviation from the
            planned trajectory), the board shall review and, if necessary, revise the associated
            actions, resources, or target ambition level (ESRS E1 paragraph 40).
        </p>
        <p style="font-size:12px;color:#718096;">
            <strong>Methodology (ESRS E1 par. 33-40):</strong> All targets use absolute reduction
            methodology (tCO₂e reduction against base year) in accordance with ESRS E1 AR 19-28.
            Emission reduction calculations follow the GHG Protocol Corporate Accounting and Reporting
            Standard and the GHG Protocol Scope 3 Standard. Progress is measured as the percentage
            of the target achieved relative to the base year (e.g., if the 2030 target is a 50%
            reduction from base year and the current reduction is 20%, the progress is 40%).
            Targets are aligned with the SBTi criteria for a 1.5°C pathway where applicable.
            This disclosure is consistent with EFRAG IG 1 paragraphs 53-62.
        </p>
    </div>
    """


def build_e1_5_energy_consumption_and_mix(
    company_name: str,
    reporting_year: int,
    context: Optional[Dict[str, str]] = None,
) -> str:
    """
    Generate ESRS E1-5 — Energy consumption and mix (par. 41-48) with data tables.

    Args:
        company_name: Name of the undertaking
        reporting_year: Reporting year (e.g., 2025)
        context: Dict of company context values to fill [TBC:*] placeholders

    Returns:
        HTML string with narrative and data tables for ESRS E1-5 (paragraphs 41-48)
    """
    ctx = context or {}
    year_n = str(reporting_year)
    year_n1 = str(reporting_year - 1)

    def val(key: str, default: str = "[TO BE CONFIRMED]") -> str:
        v = ctx.get(key)
        return str(v) if v else default

    return f"""
    <div class="e1-5-energy" style="margin:24px 0;">
        <h4 style="color:#1a365d;font-size:18px;border-bottom:1px solid #2b6cb0;padding-bottom:6px;">
            E1-5 — Energy Consumption and Mix (ESRS E1 paragraphs 41-48)
        </h4>

        <div class="section-intro" style="margin:12px 0;padding:10px 14px;border-left:4px solid #38a169;background-color:#f0fff4;">
            <p style="margin:4px 0;">
                <strong>Disclosure Requirement E1-5</strong> — In accordance with ESRS E1 paragraph 41,
                the undertaking shall disclose its total energy consumption, the share of renewable
                and non-renewable energy sources, and energy intensity ratio. All energy consumption
                figures are presented in MWh. This disclosure covers the undertaking's own operations
                (Scope 1 and 2 energy consumption) and, where material, energy consumption from the
                value chain.
            </p>
        </div>

        <h5 style="color:#2d3748;margin-top:16px;">1. Energy Consumption by Source (ESRS E1 par. 41-44)</h5>
        <p>
            <strong>{company_name}</strong> reports energy consumption in accordance with ESRS E1
            paragraphs 41-44. The following table presents the breakdown of total energy consumption
            by energy source for the reporting period.
        </p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0;">
            <thead>
                <tr style="background-color:#1a365d;color:white;">
                    <th style="border:1px solid #2b6cb0;padding:10px 12px;text-align:left;">Energy Source</th>
                    <th style="border:1px solid #2b6cb0;padding:10px 12px;text-align:right;">{year_n1} (MWh)</th>
                    <th style="border:1px solid #2b6cb0;padding:10px 12px;text-align:right;">{year_n} (MWh)</th>
                    <th style="border:1px solid #2b6cb0;padding:10px 12px;text-align:right;">Change (%)</th>
                    <th style="border:1px solid #2b6cb0;padding:10px 12px;text-align:left;">Type</th>
                    <th style="border:1px solid #2b6cb0;padding:10px 12px;text-align:left;">ESRS Reference</th>
                </tr>
            </thead>
            <tbody>
                <!-- Fossil fuel sources — non-renewable -->
                <tr style="background-color:#fff5f5;">
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;font-weight:bold;">Non-renewable energy sources</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;"></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;"></td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">&nbsp;&nbsp;Fossil — Natural gas</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_gas_n1")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_gas")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_gas_change")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Non-renewable</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.42(a)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">&nbsp;&nbsp;Fossil — Diesel and petrol (vehicle fleet)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_diesel_n1")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_diesel")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_diesel_change")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Non-renewable</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.42(a)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">&nbsp;&nbsp;Fossil — Other (fuel oil, coal, LPG)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_other_fossil_n1")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_other_fossil")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_other_fossil_change")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Non-renewable</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.42(a)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">&nbsp;&nbsp;Purchased electricity (grid, non-renewable mix)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_grid_nr_n1")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_grid_nr")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_grid_nr_change")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Non-renewable</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.42(b)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">&nbsp;&nbsp;Purchased heat and steam (non-renewable)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_heat_nr_n1")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_heat_nr")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_heat_nr_change")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Non-renewable</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.42(c)</td>
                </tr>
                <tr style="background-color:#fff5f5;font-weight:bold;">
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;"><strong>Total non-renewable energy consumption</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"><strong>{val("e1_energy_total_nr_n1")}</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"><strong>{val("e1_energy_total_nr")}</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"><strong>{val("e1_energy_total_nr_change")}</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Non-renewable</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.42</td>
                </tr>

                <!-- Renewable energy sources -->
                <tr style="background-color:#f0fff4;">
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;font-weight:bold;">Renewable energy sources</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;"></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;"></td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">&nbsp;&nbsp;Purchased renewable electricity (PPAs, green tariffs)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_re_elec_n1")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_re_elec")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_re_elec_change")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Renewable</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.43(a)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">&nbsp;&nbsp;On-site renewable energy generation (solar PV)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_re_onsite_n1")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_re_onsite")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_re_onsite_change")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Renewable</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.43(a)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">&nbsp;&nbsp;On-site renewable energy generation (wind)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_re_wind_n1")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_re_wind")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_re_wind_change")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Renewable</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.43(a)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">&nbsp;&nbsp;Purchased renewable heat and steam</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_re_heat_n1")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_re_heat")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_re_heat_change")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Renewable</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.43(b)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">&nbsp;&nbsp;Renewable fuel consumption (biofuels, biomass, hydrogen)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_re_fuel_n1")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_re_fuel")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_re_fuel_change")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Renewable</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.43(a)</td>
                </tr>
                <tr style="background-color:#f0fff4;font-weight:bold;">
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;"><strong>Total renewable energy consumption</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"><strong>{val("e1_energy_total_re_n1")}</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"><strong>{val("e1_energy_total_re")}</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"><strong>{val("e1_energy_total_re_change")}</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Renewable</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.43</td>
                </tr>

                <!-- Total -->
                <tr style="background-color:#edf2f7;font-weight:bold;">
                    <td style="border:1px solid #e2e8f0;padding:10px 12px;"><strong>Total energy consumption (renewable + non-renewable)</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:10px 12px;text-align:right;"><strong>{val("e1_energy_total_n1")}</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:10px 12px;text-align:right;"><strong>{val("e1_energy_total")}</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:10px 12px;text-align:right;"><strong>{val("e1_energy_total_change")}</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:10px 12px;">Total</td>
                    <td style="border:1px solid #e2e8f0;padding:10px 12px;">ESRS E1-5.41</td>
                </tr>
            </tbody>
        </table>

        <h5 style="color:#2d3748;margin-top:16px;">2. Renewable vs. Non-Renewable Energy Split (ESRS E1 par. 43-44)</h5>
        <table style="width:100%;border-collapse:collapse;margin:12px 0;">
            <thead>
                <tr style="background-color:#edf2f7;">
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Metric</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{year_n1}</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{year_n}</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">ESRS Reference</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Renewable energy share (%)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_re_share_n1")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_re_share_current")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.44(a)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Non-renewable energy share (%)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_nr_share_n1")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_nr_share_current")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.44(b)</td>
                </tr>
                <tr style="font-weight:bold;background-color:#edf2f7;">
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;"><strong>Total energy consumption — Own operations</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"><strong>{val("e1_energy_total_n1")}</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"><strong>{val("e1_energy_total")}</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.44(c)</td>
                </tr>
            </tbody>
        </table>

        <h5 style="color:#2d3748;margin-top:16px;">3. Energy Intensity Ratio (ESRS E1 par. 45-46)</h5>
        <p>
            In accordance with ESRS E1 paragraph 45, the undertaking presents its energy intensity
            ratio, calculated as total energy consumption (in MWh) divided by net revenue (in EUR).
        </p>
        <table style="width:100%;border-collapse:collapse;margin:12px 0;">
            <thead>
                <tr style="background-color:#edf2f7;">
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Metric</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{year_n1}</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{year_n}</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">Unit</th>
                    <th style="border:1px solid #e2e8f0;padding:8px 10px;text-align:left;">ESRS Reference</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Net revenue</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_revenue_n1")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_revenue")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">EUR</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.45(a)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Total energy consumption (own operations)</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_total_n1")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_total")}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">MWh</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.45(b)</td>
                </tr>
                <tr style="font-weight:bold;background-color:#edf2f7;">
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;"><strong>Energy intensity ratio</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"><strong>{val("e1_energy_intensity_n1")}</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;"><strong>{val("e1_energy_intensity")}</strong></td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">MWh / EUR</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.45(c)</td>
                </tr>
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">Year-on-year change in energy intensity</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">—</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;text-align:right;">{val("e1_energy_intensity_change")}%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">%</td>
                    <td style="border:1px solid #e2e8f0;padding:8px 10px;">ESRS E1-5.46</td>
                </tr>
            </tbody>
        </table>

        <h5 style="color:#2d3748;margin-top:16px;">4. Methodology and Context (ESRS E1 par. 47-48)</h5>
        <p>
            The energy consumption data is collected and calculated in accordance with the following
            methodology (ESRS E1 paragraph 47):
        </p>
        <ul style="margin:8px 0;padding-left:20px;">
            <li><strong>Scope of reporting:</strong> Energy consumption covers all facilities and operations
            over which <strong>{company_name}</strong> has operational control. This includes
            manufacturing sites, warehouses, office buildings, and the owned vehicle fleet.
            Energy consumption from leased assets is included where the undertaking is responsible
            for energy procurement.</li>
            <li><strong>Data sources:</strong> Energy data is collected from utility invoices, on-site
            meter readings, fuel purchase records, and fleet fuel management systems. Where direct
            meter readings are not available, estimates are used based on floor area, operating
            hours, and industry benchmarks.</li>
            <li><strong>Conversion factors:</strong> All energy quantities are reported in MWh using
            standard conversion factors. Fuel volumes are converted to MWh using net calorific
            values from the IPCC Guidelines for National Greenhouse Gas Inventories (2019) and
            the IEA Energy Statistics Manual. Electricity and heat are reported at the final
            consumption level.</li>
            <li><strong>Renewable vs. non-renewable classification (par. 48):</strong> Energy is classified as
            renewable if it is derived from sources that are naturally replenished at a rate that
            exceeds their rate of consumption, including solar, wind, hydro, geothermal, biomass,
            and renewable hydrogen (as defined in Directive (EU) 2018/2001 — RED II). Purchased
            electricity is classified as renewable where supported by Guarantees of Origin (GOs)
            or equivalent contractual instruments under the GHGP Scope 2 Quality Criteria, with
            a 12-month matching period.</li>
        </ul>
        <p style="font-size:12px;color:#718096;">
            <strong>Methodology (ESRS E1 par. 41-48):</strong> This disclosure is prepared in accordance
            with ESRS E1 Application Requirements (AR 29-38) and the EFRAG IG 1 implementation guidance
            (paragraphs 63-74). Energy data is subject to the undertaking's internal control framework
            and is verified as part of the limited assurance engagement on the sustainability statement.
            Comparative figures for {year_n1} are provided where available. All quantitative values
            marked [TO BE CONFIRMED] will be populated with verified data prior to finalisation of
            the sustainability statement.
        </p>
    </div>
    """


def build_e1_disclosure(
    company_name: str,
    reporting_year: int,
    context: Optional[Dict[str, str]] = None,
) -> str:
    """
    Generate the complete ESRS E1 disclosure HTML block covering E1-1 through E1-5.

    Args:
        company_name: Name of the undertaking
        reporting_year: Reporting year (e.g., 2025)
        context: Dict of company context values to fill [TBC:*] placeholders

    Returns:
        HTML string with tables and narrative for ESRS E1 (paragraphs 1-48)
    """
    ctx = context or {}
    year_n = str(reporting_year)
    year_n1 = str(reporting_year - 1)

    def val(key: str, default: str = "[TO BE CONFIRMED]") -> str:
        v = ctx.get(key)
        return str(v) if v else default

    # Build individual sections
    e1_1_html = build_e1_1_transition_plan(company_name, reporting_year, context)
    e1_2_html = build_e1_2_policies(company_name, reporting_year, context)
    e1_3_html = build_e1_3_actions_and_resources(company_name, reporting_year, context)
    e1_4_html = build_e1_4_targets(company_name, reporting_year, context)
    e1_5_html = build_e1_5_energy_consumption_and_mix(company_name, reporting_year, context)

    # ── ASSEMBLY ────────────────────────────────────────────────
    full_html = f"""<div class="e1-full-disclosure" style="margin:24px 0;">
    <h3 style="color:#1a365d;border-bottom:2px solid #2b6cb0;padding-bottom:8px;font-size:20px;">
        ESRS E1 — Climate Change (ESRS E1 paragraphs 1-48)
    </h3>

    <div class="e1-narrative-intro" style="margin:16px 0;padding:12px 16px;border-left:4px solid #3182ce;background-color:#ebf8ff;">
        <p><strong>Disclosure Requirement E1 (Climate Change)</strong> — This section covers the
        undertaking's disclosures related to climate change mitigation and adaptation, including the
        transition plan (E1-1), policies (E1-2), actions and resources (E1-3), targets (E1-4), and
        energy consumption and mix (E1-5). The disclosures cover the reporting period {year_n} with
        comparative data for {year_n1} where available. All metrics marked <em>[TO BE CONFIRMED]</em>
        will be populated with verified data prior to finalisation.</p>
        <p style="font-size:13px;color:#4a5568;">
            <strong>Materiality assessment outcome:</strong> Climate change has been identified as a
            material topic for {company_name} through the double materiality assessment (see IRO-1 and
            IRO-2). The following disclosure requirements under ESRS E1 are therefore included in this
            sustainability statement. The undertaking has assessed both its impacts on climate change
            (impact materiality) and the climate-related risks and opportunities affecting its financial
            position, performance, and access to finance (financial materiality).
        </p>
    </div>

    <hr style="margin:24px 0;"/>

    {e1_1_html}

    <hr style="margin:24px 0;"/>

    {e1_2_html}

    <hr style="margin:24px 0;"/>

    {e1_3_html}

    <hr style="margin:24px 0;"/>

    {e1_4_html}

    <hr style="margin:24px 0;"/>

    {e1_5_html}

    <hr style="margin:24px 0;"/>

    <div class="e1-data-quality" style="margin:16px 0;padding:12px 16px;border-left:4px solid #ecc94b;background-color:#fffff0;">
        <h5 style="color:#975a16;margin:0 0 8px 0;">Data Quality and Assurance</h5>
        <p style="font-size:13px;color:#744210;margin:4px 0;">
            <strong>Data sources:</strong> Energy consumption data is sourced from utility invoices, fuel
            purchase records, and on-site metering systems. GHG emission data is calculated using the
            GHG Protocol Corporate Accounting and Reporting Standard (Revised Edition) and relevant
            emission factors from the UK BEIS/DEFRA, IEA, and national grid emission factor databases,
            as applicable. Where primary data is not available, secondary data and estimates are used
            as noted in the relevant sections.<br/><br/>
            <strong>Assurance status:</strong> The climate-related disclosures in this section are subject
            to limited assurance engagement as part of the overall sustainability statement assurance
            process. The assurance report is included in the Assurance section of this report.<br/><br/>
            <strong>Data gaps and improvements:</strong> Where exact data is not available for certain
            metrics, it is indicated as [TO BE CONFIRMED]. The undertaking is committed to improving
            data completeness and quality across successive reporting cycles, with a target of achieving
            comprehensive primary data coverage for all material energy and emission sources by
            {val("e1_data_quality_target_year", year_n1)}.
        </p>
    </div>

</div>"""

    return full_html


def build_e1_content_block(
    company_name: str,
    reporting_year: int,
    context: Optional[Dict[str, str]] = None,
    block_id: str = "e1-climate-full",
) -> 'ContentBlock':
    """
    Create a ContentBlock for the full ESRS E1 disclosure (E1-1 through E1-5).

    Args:
        company_name: Name of the undertaking
        reporting_year: Reporting year
        context: Company context data for placeholder resolution
        block_id: Block ID for the content block

    Returns:
        ContentBlock of type 'narrative' with the full E1 disclosure HTML
    """
    # Late import to avoid circular dependencies
    from template_engine import ContentBlock

    html = build_e1_disclosure(
        company_name=company_name,
        reporting_year=reporting_year,
        context=context,
    )

    return ContentBlock(
        block_id=block_id,
        standard_ref="ESRS E1",
        paragraph_ref="1-48",
        title="E1 — Climate Change Mitigation and Adaptation (Full Disclosure)",
        content_html=html,
        content_type="narrative",
        datapoint_refs=[
            # E1-1: Transition plan
            "ESRS E1-1.1",
            "ESRS E1-1.2(a)",
            "ESRS E1-1.2(b)",
            "ESRS E1-1.2(c)",
            "ESRS E1-1.2(d)",
            "ESRS E1-1.2(e)",
            "ESRS E1-1.3",
            "ESRS E1-1.10",
            "ESRS E1-1.13",
            "ESRS E1-1.14",
            "ESRS E1-1.15",
            "ESRS E1-1.16",
            # E1-2: Policies
            "ESRS E1-2.17",
            "ESRS E1-2.18",
            "ESRS E1-2.19(a)",
            "ESRS E1-2.19(b)",
            "ESRS E1-2.19(c)",
            "ESRS E1-2.20",
            "ESRS E1-2.22",
            "ESRS E1-2.23",
            "ESRS E1-2.24",
            # E1-3: Actions and resources
            "ESRS E1-3.25",
            "ESRS E1-3.26",
            "ESRS E1-3.28",
            "ESRS E1-3.29",
            "ESRS E1-3.30",
            "ESRS E1-3.32",
            # E1-4: Targets
            "ESRS E1-4.33",
            "ESRS E1-4.34(a)",
            "ESRS E1-4.34(b)",
            "ESRS E1-4.34(c)",
            "ESRS E1-4.35",
            "ESRS E1-4.36",
            "ESRS E1-4.37",
            "ESRS E1-4.38",
            "ESRS E1-4.39",
            "ESRS E1-4.40",
            # E1-5: Energy consumption and mix
            "ESRS E1-5.41",
            "ESRS E1-5.42",
            "ESRS E1-5.43",
            "ESRS E1-5.44",
            "ESRS E1-5.45",
            "ESRS E1-5.46",
            "ESRS E1-5.47",
            "ESRS E1-5.48",
        ],
        order=2,
    )


def build_e1_5_content_block(
    company_name: str,
    reporting_year: int,
    context: Optional[Dict[str, str]] = None,
    block_id: str = "e1-5-energy-consumption",
) -> 'ContentBlock':
    """
    Create a standalone ContentBlock for ESRS E1-5 — Energy consumption and mix.

    Args:
        company_name: Name of the undertaking
        reporting_year: Reporting year
        context: Company context data for placeholder resolution
        block_id: Block ID for the content block

    Returns:
        ContentBlock of type 'narrative' with the E1-5 data tables and narrative
    """
    # Late import to avoid circular dependencies
    from template_engine import ContentBlock

    html = build_e1_5_energy_consumption_and_mix(
        company_name=company_name,
        reporting_year=reporting_year,
        context=context,
    )

    return ContentBlock(
        block_id=block_id,
        standard_ref="ESRS E1",
        paragraph_ref="41-48",
        title="E1-5 — Energy Consumption and Mix",
        content_html=html,
        content_type="narrative",
        datapoint_refs=[
            "ESRS E1-5.41",
            "ESRS E1-5.42",
            "ESRS E1-5.43",
            "ESRS E1-5.44",
            "ESRS E1-5.45",
            "ESRS E1-5.46",
            "ESRS E1-5.47",
            "ESRS E1-5.48",
        ],
        order=3,
    )