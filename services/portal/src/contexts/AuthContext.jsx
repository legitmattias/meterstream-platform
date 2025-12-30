/* eslint-disable react-refresh/only-export-components */
import { createContext, useState, useEffect, useContext } from 'react'
import { api } from '../lib/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      try {
        const userData = await api.request('/auth/me')
        setUser({
          email: userData.email,
          role: userData.role,
          customerId: userData.customer_id,
        })
      } catch (error) {
        console.log('No active session', error)
      }
      setLoading(false)
    }

    initAuth()
  }, [])

  const login = async (email, password) => {
    await api.login(email, password)
    const userData = await api.request('/auth/me')
    setUser({
      email: userData.email,
      role: userData.role,
      customerId: userData.customer_id,
    })  
    setLoading(false)
  }

  const logout = async () => {
    await api.logout()
    setUser(null)
    window.location.href = '/login'
  }

  const isAuthenticated = () => {
    return user !== null
  }

  const value = {
    user,
    loading,
    login,
    logout,
    isAuthenticated,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
