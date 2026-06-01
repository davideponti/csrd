'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { Button } from '@/components/ui'
import { Progress } from '@/components/ui/progress'
import { Card, CardContent } from '@/components/ui/card'
import {
  ClipboardCheck, BarChart3, FileText, Brain, Shield,
  ArrowRight, ArrowLeft, CheckCircle2, Building2,
  Users, Factory, Lightbulb, TrendingUp, AlertTriangle,
  Leaf, Zap, Flame, Truck, PlayCircle, Download,
  Sparkles, RefreshCw, ChevronRight
} from 'lucide-react'
import Link from 'next/link'
import { useLanguage } from '@/i18n/LanguageContext'

type StepStatus = 'incomplete' | 'in-progress' | 'complete'

const stepIcons = [ClipboardCheck, Brain, BarChart3, FileText]

const companySizes = [
  { id: 'small', labelKey: 'how.interactive.size.small', icon: Building2, employees: '10-50' },
  { id: 'medium', labelKey: 'how.interactive.size.medium', icon: Users, employees: '50-250' },
  { id: 'large', labelKey: 'how.interactive.size.large', icon: Factory, employees: '250+' },
]

const companySectors = [
  { id: 'manufacturing', labelKey: 'how.interactive.sector.manufacturing', icon: Factory },
  { id: 'tech', labelKey: 'how.interactive.sector.tech', icon: Lightbulb },
  { id: 'logistics', labelKey: 'how.interactive.sector.logistics', icon: Truck },
]

const materialityItems = [
  { id: 'climate', labelKey: 'how.interactive.materiality.climate', icon: Leaf, financial: 85, impact: 90, color: 'emerald' },
  { id: 'pollution', labelKey: 'how.interactive.materiality.pollution', icon: Zap, financial: 60, impact: 80, color: 'amber' },
  { id: 'water', labelKey: 'how.interactive.materiality.water', icon: Flame, financial: 45, impact: 70, color: 'blue' },
  { id: 'biodiversity', labelKey: 'how.interactive.materiality.biodiversity', icon: Leaf, financial: 30, impact: 65, color: 'green' },
  { id: 'workers', labelKey: 'how.interactive.materiality.workers', icon: Users, financial: 55, impact: 75, color: 'purple' },
  { id: 'community', labelKey: 'how.interactive.materiality.community', icon: Building2, financial: 40, impact: 60, color: 'rose' },
]

const carbonSources = [
  { id: 'electricity', labelKey: 'how.interactive.carbon.electricity', icon: Zap, unit: 'MWh', min: 0, max: 5000, step: 100, default: 800 },
  { id: 'gas', labelKey: 'how.interactive.carbon.gas', icon: Flame, unit: 'MWh', min: 0, max: 3000, step: 50, default: 500 },
  { id: 'fuel', labelKey: 'how.interactive.carbon.fuel', icon: Truck, unit: 'litri', min: 0, max: 100000, step: 1000, default: 15000 },
]

const emissionFactors: Record<string, number> = {
  electricity: 0.233, // kgCO2/kWh
  gas: 0.202, // kgCO2/kWh
  fuel: 2.68, // kgCO2/litro
}

export default function HowItWorksPage() {
  const { t } = useLanguage()
  const [currentStep, setCurrentStep] = useState(0)
  const [stepStatuses, setStepStatuses] = useState<StepStatus[]>(['in-progress', 'incomplete', 'incomplete', 'incomplete'])
  const [direction, setDirection] = useState<'forward' | 'backward'>('forward')
  const [animating, setAnimating] = useState(false)

  // Step 1: Assessment state
  const [selectedSize, setSelectedSize] = useState<string | null>(null)
  const [selectedSector, setSelectedSector] = useState<string | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisComplete, setAnalysisComplete] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)

  // Step 2: Materiality state
  const [selectedImpacts, setSelectedImpacts] = useState<string[]>([])
  const [showMaterialityResult, setShowMaterialityResult] = useState(false)

  // Step 3: Carbon state
  const [carbonValues, setCarbonValues] = useState<Record<string, number>>({
    electricity: 800,
    gas: 500,
    fuel: 15000,
  })
  const [showCarbonResult, setShowCarbonResult] = useState(false)

  // Step 4: Report state
  const [reportTab, setReportTab] = useState<'dashboard' | 'ixbrl' | 'pdf'>('dashboard')
  const [showReportCTA, setShowReportCTA] = useState(false)

  const progressPercentage = (((currentStep + 1) / 4) * 100)

  const goToStep = useCallback((step: number) => {
    if (animating) return
    if (step === currentStep) return
    setDirection(step > currentStep ? 'forward' : 'backward')
    setAnimating(true)
    setTimeout(() => {
      setCurrentStep(step)
      setAnimating(false)
    }, 300)
  }, [currentStep, animating])

  const completeStep = useCallback(() => {
    setStepStatuses(prev => {
      const next = [...prev]
      next[currentStep] = 'complete'
      return next
    })
    if (currentStep < 3) {
      setStepStatuses(prev => {
        const next = [...prev]
        next[currentStep + 1] = 'in-progress'
        return next
      })
      goToStep(currentStep + 1)
    }
  }, [currentStep, goToStep])

  // Simulate AI analysis for step 1
  const startAnalysis = useCallback(() => {
    if (!selectedSize || !selectedSector) return
    setAnalyzing(true)
    setAnalysisProgress(0)
    const interval = setInterval(() => {
      setAnalysisProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          setAnalyzing(false)
          setAnalysisComplete(true)
          return 100
        }
        return prev + Math.random() * 15 + 5
      })
    }, 400)
  }, [selectedSize, selectedSector])

  const calculateTotalEmissions = useCallback(() => {
    const total = carbonSources.reduce((sum, source) => {
      return sum + (carbonValues[source.id] || 0) * emissionFactors[source.id]
    }, 0)
    return Math.round(total)
  }, [carbonValues])

  const resetAll = useCallback(() => {
    setCurrentStep(0)
    setStepStatuses(['in-progress', 'incomplete', 'incomplete', 'incomplete'])
    setSelectedSize(null)
    setSelectedSector(null)
    setAnalyzing(false)
    setAnalysisComplete(false)
    setAnalysisProgress(0)
    setSelectedImpacts([])
    setShowMaterialityResult(false)
    setCarbonValues({ electricity: 800, gas: 500, fuel: 15000 })
    setShowCarbonResult(false)
    setShowReportCTA(false)
    setDirection('forward')
  }, [])

  const toggleImpact = (id: string) => {
    setSelectedImpacts(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    )
  }

  const renderStepIndicator = () => (
    <div className="mb-10">
      <div className="flex items-center justify-between mb-3">
        {[0, 1, 2, 3].map((step) => {
          const Icon = stepIcons[step]
          const status = stepStatuses[step]
          const isActive = currentStep === step
          return (
            <button
              key={step}
              onClick={() => {
                if (step <= currentStep || stepStatuses[step - 1] === 'complete') {
                  goToStep(step)
                }
              }}
              className={`flex flex-col items-center gap-1.5 group ${(step <= currentStep || stepStatuses[step - 1] === 'complete') ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'}`}
            >
              <div className={`
                w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300
                ${status === 'complete'
                  ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-200'
                  : isActive
                    ? 'bg-emerald-100 text-emerald-600 ring-2 ring-emerald-500 ring-offset-2'
                    : 'bg-gray-100 text-gray-400 group-hover:bg-gray-200'}
              `}>
                {status === 'complete' ? (
                  <CheckCircle2 className="h-5 w-5" />
                ) : (
                  <Icon className="h-4 w-4" />
                )}
              </div>
              <span className={`text-[10px] font-medium hidden md:block ${isActive ? 'text-emerald-600' : 'text-gray-500'}`}>
                {t(`how.step${step + 1}.title`).split(' ').slice(0, 2).join(' ')}
              </span>
            </button>
          )
        })}
      </div>
      <Progress value={((currentStep + 1) / 4) * 100} className="h-2 bg-gray-100" />
      <div className="flex justify-between mt-1.5">
        <span className="text-xs text-emerald-600 font-medium">
          {t('how.interactive.step')} {currentStep + 1} {t('how.interactive.of')} 4
        </span>
        <span className="text-xs text-gray-500">{Math.round((currentStep + 1) / 4 * 100)}%</span>
      </div>
    </div>
  )

  const renderNavigation = (showComplete = true) => (
    <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-100">
      <Button
        variant="outline"
        onClick={() => goToStep(currentStep - 1)}
        disabled={currentStep === 0 || animating}
        className="gap-2"
      >
        <ArrowLeft className="h-4 w-4" />
        {t('how.interactive.back')}
      </Button>

      <div className="flex gap-3">
        {currentStep === 3 && showReportCTA ? (
          <Link href="/auth/register">
            <Button size="lg" className="gap-2 bg-emerald-600 hover:bg-emerald-700">
              {t('pricing.trial')}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        ) : showComplete ? (
          <Button onClick={completeStep} disabled={animating} className="gap-2">
            {currentStep === 3 ? t('how.interactive.finish') : t('how.interactive.continue')}
            <ChevronRight className="h-4 w-4" />
          </Button>
        ) : null}
      </div>
    </div>
  )

  const renderStepContent = () => {
    const slideClass = animating
      ? direction === 'forward'
        ? 'animate-slide-in-from-right-8'
        : 'animate-slide-in-from-left-8'
      : 'animate-fade-in'

    switch (currentStep) {
      case 0:
        return (
          <div key="step-0" className={slideClass}>
            <div className="text-center mb-8">
              <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full text-xs font-medium mb-3">
                <PlayCircle className="h-3.5 w-3.5" />
                {t('how.interactive.try')}
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">{t('how.step1.title')}</h2>
              <p className="text-gray-500 text-sm">{t('how.step1.desc')}</p>
            </div>

            {!analysisComplete ? (
              <div className="space-y-6 max-w-xl mx-auto">
                {/* Company Size */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-3">
                    {t('how.interactive.quiz.size')}
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {companySizes.map(size => {
                      const isSelected = selectedSize === size.id
                      const Icon = size.icon
                      return (
                        <button
                          key={size.id}
                          onClick={() => !analyzing && setSelectedSize(size.id)}
                          disabled={analyzing}
                          className={`
                            relative p-4 rounded-xl border-2 text-center transition-all duration-200
                            ${isSelected
                              ? 'border-emerald-500 bg-emerald-50 shadow-sm'
                              : 'border-gray-200 hover:border-emerald-200 hover:bg-emerald-50/50'}
                            ${analyzing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                          `}
                        >
                          <Icon className={`h-6 w-6 mx-auto mb-2 ${isSelected ? 'text-emerald-600' : 'text-gray-400'}`} />
                          <span className={`text-sm font-medium block ${isSelected ? 'text-emerald-700' : 'text-gray-600'}`}>
                            {t(size.labelKey)}
                          </span>
                          <span className="text-xs text-gray-400 mt-1 block">{size.employees}</span>
                          {isSelected && (
                            <CheckCircle2 className="absolute top-2 right-2 h-4 w-4 text-emerald-500" />
                          )}
                        </button>
                      )
                    })}
                  </div>
                </div>

                {/* Company Sector */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-3">
                    {t('how.interactive.quiz.sector')}
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {companySectors.map(sector => {
                      const isSelected = selectedSector === sector.id
                      const Icon = sector.icon
                      return (
                        <button
                          key={sector.id}
                          onClick={() => !analyzing && setSelectedSector(sector.id)}
                          disabled={analyzing}
                          className={`
                            relative p-4 rounded-xl border-2 text-center transition-all duration-200
                            ${isSelected
                              ? 'border-emerald-500 bg-emerald-50 shadow-sm'
                              : 'border-gray-200 hover:border-emerald-200 hover:bg-emerald-50/50'}
                            ${analyzing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                          `}
                        >
                          <Icon className={`h-6 w-6 mx-auto mb-2 ${isSelected ? 'text-emerald-600' : 'text-gray-400'}`} />
                          <span className={`text-sm font-medium block ${isSelected ? 'text-emerald-700' : 'text-gray-600'}`}>
                            {t(sector.labelKey)}
                          </span>
                          {isSelected && (
                            <CheckCircle2 className="absolute top-2 right-2 h-4 w-4 text-emerald-500" />
                          )}
                        </button>
                      )
                    })}
                  </div>
                </div>

                {selectedSize && selectedSector && !analyzing && (
                  <div className="text-center pt-2">
                    <Button onClick={startAnalysis} size="lg" className="gap-2">
                      <Sparkles className="h-4 w-4" />
                      {t('how.interactive.analyze')}
                    </Button>
                  </div>
                )}

                {analyzing && (
                  <div className="text-center py-6 space-y-4">
                    <div className="flex justify-center">
                      <div className="relative">
                        <div className="w-16 h-16 border-4 border-emerald-100 rounded-full" />
                        <div className="absolute top-0 left-0 w-16 h-16 border-4 border-emerald-500 rounded-full border-t-transparent animate-spin" />
                        <Brain className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-6 w-6 text-emerald-600" />
                      </div>
                    </div>
                    <p className="text-sm text-emerald-600 font-medium">{t('how.interactive.analyzing')}</p>
                    <Progress value={Math.min(analysisProgress, 100)} className="h-2 max-w-xs mx-auto" />
                  </div>
                )}
              </div>
            ) : (
              <div className="max-w-xl mx-auto text-center space-y-4 animate-fade-in">
                <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-2 rounded-full">
                  <CheckCircle2 className="h-5 w-5" />
                  <span className="font-medium">{t('how.interactive.analysis.ready')}</span>
                </div>
                <Card className="bg-gradient-to-br from-emerald-50 to-white border-emerald-100">
                  <CardContent className="p-6 space-y-4">
                    <h3 className="font-semibold text-gray-900">{t('how.interactive.analysis.result')}</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-white rounded-lg p-3 border border-emerald-100">
                        <p className="text-xs text-gray-500 mb-1">{t('how.interactive.quiz.size')}</p>
                        <p className="font-semibold text-gray-900">
                          {t(companySizes.find(s => s.id === selectedSize)?.labelKey || '')}
                        </p>
                      </div>
                      <div className="bg-white rounded-lg p-3 border border-emerald-100">
                        <p className="text-xs text-gray-500 mb-1">{t('how.interactive.quiz.sector')}</p>
                        <p className="font-semibold text-gray-900">
                          {t(companySectors.find(s => s.id === selectedSector)?.labelKey || '')}
                        </p>
                      </div>
                    </div>
                    <div className="bg-emerald-50 rounded-lg p-3 text-left">
                      <p className="text-sm text-emerald-800">
                        <span className="font-semibold">{t('how.interactive.analysis.applicable')}: </span>
                        ESRS E1, ESRS E2, ESRS S1, ESRS G1
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        )

      case 1:
        return (
          <div key="step-1" className={slideClass}>
            <div className="text-center mb-8">
              <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full text-xs font-medium mb-3">
                <PlayCircle className="h-3.5 w-3.5" />
                {t('how.interactive.try')}
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">{t('how.step2.title')}</h2>
              <p className="text-gray-500 text-sm">{t('how.step2.desc')}</p>
            </div>

            {!showMaterialityResult ? (
              <div className="max-w-xl mx-auto space-y-4">
                <p className="text-sm text-gray-600 text-center mb-4">
                  {t('how.interactive.materiality.choose')}
                </p>
                <div className="grid grid-cols-2 gap-3">
                  {materialityItems.map(item => {
                    const isSelected = selectedImpacts.includes(item.id)
                    const Icon = item.icon
                    return (
                      <button
                        key={item.id}
                        onClick={() => toggleImpact(item.id)}
                        className={`
                          relative p-4 rounded-xl border-2 text-left transition-all duration-200
                          ${isSelected
                            ? 'border-emerald-500 bg-emerald-50 shadow-sm'
                            : 'border-gray-200 hover:border-emerald-200 hover:bg-emerald-50/50'}
                        `}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`
                            w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0
                            ${isSelected ? 'bg-emerald-200' : 'bg-gray-100'}
                          `}>
                            <Icon className={`h-5 w-5 ${isSelected ? 'text-emerald-700' : 'text-gray-500'}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900">{t(item.labelKey)}</p>
                            <div className="flex gap-2 mt-1.5">
                              <span className="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                                F: {item.financial}%
                              </span>
                              <span className="text-[10px] bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded">
                                I: {item.impact}%
                              </span>
                            </div>
                          </div>
                          {isSelected && (
                            <CheckCircle2 className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                          )}
                        </div>
                      </button>
                    )
                  })}
                </div>

                {selectedImpacts.length >= 2 && (
                  <div className="text-center pt-2">
                    <Button onClick={() => setShowMaterialityResult(true)} size="lg" className="gap-2">
                      <BarChart3 className="h-4 w-4" />
                      {t('how.interactive.materiality.visualize')}
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="max-w-xl mx-auto space-y-4 animate-fade-in">
                <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-2 rounded-full mx-auto w-fit">
                  <CheckCircle2 className="h-5 w-5" />
                  <span className="font-medium">{t('how.interactive.materiality.matrix')}</span>
                </div>

                {/* Materiality Matrix Visualization */}
                <Card className="bg-white border-gray-200">
                  <CardContent className="p-4">
                    <div className="relative">
                      {/* Axis labels */}
                      <div className="flex justify-between mb-2 text-xs text-gray-400">
                        <span>{t('how.interactive.materiality.axis.impact')}</span>
                        <span>{t('how.interactive.materiality.axis.financial')}</span>
                      </div>

                      {/* Matrix grid */}
                      <div className="grid grid-cols-5 gap-1.5 aspect-square max-w-[300px] mx-auto">
                        {[4, 3, 2, 1, 0].map(row => (
                          [0, 1, 2, 3, 4].map(col => {
                            const intensity = Math.sqrt((row + 1) * (col + 1)) / 5
                            return (
                              <div
                                key={`${row}-${col}`}
                                className={`
                                  rounded aspect-square transition-colors duration-500
                                  ${intensity > 0.7 ? 'bg-emerald-500' :
                                    intensity > 0.4 ? 'bg-emerald-300' :
                                    intensity > 0.2 ? 'bg-emerald-100' :
                                    'bg-gray-50'}
                                `}
                              />
                            )
                          })
                        ))}
                      </div>

                      {/* Selected items plotted */}
                      <div className="mt-4 space-y-2">
                        {materialityItems.filter(i => selectedImpacts.includes(i.id)).map(item => (
                          <div key={item.id} className="flex items-center gap-3 p-2 rounded-lg bg-gray-50">
                            <div className="w-2 h-2 rounded-full bg-emerald-500" />
                            <span className="text-sm text-gray-700 flex-1">{t(item.labelKey)}</span>
                            <span className="text-xs text-gray-400">
                              F:{item.financial}% I:{item.impact}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <p className="text-xs text-gray-500 text-center">
                  {t('how.interactive.materiality.explanation')}
                </p>
              </div>
            )}
          </div>
        )

      case 2:
        return (
          <div key="step-2" className={slideClass}>
            <div className="text-center mb-8">
              <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full text-xs font-medium mb-3">
                <PlayCircle className="h-3.5 w-3.5" />
                {t('how.interactive.try')}
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">{t('how.step3.title')}</h2>
              <p className="text-gray-500 text-sm">{t('how.step3.desc')}</p>
            </div>

            {!showCarbonResult ? (
              <div className="max-w-xl mx-auto space-y-6">
                {carbonSources.map(source => {
                  const Icon = source.icon
                  return (
                    <div key={source.id} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center">
                            <Icon className="h-4 w-4 text-emerald-600" />
                          </div>
                          <span className="text-sm font-medium text-gray-700">{t(source.labelKey)}</span>
                        </div>
                        <span className="text-sm font-semibold text-gray-900">
                          {carbonValues[source.id].toLocaleString()} {source.unit}
                        </span>
                      </div>
                      <input
                        type="range"
                        min={source.min}
                        max={source.max}
                        step={source.step}
                        value={carbonValues[source.id]}
                        onChange={(e) => {
                          setCarbonValues(prev => ({ ...prev, [source.id]: parseInt(e.target.value) }))
                          setShowCarbonResult(false)
                        }}
                        className="w-full h-2 bg-gray-100 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                      />
                      <div className="flex justify-between text-xs text-gray-400">
                        <span>{source.min.toLocaleString()}</span>
                        <span>{source.max.toLocaleString()}</span>
                      </div>
                    </div>
                  )
                })}

                <div className="text-center pt-2">
                  <Button onClick={() => setShowCarbonResult(true)} size="lg" className="gap-2">
                    <Leaf className="h-4 w-4" />
                    {t('how.interactive.carbon.calculate')}
                  </Button>
                </div>
              </div>
            ) : (
              <div className="max-w-xl mx-auto space-y-4 animate-fade-in">
                <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-2 rounded-full mx-auto w-fit">
                  <CheckCircle2 className="h-5 w-5" />
                  <span className="font-medium">{t('how.interactive.carbon.result')}</span>
                </div>

                <Card className="bg-gradient-to-br from-emerald-50 to-white border-emerald-100">
                  <CardContent className="p-6">
                    <div className="text-center mb-4">
                      <p className="text-3xl font-bold text-emerald-600">
                        {calculateTotalEmissions().toLocaleString()}
                      </p>
                      <p className="text-sm text-gray-500">tCO₂e / {t('how.interactive.carbon.year')}</p>
                    </div>

                    <div className="space-y-2">
                      {carbonSources.map(source => {
                        const Icon = source.icon
                        const emissions = Math.round((carbonValues[source.id] || 0) * emissionFactors[source.id])
                        const total = calculateTotalEmissions()
                        const percentage = total > 0 ? (emissions / total) * 100 : 0
                        return (
                          <div key={source.id} className="flex items-center gap-3">
                            <div className="w-7 h-7 rounded-lg bg-white flex items-center justify-center">
                              <Icon className="h-3.5 w-3.5 text-gray-500" />
                            </div>
                            <div className="flex-1">
                              <div className="flex justify-between text-xs mb-1">
                                <span className="text-gray-600">{t(source.labelKey)}</span>
                                <span className="font-medium text-gray-900">{emissions.toLocaleString()} t</span>
                              </div>
                              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                                  style={{ width: `${percentage}%` }}
                                />
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        )

      case 3:
        return (
          <div key="step-3" className={slideClass}>
            <div className="text-center mb-8">
              <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full text-xs font-medium mb-3">
                <PlayCircle className="h-3.5 w-3.5" />
                {t('how.interactive.try')}
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">{t('how.step4.title')}</h2>
              <p className="text-gray-500 text-sm">{t('how.step4.desc')}</p>
            </div>

            <div className="max-w-xl mx-auto">
              {/* Report type tabs */}
              <div className="flex gap-2 mb-6 bg-gray-50 p-1.5 rounded-xl">
                {(['dashboard', 'ixbrl', 'pdf'] as const).map(tab => (
                  <button
                    key={tab}
                    onClick={() => setReportTab(tab)}
                    className={`
                      flex-1 py-2.5 px-3 rounded-lg text-sm font-medium transition-all duration-200
                      ${reportTab === tab
                        ? 'bg-white text-emerald-700 shadow-sm'
                        : 'text-gray-500 hover:text-gray-700'}
                    `}
                  >
                    {tab === 'dashboard' && <BarChart3 className="h-4 w-4 inline mr-1.5" />}
                    {tab === 'ixbrl' && <FileText className="h-4 w-4 inline mr-1.5" />}
                    {tab === 'pdf' && <Download className="h-4 w-4 inline mr-1.5" />}
                    {tab.toUpperCase()}
                  </button>
                ))}
              </div>

              {/* Report Preview */}
              <Card className="border-gray-200 overflow-hidden">
                <CardContent className="p-0">
                  {reportTab === 'dashboard' && (
                    <div className="p-4 space-y-4 animate-fade-in">
                      <div className="grid grid-cols-3 gap-3">
                        {[
                          { label: t('how.interactive.report.scope1'), value: '245', unit: 'tCO₂e', color: 'emerald' },
                          { label: t('how.interactive.report.scope2'), value: '186', unit: 'tCO₂e', color: 'blue' },
                          { label: t('how.interactive.report.scope3'), value: '1,892', unit: 'tCO₂e', color: 'amber' },
                        ].map((item, i) => {
                          const colorMap: Record<string, string> = { 'emerald': 'text-emerald-600', 'blue': 'text-blue-600', 'amber': 'text-amber-600' }
                          return (
                            <div key={i} className="bg-gray-50 rounded-lg p-3 text-center">
                              <p className="text-xs text-gray-500 mb-1">{item.label}</p>
                              <p className={`text-lg font-bold ${colorMap[item.color] || 'text-gray-600'}`}>{item.value}</p>
                              <p className="text-[10px] text-gray-400">{item.unit}</p>
                            </div>
                          )
                        })}
                      </div>
                      <div className="bg-emerald-50 rounded-lg p-3">
                        <div className="flex items-center gap-2 text-sm text-emerald-800">
                          <TrendingUp className="h-4 w-4" />
                          <span className="font-medium">{t('how.interactive.report.trend')}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {reportTab === 'ixbrl' && (
                    <div className="p-4 space-y-3 animate-fade-in">
                      <div className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3">
                        <FileText className="h-4 w-4" />
                        {t('how.interactive.report.ixbrl')}
                      </div>
                      <div className="bg-gray-50 rounded-lg p-3 font-mono text-xs space-y-1 text-gray-500">
                        <p>{'<ix:nonNumeric contextRef="ref1" name="esrs:E1_1">'}</p>
                        <p className="pl-4">{t('how.interactive.report.climate')}</p>
                        <p>{'</ix:nonNumeric>'}</p>
                        <p>{'<ix:nonFraction contextRef="ref2" name="esrs:E1_2" format="ixt:numdotdecimal">'}</p>
                        <p className="pl-4">245.0</p>
                        <p>{'</ix:nonFraction>'}</p>
                      </div>
                    </div>
                  )}

                  {reportTab === 'pdf' && (
                    <div className="p-4 space-y-3 animate-fade-in">
                      <div className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3">
                        <Download className="h-4 w-4" />
                        {t('how.interactive.report.pdf')}
                      </div>
                      <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                        <div className="border-b border-gray-200 pb-2">
                          <p className="font-semibold text-gray-900 text-sm">CSRD {t('how.interactive.report.report')}</p>
                          <p className="text-xs text-gray-400">{t('how.interactive.report.sustainability')}</p>
                        </div>
                        <div className="space-y-2">
                          {[t('how.interactive.report.executive'), t('how.interactive.report.materiality'), t('how.interactive.report.emissions')].map((section, i) => (
                            <div key={i} className="flex items-center gap-2 text-xs text-gray-600">
                              <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                              {section}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              <div className="text-center mt-4">
                <Button
                  onClick={() => setShowReportCTA(true)}
                  variant="outline"
                  className="gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  {t('how.interactive.report.switch')}
                </Button>
              </div>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  const canProceed = () => {
    switch (currentStep) {
      case 0: return analysisComplete
      case 1: return showMaterialityResult
      case 2: return showCarbonResult
      case 3: return showReportCTA
      default: return false
    }
  }

  return (
    <>
      {/* Hero */}
      <section className="bg-gradient-to-b from-emerald-50 to-white pt-20 pb-12">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
            <Shield className="h-4 w-4" />
            {t('how.title')}
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            {t('how.title')}
          </h1>
          <p className="text-lg text-gray-600 mb-4">
            {t('how.subtitle')}
          </p>
          <button
            onClick={resetAll}
            className="inline-flex items-center gap-1.5 text-xs text-emerald-600 hover:text-emerald-700 transition-colors"
          >
            <RefreshCw className="h-3 w-3" />
            {t('how.interactive.restart')}
          </button>
        </div>
      </section>

      {/* Interactive Demo */}
      <section className="py-8 px-4 bg-white">
        <div className="max-w-3xl mx-auto">
          {renderStepIndicator()}
          {renderStepContent()}
          {currentStep < 3 ? (
            renderNavigation(canProceed())
          ) : (
            renderNavigation(true)
          )}
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4 bg-gradient-to-b from-emerald-50 to-white">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            {t('how.cta')}
          </h2>
          <Link href="/auth/register">
            <Button size="lg" className="text-base px-10 bg-emerald-600 hover:bg-emerald-700">
              {t('pricing.trial')}
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </section>
    </>
  )
}
