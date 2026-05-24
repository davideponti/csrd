'use client'

import { Button } from '@/components/ui'
import { Badge } from '@/components/ui'
import { CheckCircle2, X, Sparkles, ArrowRight, ExternalLink } from 'lucide-react'
import Link from 'next/link'
import { useLanguage } from '@/i18n/LanguageContext'

export default function PricingPage() {
  const { t } = useLanguage()

  const plans = [
    {
      name: t('pricing.starter.name'),
      price: '149',
      description: t('pricing.starter.desc'),
      popular: false,
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
      name: t('pricing.growth.name'),
      price: '299',
      description: t('pricing.growth.desc'),
      popular: true,
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
      name: t('pricing.scale.name'),
      price: '599',
      description: t('pricing.scale.desc'),
      popular: false,
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
      name: t('pricing.enterprise.name'),
      price: '1.299',
      description: t('pricing.enterprise.desc'),
      popular: false,
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
          <p className="text-lg text-gray-600">
            {t('pricing.subtitle')}
          </p>
        </div>
      </section>

      {/* Plans Grid */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`relative rounded-2xl border-2 p-6 flex flex-col transition-all hover:shadow-lg ${
                  plan.popular
                    ? 'border-emerald-500 bg-emerald-50/30 shadow-emerald-100'
                    : 'border-gray-200 bg-white'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge className="bg-emerald-600 text-white px-4 py-1 text-xs font-medium">
                      {plan.highlight}
                    </Badge>
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-lg font-bold text-gray-900">{plan.name}</h3>
                  <p className="text-sm text-gray-500 mt-1">{plan.description}</p>
                  <div className="mt-4 flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-gray-900">€{plan.price}</span>
                    <span className="text-sm text-gray-500">{t('pricing.month')}</span>
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

                <Link href={plan.name === t('pricing.enterprise.name') ? '#' : '/auth/register'}>
                  <Button
                    className={`w-full ${plan.name === t('pricing.enterprise.name') ? 'bg-gray-900 hover:bg-gray-800' : ''}`}
                    variant={plan.popular ? 'default' : plan.name === t('pricing.enterprise.name') ? 'default' : 'outline'}
                    size="lg"
                  >
                    {plan.cta}
                    {plan.name === t('pricing.enterprise.name') ? (
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
                    <th key={p.name} className="text-center py-3 px-4 font-semibold text-gray-900">{p.name}</th>
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
