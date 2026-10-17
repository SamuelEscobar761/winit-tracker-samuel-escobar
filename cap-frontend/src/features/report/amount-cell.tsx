import { AlertTriangle } from 'lucide-react'
import { formatMoney } from '../../shared/lib/format'
import type { CaseRow } from './case-row'

export function AmountCell({ row }: { row: CaseRow }) {
  if (row.detail_error) {
    return (
      <span className="inline-flex items-center gap-1 text-amber-600" title={row.detail_error}>
        <AlertTriangle size={12} /> unavailable
      </span>
    )
  }
  if (!row.detail) return <span className="text-slate-300">—</span>
  return <span className="tabular-nums">{formatMoney(row.detail.amount_due)}</span>
}
