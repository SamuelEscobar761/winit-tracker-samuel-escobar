import type { EventType } from './api-types'

export const EVENT_TYPES: readonly EventType[] = [
  'job_created',
  'job_started',
  'searching',
  'waiting',
  'retrying',
  'found',
  'detail_loaded',
  'detail_failed',
  'captcha_required',
  'captcha_resolved',
  'cap_down',
  'cap_recovered',
  'person_completed',
  'person_failed',
  'progress',
  'job_retry',
  'job_complete',
  'job_cancelled',
]

export const CLOSING_EVENT_TYPES: ReadonlySet<EventType> = new Set(['job_complete', 'job_cancelled'])

export const SNAPSHOT_EVENT_TYPES: ReadonlySet<EventType> = new Set([
  'job_created',
  'job_started',
  'found',
  'detail_loaded',
  'detail_failed',
  'person_completed',
  'person_failed',
  'job_retry',
  'job_complete',
  'job_cancelled',
  'captcha_required',
  'captcha_resolved',
])
