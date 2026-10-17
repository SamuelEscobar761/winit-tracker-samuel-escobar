import type { EventType, JobEvent, PersonSummary } from '../../shared/api/api-types'

export const MAX_EVENTS = 3000

export interface EventLog {
  events: JobEvent[]
  lastId: number
}

export const emptyEventLog: EventLog = { events: [], lastId: 0 }

export function appendEvents(log: EventLog, batch: JobEvent[]): EventLog {
  const fresh = batch.filter((event) => event.id > log.lastId).sort((a, b) => a.id - b.id)
  if (fresh.length === 0) return log
  return {
    events: [...log.events, ...fresh].slice(-MAX_EVENTS),
    lastId: fresh[fresh.length - 1].id,
  }
}

export function laneSlots(
  events: JobEvent[],
  people: PersonSummary[],
  parallelism: number,
): (number | null)[] {
  const seen = new Set<number>()
  events.forEach((event) => event.lane !== null && seen.add(event.lane))
  people.forEach((person) => person.lane !== null && seen.add(person.lane))
  const lanes = [...seen].sort((a, b) => a - b)
  return Array.from({ length: Math.max(parallelism, lanes.length) }, (_, slot) => lanes[slot] ?? null)
}

export type PortalStatus = 'ok' | 'down'

export function portalStatus(events: JobEvent[]): PortalStatus {
  const last = [...events].reverse().find((event) => event.type === 'cap_down' || event.type === 'cap_recovered')
  return last?.type === 'cap_down' ? 'down' : 'ok'
}

const CAPTCHA_ENDINGS: ReadonlySet<EventType> = new Set([
  'captcha_resolved',
  'person_completed',
  'person_failed',
])

export function isCaptchaPending(events: JobEvent[], lane: number | null): boolean {
  if (lane === null) return false
  const relevant = events.filter(
    (event) =>
      event.lane === lane && (event.type === 'captcha_required' || CAPTCHA_ENDINGS.has(event.type)),
  )
  return relevant[relevant.length - 1]?.type === 'captcha_required'
}

export function feedEvents(events: JobEvent[], lane: number | null, showWaits: boolean): JobEvent[] {
  return events.filter(
    (event) => event.lane === lane && event.type !== 'progress' && (showWaits || event.type !== 'waiting'),
  )
}

export function peopleOfLane(people: PersonSummary[], lane: number | null): PersonSummary[] {
  return lane === null ? [] : people.filter((person) => person.lane === lane)
}

export type FeedTone = 'search' | 'found' | 'warning' | 'error' | 'info' | 'done'

const FEED_TONES: Partial<Record<EventType, FeedTone>> = {
  searching: 'search',
  found: 'found',
  detail_loaded: 'found',
  retrying: 'warning',
  captcha_required: 'warning',
  captcha_resolved: 'found',
  cap_down: 'error',
  detail_failed: 'error',
  person_failed: 'error',
  person_completed: 'done',
  job_complete: 'done',
}

export function feedToneOf(type: EventType): FeedTone {
  return FEED_TONES[type] ?? 'info'
}
