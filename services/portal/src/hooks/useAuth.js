import { useState, useEffect } from 'react'
import { api } from '../lib/api'

/**
 * Manage authentication state (login/logout/isAuthenticated) and store the token in sessionStorage.
 * Decodes JWT locally only to surface email/role/customerId for the UI; backend still validates tokens.
 */
function decodeJwt(token) {
  try {
    const payload = token.split('.')[1]
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/').padEnd(Math.ceil(payload.length / 4) * 4, '=')
    const json = atob(normalized)
    return JSON.parse(json)
  } catch (err) {
    console.error('Failed to decode JWT', err)
    return null
  }
}

export function useAuth() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      const access_token = sessionStorage.getItem('access_token')
      if (access_token) {
        api.setToken(access_token)
        const payload = decodeJwt(access_token)
        setUser({
          email: payload?.email,
          role: payload?.role,
          customerId: payload?.customer_id,
          access_token,
        })
      }
      setLoading(false)
    }

    initAuth()
  }, [])

  const login = async (email, password) => {
    const data = await api.login(email, password)
    sessionStorage.setItem('access_token', data.access_token)
    api.setToken(data.access_token)
    const payload = decodeJwt(data.access_token)
    setUser({
      email: payload?.email ?? email,
      role: payload?.role,
      customerId: payload?.customer_id,
      access_token: data.access_token,
    })
    return data
  }

  const logout = () => {
    api.clearToken()
    sessionStorage.removeItem('access_token')
    setUser(null)
  }

  const isAuthenticated = () => {
    return !!user
  }

  return {
    user,
    loading,
    login,
    logout,
    isAuthenticated,
  }
}
