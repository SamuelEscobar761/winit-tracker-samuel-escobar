# Roadmap — build order

Working plan, not a deliverable. Say **"siguiente"** and the next unchecked step is built, tested and logged. Requirements come from [../challenge-brief.md](../challenge-brief.md); behaviour from the stories in [../user-stories/](../user-stories/README.md); technical facts of the portal from [../cap-traffic-integration.md](../cap-traffic-integration.md); decisions in [../../DECISIONS.md](../../DECISIONS.md).

**Current step:** 11 done except the commit history (the folder is not a git repository) · pending from you: supervised real-portal run, a real Anthropic call, optional public demo

## How each step runs

1. Move the step's stories to `In progress` (history row `STATUS`), asking first only if something contradicts an approved story.
2. Write code and tests together. Stack: Python 3.11 + FastAPI + Playwright (backend, folder `cap-backend/`), React + Tailwind (existing `cap-frontend/`).
3. Run the tests; report failures as they are.
4. Tick the acceptance criteria, set the status, add a history row with the files touched.
5. Tell you what to review and what I need from you (listed per step).

## Proposed backend layout

```
cap-backend/
  pyproject.toml            # deps, ruff, mypy/pyright, pytest
  app/
    config/                 # env settings (US-07.3, US-01.7)
    models.py               # Pydantic: Person, CaseSummary, CaseDetail, Charge, events
    people/                 # Person model, name normalization, query builder
    cases/                  # models, status, keys, parsing/, matching/
    csv_import/             # decoding, header, dates, row validation, duplicates, importer
    providers/
      base.py, errors.py    # CapProvider interface + typed errors
      mock/                 # MockCapProvider, catalog, failures, synthetic details
      throttle/             # sliding-window limiter, action throttle, clocks
      live.py               # LiveCapProvider (Playwright) - Step 6
    engine.py               # jobs, workers, retries, timeouts
    events.py               # per-job append-only log, SSE formatting
    api.py                  # FastAPI routes
    auth.py                 # live-mode session (US-07.3)
    screencast.py           # CDP screencast + input (EP-09)
  fixtures/                 # recorded portal JSON (search, select variants)
  tests/
```

## Steps

### Step 0 — Investigation and documentation ✅
Stories updated for `/traffic`, DECISIONS §1–3/6/7 and the technical reference written, UI mockup exists in `cap-frontend/src/mockup/`.

### Step 1 — Backend scaffold and configuration ✅
- Stories: US-07.3 (config part), US-01.7 (variables), US-08.1 (test setup)
- [x] `cap-backend/` with `pyproject.toml`, FastAPI app factory, `/health`
- [x] `config.py`: typed settings from env (`CAP_PROVIDER`, `MAX_WORKERS`, `CAP_ACTION_DELAY_SECONDS`=5, `CAP_MAX_ACTIONS_PER_MINUTE`=12, `CAP_GLOBAL_MAX_ACTIONS_PER_MINUTE`, `CAP_MAX_DETAILS_PER_PERSON`, timeouts, retries, caps, CORS, `ADMIN_TOKEN`, `ANTHROPIC_API_KEY`), validation, `.env.example`
- [x] Lint/type/test tooling wired (ruff, mypy or pyright, pytest)
- Done when: `pytest` passes and the app starts with defaults.
- Needs from you: nothing.

### Step 2 — Domain models, parsers and name matching ✅
- Stories: US-06.1, US-06.4, US-06.5, US-06.6, US-02.3 (normalization part), US-06.2 (labels)
- [x] Pydantic models from the field mapping in [../cap-traffic-integration.md](../cap-traffic-integration.md) §3 (optional fields, placeholders → null, ISO dates)
- [x] `names.py`: accent folding, `last, first` query builder (≤ 20 chars), `case_key`
- [x] `matching.py`: caption filter (last name equal, first given name prefix, DOB rule), discard counter, Warrant → restricted, identity groups by (DOB, licence), match labels
- [x] `parsers.py`: `search` and `select` JSON → models; unknown shape → `detail_unparsed`
- [x] Tests on the real Pedro Rodriguez sample (kept vs discarded examples)
- Done when: tests pass on the fixtures.
- **Needs from you:** save the full JSON responses as files (DevTools → Network → `search` → Response → copy): `search` for `pedro rodriguez` and `john smith`, and `select` for three cases (amount + Proof of Corrections, amount without it, active payment plan, e.g. `25IN-169374`). Put them in `cap-backend/fixtures/`. The pasted text was truncated by the chat limit, so complete files are needed.

### Step 3 — CSV import and validation ✅
- Stories: US-02.1, US-02.2, US-02.3, (US-02.4 backend part)
- [x] Per-row report: accepted / normalized / rejected with reason; comments and blank lines; delimiter and encoding detection (UTF-8, BOM, latin-1); size/row limits; duplicates
- [x] Rows that cannot be searched (portal limits: 4–20 chars) flagged with a reason
- [x] Tests with the five sample rows of the brief plus encodings and duplicates
- Done when: no malformed file produces a 500.
- Needs from you: nothing.

### Step 4 — Provider interface, Mock provider and throttle ✅
- Stories: US-01.2, US-01.3, US-01.7, (US-01.5 mock side)
- [x] `CapProvider` interface and typed errors: `NoResults`, `SessionExpired`, `CapDown`, `Timeout`, `CaptchaRequired`, `UnparsedLayout`
- [x] `throttle.py`: delay after every action + sliding-window cap, fake-clock tests
- [x] `MockCapProvider` from the fixtures: realistic latency (speed-up factor), random failures (seeded), expired session, maintenance, simulated CAPTCHA, ~5 s detail latency
- Done when: a script can search both test names in mock mode with the pacing applied.
- Needs from you: nothing (uses Step 2 fixtures).

### Step 5 — Engine, jobs and SSE ✅
- Stories: US-03.1 – US-03.6, US-01.8 (engine side), US-02.4 (backend)
- [x] `POST /jobs` (upload + validation report, immediate `job_id`), `GET /jobs/{id}`
- [x] Bounded worker pool, fair scheduling across jobs, per-person timeout, retries with backoff + jitter, position-check hook, graceful shutdown
- [x] Per-job append-only event log; `GET /jobs/{id}/events` SSE with heartbeat, no-buffering headers, `Last-Event-ID` replay
- [x] Details for all eligible cases streamed after the list (US-01.8); cancel and retry-failed (US-03.6)
- [x] Tests: concurrency bound, retry, replay, one failing person does not stop the job
- Done when: the full pipeline runs in mock mode from CSV to `job_complete`.
- Needs from you: nothing.

### Step 6 — LiveCapProvider (Playwright) ✅ (code) / ⏳ (real run)
- Stories: US-01.4, US-01.5 (contingency), US-01.6, US-01.8
- [x] Drive `/traffic`: Party Name → type → SEARCH → intercept `/api/traffic/search`; Select → intercept `/api/traffic/select/{case}`; Search Again; never touch payment controls
- [x] Position check after any error, session-expiry recovery, `maintenance`/`applicationmode` health check
- [x] Throttle applied to every action; raw snapshots stored for kept cases only
- [x] Optional recorder script that saves real responses as fixtures
- **Pending:** one manual live run of one person works end to end (`python -m app.tools.live_smoke Pedro Rodriguez --headed --record fixtures_live`) (you supervise; few requests, respecting the pacing).
- **Needs from you:** be present for the first live run; tell me if a CAPTCHA appears.

### Step 7 — Live view, screencast and access control ✅
- Stories: US-09.2, US-09.4, US-09.6, US-07.3 (auth part)
- [x] CDP `Page.startScreencast` on a separate channel (latest-frame wins), mock frames for mock mode
- [x] Human input forwarded only while `captcha_required`
- [x] Live mode refuses to start without `ADMIN_TOKEN`; `POST /auth/login`, HttpOnly cookie, Origin checks
- Done: the mock live view and the CAPTCHA simulation work; unauthenticated access is refused in live mode (401 on REST/SSE, closed handshake on the WebSocket).
- Needs from you: nothing.

### Step 8 — Frontend (real app) ✅
- Stories: EP-04 (US-04.1 – 04.6), EP-09 (US-09.1, 09.3, 09.5, 09.7 – 09.10)
- [x] Replace the throwaway mockup with real components wired to the API/SSE (`cap-frontend/src/mockup/` stays only as visual reference; final code does not import from it)
- [x] Upload + review of the validation report, job setup (concurrent jobs), split workspace with 2/4 panes, report cards, sortable/filterable table with columns from US-04.3, case drawer (parsed vs raw), designed states (no cases, session expired, CAP down/maintenance, throttled, CAPTCHA), "Restricted by portal" chip, identity groups
- [x] Standalone live-view tab (US-09.9), accessibility and responsive polish
- Done: a mock run is fully usable in the browser (upload, review, workspace, drawer, CAPTCHA, retry, cancel).
- **Needs from you:** review the look and flow in the browser and tell me what to change.

### Step 9 — Claude agents ✅
- Stories: US-05.1 – US-05.4
- [x] Off by default, works without `ANTHROPIC_API_KEY`; Pydantic-validated output with bounded retries; deterministic parser stays primary
- [x] Match explanation and fleet-manager insight citing fields; never overrides hard mismatches; mock agent for tests
- Added: self-healing portal rules (US-05.5, US-01.10): versioned rules, incidents, canary-verified repair, rollback, Portal rules screen.
- Needs from you: an API key only if you want to test it for real.

### Step 10 — Docker, documentation and deployment ✅ (public demo not deployed)
- Stories: US-07.1, US-07.2, US-08.2
- [x] `docker compose up` (frontend + backend with Playwright browser, healthchecks), mock default, live by env
- [x] Root `README.md` (run, config, CSV rules, SSE/reconnect, AI section, tests, deployment, limitations) and the remaining DECISIONS sections (SSE vs WS, concurrency, AI, what AI generated and how it was verified, hindsight)
- [x] Optional public mock demo (Vercel/Netlify + Render/Railway), SSE through the proxy
- Added after review: browser-backed mock (`CAP_PROVIDER=replica`, US-01.11); Compose defaults to it.
- Needs from you: accounts/URLs if you want the public demo.

### Step 11 — Debrief readiness ✅ (commit history pending)
- Stories: US-08.3
- [x] Short answers ([../debrief.md](../debrief.md)) for the brief's debrief questions (transport, concurrency 3×200, failure on the 47th name, DevTools evidence, two John Smiths, AI, live change, hindsight), readable commit history

## PDF requirement → step

| Requirement (brief) | Step |
|---|---|
| Investigate CAP with DevTools, document with screenshots | 0 (DECISIONS §1–3) |
| Provider interface, Live + Mock, one env variable | 4, 6 |
| Mock fixtures from the real site for John Smith and Pedro Rodriguez, latency, random failures | 2 (fixtures), 4 |
| Respect the portal: throttle, no CAPTCHA bypass, human-in-the-loop | 4, 6, 7 |
| Feature 1: CSV import, per-row report, never crash | 3 |
| Feature 2: background jobs, `job_id`, bounded workers, retries, timeouts, SSE, `Last-Event-ID` | 5 |
| Feature 3 (optional): Claude agents | 9 |
| Feature 4: dashboard, live feed, table, drawer, designed states | 8 |
| Data to extract (case number, dates, status, parties, charges, source metadata) | 2 (what the portal exposes; no hearings/location available) |
| Homonyms (two John Smiths) | 2 (US-06.4/06.6) |
| Tests on parser and CSV validator | 2, 3, 5 |
| README with `docker compose up`, DECISIONS.md | 10 |
| Bonus deployment | 10 |
| Live debrief | 11 |

## Known gaps versus the brief (documented in DECISIONS.md)

- Filing date is the portal's "violation date"; hearings, court location and disposition are not exposed by `/traffic`.
- No terms-of-service gate or CAPTCHA was seen on `/traffic` (contingency kept).
- Throttle default (12 actions/min per worker) is above the brief's "a few per minute"; configurable.
