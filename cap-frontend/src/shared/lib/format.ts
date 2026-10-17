export function formatDate(value: string | null): string {
  if (!value) return '—'
  const [year, month, day] = value.split('-')
  return year && month && day ? `${month}/${day}/${year}` : value
}

export function formatMoney(value: string | null): string {
  if (value === null || value === '') return '—'
  const amount = Number(value)
  if (Number.isNaN(amount)) return value
  return amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
}

export function formatClock(isoTimestamp: string): string {
  const date = new Date(isoTimestamp)
  return date.toLocaleTimeString('en-GB', { hour12: false })
}

export function shortJobId(jobId: string): string {
  return jobId.slice(0, 6)
}

export function fullName(person: { first_name: string; last_name: string }): string {
  return `${person.first_name} ${person.last_name}`
}

export function pluralize(count: number, singular: string, plural = `${singular}s`): string {
  return `${count} ${count === 1 ? singular : plural}`
}
