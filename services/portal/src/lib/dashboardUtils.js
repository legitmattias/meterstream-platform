// Shared dashboard utilities: constants and helper functions

// English months (kept for admin/backwards compatibility)
export const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

// Swedish months
export const SWEDISH_MONTHS = ['Januari', 'Februari', 'Mars', 'April', 'Maj', 'Juni', 'Juli', 'Augusti', 'September', 'Oktober', 'November', 'December']

export const SWEDISH_MONTHS_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'Maj', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec']

export const DOW = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

// Swedish UI labels
export const LABELS_SV = {
  title: 'Mina sidor',
  logout: 'Logga ut',
  year: 'År',
  month: 'Månad',
  allMonths: 'Hela året',
  showPrevYear: 'Jämför med föregående år',
  totalConsumption: 'Total förbrukning',
  averageConsumption: 'Snitt per månad',
  averageDaily: 'Snitt per dag',
  peakConsumption: 'Högsta förbrukning',
  monthlyChart: 'Månadsförbrukning',
  dailyChart: 'Daglig förbrukning',
  unit: 'kWh',
  loading: 'Laddar...',
  noData: 'Ingen data tillgänglig',
  error: 'Kunde inte hämta data',
}

export function getMostRecentDateForDayLabel(label) {
  const targetIdx = DOW.indexOf(label)
  if (targetIdx === -1) return null
  const now = new Date()
  const todayIdx = (now.getDay() + 6) % 7 // convert Sun=0.. to Mon=0..
  const diff = (todayIdx - targetIdx + 7) % 7
  const date = new Date(now)
  date.setDate(now.getDate() - diff)
  const yyyy = date.getFullYear()
  const mm = String(date.getMonth() + 1).padStart(2, '0')
  const dd = String(date.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

// Format number with Swedish locale (space as thousand separator)
export function formatNumber(value, decimals = 0) {
  if (value === null || value === undefined) return '-'
  return value.toLocaleString('sv-SE', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

// Get Swedish month name from month number (1-12)
export function getSwedishMonthName(monthNum, short = false) {
  const months = short ? SWEDISH_MONTHS_SHORT : SWEDISH_MONTHS
  return months[(monthNum - 1) % 12] || ''
}

// Find peak value in array of {consumption} objects
export function findPeak(data, labelKey = 'month') {
  if (!data || data.length === 0) return null
  let peak = { value: 0, label: null }
  data.forEach(item => {
    if (item.consumption > peak.value) {
      peak = { value: item.consumption, label: item[labelKey] }
    }
  })
  return peak
}
