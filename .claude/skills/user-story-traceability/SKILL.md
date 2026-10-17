---
name: user-story-traceability
description: Use on EVERY request that asks for code, a feature, a change, a fix or a refactor in this project. Finds the related user stories in docs/user-stories/, asks the user to validate creating or amending a story, and records the evolution as history entries (never deleting stories). Run it before writing any code.
---

# User story traceability

Each epic is its own file in `docs/user-stories/EP-XX-*.md`. The history of an epic
is the evolution of its stories, so stories are **never deleted or silently
overwritten** — they are commented, amended with a visible trail, or marked
Superseded/Dropped.

## Steps (run before any code change)

1. **Locate.** Read `docs/user-stories/README.md` (index) and the epic file(s) that
   plausibly cover the request. Search by keyword if unsure.
2. **Classify the request** against what exists:
   - **Covered** — an existing story already describes it → reference its ID (e.g. `US-03.2`).
   - **Partially covered / changed** — the story must evolve → propose an amendment.
   - **New** — no story covers it → propose a new story (in the right epic, or a new epic if none fits).
   - **Contradicts** a story → propose marking it `Superseded` and creating a replacement.
   - **Not product behavior** (typo, formatting, pure tooling) → state that no story applies and continue.
3. **Ask for validation** (AskUserQuestion, or a concise message if the answer is obvious
   from the user's own words) before editing any story. Show the exact proposed text:
   story ID, "As a / I want / so that", acceptance criteria, and what changes. Do not
   write code until the user confirms. If the user already said "go ahead" explicitly
   for that story, no extra confirmation is needed.
4. **Record the change** in the epic file once validated:
   - New story → add it with status `Proposed` or `Approved`, plus a `CREATED` history row.
   - Amended story → keep the previous wording inside a `> **Previous (YYYY-MM-DD):** …`
     blockquote (or strike it through) under the story, write the new wording, and add
     an `AMENDED` history row with the reason.
   - Any other remark → add a `COMMENT` row (do not rewrite the story).
   - Status transitions → `STATUS` row (`Proposed → Approved → In progress → Done`,
     or `Superseded` / `Dropped` with a pointer to the replacement).
   - Also add one line to the epic's **Epic changelog** table.
5. **Implement**, then update the story: tick acceptance criteria, set the status, add a
   history row naming the files touched (paths only, no code dumps).
6. **Reply** to the user listing the story IDs touched and what changed in each.

## Conventions

- IDs: epic `EP-01`, story `US-<epic>.<n>` (e.g. `US-03.2`). IDs are never reused.
- Date format ISO `YYYY-MM-DD`. Use today's date from the environment.
- History row format: `| date | type | summary / reason | trigger (request, short) |`
  with type in `CREATED | AMENDED | COMMENT | STATUS`.
- Statuses: `Proposed`, `Approved`, `In progress`, `Done`, `Superseded`, `Dropped`.
- Mark optional/bonus work with `Priority: Optional` / `Bonus` as in the brief.
- Cross-epic dependencies go in a `Depends on:` line, not by duplicating stories.
- Keep `docs/user-stories/README.md` index in sync (story counts, new epics).
- Requirements come from `docs/challenge-brief.md`; if the user's request conflicts with
  the brief, say so in the validation question.
