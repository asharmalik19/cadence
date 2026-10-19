// Date helpers. Dates travel as YYYY-MM-DD strings; parse them as local days, never UTC.
export const parseDay = (day: string) => {
  const [y, m, d] = day.split('-').map(Number)
  return new Date(y, m - 1, d)
}

export const toDay = (date: Date) =>
  `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`

export const addDays = (day: string, n: number) => {
  const date = parseDay(day)
  date.setDate(date.getDate() + n)
  return toDay(date)
}

export const formatDay = (day: string, opts: Intl.DateTimeFormatOptions = { weekday: 'short', day: 'numeric', month: 'short' }) =>
  parseDay(day).toLocaleDateString('en-GB', opts)

export const formatLong = (day: string) =>
  formatDay(day, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })

export const formatMinutes = (minutes: number) => {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return h === 0 ? `${m} min` : m === 0 ? `${h} h` : `${h} h ${m} min`
}
