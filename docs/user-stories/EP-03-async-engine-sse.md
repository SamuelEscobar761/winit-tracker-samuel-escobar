# EP-03 — Async scraping engine & SSE

Brief area: Feature 2; backend architecture & concurrency (20%).

## Epic changelog
| Date | Change |
|---|---|
| 2026-10-15 | Epic created from challenge brief (US-03.1 – US-03.6) |
| 2026-10-16 | Step 5 implemented: US-03.1 - US-03.6 Done (engine in `cap-backend/app/jobs/`, API in `cap-backend/app/api/`) |
| 2026-10-15 | Note: browser frames travel on a separate channel from the replayable event log; see US-09.2 |

---

### US-03.1 — Background jobs with immediate job_id
**Status:** Done | **Priority:** Must | **Depends on:** US-02.1
**As a** user **I want** the upload to return a `job_id` immediately **so that** the UI never blocks on scraping.

**Acceptance criteria**
- [x] `POST /jobs` validates, creates job, enqueues, responds fast
- [x] `GET /jobs/{id}` returns state snapshot (per-person status, counts)

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief | Initial setup |
| 2026-10-16 | STATUS | Proposed → In progress (roadmap Step 5: engine, jobs and SSE) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented: `POST /jobs` (multipart CSV, optional `parallelism`) answers 201 with `job_id`, the validation report and `events_url` before any search; `GET /jobs/{id}` snapshot (state, progress, people); also `GET /jobs` and `GET /jobs/{id}/people/{n}` in `cap-backend/app/api/jobs_router.py` | Roadmap Step 5 |
| 2026-10-16 | STATUS | In progress -> Done (all criteria met and tested; 283 backend tests) | Roadmap Step 5 |

### US-03.2 — Bounded concurrency
**Status:** Done | **Priority:** Must | **Depends on:** US-03.1
**As an** operator **I want** a configurable pool of browser contexts shared across jobs **so that** three users uploading 200 names don't overload the server or CAP.

**Acceptance criteria**
- [x] Global worker limit via env (e.g. `MAX_WORKERS`); fair scheduling across jobs
- [x] Per-worker throttle (few requests/minute)
- [x] Graceful shutdown; no hanging tasks

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief concurrency question | Initial setup |
| 2026-10-16 | COMMENT | Per-worker throttle is now concrete: `CAP_ACTION_DELAY_SECONDS` (default 5) and `CAP_MAX_ACTIONS_PER_MINUTE` (default 12; was 10 s / 6 before the 2026-10-16 amendment of US-01.7), see US-01.7. Capacity maths for the debrief: ≈15 s per person minimum, so 200 names ≈ 50 min per worker (docs/cap-traffic-integration.md §5) | User requirement |
| 2026-10-15 | COMMENT | Users choose concurrent jobs per run (US-09.10); this global limit stays the upper bound | Live workspace request |
| 2026-10-16 | STATUS | Proposed → In progress (roadmap Step 5: engine, jobs and SSE) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented: `cap-backend/app/jobs/`scheduler.py` (round-robin across jobs, per-job parallelism capped by `MAX_WORKERS`) and `cap-backend/app/jobs/`worker_pool.py` (one provider session per lane; stopping cancels the workers and the recovery task); throttle from Step 4 | Roadmap Step 5 |
| 2026-10-16 | STATUS | In progress -> Done (all criteria met and tested; 283 backend tests) | Roadmap Step 5 |

### US-03.3 — Retries, backoff and per-person timeouts
**Status:** Done | **Priority:** Must | **Depends on:** US-03.2, US-01.2
**As a** user **I want** transient failures retried with backoff and bounded by a timeout **so that** one bad name (e.g. the 47th) doesn't kill the job.

**Acceptance criteria**
- [x] Exponential backoff with jitter; max attempts configurable
- [x] Per-person timeout; final state `failed` with reason; job continues
- [x] CAPTCHA/CAP-down are distinct, non-retried-blindly states

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief failure question | Initial setup |
| 2026-10-16 | COMMENT | Retry policy hook: every retry of a person starts with the provider's position check (back on Step 1? Party Name selected?) defined in US-01.4, before backoff is applied | User requirement |
| 2026-10-16 | COMMENT | Portal-specific states for the engine: `SessionExpired` (token expires after a while; reload, re-select Party Name, retry the same person; counts as a retry, not a failure), `CapDown` (maintenance/applicationmode signals, pauses the job), and a slow detail call (~5 s) to include in the per-person timeout. See US-01.4 | Network investigation |
| 2026-10-16 | COMMENT | Provider errors expose `retryable`: `SessionExpired` and `ProviderTimeout` are retried with backoff; `NoResults`, `CapDown`, `CaptchaRequired`, `DetailNotAvailable`, `UnparsedLayout` are not retried blindly (`cap-backend/app/providers/errors.py`) | Roadmap Step 4 |
| 2026-10-16 | STATUS | Proposed → In progress (roadmap Step 5: engine, jobs and SSE) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented: `cap-backend/app/jobs/`retry.py` (backoff 2^n x base + jitter, per-operation timeout from `SEARCH_TIMEOUT_SECONDS` / `DETAIL_TIMEOUT_SECONDS`, only retryable errors), `cap-backend/app/jobs/`person_processor.py` (final state `failed` with reason, the job continues), `cap-backend/app/jobs/`cap_gate.py` (portal down pauses all workers and re-queues the person instead of failing it), CAPTCHA wait with timeout leading to `blocked_captcha` | Roadmap Step 5 |
| 2026-10-16 | STATUS | In progress -> Done (all criteria met and tested; 283 backend tests) | Roadmap Step 5 |

### US-03.4 — Per-job SSE stream
**Status:** Done | **Priority:** Must | **Depends on:** US-03.1
**As a** user **I want** `GET /jobs/{id}/events` to stream progress ("Searching Pedro Rodriguez…", "Found 3 cases", "CAPTCHA required", "Job complete") **so that** I see live activity.

**Acceptance criteria**
- [x] Typed event schema (searching, found, captcha_required, person_failed, progress, job_complete…)
- [x] Heartbeat comments; headers disabling proxy buffering (`X-Accel-Buffering: no`, `Cache-Control: no-cache`)
- [x] Stream closes after job completion

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief | Initial setup |
| 2026-10-16 | STATUS | Proposed → In progress (roadmap Step 5: engine, jobs and SSE) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented: typed `JobEvent`s (`cap-backend/app/jobs/events.py`), SSE route with `id`/`event`/`data` frames, heartbeat comments every `SSE_HEARTBEAT_SECONDS`, `X-Accel-Buffering: no` and `Cache-Control: no-cache` (`cap-backend/app/api/sse.py`); the stream ends when the job is closed | Roadmap Step 5 |
| 2026-10-16 | STATUS | In progress -> Done (all criteria met and tested; 283 backend tests) | Roadmap Step 5 |

### US-03.5 — Reconnect with Last-Event-ID
**Status:** Done | **Priority:** Must | **Depends on:** US-03.4
**As a** user **I want** reconnecting clients to resume from the last event **so that** no progress is lost.

**Acceptance criteria**
- [x] Per-job append-only event log with monotonic ids
- [x] Replay events after `Last-Event-ID`; works after page refresh

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief | Initial setup |
| 2026-10-16 | STATUS | Proposed → In progress (roadmap Step 5: engine, jobs and SSE) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented: `cap-backend/app/jobs/event_log.py` (ids 1..n, in memory) and replay from the `Last-Event-ID` header or `?after=`; tests in `cap-backend/tests/jobs/test_event_log.py` and `tests/api/test_jobs_api.py`. Limitation: logs are lost on server restart | Roadmap Step 5 |
| 2026-10-16 | STATUS | In progress -> Done (all criteria met and tested; 283 backend tests) | Roadmap Step 5 |

### US-03.6 — Job control
**Status:** Done | **Priority:** Could | **Depends on:** US-03.1
**As a** user **I want** to cancel a job and retry failed people **so that** I stay in control.

**Acceptance criteria**
- [x] Cancel stops queued work and emits event
- [x] Retry failed persons without re-running successful ones

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | Operational extension (not explicit in brief) | Initial setup |
| 2026-10-16 | STATUS | Proposed → In progress (roadmap Step 5: engine, jobs and SSE) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented in `cap-backend/app/jobs/`service.py`: `POST /jobs/{id}/cancel` (queued people cancelled, running ones stop at the next checkpoint, event `job_cancelled`) and `POST /jobs/{id}/retry-failed` (only failed or blocked people are re-queued, log reopened, event `job_retry`) | Roadmap Step 5 |
| 2026-10-16 | STATUS | In progress -> Done (all criteria met and tested; 283 backend tests) | Roadmap Step 5 |
