import { useState, useEffect } from 'react'
import { api } from '../lib/api'

/**
 * Manage authentication state using HttpOnly cookies.
 * JWT is stored securely in cookies and managed by the backend.
 */

export function useAuth() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      // Try to get user info from backend (will use cookie automatically)
      try {
        const userData = await api.request('/auth/me')
        setUser({
          email: userData.email,
          role: userData.role,
          customerId: userData.customer_id,
        })
      } catch (error) {
        // No valid session, user needs to login
        console.log('No active session')
      }
      setLoading(false)
    }

    initAuth()
  }, [])

  const login = async (email, password) => {
    await api.login(email, password)
    // Cookie is set automatically by backend
    // User info will be fetched by initAuth on next render
    // Force re-check authentication state
    const userData = await api.request('/auth/me')
    setUser({
      email: userData.email,
      role: userData.role,
      customerId: userData.customer_id,
    })
    setLoading(false)
  }

  const logout = async () => {
    try {
      // Call backend to clear cookie
      await api.request('/auth/logout', { method: 'POST' })
    } catch (error) {
      console.error('Logout request failed:', error)
      // Continue with logout even if request fails
    }

    // Clear local state
    setUser(null)

    // Redirect to login page
    window.location.href = '/login'
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
