import { createColumnHelper } from '@tanstack/react-table'
import { formatDate } from '../../shared/lib/format'
import type { CaseRow } from './case-row'
import { AmountCell } from './amount-cell'
import { MatchBadge } from './match-badge'
import { MATCH_ORDER } from './match-labels'
import { StatusBadge } from './status-badge'

const column = createColumnHelper<CaseRow>()

function amountOf(row: CaseRow): number {
  return Number(row.detail?.amount_due ?? Number.NEGATIVE_INFINITY)
}

export const caseColumns = [
  column.accessor('personName', { header: 'Person' }),
  column.accessor('case_number', {
    header: 'Case #',
    cell: (info) => <span className="font-mono text-xs">{info.getValue()}</span>,
  }),
  column.accessor('caption', {
    header: 'Name on case',
    cell: (info) => (
      <span className="block max-w-44 truncate" title={info.getValue()}>
        {info.getValue()}
      </span>
    ),
  }),
  column.accessor('file_date', {
    header: 'File date',
    cell: (info) => formatDate(info.getValue()),
  }),
  column.accessor('status', {
    header: 'Status',
    cell: (info) => <StatusBadge status={info.getValue()} isRestricted={info.row.original.is_restricted} />,
  }),
  column.display({
    id: 'amount',
    header: 'Amount',
    sortingFn: (a, b) => amountOf(a.original) - amountOf(b.original),
    cell: (info) => <AmountCell row={info.row.original} />,
  }),
  column.accessor('match_label', {
    header: 'Match',
    sortingFn: (a, b) => MATCH_ORDER[a.original.match_label] - MATCH_ORDER[b.original.match_label],
    cell: (info) => <MatchBadge value={info.getValue()} />,
  }),
]
