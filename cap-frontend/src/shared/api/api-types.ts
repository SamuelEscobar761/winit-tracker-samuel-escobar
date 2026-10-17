export type PersonState = 'queued' | 'running' | 'done' | 'failed' | 'blocked_captcha' | 'cancelled'
export type JobState = 'queued' | 'running' | 'completed' | 'cancelled'
export type MatchLabel = 'confirmed' | 'probable' | 'possible' | 'unlikely'
export type RowStatus = 'accepted' | 'normalized' | 'rejected'

export type EventType =
  | 'job_created'
  | 'job_started'
  | 'searching'
  | 'waiting'
  | 'retrying'
  | 'found'
  | 'detail_loaded'
  | 'detail_failed'
  | 'captcha_required'
  | 'captcha_resolved'
  | 'cap_down'
  | 'cap_recovered'
  | 'person_completed'
  | 'person_failed'
  | 'progress'
  | 'job_retry'
  | 'job_complete'
  | 'job_cancelled'

export interface JobEvent {
  id: number
  type: EventType
  job_id: string
  timestamp: string
  message: string
  person_index: number | null
  lane: number | null
  data: Record<string, unknown>
}

export interface Progress {
  queued: number
  running: number
  done: number
  failed: number
  blocked_captcha: number
  cancelled: number
  total: number
  finished: number
  percent: number
}

export interface PersonSummary {
  index: number
  line_number: number
  first_name: string
  last_name: string
  date_of_birth: string | null
  external_ref: string | null
  state: PersonState
  lane: number | null
  query: string | null
  strategy: string | null
  failure_reason: string | null
  cases_found: number
  eligible_for_details: number
  details_loaded: number
  discarded: number
  truncated: boolean
}

export interface Charge {
  statute: string
  description: string
}

export interface PaymentPlan {
  past_amount_due: string | null
  monthly_amount: string | null
  remaining_balance: string | null
}

export interface CaseDetail {
  charges: Charge[]
  amount_due: string | null
  proof_of_correction_required: boolean
  has_payment_plan: boolean
  payment_plan: PaymentPlan | null
  is_extension_eligible: boolean
  original_date: string | null
  extended_date: string | null
  notices: string[]
}

export interface CaseView {
  case_number: string
  case_key: string
  citation_number: string | null
  file_date: string | null
  caption: string
  status: string
  is_restricted: boolean
  date_of_birth: string | null
  drivers_license: string | null
  match_label: MatchLabel
  match_reasons: string[]
  group_id: number | null
  detail: CaseDetail | null
  detail_error: string | null
}

export interface IdentityGroup {
  group_id: number
  date_of_birth: string | null
  drivers_license: string | null
  case_count: number
  case_keys: string[]
}

export interface PersonView extends PersonSummary {
  cases: CaseView[]
  identity_groups: IdentityGroup[]
  discarded_by_reason: Record<string, number>
}

export interface ReportIssue {
  code: string
  message: string
  field: string | null
}

export interface ReportChange {
  field: string
  before: string
  after: string
  reason: string
}

export interface ReportRow {
  line_number: number
  status: RowStatus
  original: Record<string, string>
  changes: ReportChange[]
  issues: ReportIssue[]
  duplicate_of_line: number | null
}

export interface FileIssue {
  code: string
  severity: 'error' | 'warning'
  message: string
}

export interface ImportReport {
  encoding: string | null
  delimiter: string | null
  counts: Record<RowStatus, number>
  rows: ReportRow[]
  file_issues: FileIssue[]
}

export interface ValidationResponse {
  report: ImportReport
  ready_people: number
  max_parallelism: number
  default_parallelism: number
}

export interface JobSnapshot {
  job_id: string
  state: JobState
  created_at: string
  parallelism: number
  progress: Progress
  people: PersonSummary[]
  report: ImportReport
}

export interface JobListItem {
  job_id: string
  state: JobState
  created_at: string
  total_people: number
  progress: Progress
}

export interface CreatedJob {
  job_id: string
  state: JobState
  parallelism: number
  total_people: number
  events_url: string
  report: ImportReport
}

export interface RawCase {
  case_key: string
  is_restricted: boolean
  search_item: Record<string, unknown>
  search_source_url: string | null
  search_scraped_at: string | null
  detail_response: Record<string, unknown> | null
  detail_source_url: string | null
  detail_scraped_at: string | null
}

export interface PublicConfig {
  provider: 'mock' | 'replica' | 'live'
  max_workers: number
  default_parallelism: number
  csv_max_bytes: number
  csv_max_rows: number
}

export interface SessionInfo {
  authentication_required: boolean
  authenticated: boolean
}

export interface LaneStatus {
  lane: number
  job_id: string | null
  person_index: number | null
  person_state: PersonState | null
  awaiting_captcha: boolean
}

export type InputOutcome = 'ignored' | 'forwarded' | 'captcha_resolved' | 'invalid'

export type InputEvent =
  | { type: 'click'; x: number; y: number }
  | { type: 'text'; text: string }
  | { type: 'key'; key: string }
  | { type: 'scroll'; delta_y: number }

export interface AiStatus {
  enabled: boolean
  available: boolean
  mode: 'off' | 'anthropic' | 'offline-mock'
  model: string | null
  rules_auto_apply: boolean
  reason: string | null
}

export interface MatchExplanation {
  case_key: string
  label: string
  summary: string
  supports: string[]
  weakens: string[]
  next_step: string
  model: string
  ai_generated: boolean
}

export interface InsightFinding {
  text: string
  case_keys: string[]
}

export interface Insight {
  headline: string
  findings: InsightFinding[]
  model: string
  dropped_findings: number
}

export interface RuleChange {
  path: string
  before: unknown
  after: unknown
}

export interface ChangeEntry {
  version: number
  previous_version: number | null
  at: string
  actor: 'bootstrap' | 'agent' | 'manual' | 'rollback'
  reason: string
  incident_id: string | null
  model: string | null
  canary: string | null
  changes: RuleChange[]
}

export type IncidentStatus = 'open' | 'repairing' | 'repaired' | 'awaiting_review' | 'failed' | 'dismissed'

export interface DriftIncident {
  id: string
  at: string
  kind: 'ui' | 'response'
  message: string
  rules_version: number
  status: IncidentStatus
  outcome: string | null
}

export interface RulesProposal {
  id: string
  at: string
  incident_id: string
  diagnosis: string
  model: string
  changes: RuleChange[]
  canary: { passed: boolean; detail: string }
  status: 'pending' | 'applied' | 'rejected'
}

export interface RulesOverview {
  active: { version: number }
  versions: number[]
  changelog: ChangeEntry[]
  incidents: DriftIncident[]
  proposals: RulesProposal[]
  ai: AiStatus
}

export interface RepairOutcome {
  incident_id: string
  status: IncidentStatus
  message: string
  proposal_id: string | null
  applied_version: number | null
}
