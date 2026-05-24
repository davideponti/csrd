'use client'

import { LanguageProvider } from '@/i18n/LanguageContext'

export function LanguageProviderWrapper({ children }: { children: React.ReactNode }) {
  return <LanguageProvider>{children}</LanguageProvider>
}
