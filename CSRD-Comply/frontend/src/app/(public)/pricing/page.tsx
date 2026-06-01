'use client'

import { useState, useMemo } from 'react'
import { Button } from '@/components/ui'
import { Badge } from '@/components/ui'
import { CheckCircle2, X, Sparkles, ArrowRight, ExternalLink, Percent, Users } from 'lucide-react'
import Link from 'next/link'
import { useLanguage } from '@/i18n/LanguageContext'

const MONTHLY_PRICES: Record<string, number> = {
  'Starter': 149,
  'Growth': 299,
  'Scale': 599,
  'Enterprise': 1299,
}

const ANNUAL_DISCOUNT = 0.2 // 20%

function getSuggestedPlan(employees: number): string {
  if (employees <= 50) return 'Starter'
  if (employees <= 150) return 'Growth'
  if (employees <= 250) return 'Scale'
  return 'Enterprise'
}

export default function PricingPage() {
  const { t } = useLanguage()
  const [isYearly, setIsYearly] = useState(false)
  const [employees, setEmployees] = useState(75)
  const suggestedPlan = getSuggestedPlan(employees)

  // Find which plan index matches the suggested
  const planNames = [t('pricing.starter.name'), t('pricing.growth.name'), t('pricing.scale.name'), t('pricing.enterprise.name')]
  const rawNames = ['Starter', 'Growth', 'Scale', 'Enterprise']

  const suggestedIndex = rawNames.indexOf(suggestedPlan)

  const plans = useMemo(() => {
    const nameMap: Record<string, string> = {
      'Starter': t('pricing.starter.name'),
      'Growth': t('pricing.growth.name'),
      'Scale': t('pricing.scale.name'),
      'Enterprise': t('pricing.enterprise.name'),
    }

    const getPrice = (rawName: string) => {
      const monthly = MONTHLY_PRICES[rawName]
      if (isYearly) return Math.round(monthly * (1 - ANNUAL_DISCOUNT))
      return monthly
    }

    const getAnnualTotal = (rawName: string) => {
      return Math.round(MONTHLY_PRICES[rawName] * 12 * (1 - ANNUAL_DISCOUNT))
    }

    const getAnnualSaving = (rawName: string) => {
      return Math.round(MONTHLY_PRICES[rawName] * 12 * ANNUAL_DISCOUNT)
    }

    const isSuggested = (rawName: string) => rawName === suggestedPlan

    return [
      {
        rawName: 'Starter',
        name: nameMap['Starter'],
        price: getPrice('Starter'),
        annualTotal: getAnnualTotal('Starter'),
        annualSaving: getAnnualSaving('Starter'),
        description: t('pricing.starter.desc'),
        popular: false,
        suggested: isSuggested('Starter'),
        features: [
          { text: t('pricing.starter.feature1'), included: true },
          { text: t('pricing.starter.feature2'), included: true },
          { text: t('pricing.starter.feature3'), included: true },
          { text: t('pricing.starter.feature4'), included: true },
          { text: t('pricing.starter.feature5'), included: true },
          { text: t('pricing.growth.feature4'), included: false },
          { text: t('pricing.growth.feature5'), included: false },
          { text: t('pricing.scale.feature3'), included: false },
          { text: t('pricing.scale.feature4'), included: false },
          { text: t('pricing.scale.feature5'), included: false },
        ],
        cta: t('pricing.trial'),
        highlight: t('pricing.starter.name'),
      },
      {
        rawName: 'Growth',
        name: nameMap['Growth'],
        price: getPrice('Growth'),
        annualTotal: getAnnualTotal('Growth'),
        annualSaving: getAnnualSaving('Growth'),
        description: t('pricing.growth.desc'),
        popular: true,
        suggested: isSuggested('Growth'),
        features: [
          { text: t('pricing.growth.feature1'), included: true },
          { text: t('pricing.growth.feature2'), included: true },
          { text: t('pricing.growth.feature3'), included: true },
          { text: t('pricing.starter.feature4'), included: true },
          { text: t('pricing.starter.feature5'), included: true },
          { text: t('pricing.growth.feature4'), included: true },
          { text: t('pricing.growth.feature5'), included: true },
          { text: t('pricing.scale.feature3'), included: false },
          { text: t('pricing.scale.feature4'), included: false },
          { text: t('pricing.scale.feature5'), included: false },
        ],
        cta: t('pricing.trial'),
        highlight: t('pricing.popular'),
      },
      {
        rawName: 'Scale',
        name: nameMap['Scale'],
        price: getPrice('Scale'),
        annualTotal: getAnnualTotal('Scale'),
        annualSaving: getAnnualSaving('Scale'),
        description: t('pricing.scale.desc'),
        popular: false,
        suggested: isSuggested('Scale'),
        features: [
          { text: t('pricing.scale.feature1'), included: true },
          { text: t('pricing.scale.feature2'), included: true },
          { text: t('pricing.growth.feature3'), included: true },
          { text: t('pricing.starter.feature4'), included: true },
          { text: t('pricing.starter.feature5'), included: true },
          { text: t('pricing.growth.feature4'), included: true },
          { text: t('pricing.growth.feature5'), included: true },
          { text: t('pricing.scale.feature3'), included: true },
          { text: t('pricing.scale.feature4'), included: true },
          { text: t('pricing.scale.feature5'), included: true },
        ],
        cta: t('pricing.trial'),
        highlight: t('pricing.scale.name'),
      },
      {
        rawName: 'Enterprise',
        name: nameMap['Enterprise'],
        price: getPrice('Enterprise'),
        annualTotal: getAnnualTotal('Enterprise'),
        annualSaving: getAnnualSaving('Enterprise'),
        description: t('pricing.enterprise.desc'),
        popular: false,
        suggested: isSuggested('Enterprise'),
        features: [
          { text: t('pricing.enterprise.feature1'), included: true },
          { text: t('pricing.enterprise.feature2'), included: true },
          { text: t('pricing.enterprise.feature3'), included: true },
          { text: t('pricing.enterprise.feature4'), included: true },
          { text: t('pricing.enterprise.feature5'), included: true },
          { text: t('pricing.growth.feature4'), included: true },
          { text: t('pricing.growth.feature5'), included: true },
          { text: t('pricing.scale.feature3'), included: true },
          { text: t('pricing.support.dedicated'), included: true },
          { text: t('pricing.api'), included: true },
        ],
        cta: t('pricing.contact'),
        highlight: t('pricing.enterprise.name'),
      },
    ]
  }, [t, isYearly, suggestedPlan])

  return (
    <>
      {/* Hero */}
      <section className="bg-gradient-to-b from-emerald-50 to-white py-20">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
            <Sparkles className="h-4 w-4" />
            {t('pricing.title')}
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            {t('pricing.title')}
          </h1>
          <p className="text-lg text-gray-600 mb-10">
            {t('pricing.subtitle')}
          </p>

          {/* Interactive Controls */}
          <div className="max-w-lg mx-auto space-y-6">
            {/* Employee Slider */}
            <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-3">
                <Users className="h-4 w-4 text-emerald-600" />
                <span className="text-sm font-medium text-gray-700">{t('pricing.employees')}</span>
              </div>
              <input
                type="range"
                min="1"
                max="500"
                value={employees}
                onChange={(e) => setEmployees(Number(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-full appearance-none cursor-pointer accent-emerald-600"
              />
              <div className="flex justify-between mt-2">
                <span className="text-xs text-gray-400">1</span>
                <span className="text-sm font-bold text-emerald-700 bg-emerald-50 px-3 py-0.5 rounded-full">
                  {employees} {employees === 1 ? t('pricing.employee') : t('pricing.employees.count')}
                </span>
                <span className="text-xs text-gray-400">500+</span>
              </div>
              {/* Suggested plan */}
              <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-center gap-2">
                <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                <span className="text-xs text-gray-500">
                  {t('pricing.suggested')}:{' '}
                  <span className="font-semibold text-emerald-700">{planNames[suggestedIndex]}</span>
                </span>
              </div>
            </div>

            {/* Monthly/Yearly Toggle */}
            <div className="bg-white rounded-2xl border border-gray-200 p-2 shadow-sm inline-flex items-center gap-2">
              <button
                onClick={() => setIsYearly(false)}
                className={`px-5 py-2 rounded-xl text-sm font-medium transition-all ${
                  !isYearly
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {t('pricing.monthly')}
              </button>
              <button
                onClick={() => setIsYearly(true)}
                className={`px-5 py-2 rounded-xl text-sm font-medium transition-all flex items-center gap-2 ${
                  isYearly
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {t('pricing.yearly')}
                {!isYearly && (
                  <Badge className="bg-amber-100 text-amber-700 border-0 text-[10px] px-1.5 py-0">
                    -20%
                  </Badge>
                )}
                {isYearly && (
                  <Badge className="bg-amber-200 text-amber-800 border-0 text-[10px] px-1.5 py-0">
                    -20%
                  </Badge>
                )}
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Plans Grid */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {plans.map((plan) => (
              <div
                key={plan.rawName}
                className={`relative rounded-2xl border-2 p-6 flex flex-col transition-all duration-300 hover:shadow-lg ${
                  plan.suggested
                    ? 'border-emerald-500 bg-emerald-50/30 shadow-emerald-100 ring-1 ring-emerald-500/30'
                    : plan.popular
                    ? 'border-emerald-500 bg-emerald-50/30 shadow-emerald-100'
                    : 'border-gray-200 bg-white'
                }`}
              >
                {/* Suggested badge (highest priority) */}
                {plan.suggested && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
                    <Badge className="bg-amber-500 text-white px-4 py-1 text-xs font-medium shadow-sm">
                      <Sparkles className="h-3 w-3 mr-1 inline" />
                      {t('pricing.suggested')}
                    </Badge>
                  </div>
                )}
                {/* Popular badge */}
                {plan.popular && !plan.suggested && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge className="bg-emerald-600 text-white px-4 py-1 text-xs font-medium">
                      {plan.highlight}
                    </Badge>
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-lg font-bold text-gray-900">{plan.name}</h3>
                  <p className="text-sm text-gray-500 mt-1">{plan.description}</p>
                  <div className="mt-4">
                    <div className="flex items-baseline gap-1">
                      <span className="text-3xl font-bold text-gray-900">€{plan.price}</span>
                      <span className="text-sm text-gray-500">
                        {isYearly ? t('pricing.year') : t('pricing.month')}
                      </span>
                    </div>
                    {isYearly && (
                      <div className="mt-1 space-y-0.5">
                        <p className="text-xs text-gray-400">
                          {t('pricing.annual.total')}: €{plan.annualTotal.toLocaleString()}{isYearly ? t('pricing.year') : t('pricing.month')}
                        </p>
                        <p className="text-xs text-emerald-600 font-medium flex items-center gap-1">
                          <Percent className="h-3 w-3" />
                          {t('pricing.annual.saving')}: €{plan.annualSaving.toLocaleString()}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <ul className="space-y-3 flex-1 mb-6">
                  {plan.features.map((feature) => (
                    <li key={feature.text} className="flex items-start gap-2 text-sm">
                      {feature.included ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-500 mt-0.5 shrink-0" />
                      ) : (
                        <X className="h-4 w-4 text-gray-300 mt-0.5 shrink-0" />
                      )}
                      <span className={feature.included ? 'text-gray-700' : 'text-gray-400'}>
                        {feature.text}
                      </span>
                    </li>
                  ))}
                </ul>

                <Link href={plan.rawName === 'Enterprise' ? '#' : '/auth/register'}>
                  <Button
                    className={`w-full ${
                      plan.suggested
                        ? 'bg-amber-500 hover:bg-amber-600 text-white'
                        : plan.rawName === 'Enterprise'
                        ? 'bg-gray-900 hover:bg-gray-800'
                        : ''
                    }`}
                    variant={plan.popular && !plan.suggested ? 'default' : plan.rawName === 'Enterprise' ? 'default' : 'outline'}
                    size="lg"
                  >
                    {plan.cta}
                    {plan.rawName === 'Enterprise' ? (
                      <ExternalLink className="ml-2 h-4 w-4" />
                    ) : (
                      <ArrowRight className="ml-2 h-4 w-4" />
                    )}
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Comparison Table */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-10">
            {t('pricing.compare')}
          </h2>
          
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">{t('pricing.feature')}</th>
                  {plans.map((p) => (
                    <th key={p.rawName} className="text-center py-3 px-4 font-semibold text-gray-900">{p.name}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  { label: t('pricing.users'), values: ['1', '3', '10', t('pricing.unlimited')] },
                  { label: t('pricing.reports'), values: ['1', '3', t('pricing.unlimited'), t('pricing.unlimited')] },
                  { label: 'Scope 1', values: [true, true, true, true] },
                  { label: 'Scope 2', values: [true, true, true, true] },
                  { label: 'Scope 3', values: [false, true, true, true] },
                  { label: t('features.materiality.title'), values: [true, true, true, true] },
                  { label: t('pricing.export'), values: [t('pricing.starter.feature5'), t('pricing.growth.feature4'), `${t('pricing.yes')} iXBRL`, `${t('pricing.yes')} iXBRL`] },
                  { label: t('pricing.alerts'), values: [t('pricing.not.included'), t('pricing.yes'), t('pricing.yes'), t('pricing.yes')] },
                  { label: t('pricing.ai'), values: [t('pricing.not.included'), t('pricing.not.included'), t('pricing.yes'), t('pricing.yes')] },
                  { label: t('pricing.support'), values: [t('pricing.support.basic'), t('pricing.support.basic'), t('pricing.support.priority'), t('pricing.support.dedicated')] },
                  { label: t('pricing.api'), values: [t('pricing.not.included'), t('pricing.not.included'), t('pricing.not.included'), t('pricing.yes')] },
                ].map((row) => (
                  <tr key={row.label} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 text-gray-700 font-medium">{row.label}</td>
                    {row.values.map((val, i) => (
                      <td key={i} className="text-center py-3 px-4">
                        {typeof val === 'boolean' ? (
                          val ? (
                            <CheckCircle2 className="h-5 w-5 text-emerald-500 mx-auto" />
                          ) : (
                            <X className="h-5 w-5 text-gray-300 mx-auto" />
                          )
                        ) : (
                          <span className="text-gray-700">{val}</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4 bg-gradient-to-b from-emerald-50 to-white">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">{t('cta.title')}</h2>
          <p className="text-lg text-gray-600 mb-8">{t('cta.subtitle')}</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/auth/register">
              <Button size="lg" className="text-base px-10">
                {t('cta.button')}
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link href="/faq">
              <Button size="lg" variant="outline" className="text-base px-10">
                {t('nav.faq')}
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
