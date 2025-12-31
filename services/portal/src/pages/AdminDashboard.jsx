import React from 'react'
import { SystemMonitoring } from '../components/SystemMonitoring'
import { UserManagement } from '../components/UserManagement'
import { config } from '../config'

const GRAFANA_DASHBOARDS = [
  {
    uid: 'ff7iuh80yjh8gd',
    title: 'General Monitor',
    description: 'Raw hourly meter data (line graph).',
  },
  {
    uid: 'af7irczysogzke',
    title: 'Aggregated Bar Chart',
    description: 'Totals by interval. Filter by customer.',
  },
  {
    uid: 'df7iuv4kojsowd',
    title: 'Aggregated Line Chart',
    description: 'Trends by interval. Filter by customer.',
  },
  {
    uid: 'bf7l6gu4glrswd',
    title: 'Overlay Comparison',
    description: 'Compare time periods. Filter by customer and shift.',
  },
]

export default function AdminDashboard(props) {
  const {
    user,
    logout,
    activeTab,
    setActiveTab,
  } = props

  const role = user?.role || 'customer'

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>MeterStream Dashboard</h1>
        <div className="header-actions">
          {role !== 'customer' && (
            <a className="header-link" href="/landing">Back to Landing</a>
          )}
          <span className="user-email">Welcome, {user?.email || 'User'}</span>
          <button onClick={logout}>Logout</button>
        </div>
      </header>

      <div className="tabs">
        {role === 'admin' ? (
          <>
            <button
              className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveTab('overview')}
            >
              System Overview
            </button>
            <button
              className={`tab-button ${activeTab === 'analytics' ? 'active' : ''}`}
              onClick={() => setActiveTab('analytics')}
            >
              Consumer Analytics
            </button>
            <button
              className={`tab-button ${activeTab === 'users' ? 'active' : ''}`}
              onClick={() => setActiveTab('users')}
            >
              User Management
            </button>
          </>
        ) : (
          <button
            className={`tab-button ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveTab('analytics')}
          >
            Consumer Analytics
          </button>
        )}
      </div>

      <main className="dashboard-content">
        {role === 'admin' && activeTab === 'overview' && (
          <div className="tab-content">
            <SystemMonitoring />
          </div>
        )}

        {(activeTab === 'analytics' || (activeTab === 'overview' && role !== 'admin')) && (
          <div className="tab-content">
            {role !== 'customer' && (
              <div className="dashboard-section grafana-section">
                <h2>Consumer Analytics</h2>
                <p className="grafana-description">
                  View detailed consumption analytics, trends, and reports in Grafana.
                </p>
                <div className="grafana-dashboard-grid">
                  {GRAFANA_DASHBOARDS.map((dashboard) => (
                    <a
                      key={dashboard.uid}
                      className="grafana-dashboard-card"
                      href={`${config.grafanaUrl}/d/${dashboard.uid}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <span className="grafana-card-title">{dashboard.title}</span>
                      <span className="grafana-card-description">{dashboard.description}</span>
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {role === 'admin' && activeTab === 'users' && (
          <div className="tab-content">
            <UserManagement />
          </div>
        )}
      </main>
    </div>
  )
}
