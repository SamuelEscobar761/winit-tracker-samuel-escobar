# Debrief notes

Short answers to the brief's debrief questions, with where to open the code. Details and trade-offs: [DECISIONS.md](../DECISIONS.md).

## Transport: why SSE
Updates only flow server to client; uploads, cancel, retry and "CAPTCHA solved" are plain REST. `EventSource` reconnects by itself and sends `Last-Event-ID`; each job has an append-only log with ids so a client resumes in order (`?after=` after a page refresh). Proxy risks: response buffering (`X-Accel-Buffering: no`, nginx `proxy_buffering off`) and idle timeouts (heartbeat comment every 15 s). The screencast is different (large lossy frames), so it has its own WebSocket and is never in the replayable log.
Code: `cap-backend/app/api/sse.py`, `app/jobs/event_log.py`, `cap-frontend/src/features/job/use-event-stream.ts`, `cap-frontend/nginx.conf`.

## Concurrency: three users upload 200 names
All three `POST /jobs` return a `job_id` and the validation report at once; work is queued. `MAX_WORKERS` long-lived lanes (one browser session each) are shared by all jobs and a `FairScheduler` alternates between jobs, so one big upload cannot starve the others. Each action waits 5 s and each worker does at most 12 actions per minute, so 600 people at about 15 s each over 3 workers is roughly 50 minutes before details; the UI shows progress from the events. In-memory state in one process is the known limit (a queue and shared event store would be needed to scale out).
Code: `app/jobs/scheduler.py`, `worker_pool.py`, `app/providers/throttle/`.

## Failure: CAP errors on the 47th name
Only that person is affected. Retryable errors (expired session, timeout, HTTP 5xx) are retried with exponential backoff and jitter up to `MAX_RETRIES`, after first checking the page is back on Step 1 with Party Name selected. If retries run out the person is `failed` with the reason and the job continues; `retry-failed` re-runs only failed people. Portal in maintenance pauses all workers and a health check reopens the gate; a CAPTCHA pauses that person for a human.
Code: `app/jobs/retry.py`, `person_processor.py`, `cap_gate.py`, `app/providers/live/provider.py`.

## Scraping: DevTools evidence, DOM vs API
The page is an Angular app that loads JSON from `/api/traffic/search` and `/api/traffic/select/{case}` with a short-lived `portal-token`. Decision: Playwright drives the real page and reads the JSON the page itself receives; DOM is only the way to act. No login, no terms gate and no CAPTCHA were seen on `/traffic`. Evidence and screenshots: DECISIONS §1-2, `docs/assets/`, `docs/cap-traffic-integration.md`.

## Data quality: two John Smiths
The search is loose, so results are filtered to the CSV person (same last name, first given name as prefix, equal date of birth when both exist). A case can only be *confirmed* with a date of birth on both sides. Kept cases are grouped into identity groups by (date of birth, licence) and never merged into "the" match. Warrant status is hidden by the portal and shown only as "Restricted by portal".
Code: `app/cases/matching/` (`assessment.py`, `identity.py`, `case_filter.py`).

## AI: what generated, how verified, never-alone decisions
The assistant wrote the code under my direction; I supplied the portal captures, the pacing and the policy decisions. Verified by user stories with acceptance criteria, strict typing and lint, unit and end-to-end tests (real Chromium against the replica), and manual checks. AI is off by default and never decides alone: labels, parsing, filtering and throttling are deterministic; agent output is schema-validated and checked (citations, literal traceability); rule repairs are proven by a canary and are reversible. Not yet verified: a real Anthropic call and a supervised real-portal run (DECISIONS §8-9).

## Live change (likely asks and where to change them)
- Pacing: `CAP_ACTION_DELAY_SECONDS`, `CAP_MAX_ACTIONS_PER_MINUTE` (`app/providers/throttle/`).
- Match rule or label: `app/cases/matching/assessment.py` (+ its test in `tests/cases/`).
- A new CSV rule: `app/csv_import/row_validator.py` (+ `tests/csv_import/`).
- The portal renames a button or JSON key: edit `cap-backend/config/portal_rules.json` or let the rules agent do it (`app/rules/`); show it with `tests/live/test_self_healing.py`.
- A new event type: `app/jobs/events.py`, emit it in `person_processor.py`, render it in `cap-frontend/src/features/report/event-feed.tsx`.

## Hindsight
See DECISIONS §10.

## Before the debrief (author's checklist)
- Run `docker compose up --build` (replica), upload the sample CSV, watch a CAPTCHA appear and solve it with one click in the live view.
- Open `#/rules` and be ready to explain an incident, a canary and a rollback.
- Run `python -m app.tools.live_smoke Pedro Rodriguez --headed` once against the real portal, supervised, so the live claims are first-hand.
