'use client'
import { useState, useEffect, useCallback } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/v1'

interface AuthState {
  user: { email: string; company_name: string } | null
  loading: boolean
}

/**
 * 🔒 SICUREZZA: L'autenticazione usa SOLO cookie HttpOnly (XSS-safe).
 * Il JWT non è mai accessibile via JavaScript. Il browser lo invia
 * automaticamente con ogni richiesta grazie a `credentials: 'include'`.
 * 
 * NESSUNA operazione localStorage — il token esiste solo nel cookie
 * impostato dal backend (HttpOnly, Secure, SameSite=None).
 */
export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
  })

  const checkSession = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        credentials: 'include', // ← Il browser invia automaticamente il cookie HttpOnly
      })
      if (res.ok) {
        const data = await res.json()
        setState({
          user: { email: data.email, company_name: data.company_name || '' },
          loading: false,
        })
        return true
      }
      if (res.status === 401 && typeof window !== 'undefined') {
        // Cookie presente ma token scaduto/revocato — pulisci sessione locale
        setState({ user: null, loading: false })
        return false
      }
    } catch {
      // Not authenticated
    }
    setState({ user: null, loading: false })
    return false
  }, [])

  useEffect(() => {
    checkSession()
  }, [checkSession])

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // ← Il backend imposta il cookie HttpOnly nella response
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }))
      throw new Error(err.detail || 'Login failed')
    }
    const data = await res.json()
    // 🔒 Non salvare MAI il token in localStorage!
    // Il backend imposta il cookie HttpOnly automaticamente.
    await checkSession()
    return data
  }, [checkSession])

  const register = useCallback(async (email: string, password: string, company_name: string) => {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // ← Il backend imposta il cookie HttpOnly nella response
      body: JSON.stringify({ email, password, company_name }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Registration failed' }))
      throw new Error(err.detail || 'Registration failed')
    }
    const data = await res.json()
    // 🔒 Non salvare MAI il token in localStorage!
    await checkSession()
    return data
  }, [checkSession])

  const logout = useCallback(async () => {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      })
    } catch {
      // Ignore errors
    }
    setState({ user: null, loading: false })
  }, [])

  return {
    ...state,
    isAuthenticated: !!state.user,
    login,
    register,
    logout,
  }
}
