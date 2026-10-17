import { useMemo, useState } from 'react'
import { createColumnHelper, flexRender, getCoreRowModel, getFilteredRowModel, getSortedRowModel, useReactTable, type SortingState } from '@tanstack/react-table'
import { ArrowDown, ArrowUp, ArrowUpDown, Search } from 'lucide-react'
import type { CaseRow } from './sim'
import { Badge, ConfidenceBadge } from './ui'

const col = createColumnHelper<CaseRow>()
const TYPE_TONE = { Traffic: 'indigo', Civil: 'slate', Criminal: 'red', Probate: 'amber' } as const
const CONF_ORDER = { confirmed: 0, probable: 1, possible: 2 }

export function CasesTable({ rows, onOpen }: { rows: CaseRow[]; onOpen: (c: CaseRow) => void }) {
  'use no memo' // TanStack Table returns unstable references; opt out of React Compiler
  const [sorting, setSorting] = useState<SortingState>([])
  const [filter, setFilter] = useState('')
  const [type, setType] = useState('all')

  const data = useMemo(() => (type === 'all' ? rows : rows.filter((r) => r.type === type)), [rows, type])
  const columns = useMemo(
    () => [
      col.accessor('personName', { header: 'Person' }),
      col.accessor('caseNumber', { header: 'Case #', cell: (i) => <span className="font-mono text-xs">{i.getValue()}</span> }),
      col.accessor('type', { header: 'Type', cell: (i) => <Badge tone={TYPE_TONE[i.getValue()]}>{i.getValue()}</Badge> }),
      col.accessor('status', { header: 'Status' }),
      col.accessor('filingDate', { header: 'Filed' }),
      col.accessor('nextHearing', { header: 'Next hearing', cell: (i) => i.getValue() ?? <span className="text-slate-300">—</span> }),
      col.accessor('confidence', {
        header: 'Match',
        sortingFn: (a, b) => CONF_ORDER[a.original.confidence] - CONF_ORDER[b.original.confidence],
        cell: (i) => <ConfidenceBadge value={i.getValue()} />,
      }),
    ],
    [],
  )
  const table = useReactTable({
    data,
    columns,
    state: { sorting, globalFilter: filter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  })

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 px-4 pb-3">
        <label className="relative">
          <Search size={14} className="absolute left-2.5 top-2.5 text-slate-400" />
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter cases…"
            className="w-44 rounded-lg border-0 bg-slate-100 py-2 pl-8 pr-3 text-xs outline-none ring-1 ring-transparent focus:bg-white focus:ring-indigo-300"
          />
        </label>
        <select value={type} onChange={(e) => setType(e.target.value)} className="rounded-lg bg-slate-100 px-2.5 py-2 text-xs outline-none focus:ring-1 focus:ring-indigo-300">
          <option value="all">All types</option>
          {Object.keys(TYPE_TONE).map((t) => (
            <option key={t}>{t}</option>
          ))}
        </select>
        <span className="ml-auto text-xs text-slate-400">{table.getRowModel().rows.length} of {rows.length} cases</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id} className="border-y border-slate-100 bg-slate-50/70">
                {hg.headers.map((h) => {
                  const dir = h.column.getIsSorted()
                  return (
                    <th key={h.id} className="whitespace-nowrap px-4 py-2 text-xs font-medium text-slate-500">
                      <button onClick={h.column.getToggleSortingHandler()} className="inline-flex items-center gap-1 hover:text-slate-800">
                        {flexRender(h.column.columnDef.header, h.getContext())}
                        {dir === 'asc' ? <ArrowUp size={12} /> : dir === 'desc' ? <ArrowDown size={12} /> : <ArrowUpDown size={12} className="opacity-40" />}
                      </button>
                    </th>
                  )
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((r) => (
              <tr key={r.id} onClick={() => onOpen(r.original)} className="animate-fade-in cursor-pointer border-b border-slate-50 text-slate-700 transition hover:bg-indigo-50/50">
                {r.getVisibleCells().map((c) => (
                  <td key={c.id} className="whitespace-nowrap px-4 py-2.5">{flexRender(c.column.columnDef.cell, c.getContext())}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
