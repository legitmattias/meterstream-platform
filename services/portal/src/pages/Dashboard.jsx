import React, { useState, useEffect, useMemo } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { config } from '../config'
import { api } from '../lib/api'
import { MonthBarChart } from '../components/MonthBarChart'
import { ConsumptionChart } from '../components/ConsumptionChart'
import AdminDashboard from './AdminDashboard'
import './Dashboard.css'
import {
  MONTHS,
  DOW,
  getMostRecentDateForDayLabel,
  SWEDISH_MONTHS,
  SWEDISH_MONTHS_SHORT,
  LABELS_SV,
  formatNumber,
  getSwedishMonthName,
  findPeak,
} from '../lib/dashboardUtils'

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
  const [selectedYear, setSelectedYear] = useState('latest')
  const [selectedMonth, setSelectedMonth] = useState('all') // 'all' or 1-12
  const [selectedDay] = useState(null)
  const [weekSeries, setWeekSeries] = useState([])
  const [monthSeries, setMonthSeries] = useState([])
  const [hourlySeries, setHourlySeries] = useState([])
  const [yearSeries, setYearSeries] = useState([])
  const [availableYears, setAvailableYears] = useState([])
  const [loadingData, setLoadingData] = useState(false)
  const [dataError, setDataError] = useState('')
  const [total, setTotal] = useState(null)
  const [average, setAverage] = useState(null)
  const [resolvedYear, setResolvedYear] = useState(null)

  // Comparison mode
  const [showComparison, setShowComparison] = useState(false)
  const [comparisonData, setComparisonData] = useState(null)
  const [loadingComparison, setLoadingComparison] = useState(false)

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

  // Dashboard data (customer only - admin uses different views)
  useEffect(() => {
    if (role !== 'customer') return

    const fetchData = async () => {
      setLoadingData(true)
      setDataError('')
      try {
        const params = new URLSearchParams()
        if (selectedYear && selectedYear.toString().toLowerCase() !== 'all' && selectedYear.toString().toLowerCase() !== 'latest') {
          params.set('year', selectedYear)
        }

        // For customer view, only send month if specific month selected
        if (selectedMonth !== 'all' && selectedYear !== 'All') {
          params.set('month', String(selectedMonth))
        }

        if (selectedDay) {
          const date = getMostRecentDateForDayLabel(selectedDay)
          if (date) params.set('date', date)
        }

        const data = await api.request(`/data/dashboard?${params}`)

        // Store resolved year for display
        if (data && typeof data.year !== 'undefined' && data.year !== null) {
          setResolvedYear(String(data.year))
          if (selectedYear === 'latest' || selectedYear === null || typeof selectedYear === 'undefined') {
            setSelectedYear(String(data.year))
          }
        }

        const weekly = (data.weekly_days || []).map(d => ({ label: d.day, value: d.consumption || 0 }))
        setWeekSeries(DOW.map(d => weekly.find(w => w.label === d) || { label: d, value: 0 }))

        setMonthSeries((data.monthly_days || []).map(d => ({ day: d.day, consumption: d.consumption || 0 })))

        // Yearly months series
        if (Array.isArray(data.yearly_months)) {
          setYearSeries(data.yearly_months.map(m => ({ month: m.month, consumption: m.consumption || 0 })))
        } else {
          setYearSeries([])
        }

        setAvailableYears(Array.isArray(data.available_years) ? data.available_years : [])
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
  }, [role, selectedYear, selectedMonth, selectedDay])

  // Fetch comparison data for previous year (customer only)
  useEffect(() => {
    if (role !== 'customer' || !showComparison || !resolvedYear) {
      setComparisonData(null)
      return
    }

    const prevYear = parseInt(resolvedYear) - 1
    if (isNaN(prevYear)) {
      setComparisonData(null)
      return
    }

    const fetchComparison = async () => {
      setLoadingComparison(true)
      try {
        const params = new URLSearchParams()
        params.set('year', String(prevYear))
        if (selectedMonth !== 'all') {
          params.set('month', String(selectedMonth))
        }

        const data = await api.request(`/data/dashboard?${params}`)

        if (selectedMonth === 'all' && Array.isArray(data.yearly_months)) {
          setComparisonData(data.yearly_months.map(m => ({ month: m.month, consumption: m.consumption || 0 })))
        } else if (selectedMonth !== 'all') {
          setComparisonData((data.monthly_days || []).map(d => ({ day: d.day, consumption: d.consumption || 0 })))
        }
      } catch (err) {
        console.error('Failed to load comparison data', err)
        setComparisonData(null)
      } finally {
        setLoadingComparison(false)
      }
    }

    fetchComparison()
  }, [role, showComparison, resolvedYear, selectedMonth])

  // Computed values for customer view
  const displayYear = resolvedYear || (selectedYear !== 'latest' ? selectedYear : '')
  const comparisonYear = resolvedYear ? parseInt(resolvedYear) - 1 : null

  const peak = useMemo(() => {
    if (selectedMonth === 'all') {
      return findPeak(yearSeries, 'month')
    } else {
      return findPeak(monthSeries, 'day')
    }
  }, [yearSeries, monthSeries, selectedMonth])

  const peakLabel = useMemo(() => {
    if (!peak || !peak.label) return null
    if (selectedMonth === 'all') {
      return getSwedishMonthName(peak.label)
    }
    // Format as "7 maj" instead of "Dag 7"
    const monthName = getSwedishMonthName(parseInt(selectedMonth), true).toLowerCase()
    return `${peak.label} ${monthName}`
  }, [peak, selectedMonth])

  // For admin backward compatibility
  const weekMax = useMemo(() => Math.max(...weekSeries.map(b => b.value), 1), [weekSeries])
  const hourlyMax = useMemo(() => Math.max(...hourlySeries.map(b => b.value), 1), [hourlySeries])
  const monthSeriesLegacy = useMemo(() => monthSeries.map(d => ({ label: String(d.day), value: d.consumption })), [monthSeries])
  const monthTotal = useMemo(() => monthSeries.reduce((s, b) => s + b.consumption, 0), [monthSeries])
  const monthAverage = useMemo(
    () => (monthSeries.length ? monthTotal / monthSeries.length : 0),
    [monthSeries, monthTotal]
  )

  const baseGrafanaUrl = config.grafanaDashboardUid
    ? `${config.grafanaUrl}/d/${config.grafanaDashboardUid}`
    : config.grafanaUrl

  const opsGrafanaUrl = `${baseGrafanaUrl}?view=ops`

  if (loading || activeTab === null) {
    return <div className="dashboard-loading">{LABELS_SV.loading}</div>
  }

  // =====================
  // CUSTOMER VIEW (Swedish "Mina sidor")
  // =====================
  if (role === 'customer') {
    const isMonthlyView = selectedMonth === 'all'
    const chartData = isMonthlyView ? yearSeries : monthSeries
    const chartTitle = isMonthlyView
      ? `${displayYear}`
      : `${getSwedishMonthName(parseInt(selectedMonth))} ${displayYear}`

    return (
      <div className="customer-dashboard">
        <header className="customer-header">
          <div className="customer-header-left">
            <span className="customer-logo">MeterStream</span>
            <h1>{LABELS_SV.title}</h1>
          </div>
          <div className="customer-header-right">
            <span className="customer-email">{user?.email}</span>
            <button className="customer-logout-btn" onClick={logout}>
              {LABELS_SV.logout}
            </button>
          </div>
        </header>

        <main className="customer-main">
          {/* Filters row */}
          <div className="customer-filters">
            <div className="customer-filter-group">
              <label htmlFor="year-select">{LABELS_SV.year}:</label>
              <select
                id="year-select"
                value={selectedYear}
                onChange={(e) => setSelectedYear(e.target.value)}
              >
                {availableYears && availableYears.length > 0 ? (
                  availableYears.map(y => <option key={y} value={y}>{y}</option>)
                ) : (
                  <option value="latest">{resolvedYear || 'Laddar...'}</option>
                )}
              </select>
            </div>

            <div className="customer-filter-group">
              <label htmlFor="month-select">{LABELS_SV.month}:</label>
              <select
                id="month-select"
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
              >
                <option value="all">{LABELS_SV.allMonths}</option>
                {SWEDISH_MONTHS.map((m, idx) => (
                  <option key={idx + 1} value={idx + 1}>{m}</option>
                ))}
              </select>
            </div>

            <div className="customer-filter-group comparison-toggle">
              <label>
                <input
                  type="checkbox"
                  checked={showComparison}
                  onChange={(e) => setShowComparison(e.target.checked)}
                  disabled={!comparisonYear || !availableYears.includes(String(comparisonYear))}
                />
                {LABELS_SV.showPrevYear}
              </label>
            </div>
          </div>

          {/* Summary cards */}
          <div className="customer-cards">
            <div className="customer-card card-total">
              <div className="card-content">
                <span className="card-label">{LABELS_SV.totalConsumption}</span>
                <span className="card-value">
                  {total !== null ? `${formatNumber(total, 1)} ${LABELS_SV.unit}` : '-'}
                </span>
              </div>
            </div>

            <div className="customer-card card-average">
              <div className="card-content">
                <span className="card-label">
                  {isMonthlyView ? LABELS_SV.averageConsumption : LABELS_SV.averageDaily}
                </span>
                <span className="card-value">
                  {average !== null ? `${formatNumber(average, 1)} ${LABELS_SV.unit}` : '-'}
                </span>
              </div>
            </div>

            <div className="customer-card card-peak">
              <div className="card-content">
                <span className="card-label">{LABELS_SV.peakConsumption}</span>
                <span className="card-value">
                  {peak && peak.value > 0
                    ? `${peakLabel}: ${formatNumber(peak.value, 1)} ${LABELS_SV.unit}`
                    : '-'}
                </span>
              </div>
            </div>
          </div>

          {/* Error message */}
          {dataError && (
            <div className="customer-error" role="alert">
              {LABELS_SV.error}: {dataError}
            </div>
          )}

          {/* Main chart section */}
          <section className="customer-chart-section">
            <h2 className="customer-chart-title">{chartTitle}</h2>

            {loadingData || loadingComparison ? (
              <div className="customer-chart-loading">{LABELS_SV.loading}</div>
            ) : chartData && chartData.length > 0 ? (
              <ConsumptionChart
                data={chartData}
                comparisonData={showComparison ? comparisonData : null}
                year={displayYear}
                comparisonYear={showComparison ? comparisonYear : null}
                isMonthly={isMonthlyView}
                height={400}
              />
            ) : (
              <div className="customer-chart-empty">{LABELS_SV.noData}</div>
            )}
          </section>
        </main>

        <footer className="customer-footer">
          <p>Kalmar Energi - Meterstream</p>
        </footer>
      </div>
    )
  }

  // =====================
  // ADMIN VIEW (unchanged)
  // =====================
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
      monthSeries={monthSeriesLegacy}
      weekSeries={weekSeries}
      monthTotal={monthTotal}
      monthAverage={monthAverage}
      weekMax={weekMax}
      hourlyMax={hourlyMax}
    />
  )
}
