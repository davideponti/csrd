'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { Badge } from '@/components/ui'
import { Progress } from '@/components/ui'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui'
import { Input } from '@/components/ui'
import { assessments, companies } from '@/lib/api'
import { ClipboardCheck, FileText, BarChart3, AlertTriangle, Layers, PlayCircle, CheckCircle2, Target, Brain, Loader2, HelpCircle, Network, Building2, Users, Euro } from 'lucide-react'
export default function AssessmentPage() {
  const [assessmentList, setAssessmentList] = useState<any[]>([])
  const [activeTab, setActiveTab] = useState<string>('wizard')
  const [selectedAssessment, setSelectedAssessment] = useState<string | null>(null)
  const [companyProfile, setCompanyProfile] = useState<any>(null)
  const [iros, setIros] = useState<any[]>([])
  const [iroSummary, setIroSummary] = useState<any>(null)
  const [iroBenchmark, setIroBenchmark] = useState<any>(null)
  const [matrix, setMatrix] = useState<any[]>([])
  const [report, setReport] = useState<any>(null)
  const [questionnaire, setQuestionnaire] = useState<any>(null)
  const [questionnaireResponses, setQuestionnaireResponses] = useState<Record<string, string>>({})
  const [gapAnalysis, setGapAnalysis] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showAiDialog, setShowAiDialog] = useState(false)
  const [showSuccessDialog, setShowSuccessDialog] = useState<{title: string; message: string} | null>(null)

  useEffect(() => {
    loadAssessments()
    loadCompanyProfile()
  }, [])

  const loadCompanyProfile = async () => {
    try {
      const data = await companies.getMe()
      setCompanyProfile(data)
    } catch (err: any) {
      console.error('[AssessmentPage] Load company profile error:', err)
    }
  }

  const loadAssessments = async () => {
    try {
      const list = await assessments.list()
      setAssessmentList(list)
      if (list.length > 0 && !selectedAssessment) {
        setSelectedAssessment(list[0].id)
      }
    } catch (err: any) {
      setError(err.message)
    }
  }

  const handleCreateAssessment = async () => {
    try {
      const newAssessment = await assessments.create()
      setAssessmentList([...assessmentList, newAssessment])
      setSelectedAssessment(newAssessment.id)
    } catch (err: any) {
      setError(err.message)
    }
  }

  const handleGenerateIros = async (useAi: boolean = false) => {
    if (!selectedAssessment) return
    setLoading(true)
    setError(null)
    try {
      const data = useAi
        ? await assessments.generateIros(selectedAssessment, { use_ai: true })
        : await assessments.getIros(selectedAssessment)
      setIros(data.iros || [])
      setIroSummary(data.summary || null)
      setIroBenchmark(data.benchmark || null)
      setActiveTab('iros')
      setShowAiDialog(false)

      // ⭐ AUTO-GENERATE SCORES AFTER IROS: generate score entries for ALL datapoints
      // (1,184 ESRS datapoints: IRO-matched + neutral defaults)
      try {
        const scoreResult = await assessments.generateScores(selectedAssessment)
        // Auto-calculate scores after generating entries
        const calcResult = await assessments.calculateScores(selectedAssessment)
        // Also pre-load the matrix data
        const matrixData = await assessments.getMatrix(selectedAssessment)
        setMatrix(matrixData.matrix || [])
        setShowSuccessDialog({
          title: '✅ IRO e Score Generati',
          message: `IRO generati: ${data.iros?.length || 0}\nScore entries creati: ${scoreResult.score_entries_created || 'completi'}\nDatapoint materiali: ${calcResult.material_datapoints}\n\nTutti i ${scoreResult.total_datapoints_available || 1184} datapoint ESRS sono stati valutati con punteggi IRO-matched + neutrali di default.`
        })
      } catch (scoreErr: any) {
        console.warn('[AssessmentPage] Score auto-generation warning:', scoreErr)
        setShowSuccessDialog({
          title: '✅ IRO Generati',
          message: `IRO generati con successo (${data.iros?.length || 0}).\n\n⚠️ La generazione automatica degli score ha avuto un problema: ${scoreErr.message}\nClicca manualmente "Genera Score Entries" nella tab Scoring.`
        })
      }
    } catch (err: any) {
      setError(err.message)
    }
    setLoading(false)
  }


  const handleSaveQuestionnaireResponse = (qId: string, value: string) => {
    setQuestionnaireResponses(prev => ({ ...prev, [qId]: value }))
  }

  const handleSubmitQuestionnaire = async () => {
    if (!selectedAssessment) return
    setLoading(true)
    try {
      await assessments.saveQuestionnaireResponses(selectedAssessment, questionnaireResponses)
      // ⭐ FIX: Auto-redirect to IRO tab after submitting questionnaire, with AI generation dialog
      setActiveTab('iros')
      // Show AI dialog automatically so user can immediately generate IROs
      setTimeout(() => setShowAiDialog(true), 300)
      setShowSuccessDialog({ title: '✅ Questionario Completato!', message: 'Il questionario di contesto è stato salvato con successo.\n\n📋 SEI STATO REINDIRIZZATO ALLA SEZIONE IRO (tab "IRO" sopra).\n➡️ Clicca "Genera IRO" per creare gli Impatti, Rischi e Opportunità sulla base dei dati che hai appena inserito.\n\n💡 Suggerimento: usa la "Generazione AI" per IRO personalizzati basati sul tuo settore.' })
    } catch (err: any) {
      setError(err.message)
    }
    setLoading(false)
  }

  const handleGenerateScores = async () => {
    if (!selectedAssessment) return
    setLoading(true)
    try {
      await assessments.generateScores(selectedAssessment)
      setShowSuccessDialog({ title: 'Score Entries Generati', message: 'Le entries di scoring sono state generate con successo.' })
    } catch (err: any) {
      setError(err.message)
    }
    setLoading(false)
  }

  const handleCalculateScores = async () => {
    if (!selectedAssessment) return
    setLoading(true)
    try {
      const result = await assessments.calculateScores(selectedAssessment)
      setActiveTab('matrix')
      setShowSuccessDialog({ 
        title: 'Punteggi Calcolati', 
        message: `Datapoint materiali: ${result.material_datapoints}\nImpact medio: ${result.average_impact_score}\nFinancial medio: ${result.average_financial_score}`
      })
      // Dopo aver calcolato, carica la matrice
      setTimeout(() => handleLoadMatrix(), 500)
    } catch (err: any) {
      setError(err.message)
    }
    setLoading(false)
  }

  const handleLoadMatrix = async () => {
    if (!selectedAssessment) return
    setLoading(true)
    try {
      const data = await assessments.getMatrix(selectedAssessment)
      setMatrix(data.matrix || [])
      setActiveTab('matrix')
    } catch (err: any) {
      setError(err.message)
    }
    setLoading(false)
  }

  const handleGenerateReport = async () => {
    if (!selectedAssessment) return
    setLoading(true)
    try {
      const data = await assessments.getReport(selectedAssessment)
      setReport(data)
      setActiveTab('report')
    } catch (err: any) {
      setError(err.message)
    }
    setLoading(false)
  }

  const handleLoadQuestionnaire = async () => {
    if (!selectedAssessment) return
    setLoading(true)
    try {
      const data = await assessments.getQuestionnaire(selectedAssessment)
      setQuestionnaire(data.phases || data)
      setActiveTab('context')
    } catch (err: any) {
      setError(err.message)
    }
    setLoading(false)
  }

  const handleGapAnalysis = async () => {
    if (!selectedAssessment) return
    setLoading(true)
    try {
      const data = await assessments.getGapAnalysis(selectedAssessment)
      setGapAnalysis(data)
      setActiveTab('gap')
    } catch (err: any) {
      setError(err.message)
    }
    setLoading(false)
  }

  // IRO stats
  const iroByType = iros.reduce((acc: Record<string, number>, iro: any) => {
    acc[iro.type] = (acc[iro.type] || 0) + 1
    return acc
  }, {})

  const iroMaterialCount = iros.filter((i: any) => i.is_material).length
  const iroAiCount = iros.filter((i: any) => i.ai_generated).length

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-foreground">
          Valutazione di Doppia Materialità
        </h2>
        <Button onClick={handleCreateAssessment} size="sm">
          <ClipboardCheck className="h-4 w-4 mr-2" />
          Nuovo Assessment
        </Button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-destructive/10 text-destructive rounded-lg text-sm border border-destructive/20 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Company Profile Card */}
      {companyProfile && (
        <Card className="mb-6">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Building2 className="h-4 w-4" />
              Profilo Azienda (da Impostazioni)
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="text-center p-3 bg-muted rounded-lg">
                <Building2 className="h-4 w-4 mx-auto mb-1 text-primary" />
                <p className="text-sm font-semibold">{companyProfile.company_name || '—'}</p>
                <p className="text-[10px] text-muted-foreground">Azienda</p>
              </div>
              <div className="text-center p-3 bg-muted rounded-lg">
                <Target className="h-4 w-4 mx-auto mb-1 text-primary" />
                <p className="text-sm font-semibold">{companyProfile.sector || '—'}</p>
                <p className="text-[10px] text-muted-foreground">Settore NACE</p>
              </div>
              <div className="text-center p-3 bg-muted rounded-lg">
                <Users className="h-4 w-4 mx-auto mb-1 text-primary" />
                <p className="text-sm font-semibold">{companyProfile.employee_count ?? '—'}</p>
                <p className="text-[10px] text-muted-foreground">Dipendenti</p>
              </div>
              <div className="text-center p-3 bg-muted rounded-lg">
                <Euro className="h-4 w-4 mx-auto mb-1 text-primary" />
                <p className="text-sm font-semibold">{companyProfile.turnover ? `€${Number(companyProfile.turnover).toLocaleString()}` : '—'}</p>
                <p className="text-[10px] text-muted-foreground">Fatturato</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Assessment Selector */}
      {assessmentList.length > 0 && (
        <div className="mb-6 flex items-center gap-3">
          <label className="text-sm font-medium text-muted-foreground">Assessment:</label>
          <select
            value={selectedAssessment || ''}
            onChange={(e) => setSelectedAssessment(e.target.value)}
            className="border border-input rounded-lg px-3 py-2 text-sm bg-background"
          >
            {assessmentList.map((a: any) => (
              <option key={a.id} value={a.id}>
                {a.assessment_date} - {a.status}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Tab Navigation */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="flex-wrap">
          <TabsTrigger value="wizard">
            <PlayCircle className="h-4 w-4 mr-2" />
            Wizard
          </TabsTrigger>
          <TabsTrigger value="context">
            <Layers className="h-4 w-4 mr-2" />
            Contesto
          </TabsTrigger>
          <TabsTrigger value="iros" className="relative">
            <Target className="h-4 w-4 mr-2" />
            IRO {iros.length > 0 && <span className="ml-1">({iros.length})</span>}
          </TabsTrigger>
          <TabsTrigger value="scoring">
            <BarChart3 className="h-4 w-4 mr-2" />
            Scoring
          </TabsTrigger>
          <TabsTrigger value="matrix">
            <AlertTriangle className="h-4 w-4 mr-2" />
            Matrice
          </TabsTrigger>
          <TabsTrigger value="gap">
            <AlertTriangle className="h-4 w-4 mr-2" />
            Gap Analysis
          </TabsTrigger>
          <TabsTrigger value="report">
            <FileText className="h-4 w-4 mr-2" />
            Report
          </TabsTrigger>
        </TabsList>

        {/* Tab: Wizard */}
        <TabsContent value="wizard">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Wizard di Assessment</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground mb-6">
                Completa il questionario per determinare i temi di sostenibilità materiali per la tua azienda.
                Segui i passi in ordine.
              </p>
              <div className="space-y-4">
                <StepCard
                  step={1}
                  title="Contesto Aziendale"
                  desc="Settore, attività, value chain, stakeholder"
                  status={questionnaire ? 'completato' : 'da_completare'}
                  onStart={handleLoadQuestionnaire}
                  icon={<Building2 className="h-4 w-4" />}
                />
                <StepCard
                  step={2}
                  title="Identificazione IRO"
                  desc="Impatti, Rischi, Opportunità con scoring iniziale automatico"
                  status={iros.length > 0 ? 'completato' : 'non_iniziato'}
                  onStart={() => setShowAiDialog(true)}
                  icon={<Target className="h-4 w-4" />}
                  badge={iroSummary ? `${iroSummary.total_iros} IRO, ${iroSummary.material_count} materiali` : undefined}
                />
                <StepCard
                  step={3}
                  title="Scoring Doppia Materialità"
                  desc="Valutazione impatto e finanziario"
                  status="non_iniziato"
                  onStart={() => { handleGenerateScores(); setTimeout(handleCalculateScores, 500) }}
                  icon={<BarChart3 className="h-4 w-4" />}
                />
                <StepCard
                  step={4}
                  title="Gap Analysis"
                  desc="Confronto ESRS vs dati aziendali"
                  status={gapAnalysis ? 'completato' : 'non_iniziato'}
                  onStart={handleGapAnalysis}
                  icon={<AlertTriangle className="h-4 w-4" />}
                />
                <StepCard
                  step={5}
                  title="Matrice di Materialità"
                  desc="Visualizzazione scatter plot impatto vs finanziario"
                  status={matrix.length > 0 ? 'completato' : 'non_iniziato'}
                  onStart={handleLoadMatrix}
                  icon={<BarChart3 className="h-4 w-4" />}
                />
                <StepCard
                  step={6}
                  title="Report Materialità"
                  desc="Generazione report ESRS 2 IRO-1/2"
                  status={report ? 'completato' : 'non_iniziato'}
                  onStart={handleGenerateReport}
                  icon={<FileText className="h-4 w-4" />}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Context Questionnaire */}
        <TabsContent value="context">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Questionario di Contesto Aziendale</CardTitle>
            </CardHeader>
            <CardContent>
              {/* ╔══════════════════════════════════════════════════════╗
                   ║  BANNER ISTRUZIONI: STEP 1 → STEP 2                ║
                   ╚══════════════════════════════════════════════════════╝ */}
              <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/40 dark:to-purple-950/40 rounded-lg border-2 border-blue-200 dark:border-blue-800 shadow-sm">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center shrink-0">
                    <span className="text-lg font-bold text-blue-600 dark:text-blue-400">1</span>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-blue-700 dark:text-blue-300 text-sm">📋 PASSO 1: Compila il questionario</h4>
                    <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                      Rispondi a tutte le domande sul contesto aziendale. 
                      Al termine, premi <strong>"Salva Questionario"</strong> qui sotto.
                    </p>
                  </div>
                  <div className="hidden sm:flex items-center">
                    <span className="text-2xl text-blue-300 dark:text-blue-600">→</span>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center shrink-0">
                    <span className="text-lg font-bold text-purple-600 dark:text-purple-400">2</span>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-purple-700 dark:text-purple-300 text-sm">🎯 PASSO 2: Genera IRO</h4>
                    <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">
                      Dopo aver salvato, <strong>verrai automaticamente reindirizzato</strong> alla tab 
                      <strong> "IRO"</strong> per creare Impatti, Rischi e Opportunità!
                    </p>
                  </div>
                </div>
              </div>

              {questionnaire ? (
                <div>
                  <div className="mb-4 p-3 bg-primary/5 rounded-lg border border-primary/10">
                    <p className="text-sm text-muted-foreground">
                      Settore: <strong>{questionnaire.sector_name || questionnaire.sector}</strong>
                      {questionnaire.ai_generated_questions?.length > 0 && (
                        <span className="ml-3">
                          | <Brain className="h-3 w-3 inline mr-1" />
                          {questionnaire.ai_generated_questions.length} domande AI disponibili
                        </span>
                      )}
                    </p>
                  </div>


                  {(Array.isArray(questionnaire.phases) ? questionnaire.phases : Object.values(questionnaire.phases || {})).map((phase: any, idx: number) => (
                    <div key={idx} className="mb-6">
                      <div className="flex items-center gap-2 mb-3">
                        <Badge variant="info">Fase {phase.id}</Badge>
                        <h4 className="font-medium text-foreground">{phase.name}</h4>
                        <span className="text-xs text-muted-foreground">({phase.type})</span>
                      </div>
                      <p className="text-xs text-muted-foreground mb-3">{phase.description}</p>

                      <div className="space-y-3">
                        {phase.questions?.map((q: any) => (
                          <div key={q.id} className={`p-3 rounded-lg transition-colors ${
                            questionnaireResponses[q.id] ? 'bg-primary/5 border border-primary/20' : 'bg-muted'
                          }`}>
                            <div className="flex items-start gap-2">
                              <HelpCircle className="h-4 w-4 mt-0.5 text-muted-foreground shrink-0" />
                              <div className="flex-1">
                                <p className="text-sm font-medium text-foreground mb-2">{q.question}</p>
                                <div className="flex flex-wrap gap-2">
                                  {q.options?.map((opt: string) => {
                                    const isSelected = questionnaireResponses[q.id] === opt
                                    return (
                                      <button
                                        key={opt}
                                        onClick={() => handleSaveQuestionnaireResponse(q.id, opt)}
                                        className={`px-3 py-1.5 text-xs rounded-full border transition-all ${
                                          isSelected
                                            ? 'bg-primary text-primary-foreground border-primary'
                                            : 'border-input hover:bg-accent hover:border-ring'
                                        }`}
                                      >
                                        {opt}
                                      </button>
                                    )
                                  })}
                                </div>
                                <div className="mt-1.5 flex gap-1">
                                  {q.esrs_topics?.map((topic: string) => (
                                    <Badge key={topic} variant="info" className="text-[10px]">{topic}</Badge>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}

                  {/* AI Generated Questions */}
                  {questionnaire.ai_generated_questions?.length > 0 && (
                    <div className="mb-6 p-4 bg-purple-50 dark:bg-purple-950/30 rounded-lg border border-purple-200 dark:border-purple-800">
                      <div className="flex items-center gap-2 mb-3">
                        <Brain className="h-4 w-4 text-purple-600" />
                        <h4 className="font-medium text-purple-700 dark:text-purple-300">Domande AI Generatives</h4>
                      </div>
                      <ul className="space-y-2">
                        {questionnaire.ai_generated_questions.map((q: string, idx: number) => (
                          <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                            <span className="text-purple-500 mt-0.5">•</span>
                            {q}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="flex justify-end mt-6">
                    <Button onClick={handleSubmitQuestionnaire} disabled={loading}>
                      {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <CheckCircle2 className="h-4 w-4 mr-2" />}
                      Salva Questionario
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Layers className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>Carica il questionario dal Wizard per iniziare la compilazione.</p>
                  <p className="text-xs mt-1">Il questionario si adatta automaticamente al settore della tua azienda.</p>
                  <Button variant="outline" className="mt-4" onClick={handleLoadQuestionnaire}>
                    <Layers className="h-4 w-4 mr-2" />
                    Carica Questionario
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: IRO */}
        <TabsContent value="iros">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center flex-wrap gap-3">
                <div>
                  <CardTitle className="text-lg">IRO Identificati ({iros.length})</CardTitle>
                  {iroSummary && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {iroSummary.material_count} materiali · {iroSummary.by_type?.impact || 0} impatti · {iroSummary.by_type?.risk || 0} rischi · {iroSummary.by_type?.opportunity || 0} opportunità
                      {iroSummary.ai_generated > 0 && ` · ${iroSummary.ai_generated} generati da AI`}
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button onClick={() => setShowAiDialog(true)} size="sm" variant="outline">
                    <Brain className="h-4 w-4 mr-2" />
                    Genera IRO
                  </Button>
                  <Button onClick={handleGenerateScores} disabled={loading} size="sm">
                    <BarChart3 className="h-4 w-4 mr-2" />
                    Genera Score Entries
                  </Button>
                </div>
              </div>

              {/* Benchmark Card */}
              {iroBenchmark && (
                <div className="mt-3 p-3 bg-muted rounded-lg">
                  <p className="text-xs font-medium text-muted-foreground mb-2">
                    Benchmark Settore: <strong>{iroBenchmark.name}</strong>
                  </p>
                  <div className="flex flex-wrap gap-2 text-xs">
                    <Badge variant="info">Carbonio: {iroBenchmark.carbon_intensity}</Badge>
                    <Badge variant="info">Acqua: {iroBenchmark.water_intensity}</Badge>
                    <Badge variant="info">Rifiuti: {iroBenchmark.waste_intensity}</Badge>
                    <Badge variant="info">Sociale: {iroBenchmark.social_risk}</Badge>
                    <Badge variant="info">Governance: {iroBenchmark.governance_risk}</Badge>
                  </div>
                </div>
              )}
            </CardHeader>
            <CardContent>
              {iros.length > 0 ? (
                <div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {iros.map((iro: any, idx: number) => (
                      <div
                        key={idx}
                        className={`p-3 rounded-lg border-l-4 transition-all hover:shadow-sm ${
                          iro.is_material ? 'border-l-destructive bg-destructive/5' : 'border-l-primary bg-muted'
                        } ${iro.ai_generated ? 'ring-1 ring-purple-300 dark:ring-purple-700' : ''}`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant={
                            iro.type === 'impact' ? 'destructive' :
                            iro.type === 'risk' ? 'warning' : 'success'
                          }>
                            {iro.type}
                          </Badge>
                          <span className="text-xs text-muted-foreground">{iro.topic}</span>
                          {iro.ai_generated && (
                            <Badge variant="info" className="text-[10px]">
                              <Brain className="h-3 w-3 mr-1" />AI
                            </Badge>
                          )}
                          {iro.is_material && (
                            <Badge variant="destructive" className="text-[10px]">Materiale</Badge>
                          )}
                        </div>
                        <p className="font-medium text-sm text-foreground">{iro.name}</p>
                        <p className="text-xs text-muted-foreground mt-1">{iro.description}</p>
                        {iro.initial_impact_score && (
                          <div className="flex gap-3 mt-2 text-xs text-muted-foreground">
                            <span>Impact: <strong>{iro.initial_impact_score}</strong></span>
                            <span>Financial: <strong>{iro.initial_financial_score}</strong></span>
                            {iro.benchmark_source && <span className="text-[10px]">({iro.benchmark_source})</span>}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Summary stats */}
                  <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
                    <MetricCard label="Total IRO" value={iroSummary?.total_iros || iros.length} />
                    <MetricCard label="Materiali" value={iroMaterialCount} />
                    <MetricCard label="Da Benchmark" value={iroSummary?.benchmark_sourced || (iros.length - iroAiCount)} />
                    <MetricCard label="AI Generati" value={iroAiCount} />
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Target className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>Nessun IRO generato. Avvia dal Wizard o clicca "Genera IRO".</p>
                  <p className="text-xs mt-1">Gli IRO vengono generati automaticamente in base al settore e contesto aziendale.</p>
                  <Button variant="outline" className="mt-4" onClick={() => setShowAiDialog(true)}>
                    <Target className="h-4 w-4 mr-2" />
                    Genera IRO
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Scoring */}
        <TabsContent value="scoring">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Scoring Engine</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3 mb-6">
                <Button onClick={handleGenerateScores} disabled={loading}>
                  <BarChart3 className="h-4 w-4 mr-2" />
                  Genera Score Entries
                </Button>
                <Button onClick={handleCalculateScores} disabled={loading} variant="secondary">
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Calcola Punteggi
                </Button>
                <Button onClick={handleLoadMatrix} disabled={loading} variant="outline">
                  <AlertTriangle className="h-4 w-4 mr-2" />
                  Vedi Matrice
                </Button>
                <Button onClick={handleGenerateReport} disabled={loading} variant="outline">
                  <FileText className="h-4 w-4 mr-2" />
                  Genera Report
                </Button>
              </div>
              {loading && (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                  <p className="text-sm text-muted-foreground mt-2">Elaborazione in corso...</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Matrix */}
        <TabsContent value="matrix">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Matrice di Materialità</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                Impact Score vs Financial Score. Punti sopra 3.0 in entrambi gli assi sono materiali.
              </p>
              {matrix.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2 px-3 text-muted-foreground font-medium">Datapoint</th>
                        <th className="text-center py-2 px-3 text-muted-foreground font-medium">Standard</th>
                        <th className="text-center py-2 px-3 text-muted-foreground font-medium">Impact Score</th>
                        <th className="text-center py-2 px-3 text-muted-foreground font-medium">Financial Score</th>
                        <th className="text-center py-2 px-3 text-muted-foreground font-medium">Materiale</th>
                      </tr>
                    </thead>
                    <tbody>
                      {matrix.map((item: any, idx: number) => (
                        <tr key={idx} className="border-b hover:bg-muted/50">
                          <td className="py-2 px-3 max-w-xs truncate">{item.datapoint_name}</td>
                          <td className="text-center py-2 px-3 text-muted-foreground">{item.standard_ref}</td>
                          <td className="text-center py-2 px-3">{item.impact_score?.toFixed(1)}</td>
                          <td className="text-center py-2 px-3">{item.financial_score?.toFixed(1)}</td>
                          <td className="text-center py-2 px-3">
                            <Badge variant={item.is_material ? 'success' : 'secondary'}>
                              {item.is_material ? 'Sì' : 'No'}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <p>Nessun dato matrice disponibile. Calcola i punteggi prima.</p>
                  <Button variant="outline" className="mt-4" onClick={handleLoadMatrix}>
                    <BarChart3 className="h-4 w-4 mr-2" />
                    Carica Matrice
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>


        {/* Tab: Gap Analysis */}
        <TabsContent value="gap">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Gap Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              {gapAnalysis ? (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <MetricCard label="Total Required" value={gapAnalysis.total_required} />
                    <MetricCard label="Complete" value={gapAnalysis.complete} />
                    <MetricCard label="Partial" value={gapAnalysis.partial} />
                    <MetricCard label="Missing" value={gapAnalysis.missing} />
                  </div>
                  <div>
                    <Progress value={gapAnalysis.completion_percentage} className="h-3" />
                    <p className="text-sm text-muted-foreground mt-1 text-center">
                      Completion: {gapAnalysis.completion_percentage}%
                    </p>
                  </div>
                  {gapAnalysis.priority_actions?.length > 0 && (
                    <div>
                      <h4 className="font-medium text-foreground mb-3">Priority Actions</h4>
                      <div className="space-y-2">
                        {gapAnalysis.priority_actions.slice(0, 5).map((action: any, idx: number) => (
                          <div key={idx} className="flex items-start gap-3 p-3 bg-muted rounded-lg">
                            <Badge variant={
                              action.priority === 'critical' ? 'destructive' :
                              action.priority === 'high' ? 'warning' : 'secondary'
                            }>
                              {action.priority}
                            </Badge>
                            <div>
                              <p className="text-sm font-medium text-foreground">{action.datapoint}</p>
                              <p className="text-xs text-muted-foreground">{action.suggestion}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <p>Avvia la Gap Analysis per vedere il confronto tra requisiti ESRS e dati aziendali.</p>
                  <Button variant="outline" className="mt-4" onClick={handleGapAnalysis}>
                    <AlertTriangle className="h-4 w-4 mr-2" />
                    Avvia Gap Analysis
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Report */}
        <TabsContent value="report">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">{report?.report_title || 'Report di Materialità'}</CardTitle>
            </CardHeader>
            <CardContent>
              {report ? (
                <div className="space-y-6">
                  {report.company_name && (
                    <p className="text-sm text-muted-foreground">
                      {report.company_name} - Reporting Year: {report.reporting_year}
                    </p>
                  )}

                  {report.executive_summary && (
                    <div className="p-4 bg-primary/5 rounded-lg border border-primary/10">
                      <h4 className="font-medium text-primary mb-2">Executive Summary</h4>
                      <p className="text-sm text-muted-foreground">{report.executive_summary}</p>
                    </div>
                  )}

                  {report.scores_summary && (
                    <div>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                        <MetricCard label="ESRS Datapoints Totali" value={report.scores_summary.total_datapoints_available_in_db || report.scores_summary.total_datapoints} />
                        <MetricCard label="Valutati (scored)" value={report.scores_summary.scored_datapoints} />
                        <MetricCard label="Materiali" value={report.scores_summary.material_datapoints} />
                        <MetricCard label="Completion" value={`${report.scores_summary.completion_percentage}%`} />
                        <MetricCard label="Impact Medio" value={report.scores_summary.average_impact_score} />
                      </div>
                      {report.scores_summary.total_datapoints_available_in_db && (
                        <p className="text-xs text-muted-foreground mt-2 text-center">
                          Database contiene {report.scores_summary.total_datapoints_available_in_db} datapoint ESRS totali, 
                          di cui {report.scores_summary.total_datapoints} con score generato per questo assessment.
                        </p>
                      )}
                    </div>
                  )}

                  {report.sections?.map((section: any, idx: number) => (
                    <div key={idx} className="mb-6">
                      <h4 className="font-medium text-foreground mb-2">{section.section}: {section.title}</h4>
                      <p className="text-sm text-muted-foreground">{section.content?.methodology || section.content?.introduction}</p>
                      {section.material_topics && (
                        <div className="mt-2 flex gap-1">
                          {section.material_topics.map((topic: string) => (
                            <Badge key={topic} variant="success">{topic}</Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <p>Nessun report generato. Completa la valutazione prima.</p>
                  <Button variant="outline" className="mt-4" onClick={handleGenerateReport}>
                    <FileText className="h-4 w-4 mr-2" />
                    Genera Report
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Success Dialog */}
      <Dialog open={showSuccessDialog !== null} onOpenChange={(open) => { if (!open) setShowSuccessDialog(null) }}>
        <DialogContent>
          <DialogHeader>
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-full bg-emerald-100 flex items-center justify-center">
                <CheckCircle2 className="h-6 w-6 text-emerald-600" />
              </div>
              <div>
                <DialogTitle className="text-lg">{showSuccessDialog?.title || 'Operazione Completata'}</DialogTitle>
              </div>
            </div>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-muted-foreground whitespace-pre-line">{showSuccessDialog?.message}</p>
          </div>
          <DialogFooter>
            <Button onClick={() => setShowSuccessDialog(null)}>
              <CheckCircle2 className="h-4 w-4 mr-2" />
              OK
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* AI IRO Generation Dialog */}
      <Dialog open={showAiDialog} onOpenChange={setShowAiDialog}>
        <DialogContent>
          <DialogHeader>
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-full bg-purple-100 flex items-center justify-center">
                <Brain className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <DialogTitle>Generazione IRO</DialogTitle>
                <DialogDescription>
                  Scegli la modalità di generazione degli IRO (Impacts, Risks, Opportunities).
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <button
              onClick={() => handleGenerateIros(false)}
              disabled={loading}
              className="w-full p-4 bg-muted rounded-lg hover:bg-accent transition-colors text-left border border-input"
            >
              <div className="flex items-center gap-3">
                <BarChart3 className="h-6 w-6 text-primary" />
                <div>
                  <p className="font-medium text-foreground">Generazione Standard</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Usa il database IRO predefinito per il settore con scoring automatico basato su benchmark.
                  </p>
                </div>
              </div>
            </button>
            <button
              onClick={() => handleGenerateIros(true)}
              disabled={loading}
              className="w-full p-4 bg-purple-50 dark:bg-purple-950/30 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/50 transition-colors text-left border border-purple-200 dark:border-purple-800"
            >
              <div className="flex items-center gap-3">
                <Brain className="h-6 w-6 text-purple-600" />
                <div>
                  <p className="font-medium text-purple-700 dark:text-purple-300">
                    Generazione AI {loading && <Loader2 className="h-4 w-4 inline animate-spin ml-2" />}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Usa AI (LLM) per generare IRO specifici e personalizzati in base al contesto aziendale.
                    Richiede chiave API OpenAI configurata.
                  </p>
                </div>
              </div>
            </button>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAiDialog(false)}>
              Annulla
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function StepCard({ step, title, desc, status, onStart, icon, badge }: {
  step: number
  title: string
  desc: string
  status: 'non_iniziato' | 'da_completare' | 'completato'
  onStart: () => void
  icon?: React.ReactNode
  badge?: string
}) {
  const statusConfig = {
    non_iniziato: { variant: 'secondary' as const, label: 'Non iniziato' },
    da_completare: { variant: 'warning' as const, label: 'Da completare' },
    completato: { variant: 'success' as const, label: 'Completato' },
  }

  const config = statusConfig[status]

  return (
    <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
      <div className="flex items-center gap-3">
        <span className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-bold">
          {icon || step}
        </span>
        <div>
          <div className="flex items-center gap-2">
            <h4 className="font-medium text-foreground">{title}</h4>
            {badge && <Badge variant="info" className="text-[10px]">{badge}</Badge>}
          </div>
          <p className="text-sm text-muted-foreground">{desc}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Badge variant={config.variant}>{config.label}</Badge>
        {status !== 'completato' && (
          <Button onClick={onStart} size="sm">
            {status === 'non_iniziato' ? 'Avvia' : 'Continua'}
          </Button>
        )}
      </div>
    </div>
  )
}

function MetricCard({ label, value }: { label: string; value: any }) {
  return (
    <div className="p-3 bg-muted rounded-lg text-center">
      <p className="text-2xl font-bold text-primary">{value ?? '-'}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  )
}
