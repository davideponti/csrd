import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { LanguageProviderWrapper } from '@/components/LanguageProviderWrapper'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'CSRD Comply — Conformità CSRD per PMI Europee',
  description: 'Dalla doppia materialità al report di sostenibilità: un unico strumento per gestire l\'intero percorso di compliance ESG.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="it" suppressHydrationWarning>
      <body className={`${inter.className} bg-background text-foreground`}>

        <LanguageProviderWrapper>
          {children}
        </LanguageProviderWrapper>
      </body>
    </html>
  )
}
