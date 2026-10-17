import type {
  CaseView,
  IdentityGroup,
  JobEvent,
  PersonState,
  PersonSummary,
  PersonView,
} from '../shared/api/api-types'

export function makePerson(overrides: Partial<PersonSummary> = {}): PersonSummary {
  return {
    index: 0,
    line_number: 2,
    first_name: 'Pedro',
    last_name: 'Rodriguez',
    date_of_birth: null,
    external_ref: null,
    state: 'done' as PersonState,
    lane: 0,
    query: 'rodriguez, pedro',
    strategy: 'as_written',
    failure_reason: null,
    cases_found: 0,
    eligible_for_details: 0,
    details_loaded: 0,
    discarded: 0,
    truncated: false,
    ...overrides,
  }
}

export function makeCase(overrides: Partial<CaseView> = {}): CaseView {
  return {
    case_number: '25IN-146136',
    case_key: '25IN146136',
    citation_number: '146136',
    file_date: '2025-10-23',
    caption: 'RODRIGUEZ, PEDRO',
    status: 'Active',
    is_restricted: false,
    date_of_birth: null,
    drivers_license: null,
    match_label: 'possible',
    match_reasons: [],
    group_id: 1,
    detail: null,
    detail_error: null,
    ...overrides,
  }
}

export function makePersonView(cases: CaseView[], groups: IdentityGroup[] = []): PersonView {
  return {
    ...makePerson({ cases_found: cases.length }),
    cases,
    identity_groups: groups,
    discarded_by_reason: {},
  }
}

export function makeEvent(id: number, overrides: Partial<JobEvent> = {}): JobEvent {
  return {
    id,
    type: 'searching',
    job_id: 'job-1',
    timestamp: '2026-10-16T12:00:00Z',
    message: `event ${id}`,
    person_index: 0,
    lane: 0,
    data: {},
    ...overrides,
  }
}
