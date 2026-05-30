'use client'

import { useState, useEffect, useCallback } from 'react'

// API base URL — usa percorso relativo (Nginx proxy /api/ → backend in produzione,
// Next.js rewrites /api/v1/* → backend in sviluppo)
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/v1'

interface AuthState {
  user: { email: string; company_name: string } | null
  token: string | null
  loading: boolean
}

/**
 * Custom hook per autenticazione con HttpOnly Cookie (XSS-safe).
 *
 * Il JWT è gestito tramite cookie HttpOnly lato server.
 * Il token in memoria è solo per uso client-side (controllo UI).
 * Le API chiamano il backend che legge automaticamente il cookie.
 */
export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    loading: true,
  })

  // Check session on mount - try to get the current user via cookie
  const checkSession = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        credentials: 'include',
      })
      if (res.ok) {
        const data = await res.json()
        setState({
          user: { email: data.email, company_name: data.company_name || '' },
          token: 'authenticated', // Token is in HttpOnly cookie, not accessible from JS
          loading: false,
        })
        return true
      }
    } catch {
      // Not authenticated
    }
    setState({ user: null, token: null, loading: false })
    return false
  }, [])

  useEffect(() => {
    checkSession()
  }, [checkSession])

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
      credentials: 'include', // Send/receive cookies
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }))
      throw new Error(err.detail || 'Login failed')
    }
    const data = await res.json()
    // Token is in HttpOnly cookie - we just mark as authenticated
    setState({ user: null, token: data.access_token, loading: false })
    // Fetch user info
    await checkSession()
    return data
  }, [checkSession])

  const register = useCallback(
    async (email: string, password: string, company_name: string) => {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, company_name }),
        credentials: 'include', // Send/receive cookies
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Registration failed' }))
        throw new Error(err.detail || 'Registration failed')
      }
      const data = await res.json()
      setState({ user: null, token: data.access_token, loading: false })
      await checkSession()
      return data
    },
    [checkSession],
  )

  const logout = useCallback(async () => {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      })
    } catch {
      // Ignore errors
    }
    setState({ user: null, token: null, loading: false })
  }, [])

  return {
    ...state,
    isAuthenticated: !!state.token,
    login,
    register,
    logout,
  }
}
