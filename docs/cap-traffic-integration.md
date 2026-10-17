# CAP `/traffic` integration — technical reference

Everything here was observed manually on 2026-10-16 at `https://cap.sb-court.org/traffic` (evidence in `assets/`). Decisions and trade-offs are in [../DECISIONS.md](../DECISIONS.md); behaviour is specified in the stories (US-01.x, US-06.x). Items marked **Unverified** have not been observed yet.

## 1. Flow (3-step wizard, Angular app)

| Step | Page state | How the scraper gets there |
|---|---|---|
| 1 Search | "CASE PAYMENT SEARCH", 4 buttons: Case Number / Citation Number / Party Name / Business Name. Default selection is **Case Number** | open `/traffic` |
| 2 Select Case | "CASE PAYMENT SEARCH RESULTS", table CASE / NAME / VIOLATION DATE / STATUS | click **Party Name** → type the name in `#number` → click **SEARCH** |
| 3 Select Option | "CASE PAYMENT OPTIONS" for one case | click the row's **Select** (only rows with a Select button: every status except Closed) |
| back to 1 | Party Name is **not** kept selected | click **Search Again** (`button[ng-click="vm.loadSearchView()"]`) |

UI selectors (fallback, JSON is the primary source):
- Party Name button: `form button[3]`, `ng-click` sets `vm.searchForm.type='parn'`
- Input: `#number` (placeholder "Last, First", required, 4–20 chars)
- SEARCH: `button[type=submit]` (disabled while the form is invalid), shows a spinner while running
- Results: `table.table-striped` rows; Select: `button.btn-custom[ng-click^="vm.select("]`
- Empty result: teal toast + banner "No Case(s) Found"; hit: green toast "Found N Case(s)"
- Step 3 panel: `div.panel` with title "CASE PAYMENT OPTIONS"; **never click** its Select controls (payment / extension / ability-to-pay link)

**Position check (generic recovery rule).** After ANY error the provider first determines where the page is: Step 1 visible? Party Name selected? If not, it reselects Party Name and retypes the name before retrying. Reason: the portal drops back to Step 1 on session expiry and Party Name is never retained.

## 2. API calls (same-origin, analytics cookies only, no login)

| Call | Request | Response |
|---|---|---|
| `GET /api/traffic/token` | none | `{"token": "<32 chars>"}` (sent as `portal-token` on the next call) |
| `POST /api/traffic/search` | header `portal-token`; body `{"type":"parn","userMessage":"","value":"<name>"}` (`parn` = Party Name) | `{data:[...], result, created, message}`, ~0.5 s, ~56 kB for 193 results |
| `GET /api/traffic/select/{caseNumber}` | header `portal-token` (different value than for `search`); `caseNumber` with hyphen as in the results table | `{data:{...}, result:0, created, message:"Found Traffic Case <n>"}`, ~4–5 s |
| `GET /api/maintenance` | none | `{"data": false, ...}` — `false` = not in maintenance |
| `GET /api/applicationmode` | none | `"NORMAL"` |

Support calls seen but unused: `key`, `datetime`, `announcement/`, `calendarnodes`, `getappurlfaqinstructionalvideos`, `showtrafficpaymentmenu`.

Token lifetime: **Unverified** (not measured). Expiry is also visible in the API: a call made with a stale token returns HTTP 200 with `result: 1`, `message: "Traffic Payment Session Expired."` and an empty `data` template (fixture `cap-backend/fixtures/pedro_rodriguez.json`, a `select` response). Success is `result: 0`. On expiry the page shows a red toast and banner "Traffic Payment Session Expired. The page will be refreshed in 2 seconds.", reloads and lands on Step 1.

Shape of a "no results" `search` response (empty `data`? non-zero `result`?): **Unverified**.

## 3. Data mapping

### `search` → `data[]` item
| JSON | Meaning | Model |
|---|---|---|
| `caseId` | internal id | `portal_case_id` |
| `caseNumber` | with hyphen, e.g. `25IN-169374`; mixed formats (`MWV25003071`, `CN43133PR`, `5Y7M000F3PR`…) | `case_number` (display) + `case_key` (see §4) |
| `citationNumber` | ticket number | `citation_number` |
| `fileDate` | `m/d/yyyy`; the page labels it VIOLATION DATE | `file_date` ISO 8601 |
| `caseCaption` | `LAST, FIRST MIDDLE…`, sometimes a business or co-party | `caption` |
| `driversLicense` | placeholders seen: `""`, `UNKNOWN`, `UNK`, `NIP`, `NONE`, `A0000000` | `drivers_license` (placeholders → null) |
| `dateOfBirth` | `m/d/yyyy` or `""` | `date_of_birth` ISO or null |
| `caseStatus` | Closed, Active, Inactive, AR Fine, Warrant, Probation, Pending Adjudication, Traffic School Pending | `status` (Warrant → restricted, see US-06.5) |

### `select` → `data` (selection)
| JSON | Model |
|---|---|
| `caseNumber` (no hyphen), `caseId`, `partyId`, `fullName` | identifiers / name |
| `charges[]` (`"VC12500(A)-I: No Operator License"`) | `charges[]` (statute, description) — split on first `": "` |
| `pocChanges[]`, `isPoc`, `pocMessage` | `proof_of_correction_required`, `poc_charges[]` |
| `bfAmount`, `bailOptions[].text/amount` | `amount_due`, `options[]` |
| `hasPaymentPlan` + `paymentPastAmount`, `paymentMonthlyAmount`, … | payment-plan facts, ONLY if `hasPaymentPlan` is true |
| `isExtensionEligible`, `originalDate`, `extendedDate` | extension info |
| `isMa`/`maMessage`, `isInvalid`, `userMessage` | portal notices |
| `paymentTotal`, `paymentMonths`, `paymentDueDates`, `datesAndPayments`, fees | a plan **offer** computed for today when there is no plan: not case data, not stored |

Not available anywhere observed: court location, hearings, disposition, charge severity, case title other than the caption, case type (maybe from the number prefix: unverified).

Real plan case (`select_25IN-169374.json`): `charges` is empty and `pocChanges` has one entry; `paymentTotal` 0, `paymentMonths` 0, no due dates; `bfAmount` 93.00; the remaining balance (186.00) is only the amount of the option coded `PAYF`; option codes: `PPE` (extension, amount 0), `PAYP` (monthly), `PAYF` (pay in full), `PAYC` (custom range, amount text `93.00 - $186.00`); `isExtensionEligible` true with `originalDate`/`extendedDate` and `extensionType` `PLANEXT`.

Step 3 variants: (A) amount + Proof of Corrections box; (B) amount without the box (`isPoc` false); (C) active payment plan (`hasPaymentPlan` true: past amount due, monthly payment, remaining balance, extension option).

### Real sample sizes
- `pedro rodriguez`: 193 cases (`message: "Found 193 Case(s)"`; the total is in `message`).
- `john smith` (`cap-backend/fixtures/jhon_smith.json`): 286 cases → 224 kept by the caption filter (59 other last names, 3 businesses), spread over 118 distinct dates of birth (largest groups: 13 cases each). 65 of the kept cases are eligible for a detail call (statuses Active, AR Fine, Probation, Pending Adjudication, Inactive, Traffic School Pending; not Closed, not Warrant). Without a DOB in the CSV these are many different people (US-06.6).

## 4. Name handling

**Query string.** Always `last, first` (comma form), lower/upper case irrelevant, **accents removed**, total ≤ 20 characters (portal limit; also ≥ 4). Tested on Pedro Rodriguez:

| Input | Result |
|---|---|
| `Pedro Rodriguez`, `pedro rodriguez`, `rodriguez, pedro` | 193 cases |
| `Rodriguez Pedro`, `rodriguez pedro`, `rodríguez pedro`, `Pedro Rodríguez`, `pedro, rodriguez` | No Case(s) Found |

Without a comma the portal reads `First Last`; with a comma `Last, First`; an accent finds nothing.

**Result filtering** (US-06.4). The search is loose. Keep a result only if:
1. caption has a comma (no comma = business → discard);
2. normalized last name (before the comma) equals the CSV last name;
3. the caption's given-name tokens start with the CSV first-name tokens in order (`PEDRO LUIS` ✓ for `Pedro`; middle names ignored);
4. if the CSV has a DOB and the record has one, they are equal.

Normalization: Unicode NFKD, strip accents, uppercase, collapse whitespace. Discarded examples from the real data: `ROMERO, PEDRO RODRIGUEZ` (last name differs), `HERNANDEZ, ABEL LEON` (co-party), `NORCAL WASTE SERVICES INC` (business). Compound surnames and glued middle names (`PEDRO LUISGARZA`) are **unverified** edge cases.

**Name variants** (US-01.9). Compound surnames are unverified, so the provider will try up to `max_attempts_per_person` ordered queries from `cap-backend/config/name_variants.json`: `as_written` (always first), `first_surname_only`, `last_surname_only`, `joined_particles` (`de la cruz` → `delacruz`), `first_given_name_only`. Each attempt costs ≥ 3 paced actions. The result filter accepts the surname/given-name forms of the enabled strategies, and a variant match is never above `probable`. `stop_after_first_with_results` stops at the first attempt that yields kept cases. The `observations` list in the same file is where real examples are recorded (`csv_name`, `query_that_worked`, `caption_seen`, `strategy`, `observed_on`) once a compound-surname case is found, so the final rule can be written from evidence.

**Identity groups** (US-06.6): kept cases are grouped by (DOB, licence); a blank licence joins the only licensed group with the same DOB. Real results: John Smith 224 kept → 119 groups, Pedro Rodriguez 188 kept → 132 groups.

**Case key.** `case_key = uppercase(case_number without "-" and spaces)`; `25IN-169374` (results) and `25IN169374` (Step 3) are the same case.

## 4b. CSV rules (summary)

Implemented in `cap-backend/app/csv_import/`. Header names are matched loosely (`First Name`, `DOB`…); required `first_name`, `last_name`; optional `date_of_birth`, `external_ref`; unknown columns ignored with a warning. Delimiters `,` `;` tab `|` are detected from the header. `#` lines and blank lines are skipped (line numbers are kept). Row issues: empty names, non-letter characters, wrong column count, invalid/ambiguous/out-of-range date, not searchable, duplicate of an earlier line. File issues: empty, binary, too large, too many rows (never truncated), missing/duplicate columns. Dates: ISO always; slashed only when one reading is possible, otherwise rejected as ambiguous.

## 5. Throttling and time budget

Variables (US-01.7, US-07.3):

| Variable | Default | Meaning |
|---|---|---|
| `CAP_ACTION_DELAY_SECONDS` | 5 | wait after every click / request-triggering action |
| `CAP_MAX_ACTIONS_PER_MINUTE` | 12 | sliding-window cap per worker (the brief says "a few per minute per worker": 12 is above that wording, accepted by the user, to be justified) |
| `CAP_GLOBAL_MAX_ACTIONS_PER_MINUTE` | unset | optional cap over all workers (proposed) |

Aggregate load = workers × per-worker cap. Cost per person, minimum (defaults): Party Name click + SEARCH click + one reset action (Search Again / reload) = 3 actions ≈ 15 s. 200 names ≈ 50 min on one worker; 3 workers ≈ 17 min. Each case detail costs up to 4 actions (Party Name, SEARCH, Select, Search Again) ≈ 20 s, plus the ~5 s `select` response, because Search Again returns to Step 1 → see US-01.8 (decided: details for all eligible cases; ≈25 s each, so 20 eligible cases ≈ 8 min for that person).

## 6. Typed errors → behaviour

| Error | Trigger | Behaviour |
|---|---|---|
| `NoResults` | "No Case(s) Found" for a correctly formatted query | person done, 0 cases |
| `SessionExpired` | red toast / back on Step 1, or an API response with `result: 1` and message "Traffic Payment Session Expired." | position check, re-select Party Name, retry same person (a retry, not a failure) |
| `CapDown` | `maintenance.data == true` or `applicationmode != "NORMAL"` | pause job, emit event, do not fail people |
| `Timeout` | no response within the per-person timeout (detail call alone is ~5 s) | retry with backoff, then `failed` |
| `CaptchaRequired` | contingency: none seen so far | pause, human solves in live view (US-01.5) |
| `UnparsedLayout` | unknown Step 3 shape | store raw, flag `detail_unparsed`, continue |

## 6b. Mock provider

`cap-backend/app/providers/mock/` serves the recorded searches listed in `cap-backend/fixtures/mock_catalog.json`. It reads queries like the portal (comma = `last, first`, no comma = `first last`, accents are not folded), models the paced actions (search = 3, detail = 4), simulates latency (search 0.5 s, select 5 s) and failures, and shortens all waits by `MOCK_SPEED_FACTOR`. Details not recorded are built from the recorded layouts with deterministic amounts.

## 6c. Engine and API (summary)

Code: `cap-backend/app/jobs/` (scheduler, worker pool, person processor, retry, portal gate, event log) and `cap-backend/app/api/`.

| Endpoint | Purpose |
|---|---|
| `POST /jobs` (multipart `file`, optional `parallelism`) | validates the CSV, creates the job, answers 201 with `job_id`, `events_url` and the validation report (422 with the report when nothing can be searched) |
| `GET /jobs`, `GET /jobs/{id}` | list and snapshot (state, progress, people) |
| `GET /jobs/{id}/people/{n}` | cases of one person (labels, identity groups, details, discard counts); Warrant appears only as "Restricted by portal" |
| `GET /jobs/{id}/events` | SSE with `Last-Event-ID` or `?after=` |
| `POST /jobs/{id}/cancel`, `/retry-failed`, `/people/{n}/captcha-solved` | job control |

Person states: `queued`, `running`, `done`, `failed`, `blocked_captcha`, `cancelled`. Event types: `job_created`, `job_started`, `searching`, `waiting`, `retrying`, `found`, `detail_loaded`, `detail_failed`, `captcha_required`, `captcha_resolved`, `cap_down`, `cap_recovered`, `person_completed`, `person_failed`, `progress`, `job_retry`, `job_complete`, `job_cancelled`. Every event has `id`, `type`, `job_id`, `timestamp`, `message`, `person_index`, `lane`, `data`.

## 6d. Live provider (Playwright)

Code: `cap-backend/app/providers/live/`. One Chromium session per lane (own cookies), started on first use.

- **Actions** (each paced by the throttle): open the portal (first call of a lane or after losing the form), click Party Name (only if it is not already selected), SEARCH, Select of the result row, Search Again. The first search of a lane therefore costs 4 actions, later ones 3, a detail 4 (5 on the first call).
- **Data** comes from the JSON the page itself receives (`/api/traffic/search`, `/api/traffic/select/{case}`), captured with `expect_response`; the DOM is only used to click and to know where the page is.
- **Safety:** the provider never clicks anything on Step 3 except Search Again, and refuses to open Closed or Warrant cases before clicking.
- **Position check:** before every search it checks whether the search form is visible (waits up to 3 s for an automatic reload), recovers with Search Again or by reopening the portal, and selects Party Name if the button is not selected.
- **Error mapping:** `result != 0` with "No Case(s) Found" or an empty list → `NoResults`; "Session Expired" → `SessionExpired`; no response in `LIVE_RESPONSE_TIMEOUT_SECONDS` → `ProviderTimeout`; reCAPTCHA iframe visible → `CaptchaRequired` (never observed); other Playwright errors → `BrowserError` (retryable); unknown shapes → `UnparsedLayout`.
- **Health:** `check_health` reads `/api/maintenance` (`data: true` = down) and `/api/applicationmode` (anything but `"NORMAL"` = down); connection errors also mean down.
- **Tests:** `cap-backend/tests/live/` runs real Chromium against `tests/support/fake_portal.py`, a local replica with the same buttons, ids and endpoints; they are skipped when Chromium is not installed.
- **Supervised real run:** `python -m app.tools.live_smoke "Pedro" "Rodriguez" --headed --record some_folder` asks for confirmation, searches one person, opens one case and optionally saves the raw JSON.

## 6e. Live view and access control (summary)

Code: `cap-backend/app/live/` (frames, lanes, input, router, mock screen, CDP screencast, page input) and `cap-backend/app/auth/`.

- **Frames:** `WS /ws/lanes/{lane}` sends JSON messages: `{"type":"frame","lane","sequence","width","height","mime_type":"image/jpeg","data":"<base64>"}` and `{"type":"status","lane","job_id","person_index","person_state","awaiting_captcha"}` whenever the lane changes person or starts/stops waiting for a CAPTCHA. Each viewer holds only the newest frame (latest wins). `GET /lanes` lists the lanes.
- **Input** (client to server, same socket): `{"type":"click","x","y"}`, `{"type":"text","text"}`, `{"type":"key","key"}` (Enter, Tab, Backspace, Escape, arrows, space), `{"type":"scroll","delta_y"}`; answered with `{"type":"input","outcome":"ignored|forwarded|captcha_resolved|invalid"}`. Coordinates are in frame pixels. Input is ignored unless the lane's person is waiting for a CAPTCHA.
- **Sources:** live lanes stream Chromium's own screencast (`SCREENCAST_QUALITY`, `SCREENCAST_EVERY_NTH_FRAME`, `SCREENCAST_MAX_WIDTH`); mock lanes stream Pillow-drawn frames of the same size for every step, including a clickable fake CAPTCHA.
- **Access (live mode only):** `POST /auth/login` `{"token"}` -> `204` + `HttpOnly; Secure; SameSite=Strict` session cookie; `POST /auth/logout`; `GET /auth/session` -> `{authentication_required, authenticated}`. Without a session, REST and SSE answer 401 and the WebSocket handshake is closed. State-changing requests and WebSocket handshakes must come from an allowed origin (`CORS_ORIGINS` or the same host); live WebSockets require an Origin. Login is rate limited per client.

## 6f. Frontend (summary)

Code: `cap-frontend/src/` (`features/` upload, session, job, workspace, report, scraper, case-detail; `shared/` api, routing, ui, lib). React 19 + Tailwind 4 + TanStack Table, no router library (hash routes: `#/` upload, `#/job/{id}`, `#/live/{lane}`).

- **Data:** `GET /jobs/{id}` snapshot refreshed (throttled) when relevant SSE events arrive; `EventSource` on `/jobs/{id}/events`; `GET /jobs/{id}/people/{n}` per person (at most 3 in flight, refetched when a person's counters change); raw source through `GET /jobs/{id}/people/{n}/cases/{key}/raw`. New endpoints for the UI: `POST /jobs/validate` (report without creating a job), `GET /config` (provider and limits).
- **Live view:** one WebSocket per worker slot (`/ws/lanes/{lane}`); frames are written straight into an `<img>` (no React state per frame); clicks are scaled to frame pixels and keys are mapped to the allowed input events; input only has effect while the worker waits for a CAPTCHA.
- **Layout:** worker slots = lanes seen in events/people padded to the job's parallelism; 2 panes = one list per side, 4 panes = top `ceil(N/2)` and bottom the rest.
- **Dev:** `npm run dev` proxies `/jobs`, `/auth`, `/config`, `/lanes` and `/ws` to `BACKEND_URL` (default `http://localhost:8000`), so the browser sees one origin (as in production). `npm test` runs the unit tests, `npm run build` the type check and bundle.

## 7. Mock fixtures needed (US-01.3, US-08.1)

`search` JSON for `john smith` and `pedro rodriguez` (real shape above, with the loose matches), an empty result, `select` JSON for variants A/B/C, expired-session sequence, maintenance on/off, and the ~5 s detail latency.

## 8. Open points

- Token lifetime; JSON shape of an empty `search`; behaviour under sustained load (rate limiting, CAPTCHA); whether the Step 3 breadcrumb "Step 2 – Select Case" returns to the results without a new search; compound-surname behaviour.
