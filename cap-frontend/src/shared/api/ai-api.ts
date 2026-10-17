import { http } from './http-client'
import type {
  AiStatus,
  Insight,
  MatchExplanation,
  RepairOutcome,
  RulesOverview,
} from './api-types'

const personPath = (jobId: string, personIndex: number) => `/ai/jobs/${jobId}/people/${personIndex}`

export const aiApi = {
  status: () => http.get<AiStatus>('/ai/status'),
  explainMatch: (jobId: string, personIndex: number, caseKey: string) =>
    http.post<MatchExplanation>(`${personPath(jobId, personIndex)}/cases/${encodeURIComponent(caseKey)}/explain`),
  summarisePerson: (jobId: string, personIndex: number) =>
    http.post<Insight>(`${personPath(jobId, personIndex)}/insight`),
}

export const rulesApi = {
  overview: () => http.get<RulesOverview>('/rules'),
  repair: (incidentId: string) => http.post<RepairOutcome>(`/rules/incidents/${incidentId}/repair`),
  approve: (proposalId: string) => http.post<unknown>(`/rules/proposals/${proposalId}/approve`),
  reject: (proposalId: string) => http.post<null>(`/rules/proposals/${proposalId}/reject`),
  rollback: (version: number) => http.postJson<unknown>('/rules/rollback', { version }),
}
