const TEHRAN = 'Asia/Tehran'
const PERSIAN_LOCALE = 'fa-IR-u-ca-persian-nu-latn'

function dateParts(iso, locale = PERSIAN_LOCALE) {
  const date = new Date(`${iso}T12:00:00Z`)
  return Object.fromEntries(
    new Intl.DateTimeFormat(locale, { timeZone: TEHRAN, year: 'numeric', month: 'numeric', day: 'numeric' })
      .formatToParts(date)
      .filter(({ type }) => ['year', 'month', 'day'].includes(type))
      .map(({ type, value }) => [type, Number(value)]),
  )
}

export function getTehranTodayISO(now = new Date()) {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat('en-CA', { timeZone: TEHRAN, year: 'numeric', month: '2-digit', day: '2-digit' })
      .formatToParts(now)
      .filter(({ type }) => ['year', 'month', 'day'].includes(type))
      .map(({ type, value }) => [type, value]),
  )
  return `${parts.year}-${parts.month}-${parts.day}`
}

export function getTehranTime(now = new Date()) {
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: TEHRAN, hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).format(now)
}

export function addDays(iso, amount) {
  const date = new Date(`${iso}T12:00:00Z`)
  date.setUTCDate(date.getUTCDate() + amount)
  return date.toISOString().slice(0, 10)
}

export function getPersianParts(iso) {
  return dateParts(iso)
}

export function formatPersianDate(iso, options = { day: 'numeric', month: 'long', year: 'numeric' }) {
  return new Intl.DateTimeFormat('fa-IR-u-ca-persian', { timeZone: TEHRAN, ...options }).format(new Date(`${iso}T12:00:00Z`))
}

export function getWeekday(iso, style = 'short') {
  return new Intl.DateTimeFormat('fa-IR', { timeZone: TEHRAN, weekday: style }).format(new Date(`${iso}T12:00:00Z`))
}

function samePersianMonth(firstISO, otherISO) {
  const first = dateParts(firstISO)
  const other = dateParts(otherISO)
  return first.year === other.year && first.month === other.month
}

function buildMonth(firstISO) {
  const first = dateParts(firstISO)
  const dates = []
  let cursor = firstISO
  while (samePersianMonth(firstISO, cursor) && dates.length < 32) {
    dates.push(cursor)
    cursor = addDays(cursor, 1)
  }
  return {
    firstISO,
    year: first.year,
    month: first.month,
    dates,
    title: formatPersianDate(firstISO, { month: 'long', year: 'numeric' }),
  }
}

export function getCurrentPersianMonth(todayISO) {
  let firstISO = todayISO
  while (samePersianMonth(todayISO, addDays(firstISO, -1))) firstISO = addDays(firstISO, -1)
  return buildMonth(firstISO)
}

export function shiftPersianMonth(month, direction) {
  const adjacent = direction > 0 ? addDays(month.dates.at(-1), 1) : addDays(month.firstISO, -1)
  if (direction > 0) return buildMonth(adjacent)
  let firstISO = adjacent
  while (samePersianMonth(adjacent, addDays(firstISO, -1))) firstISO = addDays(firstISO, -1)
  return buildMonth(firstISO)
}

export function isSamePersianMonth(firstISO, otherISO) {
  return samePersianMonth(firstISO, otherISO)
}
