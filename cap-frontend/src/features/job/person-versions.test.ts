import { describe, expect, it } from 'vitest'
import { makePerson } from '../test-builders'
import { findStalePeople, versionOf } from './person-versions'

describe('findStalePeople', () => {
  const done = makePerson({ index: 0, cases_found: 3 })

  it('asks for people that were never loaded', () => {
    expect(findStalePeople([done], new Map(), new Set())).toEqual([done])
  })

  it('skips queued people, people being loaded and up-to-date ones', () => {
    const queued = makePerson({ index: 1, state: 'queued' })
    const versions = new Map([[0, versionOf(done)]])

    expect(findStalePeople([done, queued], versions, new Set())).toEqual([])
    expect(findStalePeople([done], new Map(), new Set([0]))).toEqual([])
  })

  it('asks again when new cases or details arrive', () => {
    const versions = new Map([[0, versionOf(done)]])
    const updated = makePerson({ index: 0, cases_found: 3, details_loaded: 2 })

    expect(findStalePeople([updated], versions, new Set())).toEqual([updated])
  })
})
