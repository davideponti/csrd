"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Progress } from "@/components/ui/progress"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"

// ── Types ──────────────────────────────────────────────────────

interface Report {
  id: string
  reporting_year: number
  title: string
  status: "draft" | "review" | "final" | "filed"
  xbrl_validation_passed?: boolean | null
  filed_at?: string | null
  filed_to?: string | null
}

interface ValidationResult {
  passed: boolean
  errors: { datapoint: string; description: string }[]
  warnings: { datapoint: string; description: string }[]
  total_checks: number
}

interface StepStatus {
  step: number
  label: string
  status: "pending" | "running" | "done" | "error"
  detail?: string
}

// ── Helpers ────────────────────────────────────────────────────

const statusColors: Record<string, string> = {
  draft: "bg-yellow-100 text-yellow-800 border-yellow-200",
  review: "bg-blue-100 text-blue-800 border-blue-200",
  final: "bg-green-100 text-green-800 border-green-200",
  filed: "bg-gray-100 text-gray-800 border-gray-200",
}

const statusLabels: Record<string, string> = {
  draft: "Bozza",
  review: "In Revisione",
  final: "Finale",
  filed: "Depositato",
}

const steps: StepStatus[] = [
  { step: 1, label: "Compiling ESRS data", status: "pending" },
  { step: 2, label: "Running gap analysis", status: "pending" },
  { step: 3, label: "Generating narratives", status: "pending" },
  { step: 4, label: "Building tables & charts", status: "pending" },
  { step: 5, label: "Tagging iXBRL", status: "pending" },
]

// ── Component ──────────────────────────────────────────────────

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [stepStates, setStepStates] = useState<StepStatus[]>(steps)
  const [validation, setValidation] = useState<ValidationResult | null>(null)
  const [previewHtml, setPreviewHtml] = useState<string | null>(null)
  const [showPreview, setShowPreview] = useState(false)
  const [expandingId, setExpandingId] = useState<string | null>(null)
  const [exportingFormat, setExportingFormat] = useState<string | null>(null)
  const [reviewComment, setReviewComment] = useState("")
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false)
  const [approving, setApproving] = useState(false)

  // ── Load reports ─────────────────────────────────────────────

  const loadReports = useCallback(async () => {
    try {
      const data = await api.get("/reports")
      setReports(data)
    } catch (err) {
      console.error("Failed to load reports:", err)
    } finally {
      setLoading(false)
    }

  }, [])

  const createReport = async () => {
    try {
      const data = await api.post("/reports", { title: "Report CSRD " + new Date().getFullYear(), reporting_year: new Date().getFullYear() })
      setReports(prev => [...prev, data])
    } catch (err) {
      console.error("Failed to create report:", err)
    }
  }

  useEffect(() => {
    loadReports()
  }, [loadReports])

  // ── Generation Pipeline ─────────────────────────────────────

  const runGenerationStep = async (reportId: string, step: number) => {
    setStepStates((prev) =>
      prev.map((s) => (s.step === step ? { ...s, status: "running" } : s))
    )

    try {
      await api.post(`/reports/${reportId}/generate`, { step })
      setStepStates((prev) =>
        prev.map((s) => (s.step === step ? { ...s, status: "done" } : s))
      )
      return true
    } catch (err) {
      console.error(`Step ${step} failed:`, err)
      setStepStates((prev) =>
        prev.map((s) => (s.step === step ? { ...s, status: "error" } : s))
      )
      return false
    }
  }

  const startGeneration = async (reportId: string) => {
    setGenerating(true)
    setCurrentStep(0)
    setStepStates(steps)
    setValidation(null)

    for (let step = 1; step <= 5; step++) {
      setCurrentStep(step)
      const success = await runGenerationStep(reportId, step)
      if (!success) {
        alert(`Step ${step} failed. Controlla la console per dettagli.`)
        setGenerating(false)
        return
      }
      // Small delay to show progress
      await new Promise((r) => setTimeout(r, 500))
    }

    setGenerating(false)
    await loadReports()
  }

  // ── Preview ──────────────────────────────────────────────────

  const fetchPreview = async (reportId: string) => {
    try {
      const res = await api.get_text(`/reports/${reportId}/preview`)
      setPreviewHtml(res)
      setShowPreview(true)
    } catch (err) {
      console.error("Failed to fetch preview:", err)
    }
  }

  // ── Validation ───────────────────────────────────────────────

  const fetchValidation = async (reportId: string) => {
    try {
      const data: ValidationResult = await api.get(
        `/reports/${reportId}/validation`
      )
      setValidation(data)
    } catch (err) {
      console.error("Failed to fetch validation:", err)
    }
  }

  // ── Submit for Review ────────────────────────────────────────

  const submitForReview = async (reportId: string) => {
    try {
      await api.post(`/reports/${reportId}/submit-review`, {
        comments: reviewComment
          ? [{ author: "current_user", text: reviewComment, resolved: false }]
          : [],
      })
      setReviewDialogOpen(false)
      setReviewComment("")
      await loadReports()
    } catch (err) {
      console.error("Failed to submit for review:", err)
      alert("Errore durante l'invio in revisione.")
    }
  }

  // ── Approve ──────────────────────────────────────────────────

  const approveReport = async (reportId: string) => {
    setApproving(true)
    try {
      await api.post(`/reports/${reportId}/approve`)
      await loadReports()
    } catch (err) {
      console.error("Failed to approve report:", err)
      alert("Errore durante l'approvazione del report.")
    } finally {
      setApproving(false)
    }
  }

  // ── Export ───────────────────────────────────────────────────

  const exportReport = async (reportId: string, format: string) => {
    setExportingFormat(format)
    try {
      const blob = await api.get_blob(
        `/reports/${reportId}/export/${format}`
      )
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `csrd_report.${format === "ixbrl" ? "xhtml" : format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error(`Export ${format} failed:`, err)
      alert(`Esportazione in ${format.toUpperCase()} fallita.`)
    } finally {
      setExportingFormat(null)
    }
  }

  // ── Render Card ──────────────────────────────────────────────

  const renderReportCard = (report: Report) => {
    const isExpanded = expandingId === report.id
    const isDraft = report.status === "draft"
    const isReview = report.status === "review"
    const isFinal = report.status === "final"

    return (
      <Card key={report.id} className="mb-4">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">{report.title}</CardTitle>
              <p className="text-sm text-muted-foreground">
                Reporting Year: {report.reporting_year}
              </p>
            </div>
            <Badge className={statusColors[report.status] || statusColors.draft}>
              {statusLabels[report.status] || report.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {/* Quick actions */}
          <div className="flex flex-wrap gap-2 mb-3">
            {isDraft && (
              <Button
                size="sm"
                onClick={() => startGeneration(report.id)}
                disabled={generating}
              >
                {generating ? `Step ${currentStep}/5...` : `Genera Report ${report.reporting_year}`}
              </Button>
            )}
            {isFinal && (
              <>
                {["pdf", "ixbrl", "xlsx", "docx", "json"].map((fmt) => (
                  <Button
                    key={fmt}
                    size="sm"
                    variant="outline"
                    onClick={() => exportReport(report.id, fmt)}
                    disabled={exportingFormat === fmt}
                  >
                    {exportingFormat === fmt
                      ? "Esportazione..."
                      : fmt.toUpperCase()}
                  </Button>
                ))}
              </>
            )}
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                if (isExpanded) {
                  setExpandingId(null)
                } else {
                  setExpandingId(report.id)
                  fetchPreview(report.id)
                  if (report.xbrl_validation_passed !== null) {
                    fetchValidation(report.id)
                  }
                }
              }}
            >
              {isExpanded ? "Nascondi dettagli" : "Dettagli"}
            </Button>
          </div>

          {/* Expanded details */}
          {isExpanded && (
            <Tabs defaultValue="preview" className="mt-4">
              <TabsList>
                <TabsTrigger value="preview">Anteprima</TabsTrigger>
                <TabsTrigger value="validation">
                  Validazione
                  {validation && (
                    <span className="ml-1 text-xs">
                      ({validation.errors.length} err, {validation.warnings.length} warn)
                    </span>
                  )}
                </TabsTrigger>
                <TabsTrigger value="review">Review</TabsTrigger>
              </TabsList>

              {/* ── Preview Tab ───────────────────────────────── */}
              <TabsContent value="preview">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setShowPreview(!showPreview)}
                    >
                      {showPreview ? "Nascondi" : "Mostra"} Anteprima
                    </Button>
                  </div>
                  {showPreview && previewHtml && (
                    <iframe
                      srcDoc={previewHtml}
                      className="w-full h-[400px] border rounded-md"
                      sandbox="allow-same-origin allow-scripts"
                      title="Report Preview"
                    />
                  )}
                  {showPreview && !previewHtml && (
                    <p className="text-sm text-muted-foreground">
                      Genera il report per vedere l'anteprima.
                    </p>
                  )}
                </div>
              </TabsContent>

              {/* ── Validation Tab ────────────────────────────── */}
              <TabsContent value="validation">
                {validation ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-4">
                      <Card>
                        <CardContent className="pt-4 text-center">
                          <p className="text-2xl font-bold text-green-600">
                            {validation.errors.length}
                          </p>
                          <p className="text-xs text-muted-foreground">Errori</p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="pt-4 text-center">
                          <p className="text-2xl font-bold text-amber-600">
                            {validation.warnings.length}
                          </p>
                          <p className="text-xs text-muted-foreground">Warning</p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="pt-4 text-center">
                          <p className="text-2xl font-bold text-blue-600">
                            {validation.total_checks}
                          </p>
                          <p className="text-xs text-muted-foreground">Controlli</p>
                        </CardContent>
                      </Card>
                    </div>

                    {validation.warnings.length > 0 && (
                      <div>
                        <h4 className="font-semibold mb-2">Warning</h4>
                        {validation.warnings.map((w, i) => (
                          <div
                            key={i}
                            className="flex items-start gap-2 p-2 mb-2 bg-amber-50 rounded border border-amber-200"
                          >
                            <span className="text-amber-500 mt-0.5">⚠</span>
                            <div>
                              <p className="text-sm font-medium">{w.datapoint}</p>
                              <p className="text-xs text-muted-foreground">
                                {w.description}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    <p className="text-xs text-muted-foreground">
                      Esito:{ " " }
                      {validation.passed ? (
                        <span className="text-green-600 font-medium">SUCCESSO</span>
                      ) : (
                        <span className="text-red-600 font-medium">FALLITO</span>
                      )}
                    </p>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Genera il report e poi esegui la validazione.
                  </p>
                )}
              </TabsContent>

              {/* ── Review Tab ────────────────────────────────── */}
              <TabsContent value="review">
                <div className="space-y-4">
                  {/* Submit for Review */}
                  {isDraft && (
                    <Dialog open={reviewDialogOpen} onOpenChange={setReviewDialogOpen}>
                      <DialogTrigger asChild>
                        <Button size="sm">Invia in Revisione</Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Invia Report in Revisione</DialogTitle>
                          <DialogDescription>
                            Il report passerà dallo stato "Bozza" a "In
                            Revisione". Puoi aggiungere commenti per il revisore.
                          </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Commenti</label>
                          <textarea
                            className="w-full min-h-[100px] p-2 border rounded-md"
                            placeholder="Inserisci note per il revisore..."
                            value={reviewComment}
                            onChange={(e) => setReviewComment(e.target.value)}
                          />
                        </div>
                        <DialogFooter>
                          <Button
                            variant="outline"
                            onClick={() => setReviewDialogOpen(false)}
                          >
                            Annulla
                          </Button>
                          <Button onClick={() => submitForReview(report.id)}>
                            Invia in Revisione
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  )}

                  {/* Approve (visible only in review status) */}
                  {isReview && (
                    <Button
                      size="sm"
                      onClick={() => approveReport(report.id)}
                      disabled={approving}
                    >
                      {approving ? "Approvazione..." : "Approva Report"}
                    </Button>
                  )}

                  {isFinal && (
                    <p className="text-sm text-green-600 font-medium">
                      ✓ Report approvato e pronto per l'esportazione.
                    </p>
                  )}

                  {report.filed_at && (
                    <p className="text-xs text-muted-foreground">
                      Depositato il {new Date(report.filed_at).toLocaleDateString()} su{" "}
                      {report.filed_to || "N/A"}
                    </p>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          )}
        </CardContent>
      </Card>
    )
  }

  // ── Loading State ────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <p className="text-muted-foreground">Caricamento report...</p>
      </div>
    )
  }

  // ── Main Render ──────────────────────────────────────────────

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Report CSRD</h1>
          <p className="text-muted-foreground">
            Genera, visualizza e scarica i tuoi report di sostenibilità.
          </p>
        </div>
      </div>

      {/* Generation progress indicator */}
      {generating && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">
                  Generazione report in corso...
                </span>
                <span className="text-sm text-muted-foreground">
                  Step {currentStep}/5
                </span>
              </div>
              <Progress value={(currentStep / 5) * 100} className="h-2" />
              <div className="space-y-1">
                {stepStates.map((s) => (
                  <div key={s.step} className="flex items-center gap-2 text-sm">
                    <span>
                      {s.status === "pending" && "○"}
                      {s.status === "running" && "⟳"}
                      {s.status === "done" && "✓"}
                      {s.status === "error" && "✗"}
                    </span>
                    <span
                      className={
                        s.status === "running"
                          ? "font-medium text-blue-700"
                          : s.status === "done"
                          ? "text-green-700"
                          : s.status === "error"
                          ? "text-red-700"
                          : "text-muted-foreground"
                      }
                    >
                      [{s.step}/5] {s.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Report list */}
      {reports.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-muted-foreground">
              Nessun report ancora. Crea un assessment per iniziare.
            </p>
            <Button className="mt-4" onClick={createReport}>Crea Primo Report</Button>
          </CardContent>
        </Card>
      ) : (
        reports.map(renderReportCard)
      )}
    </div>
  )
}
