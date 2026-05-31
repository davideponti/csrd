'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import Link from 'next/link'
import { Leaf, Eye, EyeOff, Loader2 } from 'lucide-react'
import { useLanguage } from '@/i18n/LanguageContext'
import { auth } from '@/lib/api'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [requiresOtp, setRequiresOtp] = useState(false)
  const [otp, setOtp] = useState('')
  const [otpLoading, setOtpLoading] = useState(false)
  const [otpSent, setOtpSent] = useState(false)
  const { login } = useAuth()
  const router = useRouter()
  const { t } = useLanguage()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const result = await auth.login({ email, password })
      if (result.requires_otp) {
        setRequiresOtp(true)
        setOtpSent(true)
      } else {
        await login(email, password)
        router.push('/dashboard')
      }
    } catch (err: any) {
      setError(err.message || 'Login fallito')
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setOtpLoading(true)
    try {
      await auth.verifyEmail({ email, otp })
      // After verification, log in
      await login(email, password)
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.message || 'Codice OTP non valido')
    } finally {
      setOtpLoading(false)
    }
  }

  const handleResendOtp = async () => {
    setError('')
    try {
      await auth.sendOtp({ email })
      setOtpSent(true)
      setOtp('')
      setError('Nuovo codice OTP inviato!')
    } catch (err: any) {
      setError(err.message || 'Errore invio OTP')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2">
            <Leaf className="h-8 w-8 text-emerald-600" />
            <span className="text-2xl font-bold text-gray-900">CSRD Comply</span>
          </Link>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          {requiresOtp ? (
            <>
              <h1 className="text-xl font-bold text-center text-gray-900 mb-2">
                Verifica Email
              </h1>
              <p className="text-sm text-center text-gray-500 mb-6">
                Inserisci il codice di verifica inviato a <strong>{email}</strong>
              </p>

              {error && (
                <div className={`mb-4 p-3 text-sm rounded-lg border ${
                  error.includes('inviato')
                    ? 'bg-green-50 text-green-700 border-green-100'
                    : 'bg-red-50 text-red-700 border-red-100'
                }`}>
                  {error}
                </div>
              )}

              <form onSubmit={handleVerifyOtp} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Codice di verifica
                  </label>
                  <input
                    type="text"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-center text-2xl tracking-[8px] font-mono"
                    placeholder="000000"
                    maxLength={6}
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={otpLoading || otp.length < 6}
                  className="w-full py-2.5 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {otpLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin mx-auto" />
                  ) : (
                    'Verifica Email'
                  )}
                </button>

                <p className="text-center">
                  <button
                    type="button"
                    onClick={handleResendOtp}
                    className="text-sm text-emerald-600 hover:text-emerald-700 font-medium"
                  >
                    Non hai ricevuto il codice? Invia di nuovo
                  </button>
                </p>
              </form>
            </>
          ) : (
            <>
              <h1 className="text-xl font-bold text-center text-gray-900 mb-2">
                {t('auth.login.title')}
              </h1>
              <p className="text-sm text-center text-gray-500 mb-8">
                {t('auth.login.subtitle')}
              </p>

              {error && (
                <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-100">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('auth.login.email')}
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    placeholder="nome@azienda.it"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('auth.login.password')}
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full px-3 py-2.5 pr-10 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                      placeholder="••••••••"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      tabIndex={-1}
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>

                <div className="flex justify-end">
                  <Link
                    href="/auth/forgot-password"
                    className="text-sm text-emerald-600 hover:text-emerald-700 font-medium"
                  >
                    Password dimenticata?
                  </Link>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin mx-auto" />
                  ) : (
                    t('auth.login.button')
                  )}
                </button>
              </form>

              <p className="mt-6 text-center text-sm text-gray-500">
                {t('auth.login.noaccount')}{' '}
                <Link href="/auth/register" className="text-emerald-600 hover:text-emerald-700 font-medium">
                  {t('auth.login.register')}
                </Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
