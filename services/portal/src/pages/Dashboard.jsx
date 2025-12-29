import React, { useState, useEffect, useMemo } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { config } from '../config'
import { api } from '../lib/api'
import { MonthBarChart } from '../components/MonthBarChart'
import AdminDashboard from './AdminDashboard'
import './Dashboard.css'
import { MONTHS, DOW, getMostRecentDateForDayLabel } from '../lib/dashboardUtils'

export function Dashboard() {
  const { user, logout, loading } = useAuth()
  const role = user?.role || 'customer'

  // Decide active tab after auth loads
  const [activeTab, setActiveTab] = useState(null)
  useEffect(() => {
    if (!loading) {
      setActiveTab(role === 'admin' ? 'overview' : 'analytics')
    }
  }, [loading, role])

  // Admin / internal data
  const [quality, setQuality] = useState({ completeness: null, accuracy: null, timeliness: null })
  const [topConsumers, setTopConsumers] = useState([])
  const [logs, setLogs] = useState([])

  // Dashboard state
  // Default to 2023 data (data CSV ranges 2020-2023)
  const [selectedYear] = useState('2023')
  const [selectedMonth] = useState(MONTHS[0])
  const [selectedDay] = useState(null)
  const [weekSeries, setWeekSeries] = useState([])
  const [monthSeries, setMonthSeries] = useState([])
  const [hourlySeries, setHourlySeries] = useState([])
  const [loadingData, setLoadingData] = useState(false)
  const [dataError, setDataError] = useState('')
  const [total, setTotal] = useState(null)
  const [average, setAverage] = useState(null)

  // Data quality (admin/internal only)
  useEffect(() => {
    if (activeTab === 'analytics' && (role === 'admin' || role === 'internal')) {
      api.request('/data/quality')
        .then(d => {
          setQuality({
            completeness: d.completeness ?? null,
            accuracy: d.accuracy ?? null,
            timeliness: d.timeliness ?? null,
          })
        })
        .catch(err => {
          console.error('Failed to fetch data quality', err)
          setQuality({ completeness: null, accuracy: null, timeliness: null })
        })
    }
  }, [activeTab, role])

  // Admin-only data
  useEffect(() => {
    if (role !== 'admin') return

    let mounted = true
    const fetchAdminData = async () => {
      try {
        const tc = await api.request('/data/top-consumers')
        if (mounted) setTopConsumers(tc.consumers || [])
      } catch {
        if (mounted) setTopConsumers([])
      }

      try {
        const lg = await api.request('/data/logs')
        if (mounted) setLogs(lg.logs || [])
      } catch {
        if (mounted) setLogs([])
      }
    }

    fetchAdminData()
    return () => { mounted = false }
  }, [role])

  // Dashboard data
  useEffect(() => {
    const fetchData = async () => {
      setLoadingData(true)
      setDataError('')
      try {
        const params = new URLSearchParams()
        if (selectedYear !== 'All') params.set('year', selectedYear)

        const monthIdx = MONTHS.indexOf(selectedMonth)
        if (monthIdx !== -1 && selectedYear !== 'All') {
          params.set('month', String(monthIdx + 1))
        }

        if (selectedDay) {
          const date = getMostRecentDateForDayLabel(selectedDay)
          if (date) params.set('date', date)
        }

        const data = await api.request(`/data/dashboard?${params}`)

        const weekly = (data.weekly_days || []).map(d => ({ label: d.day, value: d.consumption || 0 }))
        setWeekSeries(DOW.map(d => weekly.find(w => w.label === d) || { label: d, value: 0 }))

        setMonthSeries((data.monthly_days || []).map(d => ({ label: String(d.day), value: d.consumption || 0 })))
        setHourlySeries((data.hourly || []).map(h => ({ label: `${h.hour}:00`, value: h.consumption || 0 })))

        setTotal(typeof data.total === 'number' ? data.total : null)
        setAverage(typeof data.average === 'number' ? data.average : null)
      } catch (err) {
        console.error('Failed to load dashboard data', err)
        setDataError(err.message || 'Failed to load data')
      } finally {
        setLoadingData(false)
      }
    }

    fetchData()
  }, [selectedYear, selectedMonth, selectedDay])

  const weekMax = useMemo(() => Math.max(...weekSeries.map(b => b.value), 1), [weekSeries])
  const hourlyMax = useMemo(() => Math.max(...hourlySeries.map(b => b.value), 1), [hourlySeries])
  const monthTotal = useMemo(() => monthSeries.reduce((s, b) => s + b.value, 0), [monthSeries])
  const monthAverage = useMemo(
    () => (monthSeries.length ? monthTotal / monthSeries.length : 0),
    [monthSeries, monthTotal]
  )

  const baseGrafanaUrl = config.grafanaDashboardUid
    ? `${config.grafanaUrl}/d/${config.grafanaDashboardUid}`
    : config.grafanaUrl

  const opsGrafanaUrl = `${baseGrafanaUrl}?view=ops`

  if (loading || activeTab === null) {
    return <div className="dashboard-loading">Loading…</div>
  }

  if (role === 'customer') {
    return (
      <div className="dashboard-container">
        <header className="dashboard-header">
          <h1>Mina Sidor</h1>
          <div className="user-info">
            <span>{user?.email}</span>
            <button onClick={logout}>Logout</button>
          </div>
        </header>

        <main className="dashboard-content">
          <div className="summary-cards compact">
            <div className="summary-card blue">
              <div className="summary-label">Total Consumption</div>
              <div className="summary-value">
                {total !== null ? `${total.toFixed(0)} kWh` : `${monthTotal.toFixed(0)} kWh`}
              </div>
            </div>
            <div className="summary-card purple">
              <div className="summary-label">Average</div>
              <div className="summary-value">
                {average !== null ? `${average.toFixed(0)} kWh/day` : `${monthAverage.toFixed(0)} kWh/day`}
              </div>
            </div>
          </div>

          {dataError && (
            <div className="dashboard-error" role="status">
              Error loading data: {dataError}
            </div>
          )}

          {loadingData ? (
            <div className="dashboard-loading-data">Loading data…</div>
          ) : (
            <MonthBarChart data={monthSeries} type="bar" />
          )}
        </main>
      </div>
    )
  }

  return (
    <AdminDashboard
      user={user}
      logout={logout}
      activeTab={activeTab}
      setActiveTab={setActiveTab}
      opsGrafanaUrl={opsGrafanaUrl}
      logs={logs}
      topConsumers={topConsumers}
      quality={quality}
      monthSeries={monthSeries}
      weekSeries={weekSeries}
      monthTotal={monthTotal}
      monthAverage={monthAverage}
      weekMax={weekMax}
      hourlyMax={hourlyMax}
    />
  )
}
