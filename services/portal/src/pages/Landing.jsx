import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { config } from '../config'
import './Landing.css'

export function Landing() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const role = user?.role || 'customer'
  const baseGrafana = config.grafanaDashboardUid
    ? `${config.grafanaUrl}/d/${config.grafanaDashboardUid}`
    : config.grafanaUrl

  const linksByRole = {
    admin: [
      { label: 'Ops dashboard', href: `${baseGrafana}?view=ops` },
      { label: 'Admin analytics', href: '/analytics', internal: true},

    ],
    internal: [
      { label: 'Internal dashboard', href: baseGrafana },
    ],
    customer: [
      { label: 'Open analytics', href: '/analytics', internal: true },
    ],
  }

  const ctas = linksByRole[role] || linksByRole.customer

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="landing">
      <header className="landing-hero">
        <div className="hero-text">
          <p className="eyebrow">Welcome back</p>
          <h1>Hi {user?.email || 'there'}, here’s your energy snapshot</h1>
          <p className="subtitle">
            Quick links based on your role. Open the dashboards you need most, or jump to the portal analytics view.
          </p>
          <div className="hero-actions">
            {ctas.map((cta) =>
              cta.internal ? (
                <Link key={cta.label} className="btn primary" to={cta.href}>{cta.label}</Link>
              ) : (
                <a key={cta.label} className="btn primary" href={cta.href} target="_blank" rel="noreferrer">{cta.label}</a>
              )
            )}
            <button className="btn ghost" onClick={handleLogout}>Sign out</button>
          </div>
          <p className="note">Session active. Secure access enforced via gateway.</p>
        </div>
        <div className="hero-card">
          <div className="metric">
            <span className="label">Live ingestion</span>
            <span className="value">148.2 kWh</span>
            <span className="delta up">+4.2% vs hour</span>
          </div>
          <div className="metric">
            <span className="label">Today’s total</span>
            <span className="value">892 kWh</span>
            <span className="delta flat">On track</span>
          </div>
          <div className="metric">
            <span className="label">Data quality</span>
            <span className="value">98.7%</span>
            <span className="delta up">Stable</span>
          </div>
        </div>
      </header>

      <section className="features">
        <div className="feature-card">
          <h3>Role-aware links</h3>
          <p>Admin: ops/health Grafana. Internal: Grafana. Customer: portal analytics.</p>
        </div>
        <div className="feature-card">
          <h3>Scoped access</h3>
          <p>Data is filtered by your customer ID in the gateway and query service.</p>
        </div>
        <div className="feature-card">
          <h3>Fast navigation</h3>
          <p>Open the right dashboard without digging through menus.</p>
        </div>
      </section>

      <section className="cta">
        <div className="cta-card">
          <div>
            <p className="eyebrow">Next step</p>
            <h2>Open your dashboards</h2>
            <p className="subtitle">Choose the view that matches your role. Full analytics stay available anytime.</p>
          </div>
          <div className="cta-actions">
            {ctas.map((cta) =>
              cta.internal ? (
                <Link key={cta.label} className="btn primary" to={cta.href}>{cta.label}</Link>
              ) : (
                <a key={cta.label} className="btn primary" href={cta.href} target="_blank" rel="noreferrer">{cta.label}</a>
              )
            )}
            <button className="btn ghost" onClick={handleLogout}>Sign out</button>
          </div>
        </div>
      </section>
    </div>
  )
}
