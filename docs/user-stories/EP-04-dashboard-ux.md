# EP-04 — Dashboard UX/UI

Brief area: Feature 4 (HIGH PRIORITY), UX/UI 20%. Premium look: modern shadows, clean typography, consistent spacing; not an admin template.
Frontend: React + Tailwind (workspace: `cap-frontend/`).

## Epic changelog
| Date | Change |
|---|---|
| 2026-10-15 | Epic created from challenge brief (US-04.1 – US-04.6) |
| 2026-10-16 | Comments on US-04.3 / US-04.4: table columns and drawer fields vs what `/traffic` provides (pending validation); mockup in `cap-frontend/src/mockup/` still shows `/search` and old fields |
| 2026-10-16 | Step 8: real frontend in `cap-frontend/src/` (features/shared); US-04.1 - US-04.5 Done, US-04.6 open (contrast check, tokens); the mockup is kept only as visual reference |
| 2026-10-15 | UI mockup of US-04.1–04.5 in `cap-frontend/src/mockup/` (throwaway, uses lucide-react and TanStack Table v8; final components must not import from it) |
| 2026-10-15 | Note: US-04.2–04.4 components are hosted in the right half of the split view; see US-09.1 / US-09.5 |

---

### US-04.1 — Upload and start a job
**Status:** Done | **Priority:** Must | **Depends on:** US-03.1
**As a** user **I want** a drag-and-drop CSV upload with validation feedback **so that** starting a screening is effortless.

**Acceptance criteria**
- [x] Drag/drop + file picker; shows validation report (see US-02.4)
- [x] Starts job and navigates to live dashboard

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief | Initial setup |
| 2026-10-16 | STATUS | Proposed -> In progress (roadmap Step 8: frontend) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented in `cap-frontend/src/features/upload/`: drop zone + file picker, server validation (`POST /jobs/validate`) shown as a report, parallelism input, Start navigates to `#/job/{id}`; recent jobs list to resume after a refresh | Roadmap Step 8 |
| 2026-10-16 | STATUS | In progress -> Done (verified in the browser against the mock backend; 47 unit tests) | Roadmap Step 8 |

### US-04.2 — Global progress bar and live activity feed
**Status:** Done | **Priority:** Must | **Depends on:** US-03.4
**As a** user **I want** overall progress and a live feed of scraper events **so that** I know what's happening.

**Acceptance criteria**
- [x] Progress by person (done/total, failed, blocked)
- [x] Feed auto-scrolls, color-coded by event type; reconnect indicator (EventSource with Last-Event-ID)

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief | Initial setup |
| 2026-10-16 | STATUS | Proposed -> In progress (roadmap Step 8: frontend) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented in `cap-frontend/src/features/job/` and `cap-frontend/src/features/report/`: header progress bar and counts (finished/total, failed), per-worker feed (`event-feed.tsx`) auto-scrolling and colour-coded, SSE through `EventSource` (automatic `Last-Event-ID` resume, deduplicated by id) with a reconnecting banner | Roadmap Step 8 |
| 2026-10-16 | STATUS | In progress -> Done (verified in the browser against the mock backend; 47 unit tests) | Roadmap Step 8 |

### US-04.3 — Sortable, filterable results table
**Status:** Done | **Priority:** Must | **Depends on:** US-04.2, US-06.1
**As a** fleet manager **I want** a table of person, case number, type, status, filing date, next hearing **so that** I can triage quickly.

**Acceptance criteria**
- [x] Sort on every column; filter by person, type, status, text search
- [x] Rows appear live as cases arrive; match-confidence badge visible (see US-06.2)

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief | Initial setup |
| 2026-10-16 | COMMENT | UPDATE to the row below, after the Network capture: filing date IS available (`fileDate`, shown by the page as "violation date"), and so are DOB and driver's licence. Still not seen: case type (maybe from the case-number prefix), next hearing, court location. Proposal for columns: person, case number, name on case, file date, status, amount due (when loaded), match confidence (DOB-based). Pending validation | User Network capture |
| 2026-10-16 | COMMENT | The `/traffic` data source cannot fill "type", "filing date" or "next hearing". Available: case number, name, violation date, portal status (Active/Closed/Inactive/AR Fine/Warrant-hidden), amount due, charges, payment-plan info. PROPOSAL pending validation: columns become person, case number, name on case, violation date (replaces filing date), status, amount due, match confidence; "type" only if derivable from the case-number prefix; "next hearing" dropped or shown as "n/a". This deviates from the brief's column list and must be justified in DECISIONS.md | Full review of `/traffic` |
| 2026-10-16 | STATUS | Proposed -> In progress (roadmap Step 8: frontend) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented in `cap-frontend/src/features/report/cases-table.tsx` with TanStack Table: sortable columns person, case #, name on case, file date, status, amount, match; filters by text, status, match, person and identity; rows appear as cases arrive. ADAPTED to what the portal exposes (no case type or next hearing; file date = portal violation date; amount from the detail), see the earlier comment on this story | Roadmap Step 8 |
| 2026-10-16 | STATUS | In progress -> Done (verified in the browser against the mock backend; 47 unit tests) | Roadmap Step 8 |

### US-04.4 — Case detail drawer
**Status:** Done | **Priority:** Must | **Depends on:** US-04.3
**As a** user **I want** a drawer with parsed fields and raw source side by side **so that** I can verify the data.

**Acceptance criteria**
- [x] Shows parties, charges, hearings, location, source metadata
- [x] Raw HTML/JSON snapshot panel with copy action

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief | Initial setup |
| 2026-10-16 | COMMENT | Drawer additions: "Restricted by portal" chip for Warrant cases (US-06.5), identity groups by DOB (US-06.6, if approved), per-person counter "N results discarded" (US-06.4) and a "Load details" action only when the optional per-person limit of US-01.8 is set; otherwise details load automatically and stream in after the list | User decisions |
| 2026-10-16 | COMMENT | Drawer fields to adapt to `/traffic`: parties/hearings/location are not available; show case number, name, violation date, status, amount due, charges (statute + description), payment plan (past due, monthly, balance), "hidden by portal" flag for Warrant rows, and the raw snapshot. Pending validation together with US-04.3 | Full review of `/traffic` |
| 2026-10-16 | STATUS | Proposed -> In progress (roadmap Step 8: frontend) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented in `cap-frontend/src/features/case-detail/`: parsed side (match reasons, facts, charges, amount, proof of correction, payment plan, extension, notices, restricted/error/closed/loading states) next to the raw portal JSON (search item / case details tabs, copy button, source URL and scraped_at). Parties, hearings and location are not exposed by the portal, so they are not shown | Roadmap Step 8 |
| 2026-10-16 | STATUS | In progress -> Done (verified in the browser against the mock backend; 47 unit tests) | Roadmap Step 8 |

### US-04.5 — Designed empty, loading and error states
**Status:** Done | **Priority:** Must | **Depends on:** US-04.2
**As a** user **I want** clear states for no cases found, CAPTCHA blocked, CAP down, failures **so that** I always know what to do next.

**Acceptance criteria**
- [x] Distinct visuals/messages per state with next-action (retry, solve CAPTCHA)
- [x] Skeleton loaders; no raw errors shown

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief | Initial setup |
| 2026-10-16 | COMMENT | Because of pacing (5 s per action by default) a person can wait for minutes: the feed must show "waiting (throttle)" events and an ETA, and the progress bar must not look stuck. See US-01.7 | Throttling requirement |
| 2026-10-16 | COMMENT | States to design from observed portal behaviour: "No Case(s) Found" (teal), "Found N Case(s)" (green), "Session expired, retrying" (red, transient), "CAP in maintenance" (from `/api/maintenance`), and a per-case detail loading state of ~5 s. Mock must reproduce them | Network investigation |
| 2026-10-16 | STATUS | Proposed -> In progress (roadmap Step 8: frontend) | "siguiente" |
| 2026-10-16 | COMMENT | Designed states: no cases found, worker failures and "portal not responding", CAPTCHA banner, portal down/maintenance banner, session-expired retries in the feed, reconnecting stream banner, Restricted-by-portal chip, skeleton loaders, login and server-unreachable screens; API errors are shown as plain sentences | Roadmap Step 8 |
| 2026-10-16 | STATUS | In progress -> Done (verified in the browser against the mock backend; 47 unit tests) | Roadmap Step 8 |

### US-04.6 — Responsive, accessible polish
**Status:** In progress | **Priority:** Should | **Depends on:** US-04.1
**As a** user **I want** a consistent, accessible, responsive interface **so that** it feels premium.

**Acceptance criteria**
- [ ] Design tokens (spacing, shadows, typography); keyboard navigation; contrast checks
- [x] Works at laptop and tablet widths

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief visual reference | Initial setup |
| 2026-10-16 | STATUS | Proposed -> In progress (roadmap Step 8: frontend) | "siguiente" |
| 2026-10-16 | COMMENT | Step 8: keyboard support (focusable table rows, Enter opens a case, Escape closes the drawer, labelled controls and `aria-*` on tabs, progress bars, dialog and live regions), reduced-motion support, tested at 1600 px and 900 px. Still open: a formal contrast check and moving all colours to named design tokens (currently Tailwind palette + the theme in `cap-frontend/src/index.css`) | Roadmap Step 8 |
