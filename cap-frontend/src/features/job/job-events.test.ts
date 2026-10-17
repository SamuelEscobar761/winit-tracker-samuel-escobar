import { describe, expect, it } from 'vitest'
import { makeEvent, makePerson } from '../test-builders'
import {
  appendEvents,
  emptyEventLog,
  feedEvents,
  isCaptchaPending,
  laneSlots,
  MAX_EVENTS,
  peopleOfLane,
  portalStatus,
} from './job-events'

describe('appendEvents', () => {
  it('keeps events ordered by id and remembers the last one', () => {
    const log = appendEvents(emptyEventLog, [makeEvent(2), makeEvent(1)])

    expect(log.events.map((event) => event.id)).toEqual([1, 2])
    expect(log.lastId).toBe(2)
  })

  it('ignores events it already has, as after a reconnection replay', () => {
    const first = appendEvents(emptyEventLog, [makeEvent(1), makeEvent(2)])
    const second = appendEvents(first, [makeEvent(2), makeEvent(3)])

    expect(second.events.map((event) => event.id)).toEqual([1, 2, 3])
  })

  it('returns the same log when nothing is new', () => {
    const log = appendEvents(emptyEventLog, [makeEvent(1)])

    expect(appendEvents(log, [makeEvent(1)])).toBe(log)
  })

  it('keeps only the newest events but never forgets the last id', () => {
    const batch = Array.from({ length: MAX_EVENTS + 10 }, (_, index) => makeEvent(index + 1))

    const log = appendEvents(emptyEventLog, batch)

    expect(log.events).toHaveLength(MAX_EVENTS)
    expect(log.events[0].id).toBe(11)
    expect(log.lastId).toBe(MAX_EVENTS + 10)
  })
})

describe('laneSlots', () => {
  it('lists the lanes seen in events or people and pads up to the parallelism', () => {
    const events = [makeEvent(1, { lane: 2 }), makeEvent(2, { lane: 0 })]

    expect(laneSlots(events, [], 3)).toEqual([0, 2, null])
  })

  it('shows placeholders while no worker has started', () => {
    expect(laneSlots([], [makePerson({ lane: null })], 2)).toEqual([null, null])
  })

  it('never hides a lane that exceeds the requested parallelism', () => {
    const people = [makePerson({ lane: 0 }), makePerson({ index: 1, lane: 1 })]

    expect(laneSlots([], people, 1)).toEqual([0, 1])
  })
})

describe('portalStatus', () => {
  it('is down after cap_down and ok again after cap_recovered', () => {
    const down = [makeEvent(1, { type: 'cap_down', lane: null })]
    const recovered = [...down, makeEvent(2, { type: 'cap_recovered', lane: null })]

    expect(portalStatus([])).toBe('ok')
    expect(portalStatus(down)).toBe('down')
    expect(portalStatus(recovered)).toBe('ok')
  })
})

describe('isCaptchaPending', () => {
  const required = makeEvent(1, { type: 'captcha_required' })

  it('is pending until the same lane resolves or finishes the person', () => {
    expect(isCaptchaPending([required], 0)).toBe(true)
    expect(isCaptchaPending([required, makeEvent(2, { type: 'captcha_resolved' })], 0)).toBe(false)
    expect(isCaptchaPending([required, makeEvent(2, { type: 'person_failed' })], 0)).toBe(false)
  })

  it('ignores other lanes and empty slots', () => {
    expect(isCaptchaPending([required], 1)).toBe(false)
    expect(isCaptchaPending([required], null)).toBe(false)
  })
})

describe('feedEvents', () => {
  const events = [
    makeEvent(1, { type: 'searching' }),
    makeEvent(2, { type: 'waiting' }),
    makeEvent(3, { type: 'progress', lane: null }),
    makeEvent(4, { type: 'found', lane: 1 }),
  ]

  it('shows the lane activity without pacing waits by default', () => {
    expect(feedEvents(events, 0, false).map((event) => event.id)).toEqual([1])
  })

  it('can include the pacing waits', () => {
    expect(feedEvents(events, 0, true).map((event) => event.id)).toEqual([1, 2])
  })
})

describe('peopleOfLane', () => {
  it('returns the people a lane served', () => {
    const people = [makePerson({ lane: 0 }), makePerson({ index: 1, lane: 1 })]

    expect(peopleOfLane(people, 1).map((person) => person.index)).toEqual([1])
    expect(peopleOfLane(people, null)).toEqual([])
  })
})
