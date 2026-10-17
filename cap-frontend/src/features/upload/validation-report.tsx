import { AlertTriangle, CheckCircle2, Download, XCircle } from 'lucide-react'
import type { ReportRow, RowStatus, ValidationResponse } from '../../shared/api/api-types'
import { downloadText } from '../../shared/lib/download-text'
import { Badge } from '../../shared/ui/badge'
import type { Tone } from '../../shared/ui/tone'
import { buildRejectedRowsCsv } from './rejected-rows-csv'

const ROW_TONES: Record<RowStatus, Tone> = { accepted: 'green', normalized: 'amber', rejected: 'red' }

function RowIcon({ status }: { status: RowStatus }) {
  if (status === 'rejected') return <XCircle size={16} className="mt-0.5 shrink-0 text-rose-500" />
  const color = status === 'normalized' ? 'text-amber-500' : 'text-emerald-500'
  return <CheckCircle2 size={16} className={`mt-0.5 shrink-0 ${color}`} />
}

function rowText(row: ReportRow): string {
  return Object.values(row.original).join(', ')
}

function RowNotes({ row }: { row: ReportRow }) {
  return (
    <>
      {row.issues.map((issue) => (
        <p key={issue.code + issue.message} className="text-xs text-rose-600">
          {issue.message}
        </p>
      ))}
      {row.changes.map((change) => (
        <p key={change.field} className="text-xs text-amber-600">
          Normalized {change.field}: “{change.before}” → “{change.after}” ({change.reason})
        </p>
      ))}
    </>
  )
}

function FileIssues({ issues }: { issues: ValidationResponse['report']['file_issues'] }) {
  if (issues.length === 0) return null
  return (
    <ul className="space-y-1 border-t border-slate-100 px-5 py-3">
      {issues.map((issue) => (
        <li
          key={issue.code}
          className={`flex items-center gap-2 text-xs ${issue.severity === 'error' ? 'text-rose-600' : 'text-amber-700'}`}
        >
          <AlertTriangle size={13} /> {issue.message}
        </li>
      ))}
    </ul>
  )
}

export function ValidationReport({ validation }: { validation: ValidationResponse }) {
  const { report } = validation
  const rejected = report.counts.rejected
  const download = () => downloadText('rejected-rows.csv', buildRejectedRowsCsv(report.rows))

  return (
    <section className="animate-fade-in mt-6 overflow-hidden rounded-3xl bg-white shadow-card ring-1 ring-slate-200/70">
      <header className="flex flex-wrap items-center gap-2 px-5 py-4">
        <h2 className="text-sm font-semibold text-slate-900">Validation report</h2>
        <Badge tone="green">{validation.ready_people} ready</Badge>
        {report.counts.normalized > 0 && <Badge tone="amber">{report.counts.normalized} normalized</Badge>}
        {rejected > 0 && <Badge tone="red">{rejected} rejected</Badge>}
        {rejected > 0 && (
          <button
            type="button"
            onClick={download}
            className="ml-auto inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100"
          >
            <Download size={13} /> Download rejected rows
          </button>
        )}
      </header>
      <FileIssues issues={report.file_issues} />
      <ul className="max-h-72 divide-y divide-slate-50 overflow-y-auto border-t border-slate-100">
        {report.rows.map((row) => (
          <li key={row.line_number} className="flex items-start gap-3 px-5 py-2.5 text-sm">
            <RowIcon status={row.status} />
            <span className="w-8 shrink-0 font-mono text-xs text-slate-400">L{row.line_number}</span>
            <div className="min-w-0 flex-1">
              <p className="truncate font-mono text-xs text-slate-700">{rowText(row)}</p>
              <RowNotes row={row} />
            </div>
            <Badge tone={ROW_TONES[row.status]}>{row.status}</Badge>
          </li>
        ))}
      </ul>
    </section>
  )
}
