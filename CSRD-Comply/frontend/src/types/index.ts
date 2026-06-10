// ── Company ────────────────────────────────────────────────────
export interface Company {
  company_id: string
  company_name: string
  vat_number?: string
  country: string
  sector: string
  employee_count?: number
  turnover?: number
  balance_sheet_total?: number
  csrd_wave: number
  reporting_year: number
}

// ── User ───────────────────────────────────────────────────────
export type UserRole = 'admin' | 'contributor' | 'viewer'

export interface User {
  user_id: string
  company_id: string
  email: string
  role: UserRole
  is_active: boolean
}

// ── Assessment ─────────────────────────────────────────────────
export type AssessmentStatus = 'draft' | 'in_progress' | 'completed' | 'audited'

export interface MaterialityAssessment {
  id: string
  company_id: string
  assessment_date: string
  status: AssessmentStatus
  methodology_version?: string
}

// ── Emissions ──────────────────────────────────────────────────
export interface EmissionsData {
  id: string
  company_id: string
  reporting_year: number
  scope: '1' | '2' | '3'
  category?: string
  value: number
  unit: string
  calculation_method?: string
  emission_factor_source?: string
  verified: boolean
}

// ── Report ─────────────────────────────────────────────────────
export type ReportStatus = 'draft' | 'review' | 'final' | 'filed'

export interface Report {
  id: string
  company_id: string
  reporting_year: number
  title: string
  status: ReportStatus
  xbrl_validation_passed?: boolean
  filed_at?: string
  filed_to?: string
}

// ── Company Context Settings ────────────────────────────────────
export interface CompanyContextSettings {
  id: string
  company_id: string

  // Company Profile
  company_name?: string
  country?: string
  sector?: string
  reporting_year?: number
  employee_count_total?: number
  employee_count_permanent?: number
  employee_count_temporary?: number
  employee_count_male?: number
  employee_count_female?: number
  employee_count_other?: number
  employee_count_by_geography?: Record<string, number>
  annual_revenue_eur?: number
  operational_sites_count?: number

  // GHG Emissions
  scope1_emissions?: number
  scope2_location_based?: number
  scope2_market_based?: number
  scope3_total?: number
  scope3_material_categories?: string[]
  emissions_baseline_year?: number
  emissions_methodology?: string

  // Supply Chain
  tier1_suppliers_count?: number
  tier2_suppliers_count?: number
  value_chain_countries?: string[]
  high_risk_countries?: string[]
  suppliers_code_of_conduct_pct?: number
  supplier_audits_last_year?: number

  // Workforce KPIs
  ltifr?: number
  fatal_accidents?: number
  voluntary_turnover_pct?: number
  avg_training_hours_per_year?: number
  women_in_management_pct?: number
  gender_pay_gap_pct?: number
  union_coverage_pct?: number
  employee_engagement_score?: number

  // Payment Practices
  standard_payment_terms_days?: number
  avg_actual_payment_time_days?: number
  invoices_paid_within_terms_pct?: number
  invoices_paid_late_pct?: number

  // Governance
  anti_corruption_training_pct?: number
  corruption_incidents_last_year?: number
  whistleblowing_reports_received?: number
}

// ── Context Questionnaire (Step 8) ────────────────────────────
export interface QuestionnaireQuestion {
  id: string
  question: string
  options: string[]
  esrs_topics: string[]
  phase: number
}

export interface QuestionnairePhase {
  id: number
  name: string
  description: string
  questions: QuestionnaireQuestion[]
  type: 'universal' | 'sector_specific' | 'value_chain'
}

export interface QuestionnaireData {
  phases: QuestionnairePhase[]
  sector: string
  sector_name: string
  ai_generated_questions: string[]
}

export interface CompanyContext {
  value_chain_description?: string
  key_activities?: string[]
  business_relationships?: Record<string, any>
  geographical_scope?: string[]
  stakeholder_groups?: string[]
}

// ── Company Context Settings (Report Data Injection) ────────────
export interface CompanyContextSettings {
  id: string
  company_id: string

  // Company Profile
  company_name?: string
  country?: string
  sector?: string
  reporting_year?: number
  employee_count_total?: number
  employee_count_permanent?: number
  employee_count_temporary?: number
  employee_count_male?: number
  employee_count_female?: number
  employee_count_other?: number
  employee_count_by_geography?: Record<string, number>
  annual_revenue_eur?: number
  operational_sites_count?: number

  // GHG Emissions
  scope1_emissions?: number
  scope2_location_based?: number
  scope2_market_based?: number
  scope3_total?: number
  scope3_material_categories?: string[]
  emissions_baseline_year?: number
  emissions_methodology?: string

  // Supply Chain
  tier1_suppliers_count?: number
  tier2_suppliers_count?: number
  value_chain_countries?: string[]
  high_risk_countries?: string[]
  suppliers_code_of_conduct_pct?: number
  supplier_audits_last_year?: number

  // Workforce KPIs
  ltifr?: number
  fatal_accidents?: number
  voluntary_turnover_pct?: number
  avg_training_hours_per_year?: number
  women_in_management_pct?: number
  gender_pay_gap_pct?: number
  union_coverage_pct?: number
  employee_engagement_score?: number

  // Payment Practices
  standard_payment_terms_days?: number
  avg_actual_payment_time_days?: number
  invoices_paid_within_terms_pct?: number
  invoices_paid_late_pct?: number

  // Governance
  anti_corruption_training_pct?: number
  corruption_incidents_last_year?: number
  whistleblowing_reports_received?: number
}

// ── IRO Generator (Step 9) ───────────────────────────────────
export type IroType = 'impact' | 'risk' | 'opportunity'
export type IroSeverity = 'low' | 'medium' | 'high'

export interface IRO {
  id: string
  type: IroType
  topic: string
  name: string
  description: string
  default_impact_scale: number
  default_financial_magnitude: number
  severity: IroSeverity
  sector_applicable?: boolean
  ai_generated?: boolean
  generation_method?: string
  initial_impact_score?: number
  initial_financial_score?: number
  is_material?: boolean
  benchmark_source?: string
}

export interface IroSummary {
  total_iros: number
  by_type: Record<string, number>
  by_topic: Record<string, number>
  material_count: number
  ai_generated: number
  benchmark_sourced: number
}



export interface SectorBenchmark {

  name: string
  carbon_intensity: string
  water_intensity: string
  waste_intensity: string
  social_risk: string
  governance_risk: string
  typical_impact_range: [number, number]
  typical_financial_range: [number, number]
}
