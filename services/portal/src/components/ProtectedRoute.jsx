import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

/**
 * Uses useAuth to check if the user is authenticated.
 * 
 * @param {*} param0 
 * @returns 
 */
export function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return <div>Loading...</div>
  }

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />
  }

  return children
}
