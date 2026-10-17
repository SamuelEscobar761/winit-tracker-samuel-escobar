# EP-06 — Case data model & data quality

Brief area: "Data to extract", data-quality debrief question (two John Smiths).

## Epic changelog
| Date | Change |
|---|---|
| 2026-10-15 | Epic created from challenge brief (US-06.1 – US-06.3) |
| 2026-10-16 | Comments on US-06.1 and US-06.2 about `/traffic` list fields |
| 2026-10-16 | Added US-06.4 (keep only the CSV person's cases, Approved), US-06.5 (restricted Warrant, Approved), US-06.6 (identity grouping, Approved); comments on US-06.2 and US-06.3 |

---

### US-06.1 — Case data model and parser
**Status:** In progress | **Priority:** Must | **Depends on:** US-01.2
**As a** system **I want** every field CAP shows captured in a typed model **so that** data is complete and traceable.

**Acceptance criteria**
- [ ] Fields: case number (exact format, key), type/category, title, filing date (ISO 8601), status + disposition/date, court location (courthouse, department), parties (role, DOB if shown), charges (statute, description, severity), hearings (past/upcoming: date, time, department, type), source metadata (scraped_at, source URL, raw snapshot)
- [x] Deterministic parser with unit tests on recorded fixtures

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief "Data to extract" | Initial setup |
| 2026-10-16 | COMMENT | The `/traffic` results table only gives: case number, party name, violation date, status (Active/Closed/Inactive/AR Fine/Warrant) and whether a Select action exists. No DOB/charges/hearings in the list; those fields depend on the case detail page (selectors pending). Fields must be optional in the model. See US-01.4 | User correction + pasted DOM |
| 2026-10-16 | STATUS | Proposed → In progress (roadmap Step 2: domain models, parsers and name matching) | "sigue con el paso 2" |
| 2026-10-16 | COMMENT | Step 2 done for this story's parser part: models `cap-backend/app/cases/models.py`, parsers `cap-backend/app/cases/parsing/` (search + select, placeholders → null, ISO dates), tests `cap-backend/tests/cases/` on the real John Smith (286) and Pedro Rodriguez (193) fixtures. Fields hearings/location/disposition are not exposed by the portal, so they are not in the model | Roadmap Step 2 |
| 2026-10-16 | COMMENT | Real payment-plan case `25IN-169374` (fixture `select_25IN-169374.json`) shows: `charges` is empty and only `pocChanges` lists a charge (model exposes `displayed_charges`); a plan's remaining balance is only available as the amount of the option coded `PAYF`; `paymentTotal`/`paymentMonths`/due dates stay empty; options carry codes (`PPE` extension, `PAYP` monthly, `PAYF` pay in full, `PAYC` custom); extension fields are filled (`PLANEXT`) | User fixture |

### US-06.2 — Deterministic match confidence (no false "the" match)
**Status:** In progress | **Priority:** Must | **Depends on:** US-06.1, US-02.3
**As a** fleet manager **I want** each case labelled as confirmed / probable / possible / unlikely for this person **so that** I never wrongly tell someone a driver has a case.

**Acceptance criteria**
- [ ] Rules based on name match, DOB (if both known), location, party role; reasons stored
- [x] Without DOB, results are never labelled "confirmed" — shown as candidates
- [x] DOB conflict → excluded or "unlikely" with reason

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief John Smith homonym requirement | Initial setup |
| 2026-10-16 | COMMENT | The case request (`select`) adds: `charges[]` (statute + description, can be more than the 3 shown on the page), `pocChanges[]`, `bfAmount` (amount due), `bailOptions[]`, `isPoc`, `hasPaymentPlan`, `isExtensionEligible`, `originalDate`/`extendedDate`, `partyId`, `fullName`. The `payment*` fields (monthly amount, dates, fees) are a plan OFFER, not case data, unless `hasPaymentPlan` is true. Charges have no severity and no court location or hearings anywhere → those fields stay optional/null | User Network payload |
| 2026-10-16 | COMMENT | The `search` JSON gives: caseId, caseNumber, citationNumber, fileDate, caseCaption, driversLicense, dateOfBirth, caseStatus (Closed, Active, AR Fine, Warrant, Probation, Pending Adjudication). Model must include these as typed fields; DOB and licence may be empty/`UNKNOWN`/`NIP`/`NONE`/`A0000000` placeholders and must be normalized to null. Supersedes the "no DOB" remarks below | User Network capture |
| 2026-10-16 | COMMENT | Case numbers differ between Step 2 (`25IN-169374`) and Step 3 header (`25IN169374`): dedup key must strip hyphens/spaces and uppercase, display form preserved. Payment-plan cases add past_amount_due, monthly_payment, due_date, remaining_balance. Violation date comes only from Step 2. See US-01.4 variants A/B/C | User screenshot + HTML |
| 2026-10-16 | COMMENT | Step 3 of `/traffic` exposes amount due and charges (statute + description) per case, still no DOB or hearings; list rows also show violation dates back to 1991. Model fields: amount_due, charges[], proof_of_correction_required | User screenshot |
| 2026-10-16 | COMMENT | Matching order: US-06.4 first discards results that are not the CSV person (name / DOB), then the labels here apply only to what is kept. Restricted Warrant cases follow US-06.5 | User decision |
| 2026-10-16 | COMMENT | CORRECTION: DOB IS available in the `search` JSON (`dateOfBirth`), so the rules here can use it: CSV DOB equal + name match → probable/confirmed; different → excluded/unlikely with reason; no DOB on either side → candidate only. Results are loose (middle-name variants, `ROMERO, PEDRO RODRIGUEZ`, co-party captions) so name matching is mandatory before any label. Criteria text unchanged | User Network capture |
| 2026-10-16 | COMMENT | Search by "Last, First" returns many middle-name variants (e.g. `RODRIGUEZ, PEDRO LUIS`, `PEDRO MOISES`) and no DOB in the list ⇒ with list data alone every match is at most "possible"; confidence rules unchanged | User correction + pasted DOM |
| 2026-10-16 | STATUS | Proposed → In progress (roadmap Step 2: domain models, parsers and name matching) | "sigue con el paso 2" |
| 2026-10-16 | COMMENT | Implemented in `cap-backend/app/cases/matching/assessment.py` (labels confirmed/probable/possible/unlikely with reasons). Location and party role are not available from the portal, so rules use name and DOB only | Roadmap Step 2 |

### US-06.3 — Deduplication and result capping
**Status:** Proposed | **Priority:** Should | **Depends on:** US-06.1
**As a** user **I want** cases deduplicated by case number and capped per person **so that** common names don't flood the table.

**Acceptance criteria**
- [ ] Unique by case number across name variants; cap with visible "showing N of M" indicator

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief | Initial setup |
| 2026-10-16 | COMMENT | Cap and dedup apply to KEPT cases only (US-06.4); discarded results appear just as a counter, so "showing N of M" refers to the person's own cases | User decision |
| 2026-10-16 | COMMENT | Step 5: cap per person via `MAX_CASES_PER_PERSON` with a `truncated` flag; the "showing N of M" total is not exposed yet; dedup is by (case key, caption) inside one person's results | Roadmap Step 5 |

### US-06.4 — Keep only cases of the person in the CSV
**Status:** In progress | **Priority:** Must | **Depends on:** US-06.1, US-02.3
**As a** fleet manager **I want** results filtered to the person I searched **so that** I never see or store other people's cases.

**Acceptance criteria**
- [x] Caption parsed as `LAST, FIRST MIDDLE…`; a case is kept only if the normalized last name equals the CSV last name and the caption's given-name tokens start with the CSV first-name tokens (accent/case-insensitive, middle names ignored)
- [x] Discarded: other last names (`ROMERO, PEDRO RODRIGUEZ`), co-party captions (`HERNANDEZ, ABEL LEON`), businesses (caption without comma, `NORCAL WASTE SERVICES INC`)
- [x] CSV has a DOB and the record has one: different → discarded, equal → kept
- [ ] Discarded cases are not stored nor sent to the UI; only a per-person counter "N discarded" with reasons remains; the stored raw snapshot is reduced to the kept items
- [ ] Unit tests on the real Pedro Rodriguez / John Smith fixtures; compound surnames and glued middle names handled by an explicit, documented rule (currently unverified)

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-16 | CREATED | The portal search is loose (193 results for Pedro Rodriguez including other people); only the CSV person's cases are useful | "no es ventajoso tener la información de personas que no están en el csv" |
| 2026-10-16 | STATUS | Approved → In progress (roadmap Step 2: domain models, parsers and name matching) | "sigue con el paso 2" |
| 2026-10-16 | COMMENT | Implemented in `cap-backend/app/cases/matching/case_filter.py` and `caption.py`. Real results: John Smith 286 → 224 kept (59 other last names, 3 businesses); Pedro Rodriguez 193 → 188 kept (3 + 2 discarded). With a DOB the kept set shrinks to that person (John Smith 1959-10-19: 19 cases; Pedro 1985-08-30: 10). Still open: discarded cases are only counted here; not storing them / reducing the raw snapshot is done by the engine (Step 5); compound surnames unverified | Roadmap Step 2 |
| 2026-10-16 | COMMENT | The filter now accepts the name forms of the enabled variant strategies (US-01.9); a case matched through a variant is capped at `probable` and its assessment states "Matched through a name variant" | User decision |
| 2026-10-16 | COMMENT | Step 5: discarded cases are not kept in the job state and never reach the API (only counts per reason); raw snapshots are not stored yet, so the "reduce the snapshot" criterion waits for that | Roadmap Step 5 |

### US-06.5 — Restricted status for Warrant cases
**Status:** In progress | **Priority:** Must | **Depends on:** US-06.1
**As an** operator **I want** Warrant status treated as restricted **so that** the app doesn't expose what the portal's own page hides from non-elevated users.

**Acceptance criteria**
- [x] The UI shows "Restricted by portal" for those cases; the Warrant value is never sent to the frontend, never used in summaries or AI insights
- [x] No case detail (`select`) is fetched for them
- [ ] The raw value stays only in server-side snapshots, and the decision is written in DECISIONS.md

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-16 | CREATED | The page blanks the status (`hasAccess('Elevated Access')`) but the JSON carries it; the brief says "every field CAP shows". The PDF is silent on hidden fields | User answered "ok" to the recommendation |
| 2026-10-16 | STATUS | Approved → In progress (roadmap Step 2: domain models, parsers and name matching) | "sigue con el paso 2" |
| 2026-10-16 | COMMENT | Model side done in `cap-backend/app/cases/models.py` (`is_restricted`, `public_status_label` = "Restricted by portal", `is_detail_eligible` false for Warrant and Closed). Still pending: never sending the Warrant value to the frontend (API serializers, Step 5/8) | Roadmap Step 2 |
| 2026-10-16 | COMMENT | Step 5: API views (`cap-backend/app/api/views.py`) expose only the label "Restricted by portal"; a test asserts the word Warrant never appears in the person response; the engine never requests their detail | Roadmap Step 5 |

### US-06.6 — Group candidates by identity when the CSV has no DOB
**Status:** In progress | **Priority:** Should | **Depends on:** US-06.2, US-06.4
**As a** fleet manager **I want** cases of a homonym grouped as possible different people **so that** I can tell which group is my driver.

**Acceptance criteria**
- [ ] Kept cases are grouped by `(date_of_birth, drivers_license)` into "possible identities", each shown with its DOB and case count; cases without DOB form an "unknown DOB" group
- [x] Never presented as "the" match without a DOB in the CSV (US-06.2)

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-16 | CREATED | Answers the brief's "two John Smiths" question using DOB from the search JSON; awaiting validation | Data-quality review |
| 2026-10-16 | STATUS | Proposed → Approved | "para la us 06 6 es si" |
| 2026-10-16 | STATUS | Approved → In progress (roadmap Step 2: domain models, parsers and name matching) | "sigue con el paso 2" |
| 2026-10-16 | COMMENT | Backend grouping done in `cap-backend/app/cases/matching/identity.py`. Refinement of the criterion: grouped by (DOB, license), but a blank license joins the only licensed group of the same DOB (licenses are often blank). Real result: John Smith kept cases → 119 groups, largest 13 cases. Showing the groups is UI work (EP-04) | Roadmap Step 2 |
| 2026-10-16 | COMMENT | Step 5: identity groups are exposed per person (`identity_groups`, and each case has a `group_id`) | Roadmap Step 5 |
