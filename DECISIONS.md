# DECISIONS

<!-- Deliverable: CAP investigation, architecture choices (SSE, AI agents), what AI generated. One page is enough. Each decision: context, choice, trade-off accepted. -->

## 1. CAP investigation (DevTools)

Target: `https://cap.sb-court.org/traffic`. Full technical reference (flow, API, field mapping, name rules, throttling, errors): [docs/cap-traffic-integration.md](docs/cap-traffic-integration.md). Everything below was observed manually in the browser on 2026-10-16 (screenshots in `docs/assets/`). Items marked **Open** are not verified yet and are not stated as facts.

**What the page is.** A client-side Angular app (`ng-*` bindings, `vm.*` controller) called "CASE PAYMENT", a 3-step wizard: Step 1 Search → Step 2 Select Case → Step 3 Select Option. Step 1 offers four search types: Case Number, Citation Number, Party Name, Business Name ([default state](docs/assets/Captura%20de%20pantalla%202026-10-16%20152635.png)).

**Party Name search**
- Select the *Party Name* button, type `Last, First` in the input (placeholder "Last, First", required, 4–20 characters), press SEARCH ([form](docs/assets/Captura%20de%20pantalla%202026-10-16%20153258.png)).
- No login, no terms-of-service gate and no CAPTCHA appeared at any step. The page only states that cookies are required.
- **Name format** (tested on Pedro Rodriguez, case-insensitive):

  | Input | Result |
  |---|---|
  | `Pedro Rodriguez`, `pedro rodriguez` | 193 cases |
  | `rodriguez, pedro` | 193 cases |
  | `Rodriguez Pedro`, `rodriguez pedro`, `rodríguez pedro` | No Case(s) Found |
  | `Pedro Rodríguez` | No Case(s) Found |
  | `pedro, rodriguez` | No Case(s) Found |

  Reading: with a comma the text is `Last, First`; without a comma the portal reads `First Last`, so "Rodriguez Pedro" is taken as first name Rodriguez, last name Pedro. An accented letter finds nothing (records appear to be stored without accents). The scraper therefore sends `last, first` with accents stripped.
- Outcomes: the button shows a spinner while searching; a hit shows a green toast "Found 193 Case(s)"; no hit shows a teal toast and an in-page banner "No Case(s) Found" ([screenshot](docs/assets/Captura%20de%20pantalla%202026-10-16%20153453.png)).
- **Step 2, results** ([top](docs/assets/Captura%20de%20pantalla%202026-10-16%20153539.png), [end](docs/assets/Captura%20de%20pantalla%202026-10-16%20154342.png)): one table with CASE | NAME | VIOLATION DATE | STATUS, no pagination (one table down to 1991 for "Pedro Rodriguez"). Names include middle names (`RODRIGUEZ, PEDRO LUIS`), so the first name matches as a prefix. Statuses seen: Active, Closed, Inactive, AR Fine. Rows with status Warrant are rendered with the status hidden (`ng-hide`) and still have a Select button. Closed rows show "NO ACTION AVAILABLE" instead of Select.
- **Step 3, case payment options** (opened with the row's Select): shows a green toast "Found Traffic Case 26IN-055186" and a header `<NAME> | 26IN055186` (case number without hyphen). Three layouts seen:
  - amount due + "Proof of Corrections" box listing charges ([screenshot](docs/assets/Captura%20de%20pantalla%202026-10-16%20153729.png), [scrolled](docs/assets/Captura%20de%20pantalla%202026-10-16%20154431.png));
  - amount due without that box (not required for that case);
  - active payment plan: past amount due, monthly payment, remaining balance, extension option ([screenshot](docs/assets/Captura%20de%20pantalla%202026-10-16%20155411.png)).
- **Search Again** returns to Step 1 and does NOT keep Party Name selected.

**Decision on safety:** the scraper only reads Step 3. The options' *Select* controls (pay, extend, ability-to-pay form link) are payment actions and are never clicked.

**Internal API (Network tab, Fetch/XHR).** The app loads data as JSON: `search` (≈56 kB for 193 results, ~0.5 s), a request named after the case number (e.g. `26IN-055186`, ~2.6 kB, ~3.7 s) when a case is selected, and support calls (`token` repeated before requests, `key`, `datetime`, `maintenance`, `applicationmode`, `announcement/`, `calendarnodes`, `showtrafficpaymentmenu`). The `search` response is `{"data": [...]}` and each item has `caseId, caseNumber, citationNumber, fileDate, caseCaption, driversLicense, dateOfBirth, caseStatus`.

What the JSON has that the page does not show: `dateOfBirth`, `driversLicense`, and the real `caseStatus` of Warrant cases (the page blanks it, `vm.hasAccess('Elevated Access')`). The page column "VIOLATION DATE" is `fileDate`. Statuses seen: Closed, Active, AR Fine, Warrant, Probation, Pending Adjudication.

The search is loose: results include captions that only contain the words (`ROMERO, PEDRO RODRIGUEZ`), co-party or unrelated captions (`HERNANDEZ, ABEL LEON`, a company), so results must be filtered client-side.

**Data available:** case number, citation number, file date (shown as violation date), caption, DOB, driver's licence, status (search JSON); amount due, charges, payment plan (case request / Step 3). **Not seen anywhere yet:** court location, hearings, disposition, case type (maybe inferable from the case-number prefix, unverified).

**API calls** ([Network list](docs/assets/network-fetch-xhr.png)). All are same-origin requests to `cap.sb-court.org` with only analytics cookies (no login cookie).

| Call | Detail |
|---|---|
| `GET /api/traffic/token` | `{"token": "<32 chars>"}`, called before each action; the returned value is sent next as the request header `portal-token` |
| `POST /api/traffic/search` | body `{"type":"parn","userMessage":"","value":"pedro rodriguez"}` (`parn` = Party Name) + `portal-token`; response `{data:[...]}`, ~0.5 s |
| `GET /api/traffic/select/{caseNumber}` | `portal-token` (a different value than the one used by `search`); response `{data:{...}, result:0, created, message:"Found Traffic Case <n>"}`; takes ~4–5 s |
| `GET /api/maintenance` | `{"data": false, "result": 0, ...}`; `false` = not in maintenance |
| `GET /api/applicationmode` | `"NORMAL"` |

**Session expiry.** The token is short-lived: after some time the page shows a red toast and banner "Traffic Payment Session Expired. The page will be refreshed in 2 seconds.", reloads, and returns to Step 1 with Party Name deselected ([screenshot](docs/assets/session-expired.png)). The scraper must detect this, reload, re-select Party Name and retry the same person.

**`select` response (`data`).** Case facts: `caseNumber` (no hyphen), `caseId`, `partyId`, `fullName`, `charges[]` (statute + description; richer than the page: the Step 3 box lists only the 3 `pocChanges`, `charges` had a 4th, `VC40508(A)-I: Violation of Promise to Appear`), `bfAmount` (amount due), `bailOptions[]` (`text`, `amount`), `isPoc`/`pocMessage`, `hasPaymentPlan`, `isMa`/`maMessage`, `isInvalid`, `userMessage`, `isExtensionEligible`, `originalDate`/`extendedDate`. The `payment*` fields (`paymentTotal`, `paymentMonths`, `paymentDueDates`, `datesAndPayments`, fees) describe a payment-plan *offer* computed for today when the case has no plan (here: 10 × $170 starting on the request date), not a fact about the case; they are only meaningful when `hasPaymentPlan` is true. Still no court location or hearings anywhere.

**Open**
- How long a token lives (not measured; covered by the generic recovery rule in §6).
- Rate limit, CAPTCHA under load, behaviour without prior cookies.
- JSON shape of an empty `search`; whether the Step 3 breadcrumb returns to Step 2 without a new search (US-01.8).

**Decided: Warrant.** The page hides Warrant status; the JSON carries it. The brief says "capture every field CAP shows" and says nothing about hidden fields. Decision (2026-10-16): treat it as restricted, never show or use it, fetch no detail for those cases (US-06.5).

## 2. Scraping approach (DOM vs internal API vs both)

Finding: the data arrives as JSON from an internal API, not as server-rendered HTML (§1).

**Decision (validated 2026-10-16): both, with the browser as the driver.** Playwright operates the real page (select Party Name, type, SEARCH, Select) and the scraper reads the JSON responses it triggers (`page.on("response")`), using the DOM only as fallback. Reason: the page itself obtains and refreshes the short-lived `portal-token`, the flow stays at human pace, the live screencast shows a real browser, and the JSON gives typed fields (incl. DOB). Calling the API directly with an HTTP client is NOT done: it would need to fetch and rotate `portal-token` by hand and would skip the page flow. Trade-off accepted: heavier than raw HTTP (a browser context per worker) and slower per case (the `select` call takes ~5 s).

Implemented in `cap-backend/app/providers/live/` and tested in real Chromium against a local replica of the portal; the first supervised run against the real portal is still pending.

## 3. CAPTCHA and rate limits (human-in-the-loop / mock)

No CAPTCHA was seen on `/traffic`. Pacing: every click waits `CAP_ACTION_DELAY_SECONDS` (5) and each worker is capped at `CAP_MAX_ACTIONS_PER_MINUTE` (12), both configurable (US-01.7); with Party Name not retained after Search Again a person costs ≈15 s minimum and each case detail up to ≈20 s. Trade-off accepted: 12 per minute is above the brief's "no more than a few per minute per worker"; chosen to keep runs practical, adjustable down with one variable. Policy regardless: never solve or bypass a CAPTCHA; if one appears the job pauses with a "CAPTCHA required" event and a human solves it in the live view (US-01.5, US-09.4); the mock provider simulates it.

## 4. Transport: SSE vs WebSockets vs polling

- **Decision:** Server-Sent Events, one stream per job (`GET /jobs/{id}/events`). Updates only flow server to client; everything the user sends (upload, cancel, retry, CAPTCHA solved) is a normal REST call, so a bidirectional channel adds nothing. `EventSource` reconnects by itself and sends `Last-Event-ID`.
- **Rejected:** polling (latency or constant load, and no ordered replay) and WebSockets (extra protocol, manual reconnect/replay) for the event feed. The browser screencast is different (large lossy frames) and gets its own channel (roadmap Step 7).
- **What breaks SSE behind a proxy and what prevents it:** response buffering (`X-Accel-Buffering: no`, `Cache-Control: no-cache`) and idle timeouts (a `: heartbeat` comment every `SSE_HEARTBEAT_SECONDS`, 15 s by default).
- **Reconnection:** each job has an append-only log with ids 1, 2, 3…; a client resumes after the last id it saw (`Last-Event-ID` header, or `?after=` after a page refresh). The stream ends when the job is closed (completed or cancelled); `retry-failed` reopens it.
- **Trade-off accepted:** logs and job state live in memory of one process, so a server restart loses them. Events are small (counts and ids); the data itself is read through REST (`GET /jobs/{id}/people/{n}`).

## 5. Concurrency model (bounded workers, retries, timeouts)

- **Workers:** `MAX_WORKERS` long-lived workers (lanes), each with its own provider session, shared by every job. A `FairScheduler` hands out people round-robin across jobs, so one big upload cannot starve another; a job's own `parallelism` (chosen by the user, clamped by the server) caps how many lanes serve it.
- **Pacing:** every portal action waits `CAP_ACTION_DELAY_SECONDS` (5) afterwards and each worker is capped at `CAP_MAX_ACTIONS_PER_MINUTE` (12); an optional global cap bounds the sum of all workers. A search is 3 actions and a case detail 4, so a person costs about 15 s plus 20-25 s per detail.
- **Three users upload 200 names at once:** 600 people queue immediately (the three `POST /jobs` return a `job_id` and the validation report at once). With 3 workers the scheduler alternates between the three jobs; each person takes at least about 15 s, so the minimum is roughly 600 x 15 s / 3 = 50 min before details. The UI shows progress per job from the SSE events, and nothing blocks the HTTP server because all portal work runs in the workers.
- **Retries and timeouts:** only retryable errors (session expired, timeout) are retried, with exponential backoff and jitter, up to `MAX_RETRIES`; each search and each detail call has its own timeout. A person that still fails ends as `failed` with the reason and the job continues.
- **Not retried blindly:** portal down (all workers pause, people are re-queued, a health check reopens the gate) and CAPTCHA (the person waits for a human up to `CAPTCHA_WAIT_SECONDS`, then `blocked_captcha`).
- **Shutdown:** stopping the application cancels the workers and the recovery task, so no task is left hanging.
- **Trade-off accepted:** a single process with in-memory state; scaling out would need an external queue and a shared event store.

## 6. Failure handling (CAP error on name N)

- **After ANY error, check position first:** is the page back on Step 1 and is Party Name still selected? If not, re-select Party Name (and re-type) before retrying. This is the general recovery rule; the cases below are specific triggers.
- **Session expired** (red toast "Traffic Payment Session Expired", page reloads to Step 1): retryable; reload, re-select Party Name, retry the same person.
- **CAP down / maintenance:** `GET /api/maintenance` → `data:true` or `GET /api/applicationmode` ≠ `"NORMAL"` pauses new searches and emits a "CAP down" event instead of failing people one by one.
- **Empty result:** only "No Case(s) Found" with a correctly formatted query counts as "no cases"; a name that cannot be formatted is rejected before searching (US-02.3).
- One failing person never stops the job: state `failed` with reason, the job continues.
- **The 47th name fails (portal error page):** the user sees `retrying` events, then, if retries run out, `person_failed` with the reason and the progress bar moves on; failed or blocked people can be re-run with `retry-failed` without repeating the finished ones.

## 7. Data quality (homonyms, name order, accents)

- The `search` JSON includes `dateOfBirth`. With a DOB in the CSV: equal DOB + matching name → strong match; different DOB → excluded/"unlikely" with the reason. Without a DOB in the CSV (or in the record) a case is only a candidate, never "confirmed".
- The search is loose and returns middle-name variants plus unrelated or co-party captions. Decision (US-06.4): results are filtered to the CSV person (last name equal, first given name starting with the CSV first name, DOB equal when both exist) and the rest is discarded, not stored and not shown; only a "N discarded" counter remains. Grouping the kept cases by DOB/licence into possible identities is proposed (US-06.6).
- Names are searched without accents; the display form is preserved.
- Case numbers appear with and without hyphen (`25IN-169374` vs `25IN169374`): the dedup key strips hyphens/spaces and uppercases; the displayed form is preserved.

## 8. AI agents (what, why, where not)

- **Context.** The portal answers JSON, so parsing, filtering, match labels, statuses and amounts are deterministic code: free, testable and exact. An LLM there would add cost, latency and error.
- **Choice: AI only where judgement or text is involved, off by default** (`AI_ENABLED=false`; with it off, the agent endpoints answer 503 and the pipeline is identical). Every agent uses schema-validated structured output and is checked by code afterwards:
  - *Match explainer:* explains the deterministic label; the label is never taken from the model.
  - *Insight:* findings must cite real case keys and may only contain dollar amounts present in the facts; ungrounded findings are dropped and counted.
  - *Notice structurer:* free-text notices to kind/date/amount; every excerpt, date and amount must appear literally in the source.
  - *Rules healer (US-05.5):* the knowledge about the portal (selectors, API paths, response patterns, JSON field names) is versioned data, not code. When a step stops matching, an incident with privacy-safe evidence (labels, ids, paths, JSON key names and types; no values) goes to the model, which proposes edits to existing rule keys only. The patch is validated against allowlists (no code, no foreign hosts), proven by a canary search with a throwaway provider, then activated as a new numbered version or queued for approval. Every version keeps who/why/diff/model/canary and can be rolled back.
- **Defaults I chose, to be reviewed:** auto-apply of a verified repair is on when AI is on (`AI_RULES_AUTO_APPLY`); repairs are rate limited (3/hour); the agent cannot touch warrant handling, payment controls or throttling because those are not rule keys.
- **Privacy:** the explainer receives names and dates of birth of the CSV person and the case caption; driver's licence numbers are never sent. The healer sends no portal values at all.
- **Trade-offs accepted:** a canary search spends a few portal actions (throttled like any other); a wrong-but-passing repair is possible, which is why every change is logged and reversible; the offline mock model repairs by closest-name matching and is not a stand-in for model quality.
- **Not verified:** the call to the Anthropic API itself (no key was available while building). It is covered with fakes and the offline model; run once with a real key before relying on it.

## 9. What AI generated and how I verified it

- **Generated with Claude Code (the whole codebase):** backend, frontend, tests, Dockerfiles and docs were written by the assistant under my direction, step by step from the roadmap in `docs/roadmap/`.
- **What came from me, not the AI:** the target (`/traffic`), the DevTools captures and recorded responses, the pacing numbers (5 s, 12 per minute), the Warrant, identity-grouping and name-variant decisions, and the corrections whenever the assistant assumed something the portal does not do.
- **How it was verified:** every change is tied to a user story with acceptance criteria and a history; strict typing (mypy) and lint (ruff, eslint); unit tests on parsers, CSV validator, throttling, engine and API; end-to-end tests that drive real Chromium against a local replica of the portal, including drifted pages for the rules healer; manual browser checks of the UI with screenshots.
- **Not verified by me yet:** a supervised run against the real portal, and a real Anthropic call (see §8). Anything that depends on those is marked as such in the stories.

## 10. Hindsight (what I would rebuild first)

- Record the real portal fixtures and decide the mock shape (in-process or browser-backed replica) before building the live view: the first mock drew a fake screen, and a browser-backed replica was needed afterwards to make the live view and the CAPTCHA click honest.
- Put the portal knowledge in versioned data from day one; it was hard-coded first and had to be extracted for the rules agent.
- Persist jobs and event logs (SQLite) from the start; in-memory state is the main scaling and restart limit.
- Keep one test portal implementation and use it for tests and demos (it now is the replica).

## 11. Where scraping runs and live-mode access control

- **Decision:** scraping runs on the server (Playwright workers behind FastAPI); the user's browser only receives events (SSE) and screencast frames. Alternative rejected: scraping from the client (CORS, no background jobs, no worker pool).
- **Consequence:** in live mode, requests to CAP come from the server's IP, and the live view lets a person click and type in a real browser on the server.
- **Decision:** live mode requires authentication. The backend refuses to start with `CAP_PROVIDER=live` unless `ADMIN_TOKEN` is set; job, stream and input endpoints then require an authenticated session. Mock mode needs no authentication.
- **Token transport:** `POST /auth/login` with the token in the body; the server sets a random session id in a `HttpOnly; Secure; SameSite=Strict` cookie. Never in a URL: a GET query string leaks via server/proxy logs, browser history and `Referer`. `EventSource` and the screencast channel send the cookie automatically; WebSocket handshakes and state-changing POSTs validate `Origin`. Frontend and backend share one origin behind a reverse proxy so the cookie stays first-party.
- **Public demo:** mock mode only, so nothing reaches CAP and no remote browser is exposed.
- **Implemented (Step 7):** the cookie session, login rate limit, `Origin` checks for state-changing requests and WebSocket handshakes, and the live-view channel are in `cap-backend/app/auth/` and `cap-backend/app/live/`. The screencast travels on its own WebSocket (JSON with base64 JPEG, newest frame wins per viewer), never on the replayable event log.
- **Trade-off accepted:** a single shared token, not per-user accounts. Enough to stop anonymous use of a public instance; not a multi-tenant security model.
- Stories: US-09.4, US-07.3.

## 12. Mock modes: in-process mock vs browser-backed replica

- **Context.** The brief requires a `MockCapProvider` with fixtures recorded from the real site, latency and random failures, and graders run mock mode without CAP.
- **Choice.** Three providers behind the same interface. `mock` answers in process (fast, used by most tests). `replica` runs the real `LiveCapProvider` and Chromium against a styled local copy of the portal served by the backend (`app/replica/`), answering from the same fixtures; it injects expired sessions, HTTP 503 and a CAPTCHA box, so the live view and the human click are real. `live` is the real portal. The replica page says it is a replica and has no CDN dependencies.
- **Trade-off accepted:** the replica needs Chromium (already in the Docker image) and runs at real pacing; it is a copy of what was observed, not the portal itself, so it can drift from it. Compose defaults to `replica`.

