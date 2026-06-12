'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { companyContext } from '@/lib/api'
import type { CompanyContextSettings as ContextSettings } from '@/types'
import {
  Save, Loader2, Building2, Cloud, Truck, Users,
  CreditCard, Shield, Plus, X, ChevronDown, ChevronUp, Sparkles,
} from 'lucide-react'

type SectionKey = 'company_profile' | 'ghg_emissions' | 'supply_chain' | 'workforce_kpis' | 'payment_practices' | 'governance'

const FILLED_CLS = 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800'
const EMPTY_CLS = 'bg-muted/30 border-border'

function FieldInput({
  label, value, onChange, placeholder, type = 'text',
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
  type?: string
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium text-foreground/80">{label}</label>
      <Input
        type={type}
        placeholder={placeholder || label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={value ? FILLED_CLS : EMPTY_CLS}
      />
    </div>
  )
}

function StringArrayInput({
  label, value, onChange, placeholder,
}: {
  label: string
  value: string[]
  onChange: (v: string[]) => void
  placeholder?: string
}) {
  const [input, setInput] = useState('')

  const add = () => {
    if (input.trim() && !value.includes(input.trim())) {
      onChange([...value, input.trim()])
      setInput('')
    }
  }

  const remove = (idx: number) => {
    onChange(value.filter((_, i) => i !== idx))
  }

  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium text-foreground/80">{label}</label>
      <div className="flex gap-1">
        <Input
          placeholder={placeholder || 'Add value…'}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); add() } }}
          className="flex-1"
        />
        <Button variant="outline" size="sm" onClick={add} type="button">
          <Plus className="h-3.5 w-3.5" />
        </Button>
      </div>
      {value.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {value.map((item, i) => (
            <Badge key={i} variant="secondary" className="gap-1 text-xs">
              {item}
              <button onClick={() => remove(i)} className="hover:text-destructive transition-colors">
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}

function SectionCard({
  sectionKey, label, icon: Icon, isExpanded, onToggle, filled, total, children,
}: {
  sectionKey: SectionKey
  label: string
  icon: any
  isExpanded: boolean
  onToggle: () => void
  filled: number
  total: number
  children: React.ReactNode
}) {
  return (
    <Card className="border-border">
      <CardHeader
        className="cursor-pointer select-none flex flex-row items-center justify-between py-3 px-4"
        onClick={onToggle}
      >
        <div className="flex items-center gap-2">
          <Icon className="h-5 w-5 text-muted-foreground" />
          <CardTitle className="text-base font-semibold">{label}</CardTitle>
          <Badge variant="outline" className="text-xs font-normal">
            {filled}/{total} filled
          </Badge>
          {filled === total && (
            <Badge variant="secondary" className="text-xs bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
              Complete
            </Badge>
          )}
        </div>
        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onToggle() }}>
          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </Button>
      </CardHeader>
      {isExpanded && (
        <CardContent className="px-4 pb-4 pt-0 space-y-4">
          {children}
        </CardContent>
      )}
    </Card>
  )
}

const defaultData: ContextSettings = {
  id: '',
  company_id: '',
}

export default function CompanyContextSettingsForm({
  refreshKey = 0,
}: {
  refreshKey?: number
}) {
  const [data, setData] = useState<ContextSettings>({ ...defaultData })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [autoFillLoading, setAutoFillLoading] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [expanded, setExpanded] = useState<Record<SectionKey, boolean>>({
    company_profile: true,
    ghg_emissions: false,
    supply_chain: false,
    workforce_kpis: false,
    payment_practices: false,
    governance: false,
  })

  useEffect(() => { loadData() }, [refreshKey])

  const loadData = async () => {
    try {
      const result = await companyContext.get()
      setData(result)
    } catch {
      setData({ ...defaultData })
    } finally {
      setLoading(false)
    }
  }

  const getField = (key: keyof ContextSettings): string => {
    const v = data?.[key]
    if (v === undefined || v === null) return ''
    if (typeof v === 'object') return v as any
    return String(v)
  }

  const setField = (key: keyof ContextSettings, value: string) => {
    setData((prev) => ({ ...prev, [key]: value }))
  }

  const getNum = (key: keyof ContextSettings): number | undefined => {
    const v = data?.[key]
    if (v === undefined || v === null || v === '') return undefined
    if (typeof v === 'number') return v
    const n = Number(v)
    return isNaN(n) ? undefined : n
  }

  const getArr = (key: keyof ContextSettings): string[] => {
    const v = data?.[key]
    return Array.isArray(v) ? v : []
  }

  const setArr = (key: keyof ContextSettings, arr: string[]) => {
    setData((prev) => ({ ...prev, [key]: arr }))
  }

  const toggleSection = (s: SectionKey) => {
    setExpanded((prev) => ({ ...prev, [s]: !prev[s] }))
  }

  const countFilled = (fields: (keyof ContextSettings)[]): number => {
    return fields.filter((f) => {
      const v = data?.[f]
      if (v === undefined || v === null || v === '') return false
      if (Array.isArray(v)) return v.length > 0
      return true
    }).length
  }

  const handleAutoFill = async () => {
    setAutoFillLoading(true)
    setMessage(null)
    try {
      const result = await companyContext.autoFill({
        fill_emissions: true,
        overwrite: true,
      })
      await loadData()
      setMessage({
        type: 'success',
        text: result.message || 'Profilo demo compilato. I valori sostituiranno i placeholder nei report.',
      })
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Auto-fill failed' })
    } finally {
      setAutoFillLoading(false)
    }
  }

  const handleSave = async () => {
    if (!data) return
    setSaving(true)
    setMessage(null)
    try {
      const payload: Record<string, any> = {}
      const cats: SectionKey[] = ['company_profile', 'ghg_emissions', 'supply_chain', 'workforce_kpis', 'payment_practices', 'governance']
      const fieldMap: Record<SectionKey, (keyof ContextSettings)[]> = {
        company_profile: ['company_name', 'country', 'sector', 'reporting_year', 'employee_count_total', 'employee_count_permanent', 'employee_count_temporary', 'employee_count_male', 'employee_count_female', 'employee_count_other', 'employee_count_by_geography', 'annual_revenue_eur', 'operational_sites_count'],
        ghg_emissions: ['scope1_emissions', 'scope2_location_based', 'scope2_market_based', 'scope3_total', 'scope3_material_categories', 'emissions_baseline_year', 'emissions_methodology'],
        supply_chain: ['tier1_suppliers_count', 'tier2_suppliers_count', 'value_chain_countries', 'high_risk_countries', 'suppliers_code_of_conduct_pct', 'supplier_audits_last_year'],
        workforce_kpis: ['ltifr', 'fatal_accidents', 'voluntary_turnover_pct', 'avg_training_hours_per_year', 'women_in_management_pct', 'gender_pay_gap_pct', 'union_coverage_pct', 'employee_engagement_score'],
        payment_practices: ['standard_payment_terms_days', 'avg_actual_payment_time_days', 'invoices_paid_within_terms_pct', 'invoices_paid_late_pct'],
        governance: ['anti_corruption_training_pct', 'corruption_incidents_last_year', 'whistleblowing_reports_received'],
      }

      for (const cat of cats) {
        const section: Record<string, any> = {}
        for (const field of fieldMap[cat]) {
          const v = data?.[field]
          if (v !== undefined && v !== null && v !== '') {
            section[field] = v
          }
        }
        if (Object.keys(section).length) payload[cat] = section
      }

      if (data.id) {
        await companyContext.patch(payload)
      } else {
        await companyContext.update(payload)
      }

      setMessage({ type: 'success', text: 'Company context saved! Values will replace [TO BE CONFIRMED] in reports.' })
      await loadData()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Save failed' })
    } finally {
      setSaving(false)
    }
  }

  const profileFields: (keyof ContextSettings)[] = ['company_name', 'country', 'sector', 'reporting_year', 'employee_count_total', 'employee_count_permanent', 'employee_count_temporary', 'employee_count_male', 'employee_count_female', 'employee_count_other', 'annual_revenue_eur', 'operational_sites_count']
  const ghgFields: (keyof ContextSettings)[] = ['scope1_emissions', 'scope2_location_based', 'scope2_market_based', 'scope3_total', 'scope3_material_categories', 'emissions_baseline_year', 'emissions_methodology']
  const supplyFields: (keyof ContextSettings)[] = ['tier1_suppliers_count', 'tier2_suppliers_count', 'value_chain_countries', 'high_risk_countries', 'suppliers_code_of_conduct_pct', 'supplier_audits_last_year']
  const workforceFields: (keyof ContextSettings)[] = ['ltifr', 'fatal_accidents', 'voluntary_turnover_pct', 'avg_training_hours_per_year', 'women_in_management_pct', 'gender_pay_gap_pct', 'union_coverage_pct', 'employee_engagement_score']
  const paymentFields: (keyof ContextSettings)[] = ['standard_payment_terms_days', 'avg_actual_payment_time_days', 'invoices_paid_within_terms_pct', 'invoices_paid_late_pct']
  const govFields: (keyof ContextSettings)[] = ['anti_corruption_training_pct', 'corruption_incidents_last_year', 'whistleblowing_reports_received']

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Company Context</h2>
          <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
            This data is automatically injected into every report generation prompt.
            Filled values replace <code className="text-xs bg-muted px-1 py-0.5 rounded">[TO BE CONFIRMED]</code> placeholders.
            Empty fields leave the placeholder visible so you know what data is still missing.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleAutoFill}
            disabled={autoFillLoading || saving}
            size="default"
          >
            {autoFillLoading ? (
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4 mr-1" />
            )}
            {autoFillLoading ? 'Compilazione…' : 'Compila profilo demo'}
          </Button>
          <Button onClick={handleSave} disabled={saving || autoFillLoading} size="default">
            {saving ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Save className="h-4 w-4 mr-1" />}
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </div>
      </div>

      {message && (
        <div className={`text-sm px-3 py-2 rounded-md ${
          message.type === 'success'
            ? 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-400'
            : 'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-400'
        }`}>
          {message.text}
        </div>
      )}

      {/* ── Company Profile ──────────────────────────── */}
      <SectionCard
        sectionKey="company_profile" label="Company Profile" icon={Building2}
        isExpanded={expanded.company_profile} onToggle={() => toggleSection('company_profile')}
        filled={countFilled(profileFields)} total={profileFields.length}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <FieldInput label="Company name" value={getField('company_name')} onChange={(v) => setField('company_name', v)} placeholder="e.g. ACME GmbH" />
          <FieldInput label="Country / Headquarters" value={getField('country')} onChange={(v) => setField('country', v)} placeholder="e.g. Germany" />
          <FieldInput label="Sector / Industry" value={getField('sector')} onChange={(v) => setField('sector', v)} placeholder="e.g. Manufacturing" />
          <FieldInput label="Reporting year" value={getField('reporting_year')} onChange={(v) => setField('reporting_year', v)} placeholder="e.g. 2026" type="number" />
          <FieldInput label="Total employees" value={getField('employee_count_total')} onChange={(v) => setField('employee_count_total', v)} placeholder="e.g. 500" type="number" />
          <FieldInput label="Permanent employees" value={getField('employee_count_permanent')} onChange={(v) => setField('employee_count_permanent', v)} placeholder="e.g. 450" type="number" />
          <FieldInput label="Temporary employees" value={getField('employee_count_temporary')} onChange={(v) => setField('employee_count_temporary', v)} placeholder="e.g. 50" type="number" />
          <FieldInput label="Male employees" value={getField('employee_count_male')} onChange={(v) => setField('employee_count_male', v)} placeholder="e.g. 300" type="number" />
          <FieldInput label="Female employees" value={getField('employee_count_female')} onChange={(v) => setField('employee_count_female', v)} placeholder="e.g. 190" type="number" />
          <FieldInput label="Other employees" value={getField('employee_count_other')} onChange={(v) => setField('employee_count_other', v)} placeholder="e.g. 10" type="number" />
          <FieldInput label="Annual revenue (EUR)" value={getField('annual_revenue_eur')} onChange={(v) => setField('annual_revenue_eur', v)} placeholder="e.g. 50000000" type="number" />
          <FieldInput label="Operational sites" value={getField('operational_sites_count')} onChange={(v) => setField('operational_sites_count', v)} placeholder="e.g. 3" type="number" />
        </div>
      </SectionCard>

      {/* ── GHG Emissions ────────────────────────────── */}
      <SectionCard
        sectionKey="ghg_emissions" label="GHG Emissions" icon={Cloud}
        isExpanded={expanded.ghg_emissions} onToggle={() => toggleSection('ghg_emissions')}
        filled={countFilled(ghgFields)} total={ghgFields.length}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <FieldInput label="Scope 1 (tCO₂e)" value={getField('scope1_emissions')} onChange={(v) => setField('scope1_emissions', v)} placeholder="e.g. 12500" type="number" />
          <FieldInput label="Scope 2 location-based (tCO₂e)" value={getField('scope2_location_based')} onChange={(v) => setField('scope2_location_based', v)} placeholder="e.g. 3200" type="number" />
          <FieldInput label="Scope 2 market-based (tCO₂e)" value={getField('scope2_market_based')} onChange={(v) => setField('scope2_market_based', v)} placeholder="e.g. 2800" type="number" />
          <FieldInput label="Scope 3 total (tCO₂e)" value={getField('scope3_total')} onChange={(v) => setField('scope3_total', v)} placeholder="e.g. 85000" type="number" />
          <FieldInput label="Baseline year" value={getField('emissions_baseline_year')} onChange={(v) => setField('emissions_baseline_year', v)} placeholder="e.g. 2025" type="number" />
          <FieldInput label="Methodology" value={getField('emissions_methodology')} onChange={(v) => setField('emissions_methodology', v)} placeholder="e.g. GHG Protocol" />
        </div>
        <StringArrayInput label="Scope 3 material categories" value={getArr('scope3_material_categories')} onChange={(v) => setArr('scope3_material_categories', v)} placeholder="Add category (e.g. Purchased goods)" />
      </SectionCard>

      {/* ── Supply Chain ─────────────────────────────── */}
      <SectionCard
        sectionKey="supply_chain" label="Supply Chain" icon={Truck}
        isExpanded={expanded.supply_chain} onToggle={() => toggleSection('supply_chain')}
        filled={countFilled(supplyFields)} total={supplyFields.length}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <FieldInput label="Tier 1 suppliers" value={getField('tier1_suppliers_count')} onChange={(v) => setField('tier1_suppliers_count', v)} placeholder="e.g. 120" type="number" />
          <FieldInput label="Tier 2 suppliers (est.)" value={getField('tier2_suppliers_count')} onChange={(v) => setField('tier2_suppliers_count', v)} placeholder="e.g. 500" type="number" />
          <FieldInput label="% suppliers with CoC" value={getField('suppliers_code_of_conduct_pct')} onChange={(v) => setField('suppliers_code_of_conduct_pct', v)} placeholder="e.g. 85" type="number" />
          <FieldInput label="Supplier audits last year" value={getField('supplier_audits_last_year')} onChange={(v) => setField('supplier_audits_last_year', v)} placeholder="e.g. 15" type="number" />
        </div>
        <StringArrayInput label="Value chain countries" value={getArr('value_chain_countries')} onChange={(v) => setArr('value_chain_countries', v)} placeholder="Add country…" />
        <StringArrayInput label="High-risk countries" value={getArr('high_risk_countries')} onChange={(v) => setArr('high_risk_countries', v)} placeholder="Add country…" />
      </SectionCard>

      {/* ── Workforce KPIs ───────────────────────────── */}
      <SectionCard
        sectionKey="workforce_kpis" label="Workforce KPIs" icon={Users}
        isExpanded={expanded.workforce_kpis} onToggle={() => toggleSection('workforce_kpis')}
        filled={countFilled(workforceFields)} total={workforceFields.length}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <FieldInput label="LTIFR" value={getField('ltifr')} onChange={(v) => setField('ltifr', v)} placeholder="e.g. 2.5" type="number" />
          <FieldInput label="Fatal accidents" value={getField('fatal_accidents')} onChange={(v) => setField('fatal_accidents', v)} placeholder="e.g. 0" type="number" />
          <FieldInput label="Voluntary turnover (%)" value={getField('voluntary_turnover_pct')} onChange={(v) => setField('voluntary_turnover_pct', v)} placeholder="e.g. 12" type="number" />
          <FieldInput label="Avg training hours/year" value={getField('avg_training_hours_per_year')} onChange={(v) => setField('avg_training_hours_per_year', v)} placeholder="e.g. 24" type="number" />
          <FieldInput label="% women in management" value={getField('women_in_management_pct')} onChange={(v) => setField('women_in_management_pct', v)} placeholder="e.g. 35" type="number" />
          <FieldInput label="Gender pay gap (%)" value={getField('gender_pay_gap_pct')} onChange={(v) => setField('gender_pay_gap_pct', v)} placeholder="e.g. 8.5" type="number" />
          <FieldInput label="Union coverage (%)" value={getField('union_coverage_pct')} onChange={(v) => setField('union_coverage_pct', v)} placeholder="e.g. 45" type="number" />
          <FieldInput label="eNPS / Engagement score" value={getField('employee_engagement_score')} onChange={(v) => setField('employee_engagement_score', v)} placeholder="e.g. 72" type="number" />
        </div>
      </SectionCard>

      {/* ── Payment Practices ────────────────────────── */}
      <SectionCard
        sectionKey="payment_practices" label="Payment Practices" icon={CreditCard}
        isExpanded={expanded.payment_practices} onToggle={() => toggleSection('payment_practices')}
        filled={countFilled(paymentFields)} total={paymentFields.length}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <FieldInput label="Standard payment terms (days)" value={getField('standard_payment_terms_days')} onChange={(v) => setField('standard_payment_terms_days', v)} placeholder="e.g. 30" type="number" />
          <FieldInput label="Avg actual payment time (days)" value={getField('avg_actual_payment_time_days')} onChange={(v) => setField('avg_actual_payment_time_days', v)} placeholder="e.g. 42" type="number" />
          <FieldInput label="% invoices paid within terms" value={getField('invoices_paid_within_terms_pct')} onChange={(v) => setField('invoices_paid_within_terms_pct', v)} placeholder="e.g. 78" type="number" />
          <FieldInput label="% invoices paid late" value={getField('invoices_paid_late_pct')} onChange={(v) => setField('invoices_paid_late_pct', v)} placeholder="e.g. 12" type="number" />
        </div>
      </SectionCard>

      {/* ── Governance ───────────────────────────────── */}
      <SectionCard
        sectionKey="governance" label="Governance" icon={Shield}
        isExpanded={expanded.governance} onToggle={() => toggleSection('governance')}
        filled={countFilled(govFields)} total={govFields.length}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <FieldInput label="% anti-corruption training" value={getField('anti_corruption_training_pct')} onChange={(v) => setField('anti_corruption_training_pct', v)} placeholder="e.g. 95" type="number" />
          <FieldInput label="Corruption incidents last year" value={getField('corruption_incidents_last_year')} onChange={(v) => setField('corruption_incidents_last_year', v)} placeholder="e.g. 0" type="number" />
          <FieldInput label="Whistleblowing reports" value={getField('whistleblowing_reports_received')} onChange={(v) => setField('whistleblowing_reports_received', v)} placeholder="e.g. 3" type="number" />
        </div>
      </SectionCard>
    </div>
  )
}
