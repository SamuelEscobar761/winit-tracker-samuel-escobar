# California Court Case Tracker

Upload a CSV of drivers, and the app searches the San Bernardino Superior Court traffic portal (`https://cap.sb-court.org/traffic`) for each person in the background, streaming progress to a live dashboard. The default demo needs nothing but Docker.

## Quick start

```bash
cp .env.example .env        # Windows (cmd): copy .env.example .env
docker compose up --build
```

Open <http://localhost:8080> (change `WEB_PORT` in `.env` if the port is taken), drop a CSV and press Start. The default needs no account, no API key and never touches the government site. Stop with `docker compose down`.

## What it is

- **CSV in, report out.** Per-row validation, then one background job per upload. Each person is searched, filtered to the right identity, and every eligible case gets its detail (amount due, charges, payment plan).
- **Live dashboard.** Progress, live feed, sortable table, a drawer showing the parsed case next to the raw portal JSON, and a live view of the worker browsers (needed when a CAPTCHA appears).
- **Three providers behind one interface**, chosen with one variable (`CAP_PROVIDER`): `replica` (default demo: the real Playwright code driving Chromium against a local copy of the portal that answers with recorded real responses), `mock` (same fixtures, no browser, fastest; used by most tests) and `live` (the real portal).
- **Optional Claude agents**, off by default: explain a match, summarise a person's cases, structure free-text notices, and keep the scraper's portal rules up to date by itself (see [AI agents](#ai-agents-why-an-agent-and-where-ai-is-not-used)).

## Architecture overview

```
browser ──► nginx (same origin) ──► FastAPI
              static React app        ├─ REST  /jobs /ai /rules /config /auth
                                      ├─ SSE   /jobs/{id}/events  (replayable, heartbeats)
                                      ├─ WS    /ws/lanes/{n}      (screencast + human input)
                                      └─ engine: FairScheduler → WorkerPool lanes → PersonProcessor
                                                    └─ CapProvider ─ MockCapProvider
                                                                   └─ LiveCapProvider (Playwright)
                                                          reads PortalRules (versioned JSON)
```

- `cap-backend/app/` – `csv_import`, `people` (names, variants), `cases` (parsing, matching), `providers` (mock, live, throttle), `jobs` (engine, events), `api`, `auth`, `live` (screencast), `rules` (versioned portal rules + self-healing), `ai`.
- `cap-frontend/src/` – `features/{upload,job,report,case-detail,scraper,rules,ai,session}`, `shared/`.
- Scraping drives the real page and reads the JSON the page itself receives (details and reasons: [DECISIONS.md](DECISIONS.md) §2 and [docs/cap-traffic-integration.md](docs/cap-traffic-integration.md)).

## Default mode: replica, and the other providers

The default `replica` provider runs real Chromium against a styled local copy of the portal (clearly labelled as a replica) that answers from recorded portal responses. About 8 % of calls fail (expired session, HTTP 503) and about 10 % of searches show a CAPTCHA box, so retries, `failed` people and the human CAPTCHA click in the live view can all be seen.

`CAP_PROVIDER=mock` skips the browser (no Chromium needed, sped up by `MOCK_SPEED_FACTOR`) and the live view then shows a drawn simulation.

Without Docker (Python 3.11, Node 22):

```bash
cd cap-backend && python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"   # Linux/macOS: .venv/bin/pip
.venv/Scripts/uvicorn app.main:create_app --factory --port 8000
cd cap-frontend && npm ci && npm run dev        # http://localhost:5173, proxies to :8000
```

## Live mode

```bash
CAP_PROVIDER=live ADMIN_TOKEN=choose-a-long-secret docker compose up --build
```

- The backend **refuses to start** in live mode without `ADMIN_TOKEN`, and every job, stream and input endpoint then needs the login (`POST /auth/login`, `HttpOnly` cookie). Set `COOKIE_SECURE=true` when serving over HTTPS.
- Pacing: 5 s after every portal action and at most 12 actions per minute per worker (`CAP_ACTION_DELAY_SECONDS`, `CAP_MAX_ACTIONS_PER_MINUTE`). The brief asks for "a few per minute"; lower the second variable if you want to be stricter.
- A first supervised run of one person: `python -m app.tools.live_smoke Pedro Rodriguez --headed --record fixtures_live` (inside `cap-backend`).
- If a CAPTCHA ever appears the job pauses and a person solves it in the live view; the app never solves or bypasses it.
- Only run live mode on a host you control; a public deployment should be mock only.

## Configuration (environment variables)

Full list with defaults: [cap-backend/.env.example](cap-backend/.env.example). Compose reads a root `.env` (see [.env.example](.env.example)).

| Variable | Default | Meaning |
|---|---|---|
| `CAP_PROVIDER` | `mock` (`replica` in Compose) | `replica`, `mock` or `live` |
| `ADMIN_TOKEN` | – | Required for `live` |
| `MAX_WORKERS` | 3 | Browser lanes shared by all jobs |
| `CAP_ACTION_DELAY_SECONDS` / `CAP_MAX_ACTIONS_PER_MINUTE` | 5 / 12 | Pacing per worker |
| `CAP_GLOBAL_MAX_ACTIONS_PER_MINUTE` | unset | Cap across all workers |
| `CAP_MAX_DETAILS_PER_PERSON` | unset | Unset = details for every eligible case |
| `SEARCH_TIMEOUT_SECONDS` / `DETAIL_TIMEOUT_SECONDS` | 60 / 30 | Per call |
| `MAX_RETRIES`, `RETRY_BASE_DELAY_SECONDS` | 3, 2 | Exponential backoff with jitter |
| `CAPTCHA_WAIT_SECONDS` | 300 | How long a person waits for a human |
| `SSE_HEARTBEAT_SECONDS` | 15 | Keeps proxies from closing the stream |
| `CSV_MAX_BYTES`, `CSV_MAX_ROWS` | 2 MB, 1000 | Files over a limit are rejected, not truncated |
| `MOCK_SPEED_FACTOR`, `MOCK_FAILURE_RATE`, `MOCK_SEED` | 10, 0.08, – | Mock realism and reproducibility (speed factor applies to `mock` only) |
| `REPLICA_CAPTCHA_RATE` | 0.1 | Share of replica searches that show a CAPTCHA box |
| `LIVE_HEADLESS`, `LIVE_NO_SANDBOX` | true, false (true in Docker) | Chromium options |
| `CORS_ORIGINS`, `COOKIE_SECURE` | see file | Browser access |
| `AI_ENABLED` | `false` | Master switch for every agent |
| `ANTHROPIC_API_KEY`, `AI_MODEL` | –, `claude-opus-5-5` | Real model |
| `AI_OFFLINE_MOCK` | `false` | Deterministic stand-in for demos and tests |
| `AI_RULES_AUTO_APPLY` | `true` | Activate a canary-verified repair without waiting for a person |
| `AI_RULES_MAX_REPAIRS_PER_HOUR` | 3 | Rate limit for the rules agent |
| `PORTAL_RULES_DIR` | `config` (`/data/rules` in Docker) | Where rule versions and incidents are stored |

## CSV format and validation rules

Header: `first_name,last_name,date_of_birth,external_ref` (the last two optional). Lines starting with `#` and blank lines are ignored. Encodings UTF-8 (with or without BOM) and latin-1; delimiters `,` `;` tab `|`.

Every row gets a status in the report and nothing crashes the import:

- **accepted** – used as is. **normalized** – used after a visible fix (extra spaces, date reformatted). **rejected** – not queued, with the reason; "Download rejected rows" returns them as CSV.
- Rejected: missing first or last name, characters that are not part of a name (`J0hn`), an impossible date (`31/02/1990`), a name the portal cannot search (the query `last, first` must be 4–20 characters), a duplicate (points to the first line).
- Slashed dates are read as MM/DD/YYYY or DD/MM/YYYY only when one reading is impossible; otherwise the row is flagged as ambiguous. Binary files and files over the limits are refused with a clear message.

Matching: the portal search is loose, so results are filtered to the CSV person (same last name, first given name starts with the CSV first name, date of birth equal when both exist). With a date of birth in the CSV a case can be *confirmed*; without it, never. Different people sharing a name are shown as separate identity groups, never merged.

## SSE events and reconnection (Last-Event-ID)

`POST /jobs` returns a `job_id` immediately. `GET /jobs/{id}/events` streams, per job, an append-only log with ids 1, 2, 3…:

`job_created, job_started, searching, waiting, retrying, found, detail_loaded, detail_failed, captcha_required, captcha_resolved, cap_down, cap_recovered, person_completed, person_failed, progress, job_retry, job_complete, job_cancelled`

- Reconnect: `EventSource` resumes with the `Last-Event-ID` header; after a page refresh the app uses `?after=<last id>`. Missed events are replayed in order.
- Heartbeat comments every 15 s and `X-Accel-Buffering: no` keep proxies from buffering or closing the stream; the bundled nginx also disables buffering.
- Events carry counts and ids only; case data is fetched with `GET /jobs/{id}/people/{n}`.

## AI agents: why an agent, and where AI is NOT used

Off by default. With `AI_ENABLED=false` (or no key) the agent endpoints answer `503` and the whole pipeline is identical.

**Where AI is NOT used:** parsing, matching labels, filtering, status and amounts, throttling, retries, warrant handling. The portal answers JSON, so a deterministic parser is more accurate, free and testable.

**Where it is used (all with structured, schema-validated output):**

| Agent | Does | Guard |
|---|---|---|
| Match explainer | Plain-English reasons for a match, what weakens it, next step | The label comes from fixed rules and is never changed |
| Insight | Short summary of a person's cases | Each finding must cite real case keys; amounts must exist in the facts; ungrounded findings are dropped and counted |
| Notice structurer | Free-text notices → kind/date/amount | Excerpts, dates and amounts must appear literally in the source |
| **Rules healer** | When the portal changes (renamed button, input id, API path, JSON key) it proposes a patch to the scraper's rules | See below |

**Self-healing scraper, no developer needed.** Everything that depends on how the portal looks (selectors, API paths, response patterns, JSON field names) lives in versioned data (`PortalRules`), not in code. When a step stops matching the site, the provider records an *incident* with privacy-safe evidence (button labels, element ids, API paths, JSON key names and types; never values or personal data). The agent proposes edits to existing rule keys only (allowlisted patterns, never code), the candidate rules are verified by a real canary search through a throwaway provider, and only then are they activated as a new numbered version (`AI_RULES_AUTO_APPLY=true`) or queued for a person to approve. Every version is kept with who/why/diff/model/canary and can be rolled back from the **Portal rules** screen (`#/rules`). The agent never touches warrant handling, payment controls or throttling.

Try it without a key: `AI_ENABLED=true AI_OFFLINE_MOCK=true`. The offline model repairs by closest-name matching and is what the end-to-end tests use against a page whose button, API path and JSON key were changed.

## Running tests

```bash
cd cap-backend
.venv/Scripts/ruff check . && .venv/Scripts/mypy app tests && .venv/Scripts/python -m pytest
cd ../cap-frontend && npm run lint && npx tsc -b && npm test
```

`tests/live` runs real Chromium against the same replica the `replica` provider uses (`playwright install chromium` once; they are skipped if it is missing). Never against the real portal.

## Deployment strategy

- **Local / evaluation:** `docker compose up --build` (mock). Two services: `backend` (Python + Playwright Chromium, healthcheck on `/health`, rules in the `portal-rules` volume) and `frontend` (nginx serving the build and proxying `/jobs /auth /config /lanes /health /ai /rules /ws` to the backend on one origin with buffering off and long read timeouts).
- **Public demo (mock only):** run the same two containers on any container host (Render, Railway, Fly.io, a VM), behind TLS with `COOKIE_SECURE=true`. A static host for the frontend works only if it proxies the API paths on the same origin; otherwise SSE needs CORS and the session cookie stops being first-party, which is why the compose layout is recommended. Playwright is installed in the image but never launched in mock mode.
- **Live:** one trusted host, `ADMIN_TOKEN` set, HTTPS, low pacing. Not for a public URL.

## Known limitations

- "Filing date" is the portal's violation date; `/traffic` exposes no hearings, court location or disposition.
- Job state and event logs are in memory of one process; a restart loses running jobs. Scaling out would need a queue and a shared event store. Portal rules and incidents are on disk.
- 12 actions/minute/worker is above "a few per minute"; adjustable.
- The first supervised run against the real portal and a real Anthropic call have not been done by the author yet; both paths are covered by tests with fakes and a local portal replica.
- The Docker images were built and run in `replica` mode on Docker 28. Live mode inside the container, and a public deployment, were not exercised.

## Project docs

- [DECISIONS.md](DECISIONS.md)
- [docs/](docs/) – brief, user stories per epic, roadmap, portal technical reference
