'use client'

import { useState, useEffect, useCallback } from 'react'
import { auth } from '@/lib/api'

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

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      setState({ user: null, token, loading: false })
      // In production: decode JWT and fetch user profile
    } else {
      setState({ user: null, token: null, loading: false })
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const res = await auth.login({ email, password })
    localStorage.setItem('token', res.access_token)
    setState({ user: null, token: res.access_token, loading: false })
    return res
  }, [])

  const register = useCallback(
    async (email: string, password: string, company_name: string) => {
      const res = await auth.register({ email, password, company_name })
      localStorage.setItem('token', res.access_token)
      setState({ user: null, token: res.access_token, loading: false })
      return res
    },
    [],
  )

  const logout = useCallback(() => {
    localStorage.removeItem('token')
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
