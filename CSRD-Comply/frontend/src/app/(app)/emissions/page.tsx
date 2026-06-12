'use client'

import { useState, useEffect, useCallback } from 'react'
import { Button, Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui'
import { Badge } from '@/components/ui'
import { Input } from '@/components/ui'
import { Select } from '@/components/ui'
import { Leaf, Plus, Calculator, AlertTriangle, CheckCircle2, BarChart3, Upload, FileText, Database, Truck, Building, ShoppingBag, Users, Plane, Trash2, Settings, Briefcase, TrendingUp, PieChart, Zap, Sparkles, Loader2 } from 'lucide-react'
import { emissions as emissionsApi } from '@/lib/api'

// ── Types ───────────────────────────────────────────────────────

interface Scope1Result {
  scope: string
  total_tco2e: number
  categories: any[]
  method: string
}

interface StationaryCombustionInput {
  natural_gas_kwh: string
  natural_gas_m3: string
  diesel_heating_litres: string
  lpg_kwh: string
  lpg_litres: string
  biomass_kwh: string
}

interface MobileCombustionInput {
  diesel_km: string
  petrol_km: string
  diesel_van_km: string
  diesel_truck_km: string
  electric_km: string
}

interface FugitiveInput {
  r410a_kg: string
  r134a_kg: string
  r32_kg: string
  r290_kg: string
}

interface ProcessEmissionsInput {
  cement_tonnes: string
  steel_tonnes_bf_bof: string
  steel_tonnes_eaf: string
  ammonia_tonnes: string
  ethylene_tonnes: string
  methanol_tonnes: string
  aluminium_tonnes: string
  glass_tonnes: string
  paper_tonnes: string
  food_tonnes: string
  refrigerant_leak_kg: string
}

interface Scope2Input {
  electricity_kwh: string
  country: string
  has_green_tariff: boolean
}

// ── Country Options ─────────────────────────────────────────────

const COUNTRIES = [
  { code: "EU_avg", name: "EU Average" },
  { code: "IT", name: "Italy" },
  { code: "DE", name: "Germany" },
  { code: "FR", name: "France" },
  { code: "ES", name: "Spain" },
  { code: "UK", name: "United Kingdom" },
  { code: "NL", name: "Netherlands" },
  { code: "BE", name: "Belgium" },
  { code: "AT", name: "Austria" },
  { code: "PT", name: "Portugal" },
  { code: "PL", name: "Poland" },
  { code: "SE", name: "Sweden" },
  { code: "DK", name: "Denmark" },
  { code: "FI", name: "Finland" },
  { code: "IE", name: "Ireland" },
  { code: "GR", name: "Greece" },
  { code: "RO", name: "Romania" },
  { code: "CZ", name: "Czech Republic" },
  { code: "HU", name: "Hungary" },
]

// ── NACE Code options ──────────────────────────────────────────
const NACE_CODES = [
  { code: "DEFAULT", name: "Generic / Default" },
  { code: "C10", name: "Food products" },
  { code: "C20", name: "Chemicals" },
  { code: "C26", name: "Computer/Electronic" },
  { code: "C24", name: "Basic metals" },
  { code: "J62", name: "IT services" },
  { code: "M69", name: "Legal/Accounting" },
  { code: "G46", name: "Wholesale trade" },
  { code: "H49", name: "Land transport" },
  { code: "F41", name: "Construction" },
  { code: "A01", name: "Agriculture" },
]

const TRAVEL_MODES = [
  { code: "car_diesel", name: "Auto Diesel" },
  { code: "car_petrol", name: "Auto Benzina" },
  { code: "train", name: "Treno" },
  { code: "bus", name: "Bus" },
  { code: "flight_short_haul", name: "Volo Corto Raggio" },
  { code: "flight_medium_haul", name: "Volo Medio Raggio" },
  { code: "flight_long_haul", name: "Volo Lungo Raggio" },
]

const COMMUTING_MODES = [
  { code: "car_alone", name: "Auto (da solo)" },
  { code: "car_carpool", name: "Auto (car pooling)" },
  { code: "public_transport", name: "Mezzi pubblici" },
  { code: "train", name: "Treno" },
  { code: "bus", name: "Bus" },
  { code: "bike", name: "Bicicletta" },
  { code: "walking", name: "A piedi" },
]

const WASTE_TYPES = [
  { code: "mixed_waste", name: "Rifiuti misti" },
  { code: "paper_cardboard", name: "Carta/Cartone" },
  { code: "plastic", name: "Plastica" },
  { code: "glass", name: "Vetro" },
  { code: "metal", name: "Metallo" },
  { code: "organic", name: "Organico" },
  { code: "hazardous", name: "Rifiuti pericolosi" },
]

const DISPOSAL_METHODS = [
  { code: "landfill", name: "Discarica" },
  { code: "incineration", name: "Incinetimento" },
  { code: "recycling", name: "Riciclo" },
  { code: "composting", name: "Compostaggio" },
]

// ── Initial State ───────────────────────────────────────────────

const INITIAL_STATIONARY: StationaryCombustionInput = {
  natural_gas_kwh: '', natural_gas_m3: '', diesel_heating_litres: '',
  lpg_kwh: '', lpg_litres: '', biomass_kwh: '',
}

const INITIAL_MOBILE: MobileCombustionInput = {
  diesel_km: '', petrol_km: '', diesel_van_km: '', diesel_truck_km: '', electric_km: '',
}

const INITIAL_FUGITIVE: FugitiveInput = {
  r410a_kg: '', r134a_kg: '', r32_kg: '', r290_kg: '',
}

const INITIAL_PROCESS: ProcessEmissionsInput = {
  cement_tonnes: '', steel_tonnes_bf_bof: '', steel_tonnes_eaf: '',
  ammonia_tonnes: '', ethylene_tonnes: '', methanol_tonnes: '',
  aluminium_tonnes: '', glass_tonnes: '', paper_tonnes: '',
  food_tonnes: '', refrigerant_leak_kg: '',
}

// ── Number Input Component ─────────────────────────────────────

function NumberInput({ label, unit, value, onChange, disabled = false, placeholder = '0' }: {
  label: string
  unit?: string
  value: string
  onChange: (val: string) => void
  disabled?: boolean
  placeholder?: string
}) {
  return (
    <div className="p-3 bg-muted rounded-lg">
      <label className="text-sm font-medium text-foreground block mb-1">{label}</label>
      <div className="flex items-center gap-2">
        <input
          type="number"
          className="flex-1 px-3 py-1.5 text-sm border border-input rounded-md bg-background"
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          min="0"
          step="0.01"
        />
        {unit && <span className="text-xs text-muted-foreground w-12">{unit}</span>}
      </div>
    </div>
  )
}

function SelectInput({ label, value, onChange, options }: {
  label: string
  value: string
  onChange: (val: string) => void
  options: { code: string; name: string }[]
}) {
  return (
    <div className="p-3 bg-muted rounded-lg">
      <label className="text-sm font-medium text-foreground block mb-1">{label}</label>
      <select
        className="w-full px-3 py-1.5 text-sm border border-input rounded-md bg-background"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((opt) => (
          <option key={opt.code} value={opt.code}>{opt.name}</option>
        ))}
      </select>
    </div>
  )
}

function TextInput({ label, value, onChange, placeholder = '' }: {
  label: string
  value: string
  onChange: (val: string) => void
  placeholder?: string
}) {
  return (
    <div className="p-3 bg-muted rounded-lg">
      <label className="text-sm font-medium text-foreground block mb-1">{label}</label>
      <textarea
        className="w-full px-3 py-1.5 text-sm border border-input rounded-md bg-background"
        rows={3}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  )
}

// ── Result Display ──────────────────────────────────────────────

function ResultCard({ result }: { result: any }) {
  if (!result) return null

  const total = result.total_tco2e ?? 0
  const categories = result.categories ?? (result.location_based ? [] : [result])

  return (
    <Card className="border-green-200 dark:border-green-600">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2 text-green-700 dark:text-green-300">
          <CheckCircle2 className="h-4 w-4" />
          Risultato Calcolo
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold text-green-600 dark:text-green-300">
          {total.toFixed(4)} <span className="text-sm font-normal">tCO₂e</span>
        </div>

        {/* Scope 3 breakdown */}
        {result.scope === '3' && (
          <div className="mt-3 space-y-2 text-sm">
            {result.upstream_total !== undefined && (
              <div className="flex justify-between">
                <span>Upstream (Cat.1-8):</span>
                <span className="font-semibold">{result.upstream_total} tCO₂e</span>
              </div>
            )}
            {result.downstream_total !== undefined && (
              <div className="flex justify-between">
                <span>Downstream (Cat.9-15):</span>
                <span className="font-semibold">{result.downstream_total} tCO₂e</span>
              </div>
            )}
            <div className="text-xs text-muted-foreground mt-1">
              Metodologia: {result.methodology || result.method || 'GHG Protocol Scope 3'}
            </div>
          </div>
        )}

        {/* Dual reporting for Scope 2 */}
        {result.location_based && (
          <div className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between">
              <span>Location-based:</span>
              <span className="font-semibold">{result.location_based.total_tco2e} tCO₂e</span>
            </div>
            <div className="flex justify-between">
              <span>Market-based:</span>
              <span className="font-semibold">
                {result.market_based?.has_green_tariff && result.market_based?.total_tco2e === 0
                  ? "0.0 (coperto da GO/I-REC)"
                  : `${result.market_based?.total_tco2e} tCO₂e`}
              </span>
            </div>
            {result.difference_tco2e > 0 && (
              <div className="flex justify-between text-muted-foreground">
                <span>Differenza:</span>
                <span>{result.difference_tco2e} tCO₂e</span>
              </div>
            )}
            <div className="flex justify-between text-muted-foreground">
              <span>Fattore emissione:</span>
              <span>{result.location_based.emission_factor_kgco2e_per_kwh} kgCO₂e/kWh</span>
            </div>
            {result.market_based?.has_green_tariff && (
              <div className="mt-2 space-y-1">
                <Badge variant="outline" className="text-green-600 border-green-300">
                  Tariffa Verde Certificata
                </Badge>
                <p className="text-xs text-green-600 dark:text-green-400">
                  ⚡ Emissioni market-based pari a zero perché coperte da Garanzie d'Origine (GO/I-REC).
                  ESRS E1-6 richiede dual reporting: il valore 0 è corretto per contratti certificati.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Breakdown for Scope 1 */}
        {categories.length > 0 && !result.location_based && result.scope !== '3' && (
          <div className="mt-3 space-y-2">
            {categories.map((cat: any, i: number) => (
              <div key={i}>
                <div className="flex justify-between text-sm font-medium">
                  <span className="capitalize">{cat.category?.replace(/_/g, ' ')}</span>
                  <span>{cat.total_tco2e} tCO₂e</span>
                </div>
                {cat.breakdown && (
                  <div className="ml-3 mt-1 space-y-1 text-xs text-muted-foreground">
                    {Object.entries(cat.breakdown).map(([key, val]: any) => (
                      <div key={key} className="flex justify-between">
                        <span>{key.replace(/_/g, ' ')}: {val.value} {val.unit}</span>
                        <span>{val.kgCO2e ? `${(val.kgCO2e / 1000).toFixed(4)} tCO₂e` : `${val.tCO2e} tCO₂e`}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Scope 3 categories breakdown */}
        {result.scope === '3' && categories.length > 0 && (
          <div className="mt-3 space-y-1.5">
            {categories.map((cat: any, i: number) => (
              <div key={i} className="flex justify-between text-xs py-0.5 border-b border-border/50">
                <span>
                  {cat.category > 0 ? `Cat.${cat.category}: ` : ''}
                  {cat.name || cat.category?.replace(/_/g, ' ')}
                </span>
                <span className="font-medium">{cat.total_tco2e} tCO₂e</span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// ── Validation Alert ────────────────────────────────────────────

function ValidationPanel({ result }: { result: any }) {
  if (!result) return null

  return (
    <Card className="border-yellow-200 dark:border-yellow-800">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2 text-yellow-700 dark:text-yellow-400">
          <AlertTriangle className="h-4 w-4" />
          Validazione
        </CardTitle>
      </CardHeader>
      <CardContent className="text-sm">
        <div className="flex items-center gap-2 mb-2">
          <span>Score:</span>
          <span className={`font-bold text-lg ${(result.validation_score ?? 100) >= 80 ? 'text-green-600' : 'text-yellow-600'}`}>
            {result.validation_score ?? 'N/A'}%
          </span>
        </div>
        {result.alerts?.length > 0 && (
          <ul className="space-y-1">
            {result.alerts.map((alert: any, i: number) => (
              <li key={i} className={`text-xs p-1.5 rounded ${
                alert.severity === 'high' ? 'bg-red-50 dark:bg-red-950 text-red-700' :
                alert.severity === 'medium' ? 'bg-yellow-50 dark:bg-yellow-950 text-yellow-700' :
                'bg-blue-50 dark:bg-blue-950 text-blue-700'
              }`}>
                {alert.message}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

  // ── Main Page ───────────────────────────────────────────────────

  export default function EmissionsPage() {
  // Active tab
  const [activeTab, setActiveTab] = useState('overview')
  // Report year
  const [reportYear, setReportYear] = useState(new Date().getFullYear())
  // Baseline 2025
  const [baseline2025, setBaseline2025] = useState({
    scope1: '', scope2: '', scope3: '',
    scope2_market_based: '',
  })

  // Loading & Error
  const [loading, setLoading] = useState(false)
  const [autoFillLoading, setAutoFillLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [autoFillMessage, setAutoFillMessage] = useState<string | null>(null)
  // Summary
  const [summary, setSummary] = useState<any>(null)
  const [savedEmissions, setSavedEmissions] = useState<any[]>([])
  // Scope 1
  const [stationary, setStationary] = useState<StationaryCombustionInput>(INITIAL_STATIONARY)
  const [mobile, setMobile] = useState<MobileCombustionInput>(INITIAL_MOBILE)
  const [fugitive, setFugitive] = useState<FugitiveInput>(INITIAL_FUGITIVE)
  const [process, setProcess] = useState<ProcessEmissionsInput>(INITIAL_PROCESS)
  const [scope1Result, setScope1Result] = useState<any>(null)
  const [scope1ProcessResult, setScope1ProcessResult] = useState<any>(null)
  // Scope 2
  const [scope2Input, setScope2Input] = useState<Scope2Input>({
    electricity_kwh: '', country: 'EU_avg', has_green_tariff: false,
  })
  const [scope2Result, setScope2Result] = useState<any>(null)
  // Scope 3
  const [scope3Upstream, setScope3Upstream] = useState({
    spend_eur: '', supplier_nace: 'DEFAULT',
    capital_goods_eur: '', capital_goods_nace: '',
    electricity_kwh: '', natural_gas_kwh_scope3: '', diesel_litres_scope3: '',
    upstream_tkm: '', upstream_transport_mode: 'truck',
    waste_kg: '', waste_type: 'mixed_waste',
    business_travel_km: '', travel_mode: 'car_diesel',
    employees: '', avg_commute_km: '20', commuting_mode: 'car_alone', working_days: '220',
    leased_area_m2: '', lease_cost_eur: '',
  })
  const [scope3Downstream, setScope3Downstream] = useState({
    downstream_tkm: '', downstream_transport_mode: 'truck',
    distance_to_customer_km: '', product_weight_tonnes: '',
    product_value_eur: '', processing_type: 'default',
    products_sold: '', avg_energy_kwh_per_unit: '', product_type: 'default',
    product_weight_kg: '', disposal_method: 'landfill',
    downstream_leased_area_m2: '', lessees: '',
    num_franchises: '', avg_energy_kwh_per_franchise: '', franchise_revenue_eur: '',
    investment_eur: '', investment_type: 'equity', portfolio_company_revenue_eur: '',
  })
  const [scope3Result, setScope3Result] = useState<any>(null)
  // Data Collection
  const [billText, setBillText] = useState('')
  const [billParseResult, setBillParseResult] = useState<any>(null)

  // ── Load Summary ──────────────────────────────────────────────
  const loadSummary = useCallback(async () => {
    try {
      const data = await emissionsApi.getSummary(reportYear)
      setSummary(data)
    } catch (e) {
      // silent — API might not be running
    }
  }, [reportYear])

  const loadEmissions = useCallback(async () => {
    try {
      const data = await emissionsApi.list({ year: reportYear })
      setSavedEmissions(data)
    } catch (e) {
      // silent
    }
  }, [reportYear])

  useEffect(() => {
    loadSummary()
    loadEmissions()
  }, [loadSummary, loadEmissions])

  // ── Calculate Scope 1 ─────────────────────────────────────────
  const handleCalculateScope1 = async () => {
    setLoading(true)
    setError(null)
    try {
      const payload: any = {}
      // Stationary
      if (stationary.natural_gas_kwh) payload.natural_gas_kwh = parseFloat(stationary.natural_gas_kwh)
      if (stationary.natural_gas_m3) payload.natural_gas_m3 = parseFloat(stationary.natural_gas_m3)
      if (stationary.diesel_heating_litres) payload.diesel_heating_litres = parseFloat(stationary.diesel_heating_litres)
      if (stationary.lpg_kwh) payload.lpg_kwh = parseFloat(stationary.lpg_kwh)
      if (stationary.lpg_litres) payload.lpg_litres = parseFloat(stationary.lpg_litres)
      if (stationary.biomass_kwh) payload.biomass_kwh = parseFloat(stationary.biomass_kwh)
      // Mobile
      if (mobile.diesel_km) payload.diesel_km = parseFloat(mobile.diesel_km)
      if (mobile.petrol_km) payload.petrol_km = parseFloat(mobile.petrol_km)
      if (mobile.diesel_van_km) payload.diesel_van_km = parseFloat(mobile.diesel_van_km)
      if (mobile.diesel_truck_km) payload.diesel_truck_km = parseFloat(mobile.diesel_truck_km)
      if (mobile.electric_km) payload.electric_km = parseFloat(mobile.electric_km)
      // Fugitive
      if (fugitive.r410a_kg) payload.r410a_kg = parseFloat(fugitive.r410a_kg)
      if (fugitive.r134a_kg) payload.r134a_kg = parseFloat(fugitive.r134a_kg)
      if (fugitive.r32_kg) payload.r32_kg = parseFloat(fugitive.r32_kg)
      if (fugitive.r290_kg) payload.r290_kg = parseFloat(fugitive.r290_kg)

      const result = await emissionsApi.calculateScope1(payload)
      setScope1Result(result)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // ── Calculate Process Emissions ───────────────────────────────
  const handleCalculateProcess = async () => {
    setLoading(true)
    setError(null)
    try {
      const payload: any = {}
      Object.entries(process).forEach(([key, val]) => {
        if (val) payload[key] = parseFloat(val)
      })
      const result = await emissionsApi.calculateScope1Process(payload)
      setScope1ProcessResult(result)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // ── Calculate Scope 2 ─────────────────────────────────────────
  const handleCalculateScope2 = async () => {
    if (!scope2Input.electricity_kwh) {
      setError('Inserisci il consumo elettrico annuo')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const result = await emissionsApi.calculateScope2({
        electricity_kwh: parseFloat(scope2Input.electricity_kwh),
        country: scope2Input.country,
        has_green_tariff: scope2Input.has_green_tariff,
      })
      setScope2Result(result)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // ── Calculate Scope 3 ─────────────────────────────────────────
  const handleCalculateScope3 = async () => {
    setLoading(true)
    setError(null)
    try {
      const payload: any = {}
      // Upstream
      if (scope3Upstream.spend_eur) payload.spend_eur = parseFloat(scope3Upstream.spend_eur)
      payload.supplier_nace = scope3Upstream.supplier_nace
      if (scope3Upstream.capital_goods_eur) payload.capital_goods_eur = parseFloat(scope3Upstream.capital_goods_eur)
      if (scope3Upstream.capital_goods_nace) payload.capital_goods_nace = scope3Upstream.capital_goods_nace
      if (scope3Upstream.electricity_kwh) payload.electricity_kwh = parseFloat(scope3Upstream.electricity_kwh)
      if (scope3Upstream.natural_gas_kwh_scope3) payload.natural_gas_kwh_scope3 = parseFloat(scope3Upstream.natural_gas_kwh_scope3)
      if (scope3Upstream.diesel_litres_scope3) payload.diesel_litres_scope3 = parseFloat(scope3Upstream.diesel_litres_scope3)
      if (scope3Upstream.upstream_tkm) payload.upstream_tkm = parseFloat(scope3Upstream.upstream_tkm)
      payload.upstream_transport_mode = scope3Upstream.upstream_transport_mode
      if (scope3Upstream.waste_kg) payload.waste_kg = parseFloat(scope3Upstream.waste_kg)
      payload.waste_type = scope3Upstream.waste_type
      if (scope3Upstream.business_travel_km) payload.business_travel_km = parseFloat(scope3Upstream.business_travel_km)
      payload.travel_mode = scope3Upstream.travel_mode
      if (scope3Upstream.employees) payload.employees = parseInt(scope3Upstream.employees)
      payload.avg_commute_km = parseFloat(scope3Upstream.avg_commute_km) || 20
      payload.commuting_mode = scope3Upstream.commuting_mode
      payload.working_days = parseInt(scope3Upstream.working_days) || 220
      if (scope3Upstream.leased_area_m2) payload.leased_area_m2 = parseFloat(scope3Upstream.leased_area_m2)
      if (scope3Upstream.lease_cost_eur) payload.lease_cost_eur = parseFloat(scope3Upstream.lease_cost_eur)

      // Downstream
      if (scope3Downstream.downstream_tkm) payload.downstream_tkm = parseFloat(scope3Downstream.downstream_tkm)
      payload.downstream_transport_mode = scope3Downstream.downstream_transport_mode
      if (scope3Downstream.distance_to_customer_km) payload.distance_to_customer_km = parseFloat(scope3Downstream.distance_to_customer_km)
      if (scope3Downstream.product_weight_tonnes) payload.product_weight_tonnes = parseFloat(scope3Downstream.product_weight_tonnes)
      if (scope3Downstream.product_value_eur) payload.product_value_eur = parseFloat(scope3Downstream.product_value_eur)
      payload.processing_type = scope3Downstream.processing_type
      if (scope3Downstream.products_sold) payload.products_sold = parseInt(scope3Downstream.products_sold)
      if (scope3Downstream.avg_energy_kwh_per_unit) payload.avg_energy_kwh_per_unit = parseFloat(scope3Downstream.avg_energy_kwh_per_unit)
      payload.product_type = scope3Downstream.product_type
      if (scope3Downstream.product_weight_kg) payload.product_weight_kg = parseFloat(scope3Downstream.product_weight_kg)
      payload.disposal_method = scope3Downstream.disposal_method
      if (scope3Downstream.downstream_leased_area_m2) payload.downstream_leased_area_m2 = parseFloat(scope3Downstream.downstream_leased_area_m2)
      if (scope3Downstream.lessees) payload.lessees = parseInt(scope3Downstream.lessees)
      if (scope3Downstream.num_franchises) payload.num_franchises = parseInt(scope3Downstream.num_franchises)
      if (scope3Downstream.avg_energy_kwh_per_franchise) payload.avg_energy_kwh_per_franchise = parseFloat(scope3Downstream.avg_energy_kwh_per_franchise)
      if (scope3Downstream.franchise_revenue_eur) payload.franchise_revenue_eur = parseFloat(scope3Downstream.franchise_revenue_eur)
      if (scope3Downstream.investment_eur) payload.investment_eur = parseFloat(scope3Downstream.investment_eur)
      payload.investment_type = scope3Downstream.investment_type
      if (scope3Downstream.portfolio_company_revenue_eur) payload.portfolio_company_revenue_eur = parseFloat(scope3Downstream.portfolio_company_revenue_eur)

      const result = await emissionsApi.calculateScope3(payload)
      setScope3Result(result)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // ── Parse Bill ────────────────────────────────────────────────
  const handleParseBill = async () => {
    if (!billText.trim()) {
      setError('Incolla il testo della bolletta')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const result = await emissionsApi.parseBill(billText)
      setBillParseResult(result)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // ── Auto-fill realistic demo data ─────────────────────────────
  const handleAutoFill = async () => {
    setAutoFillLoading(true)
    setError(null)
    setAutoFillMessage(null)
    try {
      const result = await emissionsApi.autoFill({
        reporting_year: reportYear,
        include_previous_year: true,
        replace_existing: true,
      })

      const inputs = result.inputs || {}
      const s1 = inputs.scope1 || {}
      const s2 = inputs.scope2 || {}
      const s3 = inputs.scope3 || {}

      setStationary({
        natural_gas_kwh: String(s1.natural_gas_kwh ?? ''),
        natural_gas_m3: '',
        diesel_heating_litres: String(s1.diesel_heating_litres ?? ''),
        lpg_kwh: '',
        lpg_litres: '',
        biomass_kwh: '',
      })
      setMobile({
        diesel_km: String(s1.diesel_km ?? ''),
        petrol_km: String(s1.petrol_km ?? ''),
        diesel_van_km: String(s1.diesel_van_km ?? ''),
        diesel_truck_km: '',
        electric_km: '',
      })
      setFugitive({
        r410a_kg: String(s1.r410a_kg ?? ''),
        r134a_kg: String(s1.r134a_kg ?? ''),
        r32_kg: '',
        r290_kg: '',
      })
      if (inputs.process?.food_tonnes) {
        setProcess((prev) => ({ ...prev, food_tonnes: String(inputs.process.food_tonnes) }))
      }
      setScope2Input({
        electricity_kwh: String(s2.electricity_kwh ?? ''),
        country: s2.country || 'IT',
        has_green_tariff: !!s2.has_green_tariff,
      })
      setScope3Upstream({
        spend_eur: String(s3.spend_eur ?? ''),
        supplier_nace: s3.supplier_nace || 'C10',
        capital_goods_eur: String(s3.capital_goods_eur ?? ''),
        capital_goods_nace: s3.supplier_nace || 'C10',
        electricity_kwh: String(s3.electricity_kwh ?? ''),
        natural_gas_kwh_scope3: String(s3.natural_gas_kwh_scope3 ?? ''),
        diesel_litres_scope3: String(s3.diesel_litres_scope3 ?? ''),
        upstream_tkm: String(s3.upstream_tkm ?? ''),
        upstream_transport_mode: s3.upstream_transport_mode || 'truck',
        waste_kg: String(s3.waste_kg ?? ''),
        waste_type: s3.waste_type || 'mixed_waste',
        business_travel_km: String(s3.business_travel_km ?? ''),
        travel_mode: s3.travel_mode || 'car_diesel',
        employees: String(s3.employees ?? ''),
        avg_commute_km: String(s3.avg_commute_km ?? '20'),
        commuting_mode: s3.commuting_mode || 'car_alone',
        working_days: String(s3.working_days ?? '220'),
        leased_area_m2: String(s3.leased_area_m2 ?? ''),
        lease_cost_eur: '',
      })
      setScope3Downstream({
        downstream_tkm: String(s3.downstream_tkm ?? ''),
        downstream_transport_mode: s3.downstream_transport_mode || 'truck',
        distance_to_customer_km: String(s3.distance_to_customer_km ?? ''),
        product_weight_tonnes: String(s3.product_weight_tonnes ?? ''),
        product_value_eur: String(s3.product_value_eur ?? ''),
        processing_type: 'default',
        products_sold: String(s3.products_sold ?? ''),
        avg_energy_kwh_per_unit: '',
        product_type: 'default',
        product_weight_kg: String(s3.product_weight_kg ?? ''),
        disposal_method: s3.disposal_method || 'landfill',
        downstream_leased_area_m2: '',
        lessees: '',
        num_franchises: '',
        avg_energy_kwh_per_franchise: '',
        franchise_revenue_eur: '',
        investment_eur: '',
        investment_type: 'equity',
        portfolio_company_revenue_eur: '',
      })

      const calc = result.calculated || {}
      setScope1Result({
        scope: '1',
        total_tco2e: calc.scope1_tco2e,
        categories: [],
        method: 'activity_data_x_emission_factors',
      })
      setScope2Result({
        location_based: { total_tco2e: calc.scope2_location_tco2e },
        market_based: { total_tco2e: calc.scope2_market_tco2e },
        total_tco2e: calc.scope2_location_tco2e,
      })
      setScope3Result({
        total_tco2e: calc.scope3_tco2e,
        total: calc.scope3_tco2e,
      })

      const prevYear = reportYear - 1
      const prevSummary = result.summaries?.[prevYear]
      if (prevSummary) {
        setBaseline2025({
          scope1: String(prevSummary.scope1),
          scope2: String(prevSummary.scope2),
          scope3: String(prevSummary.scope3),
          scope2_market_based: '',
        })
      }

      await loadEmissions()
      await loadSummary()
      setAutoFillMessage(
        `${result.message} Profilo: ${result.profile}. Totale ${reportYear}: ${result.summaries?.[reportYear]?.total?.toFixed(2)} tCO₂e.`,
      )
      setActiveTab('overview')
    } catch (e: any) {
      setError(e.message || 'Errore durante la compilazione automatica')
    } finally {
      setAutoFillLoading(false)
    }
  }

  // ── Save Result ───────────────────────────────────────────────
  const handleSaveResult = async (scope: string, result: any) => {
    try {
      // Scope 2: salva sia location-based che market-based
      if (scope === '2' && result.location_based && result.market_based) {
        // Salva location-based
        await emissionsApi.saveCalculated({
          reporting_year: reportYear,
          scope: '2',
          total_tco2e: result.location_based.total_tco2e,
          category: 'scope2_location_based',
          calculation_method: 'location_based',
        })
        // Salva market-based
        await emissionsApi.saveCalculated({
          reporting_year: reportYear,
          scope: '2',
          total_tco2e: result.market_based.total_tco2e,
          category: 'scope2_market_based',
          calculation_method: 'market_based',
        })
      } else {
        await emissionsApi.saveCalculated({
          reporting_year: reportYear,
          scope,
          total_tco2e: result.total_tco2e || result.total || 0,
          category: String(result.categories?.[0]?.name || result.method || "scope3"),
          calculation_method: result.method || 'calculator',
        })
      }
      await loadEmissions()
      await loadSummary()
    } catch (e: any) {
      setError('Errore nel salvataggio: ' + e.message)
    }
  }


  // ── Reset Forms ───────────────────────────────────────────────
  const resetScope1 = () => {
    setStationary(INITIAL_STATIONARY)
    setMobile(INITIAL_MOBILE)
    setFugitive(INITIAL_FUGITIVE)
    setScope1Result(null)
  }

  const resetScope2 = () => {
    setScope2Input({ electricity_kwh: '', country: 'EU_avg', has_green_tariff: false })
    setScope2Result(null)
  }

  const resetScope3 = () => {
    setScope3Upstream({
      spend_eur: '', supplier_nace: 'DEFAULT',
      capital_goods_eur: '', capital_goods_nace: '',
      electricity_kwh: '', natural_gas_kwh_scope3: '', diesel_litres_scope3: '',
      upstream_tkm: '', upstream_transport_mode: 'truck',
      waste_kg: '', waste_type: 'mixed_waste',
      business_travel_km: '', travel_mode: 'car_diesel',
      employees: '', avg_commute_km: '20', commuting_mode: 'car_alone', working_days: '220',
      leased_area_m2: '', lease_cost_eur: '',
    })
    setScope3Downstream({
      downstream_tkm: '', downstream_transport_mode: 'truck',
      distance_to_customer_km: '', product_weight_tonnes: '',
      product_value_eur: '', processing_type: 'default',
      products_sold: '', avg_energy_kwh_per_unit: '', product_type: 'default',
      product_weight_kg: '', disposal_method: 'landfill',
      downstream_leased_area_m2: '', lessees: '',
      num_franchises: '', avg_energy_kwh_per_franchise: '', franchise_revenue_eur: '',
      investment_eur: '', investment_type: 'equity', portfolio_company_revenue_eur: '',
    })
    setScope3Result(null)
  }

  // ── Render ────────────────────────────────────────────────────
  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <Leaf className="h-6 w-6 text-green-600" />
          Carbon Footprint Calculator (GHG Protocol)
        </h2>
        <div className="flex items-center gap-2">
          <Button
            onClick={handleAutoFill}
            disabled={autoFillLoading}
            className="bg-emerald-600 hover:bg-emerald-700"
          >
            {autoFillLoading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4 mr-2" />
            )}
            Compila dati realistici
          </Button>
          <span className="text-sm text-muted-foreground">Anno Report:</span>
          <input
            type="number"
            className="w-20 px-2 py-1 text-sm border border-input rounded-md bg-background text-center"
            value={reportYear}
            onChange={(e) => setReportYear(parseInt(e.target.value) || new Date().getFullYear())}
          />
        </div>
      </div>

      {autoFillMessage && (
        <div className="mb-4 p-3 bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-lg text-sm text-green-700 dark:text-green-300 flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          {autoFillMessage}
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-400 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          {error}
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="flex-wrap">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="scope1">Scope 1</TabsTrigger>
          <TabsTrigger value="scope2">Scope 2</TabsTrigger>
          <TabsTrigger value="scope3">Scope 3 (15 cat.)</TabsTrigger>
          <TabsTrigger value="data-collection">Raccolta Dati</TabsTrigger>
        </TabsList>

        {/* ═══════════════════════════════════════════════ OVERVIEW ═══ */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">Scope 1 — Emissioni Dirette</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-foreground">
                  {summary?.summary?.scope1?.toFixed(2) ?? '0'} <span className="text-sm">tCO₂e</span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">Scope 2 — Energia</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-foreground">
                  {summary?.summary?.scope2?.toFixed(2) ?? '0'} <span className="text-sm">tCO₂e</span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">Scope 3 — Catena del Valore</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-foreground">
                  {summary?.summary?.scope3?.toFixed(2) ?? '0'} <span className="text-sm">tCO₂e</span>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-green-50 dark:bg-green-800 border-green-200 dark:border-green-500">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-green-700 dark:text-green-200">Totale</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-700 dark:text-green-200">
                  {summary?.summary?.total?.toFixed(2) ?? '0'} <span className="text-sm">tCO₂e</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {summary?.validation && (
            <ValidationPanel result={summary.validation} />
          )}

          {/* ═══ BASELINE 2025 ═══ */}
          <Card className="border-blue-200 dark:border-blue-800">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-blue-600" />
                Baseline 2025 — Confronto Anno Precedente
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                Inserisci i valori del 2025 come anno base. Il calcolatore mostrerà la variazione percentuale.
                Richiesto da ESRS E1-6 e GHG Protocol per il trend analysis.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-3 bg-muted rounded-lg">
                  <label className="text-xs font-medium text-muted-foreground block mb-1">Scope 1 — 2025</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      className="flex-1 px-2 py-1 text-sm border border-input rounded-md bg-background"
                      placeholder="0"
                      value={baseline2025.scope1}
                      onChange={(e) => setBaseline2025({...baseline2025, scope1: e.target.value})}
                      min="0"
                      step="0.01"
                    />
                    <span className="text-xs text-muted-foreground">tCO₂e</span>
                  </div>
                </div>
                <div className="p-3 bg-muted rounded-lg">
                  <label className="text-xs font-medium text-muted-foreground block mb-1">Scope 2 — 2025</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      className="flex-1 px-2 py-1 text-sm border border-input rounded-md bg-background"
                      placeholder="0"
                      value={baseline2025.scope2}
                      onChange={(e) => setBaseline2025({...baseline2025, scope2: e.target.value})}
                      min="0"
                      step="0.01"
                    />
                    <span className="text-xs text-muted-foreground">tCO₂e</span>
                  </div>
                </div>
                <div className="p-3 bg-muted rounded-lg">
                  <label className="text-xs font-medium text-muted-foreground block mb-1">Scope 3 — 2025</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      className="flex-1 px-2 py-1 text-sm border border-input rounded-md bg-background"
                      placeholder="0"
                      value={baseline2025.scope3}
                      onChange={(e) => setBaseline2025({...baseline2025, scope3: e.target.value})}
                      min="0"
                      step="0.01"
                    />
                    <span className="text-xs text-muted-foreground">tCO₂e</span>
                  </div>
                </div>
                <div className="p-3 bg-muted rounded-lg">
                  <label className="text-xs font-medium text-muted-foreground block mb-1">Scope 2 Market-based — 2025</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      className="flex-1 px-2 py-1 text-sm border border-input rounded-md bg-background"
                      placeholder="0"
                      value={baseline2025.scope2_market_based}
                      onChange={(e) => setBaseline2025({...baseline2025, scope2_market_based: e.target.value})}
                      min="0"
                      step="0.01"
                    />
                    <span className="text-xs text-muted-foreground">tCO₂e</span>
                  </div>
                </div>
              </div>
              {/* Variazione percentuale se ci sono dati */}
              {(() => {
                const curTotal = (summary?.summary?.total ?? 0)
                const baseTotal = [baseline2025.scope1, baseline2025.scope2, baseline2025.scope3]
                  .map(v => parseFloat(v) || 0)
                  .reduce((a, b) => a + b, 0)
                if (baseTotal > 0 && curTotal > 0) {
                  const change = ((curTotal - baseTotal) / baseTotal * 100).toFixed(1)
                  const isPositive = parseFloat(change) > 0
                  return (
                    <div className={`mt-3 p-2 rounded-lg text-sm flex items-center gap-2 ${
                      isPositive ? 'bg-red-50 dark:bg-red-950 text-red-700' : 'bg-green-50 dark:bg-green-950 text-green-700'
                    }`}>
                      {isPositive ? '⬆' : '⬇'}
                      <span>Variazione rispetto al 2025:</span>
                      <strong>{isPositive ? '+' : ''}{change}%</strong>
                      <span className="text-xs text-muted-foreground">
                        ({curTotal.toFixed(2)} vs {baseTotal.toFixed(2)} tCO₂e)
                      </span>
                    </div>
                  )
                }
                return null
              })()}
            </CardContent>
          </Card>

          {/* ═══ ESRS E1-6 — GHG EMISSIONS TABLE ═══ */}

          <Card className="border-green-200 dark:border-green-800">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <PieChart className="h-5 w-5 text-green-600" />
                ESRS E1-6 — Tabella Emissioni GHG (Scope 1, 2, 3, Total)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                Confronto tra l'anno di riferimento ({reportYear}) e l'anno base (2025).
                Variazione % calcolata come (valore corrente − valore base) ÷ valore base × 100.
                Obbligatorio ai sensi dell'ESRS E1-6 e del GHG Protocol.
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-green-200 dark:border-green-700">
                      <th className="text-left py-3 px-2 font-semibold">Categoria di emissione</th>
                      <th className="text-right py-3 px-2 font-semibold">2025 (tCO₂e)</th>
                      <th className="text-right py-3 px-2 font-semibold">{reportYear} (tCO₂e)</th>
                      <th className="text-right py-3 px-2 font-semibold">Variazione (%)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(() => {
                      // Helper to compute change
                      const calcPct = (base: number, current: number): { label: string; cls: string } => {
                        if (!base || base <= 0) {
                          return { label: 'N/A', cls: 'text-muted-foreground' }
                        }
                        const chg = ((current - base) / base) * 100
                        const sign = chg > 0 ? '+' : ''
                        const cls = chg > 0
                          ? 'text-red-600 dark:text-red-400 font-semibold'
                          : chg < 0
                            ? 'text-green-600 dark:text-green-400 font-semibold'
                            : 'text-muted-foreground'
                        return { label: `${sign}${chg.toFixed(1)}%`, cls }
                      }

                      // Helper to format numbers (show dash if zero)
                      const fmtNum = (v: number): string => v ? v.toFixed(2) : '—'

                      // Read values
                      const bl1 = parseFloat(baseline2025.scope1) || 0
                      const bl2 = parseFloat(baseline2025.scope2) || 0
                      const bl2m = parseFloat(baseline2025.scope2_market_based) || 0
                      const bl3 = parseFloat(baseline2025.scope3) || 0
                      const blTotal = bl1 + bl2 + bl3

                      const cur1 = summary?.summary?.scope1 || 0
                      const cur2 = summary?.summary?.scope2 || 0
                      const cur2m = summary?.summary?.scope2_market_based || 0
                      const cur3 = summary?.summary?.scope3 || 0
                      const curTotal = summary?.summary?.total || 0

                      const rows: { label: string; base: number; cur: number }[] = [
                        { label: 'Scope 1 — Emissioni dirette (GHG)', base: bl1, cur: cur1 },
                        { label: 'Scope 2 — Emissioni indirette (location-based)', base: bl2, cur: cur2 },
                        { label: 'Scope 2 — Emissioni indirette (market-based)', base: bl2m, cur: cur2m },
                        { label: 'Scope 3 — Emissioni indirette catena del valore', base: bl3, cur: cur3 },
                        { label: 'Totale emissioni GHG (Scope 1 + 2 + 3)', base: blTotal, cur: curTotal },
                      ]

                      return rows.map((row, i) => {
                        const pct = calcPct(row.base, row.cur)
                        const isTotal = i === rows.length - 1
                        return (
                          <tr key={i} className={`border-b ${isTotal ? 'border-green-300 dark:border-green-600 font-semibold bg-green-50 dark:bg-green-950/50' : 'border-border/50 hover:bg-muted/30'}`}>
                            <td className={`py-2.5 px-2 ${isTotal ? 'text-green-800 dark:text-green-200' : ''}`}>
                              {row.label}
                            </td>
                            <td className="text-right py-2.5 px-2 tabular-nums">{fmtNum(row.base)}</td>
                            <td className="text-right py-2.5 px-2 tabular-nums">{fmtNum(row.cur)}</td>
                            <td className={`text-right py-2.5 px-2 tabular-nums ${pct.cls}`}>{pct.label}</td>
                          </tr>
                        )
                      })
                    })()}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Emissioni Registrate ({reportYear})
              </CardTitle>
            </CardHeader>

            <CardContent>
              {savedEmissions.length === 0 ? (
                <p className="text-muted-foreground text-sm">
                  Nessun dato di emissione ancora inserito. Utilizza i tab Scope 1, 2, 3 per calcolare le emissioni.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2 px-2">Scope</th>
                        <th className="text-left py-2 px-2">Categoria</th>
                        <th className="text-right py-2 px-2">Valore (tCO₂e)</th>
                        <th className="text-left py-2 px-2">Metodo</th>
                        <th className="text-left py-2 px-2">Verificato</th>
                      </tr>
                    </thead>
                    <tbody>
                      {savedEmissions.map((em: any) => (
                        <tr key={em.id} className="border-b hover:bg-muted/50">
                          <td className="py-2 px-2">
                            <Badge variant="outline">Scope {em.scope}</Badge>
                          </td>
                          <td className="py-2 px-2">{em.category || '-'}</td>
                          <td className="py-2 px-2 text-right font-medium">{em.value?.toFixed(4)}</td>
                          <td className="py-2 px-2 text-muted-foreground">{em.calculation_method || '-'}</td>
                          <td className="py-2 px-2">
                            {em.verified ? (
                              <CheckCircle2 className="h-4 w-4 text-green-600" />
                            ) : (
                              <span className="text-muted-foreground">No</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ════════════════════════════════════════════ SCOPE 1 ═══ */}
        <TabsContent value="scope1" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">1. Combustione Stazionaria</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <NumberInput label="Gas Naturale" unit="kWh" value={stationary.natural_gas_kwh} onChange={(v) => setStationary({...stationary, natural_gas_kwh: v})} />
                  <NumberInput label="Gas Naturale" unit="m³" value={stationary.natural_gas_m3} onChange={(v) => setStationary({...stationary, natural_gas_m3: v})} />
                  <NumberInput label="Gasolio Riscaldamento" unit="litri" value={stationary.diesel_heating_litres} onChange={(v) => setStationary({...stationary, diesel_heating_litres: v})} />
                  <NumberInput label="GPL" unit="kWh" value={stationary.lpg_kwh} onChange={(v) => setStationary({...stationary, lpg_kwh: v})} />
                  <NumberInput label="GPL" unit="litri" value={stationary.lpg_litres} onChange={(v) => setStationary({...stationary, lpg_litres: v})} />
                  <NumberInput label="Biomassa" unit="kWh" value={stationary.biomass_kwh} onChange={(v) => setStationary({...stationary, biomass_kwh: v})} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">2. Combustione Mobile (Veicoli Aziendali)</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <NumberInput label="Auto Diesel" unit="km" value={mobile.diesel_km} onChange={(v) => setMobile({...mobile, diesel_km: v})} />
                  <NumberInput label="Auto Benzina" unit="km" value={mobile.petrol_km} onChange={(v) => setMobile({...mobile, petrol_km: v})} />
                  <NumberInput label="Furgone Diesel" unit="km" value={mobile.diesel_van_km} onChange={(v) => setMobile({...mobile, diesel_van_km: v})} />
                  <NumberInput label="Camion Diesel" unit="km" value={mobile.diesel_truck_km} onChange={(v) => setMobile({...mobile, diesel_truck_km: v})} />
                  <NumberInput label="Veicolo Elettrico" unit="km" value={mobile.electric_km} onChange={(v) => setMobile({...mobile, electric_km: v})} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">3. Emissioni Fuggitive (Refrigeranti)</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <NumberInput label="R-410A (GWP 2088)" unit="kg" value={fugitive.r410a_kg} onChange={(v) => setFugitive({...fugitive, r410a_kg: v})} />
                  <NumberInput label="R-134a (GWP 1430)" unit="kg" value={fugitive.r134a_kg} onChange={(v) => setFugitive({...fugitive, r134a_kg: v})} />
                  <NumberInput label="R-32 (GWP 675)" unit="kg" value={fugitive.r32_kg} onChange={(v) => setFugitive({...fugitive, r32_kg: v})} />
                  <NumberInput label="R-290 / Propano (GWP 3)" unit="kg" value={fugitive.r290_kg} onChange={(v) => setFugitive({...fugitive, r290_kg: v})} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">4. Process Emissions (Industriali)</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-xs text-muted-foreground mb-2">
                    Solo per aziende manifatturiere. Emissioni da processi chimici/fisici.
                  </p>
                  <NumberInput label="Cemento (clinker)" unit="tonn" value={process.cement_tonnes} onChange={(v) => setProcess({...process, cement_tonnes: v})} />
                  <NumberInput label="Acciaio BF-BOF" unit="tonn" value={process.steel_tonnes_bf_bof} onChange={(v) => setProcess({...process, steel_tonnes_bf_bof: v})} />
                  <NumberInput label="Acciaio EAF" unit="tonn" value={process.steel_tonnes_eaf} onChange={(v) => setProcess({...process, steel_tonnes_eaf: v})} />
                  <NumberInput label="Ammoniaca" unit="tonn" value={process.ammonia_tonnes} onChange={(v) => setProcess({...process, ammonia_tonnes: v})} />
                  <NumberInput label="Alluminio Primario" unit="tonn" value={process.aluminium_tonnes} onChange={(v) => setProcess({...process, aluminium_tonnes: v})} />
                  <NumberInput label="Carta" unit="tonn" value={process.paper_tonnes} onChange={(v) => setProcess({...process, paper_tonnes: v})} />
                  <NumberInput label="Vetro" unit="tonn" value={process.glass_tonnes} onChange={(v) => setProcess({...process, glass_tonnes: v})} />
                  <NumberInput label="Alimenti Processati" unit="tonn" value={process.food_tonnes} onChange={(v) => setProcess({...process, food_tonnes: v})} />
                  <NumberInput label="Perdita Refrigerante (processo)" unit="kg" value={process.refrigerant_leak_kg} onChange={(v) => setProcess({...process, refrigerant_leak_kg: v})} />
                </CardContent>
              </Card>

              <div className="flex gap-2 flex-wrap">
                <Button onClick={handleCalculateScope1} disabled={loading}>
                  <Calculator className="h-4 w-4 mr-2" />
                  {loading ? 'Calcolo...' : 'Calcola Scope 1'}
                </Button>
                <Button variant="outline" onClick={resetScope1}>
                  Reset
                </Button>
              </div>
            </div>

            <div className="space-y-6">
              {scope1Result && (
                <>
                  <ResultCard result={scope1Result} />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => handleSaveResult('1', scope1Result)}>
                      Salva nel Database
                    </Button>
                  </div>
                </>
              )}
              {scope1ProcessResult && (
                <>
                  <ResultCard result={scope1ProcessResult} />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => handleSaveResult('1', scope1ProcessResult)}>
                      Salva Process Emissions
                    </Button>
                  </div>
                </>
              )}
            </div>
          </div>

          <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
            <CardContent className="py-3 text-sm text-blue-700 dark:text-blue-300">
              <strong>Fonte fattori di emissione:</strong> DEFRA UK 2025, EPA US 2025, IPCC AR6 2025, ISPRA 2025 (Italia), 
              Ecoinvent 3.10. Metodo: Activity Data × Emission Factor.
            </CardContent>
          </Card>
        </TabsContent>

        {/* ════════════════════════════════════════════ SCOPE 2 ═══ */}
        <TabsContent value="scope2" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Consumo Elettrico Annuo</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <NumberInput
                    label="Consumo Elettrico"
                    unit="kWh"
                    value={scope2Input.electricity_kwh}
                    onChange={(v) => setScope2Input({...scope2Input, electricity_kwh: v})}
                    placeholder="es. 50000"
                  />

                  <div>
                    <label className="text-sm font-medium text-foreground block mb-1">Paese</label>
                    <select
                      className="w-full px-3 py-1.5 text-sm border border-input rounded-md bg-background"
                      value={scope2Input.country}
                      onChange={(e) => setScope2Input({...scope2Input, country: e.target.value})}
                    >
                      {COUNTRIES.map((c) => (
                        <option key={c.code} value={c.code}>{c.name}</option>
                      ))}
                    </select>
                  </div>

                  <div className="flex items-center gap-2 p-3 bg-muted rounded-lg">
                    <input
                      type="checkbox"
                      id="green-tariff"
                      checked={scope2Input.has_green_tariff}
                      onChange={(e) => setScope2Input({...scope2Input, has_green_tariff: e.target.checked})}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <label htmlFor="green-tariff" className="text-sm text-foreground">
                      Contratto energia rinnovabile certificata (GO)
                    </label>
                  </div>
                </CardContent>
              </Card>

              <div className="flex gap-2">
                <Button onClick={handleCalculateScope2} disabled={loading || !scope2Input.electricity_kwh}>
                  <Calculator className="h-4 w-4 mr-2" />
                  {loading ? 'Calcolo...' : 'Calcola Scope 2'}
                </Button>
                <Button variant="outline" onClick={resetScope2}>
                  Reset
                </Button>
              </div>
            </div>

            <div className="space-y-6">
              {scope2Result && (
                <>
                  <ResultCard result={scope2Result} />
                  <div className="space-y-2">
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => handleSaveResult('2', scope2Result)}>
                        Salva nel Database
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      ESRS E1-6 richiede il reporting duale (location-based + market-based).
                      La differenza tra i due metodi è un indicatore chiave.
                    </p>
                  </div>
                </>
              )}

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Fattori di Emissione per Paese</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="max-h-48 overflow-y-auto text-xs space-y-1">
                    {COUNTRIES.filter(c => c.code !== 'EU_avg').map(c => (
                      <div key={c.code} className="flex justify-between py-0.5">
                        <span>{c.name}</span>
                        <span className="font-mono">
                          {c.code === 'IT' ? 0.286 : c.code === 'DE' ? 0.374 : c.code === 'FR' ? 0.055 : c.code === 'ES' ? 0.226 : c.code === 'UK' ? 0.205 : 0.276} kgCO₂e/kWh
                        </span>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Fonte: AIE/Eurostat 2025 (location-based), AIB Residual Mix 2025 (market-based)
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>

          <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
            <CardContent className="py-3 text-sm text-blue-700 dark:text-blue-300">
              <strong>ESRS E1-6:</strong> Le emissioni Scope 2 devono essere riportate con entrambi i metodi 
              (location-based e market-based). Il market-based riflette contratti di energia rinnovabile.
            </CardContent>
          </Card>
        </TabsContent>

        {/* ════════════════════════════════════════════ SCOPE 3 ═══ */}
        <TabsContent value="scope3" className="space-y-6">
          <Card className="bg-purple-50 dark:bg-purple-950 border-purple-200 dark:border-purple-800">
            <CardContent className="py-3 text-sm text-purple-700 dark:text-purple-300">
              <strong>GHG Protocol Scope 3 — 15 Categorie.</strong> Metodo principale: spend-based (adatto PMI).
              Fonti: EXIOBASE 3 + Ecoinvent 3.10 per codici NACE. Completa i campi pertinenti per la tua azienda.
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* ── UPSTREAM (1-8) ── */}
            <div className="space-y-6">
              <h3 className="font-semibold flex items-center gap-2 text-lg">
                <Truck className="h-5 w-5 text-purple-600" />
                Upstream (Categorie 1-8)
              </h3>

              {/* Cat.1: Purchased goods */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <ShoppingBag className="h-4 w-4" />
                    1. Purchased Goods & Services
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <NumberInput label="Spesa Annua Beni/Servizi" unit="EUR" value={scope3Upstream.spend_eur} onChange={(v) => setScope3Upstream({...scope3Upstream, spend_eur: v})} />
                  <SelectInput label="Settore Fornitore (NACE)" value={scope3Upstream.supplier_nace} onChange={(v) => setScope3Upstream({...scope3Upstream, supplier_nace: v})} options={NACE_CODES} />
                </CardContent>
              </Card>

              {/* Cat.2: Capital goods */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Briefcase className="h-4 w-4" />
                    2. Capital Goods
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <NumberInput label="Spesa Annua Beni Strumentali" unit="EUR" value={scope3Upstream.capital_goods_eur} onChange={(v) => setScope3Upstream({...scope3Upstream, capital_goods_eur: v})} />
                  <SelectInput label="Settore (NACE)" value={scope3Upstream.capital_goods_nace || scope3Upstream.supplier_nace} onChange={(v) => setScope3Upstream({...scope3Upstream, capital_goods_nace: v})} options={NACE_CODES} />
                </CardContent>
              </Card>

              {/* Cat.3: WTT */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Zap className="h-4 w-4" />
                    3. Fuel & Energy Related (WTT)
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <NumberInput label="Energia Elettrica acquistata" unit="kWh" value={scope3Upstream.electricity_kwh} onChange={(v) => setScope3Upstream({...scope3Upstream, electricity_kwh: v})} />
                  <NumberInput label="Gas Naturale acquistato" unit="kWh" value={scope3Upstream.natural_gas_kwh_scope3} onChange={(v) => setScope3Upstream({...scope3Upstream, natural_gas_kwh_scope3: v})} />
                  <NumberInput label="Gasolio acquistato" unit="litri" value={scope3Upstream.diesel_litres_scope3} onChange={(v) => setScope3Upstream({...scope3Upstream, diesel_litres_scope3: v})} />
                </CardContent>
              </Card>

              {/* Cat.4: Upstream transport */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Truck className="h-4 w-4" />
                    4. Upstream Transportation
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <NumberInput label="tkm totali (tonn×km)" unit="tkm" value={scope3Upstream.upstream_tkm} onChange={(v) => setScope3Upstream({...scope3Upstream, upstream_tkm: v})} />
                  <SelectInput label="Mezzo di Trasporto" value={scope3Upstream.upstream_transport_mode} onChange={(v) => setScope3Upstream({...scope3Upstream, upstream_transport_mode: v})} options={[{ code: 'truck', name: 'Camion' }, { code: 'train', name: 'Treno' }, { code: 'ship', name: 'Nave' }, { code: 'air', name: 'Aereo' }, { code: 'van', name: 'Furgone' }]} />
                </CardContent>
              </Card>

              {/* Cat.5: Waste */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Trash2 className="h-4 w-4" />
                    5. Waste Generated
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <NumberInput label="Rifiuti totali annui" unit="kg" value={scope3Upstream.waste_kg} onChange={(v) => setScope3Upstream({...scope3Upstream, waste_kg: v})} />
                  <SelectInput label="Tipo Rifiuto" value={scope3Upstream.waste_type} onChange={(v) => setScope3Upstream({...scope3Upstream, waste_type: v})} options={WASTE_TYPES} />
                </CardContent>
              </Card>

              {/* Cat.6: Business travel */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Plane className="h-4 w-4" />
                    6. Business Travel
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <NumberInput label="km viaggio annui totali" unit="km" value={scope3Upstream.business_travel_km} onChange={(v) => setScope3Upstream({...scope3Upstream, business_travel_km: v})} />
                  <SelectInput label="Mezzo" value={scope3Upstream.travel_mode} onChange={(v) => setScope3Upstream({...scope3Upstream, travel_mode: v})} options={TRAVEL_MODES} />
                </CardContent>
              </Card>

              {/* Cat.7: Commuting */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Users className="h-4 w-4" />
                    7. Employee Commuting
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <NumberInput label="Numero Dipendenti" unit="" value={scope3Upstream.employees} onChange={(v) => setScope3Upstream({...scope3Upstream, employees: v})} />
                  <NumberInput label="Distanza media casa-lavoro" unit="km" value={scope3Upstream.avg_commute_km} onChange={(v) => setScope3Upstream({...scope3Upstream, avg_commute_km: v})} />
                  <SelectInput label="Mezzo principale" value={scope3Upstream.commuting_mode} onChange={(v) => setScope3Upstream({...scope3Upstream, commuting_mode: v})} options={COMMUTING_MODES} />
                  <NumberInput label="Giorni lavorativi/anno" unit="" value={scope3Upstream.working_days} onChange={(v) => setScope3Upstream({...scope3Upstream, working_days: v})} />
                </CardContent>
              </Card>

              {/* Cat.8: Leased assets */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Building className="h-4 w-4" />
                    8. Upstream Leased Assets
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <NumberInput label="Superficie in locazione" unit="m²" value={scope3Upstream.leased_area_m2} onChange={(v) => setScope3Upstream({...scope3Upstream, leased_area_m2: v})} />
                  <NumberInput label="Costo annuo locazione" unit="EUR" value={scope3Upstream.lease_cost_eur} onChange={(v) => setScope3Upstream({...scope3Upstream, lease_cost_eur: v})} />
                </CardContent>
              </Card>
            </div>

            {/* ── DOWNSTREAM (9-15) ── */}
            <div className="space-y-6">
              <h3 className="font-semibold flex items-center gap-2 text-lg">
                <TrendingUp className="h-5 w-5 text-purple-600" />
                Downstream (Categorie 9-15)
              </h3>

              {/* Cat.9: Downstream transport */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Truck className="h-4 w-4" />
                    9. Downstream Transportation
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <NumberInput label="tkm downstream" unit="tkm" value={scope3Downstream.downstream_tkm} onChange={(v) => setScope3Downstream({...scope3Downstream, downstream_tkm: v})} />
                  <SelectInput label="Mezzo" value={scope3Downstream.downstream_transport_mode} onChange={(v) => setScope3Downstream({...scope3Downstream, downstream_transport_mode: v})} options={[{ code: 'truck', name: 'Camion' }, { code: 'train', name: 'Treno' }, { code: 'ship', name: 'Nave' }, { code: 'air', name: 'Aereo' }]} />
                  <NumberInput label="Distanza media cliente" unit="km" value={scope3Downstream.distance_to_customer_km} onChange={(v) => setScope3Downstream({...scope3Downstream, distance_to_customer_km: v})} />
                  <NumberInput label="Peso medio prodotto" unit="tonn" value={scope3Downstream.product_weight_tonnes} onChange={(v) => setScope3Downstream({...scope3Downstream, product_weight_tonnes: v})} />
                </CardContent>
              </Card>

              {/* Cat.10: Processing */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Settings className="h-4 w-4" />
                    10. Processing of Sold Products
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <NumberInput label="Valore prodotti venduti" unit="EUR" value={scope3Downstream.product_value_eur} onChange={(v) => setScope3Downstream({...scope3Downstream, product_value_eur: v})} />
                  <SelectInput label="Tipo Processing" value={scope3Downstream.processing_type} onChange={(v) => setScope3Downstream({...scope3Downstream, processing_type: v})} options={[{ code: 'default', name: 'Default' }, { code: 'basic_metals', name: 'Metalli base' }, { code: 'chemicals', name: 'Chimici' }, { code: 'food', name: 'Alimentare' }, { code: 'textiles', name: 'Tessile' }]} />
                </CardContent>
              </Card>

              {/* Cat.11: Use of sold products */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Zap className="h-4 w-4" />
                    11. Use of Sold Products
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <NumberInput label="Prodotti venduti (n.)" unit="" value={scope3Downstream.products_sold} onChange={(v) => setScope3Downstream({...scope3Downstream, products_sold: v})} />
                  <NumberInput label="Energia media per prodotto" unit="kWh" value={scope3Downstream.avg_energy_kwh_per_unit} onChange={(v) => setScope3Downstream({...scope3Downstream, avg_energy_kwh_per_unit: v})} />
                  <SelectInput label="Tipo Prodotto" value={scope3Downstream.product_type} onChange={(v) => setScope3Downstream({...scope3Downstream, product_type: v})} options={[{ code: 'default', name: 'Default' }, { code: 'electronics', name: 'Elettronica' }, { code: 'appliances', name: 'Elettrodomestici' }, { code: 'machinery', name: 'Macchinari' }, { code: 'vehicles', name: 'Veicoli' }]} />
                </CardContent>
              </Card>

              {/* Cat.12: End of life */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Trash2 className="h-4 w-4" />
                    12. End-of-Life of Sold Products
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <NumberInput label="Peso medio per prodotto" unit="kg" value={scope3Downstream.product_weight_kg} onChange={(v) => setScope3Downstream({...scope3Downstream, product_weight_kg: v})} />
                  <SelectInput label="Metodo Smaltimento" value={scope3Downstream.disposal_method} onChange={(v) => setScope3Downstream({...scope3Downstream, disposal_method: v})} options={DISPOSAL_METHODS} />
                </CardContent>
              </Card>

              {/* Cat.13: Downstream leased */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Building className="h-4 w-4" />
                    13. Downstream Leased Assets
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <NumberInput label="Superficie in sublocazione" unit="m²" value={scope3Downstream.downstream_leased_area_m2} onChange={(v) => setScope3Downstream({...scope3Downstream, downstream_leased_area_m2: v})} />
                  <NumberInput label="Numero locatari" unit="" value={scope3Downstream.lessees} onChange={(v) => setScope3Downstream({...scope3Downstream, lessees: v})} />
                </CardContent>
              </Card>

              {/* Cat.14: Franchises */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <PieChart className="h-4 w-4" />
                    14. Franchises
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <NumberInput label="Numero Franchise" unit="" value={scope3Downstream.num_franchises} onChange={(v) => setScope3Downstream({...scope3Downstream, num_franchises: v})} />
                  <NumberInput label="Energia media per franchise" unit="kWh" value={scope3Downstream.avg_energy_kwh_per_franchise} onChange={(v) => setScope3Downstream({...scope3Downstream, avg_energy_kwh_per_franchise: v})} />
                  <NumberInput label="Fatturato franchise" unit="EUR" value={scope3Downstream.franchise_revenue_eur} onChange={(v) => setScope3Downstream({...scope3Downstream, franchise_revenue_eur: v})} />
                </CardContent>
              </Card>

              {/* Cat.15: Investments */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" />
                    15. Investments
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-xs text-muted-foreground">Per banche, assicurazioni, società di investimento.</p>
                  <NumberInput label="Investimenti totali" unit="EUR" value={scope3Downstream.investment_eur} onChange={(v) => setScope3Downstream({...scope3Downstream, investment_eur: v})} />
                  <SelectInput label="Tipo Investimento" value={scope3Downstream.investment_type} onChange={(v) => setScope3Downstream({...scope3Downstream, investment_type: v})} options={[{ code: 'equity', name: 'Equity' }, { code: 'debt', name: 'Debito' }, { code: 'project_finance', name: 'Project Finance' }]} />
                  <NumberInput label="Fatturato società partecipate" unit="EUR" value={scope3Downstream.portfolio_company_revenue_eur} onChange={(v) => setScope3Downstream({...scope3Downstream, portfolio_company_revenue_eur: v})} />
                </CardContent>
              </Card>

              {/* Calculate all Categs button */}
              <div className="flex gap-2">
                <Button onClick={handleCalculateScope3} disabled={loading} className="bg-purple-600 hover:bg-purple-700">
                  <Calculator className="h-4 w-4 mr-2" />
                  {loading ? 'Calcolo...' : 'Calcola Totale Scope 3 (15 cat.)'}
                </Button>
                <Button variant="outline" onClick={resetScope3}>
                  Reset
                </Button>
              </div>
            </div>
          </div>

          {/* Scope 3 Results */}
          {scope3Result && (
            <div className="space-y-4">
              <ResultCard result={scope3Result} />
              <div className="flex gap-2">
                <Button size="sm" onClick={() => handleSaveResult('3', scope3Result)}>
                  Salva Scope 3 nel Database
                </Button>
              </div>
            </div>
          )}
        </TabsContent>

        {/* ════════════════════════════════════════ DATA COLLECTION ═══ */}
        <TabsContent value="data-collection" className="space-y-6">
          <Card className="bg-amber-50 dark:bg-amber-950 border-amber-200 dark:border-amber-800">
            <CardContent className="py-3 text-sm text-amber-700 dark:text-amber-300 flex items-center gap-2">
              <Database className="h-4 w-4" />
              <span>Raccogli automaticamente dati da fonti esterne: bollette, contabilità, flotta, HR.</span>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* ── Utility Bill OCR ── */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  OCR Bolletta Elettrica/Gas
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-xs text-muted-foreground">
                  Incolla il testo estratto dal PDF della bolletta. Il sistema estrae automaticamente consumi, fornitore e periodo.
                </p>
                <TextInput
                  label="Testo bolletta (da PDF/OCR)"
                  value={billText}
                  onChange={setBillText}
                  placeholder="Incolla qui il testo della bolletta..."
                />
                <Button onClick={handleParseBill} disabled={loading}>
                  <Upload className="h-4 w-4 mr-2" />
                  {loading ? 'Analisi...' : 'Analizza Bolletta'}
                </Button>

                {billParseResult && (
                  <div className="mt-3 space-y-2 text-sm">
                    {/* Supporta sia formato nuovo che legacy */}
                    {(() => {
                      // Normalizza: nuovo formato o legacy
                      const hasNewFormat = 'fornitore' in billParseResult
                      const success = hasNewFormat
                        ? (billParseResult.confidenza >= 30)
                        : billParseResult.success
                      const provider = hasNewFormat ? billParseResult.fornitore : billParseResult.provider
                      const tipo = hasNewFormat ? billParseResult.tipo : billParseResult.bill_type
                      const consumo = hasNewFormat ? billParseResult.consumo_kwh : billParseResult.consumption_kwh
                      const costo = hasNewFormat ? billParseResult.costo_euro : billParseResult.total_cost_eur
                      const periodoInizio = hasNewFormat ? billParseResult.periodo_inizio : billParseResult.period_start
                      const periodoFine = hasNewFormat ? billParseResult.periodo_fine : billParseResult.period_end
                      const podPdr = hasNewFormat ? billParseResult.pod_pdr : billParseResult.pod_pdr_code
                      const confidenza = hasNewFormat ? billParseResult.confidenza : Math.round((billParseResult.confidence || 0) * 100)

                      return (
                        <div className={`p-3 rounded-lg ${confidenza >= 50 ? 'bg-green-50 dark:bg-green-800' : confidenza >= 30 ? 'bg-yellow-50 dark:bg-yellow-800' : 'bg-red-50 dark:bg-red-950'}`}>
                          <div className="flex items-center gap-2 mb-2">
                            {confidenza >= 50 ? (
                              <CheckCircle2 className="h-4 w-4 text-green-600" />
                            ) : (
                              <AlertTriangle className="h-4 w-4 text-yellow-600" />
                            )}
                            <span className="font-medium">
                              {confidenza >= 50 ? 'Dati estratti' : confidenza >= 30 ? 'Estrazione parziale' : 'Estrazione incerta'}
                            </span>
                            <Badge variant={confidenza >= 50 ? 'default' : 'outline'} className={`ml-auto text-xs ${confidenza >= 70 ? 'bg-green-500' : confidenza >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}>
                              {confidenza}%
                            </Badge>
                          </div>
                          <div className="space-y-1 text-xs">
                            <div className="flex justify-between">
                              <span>Fornitore:</span>
                              <span className="font-medium">{provider || 'N/D'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Tipo:</span>
                              <span className="font-medium capitalize">{tipo || 'N/D'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Consumo:</span>
                              <span className="font-medium">{consumo ? `${consumo} kWh` : 'N/D'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Costo:</span>
                              <span className="font-medium">{costo ? `€${costo.toFixed(2)}` : 'N/D'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Periodo:</span>
                              <span className="font-medium">{periodoInizio || '?'} → {periodoFine || '?'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>POD/PDR:</span>
                              <span className="font-medium">{podPdr || 'N/D'}</span>
                            </div>
                          </div>
                        </div>
                      )
                    })()}
                  </div>
                )}

              </CardContent>
            </Card>

            {/* ── Integration Options ── */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  Opzioni di Integrazione
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2">
                  <div className="p-3 bg-muted rounded-lg">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <Database className="h-4 w-4 text-blue-500" />
                      Contabilità (XERO/QuickBooks)
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">Importa spese per calcolo spend-based Scope 3 Cat.1</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <Zap className="h-4 w-4 text-yellow-500" />
                      Fornitore Energia (API)
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">Enel, EDF, E.ON, Iberdrola, Engie</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <Users className="h-4 w-4 text-green-500" />
                      HR / Payroll
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">Dipendenti per commuting Scope 3 Cat.7</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <Truck className="h-4 w-4 text-orange-500" />
                      Flotta Aziendale
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">Veicoli per Scope 1 mobile combustion</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <Building className="h-4 w-4 text-purple-500" />
                      Banca (CSV/CAMT.053)
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">Mapping automatico spese da estratto conto</p>
                  </div>
                </div>
                <div className="p-3 bg-blue-50 dark:bg-blue-950 rounded-lg text-xs text-blue-700 dark:text-blue-300">
                  <strong>CSV Upload:</strong> Carica file CSV con transazioni, flotta, consumi energetici o rifiuti.
                  Il sistema riconosce automaticamente i campi in italiano e inglese.
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
