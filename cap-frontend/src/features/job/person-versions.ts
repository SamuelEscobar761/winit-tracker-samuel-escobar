import type { PersonSummary } from '../../shared/api/api-types'

export function versionOf(person: PersonSummary): string {
  return `${person.state}|${person.cases_found}|${person.details_loaded}|${person.failure_reason ?? ''}`
}

export function findStalePeople(
  people: PersonSummary[],
  loadedVersions: ReadonlyMap<number, string>,
  loading: ReadonlySet<number>,
): PersonSummary[] {
  return people.filter(
    (person) =>
      person.state !== 'queued' &&
      !loading.has(person.index) &&
      loadedVersions.get(person.index) !== versionOf(person),
  )
}
