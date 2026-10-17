import { http } from './http-client'
import type {
  CreatedJob,
  JobListItem,
  JobSnapshot,
  PersonView,
  PublicConfig,
  RawCase,
  SessionInfo,
  ValidationResponse,
} from './api-types'

function buildForm(file: File, parallelism?: number): FormData {
  const form = new FormData()
  form.append('file', file)
  if (parallelism !== undefined) form.append('parallelism', String(parallelism))
  return form
}

export const jobsApi = {
  validate: (file: File) => http.postForm<ValidationResponse>('/jobs/validate', buildForm(file)),
  create: (file: File, parallelism: number) =>
    http.postForm<CreatedJob>('/jobs', buildForm(file, parallelism)),
  list: () => http.get<JobListItem[]>('/jobs'),
  get: (jobId: string) => http.get<JobSnapshot>(`/jobs/${jobId}`),
  getPerson: (jobId: string, personIndex: number) =>
    http.get<PersonView>(`/jobs/${jobId}/people/${personIndex}`),
  getRawCase: (jobId: string, personIndex: number, caseKey: string) =>
    http.get<RawCase>(`/jobs/${jobId}/people/${personIndex}/cases/${encodeURIComponent(caseKey)}/raw`),
  cancel: (jobId: string) => http.post<JobSnapshot>(`/jobs/${jobId}/cancel`),
  retryFailed: (jobId: string) => http.post<JobSnapshot>(`/jobs/${jobId}/retry-failed`),
  markCaptchaSolved: (jobId: string, personIndex: number) =>
    http.post<null>(`/jobs/${jobId}/people/${personIndex}/captcha-solved`),
}

export const sessionApi = {
  get: () => http.get<SessionInfo>('/auth/session'),
  login: (token: string) => http.postJson<null>('/auth/login', { token }),
  logout: () => http.post<null>('/auth/logout'),
}

export const configApi = {
  get: () => http.get<PublicConfig>('/config'),
}
