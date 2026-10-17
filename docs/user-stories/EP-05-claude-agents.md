# EP-05 — Claude agents (optional)

Brief area: Feature 3 (optional). Must be explained in README: why an agent vs deterministic parser, and where AI is NOT used.

## Epic changelog
| Date | Change |
|---|---|
| 2026-10-15 | Epic created from challenge brief (US-05.1 – US-05.4) |
| 2026-10-16 | Added US-05.5 (self-healing portal rules) at the user's request; Step 9 started |
| 2026-10-16 | US-05.1 – US-05.5 Done (US-05.1/05.2 criteria reworded to what the JSON portal allows) |

---

### US-05.1 — Structure raw case pages into validated JSON
**Status:** Done | **Priority:** Optional | **Depends on:** US-06.1
**As a** system **I want** Claude to turn raw case pages into Pydantic-validated JSON **so that** unusual layouts still parse.

**Acceptance criteria**
> **Previous (2026-10-16):** Output validated against schema; invalid output rejected and retried (bounded), never trusted blindly. Deterministic parser remains the primary path; agent is fallback/cross-check.

- [x] Structured output validated against a Pydantic schema (SDK structured outputs); an answer that does not match is rejected, never trusted blindly
- [x] Applied to the free-text notices of a case (`maMessage`/`userMessage`): every excerpt, date and amount must appear literally in the source text or the item is dropped and counted
- [x] The deterministic parser stays the only path for charges, amounts and statuses (the portal answers JSON, so no page-to-JSON agent is needed); decision documented

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief Feature 3 | Initial setup |
| 2026-10-16 | COMMENT | `/traffic` pages are small, fixed-layout Angular views (3 observed variants), so a deterministic parser is clearly the right primary path; the agent is justified only as fallback for unknown Step 3 layouts (`detail_unparsed`) and for the explained match confidence. Document this in the README AI section | Full review of `/traffic` |
| 2026-10-16 | STATUS | Proposed -> In progress (roadmap Step 9: Claude agents) | "siguiente… los agentes claude deben actualizar las reglas de scrapping" |
| 2026-10-16 | STATUS | In progress -> Done. Code and tests complete; the Anthropic call path itself is covered with fakes only (no API key was available), so a real-key smoke run is still recommended | Step 9 delivered |
| 2026-10-16 | AMENDED | Criteria reworded: the portal answers JSON, so the agent structures the free-text notices and every extracted value must be traceable to the source text | Step 9 implementation |

### US-05.2 — Match confidence with explanation
**Status:** Done | **Priority:** Optional | **Depends on:** US-06.2
**As a** fleet manager **I want** an explained confidence that a case belongs to this person **so that** homonyms aren't mistaken for the driver.

**Acceptance criteria**
> **Previous (2026-10-16):** Score + reasons referencing name, DOB, location.

- [x] Plain-English explanation of why the case was linked (supports / weakens / next step) built from the caption, DOB and the deterministic reasons; `/traffic` exposes no location, so none is cited
- [x] Agent never overrides deterministic hard mismatches (e.g. DOB conflict)

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief | Initial setup |
| 2026-10-16 | STATUS | Proposed -> In progress (roadmap Step 9: Claude agents) | "siguiente… los agentes claude deben actualizar las reglas de scrapping" |
| 2026-10-16 | STATUS | In progress -> Done. Code and tests complete; the Anthropic call path itself is covered with fakes only (no API key was available), so a real-key smoke run is still recommended | Step 9 delivered |
| 2026-10-16 | AMENDED | Criteria reworded: `/traffic` exposes no location; explanation uses caption, DOB and the deterministic reasons, and the label is never changed by the agent | Step 9 implementation |

### US-05.3 — Actionable insight for fleet managers
**Status:** Done | **Priority:** Optional | **Depends on:** US-05.1
**As a** fleet manager **I want** a summary (e.g. open traffic case, next hearing) citing the fields used **so that** I can act.

**Acceptance criteria**
- [x] Each finding cites the case keys it relies on; a finding citing an unknown case or a dollar amount absent from the facts is dropped and counted; no grounded finding at all is an error

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief | Initial setup |
| 2026-10-16 | STATUS | Proposed -> In progress (roadmap Step 9: Claude agents) | "siguiente… los agentes claude deben actualizar las reglas de scrapping" |
| 2026-10-16 | STATUS | In progress -> Done. Code and tests complete; the Anthropic call path itself is covered with fakes only (no API key was available), so a real-key smoke run is still recommended | Step 9 delivered |
| 2026-10-16 | AMENDED | Criteria detailed: citations are case keys and amounts are checked against the facts | Step 9 implementation |

### US-05.4 — AI off switch and cost/safety guards
**Status:** Done | **Priority:** Should | **Depends on:** US-05.1
**As an** operator **I want** AI features disabled by default and configurable via env **so that** the app runs without an API key (mock demo).

**Acceptance criteria**
- [x] AI off by default; with `AI_ENABLED=false` or no key every agent endpoint answers 503 and the whole pipeline is unchanged
- [x] Model, timeout and output-token limit configured by env; refusals, outages and invalid output become typed errors (HTTP 502)
- [x] Offline mock model (`AI_OFFLINE_MOCK=true`) answers deterministically for demos and tests

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | Needed so graders can run mock mode | Initial setup |
| 2026-10-16 | STATUS | Proposed -> In progress (roadmap Step 9: Claude agents) | "siguiente… los agentes claude deben actualizar las reglas de scrapping" |
| 2026-10-16 | STATUS | In progress -> Done. Code and tests complete; the Anthropic call path itself is covered with fakes only (no API key was available), so a real-key smoke run is still recommended | Step 9 delivered |
| 2026-10-16 | AMENDED | Criteria detailed: 503 when off, 502 on model errors, offline mock model | Step 9 implementation |

### US-05.5 — Self-healing portal rules (no code changes needed when the portal changes)
**Status:** Done | **Priority:** Should | **Depends on:** US-01.10, US-05.4, US-01.4
**As an** operator **I want** a Claude agent to repair the scraper's portal rules when the portal's page or JSON changes **so that** the scraper keeps working without a developer editing code.

**Acceptance criteria**
- [x] A drift incident (selector not found, response shape changed, unexpected layout) is recorded with a privacy-safe diagnostic bundle: failing step, error, current rules, interactive elements of the page, key names and types of the JSON (no values, no personal data)
- [x] The agent proposes a rules patch as structured output (validated, only known rule fields, selectors and paths checked by an allowlist, never code or scripts)
- [x] A candidate is verified before use by a read-only canary run against the portal with the candidate rules (throttled like any other run); a failing candidate is never activated
- [x] Verified candidates are activated automatically when `AI_RULES_AUTO_APPLY=true` (default when AI is on), otherwise kept as a pending proposal approved or rejected by a person
- [x] Every activation writes a new numbered version, keeps the previous ones, logs who/why/diff/incident/model, and can be rolled back to any earlier version
- [x] Guards: AI off by default, repair attempts rate limited (`AI_RULES_MAX_REPAIRS_PER_HOUR`, one open incident per distinct failure), the agent never touches Warrant handling, payment controls or throttling settings
- [x] Works end to end in a test where the portal page is changed (renamed button, input id, JSON key) and the rules are repaired and verified in real Chromium
- [x] Rules and proposals are visible and manageable through `GET /rules`, approve, reject and rollback endpoints and a simple screen in the frontend

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-16 | CREATED | The agent's job is to keep the scraping rules up to date by itself; requires the rules to live in versioned data, not in code (US-01.10) | "sabes que los agentes claude deben… actualizar las reglas de scrapping para que se auto actualice el scrapper sin codificadores?" |
| 2026-10-16 | STATUS | In progress -> Done. Code and tests complete; the Anthropic call path itself is covered with fakes only (no API key was available), so a real-key smoke run is still recommended | Step 9 delivered |
| 2026-10-16 | AMENDED | Rate-limit variable implemented as AI_RULES_MAX_REPAIRS_PER_HOUR instead of a minimum interval | Step 9 implementation |
