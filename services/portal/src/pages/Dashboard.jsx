import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { config } from '../config'
import './Dashboard.css'

// Stable module-level constants to avoid memoization issues
const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']
const WEEK_SERIES_MAP = {
  'Week 1': [
    { label: 'Mon', value: 120 },
    { label: 'Tue', value: 140 },
    { label: 'Wed', value: 110 },
    { label: 'Thu', value: 160 },
    { label: 'Fri', value: 130 },
    { label: 'Sat', value: 90 },
    { label: 'Sun', value: 100 },
  ],
}

function genMonth(base) {
  return Array.from({ length: 30 }, (_, i) => ({ label: `${i + 1}`, value: base + ((i * 7) % 40) }))
}

const MONTH_SERIES_BY_YEAR = {
  '2024': Object.fromEntries(MONTHS.map((m, idx) => [m, genMonth(95 + (idx % 6) * 5)])),
  '2025': Object.fromEntries(MONTHS.map((m, idx) => [m, genMonth(110 + (idx % 6) * 5)])),
}

function genHourly(base) {
  return Array.from({ length: 24 }, (_, i) => ({ label: `${i}:00`, value: base + ((i * 3) % 20) }))
}

const HOURLY_SERIES_BY_DAY = {
  Mon: genHourly(10),
  Tue: genHourly(12),
  Wed: genHourly(9),
  Thu: genHourly(14),
  Fri: genHourly(11),
  Sat: genHourly(7),
  Sun: genHourly(8),
}

export function Dashboard() {
  const { user, logout } = useAuth()
  const role = user?.role || 'customer'
  const [activeTab, setActiveTab] = useState(role === 'customer' ? 'analytics' : 'overview')
  const [selectedYear, setSelectedYear] = useState('All')
  const [selectedMonth, setSelectedMonth] = useState('January')
  const [selectedDay, setSelectedDay] = useState(null)

  const currentWeekSeries = WEEK_SERIES_MAP['Week 1'] || []
  const currentMonthSeries = (selectedYear === 'All'
    ? (MONTH_SERIES_BY_YEAR['2025'][selectedMonth] || [])
    : (MONTH_SERIES_BY_YEAR[selectedYear]?.[selectedMonth] || []))

  const weekMax = Math.max(...currentWeekSeries.map((b) => b.value), 1)
  const monthMax = Math.max(...currentMonthSeries.map((b) => b.value), 1)
  const adminWeeklyMax = Math.max(...(WEEK_SERIES_MAP['Week 1'] || []).map((b) => b.value), 1)
  const hourlySeries = selectedDay && HOURLY_SERIES_BY_DAY[selectedDay] ? HOURLY_SERIES_BY_DAY[selectedDay] : []
  const hourlyMax = Math.max(...hourlySeries.map((b) => b.value), 1)
  

  const monthTotal = currentMonthSeries.reduce((sum, b) => sum + b.value, 0)
  const monthAverage = currentMonthSeries.length ? monthTotal / currentMonthSeries.length : 0

  const baseGrafanaUrl = config.grafanaDashboardUid
    ? `${config.grafanaUrl}/d/${config.grafanaDashboardUid}`
    : config.grafanaUrl

  const opsGrafanaUrl = `${baseGrafanaUrl}?view=ops`
  const analyticsGrafanaUrl = `${baseGrafanaUrl}?view=analytics`
  const customerGrafanaUrl = `${baseGrafanaUrl}?view=customer${user?.customerId ? `&customer=${encodeURIComponent(user.customerId)}` : ''}`
  const customerGrafanaWithYear = selectedYear === 'All' ? customerGrafanaUrl : `${customerGrafanaUrl}&year=${selectedYear}`

  // Customer view: only show customer-scoped analytics
  if (role === 'customer') {
    return (
      <div className="dashboard-container">
        <header className="dashboard-header">
          <h1>Your Analytics</h1>
          <div className="user-info">
            <span>{user?.email || 'User'}</span>
            <button onClick={logout}>Logout</button>
          </div>
        </header>

        <main className="dashboard-content">
          <div className="tab-content">
            <div className="dashboard-section">
              <div className="section-header">
                <h2>Consumption (scoped to you)</h2>
                <select
                  className="month-select"
                  value={selectedYear}
                  onChange={(e) => setSelectedYear(e.target.value)}
                >
                  <option value="All">All years</option>
                  <option value="2025">2025</option>
                  <option value="2024">2024</option>
                </select>
              </div>
              <div className="grafana-embed">
                <iframe
                  src={customerGrafanaWithYear}
                  width="100%"
                  height="320"
                  frameBorder="0"
                  title="Customer Consumption"
                ></iframe>
              </div>
            </div>
            {/* Removed inline year total card; will show at bottom */}

            <div className="dashboard-section">
              <h2>Weekly view (per day)</h2>
              <div className="mini-bar-chart">
                {currentWeekSeries.map((bar) => (
                  <div
                    key={bar.label}
                    className={`bar ${selectedDay === bar.label ? 'selected' : ''}`}
                    onClick={() => setSelectedDay(bar.label)}
                    role="button"
                    tabIndex={0}
                  >
                    <div className="bar-fill" style={{ height: `${(bar.value / weekMax) * 100}%` }}></div>
                    <span className="bar-day">{bar.label}</span>
                  </div>
                ))}
              </div>
            </div>

            {selectedDay && (
              <div className="dashboard-section">
                <h2>Daily breakdown ({selectedDay})</h2>
                <div className="mini-bar-chart hourly">
                  {hourlySeries.map((h) => (
                    <div key={h.label} className="bar small">
                      <div className="bar-fill" style={{ height: `${(h.value / hourlyMax) * 100}%` }}></div>
                      <span className="bar-day">{h.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="dashboard-section">
              <div className="section-header">
                <h2>Monthly view (per day)</h2>
                <select
                  className="month-select"
                  value={selectedMonth}
                  onChange={(e) => setSelectedMonth(e.target.value)}
                >
                  {MONTHS.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
              <div className="mini-bar-chart">
                {currentMonthSeries.map((bar) => (
                  <div key={bar.label} className="bar">
                    <div className="bar-fill" style={{ height: `${(bar.value / monthMax) * 100}%` }}></div>
                    <span className="bar-day">{bar.label}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="summary-cards compact">
              <div className="summary-card blue">
                <div className="summary-label">Total Consumption</div>
                <div className="summary-value">{monthTotal.toFixed(0)} kWh</div>
              </div>
              <div className="summary-card purple">
                <div className="summary-label">Average</div>
                <div className="summary-value">{monthAverage.toFixed(0)} kWh/day</div>
              </div>
            </div>
          </div>
        </main>
      </div>
    )
  }

  // Admin / internal view: ops + analytics tabs
  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>MeterStream Dashboard</h1>
        <div className="user-info">
          <span>Welcome, {user?.email || 'User'}</span>
          <button onClick={logout}>Logout</button>
        </div>
      </header>

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
              <div className="logs">
                <div className="log-entry">
                  <span className="log-badge info">INFO</span>
                  <span className="log-text">System operating normally</span>
                  <span className="log-time">13:05</span>
                </div>
                <div className="log-entry">
                  <span className="log-badge warn">WARN</span>
                  <span className="log-text">Queue length elevated</span>
                  <span className="log-time">12:58</span>
                </div>
                <div className="log-entry">
                  <span className="log-badge info">INFO</span>
                  <span className="log-text">Batch processing completed</span>
                  <span className="log-time">12:45</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="tab-content">
            <div className="dashboard-section">
              <h2>Aggregate Energy Consumption</h2>
              <div className="grafana-embed">
                <iframe
                  src={analyticsGrafanaUrl}
                  width="100%"
                  height="300"
                  frameBorder="0"
                  title="Aggregate Energy Consumption"
                ></iframe>
              </div>
            </div>

            <div className="dashboard-grid">
              <div className="dashboard-section">
                <h2>Top Consumers</h2>
                <div className="table-container">
                  <table className="consumers-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Customer</th>
                        <th>Consumption</th>
                        <th>Change</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>1.</td>
                        <td>Industrial Corp A</td>
                        <td>45 650 kWh</td>
                        <td className="change-positive">+5.7%</td>
                      </tr>
                      <tr>
                        <td>2.</td>
                        <td>Manufacturing Plant B</td>
                        <td>38 940 kWh</td>
                        <td className="change-positive">+2.1%</td>
                      </tr>
                      <tr>
                        <td>3.</td>
                        <td>Datacenter C</td>
                        <td>34 210 kWh</td>
                        <td className="change-negative">-1.3%</td>
                      </tr>
                      <tr>
                        <td>4.</td>
                        <td>Retail Chain D</td>
                        <td>29 850 kWh</td>
                        <td className="change-positive">+8.7%</td>
                      </tr>
                      <tr>
                        <td>5.</td>
                        <td>Office Complex E</td>
                        <td>24 160 kWh</td>
                        <td className="change-positive">+3.4%</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="dashboard-section">
                <h2>Data Quality</h2>
                <div className="quality-metrics">
                  <div className="quality-item">
                    <div className="quality-header">
                      <span>Completeness</span>
                      <span className="quality-value">98.5%</span>
                    </div>
                    <div className="quality-bar">
                      <div className="quality-fill" style={{width: '98.5%'}}></div>
                    </div>
                  </div>
                  <div className="quality-item">
                    <div className="quality-header">
                      <span>Accuracy</span>
                      <span className="quality-value">97.7%</span>
                    </div>
                    <div className="quality-bar">
                      <div className="quality-fill" style={{width: '97.7%'}}></div>
                    </div>
                  </div>
                  <div className="quality-item">
                    <div className="quality-header">
                      <span>Timeliness</span>
                      <span className="quality-value">99.1%</span>
                    </div>
                    <div className="quality-bar">
                      <div className="quality-fill" style={{width: '99.1%'}}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="dashboard-section">
              <h2>Monthly Consumption</h2>
              <div className="grafana-embed">
                <iframe
                  src={analyticsGrafanaUrl}
                  width="100%"
                  height="300"
                  frameBorder="0"
                  title="Monthly Consumption"
                ></iframe>
              </div>
            </div>

            <div className="dashboard-section">
              <h2>This Week</h2>
              <div className="mini-bar-chart">
                {WEEK_SERIES_MAP['Week 1'].map((bar) => (
                  <div key={bar.label} className="bar">
                    <div className="bar-fill" style={{ height: `${(bar.value / adminWeeklyMax) * 100}%` }}></div>
                    <span className="bar-day">{bar.label}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="summary-cards compact two-up">
              <div className="summary-card blue">
                <div className="summary-label">Total Consumption</div>
                <div className="summary-value">892 kWh</div>
              </div>
              <div className="summary-card purple">
                <div className="summary-label">Average</div>
                <div className="summary-value">892 kWh/day</div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
