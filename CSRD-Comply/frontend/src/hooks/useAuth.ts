'use client'
import { useState, useEffect, useCallback } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/v1'

interface AuthState {
  user: { email: string; company_name: string } | null
  token: string | null
  loading: boolean
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    loading: true,
  })

  const checkSession = useCallback(async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setState({ user: null, token: null, loading: false })
      return false
    }
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (res.ok) {
        const data = await res.json()
        setState({
          user: { email: data.email, company_name: data.company_name || '' },
          token,
          loading: false,
        })
        return true
      }
    } catch {
      // Not authenticated
    }
    localStorage.removeItem('access_token')
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
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }))
      throw new Error(err.detail || 'Login failed')
    }
    const data = await res.json()
    if (data.access_token) localStorage.setItem('access_token', data.access_token)
    await checkSession()
    return data
  }, [checkSession])

  const register = useCallback(async (email: string, password: string, company_name: string) => {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, company_name }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Registration failed' }))
      throw new Error(err.detail || 'Registration failed')
    }
    const data = await res.json()
    if (data.access_token) localStorage.setItem('access_token', data.access_token)
    await checkSession()
    return data
  }, [checkSession])

  const logout = useCallback(async () => {
    localStorage.removeItem('access_token')
    try {
      const token = localStorage.getItem('access_token')
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
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
