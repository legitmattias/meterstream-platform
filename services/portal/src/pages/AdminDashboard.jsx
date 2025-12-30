import React from 'react'
import { SystemMonitoring } from '../components/SystemMonitoring'
import { UserManagement } from '../components/UserManagement'

export default function AdminDashboard(props) {
  const {
    user,
    logout,
    activeTab,
    setActiveTab,
    opsGrafanaUrl,
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
                  Dashboards include real-time data, historical comparisons, and customer insights.
                </p>
                <a
                  className="grafana-button"
                  href={opsGrafanaUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <span className="grafana-button-text">
                    <strong>Open Grafana Dashboard</strong>
                    <small>Opens in a new tab</small>
                  </span>
                </a>
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
