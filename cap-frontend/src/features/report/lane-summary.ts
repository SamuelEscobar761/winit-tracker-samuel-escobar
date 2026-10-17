import type { PersonState, PersonSummary, PersonView } from '../../shared/api/api-types'
import { peopleOfLane } from '../job/job-events'
import { buildCaseRows, type CaseRow } from './case-row'

export interface LaneSummary {
  people: PersonSummary[]
  rows: CaseRow[]
  finished: number
  failed: PersonSummary[]
  running: PersonSummary | null
  hasCases: boolean
  isIdle: boolean
  allFailed: boolean
}

const FAILURE_STATES: ReadonlySet<PersonState> = new Set(['failed', 'blocked_captcha'])
const FINISHED_STATES: ReadonlySet<PersonState> = new Set(['done', 'failed', 'blocked_captcha', 'cancelled'])

export function summarizeLane(
  allPeople: PersonSummary[],
  lane: number | null,
  results: Record<number, PersonView>,
): LaneSummary {
  const people = peopleOfLane(allPeople, lane)
  const loaded = people.flatMap((person) => (results[person.index] ? [results[person.index]] : []))
  const failed = people.filter((person) => FAILURE_STATES.has(person.state))
  const finished = people.filter((person) => FINISHED_STATES.has(person.state)).length
  return {
    people,
    rows: buildCaseRows(loaded),
    finished,
    failed,
    running: people.find((person) => person.state === 'running') ?? null,
    hasCases: people.some((person) => person.cases_found > 0),
    isIdle: people.length > 0 && finished === people.length,
    allFailed: people.length > 0 && failed.length === people.length,
  }
}
