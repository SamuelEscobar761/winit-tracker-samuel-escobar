import { useEffect, useRef, useState } from 'react'
import type { PersonSummary, PersonView } from '../../shared/api/api-types'
import { jobsApi } from '../../shared/api/jobs-api'
import { findStalePeople, versionOf } from './person-versions'

const MAX_CONCURRENT_LOADS = 3

export function usePersonResults(jobId: string, people: PersonSummary[]): Record<number, PersonView> {
  const [results, setResults] = useState<Record<number, PersonView>>({})
  const [tick, setTick] = useState(0)
  const versions = useRef(new Map<number, string>())
  const loading = useRef(new Set<number>())

  useEffect(() => {
    const free = MAX_CONCURRENT_LOADS - loading.current.size
    const stale = findStalePeople(people, versions.current, loading.current).slice(0, Math.max(free, 0))
    stale.forEach((person) => {
      const requested = versionOf(person)
      loading.current.add(person.index)
      jobsApi
        .getPerson(jobId, person.index)
        .then((view) => {
          versions.current.set(person.index, requested)
          setResults((previous) => ({ ...previous, [person.index]: view }))
        })
        .catch(() => undefined)
        .finally(() => {
          loading.current.delete(person.index)
          setTick((value) => value + 1)
        })
    })
  }, [jobId, people, tick])

  return results
}
