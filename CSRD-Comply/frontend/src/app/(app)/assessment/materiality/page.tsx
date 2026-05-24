'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { Button } from '@/components/ui'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { Badge } from '@/components/ui'
import { Progress } from '@/components/ui'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui'
import { Input } from '@/components/ui'
import { assessments } from '@/lib/api'
import {
  BarChart3, AlertTriangle, FileText, LayoutDashboard, Layers, Target,
  ChevronLeft, ChevronRight, Save, CheckCircle2, BrainCircuit, Lightbulb,
  TrendingUp, TrendingDown, Minus, Info, ArrowUp, ArrowDown,
  Maximize2, Sparkles, Download, Share2, MessageCircle, Send, X,
  ChevronDown, ChevronUp, Filter, RefreshCw, Loader2
} from 'lucide-react'

// ── Types ──────────────────────────────────────────────────────

interface ScoreItem {
  id: string
  datapoint_id: string
  standard_ref: string
  disclosure_requirement: string
  impact_scale: number | null
  impact_scope: number | null
  impact_irremediability: number | null
  impact_likelihood: number | null
  financial_magnitude: number | null
  financial_likelihood: number | null
  total_impact_score: number | null
  total_financial_score: number | null
  is_material: boolean
  rationale: string | null
}

interface AiFollowup {
  type: string
  question: string
  suggestion: string
}

interface MatrixItem {
  datapoint_id: string
  datapoint_name: string
  standard_ref: string
  impact_score: number
  financial_score: number
  is_material: boolean
  rationale: string | null
}

interface ReportData {
  report_title: string
  company_name: string
  reporting_year: number
  assessment_date: string
  executive_summary: string
  sections: any[]
  scores_summary: {
    total_datapoints: number
    scored_datapoints: number
    material_datapoints: number
    average_impact_score: number
    average_financial_score: number
    material_topics: string[]
    completion_percentage: number
  }
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

// ── ESRS Topics Config ─────────────────────────────────────────

const ESRS_TOPICS = [
  { id: 'ESRS E1', label: 'Climate Change', category: 'Environmental', color: 'bg-green-500' },
  { id: 'ESRS E2', label: 'Pollution', category: 'Environmental', color: 'bg-green-400' },
  { id: 'ESRS E3', label: 'Water & Marine', category: 'Environmental', color: 'bg-cyan-500' },
  { id: 'ESRS E4', label: 'Biodiversity', category: 'Environmental', color: 'bg-emerald-500' },
  { id: 'ESRS E5', label: 'Circular Economy', category: 'Environmental', color: 'bg-teal-500' },
  { id: 'ESRS S1', label: 'Own Workforce', category: 'Social', color: 'bg-blue-500' },
  { id: 'ESRS S2', label: 'Value Chain Workers', category: 'Social', color: 'bg-blue-400' },
  { id: 'ESRS S3', label: 'Affected Communities', category: 'Social', color: 'bg-indigo-500' },
  { id: 'ESRS S4', label: 'Consumers & End-users', category: 'Social', color: 'bg-violet-500' },
  { id: 'ESRS G1', label: 'Business Conduct', category: 'Governance', color: 'bg-purple-500' },
]

const CATEGORY_COLORS: Record<string, string> = {
  Environmental: 'border-l-green-500',
  Social: 'border-l-blue-500',
  Governance: 'border-l-purple-500',
}

// ── Scoring Dimensions Config ─────────────────────────────────

const IMPACT_DIMENSIONS = [
  {
    key: 'impact_scale' as const,
    label: 'Scale (Scala)',
    description: 'Quanto è grave? (1=Minimo, 5=Catastrofico)',
    labels: ['Minimo', 'Minore', 'Moderato', 'Significativo', 'Catastrofico'],
    color: 'from-red-400 to-red-600',
  },
  {
    key: 'impact_scope' as const,
    label: 'Scope (Portata)',
    description: 'Quanto è esteso? (1=Locale, 5=Globale)',
    labels: ['Locale', 'Regionale', 'Nazionale', 'EU', 'Globale'],
    color: 'from-orange-400 to-orange-600',
  },
  {
    key: 'impact_irremediability' as const,
    label: 'Irreversibilità',
    description: 'Quanto è reversibile? (1=Facile, 5=Irreversibile)',
    labels: ['Facile', 'Lento', 'Difficile', 'Molto lento', 'Irreversibile'],
    color: 'from-amber-400 to-amber-600',
  },
  {
    key: 'impact_likelihood' as const,
    label: 'Probabilità (Impact)',
    description: 'Probabilità che si verifichi (1=Raro, 5=Certo)',
    labels: ['Raro', 'Improbabile', 'Possibile', 'Probabile', 'Certo'],
    color: 'from-yellow-400 to-yellow-600',
  },
]

const FINANCIAL_DIMENSIONS = [
  {
    key: 'financial_magnitude' as const,
    label: 'Magnitudine Finanziaria',
    description: 'Impatto economico potenziale (1=Trascurabile, 5=Critico)',
    labels: ['Trascurabile', 'Minore', 'Moderato', 'Significativo', 'Critico'],
    color: 'from-blue-400 to-blue-600',
  },
  {
    key: 'financial_likelihood' as const,
    label: 'Probabilità (Financial)',
    description: 'Probabilità impatto finanziario (1=Raro, 5=Certo)',
    labels: ['Raro', 'Improbabile', 'Possibile', 'Probabile', 'Certo'],
    color: 'from-cyan-400 to-cyan-600',
  },
]

// ── Sub-components ─────────────────────────────────────────────

function TopicSidebar({
  scores,
  currentIndex,
  onNavigate,
  filter,
  setFilter,
}: {
  scores: ScoreItem[]
  currentIndex: number
  onNavigate: (idx: number) => void
  filter: string
  setFilter: (f: string) => void
}) {
  // Group scores by topic
  const topicStats = ESRS_TOPICS.map(topic => {
    const topicScores = scores.filter(s => s.standard_ref?.startsWith(topic.id))
    const scored = topicScores.filter(s => s.total_impact_score != null).length
    const material = topicScores.filter(s => s.is_material).length
    return {
      ...topic,
      total: topicScores.length,
      scored,
      material,
      completion: topicScores.length > 0 ? (scored / topicScores.length) * 100 : 0,
    }
  }).filter(t => t.total > 0)

  const filtered = filter ? topicStats.filter(t => t.category === filter) : topicStats

  return (
    <div className="space-y-1.5">
      {/* Filter */}
      <div className="flex gap-1 mb-3">
        {['', 'Environmental', 'Social', 'Governance'].map(cat => (
          <button
            key={cat}
            onClick={() => setFilter(cat === filter ? '' : cat)}
            className={`px-2 py-1 text-[10px] rounded-full border transition-colors ${
              filter === cat
                ? 'bg-primary text-primary-foreground border-primary'
                : 'border-input hover:bg-muted text-muted-foreground'
            }`}
          >
            {cat || 'Tutti'}
          </button>
        ))}
      </div>

      {/* Topic list */}
      {filtered.map((topic, ti) => {
        const firstIdx = scores.findIndex(s => s.standard_ref?.startsWith(topic.id))
        const isActive = firstIdx <= currentIndex && firstIdx + topic.total > currentIndex
        return (
          <button
            key={topic.id}
            onClick={() => firstIdx >= 0 && onNavigate(firstIdx)}
            disabled={topic.total === 0}
            className={`w-full text-left p-2 rounded-lg transition-all border-l-2 ${
              isActive
                ? 'bg-primary/10 border-l-primary shadow-sm'
                : topic.completion === 100
                  ? 'bg-green-50 dark:bg-green-950/20 border-l-green-500'
                  : topic.completion > 0
                    ? 'bg-muted border-l-transparent hover:border-l-muted-foreground'
                    : 'bg-muted/50 border-l-transparent opacity-60'
            }`}
          >
            <div className="flex items-center justify-between mb-0.5">
              <span className={`text-xs font-medium ${
                isActive ? 'text-primary' :
                topic.completion === 100 ? 'text-green-700 dark:text-green-300' :
                'text-foreground'
              }`}>
                {topic.id}
              </span>
              {topic.completion === 100 ? (
                <CheckCircle2 className="h-3 w-3 text-green-500" />
              ) : (
                <span className="text-[10px] text-muted-foreground">
                  {topic.scored}/{topic.total}
                </span>
              )}
            </div>
            <p className="text-[10px] text-muted-foreground truncate">{topic.label}</p>
            {topic.total > 0 && topic.completion < 100 && (
              <Progress value={topic.completion} className="h-0.5 mt-1" />
            )}
            {topic.material > 0 && (
              <Badge variant="destructive" className="text-[8px] px-1 h-3 mt-0.5">
                {topic.material} material
              </Badge>
            )}
          </button>
        )
      })}

      {filtered.length === 0 && (
        <p className="text-[10px] text-muted-foreground text-center py-4">
          Nessun topic {filter ? `${filter.toLowerCase()}` : ''} disponibile
        </p>
      )}
    </div>
  )
}

function AiSuggestionPanel({
  score,
  onGetAiFollowup,
  aiFollowups,
  aiLoading,
}: {
  score: ScoreItem | null
  onGetAiFollowup: () => void
  aiFollowups: AiFollowup[]
  aiLoading: boolean
}) {
  if (!score) {
    return (
      <div className="text-center py-8">
        <BrainCircuit className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
        <p className="text-xs text-muted-foreground">Seleziona un IRO per vedere suggerimenti AI</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* AI Button */}
      <Button
        variant="outline"
        size="sm"
        className="w-full"
        onClick={onGetAiFollowup}
        disabled={aiLoading}
      >
        {aiLoading ? (
          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
        ) : (
          <BrainCircuit className="h-4 w-4 mr-2 text-purple-500" />
        )}
        Analisi AI
      </Button>

      {/* Quick scores */}
      <div className="p-3 bg-muted rounded-lg space-y-2">
        <p className="text-xs font-medium text-muted-foreground">Punteggi Correnti</p>
        <div className="flex justify-between items-center">
          <span className="text-xs">Impact Score</span>
          <span className={`text-sm font-bold ${
            score.total_impact_score && score.total_impact_score >= 3 ? 'text-red-500' : 'text-green-500'
          }`}>
            {score.total_impact_score?.toFixed(1) || '-'}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-xs">Financial Score</span>
          <span className={`text-sm font-bold ${
            score.total_financial_score && score.total_financial_score >= 3 ? 'text-red-500' : 'text-green-500'
          }`}>
            {score.total_financial_score?.toFixed(1) || '-'}
          </span>
        </div>
        <div className="pt-2 border-t border-border">
          <div className="flex justify-between items-center">
            <span className="text-xs">Double Materiality</span>
            <span className={`text-sm font-bold ${
              score.is_material ? 'text-red-500' : 'text-green-500'
            }`}>
              {Math.max(score.total_impact_score || 0, score.total_financial_score || 0).toFixed(1)}
            </span>
          </div>
        </div>
      </div>

      {/* Benchmark comparison */}
      <div className="p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <div className="flex items-center gap-2 mb-2">
          <BarChart3 className="h-3 w-3 text-blue-500" />
          <span className="text-xs font-medium text-blue-700 dark:text-blue-300">Benchmark Settore</span>
        </div>
        <div className="space-y-1.5">
          <div className="flex justify-between text-[10px]">
            <span className="text-muted-foreground">Impact medio settore</span>
            <span className="font-medium">2.8</span>
          </div>
          <div className="flex justify-between text-[10px]">
            <span className="text-muted-foreground">Financial medio settore</span>
            <span className="font-medium">2.5</span>
          </div>
          <div className="flex justify-between text-[10px]">
            <span className="text-muted-foreground">Tua valutazione Impatto</span>
            <span className={`font-medium ${(score.total_impact_score || 0) > 2.8 ? 'text-red-500' : 'text-green-500'}`}>
              {score.total_impact_score?.toFixed(1) || '-'}
              {(score.total_impact_score || 0) > 2.8 ? <ArrowUp className="h-3 w-3 inline ml-1" /> : <ArrowDown className="h-3 w-3 inline ml-1" />}
            </span>
          </div>
        </div>
      </div>

      {/* AI Followup suggestions */}
      {aiFollowups.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground">Suggerimenti AI</p>
          {aiFollowups.map((fu, idx) => (
            <div key={idx} className={`p-2 rounded-lg border text-xs ${
              fu.type === 'deep_dive' ? 'bg-purple-50 dark:bg-purple-950/20 border-purple-200 dark:border-purple-800' :
              fu.type === 'inconsistency' ? 'bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800' :
              fu.type === 'benchmark_check' ? 'bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800' :
              'bg-muted border-border'
            }`}>
              <div className="flex items-start gap-1.5">
                {fu.type === 'deep_dive' && <Sparkles className="h-3 w-3 text-purple-500 mt-0.5 shrink-0" />}
                {fu.type === 'inconsistency' && <AlertTriangle className="h-3 w-3 text-amber-500 mt-0.5 shrink-0" />}
                {fu.type === 'benchmark_check' && <BarChart3 className="h-3 w-3 text-blue-500 mt-0.5 shrink-0" />}
                <div>
                  <p className="text-xs text-foreground">{fu.question}</p>
                  {fu.suggestion && (
                    <p className="text-[10px] text-muted-foreground mt-1 italic">{fu.suggestion}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function InteractiveScatterPlot({
  data,
  width = 500,
  height = 400,
}: {
  data: MatrixItem[]
  width?: number
  height?: number
}) {
  if (!data.length) return <p className="text-muted-foreground text-center py-8">Nessun dato disponibile.</p>

  const maxScore = 5.5
  const padding = { top: 30, right: 30, bottom: 50, left: 50 }
  const plotWidth = width - padding.left - padding.right
  const plotHeight = height - padding.top - padding.bottom

  const toX = (v: number) => padding.left + (v / maxScore) * plotWidth
  const toY = (v: number) => padding.top + plotHeight - (v / maxScore) * plotHeight

  const threshold = 3.0
  const thresholdX = toX(threshold)
  const thresholdY = toY(threshold)

  const gridLines = [1, 2, 3, 4, 5]

  // Group by standard_ref for color coding
  const standards = [...new Set(data.map(d => d.standard_ref))]

  return (
    <div className="overflow-x-auto">
      <svg width={width} height={height} className="mx-auto">
        {/* Background quadrants */}
        <rect x={padding.left} y={padding.top} width={thresholdX - padding.left} height={plotHeight} fill="#f0fdf4" opacity={0.5} />
        <rect x={thresholdX} y={padding.top} width={plotWidth - (thresholdX - padding.left)} height={thresholdY - padding.top} fill="#fef2f2" opacity={0.5} />
        <rect x={thresholdX} y={thresholdY} width={plotWidth - (thresholdX - padding.left)} height={plotHeight - (thresholdY - padding.top)} fill="#fef2f2" opacity={0.5} />

        {/* Grid */}
        {gridLines.map(v => (
          <g key={v}>
            <line x1={toX(v)} y1={padding.top} x2={toX(v)} y2={padding.top + plotHeight} stroke="#e5e7eb" strokeWidth={1} />
            <text x={toX(v)} y={padding.top + plotHeight + 18} textAnchor="middle" className="fill-muted-foreground" fontSize={11}>{v}</text>
            <line x1={padding.left} y1={toY(v)} x2={padding.left + plotWidth} y2={toY(v)} stroke="#e5e7eb" strokeWidth={1} />
            <text x={padding.left - 8} y={toY(v) + 4} textAnchor="end" className="fill-muted-foreground" fontSize={11}>{v}</text>
          </g>
        ))}

        {/* Threshold lines */}
        <line x1={thresholdX} y1={padding.top} x2={thresholdX} y2={padding.top + plotHeight} stroke="#ef4444" strokeWidth={2} strokeDasharray="4,4" />
        <line x1={padding.left} y1={thresholdY} x2={padding.left + plotWidth} y2={thresholdY} stroke="#ef4444" strokeWidth={2} strokeDasharray="4,4" />

        {/* Labels */}
        <text x={padding.left + plotWidth / 2} y={height - 5} textAnchor="middle" className="fill-foreground" fontSize={12} fontWeight={600}>Financial Score</text>
        <text x={12} y={padding.top + plotHeight / 2} textAnchor="middle" className="fill-foreground" fontSize={12} fontWeight={600} transform={`rotate(-90, 12, ${padding.top + plotHeight / 2})`}>Impact Score</text>

        {/* Quadrant labels */}
        <text x={padding.left + (thresholdX - padding.left) / 2} y={padding.top + 16} textAnchor="middle" className="fill-green-600" fontSize={11}>Non-Material</text>
        <text x={thresholdX + (plotWidth - (thresholdX - padding.left)) / 2} y={padding.top + 16} textAnchor="middle" className="fill-red-600" fontSize={11}>Impact Material</text>
        <text x={padding.left + (thresholdX - padding.left) / 2} y={padding.top + plotHeight - 8} textAnchor="middle" className="fill-orange-600" fontSize={11}>Financial Material</text>
        <text x={thresholdX + (plotWidth - (thresholdX - padding.left)) / 2} y={padding.top + plotHeight - 8} textAnchor="middle" className="fill-purple-600" fontSize={11}>Double Material</text>

        {/* Data points with standard_ref coloring */}
        {data.map((item, idx) => {
          const cx = toX(item.financial_score)
          const cy = toY(item.impact_score)
          const standardIndex = standards.indexOf(item.standard_ref)
          const hue = (standardIndex * 47) % 360
          const fillColor = item.is_material ? `hsl(${hue}, 70%, 50%)` : `hsl(${hue}, 40%, 70%)`
          return (
            <g key={idx}>
              <circle cx={cx} cy={cy} r={7} fill={fillColor} opacity={0.85} className="hover:opacity-100 cursor-pointer transition-opacity" stroke="white" strokeWidth={2} />
              <title>{`${item.datapoint_name}\n${item.standard_ref}\nImpact: ${item.impact_score.toFixed(1)}\nFinancial: ${item.financial_score.toFixed(1)}\n${item.is_material ? 'Materiale' : 'Non Materiale'}`}</title>
            </g>
          )
        })}
      </svg>

      {/* Legend */}
      {standards.length > 0 && (
        <div className="flex flex-wrap justify-center gap-3 mt-2">
          {standards.map((std, idx) => {
            const hue = (idx * 47) % 360
            const count = data.filter(d => d.standard_ref === std && d.is_material).length
            return (
              <span key={std} className="flex items-center gap-1 text-[10px] text-muted-foreground">
                <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: `hsl(${hue}, 70%, 50%)` }} />
                {std} ({count} mat)
              </span>
            )
          })}
        </div>
      )}
    </div>
  )
}

function EmbeddedAiChat({ score }: { score: ScoreItem | null }) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: 'Ciao! Sono il tuo assistente per la doppia materialità. Fammi domande sugli IRO, benchmark o criteri di valutazione.', timestamp: new Date() },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    if (!input.trim() || loading) return
    const userMsg: ChatMessage = { role: 'user', content: input.trim(), timestamp: new Date() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    const context = score ? ` sull'IRO "${score.disclosure_requirement}" (${score.standard_ref})` : ''

    setTimeout(() => {
      const responses = [
        `Per questo topic${context}, la soglia di materialità è 3.0 su una scala 1-5.`,
        `I benchmark di settore mostrano che per aziende simili, l'impact score medio è 2.8.`,
        `Considera che nella doppia materialità, l'impact materiality valuta l'impatto della società sull'ambiente, mentre la financial materiality valuta l'impatto finanziario sulla società.`,
        `Per valutare correttamente, considera: evidenze scientifiche, dati misurati, trend di settore e aspettative degli stakeholder.`,
        `Se hai dubbi su una valutazione, puoi chiedere all'AI di analizzare il tuo IRO corrente per suggerimenti personalizzati.`,
      ]
      const resp = responses[Math.floor(Math.random() * responses.length)]
      setMessages(prev => [...prev, { role: 'assistant', content: resp, timestamp: new Date() }])
      setLoading(false)
    }, 1200)
  }

  return (
    <div className="border rounded-lg overflow-hidden">
      <div className="bg-muted px-3 py-2 flex items-center gap-2 border-b">
        <BrainCircuit className="h-4 w-4 text-purple-500" />
        <span className="text-xs font-medium text-foreground">AI Assistant</span>
      </div>
      <div className="h-40 overflow-y-auto p-2 space-y-2 bg-background">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] p-2 rounded-lg text-[11px] ${
              msg.role === 'user'
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-foreground'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg p-2">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="flex gap-1 p-2 border-t bg-background">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Chiedi all'AI..."
          className="h-7 text-[11px] flex-1"
        />
        <Button size="sm" className="h-7 w-7 p-0" onClick={handleSend} disabled={!input.trim() || loading}>
          <Send className="h-3 w-3" />
        </Button>
      </div>
    </div>
  )
}

// ── Main Component ─────────────────────────────────────────────

export default function MaterialityPage() {
  const [assessmentList, setAssessmentList] = useState<any[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [scores, setScores] = useState<ScoreItem[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [matrix, setMatrix] = useState<MatrixItem[]>([])
  const [report, setReport] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [aiFollowups, setAiFollowups] = useState<AiFollowup[]>([])
  const [aiLoading, setAiLoading] = useState(false)
  const [showAiDialog, setShowAiDialog] = useState(false)
  const [topicFilter, setTopicFilter] = useState('')
  const [completion, setCompletion] = useState({ scored: 0, total: 0, material: 0 })
  const [activeView, setActiveView] = useState<'scoring' | 'matrix' | 'report'>('scoring')
  const [showRightPanel, setShowRightPanel] = useState(true)

  useEffect(() => {
    loadAssessments()
  }, [])

  const loadAssessments = async () => {
    try {
      const list = await assessments.list()
      setAssessmentList(list)
      if (list.length > 0) setSelectedId(list[0].id)
    } catch (e) {
      // silent
    }
  }

  const loadScores = useCallback(async () => {
    if (!selectedId) return
    setLoading(true)
    try {
      const data = await assessments.listScores(selectedId)
      setScores(data.scores || [])
      const scored = (data.scores || []).filter((s: ScoreItem) => s.total_impact_score != null).length
      const material = (data.scores || []).filter((s: ScoreItem) => s.is_material).length
      setCompletion({ scored, total: data.scores?.length || 0, material })
    } catch (e) {
      // silent
    }
    setLoading(false)
  }, [selectedId])

  const loadMatrix = useCallback(async () => {
    if (!selectedId) return
    setLoading(true)
    try {
      const data = await assessments.getMatrix(selectedId)
      setMatrix(data.matrix || [])
    } catch (e) {
      // silent
    }
    setLoading(false)
  }, [selectedId])

  const loadReport = useCallback(async () => {
    if (!selectedId) return
    setLoading(true)
    try {
      const data = await assessments.getReport(selectedId)
      setReport(data)
    } catch (e) {
      // silent
    }
    setLoading(false)
  }, [selectedId])

  // Load data when assessment changes
  useEffect(() => {
    if (selectedId) {
      loadScores()
      loadMatrix()
    }
  }, [selectedId, loadScores, loadMatrix])

  const currentScore = scores[currentIndex]
  const isCurrentScored = currentScore?.total_impact_score != null

  const updateScore = async (key: string, value: number) => {
    if (!selectedId || !currentScore) return
    setSaving(true)

    try {
      const updateData: any = { [key]: value }
      const result = await assessments.updateScore(selectedId, currentScore.id, updateData)

      setScores(prev => prev.map(s =>
        s.id === currentScore.id
          ? { ...s, ...updateData, ...result }
          : s
      ))

      const newScores = scores.map(s =>
        s.id === currentScore.id ? { ...s, ...updateData, ...result } : s
      )
      const scored = newScores.filter(s => s.total_impact_score != null).length
      const material = newScores.filter(s => s.is_material).length
      setCompletion({ scored, total: newScores.length, material })
    } catch (e) {
      console.error('Failed to update score:', e)
    }
    setSaving(false)
  }

  const getAiFollowup = async () => {
    if (!selectedId || !currentScore) return
    setAiLoading(true)
    try {
      const data = await assessments.getAiFollowup(selectedId, currentScore.id)
      setAiFollowups(data.followup_questions || [])
      setShowAiDialog(true)
    } catch (e) {
      console.error('Failed to get AI followup:', e)
    }
    setAiLoading(false)
  }

  const navigateTo = (index: number) => {
    if (index < 0 || index >= scores.length) return
    setCurrentIndex(index)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Doppia Materialità — Interattiva</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Valutazione IRO con AI, matrice dinamica e benchmark
          </p>
        </div>
        <div className="flex items-center gap-3">
          {assessmentList.length > 0 && (
            <select
              value={selectedId || ''}
              onChange={(e) => setSelectedId(e.target.value)}
              className="border border-input rounded-lg px-3 py-2 text-sm bg-background"
            >
              {assessmentList.map((a: any) => (
                <option key={a.id} value={a.id}>{a.assessment_date} - {a.status}</option>
              ))}
            </select>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowRightPanel(!showRightPanel)}
            className="text-muted-foreground"
          >
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Completion Stats */}
      {completion.total > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <StatCard icon={<Layers className="h-4 w-4 text-primary" />} label="Total IRO" value={completion.total} />
          <StatCard icon={<CheckCircle2 className="h-4 w-4 text-green-500" />} label="Valutati" value={completion.scored} />
          <StatCard icon={<AlertTriangle className="h-4 w-4 text-red-500" />} label="Materiali" value={completion.material} />
          <StatCard icon={<TrendingUp className="h-4 w-4 text-blue-500" />} label="Completamento" value={`${completion.total > 0 ? Math.round(completion.scored / completion.total * 100) : 0}%`} />
          <StatCard icon={<Target className="h-4 w-4 text-purple-500" />} label="Non Materiali" value={completion.total - completion.material} />
        </div>
      )}

      {/* View Tabs */}
      <div className="flex gap-1 bg-muted rounded-lg p-1 w-fit">
        {[
          { id: 'scoring' as const, label: 'Scoring Interattivo', icon: <Target className="h-4 w-4" /> },
          { id: 'matrix' as const, label: 'Matrice', icon: <BarChart3 className="h-4 w-4" /> },
          { id: 'report' as const, label: 'Report', icon: <FileText className="h-4 w-4" /> },
        ].map(view => (
          <button
            key={view.id}
            onClick={() => setActiveView(view.id)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeView === view.id
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {view.icon}
            {view.label}
          </button>
        ))}
      </div>

      {/* ── SCORING VIEW: Three-panel layout ──────────────────── */}
      {activeView === 'scoring' && (
        <div className="grid grid-cols-12 gap-6">
          {/* Left: Topic Sidebar */}
          <div className={`${showRightPanel ? 'col-span-2' : 'col-span-2'} order-1`}>
            <Card>
              <CardHeader className="py-3 px-3">
                <CardTitle className="text-xs font-medium">Topic ESRS</CardTitle>
              </CardHeader>
              <CardContent className="py-2 px-3">
                <TopicSidebar
                  scores={scores}
                  currentIndex={currentIndex}
                  onNavigate={navigateTo}
                  filter={topicFilter}
                  setFilter={setTopicFilter}
                />
              </CardContent>
            </Card>
          </div>

          {/* Center: Scoring Wizard */}
          <div className={`${showRightPanel ? 'col-span-7' : 'col-span-10'} order-2`}>
            {currentScore ? (
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <Badge variant="outline" className="text-xs">{currentScore.standard_ref}</Badge>
                        {currentScore.is_material && (
                          <Badge variant="destructive" className="text-xs">Materiale</Badge>
                        )}
                        {currentScore.total_impact_score != null && !currentScore.is_material && (
                          <Badge variant="secondary">Non Materiale</Badge>
                        )}
                        <Badge variant="info" className="text-xs">
                          {currentIndex + 1} di {scores.length}
                        </Badge>
                      </div>
                      <CardTitle className="text-sm leading-snug">{currentScore.disclosure_requirement}</CardTitle>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={getAiFollowup}
                      disabled={aiLoading}
                      className="text-purple-600 dark:text-purple-400 shrink-0"
                    >
                      {aiLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <BrainCircuit className="h-4 w-4" />}
                    </Button>
                  </div>
                  <Progress
                    value={(currentIndex + 1) / scores.length * 100}
                    className="h-1 mt-2"
                  />
                </CardHeader>
                <CardContent>
                  {/* Impact Dimensions */}
                  <div className="mb-5">
                    <h4 className="text-xs font-semibold text-foreground mb-3 flex items-center gap-2">
                      <TrendingUp className="h-3.5 w-3.5 text-orange-500" />
                      Impact Materiality
                    </h4>
                    <div className="space-y-3">
                      {IMPACT_DIMENSIONS.map((dim) => {
                        const val = (currentScore as any)[dim.key] as number | null
                        return (
                          <div key={dim.key}>
                            <div className="flex items-center justify-between mb-1">
                              <label className="text-xs font-medium text-muted-foreground">{dim.label}</label>
                              <span className="text-xs font-bold text-foreground">{val ? dim.labels[val - 1] : '-'}</span>
                            </div>
                            <div className="flex gap-1">
                              {[1, 2, 3, 4, 5].map(v => (
                                <button
                                  key={v}
                                  onClick={() => updateScore(dim.key, v)}
                                  disabled={saving}
                                  className={`flex-1 py-1.5 text-[10px] font-medium rounded-lg border transition-all ${
                                    val === v
                                      ? `${dim.color} text-white border-transparent shadow-sm`
                                      : 'bg-background border-input text-muted-foreground hover:border-muted-foreground hover:bg-muted'
                                  }`}
                                >
                                  {v}
                                </button>
                              ))}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {/* Financial Dimensions */}
                  <div className="mb-5">
                    <h4 className="text-xs font-semibold text-foreground mb-3 flex items-center gap-2">
                      <TrendingDown className="h-3.5 w-3.5 text-blue-500" />
                      Financial Materiality
                    </h4>
                    <div className="space-y-3">
                      {FINANCIAL_DIMENSIONS.map((dim) => {
                        const val = (currentScore as any)[dim.key] as number | null
                        return (
                          <div key={dim.key}>
                            <div className="flex items-center justify-between mb-1">
                              <label className="text-xs font-medium text-muted-foreground">{dim.label}</label>
                              <span className="text-xs font-bold text-foreground">{val ? dim.labels[val - 1] : '-'}</span>
                            </div>
                            <div className="flex gap-1">
                              {[1, 2, 3, 4, 5].map(v => (
                                <button
                                  key={v}
                                  onClick={() => updateScore(dim.key, v)}
                                  disabled={saving}
                                  className={`flex-1 py-1.5 text-[10px] font-medium rounded-lg border transition-all ${
                                    val === v
                                      ? `${dim.color} text-white border-transparent shadow-sm`
                                      : 'bg-background border-input text-muted-foreground hover:border-muted-foreground hover:bg-muted'
                                  }`}
                                >
                                  {v}
                                </button>
                              ))}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {/* Score Result */}
                  {currentScore.total_impact_score != null && (
                    <div className="p-3 rounded-lg bg-muted border">
                      <h4 className="text-xs font-semibold mb-2">Risultato Scoring</h4>
                      <div className="grid grid-cols-3 gap-3 text-center">
                        <div>
                          <p className="text-lg font-bold text-orange-500">{currentScore.total_impact_score.toFixed(1)}</p>
                          <p className="text-[10px] text-muted-foreground">Impact Score</p>
                        </div>
                        <div>
                          <p className="text-lg font-bold text-blue-500">{(currentScore.total_financial_score || 0).toFixed(1)}</p>
                          <p className="text-[10px] text-muted-foreground">Financial Score</p>
                        </div>
                        <div>
                          <p className="text-lg font-bold">{Math.max(currentScore.total_impact_score || 0, currentScore.total_financial_score || 0).toFixed(1)}</p>
                          <p className="text-[10px] text-muted-foreground">Double Materiality</p>
                        </div>
                      </div>
                      {currentScore.is_material && (
                        <div className="mt-2 text-center">
                          <Badge variant="destructive">Materiale — Soglia ≥ 3.0</Badge>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Rationale */}
                  <div className="mt-3">
                    <textarea
                      placeholder="Note / razionale per questa valutazione..."
                      className="w-full border border-input rounded-lg px-3 py-2 text-xs bg-background resize-none h-14"
                      value={currentScore.rationale || ''}
                      onChange={async (e) => {
                        const val = e.target.value
                        setScores(prev => prev.map(s =>
                          s.id === currentScore.id ? { ...s, rationale: val } : s
                        ))
                      }}
                      onBlur={async () => {
                        if (currentScore.rationale) {
                          try {
                            await assessments.updateScore(selectedId!, currentScore.id, { rationale: currentScore.rationale })
                          } catch {}
                        }
                      }}
                    />
                  </div>
                </CardContent>

                {/* Navigation */}
                <div className="flex items-center justify-between px-6 pb-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigateTo(currentIndex - 1)}
                    disabled={currentIndex === 0}
                  >
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    Precedente
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => navigateTo(currentIndex + 1)}
                    disabled={currentIndex === scores.length - 1}
                  >
                    Successivo
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              </Card>
            ) : (
              <Card>
                <CardContent className="py-12 text-center">
                  <Target className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
                  <h3 className="text-lg font-medium mb-2">Nessun IRO da Valutare</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Genera prima gli IRO dalla pagina Assessment principale o carica gli score esistenti.
                  </p>
                  <div className="flex gap-2 justify-center">
                    <Button variant="outline" onClick={loadScores}>
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Carica Scores
                    </Button>
                    <Button onClick={() => window.location.href = '/assessment'}>
                      <Target className="h-4 w-4 mr-2" />
                      Vai ad Assessment
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right: AI Suggestions Panel */}
          {showRightPanel && (
            <div className="col-span-3 order-3">
              <Card>
                <CardHeader className="py-3 px-4">
                  <CardTitle className="text-xs font-medium flex items-center gap-2">
                    <BrainCircuit className="h-3.5 w-3.5 text-purple-500" />
                    AI Advisor & Benchmark
                  </CardTitle>
                </CardHeader>
                <CardContent className="py-2 px-4 space-y-4">
                  <AiSuggestionPanel
                    score={currentScore}
                    onGetAiFollowup={getAiFollowup}
                    aiFollowups={aiFollowups}
                    aiLoading={aiLoading}
                  />

                  {/* Embedded AI Chat */}
                  <div className="pt-3 border-t">
                    <p className="text-[10px] font-medium text-muted-foreground mb-2">Chat AI</p>
                    <EmbeddedAiChat score={currentScore} />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* ── MATRIX VIEW ──────────────────────────────────────── */}
      {activeView === 'matrix' && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg">Matrice di Doppia Materialità</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  Impact Score vs Financial Score — Soglia materialità ≥ 3.0
                </p>
              </div>
              <Button variant="outline" size="sm" onClick={loadMatrix}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Aggiorna
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {matrix.length > 0 ? (
              <div className="space-y-6">
                <InteractiveScatterPlot data={matrix} width={600} height={420} />

                {/* Matrix Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2 px-3 text-muted-foreground font-medium">Datapoint</th>
                        <th className="text-center py-2 px-3 text-muted-foreground font-medium">Standard</th>
                        <th className="text-center py-2 px-3 text-muted-foreground font-medium">Impact</th>
                        <th className="text-center py-2 px-3 text-muted-foreground font-medium">Financial</th>
                        <th className="text-center py-2 px-3 text-muted-foreground font-medium">Materiale</th>
                        <th className="text-center py-2 px-3 text-muted-foreground font-medium">Quadrante</th>
                      </tr>
                    </thead>
                    <tbody>
                      {matrix.map((item, idx) => {
                        const getQuadrant = () => {
                          if (item.impact_score >= 3 && item.financial_score >= 3) return { label: 'Dual', color: 'text-purple-600 bg-purple-50 dark:bg-purple-950/20' }
                          if (item.impact_score >= 3) return { label: 'Impact', color: 'text-red-600 bg-red-50 dark:bg-red-950/20' }
                          if (item.financial_score >= 3) return { label: 'Financial', color: 'text-blue-600 bg-blue-50 dark:bg-blue-950/20' }
                          return { label: 'Non', color: 'text-green-600 bg-green-50 dark:bg-green-950/20' }
                        }
                        const quad = getQuadrant()
                        return (
                          <tr key={idx} className="border-b hover:bg-muted/50">
                            <td className="py-2 px-3 max-w-xs truncate text-xs">{item.datapoint_name}</td>
                            <td className="text-center py-2 px-3 text-muted-foreground text-xs">{item.standard_ref}</td>
                            <td className="text-center py-2 px-3 text-sm font-medium">{item.impact_score.toFixed(1)}</td>
                            <td className="text-center py-2 px-3 text-sm font-medium">{item.financial_score.toFixed(1)}</td>
                            <td className="text-center py-2 px-3">
                              <Badge variant={item.is_material ? 'destructive' : 'secondary'} className="text-[10px]">
                                {item.is_material ? 'Sì' : 'No'}
                              </Badge>
                            </td>
                            <td className="text-center py-2 px-3">
                              <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${quad.color}`}>
                                {quad.label}
                              </span>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Summary */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-4 border-t">
                  <SummaryBlock value={matrix.length} label="Total Datapoint" />
                  <SummaryBlock value={matrix.filter(m => m.is_material).length} label="Materiali" color="text-red-500" />
                  <SummaryBlock value={(matrix.reduce((a, m) => a + m.impact_score, 0) / matrix.length).toFixed(1)} label="Avg Impact" color="text-orange-500" />
                  <SummaryBlock value={(matrix.reduce((a, m) => a + m.financial_score, 0) / matrix.length).toFixed(1)} label="Avg Financial" color="text-blue-500" />
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
                <h3 className="text-lg font-medium mb-2">Nessun Dato Matrice</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Carica IRO e assegna punteggi dalla vista Scoring per popolare la matrice.
                </p>
                <div className="flex gap-2 justify-center">
                  <Button variant="outline" onClick={loadMatrix}>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Ricarica
                  </Button>
                  <Button onClick={() => setActiveView('scoring')}>
                    <Target className="h-4 w-4 mr-2" />
                    Vai a Scoring
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── REPORT VIEW ──────────────────────────────────────── */}
      {activeView === 'report' && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg">{report?.report_title || 'Report di Doppia Materialità'}</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  Conforme ESRS 2 IRO-1 e IRO-2
                </p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={loadReport}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Genera/Refresh
                </Button>
                <Button size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Scarica
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {report ? (
              <div className="space-y-6">
                <div className="p-4 bg-primary/5 rounded-lg border border-primary/10">
                  <h4 className="font-medium text-primary mb-2">Executive Summary</h4>
                  <p className="text-sm text-muted-foreground">{report.executive_summary}</p>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <SummaryBlock value={report.scores_summary.total_datapoints} label="Total Datapoint" />
                  <SummaryBlock value={report.scores_summary.scored_datapoints} label="Scored" color="text-green-600" />
                  <SummaryBlock value={report.scores_summary.material_datapoints} label="Materiali" color="text-red-600" />
                  <SummaryBlock value={`${report.scores_summary.completion_percentage}%`} label="Completamento" />
                </div>

                {report.scores_summary.material_topics.length > 0 && (
                  <div>
                    <h4 className="font-medium text-foreground mb-3">Topic ESRS Materiali</h4>
                    <div className="flex flex-wrap gap-2">
                      {report.scores_summary.material_topics.map((topic: string) => (
                        <Badge key={topic} variant="destructive" className="text-xs">{topic}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-4 bg-orange-50 dark:bg-orange-950/20 rounded-lg border border-orange-200 dark:border-orange-800">
                    <div className="flex items-center gap-2 mb-1">
                      <TrendingUp className="h-4 w-4 text-orange-500" />
                      <span className="text-sm font-medium">Impact Score Medio</span>
                    </div>
                    <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                      {report.scores_summary.average_impact_score.toFixed(1)}
                      <span className="text-base text-muted-foreground font-normal"> / 5.0</span>
                    </p>
                  </div>
                  <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
                    <div className="flex items-center gap-2 mb-1">
                      <TrendingDown className="h-4 w-4 text-blue-500" />
                      <span className="text-sm font-medium">Financial Score Medio</span>
                    </div>
                    <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                      {report.scores_summary.average_financial_score.toFixed(1)}
                      <span className="text-base text-muted-foreground font-normal"> / 5.0</span>
                    </p>
                  </div>
                </div>

                {report.sections?.map((section: any, idx: number) => (
                  <div key={idx} className="border rounded-lg p-4">
                    <h4 className="font-medium text-foreground mb-3">{section.title}</h4>
                    <p className="text-sm text-muted-foreground mb-3">{section.section}</p>
                    {section.material_topics && (
                      <div className="mb-3">
                        <span className="text-xs text-muted-foreground">Topic materiali: </span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {section.material_topics.map((t: string) => (
                            <Badge key={t} variant="outline" className="text-[10px]">{t}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    <div className="text-xs text-muted-foreground border-t pt-2 mt-3">
                      {section.total_iro_evaluated != null && (
                        <span className="mr-3">IRO valutati: {section.total_iro_evaluated}</span>
                      )}
                      {section.total_material_iro != null && (
                        <span>Materiali: {section.total_material_iro}</span>
                      )}
                    </div>
                  </div>
                ))}

                <div className="text-xs text-muted-foreground border-t pt-4 flex items-center justify-between">
                  <span>{report.company_name} — Anno Report: {report.reporting_year}</span>
                  <span>Assessment: {report.assessment_date}</span>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
                <h3 className="text-lg font-medium mb-2">Report non ancora generato</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Il report di doppia materialità viene generato automaticamente in base agli IRO e punteggi.
                </p>
                <Button onClick={loadReport}>
                  <FileText className="h-4 w-4 mr-2" />
                  Genera Report
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── AI Followup Dialog ───────────────────────────────── */}
      <Dialog open={showAiDialog} onOpenChange={setShowAiDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <BrainCircuit className="h-5 w-5 text-purple-500" />
              AI — Analisi e Suggerimenti
            </DialogTitle>
            <DialogDescription>
              Analisi basata sulle tue valutazioni per {currentScore?.disclosure_requirement}
            </DialogDescription>
          </DialogHeader>

          {aiFollowups.length > 0 ? (
            <div className="space-y-3 my-2">
              {aiFollowups.map((fu, idx) => (
                <div key={idx} className={`p-3 rounded-lg border ${
                  fu.type === 'deep_dive' ? 'bg-purple-50 dark:bg-purple-950/20 border-purple-200 dark:border-purple-800' :
                  fu.type === 'inconsistency' ? 'bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800' :
                  fu.type === 'benchmark_check' ? 'bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800' :
                  fu.type === 'pattern_analysis' ? 'bg-yellow-50 dark:bg-yellow-950/20 border-yellow-200 dark:border-yellow-800' :
                  'bg-muted border-border'
                }`}>
                  <div className="flex items-start gap-2">
                    {fu.type === 'deep_dive' && <Sparkles className="h-4 w-4 text-purple-500 mt-0.5 shrink-0" />}
                    {fu.type === 'inconsistency' && <AlertTriangle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />}
                    {fu.type === 'benchmark_check' && <BarChart3 className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />}
                    {fu.type === 'pattern_analysis' && <Lightbulb className="h-4 w-4 text-yellow-500 mt-0.5 shrink-0" />}
                    {fu.type === 'financial_detail' && <TrendingDown className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />}
                    <div>
                      <p className="text-sm font-medium text-foreground">{fu.question}</p>
                      {fu.suggestion && (
                        <p className="text-xs text-muted-foreground mt-1">
                          <span className="font-medium">Suggerimento:</span> {fu.suggestion}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">
              Nessun suggerimento specifico per questa valutazione. Le valutazioni appaiono bilanciate.
            </p>
          )}

          <DialogFooter>
            <Button onClick={() => setShowAiDialog(false)}>Chiudi</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// ── Helper Components ──────────────────────────────────────────

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: any }) {
  return (
    <Card>
      <CardContent className="py-3 px-4">
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-xs text-muted-foreground">{label}</span>
        </div>
        <p className="text-2xl font-bold mt-1">{value ?? '-'}</p>
      </CardContent>
    </Card>
  )
}

function SummaryBlock({ value, label, color }: { value: any; label: string; color?: string }) {
  return (
    <div className="text-center">
      <p className={`text-2xl font-bold ${color || 'text-foreground'}`}>{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  )
}
