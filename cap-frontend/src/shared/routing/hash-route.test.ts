import { describe, expect, it } from 'vitest'
import { jobHash, liveHash, parseRoute } from './hash-route'

describe('parseRoute', () => {
  it('opens the upload screen by default', () => {
    expect(parseRoute('')).toEqual({ name: 'home' })
    expect(parseRoute('#/unknown')).toEqual({ name: 'home' })
  })

  it('recognises a job and a standalone lane view', () => {
    expect(parseRoute('#/job/ab12cd34ef56')).toEqual({ name: 'job', jobId: 'ab12cd34ef56' })
    expect(parseRoute('#/live/2')).toEqual({ name: 'live', lane: 2 })
  })

  it('recognises the portal rules screen', () => {
    expect(parseRoute('#/rules')).toEqual({ name: 'rules' })
  })

  it('rejects ids with unexpected characters', () => {
    expect(parseRoute('#/job/../secret')).toEqual({ name: 'home' })
    expect(parseRoute('#/live/x')).toEqual({ name: 'home' })
  })

  it('builds links that parse back', () => {
    expect(parseRoute(jobHash('abc123'))).toEqual({ name: 'job', jobId: 'abc123' })
    expect(parseRoute(liveHash(1))).toEqual({ name: 'live', lane: 1 })
  })
})
