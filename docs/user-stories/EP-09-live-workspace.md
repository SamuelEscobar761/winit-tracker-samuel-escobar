# EP-09 — Live workspace (split view: live scraping + live report)

Not in the original brief; added at the user's request. Extends EP-01 (CAPTCHA), EP-03 (stream), EP-04 (report UI). Validated decisions: screencast via CDP (not noVNC / not screenshots only); dedicated epic.

## Epic changelog
| Date | Change |
|---|---|
| 2026-10-15 | Epic created (US-09.1 – US-09.6); cross-reference comments added to US-01.3, US-01.5, EP-03, EP-04 |
| 2026-10-16 | Step 7: US-09.4 and US-09.6 Done; US-09.2 backend done (open: behaviour behind a proxy) |
| 2026-10-15 | Added US-09.7–US-09.10 (2/4 layout, id badge, 3-dots pop-out, concurrent jobs input); US-09.1 amended (sides swapped), US-09.3 commented |
| 2026-10-15 | US-09.7 amended (panes are scrollable lists; 4 panes = 2 lists per side); US-09.10 open question closed; US-09.3 commented |
| 2026-10-15 | US-09.7 amended again: top lists get ceil(N/2) jobs, bottom lists the rest |
| 2026-10-15 | US-09.4 amended: live mode requires authentication (`ADMIN_TOKEN`) |
| 2026-10-15 | Clickable UI mockup (fake data, no backend) added in `cap-frontend/src/mockup/`, entry `cap-frontend/mockup.html`; illustrates US-09.1, 09.3, 09.5, 09.7–09.10 and US-04.1–04.5. No story changed |

---

### US-09.1 — 50/50 split-view workspace
**Status:** Done | **Priority:** Must | **Depends on:** US-04.1
**As a** user **I want** one browser page split in two halves, each with its own independent `overflow-auto` **so that** I can watch the scraping and read the report at the same time.

**Acceptance criteria**
- [x] Left half: live report panel (US-09.5); right half: live scraping panel (US-09.3)
- [x] Each pane scrolls independently (`overflow-auto`); page itself does not scroll
- [x] Layout degrades to stacked/tabbed on narrow screens
- [x] Layout can be 2 or 4 panes, see US-09.7

> **Previous (2026-10-15):** Left half: live scraping panel (US-09.3); right half: live report panel (US-09.5).
> Replaced because the user's later example places reports on the left and scrapers on the right.

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | User asked for half-and-half layout with overflow-auto on each | "ver los jobs en una mitad y el reporte en la otra" |
| 2026-10-15 | AMENDED | Sides swapped (reports left, scrapers right) and 2/4 layout added | "2 reportes a la izquierda y 2 scrappers a la derecha" |
| 2026-10-16 | STATUS | Approved -> In progress (roadmap Step 8: frontend) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented in `cap-frontend/src/features/workspace/workspace.tsx`: reports on the left, live scraping on the right, each pane scrolls on its own, the page does not scroll, one column below the `lg` breakpoint, 2 or 4 panes | Roadmap Step 8 |
| 2026-10-16 | STATUS | In progress -> Done (verified in the browser against the mock backend; 47 unit tests) | Roadmap Step 8 |

### US-09.2 — Browser screencast stream (backend)
**Status:** In progress | **Priority:** Must | **Depends on:** US-01.4, US-03.1
**As a** system **I want** to stream frames of each Playwright session via CDP `Page.startScreencast` **so that** the UI can show the real scraping live.

**Acceptance criteria**
- [x] Separate channel from the event SSE (frames are large/lossy; events must stay replayable per US-03.5)
- [x] Frame rate/quality configurable; frames dropped under backpressure (latest wins)
- [x] Per-job/worker session identification; stream ends cleanly when the job ends
- [ ] Works through the proxy (no buffering, heartbeats)

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | Validated approach: CDP screencast | AskUserQuestion answer |
| 2026-10-16 | STATUS | Approved -> In progress (roadmap Step 7: live view, screencast and access control) | "siguiente" |
| 2026-10-16 | COMMENT | Step 7: frames travel on `WS /ws/lanes/{lane}` as JSON messages (`type: frame`, base64 JPEG, `sequence`, `width`, `height`) separate from the event SSE; a `status` message says which job/person the lane serves and whether it waits for a CAPTCHA; `GET /lanes` lists lanes. Live frames come from CDP `Page.startScreencast` (`cap-backend/app/live/`cdp_screencast.py`, quality/every-nth-frame/max-width from `SCREENCAST_*`); each viewer keeps only the newest frame (`cap-backend/app/live/`frames.py`). Verified with real Chromium. Open: running behind a proxy (checked in Step 10); the WebSocket uses the server's ping and no extra heartbeat | Roadmap Step 7 |

### US-09.3 — Live scraping panel (jobs + browser view)
**Status:** Done | **Priority:** Must | **Depends on:** US-09.2, US-09.1
**As a** user **I want** to see all jobs and, for each running one, its live browser view **so that** I can follow the scrape itself.

**Acceptance criteria**
- [x] List of jobs with state (queued/running/captcha/done/failed) and per-worker live view
- [x] Selecting a job/worker focuses its view; finished jobs show last frame or "idle" state
- [x] Designed states: no active job, stream disconnected, CAP down

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | Left half of the split view | User request |
| 2026-10-15 | COMMENT | Now the right-hand side of the layout; each pane shows ONE job (id badge US-09.8, menu US-09.9). The "list of all jobs" criterion is satisfied by the slot grid (US-09.7) | Layout refinement |
| 2026-10-15 | COMMENT | Correction: the scraper pane is a scrollable LIST of live views (one per job), not a single view; with the 4-pane layout there are two such lists (US-09.7). The original criteria stand as written | "ese componente es la lista de vistas" |
| 2026-10-16 | STATUS | Approved -> In progress (roadmap Step 8: frontend) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented in `cap-frontend/src/features/scraper/`: one live view per worker with its status (idle, live job/person, waiting for CAPTCHA, reconnecting), last frame kept when idle. The "job" of this story is a worker lane (see US-09.10); pairing with its report is by hover highlight | Roadmap Step 8 |
| 2026-10-16 | STATUS | In progress -> Done (verified in the browser against the mock backend; 47 unit tests) | Roadmap Step 8 |

### US-09.4 — Solve CAPTCHA inside the live view (human-in-the-loop)
**Status:** Done | **Priority:** Must | **Depends on:** US-09.2, US-01.5
**As an** operator **I want** to click/type in the live view to solve the CAPTCHA myself **so that** the job continues without any bypass.

**Acceptance criteria**
- [x] Input (mouse/keyboard) forwarded to the page only while a job is in `captcha_required`
- [x] Job resumes automatically when the CAPTCHA is passed; timeout → `blocked_captcha`
- [x] Only the human's own input is forwarded; no automated solving anywhere
- [x] In live mode, the screencast and input channels require authentication (`ADMIN_TOKEN`, see US-07.3); unauthenticated requests get 401 and no frames
- [x] In mock mode no authentication is required

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | Concretizes how US-01.5 is operated | User request + US-01.5 |
| 2026-10-15 | AMENDED | Added authentication criteria for live mode (remote browser control is a security risk on a public URL) | "agrega la autenticacion para el live" |
| 2026-10-16 | COMMENT | The human-in-the-loop is no longer needed for logging in to CAP (DECISIONS.md §1 assumed it) because `/traffic` needs no login. The live view stays useful to watch the scrape and as contingency if a CAPTCHA appears | Full review of `/traffic` |
| 2026-10-16 | STATUS | Approved -> In progress (roadmap Step 7: live view, screencast and access control) | "siguiente" |
| 2026-10-16 | COMMENT | Step 7: input comes as validated events (click, text, a short list of keys, scroll) over the same WebSocket and is routed by `cap-backend/app/live/`input_router.py` only while the lane's person is in `captcha_pending`; the page replays it (`cap-backend/app/live/`page_input.py`) and, once no reCAPTCHA is visible, the router resolves the CAPTCHA and the job continues. Unauthenticated WebSocket handshakes are closed (policy violation) and receive no frames; in mock mode no authentication is needed. Tests: `cap-backend/tests/live_view/`, `tests/auth/`, `tests/live/test_live_view.py` | Roadmap Step 7 |
| 2026-10-16 | STATUS | In progress -> Done (all criteria met; the UI that draws the view comes in Step 8) | Roadmap Step 7 |

### US-09.5 — Live report panel
**Status:** Done | **Priority:** Must | **Depends on:** US-09.1, US-04.2, US-04.3, US-04.4
**As a** user **I want** the real-time report (progress bar, activity feed, results table, case drawer, error states) in the right half **so that** I see results as they appear.

**Acceptance criteria**
- [x] Reuses the components from EP-04; no duplicate implementations
- [x] Updates from the event SSE with Last-Event-ID resume
- [x] Selecting a job on the left filters the report on the right (and vice versa)

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | Right half of the split view | User request |
| 2026-10-16 | STATUS | Approved -> In progress (roadmap Step 8: frontend) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented with the EP-04 components in `cap-frontend/src/features/report/` (no duplicates); updates from SSE; each report card is paired one to one with the live view of the same worker slot | Roadmap Step 8 |
| 2026-10-16 | STATUS | In progress -> Done (verified in the browser against the mock backend; 47 unit tests) | Roadmap Step 8 |

### US-09.6 — Mock screencast
**Status:** Done | **Priority:** Must | **Depends on:** US-09.2, US-01.3
**As a** grader **I want** the live view to work in mock mode **so that** the whole workspace is demonstrable without CAP.

**Acceptance criteria**
- [x] Mock provider emits synthetic frames (rendered fixture pages / simulated CAPTCHA) on the same channel and format as live
- [x] Simulated CAPTCHA can be "solved" by a click to demo US-09.4

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | Brief requires full demo in mock mode | Brief + user request |
| 2026-10-16 | STATUS | Approved -> In progress (roadmap Step 7: live view, screencast and access control) | "siguiente" |
| 2026-10-16 | COMMENT | Step 7: `cap-backend/app/live/`mock_screen.py` draws the portal steps (form, searching, results, no results, case options, errors, CAPTCHA) with Pillow and publishes them on the same channel and format as live; clicking the fake checkbox solves the simulated CAPTCHA | Roadmap Step 7 |
| 2026-10-16 | STATUS | In progress -> Done | Roadmap Step 7 |

---

### US-09.7 — Choose 2 or 4 panes; reports and scrapers paired by row
**Status:** Done | **Priority:** Must | **Depends on:** US-09.1, US-09.3, US-09.5
**As a** user **I want** to choose a 2-pane or 4-pane horizontal layout, where each pane is a vertically scrollable list of job views **so that** I can follow all my jobs, split across one or two lists.

**Acceptance criteria**
- [x] Layout selector: 2 panes = 1 list of reports (left) + 1 list of scrapers (right); 4 panes = 2 lists of reports (left column, top/bottom) + 2 lists of scrapers (right column, top/bottom)
- [x] Each pane is an `overflow-auto-y` list: every job is one item (a report card in the left list, a live browser view in the right list), so any number of jobs fits
- [x] In the 4-pane layout the N jobs are split in two contiguous blocks: the top lists get the first ceil(N/2) jobs and the bottom lists get the rest (N=1 → 1 top / 0 bottom; N=3 → 2 / 1; N=4 → 2 / 2); the top report list and top scraper list hold the same jobs in the same order, likewise for the bottom
- [x] In the 2-pane layout all N jobs go in the single list of each side
- [x] A list with no jobs shows "No jobs to show" in both its report and scraper panes (4-pane layout with 1 job → bottom lists show that message)
- [x] Switching the layout re-distributes jobs without restarting them

> **Previous (2026-10-15):** 2 panes = 1 row (report | scraper); 4 panes = 2 rows with one report and one scraper per row; rows without a job show "No jobs to show".
> Replaced because each pane is a scrollable list of views, not a single view; 4 panes means 2 lists instead of 1.

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | 2/4 pane selector with row pairing and empty state | User request |
| 2026-10-15 | AMENDED | Panes are scrollable lists of job views; 4 panes = 2 lists per side | "ese componente es la lista de vistas… 2 listas en lugar de solo 1" |
| 2026-10-15 | AMENDED | Distribution rule fixed: top gets ceil(N/2), bottom the rest (replaces the round-robin assumption, which was never approved) | "dividimos entre 2 roof rounding… el resto lo pasamos a la lista de abajo" |
| 2026-10-16 | STATUS | Approved -> In progress (roadmap Step 8: frontend) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented in `cap-frontend/src/features/workspace/` (`layout.ts` with tests, `pane-list.tsx`): 2/4-pane selector, top lists get ceil(N/2), "No jobs to show" when a list is empty, switching only redistributes | Roadmap Step 8 |
| 2026-10-16 | STATUS | In progress -> Done (verified in the browser against the mock backend; 47 unit tests) | Roadmap Step 8 |

### US-09.8 — Job ID badge shared by scraper and report
**Status:** Done | **Priority:** Must | **Depends on:** US-09.7
**As a** user **I want** a small, semi-transparent job id at the top-left of each scraper view that matches the id shown on its report **so that** I can tell which report belongs to which browser.

**Acceptance criteria**
- [x] Badge at top-left of the scraper pane: transparent, small, does not block the view
- [x] Same id shown in the header of the matching report pane
- [x] Hovering/selecting one highlights its counterpart

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | Visual pairing of scraper and report | User request |
| 2026-10-16 | STATUS | Approved -> In progress (roadmap Step 8: frontend) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented: semi-transparent badge top-left of each live view (`L1`, `L2`…) and the same badge in the header of its report card; hovering one highlights the other | Roadmap Step 8 |
| 2026-10-16 | STATUS | In progress -> Done (verified in the browser against the mock backend; 47 unit tests) | Roadmap Step 8 |

### US-09.9 — Pane menu (3 dots) with "open in separate tab"
**Status:** Done | **Priority:** Must | **Depends on:** US-09.3
**As a** user **I want** a three-dots menu at the top-right of each scraper view with the option "Open in separate tab" **so that** I can watch or operate that browser full-size.

**Acceptance criteria**
- [x] Menu at top-right of each scraper pane; first option opens a new browser tab with that job's live view
- [x] The standalone page has a stable URL (job id) and works after refresh; shows an ended state if the job finished
- [x] CAPTCHA interaction (US-09.4) works from the standalone tab too

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | Pop-out of a single browser view | User request |
| 2026-10-16 | STATUS | Approved -> In progress (roadmap Step 8: frontend) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented: three-dots menu on each live view with "Open in separate tab" opening `#/live/{lane}` (`cap-frontend/src/features/scraper/standalone-view.tsx`). The URL is by worker lane (stable, works after a refresh, shows idle when no person is assigned); solving a CAPTCHA works from that tab too | Roadmap Step 8 |
| 2026-10-16 | STATUS | In progress -> Done (verified in the browser against the mock backend; 47 unit tests) | Roadmap Step 8 |

### US-09.10 — Choose number of concurrent jobs before Start
**Status:** Done | **Priority:** Must | **Depends on:** US-03.2, US-04.1
**As a** user **I want** an input to set how many jobs run at the same time before pressing Start **so that** I control the parallelism of my run.

**Acceptance criteria**
- [x] Numeric input (min 1, max = server-configured limit) next to Start; value sent with job creation
- [x] The server enforces the limit regardless of the client value (global bound from US-03.2 still applies)
- [x] All requested jobs run and appear as items in the scrollable lists (US-09.7); no job is hidden for lack of space

> **Previous (2026-10-15):** Open question: if requested jobs exceed visible rows (2 or 4 panes), the extra jobs run but are only reachable via separate tab / selector.
> Resolved by the user: the extra jobs run and live in the scrollable list.

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | User-selectable parallel jobs | User request |
| 2026-10-15 | AMENDED | Open question closed: extra jobs go in the scrollable list | "corre igual pero lo tenemos en el componente que tiene overflow-auto-y" |
| 2026-10-16 | COMMENT | Backend interpretation (Step 5): the requested number becomes the job's `parallelism`, i.e. the lanes (workers) serving that one upload, clamped by `MAX_WORKERS`; every event and person carries its `lane`, so the UI maps each lane to one live scraper view. To confirm: splitting the CSV into several independent jobs would be a different design | Roadmap Step 5 |
| 2026-10-16 | STATUS | Approved -> In progress (roadmap Step 8: frontend) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented in `cap-frontend/src/features/upload/upload-screen.tsx`: numeric input (min 1, max = server limit) next to Start, sent as `parallelism`; the server clamps it; every lane becomes an item of the pane lists | Roadmap Step 8 |
| 2026-10-16 | STATUS | In progress -> Done (verified in the browser against the mock backend; 47 unit tests) | Roadmap Step 8 |
| 2026-10-16 | AMENDED | A job never gets more panes/workers than it has people to search: parallelism = min(requested, MAX_WORKERS, people), and the selector's maximum follows the same rule, so no pane waits for a worker that has nothing to do | "que si pongo 3... me permita tener 3 pantallas y no me salga waiting for worker" |
