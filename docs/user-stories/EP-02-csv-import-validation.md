# EP-02 — CSV import & validation

Brief area: Feature 1.

## Epic changelog
| Date | Change |
|---|---|
| 2026-10-15 | Epic created from challenge brief (US-02.1 – US-02.4) |
| 2026-10-16 | Comment on US-02.3 (4–20 char portal query) |
| 2026-10-16 | Step 3 implemented (US-02.1–02.3 criteria ticked, still In progress until the API returns the report) |

---

### US-02.1 — Upload CSV and get a per-row report
**Status:** Done | **Priority:** Must | **Depends on:** —
**As a** fleet manager **I want** to upload a CSV (first_name, last_name, optional date_of_birth, external_ref) **so that** I can screen many drivers at once.

**Acceptance criteria**
- [x] Each row reported as `accepted`, `normalized` (with what changed) or `rejected` (with reason)
- [x] Report returned immediately with the job creation response
- [x] Comment lines (`#`) and blank lines handled

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief Feature 1 | Initial setup |
| 2026-10-16 | STATUS | Proposed → In progress (roadmap Step 3: CSV import and validation) | "siguiente" |
| 2026-10-16 | COMMENT | Step 3 backend done in `cap-backend/app/csv_import/` (`importer.py`, `row_validator.py`, `models.py`): per-row status accepted/normalized/rejected with changes and issues, comment/blank lines skipped, original line numbers kept. Pending: returning the report with the job creation response (Step 5) | Roadmap Step 3 |
| 2026-10-16 | STATUS | In progress -> Done (the report is returned by `POST /jobs`) | Roadmap Step 5 |

### US-02.2 — Never crash on malformed input
**Status:** Done | **Priority:** Must | **Depends on:** US-02.1
**As a** user **I want** wrong delimiters, empty cells, bad encodings and duplicates handled gracefully **so that** a bad file gives a clear message, not a 500.

**Acceptance criteria**
- [x] Sample rows rejected/flagged: `,Smith,,DRV-1003` (empty first name), `Pedro;Rodriguez,,DRV-1004` (wrong delimiter), `J0hn,Smith,31/02/1990,DRV-1005` (invalid chars + impossible date)
- [x] Encoding detection/fallback (UTF-8, UTF-8 BOM, latin-1); file size/row limits
- [x] Duplicates detected (same normalized name+DOB) and flagged

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief sample CSV | Initial setup |
| 2026-10-16 | STATUS | Proposed → In progress (roadmap Step 3: CSV import and validation) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented and tested with the brief's sample rows plus encodings (UTF-8, BOM, latin-1), delimiter detection (`,` `;` tab `|`), file limits (`CSV_MAX_BYTES` 2 MB, `CSV_MAX_ROWS` 1000, rejected not truncated), binary files, unreadable rows and duplicates (rejected, pointing to the first line). Tests: `cap-backend/tests/csv_import/` | Roadmap Step 3 |
| 2026-10-16 | STATUS | In progress -> Done (the report is returned by `POST /jobs`) | Roadmap Step 5 |

### US-02.3 — Name and date normalization
**Status:** Done | **Priority:** Must | **Depends on:** US-02.1
**As a** system **I want** names normalized (whitespace, casing, accents kept for display, folded for matching) and dates parsed to ISO 8601 **so that** searches and matching are consistent.

**Acceptance criteria**
- [x] `Rodríguez` / `rodriguez` / `RODRIGUEZ` match key identical; display form preserved
- [x] Ambiguous date formats handled explicitly (documented choice) or flagged

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | From brief test data | Initial setup |
| 2026-10-16 | COMMENT | Search-string rule verified: build `last, first` (comma required), strip accents, case irrelevant (see US-01.6). Normalization must therefore produce an accent-free search key in addition to the display form; the `Rodríguez`/`rodriguez` match key already required here is the same thing | User tests |
| 2026-10-16 | COMMENT | The portal search string `Last, First` must be 4–20 characters. The validator should compute it and flag rows that cannot be searched (e.g. long compound names, only last name) as `normalized`/`rejected` with reason, instead of failing at scrape time. Exact rule pending the open tests in US-01.6 | Full review of `/traffic` |
| 2026-10-16 | STATUS | Proposed → In progress (roadmap Step 2: domain models, parsers and name matching) | "sigue con el paso 2" |
| 2026-10-16 | COMMENT | Name normalization and search-query builder done in `cap-backend/app/people/names.py` (match key, `last, first` without accents, 4–20 length check) with tests in `cap-backend/tests/people/test_names.py`. Date handling for CSV input comes with the validator (Step 3) | Roadmap Step 2 |
| 2026-10-16 | COMMENT | Documented date choice (`dates.py`): ISO `YYYY-MM-DD` always; slashed dates are read as MM/DD/YYYY or DD/MM/YYYY only when the other reading is impossible (e.g. 24/07/1978) and stored as ISO with a note; when both readings are valid and differ (03/04/1990) the row is rejected as ambiguous, because a wrong DOB would wrongly exclude the person's cases; dates before 1900 or in the future are rejected. Names are only whitespace-normalized (display form and accents kept). A row is also rejected when no search text of 4–20 characters can be built even with the name variants (US-01.9) | Roadmap Step 3 |
| 2026-10-16 | STATUS | In progress -> Done (the report is returned by `POST /jobs`) | Roadmap Step 5 |

### US-02.4 — Import review UI
**Status:** Done | **Priority:** Should | **Depends on:** US-02.1, US-04.1
**As a** user **I want** to see the validation report before/while the job starts **so that** I can fix rejected rows.

**Acceptance criteria**
- [x] Table of rows with status chips and reasons; downloadable rejected-rows list
- [x] Only accepted/normalized rows are queued

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| 2026-10-15 | CREATED | UX complement to Feature 1 | Initial setup |
| 2026-10-16 | COMMENT | Backend data for the review UI is ready: `ImportReport` (`counts`, `rows` with `changes` and `issues`, `file_issues`, `queueable_people`). Endpoint and UI come in Steps 5 and 8 | Roadmap Step 3 |
| 2026-10-16 | STATUS | Proposed -> In progress (roadmap Step 8: frontend) | "siguiente" |
| 2026-10-16 | COMMENT | Implemented in `cap-frontend/src/features/upload/validation-report.tsx`: row status chips with reasons and normalizations, file issues, "Download rejected rows" (`rejected-rows-csv.ts`); only accepted/normalized rows are queued by the server | Roadmap Step 8 |
| 2026-10-16 | STATUS | In progress -> Done (verified in the browser against the mock backend; 47 unit tests) | Roadmap Step 8 |
