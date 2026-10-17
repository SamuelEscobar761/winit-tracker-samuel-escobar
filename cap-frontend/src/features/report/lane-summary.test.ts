import { describe, expect, it } from 'vitest'
import { makeCase, makePerson, makePersonView } from '../test-builders'
import { summarizeLane } from './lane-summary'

describe('summarizeLane', () => {
  it('counts what a lane finished and what failed', () => {
    const people = [
      makePerson({ index: 0, lane: 0, state: 'done', cases_found: 1 }),
      makePerson({ index: 1, lane: 0, state: 'failed' }),
      makePerson({ index: 2, lane: 1, state: 'running' }),
    ]

    const summary = summarizeLane(people, 0, {})

    expect(summary.people).toHaveLength(2)
    expect(summary.finished).toBe(2)
    expect(summary.failed.map((person) => person.index)).toEqual([1])
    expect(summary.isIdle).toBe(true)
    expect(summary.allFailed).toBe(false)
  })

  it('builds the rows from the people already loaded', () => {
    const people = [makePerson({ index: 0, lane: 0, cases_found: 1 })]

    const summary = summarizeLane(people, 0, { 0: makePersonView([makeCase()]) })

    expect(summary.rows).toHaveLength(1)
    expect(summary.hasCases).toBe(true)
  })

  it('detects a worker whose searches all failed', () => {
    const people = [makePerson({ index: 0, lane: 0, state: 'failed' })]

    expect(summarizeLane(people, 0, {}).allFailed).toBe(true)
  })

  it('reports the running person and an empty slot', () => {
    const people = [makePerson({ index: 0, lane: 0, state: 'running' })]

    expect(summarizeLane(people, 0, {}).running?.index).toBe(0)
    expect(summarizeLane(people, null, {}).people).toEqual([])
  })
})
