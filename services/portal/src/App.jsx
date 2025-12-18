import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Login } from './pages/Login'
import { Register } from './pages/Register'
import { Dashboard } from './pages/Dashboard'
import { Landing } from './pages/Landing'
// import { ProtectedRoute } from './components/ProtectedRoute'
import './App.css'

/**
 * Entry point of the application, sets up routing.
 *
 * @returns 
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        {/* Authenticated landing */}
        <Route path="/dashboard" element={<Landing />} />
        {/* Legacy analytics page (if needed) */}
        <Route path="/analytics" element={<Dashboard />} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
