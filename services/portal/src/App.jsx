import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { Login } from './pages/Login'
import { Dashboard } from './pages/Dashboard'
import { Landing } from './pages/Landing'
import { ProtectedRoute } from './components/ProtectedRoute'
import './App.css'

/**
 * Entry point of the application, sets up routing.
 *
 * @returns
 */
function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          {/* Authenticated landing */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Landing />
              </ProtectedRoute>
            }
          />
          {/* Analytics */}
          <Route
            path="/analytics"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
