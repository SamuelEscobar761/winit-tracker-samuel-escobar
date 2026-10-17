# EP-07 — Deployment & Docker

Brief area: README with `docker compose up` (5%), deployment bonus.

## Epic changelog
| Date | Change |
|---|---|
| 2026-10-15 | Epic created from challenge brief (US-07.1 – US-07.3) |
| 2026-10-15 | US-07.3 amended: live-mode `ADMIN_TOKEN` guard |
| 2026-10-15 | US-07.3 amended again: POST login + HttpOnly session cookie instead of header/query token |
| 2026-10-16 | Step 10: US-07.1 and US-07.3 Done; US-07.2 strategy documented, not deployed |

---

### US-07.1 — docker compose in mock and live mode
**Status:** Done | **Priority:** Must | **Depends on:** US-01.2
**As a** grader **I want** `docker compose up` to run the whole app **so that** I can evaluate it in mock mode with zero setup.

**Acceptance criteria**
- [x] Frontend + backend services; mock is the default; live via env var
- [x] Backend image includes Playwright browser; healthchecks

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief deliverables | Initial setup |
| 2026-10-16 | COMMENT | The backend image needs Playwright's Chromium (`playwright install --with-deps chromium`) and the new variables `CAP_BASE_URL`, `LIVE_HEADLESS`, `LIVE_RESPONSE_TIMEOUT_SECONDS` | Roadmap Step 6 |
| 2026-10-16 | STATUS | Proposed -> Done. docker-compose.yml, cap-backend/Dockerfile (Python + Playwright Chromium, non-root, healthcheck), cap-frontend/Dockerfile + nginx.conf (same origin, SSE buffering off, WebSocket upgrade), .env.example, .dockerignore. Built and run on Docker 28: compose defaults to `replica`; `CAP_PROVIDER=live` needs ADMIN_TOKEN or the backend refuses to start. Live mode inside the container was not exercised against the real portal | Step 10 |

### US-07.2 — Public deployment (mock demo)
**Status:** Proposed | **Priority:** Bonus | **Depends on:** US-07.1
**As a** reviewer **I want** a public URL **so that** I can try the app instantly.

**Acceptance criteria**
- [ ] Frontend on Vercel/Netlify; backend on Render/Railway/DigitalOcean
- [ ] SSE works through proxy (no buffering, heartbeats, timeouts); documented how Playwright was handled

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief bonus | Initial setup |
| 2026-10-16 | COMMENT | Not deployed. Strategy written in README (same two containers on a container host, mock/replica only, TLS, same-origin proxy, SSE settings). Needs an account/URL from the user | Step 10 |

### US-07.3 — Configuration via environment
**Status:** Done | **Priority:** Should | **Depends on:** —
**As an** operator **I want** all knobs in env vars with a documented `.env.example` **so that** deployment is reproducible.

**Acceptance criteria**
- [x] Provider, workers, timeouts, retries, caps, CORS, AI key documented in README
- [x] Live-mode guard: with `CAP_PROVIDER=live` the backend refuses to start unless `ADMIN_TOKEN` is set; all job/stream/input endpoints then require an authenticated session
- [x] Login is `POST /auth/login` with the token in the JSON body (never in a URL/query string); the server answers with a random session id in a `HttpOnly; Secure; SameSite=Strict` cookie (`Secure` relaxed only in local dev over HTTP)
- [x] SSE and the screencast channel authenticate via that cookie; WebSocket handshakes validate `Origin`; state-changing POSTs validate `Origin`
- [x] Frontend and backend are served from the same origin (reverse proxy) so the cookie is first-party

> **Previous (2026-10-15):** all job/stream/input endpoints then require it (header, or cookie/query param for EventSource and the screencast channel).
> Replaced because a token in a GET query string leaks via logs, history and Referer.
- [x] Public demo deployments run mock mode only; README states this

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | Supports reproducibility | Initial setup |
| 2026-10-15 | AMENDED | Added live-mode authentication guard and mock-only public demo | "agrega la autenticacion para el live" |
| 2026-10-15 | AMENDED | Session via POST login + HttpOnly cookie; no token in URLs | "creo que get lo hace publico no?" |
| 2026-10-16 | COMMENT | `.env.example` must include `CAP_ACTION_DELAY_SECONDS` (5), `CAP_MAX_ACTIONS_PER_MINUTE` (12), optional `CAP_GLOBAL_MAX_ACTIONS_PER_MINUTE`, and optional `CAP_MAX_DETAILS_PER_PERSON` (unset = fetch details for all eligible cases, US-01.8) | Throttling requirement |
| 2026-10-16 | COMMENT | `ADMIN_TOKEN` guard is still required, but its reason changes: it is no longer about the CAP account login (not needed on `/traffic`) but about exposing a remote-controlled browser and the server's IP on a public URL | Full review of `/traffic` |
| 2026-10-16 | STATUS | Proposed → In progress (roadmap Step 1: backend scaffold and configuration) | "siguiente" |
| 2026-10-16 | COMMENT | Step 1 partial: typed settings from env with validation, startup refused when `CAP_PROVIDER=live` without `ADMIN_TOKEN` (`cap-backend/app/config/settings.py`), `cap-backend/.env.example`, CORS from `CORS_ORIGINS` (`cap-backend/app/main.py`), tests in `cap-backend/tests/`. Pending: README config table, login/session/Origin checks (Step 7) | Roadmap Step 1 |
| 2026-10-16 | COMMENT | New variables: `MOCK_FIXTURES_DIR`, `MOCK_SPEED_FACTOR` (10), `MOCK_FAILURE_RATE` (0.08), `MOCK_SEED`, `NAME_VARIANTS_FILE`, `CSV_MAX_BYTES`, `CSV_MAX_ROWS` (all in `cap-backend/.env.example`); README config table still pending | Roadmap Step 4 |
| 2026-10-16 | COMMENT | Step 7 auth done in `cap-backend/app/auth/`: `POST /auth/login` (JSON body, constant-time comparison, 5 failures per minute then 429), random 256-bit session id in an `HttpOnly; Secure; SameSite=Strict` cookie (`COOKIE_SECURE=false` only for local HTTP), `POST /auth/logout`, `GET /auth/session`; in live mode every job, SSE and lane endpoint needs the session; state-changing requests and WebSocket handshakes validate `Origin` (configured frontend origins or the same host; live WebSockets require an Origin). Pending: README config table, same-origin reverse proxy (Step 10), the statement that public demos run mock only | Roadmap Step 7 |
| 2026-10-16 | STATUS | In progress -> Done. README config table, root and backend .env.example, nginx same-origin proxy; README states public demos are mock/replica only | Step 10 |
