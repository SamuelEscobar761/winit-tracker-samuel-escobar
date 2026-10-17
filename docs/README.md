# docs/ — project knowledge base

Working reference for development (and for Claude). Not a replacement for the root
`README.md` / `DECISIONS.md`, which are the deliverables.

| Document | Purpose |
|---|---|
| [challenge-brief.md](challenge-brief.md) | Structured summary of the WINIT challenge PDF: requirements, rules, grading |
| [user-stories/](user-stories/README.md) | Epics (one file each) with user stories and their change history |
| [cap-traffic-integration.md](cap-traffic-integration.md) | Technical reference of the CAP `/traffic` integration: flow, API calls, data mapping, name rules, throttling, errors |
| [roadmap/README.md](roadmap/README.md) | Build order: steps, stories per step, what is needed from the user, PDF requirement coverage |
| `assets/` | Screenshots and recorded fixtures references (create when needed) |

Skills live in [../.claude/skills/](../.claude/skills/). The first one,
`user-story-traceability`, governs how requests become/modify user stories.
