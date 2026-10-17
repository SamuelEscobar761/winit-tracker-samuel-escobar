import { useCallback, useEffect, useState } from 'react'
import type { Person } from './csv'
import { SCRIPTS, type CaseRecord } from './data'

export type JobStatus = 'queued' | 'running' | 'captcha' | 'done'
export type Outcome = 'done' | 'no_cases' | 'failed'
export type Page = 'idle' | 'search' | 'form' | 'captcha' | 'results' | 'case' | 'error' | 'done'
export type EventKind = 'search' | 'found' | 'captcha' | 'error' | 'info' | 'done'

export interface FeedEvent {
  id: number
  t: string
  kind: EventKind
  text: string
}
export interface CaseRow extends CaseRecord {
  jobId: string
  personName: string
}
export interface Job {
  id: string
  status: JobStatus
  persons: Person[]
  pi: number
  phase: number
  ci: number
  t: number
  page: Page
  typed: string
  solved: Record<string, true>
  outcomes: Record<string, Outcome>
  events: FeedEvent[]
  cases: CaseRow[]
}

const clock = (t: number) => `${String(Math.floor(t / 60)).padStart(2, '0')}:${String(t % 60).padStart(2, '0')}`
const fullName = (p: Person) => `${p.firstName} ${p.lastName}`

const emit = (j: Job, kind: EventKind, text: string): Job => ({
  ...j,
  events: [...j.events, { id: j.events.length + 1, t: clock(j.t), kind, text }],
})
const nextPerson = (j: Job, o: Outcome): Job => ({
  ...j,
  outcomes: { ...j.outcomes, [j.persons[j.pi].id]: o },
  pi: j.pi + 1,
  phase: 0,
  ci: 0,
  page: 'search',
})

// One tick = one visible step of the (simulated) scraper.
export function stepJob(prev: Job): Job {
  if (prev.status === 'done' || prev.status === 'captcha') return prev
  const j: Job = { ...prev, t: prev.t + 1, status: 'running' }
  const p = j.persons[j.pi]
  if (!p) return { ...emit(j, 'done', 'Job complete'), status: 'done', page: 'done' }
  const script = SCRIPTS[p.key] ?? { cases: [] }

  switch (j.phase) {
    case 0:
      return { ...emit(j, 'search', `Searching ${fullName(p)}…`), phase: 1, page: 'form', typed: '' }
    case 1:
      return { ...j, phase: 2, typed: fullName(p) }
    case 2:
      if (script.error)
        return nextPerson(
          { ...emit(j, 'error', `CAP returned an error page for ${fullName(p)} (HTTP 500). Moving on.`), page: 'error' },
          'failed',
        )
      if (script.captcha && !j.solved[p.id])
        return { ...emit(j, 'captcha', `CAPTCHA required for ${fullName(p)}: solve it in the live view`), status: 'captcha', page: 'captcha' }
      return { ...(script.captcha ? emit(j, 'info', 'CAPTCHA solved by operator') : j), phase: 3, page: 'results' }
    case 3: {
      const n = script.cases.length
      if (!n) return nextPerson(emit(j, 'info', `No cases found for ${fullName(p)}`), 'no_cases')
      const more = script.total && script.total > n ? ` (showing ${n} of ${script.total})` : ''
      return { ...emit(j, 'found', `Found ${script.total ?? n} cases for ${fullName(p)}${more}`), phase: 4 }
    }
    default: {
      const k = script.cases[j.ci]
      if (!k) return nextPerson(j, 'done')
      const row: CaseRow = { ...k, jobId: j.id, personName: fullName(p) }
      return { ...emit(j, 'info', `Parsed case ${k.caseNumber}`), ci: j.ci + 1, page: 'case', cases: [...j.cases, row] }
    }
  }
}

export function buildJobs(n: number, persons: Person[], firstIndex = 1): Job[] {
  return Array.from({ length: n }, (_, i) => ({
    id: `J-${String(firstIndex + i).padStart(2, '0')}`,
    status: 'queued' as JobStatus,
    persons: persons.filter((_, k) => k % n === i),
    pi: 0, phase: 0, ci: 0, t: 0,
    page: 'idle' as Page,
    typed: '',
    solved: {}, outcomes: {}, events: [], cases: [],
  }))
}

export function useRun(tickMs = 900) {
  const [jobs, setJobs] = useState<Job[]>([])
  const active = jobs.some((j) => j.status === 'queued' || j.status === 'running')

  useEffect(() => {
    if (!active) return
    const id = setInterval(() => setJobs((js) => js.map(stepJob)), tickMs)
    return () => clearInterval(id)
  }, [active, tickMs])

  const start = useCallback((n: number, persons: Person[]) => setJobs(buildJobs(n, persons)), [])
  const reset = useCallback(() => setJobs([]), [])
  const solveCaptcha = useCallback(
    (id: string) =>
      setJobs((js) =>
        js.map((j) => {
          if (j.id !== id || j.status !== 'captcha') return j
          const p = j.persons[j.pi]
          return { ...j, status: 'running', solved: { ...j.solved, [p.id]: true } }
        }),
      ),
    [],
  )
  return { jobs, start, reset, solveCaptcha, setJobs }
}
