import { describe, expect, it } from 'vitest'
import { formatDate, formatMoney, fullName, pluralize, shortJobId } from './format'

describe('format', () => {
  it('shows ISO dates the way the portal does', () => {
    expect(formatDate('2025-10-23')).toBe('10/23/2025')
    expect(formatDate(null)).toBe('—')
  })

  it('formats amounts as dollars and keeps unknown values readable', () => {
    expect(formatMoney('1665.00')).toBe('$1,665.00')
    expect(formatMoney(null)).toBe('—')
    expect(formatMoney('n/a')).toBe('n/a')
  })

  it('builds names, short ids and plurals', () => {
    expect(fullName({ first_name: 'Pedro', last_name: 'Rodriguez' })).toBe('Pedro Rodriguez')
    expect(shortJobId('abcdef123456')).toBe('abcdef')
    expect(pluralize(1, 'case')).toBe('1 case')
    expect(pluralize(2, 'person', 'people')).toBe('2 people')
  })
})
