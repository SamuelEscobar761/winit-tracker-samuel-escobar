# User stories index

One file per epic. Stories are never deleted: they are amended with a visible trail,
commented, or marked `Superseded` / `Dropped`. Process: [user-story-traceability skill](../../.claude/skills/user-story-traceability/SKILL.md).

| Epic | File | Brief area | Stories |
|---|---|---|---|
| EP-01 | [CAP investigation & providers](EP-01-cap-investigation-providers.md) | Scraping & resilience | 11 |
| EP-02 | [CSV import & validation](EP-02-csv-import-validation.md) | Feature 1 | 4 |
| EP-03 | [Async engine & SSE](EP-03-async-engine-sse.md) | Feature 2 | 6 |
| EP-04 | [Dashboard UX/UI](EP-04-dashboard-ux.md) | Feature 4 (high priority) | 6 |
| EP-05 | [Claude agents](EP-05-claude-agents.md) | Feature 3 (optional) | 5 |
| EP-06 | [Case data model & data quality](EP-06-case-data-quality.md) | Data to extract | 6 |
| EP-07 | [Deployment & Docker](EP-07-deployment-docker.md) | Bonus + README | 3 |
| EP-08 | [Quality, tests & documentation](EP-08-quality-tests-docs.md) | Code quality, docs, debrief | 3 |
| EP-09 | [Live workspace (split view)](EP-09-live-workspace.md) | Added by user request | 10 |

## Story template

```markdown
### US-XX.N — Title
**Status:** Proposed | **Priority:** Must/Should/Optional/Bonus | **Depends on:** —
**As a** … **I want** … **so that** …

**Acceptance criteria**
- [ ] …

**History**
| Date | Type | Summary / reason | Trigger |
|---|---|---|---|
| YYYY-MM-DD | CREATED | … | … |
```

History types: `CREATED`, `AMENDED` (keep old text in a `> Previous (date):` quote), `COMMENT`, `STATUS`.
