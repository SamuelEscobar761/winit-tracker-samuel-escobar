# EP-01 — CAP investigation & scraping providers

Brief area: Scraping & resilience (20%), understanding (25%). Rules of engagement apply (throttle, no CAPTCHA bypass).

## Epic changelog
| Date | Change |
|---|---|
| 2026-10-15 | Epic created from challenge brief (US-01.1 – US-01.6) |
| 2026-10-15 | Comments on US-01.3 and US-01.5 pointing to EP-09 |
| 2026-10-16 | Added US-01.11 (browser-backed mock: local replica of the portal, In progress) |
| 2026-10-16 | Added US-01.10 (portal rules as versioned data, In progress) |
| 2026-10-16 | Added US-01.9 (configurable name-variant attempts, In progress): config in `cap-backend/config/name_variants.json` |
| 2026-10-16 | Name-format tests and Network capture recorded as comments on US-01.1, US-01.4, US-01.6 (JSON API found; DOB available) |
| 2026-10-16 | Step 6: LiveCapProvider implemented and tested on a local portal replica; US-01.2 Done; real-portal run pending (US-01.4 stays In progress) |
| 2026-10-16 | US-01.8 approved: automatic details for all eligible cases |
| 2026-10-16 | US-01.7 defaults amended: 5 s delay, 12 actions/min per worker |
| 2026-10-16 | Added US-01.7 (configurable throttling, Approved) and US-01.8 (detail fetching policy, Proposed); US-01.4 throttle criterion now points to US-01.7; technical reference in docs/cap-traffic-integration.md |
| 2026-10-16 | Full review of all epics against `/traffic` screenshots: comments on US-01.1, US-01.5, US-01.6 (no login, no CAPTCHA seen, comma required in name) |
| 2026-10-16 | Target changed to https://cap.sb-court.org/traffic (Party Name search). Amended US-01.1, US-01.3, US-01.4, US-01.6 |
| 2026-10-16 | US-01.11 Done (browser-backed mock replica) |

---

### US-01.1 — Investigate how CAP loads data
**Status:** Proposed | **Priority:** Must | **Depends on:** —
**As a** developer **I want** to inspect CAP in DevTools (DOM vs JSON API, session/cookie/token, account requirement, CAPTCHA) **so that** the scraper design is based on evidence.

**Acceptance criteria**
- [ ] Findings documented in DECISIONS.md §1–3 with screenshots in docs/assets/
- [ ] Explicit decision: scrape DOM, call internal API, or both, with trade-off
- [ ] Notes on ToS gate, rate limits and whether an account is needed

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief "Investigate before you code" | Initial setup |
| 2026-10-16 | COMMENT | Investigation target is the Traffic portal `https://cap.sb-court.org/traffic` (AngularJS app, `vm.searchForm`), not `/search`. Earlier screenshots/DECISIONS.md §1–3 about `/search` must be redone for `/traffic`; selectors are being supplied incrementally by the user (see US-01.4) | User correction |
| 2026-10-16 | COMMENT | Investigation result: data is fetched as JSON from an internal API (not DOM-only); the JSON carries DOB and driver's licence that the page does not show. Open: request headers/`token` mechanism, case-request response, rate limits. See DECISIONS.md §1–§2 | User Network capture |
| 2026-10-16 | COMMENT | Wording fix: fields such as filing date, hearings, court location, DOB, case type are not VISIBLE in the `/traffic` UI, but the internal JSON may carry more than the DOM renders (e.g. `citationNumber`). Whether they are available is an open point until the Network tab is inspected; case type may be inferable from the case-number prefix. Earlier `/search` findings are discarded as invalid (wrong URL) and removed from DECISIONS.md | User correction |
| 2026-10-16 | COMMENT | Evidence from `/traffic` (screenshots 2026-10-16 in docs/assets): the page is the "CASE PAYMENT" tool (Case Number / Citation Number / Party Name / Business Name) and Party Name search worked WITHOUT login or CAPTCHA, unlike `/search` where DECISIONS.md §1 recorded "LOGIN REQUIRED". Trade-off: no login, but data is limited to what the payment flow exposes (no hearings, courthouse, DOB, filing date). Still open for §2 (graded): whether the SPA loads results from an internal JSON API (Network tab) and what headers/tokens it needs | Full review |

### US-01.2 — Provider interface
**Status:** Done | **Priority:** Must | **Depends on:** —
**As a** developer **I want** a `CapProvider` interface (search by person → case summaries; fetch case detail) **so that** live and mock are interchangeable.

**Acceptance criteria**
- [x] Typed abstract interface; engine depends only on it
- [x] Single env variable selects implementation (e.g. `CAP_PROVIDER=mock|live`)
- [x] Provider errors are typed (CaptchaRequired, CapDown, Timeout, NoResults…)

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief "Mock mode is required" | Initial setup |
| 2026-10-16 | STATUS | Proposed → In progress (roadmap Step 4: provider interface, mock provider, throttle) | "siguiente" |
| 2026-10-16 | COMMENT | Step 4: `CapProvider` (`search`, `fetch_detail`, `check_health`, `aclose`) and typed errors (`NoResults`, `SessionExpired`, `ProviderTimeout`, `CapDown`, `CaptchaRequired`, `DetailNotAvailable`, `UnparsedLayout`, each with a `retryable` flag) in `cap-backend/app/providers/`. `create_provider` (`factory.py`) builds the mock from `CAP_PROVIDER=mock`; `live` raises until Step 6, so the env-variable criterion stays open | Roadmap Step 4 |
| 2026-10-16 | COMMENT | Step 6: `CAP_PROVIDER=live` now builds `LiveCapProvider` (`cap-backend/app/providers/factory.py`); the criterion is met | Roadmap Step 6 |
| 2026-10-16 | STATUS | In progress -> Done (all criteria met) | Roadmap Step 6 |

### US-01.3 — MockCapProvider with recorded fixtures
**Status:** In progress | **Priority:** Must | **Depends on:** US-01.1, US-01.2
**As a** grader **I want** the app to run fully without CAP **so that** the SSE pipeline is demonstrable offline.

**Acceptance criteria**
- [x] Fixtures recorded from the real `/traffic` Party Name search for John Smith (many results) and Pedro Rodriguez (name-order/accent variants; real result table captured 2026-10-16 with ~50+ rows: Active/Closed/Inactive/AR Fine/Warrant statuses, mixed-case names, case-number formats `26IN-055186`, `MWV25003071`, `CN43133PR`…)
- [ ] A "No Case(s) Found" fixture (empty result)
- [x] Realistic latency and configurable random failures (incl. CAPTCHA required, CAP down)
- [x] Deterministic mode (seeded) for tests

> **Previous (2026-10-16):** Fixtures recorded from the real site for John Smith (many results, paginated) and Pedro Rodriguez (name-order/accent variants)

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief | Initial setup |
| 2026-10-16 | AMENDED | Fixtures now come from `/traffic`; results are a single table (no pagination seen), plus empty-result fixture | User correction + pasted DOM |
| 2026-10-15 | COMMENT | Mock must also emit synthetic screencast frames → see US-09.6 | Live workspace request |
| 2026-10-16 | STATUS | Proposed → In progress (roadmap Step 4: provider interface, mock provider, throttle) | "siguiente" |
| 2026-10-16 | COMMENT | Step 4: `MockCapProvider` in `cap-backend/app/providers/`mock/` serves the recorded John Smith (286) and Pedro Rodriguez (193) searches through `fixtures/mock_catalog.json`, reproduces the portal's name rules (comma form, `first last` without comma, accents find nothing), recorded details for 26IN-055186 and 25IN-169374 and deterministic synthetic details for other cases (payment-plan layout for AR Fine). Failures: seeded random (`MOCK_FAILURE_RATE`, `MOCK_SEED`) or scripted; `MOCK_SPEED_FACTOR` (default 10) shortens waits for demos. Open: a recorded "No Case(s) Found" JSON; synthetic frames come in Step 7 | Roadmap Step 4 |
| 2026-10-16 | COMMENT | The in-process mock stays; the browser-backed variant is US-01.11 (`CAP_PROVIDER=replica`) | Realistic mock request |

### US-01.4 — LiveCapProvider (Playwright)
**Status:** In progress | **Priority:** Must | **Depends on:** US-01.1, US-01.2
**As a** user **I want** real searches against cap.sb-court.org **so that** results reflect current court data.

**Acceptance criteria**
- [ ] Reproduces flow on `https://cap.sb-court.org/traffic`: open → click **Party Name** button (`form button[3]`, sets `searchForm.type='parn'`) → type `Last, First` in the input (`#number`, placeholder "Last, First", required, 4–20 chars) → click **SEARCH** (`form button[5]`, `button[type=submit]`, disabled while the form is invalid) → read outcome
- [ ] Outcome detection: `h3 > strong` "No Case(s) Found" ⇒ empty result; otherwise parse results `table.table-striped` with columns CASE | NAME | VIOLATION DATE | STATUS (first column holds a **Select** button for non-Closed cases, or "NO ACTION AVAILABLE" for Closed)
- [ ] Rows with status **Warrant** are rendered hidden (`ng-hide`) unless the user has "Elevated Access": parser must still read the text and flag `hidden_by_portal=true` rather than silently dropping or exposing it as visible
- [ ] Portal is a 3-step wizard: Step 1 Search → Step 2 Select Case (results table) → Step 3 Select Option ("CASE PAYMENT OPTIONS"). Case detail is reached via the row's **Select** button (`vm.select(caseNumber, citationNumber)`); Closed cases have no detail action → summary-only
- [ ] Step 3 is read-only for us: extract amount due and the charge list (statute code + description, e.g. `VC12500(A)-I: No Operator License`) and "Proof of Corrections" notice. The two **Select** buttons on Step 3 are payment / ability-to-pay actions and MUST NEVER be clicked; the scraper returns to Step 1 via **Search Again**
- [ ] Step 3 selectors (container `div.panel[ng-if="vm.viewState==='bailOptions'"]`, title "CASE PAYMENT OPTIONS"): amount due = `<b>` in the first paragraph ("The amount due on this case is $X"); charges = `div.alert-poc li` ("Charge: <statute>: <description>", only when `isPoc`); options table `table.table-striped` with OPTION / ACTION / AMOUNT DUE. Option 1 `button[ng-click="vm.selectOption(opt)"]` is the payment action (never click); option 2 is an `<a>` link to a PDF form (never click). Return to Step 1 with `button[ng-click="vm.loadSearchView()"]` ("Search Again")
- [ ] Data source per field: violation date, case number, name and status come from the **Step 2 table** (Step 3 does not show the violation date). Step 3 adds: header `CASE PAYMENT - <NAME> | <case number without hyphen>` (e.g. `25IN169374` vs `25IN-169374` in Step 2 → normalize case numbers for dedup/matching), amount due, charges, payment plan data
- [ ] Step 3 has 3 observed variants (screenshots in docs/assets):
  - **A. Amount due + Proof of Corrections** (case 1,665.00): paragraph "amount due is $X" + blue `alert-poc` box listing charges; options: pay in full + ability-to-pay link
  - **B. Amount due without the blue box** (`isPoc` false ⇒ no Proof of Corrections required): same layout but `charges = []`, `proof_of_correction_required = false`. Absence of the box is normal, not an error
  - **C. Active payment plan** (`hasPaymentPlan`, case `25IN-169374`, status AR Fine): text "This case has an active payment plan. A past amount of $X is due now. You may request a fee extension"; no amount-due paragraph, no charges; options table: fees-due extension (current → new date), monthly payment ($93.00, due date), pay off remainder ($186.00), custom amount range ($93.00–$186.00), ability-to-pay link. Extract: past_amount_due, monthly_payment, due_date, remaining_balance, option list as read-only info
- [ ] Other variants to tolerate: empty `bailOptions` list, `userMessage` / `errorMessage` banners. Unknown layout ⇒ store raw HTML and flag `detail_unparsed`, do not fail the job
- [ ] **Search Again does NOT keep Party Name selected** (verified by user): before every new search the scraper must click Party Name again and re-type the name
- [ ] No pagination exists: the full result set (observed back to 1991) is in one table, so the scraper reads the whole table at once
- [ ] No terms-of-use gate observed on `/traffic`; CAPTCHA not yet observed (user to report if it appears)
- [ ] **Validated approach (2026-10-16):** Playwright drives the real page and intercepts the JSON responses `POST /api/traffic/search` and `GET /api/traffic/select/{caseNumber}` (`{data, result, created, message}`; `result: 0` = OK); DOM parsing only as fallback; no direct HTTP calls to the API (the page manages the short-lived `portal-token`)
- [ ] **Session expiry:** also detected from the API (`result != 0` with message "Traffic Payment Session Expired."); if the page shows "Traffic Payment Session Expired" (page auto-reloads to Step 1, Party Name deselected) the provider raises a retryable `SessionExpired`, re-selects Party Name and retries the same person
- [ ] **Generic recovery rule (user requirement):** after ANY error (timeout, unexpected response, expired session, failed click), the provider first checks where the page is: if it is back on Step 1 or Party Name is no longer selected, it re-selects Party Name and re-types the name before retrying; only then it applies the retry/backoff policy
- [ ] Request/response shapes used: search body `{"type":"parn","userMessage":"","value":"<first last | last, first>"}`; `GET /api/traffic/token` → `{"token": ...}` sent as header `portal-token` on the next call; `select` data: `charges[]`, `pocChanges[]`, `bfAmount`, `bailOptions[]`, `hasPaymentPlan`, `isPoc`, `caseId`, `partyId`, `fullName`. The `payment*` fields are a payment-plan offer, not case facts, and are only stored when `hasPaymentPlan` is true
- [ ] Health signals before searching: `GET /api/maintenance` (`data:false` = ok) and `GET /api/applicationmode` (`"NORMAL"`); otherwise raise `CapDown`
- [ ] The `select` call takes ~5 s per case: the per-case timeout must allow it, and detail fetching is throttled
- [ ] Waits for SPA render (AngularJS)
- [ ] Stores raw HTML/JSON snapshot + source URL per case
- [x] Throttled per US-01.7 (wait after every action, max actions per minute per worker, both configurable); clean failure identification

> **Previous (2026-10-16):** Throttled (few requests/min per worker); clean failure identification

> **Previous (2026-10-16):** Reproduces flow: open → accept terms → Search → Case Information → name search → results → paginate → case details

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief | Initial setup |
| 2026-10-16 | AMENDED | Flow and selectors replaced by the `/traffic` Party Name flow (button, input, search, empty message, results table). Detail-page selectors still pending | User correction + pasted DOM/XPaths |
| 2026-10-16 | AMENDED | Step 3 DOM captured: selectors for amount, charges, options table, Search Again; payment Select is a button, ability-to-pay Select is a PDF link; variants to tolerate | User pasted HTML |
| 2026-10-16 | AMENDED | Documented 3 Step 3 variants (with/without Proof of Corrections box, active payment plan), data source per field (violation date is in Step 2), case-number format difference with/without hyphen, Search Again resets Party Name | User screenshot + HTML + verification |
| 2026-10-16 | AMENDED | Approach validated by the user: "use A", Playwright + JSON interception, not direct API calls. Added criteria for interception, session expiry (`SessionExpired`, retryable), health endpoints and the ~5 s `select` latency. The Step 2/Step 3 DOM criteria above stay as fallback | "usamos la a… no nos casa directamente solo a la api" |
| 2026-10-16 | AMENDED | Throttle criterion moved to US-01.7 (10 s after each action, max 6/min per worker, configurable) | User requirement |
| 2026-10-16 | COMMENT | Warrant rows: the status is restricted, never shown or used and no detail is fetched (US-06.5, approved); the `hidden_by_portal` criterion above becomes "restricted by portal". Results are filtered to the CSV person before anything else (US-06.4). Technical details in docs/cap-traffic-integration.md | User decisions |
| 2026-10-16 | AMENDED | Added the generic "after any error check Step 1 / Party Name" rule and the concrete request/response shapes (search body, token, select data) | User requirement + Network payloads |
| 2026-10-16 | COMMENT | Network tab shows an internal JSON API (`search` → `{data:[{caseId, caseNumber, citationNumber, fileDate, caseCaption, driversLicense, dateOfBirth, caseStatus}]}`; a per-case request named after the case number for Step 3). PROPOSAL pending validation: Playwright drives the real page and intercepts these JSON responses instead of parsing the DOM (DOM as fallback). Warrant status is in the JSON though the page hides it: whether to expose it is a policy decision pending (see DECISIONS.md §1 Open). Would amend the Step 2/Step 3 criteria above | User Network capture |
| 2026-10-16 | AMENDED | Added Step 3 (payment options page): read amount due + charges only, never click its Select buttons; confirmed no pagination and no terms gate (screenshots in docs/assets) | User screenshots |
| 2026-10-16 | STATUS | Proposed -> In progress (roadmap Step 6: LiveCapProvider with Playwright) | "siguiente" |
| 2026-10-16 | COMMENT | Step 6 implemented in `cap-backend/app/providers/live/`: `provider.py` (flow and error mapping), `portal_page.py` (the only code that touches the page), `page_source.py` (one Chromium session per lane), `health.py` (`/api/maintenance` and `/api/applicationmode`). It drives Party Name, SEARCH, the row's Select and Search Again, reads the JSON the page receives (`/api/traffic/search`, `/api/traffic/select/{case}`), never clicks payment controls, refuses Closed/Warrant details before clicking, re-selects Party Name after any error, maps session expiry / empty result / timeout / CAPTCHA iframe / maintenance to typed errors. Verified with 20 tests against a local replica of the portal (`cap-backend/tests/support/fake_portal.py`) in real Chromium. NOT yet verified against the real portal: the supervised run with `python -m app.tools.live_smoke` is pending, so the flow criteria stay open. First call of a lane costs one extra paced action (opening the page) | Roadmap Step 6 |

### US-01.5 — CAPTCHA handled by human-in-the-loop (no bypass)
**Status:** Done | **Priority:** Must | **Depends on:** US-01.4, US-03.3
**As an** operator **I want** the job to pause with a "CAPTCHA required" event and resume once I solve it **so that** the tool stays within the rules of engagement.

**Acceptance criteria**
- [x] No solving farms/exploits anywhere in code
- [x] CAPTCHA event emitted to SSE; person marked `blocked_captcha` if unsolved within timeout
- [x] Mock provider can simulate CAPTCHA to demo the flow

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief rules of engagement | Initial setup |
| 2026-10-15 | COMMENT | The human solves the CAPTCHA by interacting with the live browser view → see US-09.4 (criteria here unchanged) | Live workspace request |
| 2026-10-16 | COMMENT | No CAPTCHA has appeared on `/traffic` (Party Name search, results, Step 3). Story stays as a contingency (rate limiting may trigger one) and for the mock demo; the page does require cookies ("Cookies are required to process case payments") so the browser context must keep them across Search Again | Full review |
| 2026-10-16 | COMMENT | Step 4 mock side: the mock can raise `CaptchaRequired` (random or scripted). Pausing the job and the human solving it in the live view come in Steps 5 and 7 | Roadmap Step 4 |
| 2026-10-16 | STATUS | Proposed -> In progress (roadmap Step 6: LiveCapProvider with Playwright) | "siguiente" |
| 2026-10-16 | COMMENT | Step 6: the live provider raises `CaptchaRequired` when a reCAPTCHA iframe is visible after an action or when a wait times out with one on screen. Never observed on the real portal, so this detection is unverified | Roadmap Step 6 |
| 2026-10-16 | COMMENT | Step 7: the human solves the CAPTCHA in the live view (US-09.4) and the mock can show and clear a simulated one; no solving service or bypass exists in the code | Roadmap Step 7 |
| 2026-10-16 | STATUS | In progress -> Done (the live detection itself stays unverified until a real CAPTCHA appears) | Roadmap Step 7 |

### US-01.6 — Name search variants and result capping
**Status:** In progress | **Priority:** Should | **Depends on:** US-01.4
**As a** user **I want** searches to handle name order, accents, casing and very common names **so that** matches aren't lost or flooded.

**Acceptance criteria**
- [ ] Query is always formatted `Last, First` (portal input is 4–20 chars; validate length before submitting); tries accent/order variants ("Rodríguez, Pedro") without duplicating cases
- [ ] Portal returns names with middle names/suffixes and mixed case (`RODRIGUEZ, PEDRO LUIS`, `Rodriguez, Pedro`): results are filtered/matched client-side (see US-06.2)
- [ ] Pagination handled only if the portal shows it (none observed on `/traffic`); sensible configurable cap (max N cases per person) with a "truncated" flag
- [ ] Cases deduplicated by case number

> **Previous (2026-10-16):** Tries "Rodriguez Pedro" / "Rodríguez" variants without duplicating cases; Paginates; sensible configurable cap…

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief test data notes | Initial setup |
| 2026-10-16 | AMENDED | Query format, 4–20 char limit, middle-name/case variants and no-pagination observation from `/traffic` | User correction + pasted DOM |
| 2026-10-16 | COMMENT | Name-format tests by the user (Pedro Rodriguez): `Pedro Rodriguez` / `pedro rodriguez` / `rodriguez, pedro` → 193 cases; `Rodriguez Pedro` / `rodriguez pedro` / `rodríguez pedro` / `Pedro Rodríguez` / `pedro, rodriguez` → "No Case(s) Found". This confirms the 153453 screenshot. Rule: without comma the portal reads `First Last`; with comma `Last, First`; accents break the match; case is irrelevant. The brief's "Rodriguez Pedro" must be sent as `rodriguez, pedro`; the provider sends `last, first` without accents. Supersedes the correction row below | User tests |
| 2026-10-16 | COMMENT | CORRECTION of the next row: the claim that `Rodriguez Pedro` without a comma returns nothing is NOT confirmed. The screenshot `153453` shows that text with "No Case(s) Found", but the user reports that the same text returns the full result list. Evidence is contradictory; to be re-tested (see pending validations). Keep the idea that an empty result must not be reported as "no cases" without a sanity check (e.g. retry with the canonical `Last, First` form) | User correction |
| 2026-10-16 | COMMENT | (see correction in the row above) Verified by screenshot: searching `Rodriguez Pedro` (no comma) returns "No Case(s) Found", while `Rodriguez, Pedro` returns results. So the "Rodriguez Pedro" name-order variant of the brief must NOT be sent as-is: the comma is mandatory and an empty result for a wrong format must not be reported as "person has no cases". First names match as prefix (`PEDRO` also returns `PEDRO LUIS`, `PEDRO MOISES`). Open: exact vs prefix last name, accents (`Rodríguez`), last-name-only | Full review + screenshot |
| 2026-10-16 | COMMENT | Compound surnames and multi-word first names are handled by US-01.9 (several ordered attempts from a JSON configuration); the "verify exact vs prefix surname" question stays open until a real case is observed and recorded there | User decision |
| 2026-10-16 | STATUS | Proposed -> In progress (roadmap Step 6: LiveCapProvider with Playwright) | "siguiente" |
| 2026-10-16 | COMMENT | Step 6: empty results are recognised in both possible shapes (`result != 0` with "No Case(s) Found", or `result 0` with an empty list) because the real shape was never captured | Roadmap Step 6 |

### US-01.7 — Human-paced, configurable throttling
**Status:** Done | **Priority:** Must | **Depends on:** US-01.4, US-03.2
**As an** operator **I want** every browser action to wait and the request rate to be capped, both configurable, **so that** the public portal is never hammered.

**Acceptance criteria**
- [x] After every click (and every action that triggers a request) the provider waits `CAP_ACTION_DELAY_SECONDS` (default 5)
- [x] Hard cap `CAP_MAX_ACTIONS_PER_MINUTE` per worker (default 12; note the brief says "no more than a few per minute per worker", so this default is above the brief's wording and must be justified in DECISIONS.md); sliding window; the cap wins if the delay is lowered

> **Previous (2026-10-16):** delay default 10 s, cap default 6 per minute per worker.
- [x] Both are environment variables, validated (delay ≥ 0, cap ≥ 1) and documented in `.env.example` (US-07.3)
- [x] The throttle also applies to retries and to session-expiry recovery clicks
- [x] SSE emits a "waiting/throttled" info event so the UI can show why a person is idle (US-04.2)
- [x] Mock provider simulates the same pacing with a configurable speed-up factor for demos and tests
- [x] (Proposed, not validated) optional global cap `CAP_GLOBAL_MAX_ACTIONS_PER_MINUTE` over all workers, since total load = workers × per-worker cap

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-16 | CREATED | 10 s wait after every click, max 6 per minute as in the PDF, both adjustable variables | "cada click… esperar 10 segundos… no más de 6 por minuto… variable ajustable" |
| 2026-10-16 | AMENDED | Defaults changed: delay 10 s → 5 s, cap 6 → 12 actions per minute per worker (still env variables). 12/min is above the brief's "a few per minute" wording: risk accepted by the user, to be explained in DECISIONS.md | "reduzcamos de 10 segundos a 5… el máximo… 12 por worker" |
| 2026-10-16 | STATUS | Approved → In progress (roadmap Step 1: backend scaffold and configuration) | "siguiente" |
| 2026-10-16 | COMMENT | Step 1 done: variables `CAP_ACTION_DELAY_SECONDS` / `CAP_MAX_ACTIONS_PER_MINUTE` (+ optional global cap) validated in `cap-backend/app/config/settings.py`, listed in `cap-backend/.env.example`, tested in `cap-backend/tests/test_settings.py`. Throttle logic itself comes in Step 4 | Roadmap Step 1 |
| 2026-10-16 | COMMENT | Step 4: throttle in `cap-backend/app/providers/`throttle/` (`SlidingWindowLimiter`, `ActionThrottle.action()` waits after every action, also on failure; optional shared global limiter; `ScaledSleeper` for the mock). Tests with a fake clock prove 12 actions/min and that the cap wins over a short delay. Search = 3 paced actions, detail = 4 (Party Name, SEARCH, Select, Search Again). Pending: the "waiting" SSE event and applying it to retries (Step 5) | Roadmap Step 4 |
| 2026-10-16 | COMMENT | Step 5: every provider action (including retries and recovery) goes through the throttle; each pause emits a `waiting` event with the person and lane (`cap-backend/app/jobs/activity.py`) | Roadmap Step 5 |
| 2026-10-16 | STATUS | In progress -> Done (all criteria met) | Roadmap Step 5 |

### US-01.8 — Case detail fetching policy (time budget)
**Status:** In progress | **Priority:** Should | **Depends on:** US-01.4, US-01.7, US-06.4
**As a** user **I want** details loaded only where they add value **so that** a person with many cases doesn't take an hour.

Context: **Search Again** returns to Step 1 with Party Name deselected, so each detail costs up to 4 actions (Party Name, SEARCH, Select, Search Again) ≈ 20 s at 5 s per action (defaults). The `search` JSON already gives the core fields; the detail adds charges, amount due and payment-plan data.

**Acceptance criteria**
- [x] Details only for kept cases (US-06.4) whose status is neither Closed (no Select available) nor Warrant (restricted, US-06.5)
- [x] **Decided:** details are fetched automatically for ALL eligible cases of the person (no per-person limit by default)
- [x] Optional safety variable `CAP_MAX_DETAILS_PER_PERSON`, unset by default (= all); only if set, the remaining cases offer a "Load details" action in the drawer (US-04.4)
- [x] The case table is filled first from the `search` response; details arrive afterwards as separate SSE events (US-03.4), so the user never waits for them to see the list
- [ ] Progress/ETA accounts for ≈25 s per detail (≈20 s of actions at the defaults + ~5 s `select` response), e.g. 20 eligible cases ≈ 8 min for that person
- [ ] If the Step 3 breadcrumb "Step 2 – Select Case" returns to the results without a new search, use it and cut the cost to ~2 actions per extra detail (to be verified by the user)

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-16 | CREATED | Consequence of 10 s/click pacing and Party Name not being retained; needs the user's decision | Throttling request |
| 2026-10-16 | STATUS | Proposed → Approved. Decision: details for ALL eligible cases, the per-person limit stays only as an optional variable (unset) | "para la us 01 8 es todos" |
| 2026-10-16 | COMMENT | Cost confirmed and accepted: with the real John Smith sample (no DOB) 65 eligible cases ≈ 27 min for that person; the user does NOT want a limit, so `CAP_MAX_DETAILS_PER_PERSON` stays unset (all) | User decision |
| 2026-10-16 | STATUS | Approved → In progress (roadmap Step 5: engine, jobs and SSE) | "siguiente" |
| 2026-10-16 | COMMENT | Step 5: the engine loads details for all eligible kept cases after publishing `found`; each detail arrives as a `detail_loaded` or `detail_failed` event (`cap-backend/app/jobs/person_processor.py`). Pending: ETA in the UI and the "Load details" action when the optional limit is set | Roadmap Step 5 |

### US-01.9 — Configurable name-variant search attempts
**Status:** Done | **Priority:** Should | **Depends on:** US-01.6, US-02.3, US-06.4
**As an** operator **I want** the provider to try several spellings of a person's name, driven by a JSON configuration **so that** compound surnames and similar cases are found, and what worked is kept for later.

Context: nobody has been found yet with a two-word surname, so the portal's behaviour (exact or prefix surname, how the caption is written) is unverified. Instead of guessing one rule, the app tries a few ordered strategies and records the real observations in the configuration once a case appears.

**Acceptance criteria**
- [x] `cap-backend/config/name_variants.json` defines: ordered strategies with an `enabled` flag, `max_attempts_per_person`, `stop_after_first_with_results`, the list of name particles (`DE`, `DEL`, `LA`…), and an `observations` list for real cases
- [x] Strategies: `as_written` (always first), `first_surname_only`, `last_surname_only`, `joined_particles` (`de la cruz` → `delacruz`), `first_given_name_only`
- [x] Queries are generated per person in that order, without duplicates, dropping those outside the portal's 4–20 character limit, up to `max_attempts_per_person`
- [x] The result filter (US-06.4) accepts the surname and given-name forms of the enabled strategies; a case matched through a variant is never above `probable` and states the reason
- [x] An invalid configuration (unknown strategy, `as_written` missing or not first) fails at startup with a clear message
- [x] The engine/provider runs the attempts in order, each one paced by US-01.7, and stops at the first attempt that yields kept cases when `stop_after_first_with_results` is true (Steps 5–6)
- [x] When a non-default strategy is the one that worked, the engine appends it to `observations` (Steps 5–6)

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-16 | CREATED | No compound-surname example could be found to verify the portal's behaviour; try several variants and keep the findings in a JSON configuration | "haz varios intentos y guárdalos en un json de configuración" |
| 2026-10-16 | COMMENT | Domain side done: config `cap-backend/config/name_variants.json` (path via `NAME_VARIANTS_FILE`), loader/validation, attempt generator and accepted name forms in `cap-backend/app/people/variants/`; filter and assessment use them (`cap-backend/app/cases/matching/`); tests `tests/people/test_name_variants.py` and `tests/cases/test_variant_matching.py` (131 tests passing in total). Pending: running the attempts and recording observations in the provider/engine (Steps 5–6) | Roadmap Step 2 |
| 2026-10-16 | COMMENT | Step 5: attempts run in order with early stop (`person_processor.py`) and the winning variant is appended to `observations` by `cap-backend/app/jobs/observations.py` (tested with a synthetic compound-surname catalog) | Roadmap Step 5 |
| 2026-10-16 | STATUS | In progress -> Done | Roadmap Step 5 |

### US-01.10 — Portal rules as versioned data
**Status:** Done | **Priority:** Must | **Depends on:** US-01.4
**As an** operator **I want** everything that depends on how the portal looks (selectors, API paths, response patterns, JSON field names) in a versioned JSON file instead of in code **so that** it can be updated, audited and rolled back without a deployment, including by the rules agent (US-05.5).

**Acceptance criteria**
- [x] `cap-backend/config/portal_rules.json` holds: UI selectors/labels, API paths, success/expired/no-results patterns, health endpoints and the JSON field names of the search and case responses
- [x] The live provider, the page helper, the health check and the parsers read the active rules at run time; changing the active rules takes effect without restarting the server
- [x] Rules are validated on load (schema, safe selectors and paths) and every change creates a new numbered version with the previous ones kept
- [x] Default rules reproduce the behaviour verified so far (all existing live tests keep passing)

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-16 | CREATED | Prerequisite of the self-healing agent: the knowledge about the portal must be data, not code | Step 9 request |
| 2026-10-16 | STATUS | In progress -> Done. Files: cap-backend/app/rules/*, config/portal_rules.json, providers/live/*, cases/parsing/* | Step 9 delivered |

### US-01.11 — Browser-backed mock: a local replica of the portal
**Status:** Done | **Priority:** Should | **Depends on:** US-01.3, US-01.4, US-09.2
**As a** grader or demo user **I want** mock mode to drive a real browser against a good-looking local replica of the portal **so that** the live view, the human CAPTCHA click and the whole Playwright path can be seen without touching the government site.

**Acceptance criteria**
- [x] New provider kind `replica` (one env variable, `CAP_PROVIDER=replica`): the same `LiveCapProvider` and Chromium, pointed at a replica served by the backend itself; nothing reaches `cap.sb-court.org`
- [x] The replica is a polished, self-contained page (no CDN) with the same flow, labels, ids and API paths as `/traffic`, a visible "local replica" ribbon, and answers with the recorded fixtures
- [x] The replica injects failures from `MOCK_FAILURE_RATE` (expired session, HTTP 503, CAPTCHA widget) and the CAPTCHA can be solved by a real click in the live view
- [x] The in-process `mock` provider stays as the fast option for tests and Chromium-less environments; Docker Compose defaults to `replica`
- [x] The test portal in `tests/` is the same replica (one implementation)

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-16 | CREATED | The in-process mock draws a fake screen, so the live view was not a real browser. The brief only requires a mock provider with recorded fixtures; the user asked for a more realistic mock with a nicer page | "el mock lo puedes hacer mas realista? con una pagina mas bonita con tailwind" |
| 2026-10-16 | STATUS | In progress -> Done. Files: cap-backend/app/replica/*, providers/factory.py, config/settings.py, main.py, tests/live/test_replica.py, tests/support/fake_portal.py; verified in Chromium and in Docker (a 188-case job loads details through the replica). Bug found on the way and fixed: an HTTP 5xx from the portal was read as a layout change; it is now a retryable error | Browser-backed mock |

