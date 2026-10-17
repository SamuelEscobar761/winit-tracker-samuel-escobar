import { describe, expect, it } from 'vitest'
import type { ReportRow } from '../../shared/api/api-types'
import { buildRejectedRowsCsv } from './rejected-rows-csv'

function row(overrides: Partial<ReportRow>): ReportRow {
  return {
    line_number: 2,
    status: 'rejected',
    original: { first_name: 'J0hn', last_name: 'Smith' },
    changes: [],
    issues: [
      {
        code: 'invalid_characters',
        message: 'first_name contains characters that are not letters',
        field: 'first_name',
      },
    ],
    duplicate_of_line: null,
    ...overrides,
  }
}

describe('buildRejectedRowsCsv', () => {
  it('lists only rejected rows with their line number and reasons', () => {
    const accepted = row({ line_number: 3, status: 'accepted', issues: [] })

    const csv = buildRejectedRowsCsv([row({}), accepted])

    expect(csv.split('\n')).toEqual([
      'line_number,reasons,first_name,last_name',
      '2,first_name contains characters that are not letters,J0hn,Smith',
    ])
  })

  it('quotes cells with commas, quotes or line breaks', () => {
    const tricky = row({ original: { first_name: 'A, "B"', last_name: 'C' } })

    expect(buildRejectedRowsCsv([tricky])).toContain('"A, ""B"""')
  })

  it('returns only the header when nothing was rejected', () => {
    expect(buildRejectedRowsCsv([row({ status: 'accepted' })])).toBe('line_number,reasons')
  })
})
