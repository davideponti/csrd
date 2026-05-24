'use client'

import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { Button } from '@/components/ui'
import { Badge } from '@/components/ui'
import { Progress } from '@/components/ui'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui'
import { Input } from '@/components/ui'
import { assessments, emissions, reports } from '@/lib/api'
import {
  LayoutDashboard, ClipboardCheck, Leaf, FileText, Settings, Bell, User,
  TrendingUp, TrendingDown, AlertTriangle, CheckCircle2, Target, Brain,
  Calendar, ChevronRight, Sparkles, MessageCircle, X, Send, Loader2,
  BarChart3, Layers, Plus, ArrowUp, ArrowDown, Minus, Clock,
  ExternalLink, Activity, Shield, Zap
} from 'lucide-react'

// ── Types ──────────────────────────────────────────────────────

interface DashboardData {
  readinessScore: number
  readinessColor: 'red' | 'yellow' | 'green'
  emissionsSummary: {
    scope1: number
    scope2: number
    scope3: number
    total: number
    trend: 'up' | 'down' | 'stable'
    yoyChange: number
    lastYears: number[]
  }
  deadlines: {
    id: string
    title: string
    date: string
    daysRemaining: number
    severity: 'critical' | 'warning' | 'info'
    category: string
  }[]
  materialityMatrix: {
    impactScore: number
    financialScore: number
    isMaterial: boolean
    topic: string
    count: number
  }[]
  quickActions: {
    id: string
    label: string
    description: string
    href: string
    icon: string
    priority: 'high' | 'medium' | 'low'
    completed: boolean
  }[]
  regulatoryUpdates: {
    id: string
    title: string
    summary: string
    date: string
    impact: 'CRITICAL' | 'MODERATE' | 'INFO'
    isNew: boolean
  }[]
  gapAnalysisStatus: {
    total: number
    complete: number
    partial: number
    missing: number
    completionPercentage: number
  }
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

// ── Mock data fallback ────────────────────────────────────────

const MOCK_DASHBOARD: DashboardData = {
  readinessScore: 32,
  readinessColor: 'red',
  emissionsSummary: {
    scope1: 105,
    scope2: 75,
    scope3: 420,
    total: 600,
    trend: 'down',
    yoyChange: -8.5,
    lastYears: [650, 620, 600],
  },
  deadlines: [
    { id: 'd1', title: 'Completamento Assessment Materialità', date: '2026-06-15', daysRemaining: 23, severity: 'critical', category: 'Assessment' },
    { id: 'd2', title: 'Raccolta Dati Emissioni Scope 3', date: '2026-07-31', daysRemaining: 69, severity: 'warning', category: 'Emissions' },
    { id: 'd3', title: 'Generazione Report CSRD Annuale', date: '2026-09-30', daysRemaining: 130, severity: 'info', category: 'Reporting' },
    { id: 'd4', title: 'Filing Report a ESAP', date: '2027-04-30', daysRemaining: 342, severity: 'info', category: 'Filing' },
  ],
  materialityMatrix: [
    { impactScore: 4.2, financialScore: 3.8, isMaterial: true, topic: 'ESRS E1', count: 12 },
    { impactScore: 3.5, financialScore: 2.1, isMaterial: true, topic: 'ESRS E2', count: 5 },
    { impactScore: 2.8, financialScore: 4.0, isMaterial: true, topic: 'ESRS S1', count: 8 },
    { impactScore: 1.5, financialScore: 2.0, isMaterial: false, topic: 'ESRS E3', count: 3 },
    { impactScore: 3.2, financialScore: 2.5, isMaterial: true, topic: 'ESRS G1', count: 6 },
  ],
  quickActions: [
    { id: 'qa1', label: 'Completa Gap Analysis', description: 'Identifica i datapoint ESRS mancanti', href: '/assessment', icon: 'AlertTriangle', priority: 'high', completed: false },
    { id: 'qa2', label: 'Inserisci Dati Emissioni', description: 'Scope 1, 2 e 3 per l\'anno corrente', href: '/emissions', icon: 'Leaf', priority: 'high', completed: false },
    { id: 'qa3', label: 'Avvia Assessment Materialità', description: 'Valutazione IRO e doppia materialità', href: '/assessment', icon: 'ClipboardCheck', priority: 'medium', completed: true },
    { id: 'qa4', label: 'Genera Report CSRD', description: 'Report annuale con tagging iXBRL', href: '/reports', icon: 'FileText', priority: 'medium', completed: false },
  ],
  regulatoryUpdates: [
    { id: 'ru1', title: 'EFARG pubblica nuove linee guida su ESRS E5', summary: 'Nuove indicazioni per il reporting sull\'economia circolare e gestione rifiuti.', date: '2026-05-15', impact: 'MODERATE', isNew: true },
    { id: 'ru2', title: 'Omnibus Directive - Chiarimenti su threshold', summary: 'La Commissione EU chiarisce le soglie per le PMI esonerate dal reporting.', date: '2026-05-10', impact: 'INFO', isNew: true },
    { id: 'ru3', title: 'ESMA aggiorna tassonomia XBRL per ESRS Set 2', summary: 'Nuovi elementi di tagging per report 2026 con impatti su E4 e S2.', date: '2026-04-28', impact: 'CRITICAL', isNew: false },
  ],
  gapAnalysisStatus: {
    total: 320,
    complete: 45,
    partial: 120,
    missing: 155,
    completionPercentage: 14,
  },
}

// ── Icon map ──────────────────────────────────────────────────

const ACTION_ICONS: Record<string, React.ReactNode> = {
  AlertTriangle: <AlertTriangle className="h-4 w-4" />,
  Leaf: <Leaf className="h-4 w-4" />,
  ClipboardCheck: <ClipboardCheck className="h-4 w-4" />,
  FileText: <FileText className="h-4 w-4" />,
}

// ── Helper Components ──────────────────────────────────────────

function SparklineChart({ data, color = 'green' }: { data: number[]; color?: string }) {
  if (!data.length) return null
  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1
  const w = 60
  const h = 24
  const points = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`).join(' ')

  return (
    <svg width={w} height={h} className="inline-block ml-2">
      <polyline
        points={points}
        fill="none"
        stroke={color === 'green' ? '#22c55e' : color === 'red' ? '#ef4444' : '#3b82f6'}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function DeadlinesTimeline({ deadlines }: { deadlines: DashboardData['deadlines'] }) {
  const sorted = [...deadlines].sort((a, b) => a.daysRemaining - b.daysRemaining)
  return (
    <div className="space-y-2">
      {sorted.map((d) => (
        <div key={d.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 transition-colors">
          <div className={`w-2 h-2 rounded-full shrink-0 ${
            d.severity === 'critical' ? 'bg-red-500' :
            d.severity === 'warning' ? 'bg-amber-500' : 'bg-blue-500'
          }`} />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">{d.title}</p>
            <p className="text-xs text-muted-foreground">{d.category} · {d.date}</p>
          </div>
          <Badge variant={
            d.severity === 'critical' ? 'destructive' :
            d.severity === 'warning' ? 'warning' : 'secondary'
          } className="shrink-0 text-xs">
            {d.daysRemaining <= 0 ? 'Scaduto' : `${d.daysRemaining}gg`}
          </Badge>
        </div>
      ))}
    </div>
  )
}

function MiniScatterPlot({ data }: { data: DashboardData['materialityMatrix'] }) {
  if (!data.length) return <p className="text-xs text-muted-foreground text-center py-4">Nessun dato</p>

  const w = 180, h = 150, pad = 20
  const plotW = w - pad * 2, plotH = h - pad * 2

  return (
    <svg width={w} height={h} className="mx-auto">
      {/* Quadrants */}
      <rect x={pad + plotW / 2} y={pad} width={plotW / 2} height={plotH / 2} fill="#fef2f2" opacity={0.3} />
      <rect x={pad} y={pad + plotH / 2} width={plotW / 2} height={plotH / 2} fill="#fef2f2" opacity={0.3} />
      <rect x={pad + plotW / 2} y={pad + plotH / 2} width={plotW / 2} height={plotH / 2} fill="#fef2f2" opacity={0.5} />

      {/* Threshold lines */}
      <line x1={pad + plotW / 2} y1={pad} x2={pad + plotW / 2} y2={pad + plotH} stroke="#ef4444" strokeWidth={1} strokeDasharray="2,2" />
      <line x1={pad} y1={pad + plotH / 2} x2={pad + plotW} y2={pad + plotH / 2} stroke="#ef4444" strokeWidth={1} strokeDasharray="2,2" />

      {/* Labels */}
      <text x={pad + plotW / 2} y={h - 2} textAnchor="middle" fill="#6b7280" fontSize={7}>Financial</text>
      <text x={4} y={pad + plotH / 2} textAnchor="middle" fill="#6b7280" fontSize={7} transform={`rotate(-90, 4, ${pad + plotH / 2})`}>Impact</text>

      {/* Data points */}
      {data.map((d, i) => {
        const cx = pad + (d.financialScore / 5) * plotW
        const cy = pad + plotH - (d.impactScore / 5) * plotH
        const r = Math.min(12, Math.max(4, d.count * 1.5))
        return (
          <circle key={i} cx={cx} cy={cy} r={r}
            fill={d.isMaterial ? '#ef4444' : '#22c55e'} opacity={0.6}
            className="hover:opacity-100 transition-opacity cursor-pointer"
          >
            <title>{`${d.topic}: Impact ${d.impactScore}, Financial ${d.financialScore} (${d.count} IRO)`}</title>
          </circle>
        )
      })}
    </svg>
  )
}

function RegulatoryUpdateCard({ update }: { update: DashboardData['regulatoryUpdates'][0] }) {
  const impactColor = {
    CRITICAL: 'destructive' as const,
    MODERATE: 'warning' as const,
    INFO: 'secondary' as const,
  }
  return (
    <div className="p-3 rounded-lg border hover:bg-muted/50 transition-colors cursor-pointer">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant={impactColor[update.impact]} className="text-[10px]">{update.impact}</Badge>
            {update.isNew && <Badge variant="info" className="text-[10px]">NEW</Badge>}
          </div>
          <p className="text-sm font-medium text-foreground truncate">{update.title}</p>
          <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{update.summary}</p>
        </div>
      </div>
      <p className="text-[10px] text-muted-foreground mt-2">{update.date}</p>
    </div>
  )
}

function AiChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: 'Ciao! Sono il tuo Advisor CSRD. Come posso aiutarti oggi?', timestamp: new Date() },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return
    const userMsg: ChatMessage = { role: 'user', content: input.trim(), timestamp: new Date() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    // Simulate AI response
    setTimeout(() => {
      const responses = [
        'In base ai dati attuali, il tuo progresso complessivo è del 32%. Ti consiglio di iniziare dalla Gap Analysis per identificare i datapoint mancanti.',
        'Per la tua azienda (settore manifatturiero), i topic ESRS più rilevanti sono E1 (Climate Change) e S1 (Own Workforce).',
        'La scadenza più vicina è il completamento dell\'assessment materialità tra 23 giorni. Vuoi che ti aiuti a prepararlo?',
        'I benchmark di settore mostrano che le emissioni Scope 1 sono in linea con aziende comparabili. Ottimo lavoro!',
        'Per il filing del report, ricorda che devi completare la validazione iXBRL prima dell\'invio a ESAP.',
      ]
      const resp = responses[Math.floor(Math.random() * responses.length)]
      setMessages(prev => [...prev, { role: 'assistant', content: resp, timestamp: new Date() }])
      setLoading(false)
    }, 1500)
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-primary text-primary-foreground shadow-lg hover:bg-primary/90 transition-all hover:scale-105 flex items-center justify-center"
      >
        <MessageCircle className="h-6 w-6" />
      </button>
    )
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 h-[500px] bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-border flex flex-col z-50">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-primary/5 rounded-t-2xl">
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-primary" />
          <div>
            <p className="text-sm font-semibold text-foreground">Advisor CSRD</p>
            <p className="text-xs text-muted-foreground">AI Assistant</p>
          </div>
        </div>
        <button onClick={() => setOpen(false)} className="p-1 rounded-lg hover:bg-muted text-muted-foreground">
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-3 rounded-xl text-sm ${
              msg.role === 'user'
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-foreground'
            }`}>
              {msg.content}
              <p className="text-[10px] mt-1 opacity-60">
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-xl p-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-border">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Fai una domanda sul tuo CSRD..."
            className="flex-1 text-sm"
          />
          <Button size="icon" onClick={handleSend} disabled={!input.trim() || loading}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}

// ── Main Component ─────────────────────────────────────────────

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData>(MOCK_DASHBOARD)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setLoading(true)
    setError(null)
    try {
      // Try to load real data from API
      const [emissionsSummary, gapAnalysis, assessmentList, reportsList] = await Promise.allSettled([
        emissions.getSummary(),
        assessments.list(),
        assessments.list(),
        reports.list(),
      ])

      // For now use mock data with real data where available
      const newData = { ...MOCK_DASHBOARD }

      if (emissionsSummary.status === 'fulfilled' && emissionsSummary.value) {
        const es = emissionsSummary.value.summary
        newData.emissionsSummary = {
          ...newData.emissionsSummary,
          scope1: es.scope1 || 0,
          scope2: es.scope2 || 0,
          scope3: es.scope3 || 0,
          total: es.total || 0,
        }
      }

      setData(newData)
    } catch (err: any) {
      setError(err.message)
      // Fall back to mock data
      setData(MOCK_DASHBOARD)
    }
    setLoading(false)
  }

  const readinessColorClass = {
    red: 'text-red-500',
    yellow: 'text-amber-500',
    green: 'text-green-500',
  }

  const readinessBgColor = {
    red: 'bg-red-500',
    yellow: 'bg-amber-500',
    green: 'bg-green-500',
  }

  const highPriorityActions = data.quickActions.filter(a => a.priority === 'high' && !a.completed)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Dashboard</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Panoramica del tuo stato di conformità CSRD
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={loadDashboardData} disabled={loading}>
            <Activity className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Aggiorna
          </Button>
          <Button size="sm">
            <Calendar className="h-4 w-4 mr-2" />
            Report Annuale
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-destructive/10 text-destructive rounded-lg text-sm border border-destructive/20">
          {error}
        </div>
      )}

      {/* ── Row 1: Readiness Score + Emissions Overview ─────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 1. CSRD Readiness Score */}
        <Card className="lg:col-span-1">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">CSRD Readiness Score</CardTitle>
              <Shield className={`h-4 w-4 ${readinessColorClass[data.readinessColor]}`} />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-center py-4">
              <div className="relative w-28 h-28 mx-auto mb-3">
                <svg viewBox="0 0 100 100" className="transform -rotate-90 w-full h-full">
                  <circle cx="50" cy="50" r="42" fill="none" stroke="#e5e7eb" strokeWidth="8" />
                  <circle
                    cx="50" cy="50" r="42"
                    fill="none"
                    stroke={data.readinessColor === 'red' ? '#ef4444' : data.readinessColor === 'yellow' ? '#f59e0b' : '#22c55e'}
                    strokeWidth="8"
                    strokeDasharray={`${(data.readinessScore / 100) * 264} 264`}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-3xl font-bold text-foreground">{data.readinessScore}%</span>
                </div>
              </div>
              <p className={`text-xs font-medium ${readinessColorClass[data.readinessColor]}`}>
                {data.readinessScore < 30 ? 'Critico — Azioni richieste urgenti' :
                 data.readinessScore < 70 ? 'In Progress — Continuare il lavoro' :
                 'Buono — Compliance in linea'}
              </p>
            </div>

            {/* Gap breakdown */}
            <div className="space-y-2 pt-3 border-t border-border">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Gap Analysis</span>
                <span className="font-medium">{data.gapAnalysisStatus.completionPercentage}%</span>
              </div>
              <Progress value={data.gapAnalysisStatus.completionPercentage} className="h-1.5" />
              <div className="flex justify-between text-[10px] text-muted-foreground">
                <span className="text-green-500">{data.gapAnalysisStatus.complete} complete</span>
                <span className="text-amber-500">{data.gapAnalysisStatus.partial} parziali</span>
                <span className="text-red-500">{data.gapAnalysisStatus.missing} mancanti</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 2. Emissions Overview */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">Emissioni GHG</CardTitle>
              <div className="flex items-center gap-2">
                <span className={`text-xs font-medium flex items-center gap-1 ${
                  data.emissionsSummary.trend === 'down' ? 'text-green-500' :
                  data.emissionsSummary.trend === 'up' ? 'text-red-500' : 'text-muted-foreground'
                }`}>
                  {data.emissionsSummary.trend === 'down' ? <TrendingDown className="h-3 w-3" /> :
                   data.emissionsSummary.trend === 'up' ? <TrendingUp className="h-3 w-3" /> :
                   <Minus className="h-3 w-3" />}
                  {Math.abs(data.emissionsSummary.yoyChange).toFixed(1)}% YoY
                </span>
                <SparklineChart data={data.emissionsSummary.lastYears} color={data.emissionsSummary.trend === 'down' ? 'green' : 'red'} />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-3 mb-4">
              <MetricCard value={data.emissionsSummary.scope1} label="Scope 1" unit="tCO₂e" color="text-red-500" />
              <MetricCard value={data.emissionsSummary.scope2} label="Scope 2" unit="tCO₂e" color="text-blue-500" />
              <MetricCard value={data.emissionsSummary.scope3} label="Scope 3" unit="tCO₂e" color="text-amber-500" />
              <MetricCard value={data.emissionsSummary.total} label="Totale" unit="tCO₂e" color="text-foreground" bold />
            </div>
            {/* Mini bar chart / scope comparison */}
            <div className="flex items-end gap-1 h-16 pt-2 border-t border-border">
              {[
                { label: 'Scope 1', value: data.emissionsSummary.scope1, color: 'bg-red-500' },
                { label: 'Scope 2', value: data.emissionsSummary.scope2, color: 'bg-blue-500' },
                { label: 'Scope 3', value: data.emissionsSummary.scope3, color: 'bg-amber-500' },
              ].map((s) => {
                const maxVal = Math.max(data.emissionsSummary.scope1, data.emissionsSummary.scope2, data.emissionsSummary.scope3, 1)
                const h = (s.value / maxVal) * 100
                return (
                  <div key={s.label} className="flex-1 flex flex-col items-center gap-1">
                    <span className="text-[10px] text-muted-foreground">{s.value.toFixed(0)}</span>
                    <div className="w-full bg-muted rounded-full h-12 flex items-end overflow-hidden">
                      <div className={`w-full ${s.color} rounded-full transition-all duration-500`} style={{ height: `${h}%` }} />
                    </div>
                    <span className="text-[10px] text-muted-foreground">{s.label}</span>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── Row 2: Deadlines + Matrix Mini + Quick Actions ───── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 3. Upcoming Deadlines */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">Prossime Scadenze</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <DeadlinesTimeline deadlines={data.deadlines} />
            <div className="mt-3 pt-2 border-t border-border">
              <a href="/assessment" className="text-xs text-primary hover:underline flex items-center gap-1">
                Vedi tutte le scadenze <ChevronRight className="h-3 w-3" />
              </a>
            </div>
          </CardContent>
        </Card>

        {/* 4. Materiality Matrix Mini */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">Matrice Materialità</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <MiniScatterPlot data={data.materialityMatrix} />
            <div className="flex items-center justify-center gap-4 mt-2">
              <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
                {data.materialityMatrix.filter(d => d.isMaterial).length} Materiali
              </span>
              <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
                {data.materialityMatrix.filter(d => !d.isMaterial).length} Non materiali
              </span>
            </div>
            <div className="mt-3 pt-2 border-t border-border text-center">
              <a href="/assessment/materiality" className="text-xs text-primary hover:underline flex items-center justify-center gap-1">
                Vai alla matrice completa <ChevronRight className="h-3 w-3" />
              </a>
            </div>
          </CardContent>
        </Card>

        {/* 5. Quick Actions */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">Azioni Rapide</CardTitle>
              {highPriorityActions.length > 0 && (
                <Badge variant="destructive" className="text-[10px]">{highPriorityActions.length} da fare</Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.quickActions.map((action) => (
                <a
                  key={action.id}
                  href={action.href}
                  className={`flex items-center gap-3 p-2 rounded-lg transition-colors ${
                    action.completed
                      ? 'opacity-50 cursor-default'
                      : action.priority === 'high'
                        ? 'bg-red-50 dark:bg-red-950/20 hover:bg-red-100 dark:hover:bg-red-900/30'
                        : 'hover:bg-muted'
                  }`}
                >
                  <span className={`${action.completed ? 'text-green-500' : action.priority === 'high' ? 'text-red-500' : 'text-muted-foreground'}`}>
                    {ACTION_ICONS[action.icon] || <Zap className="h-4 w-4" />}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium truncate ${action.completed ? 'text-green-500' : 'text-foreground'}`}>
                      {action.label}
                    </p>
                    <p className="text-[10px] text-muted-foreground truncate">{action.description}</p>
                  </div>
                  {action.completed ? (
                    <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                  )}
                </a>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── Row 3: Regulatory Updates ─────────────────────────── */}
      <div className="grid grid-cols-1 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">Aggiornamenti Normativi</CardTitle>
              <Bell className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {data.regulatoryUpdates.map((update) => (
                <RegulatoryUpdateCard key={update.id} update={update} />
              ))}
            </div>
            <div className="mt-3 pt-2 border-t border-border">
              <a href="/settings" className="text-xs text-primary hover:underline flex items-center gap-1">
                Gestisci notifiche <ChevronRight className="h-3 w-3" />
              </a>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── AI Chat Widget ──────────────────────────────────── */}
      <AiChatWidget />
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────

function MetricCard({ value, label, unit, color, bold = false }: {
  value: number
  label: string
  unit?: string
  color?: string
  bold?: boolean
}) {
  return (
    <div className="text-center">
      <p className={`${bold ? 'text-xl' : 'text-lg'} font-bold ${color || 'text-foreground'}`}>
        {value.toFixed(1)}
      </p>
      <p className="text-[10px] text-muted-foreground">{label}</p>
      {unit && <p className="text-[9px] text-muted-foreground">{unit}</p>}
    </div>
  )
}
