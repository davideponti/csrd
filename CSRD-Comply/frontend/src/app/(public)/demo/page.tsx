'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import Link from 'next/link'
import {
  Building2,
  Gauge,
  LayoutGrid,
  Flame,
  FileText,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Download,
  Building,
  Briefcase,
  Globe,
  Euro,
  TrendingUp,
  AlertTriangle,
  ChevronRight,
  ExternalLink,
  ScrollText,
  Tag,
  FileSpreadsheet,
  Sparkles,
} from 'lucide-react'
import { Button } from '@/components/ui'
import { cn } from '@/lib/utils'

// ─── Configuration ───────────────────────────────────────────────
const SIGNUP_URL = 'https://csrdcomply.com/auth/register'

const STEPS = [
  { id: 1, label: 'Profilo', icon: Building2 },
  { id: 2, label: 'Readiness', icon: Gauge },
  { id: 3, label: 'Materialità', icon: LayoutGrid },
  { id: 4, label: 'Carbon', icon: Flame },
  { id: 5, label: 'Report', icon: FileText },
]

const READINESS_AREAS = [
  { label: 'Governance', score: 45, color: 'bg-emerald-500' },
  { label: 'Ambiente', score: 28, color: 'bg-sky-500' },
  { label: 'Sociale', score: 31, color: 'bg-violet-500' },
  { label: 'Disclosure', score: 22, color: 'bg-amber-500' },
]

const MATERIALITY_POINTS = [
  { id: 'Emissioni GHG', x: 82, y: 88, size: 14, color: '#ef4444' },
  { id: 'Consumo energetico', x: 70, y: 65, size: 12, color: '#f59e0b' },
  { id: 'Diritti lavoratori', x: 55, y: 60, size: 11, color: '#8b5cf6' },
  { id: 'Diversità & Inclusione', x: 40, y: 45, size: 9, color: '#8b5cf6' },
  { id: 'Acque reflue', x: 30, y: 35, size: 8, color: '#06b6d4' },
  { id: 'Biodiversità', x: 15, y: 18, size: 7, color: '#06b6d4' },
]

const CARBON_DATA = [
  { name: 'Scope 1', value: 847, color: '#ef4444' },
  { name: 'Scope 2', value: 312, color: '#f59e0b' },
  { name: 'Scope 3', value: 2341, color: '#6b7280' },
]

const LOG_LINES = [
  'Analisi gap ESRS completata... OK',
  'Applicando standard ESRS E1 (Cambiamenti climatici)...',
  'Mapping dati finanziari con tassonomia ESEF 2025...',
  'Tagging iXBRL completato — 347 facts marcati',
]

// ─── Custom Hooks ────────────────────────────────────────────────

function useCounter(target: number, duration: number, trigger: boolean) {
  const [value, setValue] = useState(0)

  useEffect(() => {
    if (!trigger) return
    let start = 0
    const increment = target / (duration / 16)
    const timer = setInterval(() => {
      start += increment
      if (start >= target) {
        setValue(target)
        clearInterval(timer)
      } else {
        setValue(Math.floor(start))
      }
    }, 16)
    return () => clearInterval(timer)
  }, [target, duration, trigger])

  return value
}

function useProgressAnimation(target: number, trigger: boolean) {
  const [width, setWidth] = useState(0)

  useEffect(() => {
    if (!trigger) return
    const timer = setTimeout(() => setWidth(target), 300)
    return () => clearTimeout(timer)
  }, [target, trigger])

  return width
}

function useSequentialLogs() {
  const [visibleLogs, setVisibleLogs] = useState<string[]>([])

  const startLogs = useCallback(() => {
    setVisibleLogs([])
    LOG_LINES.forEach((line, i) => {
      setTimeout(() => {
        setVisibleLogs((prev) => [...prev, line])
      }, (i + 1) * 800)
    })
  }, [])

  return { visibleLogs, startLogs }
}

// ─── Step 1: Company Profile ─────────────────────────────────────

function StepProfile({ onNext }: { onNext: () => void }) {
  return (
    <div className="space-y-8">
      {/* Company card */}
      <div className="bg-white rounded-2xl border border-emerald-100 overflow-hidden shadow-sm">
        <div className="bg-gradient-to-r from-emerald-600 to-emerald-700 px-6 py-5">
          <div className="flex items-center gap-3">
            <Building className="h-6 w-6 text-emerald-100" />
            <div>
              <h3 className="text-white font-semibold text-lg">Rossi Meccanica S.r.l.</h3>
              <p className="text-emerald-200 text-sm">Manifatturiero metalmeccanico</p>
            </div>
          </div>
        </div>
        <div className="p-6 grid grid-cols-1 sm:grid-cols-2 gap-6">
          {[
            { icon: Briefcase, label: 'Settore NACE', value: 'C25 — Fabbricazione prodotti in metallo' },
            { icon: Building2, label: 'Dipendenti', value: '310' },
            { icon: Euro, label: 'Fatturato', value: '€ 42.000.000' },
            { icon: Globe, label: 'Paese', value: 'Italia 🇮🇹' },
          ].map((item) => (
            <div key={item.label} className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center shrink-0">
                <item.icon className="h-5 w-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">{item.label}</p>
                <p className="text-gray-900 font-medium mt-0.5">{item.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* CSRD notice */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 flex items-start gap-4">
        <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center shrink-0">
          <AlertTriangle className="h-5 w-5 text-amber-600" />
        </div>
        <div>
          <p className="font-semibold text-amber-800">Soggetta alla CSRD dal 2026</p>
          <p className="text-amber-700 text-sm mt-1">
            Prima rendicontazione di sostenibilità obbligatoria entro{' '}
            <strong>aprile 2027</strong> — gap attuale stimato: 66%.
          </p>
        </div>
      </div>

      {/* CTA */}
      <div className="text-center pt-2">
        <Button
          size="lg"
          onClick={onNext}
          className="bg-emerald-600 hover:bg-emerald-700 text-white px-10 text-base shadow-lg shadow-emerald-200"
        >
          Avvia Assessment
          <ArrowRight className="ml-2 h-5 w-5" />
        </Button>
      </div>
    </div>
  )
}

// ─── Step 2: Readiness Score ─────────────────────────────────────

function StepReadiness() {
  const [started, setStarted] = useState(false)
  const score = useCounter(34, 2000, started)
  const governanceWidth = useProgressAnimation(45, started)
  const ambienteWidth = useProgressAnimation(28, started)
  const socialeWidth = useProgressAnimation(31, started)
  const disclosureWidth = useProgressAnimation(22, started)

  useEffect(() => {
    setStarted(true)
  }, [])

  const barWidths = [governanceWidth, ambienteWidth, socialeWidth, disclosureWidth]

  return (
    <div className="space-y-8">
      {/* Score circle */}
      <div className="flex justify-center">
        <div className="relative w-40 h-40">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="52" fill="none" stroke="#e5e7eb" strokeWidth="8" />
            <circle
              cx="60" cy="60" r="52"
              fill="none"
              stroke="#059669"
              strokeWidth="8"
              strokeDasharray={`${(score / 100) * 326.73} 326.73`}
              strokeLinecap="round"
              className="transition-all duration-500"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-4xl font-bold text-gray-900">{score}</span>
            <span className="text-sm text-gray-500 font-medium">/ 100</span>
          </div>
        </div>
      </div>

      <p className="text-center text-gray-600">
        CSRD Readiness Score
      </p>

      {/* Bars */}
      <div className="space-y-4">
        {READINESS_AREAS.map((area, i) => (
          <div key={area.label}>
            <div className="flex justify-between text-sm mb-1.5">
              <span className="font-medium text-gray-700">{area.label}</span>
              <span className="text-gray-500">{area.score}%</span>
            </div>
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={cn('h-full rounded-full transition-all duration-1000 ease-out', area.color)}
                style={{ width: `${barWidths[i]}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Message */}
      <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
        <AlertTriangle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-red-800">Gap significativi rilevati</p>
          <p className="text-red-700 text-sm mt-1">
            Sono state identificate <strong>3 aree prioritarie</strong> che richiedono interventi urgenti:
            Ambiente, Sociale e Disclosure.
          </p>
        </div>
      </div>
    </div>
  )
}

// ─── Step 3: Double Materiality ──────────────────────────────────

function StepMateriality() {
  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-500 text-center">
        Impatto vs Rischio Finanziario — I temi sopra la soglia tratteggiata sono <strong>materiali</strong>
      </p>

      {/* Scatter plot */}
      <div className="flex justify-center">
        <svg viewBox="0 0 400 360" className="w-full max-w-md h-auto" xmlns="http://www.w3.org/2000/svg">
          {/* Grid lines */}
          {[0, 1, 2, 3, 4].map((i) => (
            <line key={`h${i}`} x1="40" y1={40 + i * 60} x2="380" y2={40 + i * 60} stroke="#f3f4f6" strokeWidth="1" />
          ))}
          {[0, 1, 2, 3, 4].map((i) => (
            <line key={`v${i}`} x1={40 + i * 68} y1="40" x2={40 + i * 68} y2="280" stroke="#f3f4f6" strokeWidth="1" />
          ))}

          {/* Threshold dashed line */}
          <line x1="40" y1="160" x2="380" y2="160" stroke="#059669" strokeWidth="1.5" strokeDasharray="5,4" opacity="0.6" />
          <text x="385" y="164" fontSize="9" fill="#059669" fontWeight="500">Soglia</text>

          {/* Labels */}
          <text x="370" y="295" fontSize="10" fill="#6b7280" textAnchor="end">Impatto →</text>
          <text x="15" y="100" fontSize="10" fill="#6b7280" transform="rotate(-90,15,100)" textAnchor="middle">Rischio Finanziario →</text>

          {/* Axis labels */}
          <text x="50" y="310" fontSize="8" fill="#9ca3af">Basso</text>
          <text x="340" y="310" fontSize="8" fill="#9ca3af">Alto</text>
          <text x="10" y="270" fontSize="8" fill="#9ca3af">Basso</text>
          <text x="10" y="50" fontSize="8" fill="#9ca3af">Alto</text>

          {/* Quadrant labels */}
          <text x="100" y="100" fontSize="9" fill="#d1d5db" fontStyle="italic" textAnchor="middle">Non materiale</text>
          <text x="300" y="100" fontSize="9" fill="#d1d5db" fontStyle="italic" textAnchor="middle">Materiale</text>
          <text x="100" y="240" fontSize="9" fill="#d1d5db" fontStyle="italic" textAnchor="middle">Non rilevante</text>
          <text x="300" y="240" fontSize="9" fill="#d1d5db" fontStyle="italic" textAnchor="middle">Da monitorare</text>

          {/* Dots */}
          {MATERIALITY_POINTS.map((p) => {
            const cx = 40 + (p.x / 100) * 310
            const cy = 280 - (p.y / 100) * 240
            return (
              <g key={p.id}>
                <circle cx={cx} cy={cy} r={p.size} fill={p.color} opacity="0.8" className="hover:opacity-100 transition-opacity cursor-pointer" />
                <circle cx={cx} cy={cy} r={p.size} fill="none" stroke={p.color} strokeWidth="2" opacity="0.3" />
                <text
                  x={cx + p.size + 4}
                  y={cy + 3}
                  fontSize="8"
                  fill="#374151"
                  className="select-none"
                >
                  {p.id}
                </text>
              </g>
            )
          })}
        </svg>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap justify-center gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500" /> Ambientali
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Energetici
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-violet-500" /> Sociali
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-500" /> Ambientali non materiali
        </span>
      </div>
    </div>
  )
}

// ─── Step 4: Carbon Footprint ────────────────────────────────────

function StepCarbon() {
  const total = CARBON_DATA.reduce((acc, d) => acc + d.value, 0)
  const [animate, setAnimate] = useState(false)

  useEffect(() => {
    setAnimate(true)
  }, [])

  return (
    <div className="space-y-6">
      {/* 3 Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {CARBON_DATA.map((scope) => {
          const icons = {
            'Scope 1': Flame,
            'Scope 2': Zap,
            'Scope 3': Truck,
          }
          const Icon = icons[scope.name as keyof typeof icons]
          return (
            <div
              key={scope.name}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center gap-2 mb-3">
                <Icon className="h-4 w-4" style={{ color: scope.color }} />
                <span className="text-sm font-semibold text-gray-700">{scope.name}</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{scope.value.toLocaleString()}</p>
              <p className="text-xs text-gray-500 mt-1">tCO₂e/anno</p>
            </div>
          )
        })}
      </div>

      {/* Stacked bar */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="flex justify-between items-center mb-3">
          <span className="text-sm font-semibold text-gray-700">Totale Emissioni</span>
          <span className="text-lg font-bold text-gray-900">{total.toLocaleString()} tCO₂e/anno</span>
        </div>
        <div className="h-6 bg-gray-100 rounded-full overflow-hidden flex">
          {CARBON_DATA.map((scope, i) => {
            const percentage = (scope.value / total) * 100
            return (
              <div
                key={scope.name}
                className={cn(
                  'h-full transition-all duration-1000 ease-out first:rounded-l-full last:rounded-r-full',
                  i === 0 ? 'rounded-l-full' : '',
                  i === CARBON_DATA.length - 1 ? 'rounded-r-full' : ''
                )}
                style={{
                  width: animate ? `${percentage}%` : '0%',
                  backgroundColor: scope.color,
                }}
              />
            )
          })}
        </div>
        {/* Legend */}
        <div className="flex gap-4 mt-3 text-xs text-gray-500">
          {CARBON_DATA.map((s) => (
            <span key={s.name} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: s.color }} />
              {s.name}: {Math.round((s.value / total) * 100)}%
            </span>
          ))}
        </div>
      </div>

      {/* Benchmark */}
      <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 flex items-start gap-3">
        <TrendingUp className="h-5 w-5 text-orange-500 shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-orange-800">Benchmark settoriale</p>
          <p className="text-orange-700 text-sm mt-1">
            <strong>28% sopra</strong> la media del settore metalmeccanico (2.734 tCO₂e/anno).
            Opportunità di riduzione identificate: efficienza energetica, logistica green, fornitore energia rinnovabile.
          </p>
        </div>
      </div>
    </div>
  )
}

// Helper: icons used in carbon step
function Zap({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <svg className={className} style={style} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  )
}

function Truck({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <svg className={className} style={style} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10 17h4V5H2v12h2" />
      <path d="M20 17h2v-3.34a4 4 0 0 0-1.17-2.83L19 9h-5v8h1" />
      <circle cx="7.5" cy="17.5" r="2.5" />
      <circle cx="17.5" cy="17.5" r="2.5" />
    </svg>
  )
}

// ─── Step 5: Report Generation ──────────────────────────────────

function StepReport() {
  const { visibleLogs, startLogs } = useSequentialLogs()
  const [showResult, setShowResult] = useState(false)
  const hasStarted = useRef(false)

  useEffect(() => {
    if (!hasStarted.current) {
      hasStarted.current = true
      startLogs()
    }
  }, [startLogs])

  useEffect(() => {
    if (visibleLogs.length === LOG_LINES.length) {
      const timer = setTimeout(() => setShowResult(true), 600)
      return () => clearTimeout(timer)
    }
  }, [visibleLogs])

  return (
    <div className="space-y-6">
      {/* Terminal */}
      <div className="bg-gray-900 rounded-xl p-5 font-mono text-sm shadow-lg">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span className="text-gray-500 text-xs ml-2">CSRD Comply Engine v3.2</span>
        </div>
        <div className="space-y-2">
          {LOG_LINES.map((line, i) => {
            const isVisible = visibleLogs.includes(line)
            const isDone = line.includes('OK') || line.includes('completato')
            const isCurrent =
              visibleLogs.length > 0 &&
              visibleLogs[visibleLogs.length - 1] === line &&
              !showResult

            return (
              <div
                key={i}
                className={cn(
                  'flex items-start gap-2 transition-all duration-300',
                  isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-4'
                )}
              >
                {isCurrent ? (
                  <span className="text-emerald-400 text-xs mt-1 animate-pulse">▸</span>
                ) : isVisible ? (
                  <span className="text-emerald-400 text-xs mt-1">✓</span>
                ) : (
                  <span className="text-gray-600 text-xs mt-1">○</span>
                )}
                <span
                  className={cn(
                    isDone && isVisible ? 'text-emerald-300' : 'text-gray-300'
                  )}
                >
                  {line}
                  {isCurrent && <span className="animate-pulse ml-0.5">▊</span>}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Result box */}
      {showResult && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6 text-center animate-slide-in-from-bottom-4">
          <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 className="h-8 w-8 text-emerald-600" />
          </div>
          <h3 className="text-xl font-bold text-emerald-900 mb-2">
            Report CSRD pronto
          </h3>
          <p className="text-emerald-700 font-medium mb-1">
            47 pagine — conforme ESRS 2025
          </p>
          <p className="text-emerald-600 text-sm mb-6">
            Include datapoint quantitativi, narrative e tagging iXBRL.
          </p>

          {/* Fake download buttons */}
          <div className="flex flex-wrap justify-center gap-3 mb-6">
            <Button variant="outline" className="border-emerald-200 text-emerald-700 hover:bg-emerald-50 gap-2" disabled>
              <Download className="h-4 w-4" />
              Scarica PDF
            </Button>
            <Button variant="outline" className="border-emerald-200 text-emerald-700 hover:bg-emerald-50 gap-2" disabled>
              <Tag className="h-4 w-4" />
              Scarica iXBRL
            </Button>
            <Button variant="outline" className="border-emerald-200 text-emerald-700 hover:bg-emerald-50 gap-2" disabled>
              <FileSpreadsheet className="h-4 w-4" />
              Scarica XLSX
            </Button>
          </div>

          <p className="text-xs text-gray-400 mb-6">
            * Pulsanti disabilitati — registrati per abilitare il download
          </p>

          {/* Real CTA */}
          <Link href={SIGNUP_URL}>
            <Button
              size="lg"
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-10 text-base shadow-lg shadow-emerald-200 gap-2"
            >
              <Sparkles className="h-5 w-5" />
              Genera il report della tua azienda →
            </Button>
          </Link>
        </div>
      )}
    </div>
  )
}

// ─── Main Demo Wizard ────────────────────────────────────────────

export default function DemoPage() {
  const [currentStep, setCurrentStep] = useState(1)
  const [direction, setDirection] = useState<'forward' | 'backward'>('forward')

  const goNext = useCallback(() => {
    if (currentStep < 5) {
      setDirection('forward')
      setCurrentStep((s) => s + 1)
    }
  }, [currentStep])

  const goPrev = useCallback(() => {
    if (currentStep > 1) {
      setDirection('backward')
      setCurrentStep((s) => s - 1)
    }
  }, [currentStep])

  const progress = ((currentStep - 1) / (STEPS.length - 1)) * 100

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-white to-white py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-1.5 rounded-full text-sm font-medium mb-4">
            <Sparkles className="h-4 w-4" />
            Demo Interattiva
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
            Prova CSRD Comply
          </h1>
          <p className="text-gray-500 text-sm max-w-md mx-auto">
            Simula l'assessment di sostenibilità per <strong>Rossi Meccanica S.r.l.</strong> in meno di 2 minuti.
          </p>
        </div>

        {/* Progress bar */}
        <div className="mb-8">
          {/* Step indicators */}
          <div className="flex justify-between mb-3">
            {STEPS.map((step) => {
              const Icon = step.icon
              const isActive = currentStep === step.id
              const isCompleted = currentStep > step.id
              return (
                <div key={step.id} className="flex flex-col items-center">
                  <div
                    className={cn(
                      'w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 border-2',
                      isActive
                        ? 'bg-emerald-600 border-emerald-600 text-white shadow-md shadow-emerald-200 scale-110'
                        : isCompleted
                          ? 'bg-emerald-100 border-emerald-300 text-emerald-600'
                          : 'bg-white border-gray-200 text-gray-400'
                    )}
                  >
                    {isCompleted ? (
                      <CheckCircle2 className="h-5 w-5" />
                    ) : (
                      <Icon className="h-4 w-4" />
                    )}
                  </div>
                  <span
                    className={cn(
                      'text-xs mt-1.5 font-medium transition-colors hidden sm:block',
                      isActive ? 'text-emerald-700' : isCompleted ? 'text-emerald-500' : 'text-gray-400'
                    )}
                  >
                    {step.label}
                  </span>
                </div>
              )
            })}
          </div>

          {/* Progress track */}
          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Step content */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 md:p-8 mb-6">
          {/* Step title */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-1">
              {(() => {
                const Icon = STEPS[currentStep - 1].icon
                return <Icon className="h-5 w-5 text-emerald-600" />
              })()}
              <h2 className="text-lg font-bold text-gray-900">
                {currentStep === 1 && 'Profilo Azienda'}
                {currentStep === 2 && 'CSRD Readiness Score'}
                {currentStep === 3 && 'Doppia Materialità'}
                {currentStep === 4 && 'Carbon Footprint'}
                {currentStep === 5 && 'Report Generato'}
              </h2>
            </div>
            <p className="text-sm text-gray-500 mt-1">
              {currentStep === 1 && 'I dati di Rossi Meccanica S.r.l. sono già stati importati dal tuo CRM.'}
              {currentStep === 2 && 'Valutazione preliminare del livello di conformità CSRD.'}
              {currentStep === 3 && 'Analisi di materialità doppia: impatto e rischio finanziario.'}
              {currentStep === 4 && "Calcolo dell'impronta carbonio sugli Scope 1, 2 e 3."}
              {currentStep === 5 && "Report finale generato dall'AI Engine di CSRD Comply."}
            </p>
          </div>

          {/* Animated content wrapper */}
          <div className="relative min-h-[360px]">
            <div
              key={currentStep}
              className={cn(
                'transition-all duration-400',
                direction === 'forward' ? 'animate-slide-in-from-right-8' : 'animate-slide-in-from-left-8'
              )}
            >
              {currentStep === 1 && <StepProfile onNext={goNext} />}
              {currentStep === 2 && <StepReadiness />}
              {currentStep === 3 && <StepMateriality />}
              {currentStep === 4 && <StepCarbon />}
              {currentStep === 5 && <StepReport />}
            </div>
          </div>
        </div>

        {/* Navigation buttons */}
        <div className="flex justify-between">
          <div>
            {currentStep > 1 && (
              <Button variant="outline" onClick={goPrev} className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Indietro
              </Button>
            )}
          </div>
          <div>
            {currentStep < 5 && (
              <Button onClick={goNext} className="bg-emerald-600 hover:bg-emerald-700 text-white gap-2">
                Avanti
                <ChevronRight className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-10">
          <p className="text-sm text-gray-400">
            Questa è una demo interattiva. I dati mostrati sono simulati.
          </p>
          <Link
            href={SIGNUP_URL}
            className="inline-flex items-center gap-1.5 text-emerald-600 hover:text-emerald-700 font-medium text-sm mt-2 transition-colors"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            Crea il tuo account e inizia subito
          </Link>
        </div>
      </div>
    </div>
  )
}
