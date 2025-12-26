import React from 'react'
import { SummaryCards } from '../components/SummaryCards'
import { SystemMonitoring } from '../components/SystemMonitoring'

export default function AdminDashboard(props) {
  const {
    user,
    logout,
    monthTotal,
    monthAverage,
    hourlyMax,
    weekMax,
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
          {role === 'admin' && (
            <a
              className="header-link"
              href={opsGrafanaUrl}
              target="_blank"
              rel="noopener noreferrer"
            >
              Open Grafana
            </a>
          )}
          {role !== 'customer' && (
            <a className="header-link" href="/landing">Back to Landing</a>
          )}
          <span className="user-email">Welcome, {user?.email || 'User'}</span>
          <button onClick={logout}>Logout</button>
        </div>
      </header>

      {activeTab !== 'overview' && (
        <SummaryCards
          monthTotal={monthTotal}
          monthAverage={monthAverage}
          hourlyMax={hourlyMax}
          weekMax={weekMax}
        />
      )}

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
              <div className="dashboard-section">
                <h2>Consumer Grafana</h2>
                <div className="grafana-embed">
                  <iframe
                    src={opsGrafanaUrl}
                    width="100%"
                    height="400"
                    frameBorder="0"
                    title="Consumer Analytics (Grafana)"
                  ></iframe>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
