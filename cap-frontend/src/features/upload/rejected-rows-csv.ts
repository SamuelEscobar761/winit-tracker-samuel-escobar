import type { ReportRow } from '../../shared/api/api-types'

function escapeCell(value: string): string {
  return /[",\n]/.test(value) ? `"${value.replaceAll('"', '""')}"` : value
}

export function buildRejectedRowsCsv(rows: ReportRow[]): string {
  const rejected = rows.filter((row) => row.status === 'rejected')
  const columns = [...new Set(rejected.flatMap((row) => Object.keys(row.original)))]
  const header = ['line_number', 'reasons', ...columns]
  const lines = rejected.map((row) => [
    String(row.line_number),
    row.issues.map((issue) => issue.message).join(' | '),
    ...columns.map((column) => row.original[column] ?? ''),
  ])
  return [header, ...lines].map((cells) => cells.map(escapeCell).join(',')).join('\n')
}
