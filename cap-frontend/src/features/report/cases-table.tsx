import { useMemo, useState } from 'react'
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from '@tanstack/react-table'
import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react'
import { filterRows, noFilters, type CaseRow, type TableFilters } from './case-row'
import { caseColumns } from './table-columns'
import { TableToolbar } from './table-toolbar'

interface CasesTableProps {
  rows: CaseRow[]
  onOpen: (row: CaseRow) => void
}

function SortIcon({ direction }: { direction: false | 'asc' | 'desc' }) {
  if (direction === 'asc') return <ArrowUp size={12} />
  if (direction === 'desc') return <ArrowDown size={12} />
  return <ArrowUpDown size={12} className="opacity-40" />
}

export function CasesTable({ rows, onOpen }: CasesTableProps) {
  'use no memo'
  const [sorting, setSorting] = useState<SortingState>([])
  const [filters, setFilters] = useState<TableFilters>(noFilters)
  const data = useMemo(() => filterRows(rows, filters), [rows, filters])
  const isSinglePerson = new Set(rows.map((row) => row.personIndex)).size <= 1
  const table = useReactTable({
    data,
    columns: caseColumns,
    state: { sorting, columnVisibility: { personName: !isSinglePerson } },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  return (
    <div>
      <TableToolbar rows={rows} shownCount={data.length} filters={filters} onChange={setFilters} />
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            {table.getHeaderGroups().map((group) => (
              <tr key={group.id} className="border-y border-slate-100 bg-slate-50/70">
                {group.headers.map((header) => (
                  <th
                    key={header.id}
                    aria-sort={ariaSort(header.column.getIsSorted())}
                    className="whitespace-nowrap px-3 py-2 text-xs font-medium text-slate-500"
                  >
                    <button
                      type="button"
                      onClick={header.column.getToggleSortingHandler()}
                      className="inline-flex items-center gap-1 hover:text-slate-800"
                    >
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      <SortIcon direction={header.column.getIsSorted()} />
                    </button>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                tabIndex={0}
                onClick={() => onOpen(row.original)}
                onKeyDown={(event) => event.key === 'Enter' && onOpen(row.original)}
                className="cursor-pointer border-b border-slate-50 text-slate-700 transition hover:bg-indigo-50/50 focus:bg-indigo-50/70 focus:outline-none"
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="whitespace-nowrap px-3 py-2.5">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {data.length === 0 && (
          <p className="px-4 py-6 text-center text-xs text-slate-400">No case matches these filters.</p>
        )}
      </div>
    </div>
  )
}

function ariaSort(direction: false | 'asc' | 'desc') {
  if (direction === 'asc') return 'ascending'
  if (direction === 'desc') return 'descending'
  return 'none'
}
