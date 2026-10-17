import type { CaseView, IdentityGroup, PersonView } from '../../shared/api/api-types'
import { formatDate, fullName } from '../../shared/lib/format'

export interface CaseRow extends CaseView {
  personIndex: number
  personName: string
  groupLabel: string
}

export function describeGroup(group: IdentityGroup | undefined): string {
  if (!group || !group.date_of_birth) return 'No date of birth'
  return `DOB ${formatDate(group.date_of_birth)}`
}

export function buildCaseRows(people: PersonView[]): CaseRow[] {
  return people.flatMap((person) =>
    person.cases.map((item) => ({
      ...item,
      personIndex: person.index,
      personName: fullName(person),
      groupLabel: describeGroup(person.identity_groups.find((group) => group.group_id === item.group_id)),
    })),
  )
}

export interface TableFilters {
  text: string
  status: string
  match: string
  person: string
  group: string
}

export const noFilters: TableFilters = { text: '', status: 'all', match: 'all', person: 'all', group: 'all' }

function matchesText(row: CaseRow, text: string): boolean {
  const needle = text.trim().toLowerCase()
  if (!needle) return true
  const haystack = [row.case_number, row.caption, row.personName, row.status, row.citation_number ?? '']
  return haystack.some((value) => value.toLowerCase().includes(needle))
}

export function filterRows(rows: CaseRow[], filters: TableFilters): CaseRow[] {
  return rows.filter(
    (row) =>
      matchesText(row, filters.text) &&
      (filters.status === 'all' || row.status === filters.status) &&
      (filters.match === 'all' || row.match_label === filters.match) &&
      (filters.person === 'all' || row.personName === filters.person) &&
      (filters.group === 'all' || row.groupLabel === filters.group),
  )
}

export function distinct(rows: CaseRow[], pick: (row: CaseRow) => string): string[] {
  return [...new Set(rows.map(pick))].sort((a, b) => a.localeCompare(b))
}

export function countByGroup(rows: CaseRow[]): Map<string, number> {
  const counts = new Map<string, number>()
  rows.forEach((row) => counts.set(row.groupLabel, (counts.get(row.groupLabel) ?? 0) + 1))
  return counts
}
