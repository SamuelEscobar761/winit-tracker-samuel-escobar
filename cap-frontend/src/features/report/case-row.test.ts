import { describe, expect, it } from 'vitest'
import { makeCase, makePersonView } from '../test-builders'
import { buildCaseRows, countByGroup, describeGroup, distinct, filterRows, noFilters } from './case-row'

const groups = [
  { group_id: 1, date_of_birth: '1978-07-24', drivers_license: null, case_count: 2, case_keys: [] },
  { group_id: 2, date_of_birth: null, drivers_license: null, case_count: 1, case_keys: [] },
]

const person = makePersonView(
  [
    makeCase({ case_key: 'A', case_number: 'A-1', group_id: 1, status: 'Active', match_label: 'possible' }),
    makeCase({ case_key: 'B', case_number: 'B-2', group_id: 1, status: 'Closed', match_label: 'confirmed' }),
    makeCase({
      case_key: 'C',
      case_number: 'C-3',
      group_id: 2,
      status: 'Active',
      match_label: 'possible',
      caption: 'RODRIGUEZ, PEDRO LUIS',
    }),
  ],
  groups,
)
const rows = buildCaseRows([person])

describe('buildCaseRows', () => {
  it('adds the person and identity group to every case', () => {
    expect(rows.map((row) => row.groupLabel)).toEqual([
      'DOB 07/24/1978',
      'DOB 07/24/1978',
      'No date of birth',
    ])
    expect(rows[0].personName).toBe('Pedro Rodriguez')
    expect(rows[0].personIndex).toBe(0)
  })

  it('describes groups without a date of birth', () => {
    expect(describeGroup(undefined)).toBe('No date of birth')
  })
})

describe('filterRows', () => {
  it('returns everything without filters', () => {
    expect(filterRows(rows, noFilters)).toHaveLength(3)
  })

  it('filters by text over case number, caption and status', () => {
    expect(filterRows(rows, { ...noFilters, text: 'luis' })).toHaveLength(1)
    expect(filterRows(rows, { ...noFilters, text: 'b-2' })).toHaveLength(1)
    expect(filterRows(rows, { ...noFilters, text: 'closed' })).toHaveLength(1)
  })

  it('combines status, match and identity filters', () => {
    const filtered = filterRows(rows, {
      ...noFilters,
      status: 'Active',
      match: 'possible',
      group: 'DOB 07/24/1978',
    })

    expect(filtered.map((row) => row.case_key)).toEqual(['A'])
  })
})

describe('helpers', () => {
  it('lists distinct sorted values', () => {
    expect(distinct(rows, (row) => row.status)).toEqual(['Active', 'Closed'])
  })

  it('counts cases per identity', () => {
    expect(countByGroup(rows).get('DOB 07/24/1978')).toBe(2)
  })
})
