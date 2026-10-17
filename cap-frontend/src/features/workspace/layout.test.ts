import { describe, expect, it } from 'vitest'
import { splitSlots } from './layout'

describe('splitSlots', () => {
  it('keeps every slot in one list for two panes', () => {
    expect(splitSlots([1, 2, 3], 2)).toEqual([[1, 2, 3]])
  })

  it.each([
    [0, [[], []]],
    [1, [[1], []]],
    [3, [[1, 2], [3]]],
    [4, [[1, 2], [3, 4]]],
  ])('gives the top lists ceil(n/2) slots for %i slots in four panes', (count, expected) => {
    const slots = Array.from({ length: count }, (_, index) => index + 1)
    expect(splitSlots(slots, 4)).toEqual(expected)
  })
})
