'use client'

import { useState } from 'react'
import { Button } from '@/components/ui'
import { ChevronDown, ChevronUp, HelpCircle, ArrowRight } from 'lucide-react'
import Link from 'next/link'
import { useLanguage } from '@/i18n/LanguageContext'

export default function FAQPage() {
  const { t } = useLanguage()
  const [openItems, setOpenItems] = useState<Record<string, boolean>>({})

  const toggleItem = (categoryIdx: number, questionIdx: number) => {
    const key = `${categoryIdx}-${questionIdx}`
    setOpenItems((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const faqCategories = [
    {
      title: t('faq.category.general'),
      questions: [
        { q: t('faq.q1.question'), a: t('faq.q1.answer') },
        { q: t('faq.q2.question'), a: t('faq.q2.answer') },
      ],
    },
    {
      title: t('faq.category.subscription'),
      questions: [
        { q: t('faq.q3.question'), a: t('faq.q3.answer') },
        { q: t('faq.q4.question'), a: t('faq.q4.answer') },
      ],
    },
    {
      title: t('faq.category.platform'),
      questions: [
        { q: t('faq.q6.question'), a: t('faq.q6.answer') },
        { q: t('faq.q7.question'), a: t('faq.q7.answer') },
        { q: t('faq.q8.question'), a: t('faq.q8.answer') },
      ],
    },
    {
      title: t('faq.category.security'),
      questions: [
        { q: t('faq.q5.question'), a: t('faq.q5.answer') },
      ],
    },
  ]

  return (
    <>
      {/* Hero */}
      <section className="bg-gradient-to-b from-emerald-50 to-white py-20">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
            <HelpCircle className="h-4 w-4" />
            FAQ
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            {t('faq.title')}
          </h1>
          <p className="text-lg text-gray-600">
            {t('faq.subtitle')}
          </p>
        </div>
      </section>

      {/* FAQ Accordion */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-3xl mx-auto">
          {faqCategories.map((category, catIdx) => (
            <div key={category.title} className="mb-10">
              <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                <span className="w-8 h-0.5 bg-emerald-500 rounded-full inline-block" />
                {category.title}
              </h2>
              <div className="space-y-3">
                {category.questions.map((item, qIdx) => {
                  const key = `${catIdx}-${qIdx}`
                  const isOpen = openItems[key]
                  return (
                    <div
                      key={qIdx}
                      className="border border-gray-200 rounded-xl overflow-hidden transition-all hover:border-emerald-200"
                    >
                      <button
                        onClick={() => toggleItem(catIdx, qIdx)}
                        className="w-full flex items-center justify-between p-5 text-left bg-white hover:bg-gray-50 transition-colors"
                      >
                        <span className="text-sm font-medium text-gray-900 pr-4">
                          {item.q}
                        </span>
                        {isOpen ? (
                          <ChevronUp className="h-4 w-4 text-emerald-600 shrink-0" />
                        ) : (
                          <ChevronDown className="h-4 w-4 text-gray-400 shrink-0" />
                        )}
                      </button>
                      {isOpen && (
                        <div className="px-5 pb-5 pt-0 border-t border-gray-100">
                          <p className="text-sm text-gray-600 leading-relaxed">
                            {item.a}
                          </p>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Still have questions */}
      <section className="py-16 px-4 bg-gray-50">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">{t('cta.title')}</h2>
          <p className="text-gray-600 mb-8">{t('cta.subtitle')}</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/auth/register">
              <Button size="lg" className="text-base px-8">
                {t('cta.button')}
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link href="/pricing">
              <Button size="lg" variant="outline" className="text-base px-8">
                {t('nav.pricing')}
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
