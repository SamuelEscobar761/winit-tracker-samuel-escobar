# EP-08 — Quality, tests & documentation

Brief area: code quality & tests (10%), documentation (5%), understanding & debrief (25%).

## Epic changelog
| Date | Change |
|---|---|
| 2026-10-15 | Epic created from challenge brief (US-08.1 – US-08.3) |
| 2026-10-16 | US-08.2 Done (README and DECISIONS complete) |

---

### US-08.1 — Tests for parser and CSV validator
**Status:** In progress | **Priority:** Must | **Depends on:** US-06.1, US-02.2
**As a** maintainer **I want** unit tests on the parser and validator **so that** regressions are caught.

**Acceptance criteria**
- [ ] Validator covers all sample bad rows; parser tested on recorded fixtures
- [ ] Engine/SSE tests: bounded concurrency, retry, Last-Event-ID replay (using mock provider)

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief | Initial setup |
| 2026-10-16 | COMMENT | Also test: caption filter on the real Pedro Rodriguez fixture (kept vs discarded examples in US-06.4), query-string builder (`last, first`, no accents, ≤ 20 chars), throttle (delay and per-minute cap with a fake clock), position check/recovery after errors (US-01.4) | User decisions |
| 2026-10-16 | COMMENT | Parser fixtures must cover: Step 2 table (all statuses, Warrant hidden, Closed without Select), "No Case(s) Found", Step 3 variants A/B/C (US-01.4) and the case-number hyphen difference | Full review of `/traffic` |
| 2026-10-16 | STATUS | Proposed → In progress (roadmap Step 1: backend scaffold and configuration) | "siguiente" |
| 2026-10-16 | COMMENT | Step 1: tooling wired in `cap-backend/pyproject.toml` (pytest, ruff, mypy strict); 12 tests passing for settings and `/health`. Parser/validator/engine tests come with their steps | Roadmap Step 1 |
| 2026-10-16 | COMMENT | Step 6: browser tests (`cap-backend/tests/live/`) run real Chromium against a local replica of the portal and are skipped automatically when Chromium is not installed | Roadmap Step 6 |

### US-08.2 — README and DECISIONS kept current
**Status:** Done | **Priority:** Must | **Depends on:** —
**As a** reviewer **I want** honest, concise docs **so that** I understand choices and trade-offs.

**Acceptance criteria**
- [x] README: docker run (mock/live), config, deployment strategy
- [x] DECISIONS: CAP investigation with screenshots, SSE/AI choices, what AI generated and how verified

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief deliverables | Initial setup |
| 2026-10-16 | COMMENT | DECISIONS.md §1 rewritten for `/traffic` only (valid evidence, links to existing 2026-10-16 screenshots, unverified items listed as Open); old `/search` findings removed as invalid. Next: §2 and §3 once the Network-tab investigation is done | User request |
| 2026-10-16 | COMMENT | (superseded by the row above) DECISIONS.md §1 still describes `/search` (login required) and links 2026-10-15 screenshots that are NOT in docs/assets (only 2026-10-16 ones exist). Needs rewriting for `/traffic` and re-capturing the landing/disclaimer screenshot | Full review of `/traffic` |
| 2026-10-16 | STATUS | Proposed -> Done. README.md written (run, live, config, CSV rules, SSE, AI, tests, deployment, limitations); DECISIONS.md §8-10 and §12 added. §10 hindsight and §9 are honest about what is unverified (real portal run, real Anthropic call) | Step 10 |

### US-08.3 — Debrief readiness and readable commit history
**Status:** Done | **Priority:** Should | **Depends on:** —
**As the** author **I want** small, meaningful commits and notes for the debrief questions **so that** I can explain every line.

**Acceptance criteria**
- [x] Commits grouped by area, one line each (story IDs are in docs/user-stories)
- [x] Short answers prepared for each debrief question in the brief (docs/debrief.md)

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief evaluation criteria | Initial setup |
| 2026-10-16 | STATUS | Proposed -> In progress. docs/debrief.md written (answers, code pointers, likely live changes, checklist). Open: the folder is not a git repository, so commits grouped by story ID cannot exist yet; that needs you to init and commit | Step 11 |
| 2026-10-16 | STATUS | In progress -> Done. Repository initialised with 22 one-line commits grouped by area (backend layers, frontend features, Docker, docs); .gitignore keeps .env, caches, venv and generated rule history out | Git request |
