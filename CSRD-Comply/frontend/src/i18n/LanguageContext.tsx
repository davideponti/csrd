'use client'

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { LANGUAGES, DEFAULT_LANGUAGE, type Language } from './languages'

type LanguageContextType = {
  language: Language
  setLanguage: (lang: Language) => void
  t: (key: string) => string
  translations: Record<string, string>
}

const LanguageContext = createContext<LanguageContextType | null>(null)

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('csrd-language')
      if (saved) {
        const found = LANGUAGES.find(l => l.code === saved)
        if (found) return found
      }
    }
    return LANGUAGES.find(l => l.code === DEFAULT_LANGUAGE) || LANGUAGES[0]
  })

  const [translations, setTranslations] = useState<Record<string, string>>({})

  useEffect(() => {
    loadTranslations(language.code)
  }, [language.code])

  const loadTranslations = async (code: string) => {
    try {
      const module = await import(`./translations/${code}`)
      setTranslations(module.default || {})
    } catch (e) {
      console.error(`Failed to load translations for ${code}`, e)
      const fallback = await import('./translations/it')
      setTranslations(fallback.default || {})
    }
  }

  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang)
    localStorage.setItem('csrd-language', lang.code)
  }, [])

  const t = useCallback((key: string): string => {
    return translations[key] || key
  }, [translations])

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, translations }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}
