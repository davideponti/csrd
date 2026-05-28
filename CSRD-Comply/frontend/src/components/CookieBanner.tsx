'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui'
import { X } from 'lucide-react'

const COOKIE_CONSENT_KEY = 'csrd-cookie-consent'

export default function CookieBanner() {
  const [show, setShow] = useState(false)

  useEffect(() => {
    const consent = localStorage.getItem(COOKIE_CONSENT_KEY)
    if (consent !== 'accepted') {
      setShow(true)
    }
  }, [])

  const handleAccept = () => {
    localStorage.setItem(COOKIE_CONSENT_KEY, 'accepted')
    setShow(false)
  }

  if (!show) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-gray-900/95 backdrop-blur-sm text-white shadow-2xl border-t border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="text-sm text-gray-200 text-center sm:text-left">
          Utilizziamo cookie tecnici necessari al funzionamento del sito. Continuando accetti l'uso dei cookie.
        </p>
        <div className="flex items-center gap-3 shrink-0">
          <Button
            onClick={handleAccept}
            size="sm"
            className="bg-emerald-600 hover:bg-emerald-500 text-white"
          >
            Accetto
          </Button>
          <button
            onClick={handleAccept}
            className="p-1 rounded-full hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
            aria-label="Chiudi"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
