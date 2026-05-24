'use client'

import { Button } from '@/components/ui'
import { ClipboardCheck, BarChart3, FileText, Brain, Shield, ArrowRight, CheckCircle2 } from 'lucide-react'
import Link from 'next/link'
import { useLanguage } from '@/i18n/LanguageContext'

export default function HowItWorksPage() {
  const { t } = useLanguage()

  const steps = [
    {
      icon: ClipboardCheck,
      title: t('how.step1.title'),
      description: t('how.step1.desc'),
    },
    {
      icon: Brain,
      title: t('how.step2.title'),
      description: t('how.step2.desc'),
    },
    {
      icon: BarChart3,
      title: t('how.step3.title'),
      description: t('how.step3.desc'),
    },
    {
      icon: FileText,
      title: t('how.step4.title'),
      description: t('how.step4.desc'),
    },
  ]

  return (
    <>
      {/* Hero */}
      <section className="bg-gradient-to-b from-emerald-50 to-white py-20">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
            <Shield className="h-4 w-4" />
            {t('how.title')}
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            {t('how.title')}
          </h1>
          <p className="text-lg text-gray-600">
            {t('how.subtitle')}
          </p>
        </div>
      </section>

      {/* Steps */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-4xl mx-auto">
          <div className="space-y-16">
            {steps.map((step, idx) => (
              <div key={idx} className="grid grid-cols-1 md:grid-cols-5 gap-8 items-start">
                <div className="md:col-span-2">
                  <div className="w-14 h-14 bg-emerald-100 rounded-xl flex items-center justify-center mb-4">
                    <step.icon className="h-7 w-7 text-emerald-600" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-3">{step.title}</h2>
                  <p className="text-gray-600">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4 bg-gradient-to-b from-emerald-50 to-white">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            {t('how.cta')}
          </h2>
          <Link href="/auth/register">
            <Button size="lg" className="text-base px-10">
              {t('pricing.trial')}
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </section>
    </>
  )
}
