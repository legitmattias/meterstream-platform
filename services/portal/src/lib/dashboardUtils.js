// Shared dashboard utilities: constants and helper functions
export const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

export const DOW = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

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
