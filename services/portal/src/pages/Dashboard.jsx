import React from 'react';
import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { config } from '../config'
import { api } from '../lib/api'
import { MonthBarChart } from '../components/MonthBarChart'
import AdminDashboard from './AdminDashboard'
import './Dashboard.css'
import { MONTHS, DOW, getMostRecentDateForDayLabel } from '../lib/dashboardUtils'

// (MONTHS, DOW and getMostRecentDateForDayLabel are imported from ../lib/dashboardUtils)

export function Dashboard() {
  // --- All state declarations at the top ---
  const { user, logout } = useAuth()
  const role = user?.role || 'customer'
  const [activeTab, setActiveTab] = useState(role === 'customer' ? 'analytics' : 'overview')
  const [quality, setQuality] = useState({ completeness: null, accuracy: null, timeliness: null })
  const [topConsumers, setTopConsumers] = useState([])
  const [logs, setLogs] = useState([])
  const [selectedYear, setSelectedYear] = useState('All')
  const [selectedMonth, setSelectedMonth] = useState('January')
  const [selectedDay, setSelectedDay] = useState(null)
  const [weekSeries, setWeekSeries] = useState([])
  const [monthSeries, setMonthSeries] = useState([])
  const [hourlySeries, setHourlySeries] = useState([])
  const [loadingData, setLoadingData] = useState(false)
  const [dataError, setDataError] = useState('')
  const [total, setTotal] = useState(null)
  const [average, setAverage] = useState(null)

  // --- Effects and logic below ---
  // Fetch data quality metrics when analytics tab is active
  useEffect(() => {
    // Only fetch admin/internal endpoints for non-customer roles
    if (activeTab === 'analytics' && role !== 'customer') {
      api.request('/data/quality')
        .then(data => {
          setQuality({
            completeness: data.completeness ?? null,
            accuracy: data.accuracy ?? null,
            timeliness: data.timeliness ?? null,
          })
        })
        .catch(err => {
          console.error('Failed to fetch data quality', err)
          setQuality({ completeness: null, accuracy: null, timeliness: null })
        })
    }
  }, [activeTab, role])

  // Fetch top consumers and logs when analytics tab is active
  useEffect(() => {
    // Only fetch admin/internal endpoints for non-customer roles
    if (activeTab === 'analytics' && role !== 'customer') {
      api.request('/data/top-consumers')
        .then(data => {
          setTopConsumers(data.consumers || [])
        })
        .catch(err => {
          console.error('Failed to fetch top consumers', err)
          setTopConsumers([])
        })
      api.request('/data/logs')
        .then(data => {
          setLogs(data.logs || [])
        })
        .catch(err => {
          console.error('Failed to fetch logs', err)
          setLogs([])
        })
    }
  }, [activeTab, role])

  useEffect(() => {
    const fetchData = async () => {
      setLoadingData(true)
      setDataError('')
      try {
        const params = new URLSearchParams()
        if (selectedYear && selectedYear !== 'All') params.set('year', String(selectedYear))
        const monthIdx = MONTHS.indexOf(selectedMonth)
        if (monthIdx !== -1 && selectedYear !== 'All') params.set('month', String(monthIdx + 1))
        if (selectedDay) {
          const date = getMostRecentDateForDayLabel(selectedDay)
          if (date) params.set('date', date)
        }

        const data = await api.request(`/data/dashboard?${params.toString()}`)

        // Summary values returned by the dashboard endpoint
        setTotal(data.total ?? null)
        setAverage(data.average ?? null)

        const weekly = (data.weekly_days || []).map(d => ({ label: d.day, value: d.consumption || 0 }))
        const weeklyOrdered = DOW.map(day => weekly.find(w => w.label === day) || { label: day, value: 0 })
        setWeekSeries(weeklyOrdered)

        const monthly = (data.monthly_days || []).map(d => ({ label: String(d.day), value: d.consumption || 0 }))
        setMonthSeries(monthly)

        const hourly = (data.hourly || []).map(h => ({ label: `${h.hour}:00`, value: h.consumption || 0 }))
        setHourlySeries(hourly)
      } catch (err) {
        console.error('Failed to load dashboard data', err)
        setDataError(err.message || 'Failed to load data')
      } finally {
        setLoadingData(false)
      }
    }
    fetchData()
  }, [selectedYear, selectedMonth, selectedDay])

  const weekMax = React.useMemo(() => Math.max(...weekSeries.map((b) => b.value), 1), [weekSeries])
  const hourlyMax = React.useMemo(() => Math.max(...hourlySeries.map((b) => b.value), 1), [hourlySeries])
  const monthTotal = React.useMemo(() => monthSeries.reduce((sum, b) => sum + b.value, 0), [monthSeries])
  const monthAverage = React.useMemo(() => monthSeries.length ? monthTotal / monthSeries.length : 0, [monthSeries, monthTotal])

  const baseGrafanaUrl = config.grafanaDashboardUid
    ? `${config.grafanaUrl}/d/${config.grafanaDashboardUid}`
    : config.grafanaUrl

  // Only used for admin/internal view
  const opsGrafanaUrl = `${baseGrafanaUrl}?view=ops`

  // Customer view: show custom charts using Influx data
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
              {loadingData ? (
                <div>Loading data…</div>
              ) : dataError ? (
                <div style={{ color: '#b91c1c' }}>Error: {dataError}</div>
              ) : monthSeries && monthSeries.length > 0 ? (
                <MonthBarChart data={monthSeries} type={"line"} key={'line'} />
              ) : (
                <div style={{ color: '#64748b' }}>No data available for this month.</div>
              )}
            </div>

            <div className="dashboard-section">
              <h2>Weekly view (per day)</h2>
              <div className="mini-bar-chart">
                {weekSeries.map((bar) => (
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
                {dataError && hourlySeries.length === 0 ? (
                  <div style={{ color: '#b91c1c', margin: '1em 0' }}>
                    {dataError.includes('500')
                      ? 'No data available for this day or a server error occurred.'
                      : dataError}
                  </div>
                ) : (
                  <div className="mini-bar-chart hourly">
                    {hourlySeries.length === 0 ? (
                      <div style={{ color: '#64748b', margin: '1em 0' }}>No data for this day.</div>
                    ) : (
                      hourlySeries.map((h) => (
                        <div key={h.label} className="bar small">
                          <div className="bar-fill" style={{ height: `${(h.value / hourlyMax) * 100}%` }}></div>
                          <span className="bar-day">{h.label}</span>
                        </div>
                      ))
                    )}
                  </div>
                )}
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
              {loadingData ? (
                <div>Loading data…</div>
              ) : dataError ? (
                <div style={{ color: '#b91c1c' }}>Error: {dataError.includes('500') ? 'No data available for this month or a server error occurred.' : dataError}</div>
              ) : monthSeries && monthSeries.length > 0 ? (
                <MonthBarChart data={monthSeries} type={"bar"} key={'bar'} />
              ) : (
                <div style={{ color: '#64748b' }}>No data available for this month.</div>
              )}
            </div>

            <div className="summary-cards compact">
              <div className="summary-card blue">
                <div className="summary-label">Total Consumption</div>
                <div className="summary-value">
                  {total !== null ? `${Number(total).toFixed(0)} kWh` : (monthSeries && monthSeries.length > 0 ? `${monthTotal.toFixed(0)} kWh` : '—')}
                </div>
              </div>
              <div className="summary-card purple">
                <div className="summary-label">Average</div>
                <div className="summary-value">
                  {average !== null ? `${Number(average).toFixed(0)} kWh/day` : (monthSeries && monthSeries.length > 0 ? `${monthAverage.toFixed(0)} kWh/day` : '—')}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    )
  }

  // Admin / internal view: ops + analytics tabs
  return (
    <AdminDashboard
      user={user}
      logout={logout}
      monthTotal={monthTotal}
      monthAverage={monthAverage}
      hourlyMax={hourlyMax}
      weekMax={weekMax}
      activeTab={activeTab}
      setActiveTab={setActiveTab}
      opsGrafanaUrl={opsGrafanaUrl}
      logs={logs}
      topConsumers={topConsumers}
      quality={quality}
      monthSeries={monthSeries}
      weekSeries={weekSeries}
    />
  )
}
