'use client'

import { useState, useRef, useEffect } from 'react'
import { useLanguage } from '@/i18n/LanguageContext'
import { LANGUAGES } from '@/i18n/languages'
import { Check, ChevronDown, Globe } from 'lucide-react'

export function LanguageSwitcher() {
  const { language, setLanguage, t } = useLanguage()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-2 py-1.5 text-sm text-gray-600 hover:text-emerald-600 rounded-lg hover:bg-gray-100 transition-colors"
        title={t('lang.select')}
      >
        <Globe className="h-4 w-4" />
        <span className="hidden sm:inline">{language.flag} {language.nativeName}</span>
        <span className="sm:hidden">{language.flag}</span>
        <ChevronDown className="h-3 w-3" />
      </button>

      {open && (
        <div className="absolute right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-50 min-w-[180px]">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => {
                setLanguage(lang)
                setOpen(false)
              }}
              className={`w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50 transition-colors ${
                language.code === lang.code ? 'text-emerald-600 font-medium' : 'text-gray-700'
              }`}
            >
              <span>{lang.flag}</span>
              <span>{lang.nativeName}</span>
              {language.code === lang.code && <Check className="h-3.5 w-3.5 ml-auto text-emerald-600" />}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
