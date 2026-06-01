'use client'

import { useState, useMemo } from 'react'
import { Button, Input } from '@/components/ui'
import { Search, ChevronDown, ChevronUp, HelpCircle, ArrowRight, ThumbsUp, ThumbsDown, X } from 'lucide-react'
import Link from 'next/link'
import { useLanguage } from '@/i18n/LanguageContext'

interface FeedbackCounts {
  [key: string]: { yes: number; no: number }
}

export default function FAQPage() {
  const { t } = useLanguage()
  const [openItems, setOpenItems] = useState<Record<string, boolean>>({})
  const [search, setSearch] = useState('')
  const [feedback, setFeedback] = useState<FeedbackCounts>({})
  const [userFeedback, setUserFeedback] = useState<Record<string, 'yes' | 'no' | null>>({})

  const toggleItem = (categoryIdx: number, questionIdx: number) => {
    const key = `${categoryIdx}-${questionIdx}`
    setOpenItems((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const giveFeedback = (key: string, type: 'yes' | 'no') => {
    setFeedback((prev) => ({
      ...prev,
      [key]: {
        yes: prev[key]?.yes || 0,
        no: prev[key]?.no || 0,
        [type]: (prev[key]?.[type] || 0) + 1,
      },
    }))
    setUserFeedback((prev) => ({ ...prev, [key]: type }))
  }

  const faqCategories = useMemo(() => [
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
  ], [t])

  // Flatten all questions with category index for search
  const allQuestions = useMemo(() => {
    const result: Array<{ catIdx: number; qIdx: number; question: string; answer: string; category: string }> = []
    faqCategories.forEach((cat, catIdx) => {
      cat.questions.forEach((item, qIdx) => {
        result.push({
          catIdx,
          qIdx,
          question: item.q,
          answer: item.a,
          category: cat.title,
        })
      })
    })
    return result
  }, [faqCategories])

  const filteredQuestions = useMemo(() => {
    if (!search.trim()) return null
    const q = search.toLowerCase()
    return allQuestions.filter(
      (item) =>
        item.question.toLowerCase().includes(q) ||
        item.answer.toLowerCase().includes(q) ||
        item.category.toLowerCase().includes(q)
    )
  }, [search, allQuestions])

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
          <p className="text-lg text-gray-600 mb-8">
            {t('faq.subtitle')}
          </p>

          {/* Search Bar */}
          <div className="relative max-w-xl mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <Input
              type="text"
              placeholder={t('faq.search')}
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setOpenItems({}) // close all when searching
              }}
              className="pl-12 pr-10 h-14 text-base rounded-2xl border-gray-200 shadow-sm focus:border-emerald-400 focus:ring-emerald-400"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </section>

      {/* FAQ Accordion */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-3xl mx-auto">
          {filteredQuestions ? (
            // Search results
            filteredQuestions.length > 0 ? (
              <div className="space-y-3">
                <p className="text-sm text-gray-500 mb-2">
                  {filteredQuestions.length} {filteredQuestions.length === 1 ? t('faq.result') : t('faq.results')}
                </p>
                {filteredQuestions.map((item, idx) => {
                  const key = `${item.catIdx}-${item.qIdx}`
                  const isOpen = openItems[key]
                  return (
                    <div
                      key={idx}
                      className="border border-gray-200 rounded-xl overflow-hidden transition-all hover:border-emerald-200"
                    >
                      <button
                        onClick={() => toggleItem(item.catIdx, item.qIdx)}
                        className="w-full flex items-center justify-between p-5 text-left bg-white hover:bg-gray-50 transition-colors"
                      >
                        <div className="pr-4">
                          <p className="text-xs text-emerald-600 font-medium mb-1">{item.category}</p>
                          <span className="text-sm font-medium text-gray-900">
                            {item.question}
                          </span>
                        </div>
                        {isOpen ? (
                          <ChevronUp className="h-4 w-4 text-emerald-600 shrink-0" />
                        ) : (
                          <ChevronDown className="h-4 w-4 text-gray-400 shrink-0" />
                        )}
                      </button>
                      {isOpen && (
                        <div className="px-5 pb-5 pt-0 border-t border-gray-100">
                          <p className="text-sm text-gray-600 leading-relaxed mb-3">
                            {item.answer}
                          </p>
                          {/* Feedback */}
                          <div className="flex items-center gap-3 pt-2 border-t border-gray-50">
                            <span className="text-xs text-gray-400">{t('faq.feedback')}</span>
                            <button
                              onClick={() => giveFeedback(key, 'yes')}
                              className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full transition-all ${
                                userFeedback[key] === 'yes'
                                  ? 'bg-emerald-100 text-emerald-700'
                                  : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                              }`}
                            >
                              <ThumbsUp className="h-3 w-3" />
                              {t('faq.feedback.yes')}
                              {(feedback[key]?.yes || 0) > 0 && (
                                <span className="font-medium">{feedback[key].yes}</span>
                              )}
                            </button>
                            <button
                              onClick={() => giveFeedback(key, 'no')}
                              className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full transition-all ${
                                userFeedback[key] === 'no'
                                  ? 'bg-red-100 text-red-600'
                                  : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                              }`}
                            >
                              <ThumbsDown className="h-3 w-3" />
                              {t('faq.feedback.no')}
                              {(feedback[key]?.no || 0) > 0 && (
                                <span className="font-medium">{feedback[key].no}</span>
                              )}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            ) : (
              // No results
              <div className="text-center py-12">
                <Search className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">
                  {t('faq.noresults')} &ldquo;<span className="font-medium text-gray-700">{search}</span>&rdquo;
                </p>
                <button
                  onClick={() => setSearch('')}
                  className="mt-4 text-emerald-600 hover:text-emerald-700 text-sm font-medium underline underline-offset-2"
                >
                  {t('how.interactive.restart')}
                </button>
              </div>
            )
          ) : (
            // Normal categorized view
            faqCategories.map((category, catIdx) => (
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
                            <p className="text-sm text-gray-600 leading-relaxed mb-3">
                              {item.a}
                            </p>
                            {/* Feedback */}
                            <div className="flex items-center gap-3 pt-2 border-t border-gray-50">
                              <span className="text-xs text-gray-400">{t('faq.feedback')}</span>
                              <button
                                onClick={() => giveFeedback(key, 'yes')}
                                className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full transition-all ${
                                  userFeedback[key] === 'yes'
                                    ? 'bg-emerald-100 text-emerald-700'
                                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                                }`}
                              >
                                <ThumbsUp className="h-3 w-3" />
                                {t('faq.feedback.yes')}
                                {(feedback[key]?.yes || 0) > 0 && (
                                  <span className="font-medium">{feedback[key].yes}</span>
                                )}
                              </button>
                              <button
                                onClick={() => giveFeedback(key, 'no')}
                                className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full transition-all ${
                                  userFeedback[key] === 'no'
                                    ? 'bg-red-100 text-red-600'
                                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                                }`}
                              >
                                <ThumbsDown className="h-3 w-3" />
                                {t('faq.feedback.no')}
                                {(feedback[key]?.no || 0) > 0 && (
                                  <span className="font-medium">{feedback[key].no}</span>
                                )}
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            ))
          )}
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
