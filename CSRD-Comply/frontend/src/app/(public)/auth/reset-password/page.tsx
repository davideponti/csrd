'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Leaf, Eye, EyeOff, Loader2, CheckCircle2, XCircle } from 'lucide-react'
import { auth } from '@/lib/api'

function ResetPasswordForm() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const token = searchParams.get('token')

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  // Password requirements
  const requirements = [
    { label: 'Minimo 8 caratteri', test: (p: string) => p.length >= 8 },
    { label: 'Una lettera maiuscola', test: (p: string) => /[A-Z]/.test(p) },
    { label: 'Una lettera minuscola', test: (p: string) => /[a-z]/.test(p) },
    { label: 'Un numero', test: (p: string) => /\d/.test(p) },
    { label: 'Un carattere speciale (!@#$%^&*)', test: (p: string) => /[!@#$%^&*(),.?":{}|<>]/.test(p) },
  ]

  const passwordErrors = requirements.filter(r => !r.test(password))
  const passwordsMatch = password === confirmPassword
  const isPasswordValid = passwordErrors.length === 0
  const canSubmit = isPasswordValid && passwordsMatch && token && !loading

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!token) {
      setError('Token di reset mancante.')
      return
    }
    if (!isPasswordValid) {
      setError('La password non soddisfa i requisiti di sicurezza.')
      return
    }
    if (!passwordsMatch) {
      setError('Le password non coincidono.')
      return
    }
    setLoading(true)
    try {
      await auth.resetPassword({ token, password })
      setSuccess(true)
    } catch (err: any) {
      setError(err.message || 'Errore durante il reset della password')
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <div className="text-center py-8">
        <XCircle className="h-16 w-16 text-red-400 mx-auto mb-4" />
        <h1 className="text-xl font-bold text-gray-900 mb-2">Link Non Valido</h1>
        <p className="text-sm text-gray-500 mb-6">
          Il link di reset della password non è valido o è scaduto.
        </p>
        <Link
          href="/auth/forgot-password"
          className="text-emerald-600 hover:text-emerald-700 font-medium text-sm"
        >
          Richiedi un nuovo link
        </Link>
      </div>
    )
  }

  if (success) {
    return (
      <div className="text-center py-8">
        <CheckCircle2 className="h-16 w-16 text-emerald-500 mx-auto mb-4" />
        <h1 className="text-xl font-bold text-gray-900 mb-2">Password Reimpostata!</h1>
        <p className="text-sm text-gray-500 mb-6">
          La tua password è stata aggiornata con successo.
        </p>
        <Link
          href="/auth/login"
          className="inline-block px-6 py-2.5 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors"
        >
          Accedi Ora
        </Link>
      </div>
    )
  }

  return (
    <>
      <h1 className="text-xl font-bold text-gray-900 mb-2">Reimposta Password</h1>
      <p className="text-sm text-gray-500 mb-8">
        Scegli una nuova password per il tuo account.
      </p>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-100">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Nuova Password
          </label>
          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2.5 pr-10 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              placeholder="Min. 8 caratteri"
              required
              minLength={8}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              tabIndex={-1}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {password.length > 0 && (
            <div className="mt-2 space-y-1">
              {requirements.map((req, idx) => (
                <div key={idx} className="flex items-center gap-1.5 text-xs">
                  {req.test(password) ? (
                    <CheckCircle2 className="h-3 w-3 text-emerald-500 shrink-0" />
                  ) : (
                    <XCircle className="h-3 w-3 text-gray-300 shrink-0" />
                  )}
                  <span className={req.test(password) ? 'text-emerald-600' : 'text-gray-400'}>
                    {req.label}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Conferma Nuova Password
          </label>
          <div className="relative">
            <input
              type={showConfirmPassword ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-3 py-2.5 pr-10 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              placeholder="Ripeti la password"
              required
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              tabIndex={-1}
            >
              {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {confirmPassword.length > 0 && (
            <div className="mt-1 flex items-center gap-1.5 text-xs">
              {passwordsMatch ? (
                <>
                  <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                  <span className="text-emerald-600">Le password coincidono</span>
                </>
              ) : (
                <>
                  <XCircle className="h-3 w-3 text-red-400" />
                  <span className="text-red-400">Le password non coincidono</span>
                </>
              )}
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={!canSubmit}
          className="w-full py-2.5 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin mx-auto" />
          ) : (
            'Reimposta Password'
          )}
        </button>
      </form>
    </>
  )
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2">
            <Leaf className="h-8 w-8 text-emerald-600" />
            <span className="text-2xl font-bold text-gray-900">CSRD Comply</span>
          </Link>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <Suspense fallback={
            <div className="text-center py-8">
              <Loader2 className="h-8 w-8 animate-spin mx-auto text-emerald-600" />
            </div>
          }>
            <ResetPasswordForm />
          </Suspense>
        </div>
      </div>
    </div>
  )
}
