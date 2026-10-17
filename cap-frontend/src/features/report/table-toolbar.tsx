import { Search } from 'lucide-react'
import { distinct, type CaseRow, type TableFilters } from './case-row'
import { MATCH_OPTIONS } from './match-labels'

interface TableToolbarProps {
  rows: CaseRow[]
  shownCount: number
  filters: TableFilters
  onChange: (filters: TableFilters) => void
}

interface FilterSelectProps {
  label: string
  value: string
  allLabel: string
  options: { value: string; label: string }[]
  onChange: (value: string) => void
}

function FilterSelect({ label, value, allLabel, options, onChange }: FilterSelectProps) {
  return (
    <select
      aria-label={label}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="max-w-40 rounded-lg bg-slate-100 px-2.5 py-2 text-xs outline-none focus:ring-1 focus:ring-indigo-300"
    >
      <option value="all">{allLabel}</option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  )
}

const asOptions = (values: string[]) => values.map((value) => ({ value, label: value }))

export function TableToolbar({ rows, shownCount, filters, onChange }: TableToolbarProps) {
  const set = (patch: Partial<TableFilters>) => onChange({ ...filters, ...patch })
  const people = distinct(rows, (row) => row.personName)
  const groups = distinct(rows, (row) => row.groupLabel)

  return (
    <div className="flex flex-wrap items-center gap-2 px-4 pb-3">
      <label className="relative">
        <Search size={14} className="absolute left-2.5 top-2.5 text-slate-400" />
        <input
          value={filters.text}
          onChange={(event) => set({ text: event.target.value })}
          placeholder="Filter cases…"
          aria-label="Filter cases"
          className="w-40 rounded-lg border-0 bg-slate-100 py-2 pl-8 pr-3 text-xs outline-none ring-1 ring-transparent focus:bg-white focus:ring-indigo-300"
        />
      </label>
      <FilterSelect
        label="Status"
        value={filters.status}
        allLabel="All statuses"
        options={asOptions(distinct(rows, (row) => row.status))}
        onChange={(status) => set({ status })}
      />
      <FilterSelect
        label="Match"
        value={filters.match}
        allLabel="All matches"
        options={MATCH_OPTIONS}
        onChange={(match) => set({ match })}
      />
      {people.length > 1 && (
        <FilterSelect label="Person" value={filters.person} allLabel="All people" options={asOptions(people)} onChange={(person) => set({ person })} />
      )}
      {groups.length > 1 && (
        <FilterSelect label="Identity" value={filters.group} allLabel="All identities" options={asOptions(groups)} onChange={(group) => set({ group })} />
      )}
      <span className="ml-auto text-xs text-slate-400">
        {shownCount} of {rows.length} cases
      </span>
    </div>
  )
}
