import { useAuth } from '../contexts/AuthContext'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { config } from '../config'
import './Header.css'

export function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const role = user?.role || 'customer'
  const showGrafana = role === 'admin' || role === 'internal'
  const isHomePage = location.pathname === '/dashboard' || location.pathname === '/'

  return (
    <header className="global-header">
      <div className="header-left">
        <h1 className="logo">MeterStream</h1>
        <nav className="header-nav">
          <Link
            to="/dashboard"
            className={`header-nav-link ${isHomePage ? 'active' : ''}`}
          >
            Home
          </Link>
          <Link
            to="/analytics"
            className={`header-nav-link ${location.pathname === '/analytics' ? 'active' : ''}`}
          >
            Analytics
          </Link>
          {showGrafana && (
            <a
              href={config.grafanaUrl}
              target="_blank"
              rel="noreferrer"
              className="header-nav-link"
            >
              Grafana
            </a>
          )}
        </nav>
      </div>
      <div className="header-right">
        <span className="user-info">{user?.name || 'User'}</span>
        <button className="logout-btn" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </header>
  )
}
