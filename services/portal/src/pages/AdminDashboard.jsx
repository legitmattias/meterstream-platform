import React from 'react'
import { SummaryCards } from '../components/SummaryCards'
import { MonthBarChart } from '../components/MonthBarChart'
import { WeekBarChart } from '../components/WeekBarChart'
import { TopConsumersTable } from '../components/TopConsumersTable'
import { LogsList } from '../components/LogsList'

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
    logs,
    topConsumers,
    quality,
    monthSeries,
    weekSeries,
  } = props

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>MeterStream Dashboard</h1>
        <div className="user-info">
          <span>Welcome, {user?.email || 'User'}</span>
          <button onClick={logout}>Logout</button>
        </div>
      </header>

      {/* Summary Cards - calculated from fetched data, shown for all roles */}
      <SummaryCards
        monthTotal={monthTotal}
        monthAverage={monthAverage}
        hourlyMax={hourlyMax}
        weekMax={weekMax}
      />

      <div className="tabs">
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
      </div>

      <main className="dashboard-content">
        {activeTab === 'overview' && (
          <div className="tab-content">
            <div className="dashboard-section">
              <h2>Real-Time Ingestion Metrics</h2>
              <div className="grafana-embed">
                <iframe
                  src={opsGrafanaUrl}
                  width="100%"
                  height="300"
                  frameBorder="0"
                  title="Ingestion Metrics"
                ></iframe>
              </div>
            </div>

            <div className="dashboard-section">
              <h2>Queue Length</h2>
              <div className="grafana-embed">
                <iframe
                  src={opsGrafanaUrl}
                  width="100%"
                  height="300"
                  frameBorder="0"
                  title="Queue Length"
                ></iframe>
              </div>
            </div>

            <div className="dashboard-section">
              <h2>Processing Rate</h2>
              <div className="grafana-embed">
                <iframe
                  src={opsGrafanaUrl}
                  width="100%"
                  height="300"
                  frameBorder="0"
                  title="Processing Rate"
                ></iframe>
              </div>
            </div>

            <div className="dashboard-section">
              <h2>Logs</h2>
              <LogsList logs={logs} />
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="tab-content">
            <div className="dashboard-section">
              <h2>Aggregate Energy Consumption</h2>
              <MonthBarChart data={monthSeries} type="line" />
            </div>

            <div className="dashboard-grid">
              <div className="dashboard-section">
                <h2>Top Consumers</h2>
                <TopConsumersTable consumers={topConsumers} />
              </div>

              <div className="dashboard-section">
                <h2>Data Quality</h2>
                <div className="quality-metrics">
                  <div className="quality-item">
                    <div className="quality-header">
                      <span>Completeness</span>
                      <span className="quality-value">{quality.completeness !== null ? `${quality.completeness}%` : 'N/A'}</span>
                    </div>
                    <div className="quality-bar">
                      <div className="quality-fill" style={{ width: quality.completeness !== null ? `${quality.completeness}%` : '0%' }}></div>
                    </div>
                  </div>
                  <div className="quality-item">
                    <div className="quality-header">
                      <span>Accuracy</span>
                      <span className="quality-value">{quality.accuracy !== null ? `${quality.accuracy}%` : 'N/A'}</span>
                    </div>
                    <div className="quality-bar">
                      <div className="quality-fill" style={{ width: quality.accuracy !== null ? `${quality.accuracy}%` : '0%' }}></div>
                    </div>
                  </div>
                  <div className="quality-item">
                    <div className="quality-header">
                      <span>Timeliness</span>
                      <span className="quality-value">{quality.timeliness !== null ? `${quality.timeliness}%` : 'N/A'}</span>
                    </div>
                    <div className="quality-bar">
                      <div className="quality-fill" style={{ width: quality.timeliness !== null ? `${quality.timeliness}%` : '0%' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="dashboard-section">
              <h2>Monthly Consumption</h2>
              <MonthBarChart data={monthSeries} />
            </div>

            <div className="dashboard-section">
              <h2>This Week</h2>
              <WeekBarChart data={weekSeries} />
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
