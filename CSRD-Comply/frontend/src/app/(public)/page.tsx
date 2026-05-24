'use client'

import Link from 'next/link'
import { Button } from '@/components/ui'
import { Leaf, Target, FileText, BarChart3, ArrowRight, CheckCircle2 } from 'lucide-react'
import { useLanguage } from '@/i18n/LanguageContext'

export default function HomePage() {
  const { t } = useLanguage()

  return (
    <>
      {/* ── Hero Section ───────────────────────────────────── */}
      <section className="relative overflow-hidden bg-gradient-to-b from-emerald-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-28">
          <div className="text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
              <Leaf className="h-4 w-4" />
              {t('hero.title')}
            </div>
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
              {t('hero.title')}{' '}
              <span className="bg-gradient-to-r from-emerald-600 to-teal-500 bg-clip-text text-transparent">
                PMI Europee
              </span>
            </h1>
            <p className="text-lg md:text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
              {t('hero.subtitle')}
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth/register">
                <Button size="lg" className="w-full sm:w-auto text-base px-8">
                  {t('hero.cta')}
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link href="/how-it-works">
                <Button size="lg" variant="outline" className="w-full sm:w-auto text-base px-8">
                  {t('hero.learn')}
                </Button>
              </Link>
            </div>
            <div className="mt-8 flex items-center justify-center gap-6 text-sm text-gray-500">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                {t('pricing.trial')}
              </span>
            </div>
          </div>
        </div>
        <div className="absolute top-0 right-0 -z-10 w-[600px] h-[600px] bg-emerald-100/50 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 -z-10 w-[400px] h-[400px] bg-teal-100/30 rounded-full blur-3xl" />
      </section>

      {/* ── Features Section ──────────────────────────────── */}
      <section id="features" className="py-20 px-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              {t('features.title')}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {t('features.subtitle')}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-lg hover:border-emerald-200 transition-all">
              <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center mb-5">
                <Target className="h-6 w-6 text-emerald-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">{t('features.materiality.title')}</h3>
              <p className="text-gray-600 mb-4">
                {t('features.materiality.desc')}
              </p>
            </div>

            <div className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-lg hover:border-emerald-200 transition-all">
              <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center mb-5">
                <BarChart3 className="h-6 w-6 text-emerald-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">{t('features.carbon.title')}</h3>
              <p className="text-gray-600 mb-4">
                {t('features.carbon.desc')}
              </p>
            </div>

            <div className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-lg hover:border-emerald-200 transition-all">
              <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center mb-5">
                <FileText className="h-6 w-6 text-emerald-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">{t('features.reporting.title')}</h3>
              <p className="text-gray-600 mb-4">
                {t('features.reporting.desc')}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats Section ─────────────────────────────────── */}
      <section className="py-16 bg-emerald-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {[
              { value: '320+', label: 'Datapoint ESRS' },
              { value: '100%', label: 'CSRD' },
              { value: '7 gg', label: t('pricing.trial') },
              { value: '24/7', label: 'AI' },
            ].map((stat) => (
              <div key={stat.label}>
                <p className="text-3xl md:text-4xl font-bold text-white">{stat.value}</p>
                <p className="text-sm text-emerald-200 mt-1">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA Section ───────────────────────────────────── */}
      <section className="py-20 px-4 bg-gradient-to-b from-white to-emerald-50">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            {t('cta.title')}
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            {t('cta.subtitle')}
          </p>
          <Link href="/auth/register">
            <Button size="lg" className="text-base px-10">
              {t('cta.button')}
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </section>
    </>
  )
}
