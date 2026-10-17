# Challenge brief — WINIT California Court Case Tracker (Edition 2)

Source: `WINIT_CA_Court_Case_Tracker_Challenge.pdf`. Summary for development use.

## Goal
Take a CSV of people, search the Superior Court of California, County of San Bernardino
public portal (CAP, https://cap.sb-court.org/) asynchronously, and stream progress to a
modern dashboard as each search runs. Use case: fleet / driver screening (open traffic,
civil, criminal matters).

## Required stack
- Frontend: React + Tailwind
- Backend: Python (FastAPI)
- Comm: Server-Sent Events (SSE)
- Scraping: Playwright (preferred) or Selenium
- AI (optional): Claude API

## Grading
| Area | Weight | Notes |
|---|---|---|
| Understanding & debrief | 25% | DECISIONS.md, live explanation, live change |
| Scraping & resilience | 20% | CAP flow, pagination, CAPTCHA/rate-limit handling, mock provider |
| Backend architecture & concurrency | 20% | background jobs, bounded workers, SSE reconnect, no hanging server |
| UX/UI | 20% | polish, live feed, results table, empty/error states |
| Code quality & tests | 10% | separation of concerns, typing, tests on parser and CSV validator |
| Documentation | 5% | README with Docker run + deployment strategy |

A 45-minute live debrief follows submission: walk through code, change it live, reason
about failures. AI tools allowed, but must be able to explain everything ("the AI did it"
costs points). Be honest about what was generated and how it was verified.

## CAP navigation to reproduce
1. Open CAP (client-side SPA; wait for render — plain requests+BS4 sees nothing)
2. Accept terms of service gate
3. Search → Case Information
4. Name (person/party) search: first + last name, complete CAPTCHA
5. Read result list, paginate, open each case, extract details

Investigate with DevTools Network tab first: DOM-rendered vs internal JSON API? Session /
cookie / token? Account required? Document in DECISIONS.md with screenshots (graded).

## Rules of engagement
- Public government service: respect terms of use, throttle (few requests/min per worker),
  report failures cleanly.
- Do NOT bypass the CAPTCHA (no solving farms/exploits). Human-in-the-loop or mock is fine if explained.

## Test data
- John Smith (very common → many results; paginate, cap results, never present a homonym as "the" match)
- Pedro Rodriguez (often "Rodriguez Pedro"; handle name order, accents Rodríguez, casing)

```csv
first_name,last_name,date_of_birth,external_ref
John,Smith,,DRV-1001
Pedro,Rodriguez,,DRV-1002
# validator must reject or flag the rows below gracefully
,Smith,,DRV-1003
Pedro;Rodriguez,,DRV-1004
J0hn,Smith,31/02/1990,DRV-1005
```

## Mock mode (required)
Provider interface with `LiveCapProvider` and `MockCapProvider` (fixtures recorded from the
real site for the two names, realistic latency, random failures). One env variable switches.
The graders run the app in mock mode; the SSE pipeline must be fully demonstrable without CAP.

## Features
1. **Bulk import & validation** — CSV with first_name, last_name, optional date_of_birth, external_ref.
   Per-row report: accepted / normalized / rejected (+reason). Never crash: wrong delimiter,
   empty cells, bad encoding, duplicates.
2. **Async scraping engine** — upload returns `job_id` immediately; bounded concurrency
   (configurable pool of browser contexts), retries with backoff, per-person timeouts;
   SSE per job ("Searching Pedro Rodriguez…", "Found 3 cases", "CAPTCHA required",
   "Job complete"); reconnect resumes via `Last-Event-ID`.
3. **Claude agents (optional)** — raw page → validated JSON (Pydantic; invalid output rejected
   and retried); match confidence with explanation (name, DOB, location); actionable insight for
   a fleet manager citing fields. README must explain why an agent vs deterministic parser and
   where AI was not used.
4. **Professional UX/UI (high priority)** — dashboard with global progress bar + live feed;
   sortable/filterable table (person, case number, type, status, filing date, next hearing);
   case detail drawer (parsed fields vs raw source side by side); designed empty/loading/error
   states (no cases, CAPTCHA blocked, CAP down). Premium look, not an admin template.

## Data to extract (per case, at minimum)
Case number (court's exact format, primary key) · case type/category · case title · filing date
(ISO 8601) · status (+ disposition and date) · court location (courthouse, department) ·
parties (role, DOB if shown) · charges/causes (statute, description, severity) · hearings
(date, time, department, type; past and upcoming) · source metadata (scraped_at, source URL,
raw HTML/JSON snapshot).

## Expected system shape (guideline)
React app → FastAPI (validate, create job) → job queue (bounded workers) → provider
(Live CAP | Mock) → parser/agent (raw → JSON). Each stage publishes to a per-job event log;
`GET /jobs/{id}/events` streams it over SSE.

## Debrief questions to prepare
Transport (SSE vs WS/polling, proxy issues) · Concurrency (3 users × 200 names) · Failure
(CAP error on 47th name) · Scraping (DevTools evidence, DOM vs API) · Data quality (two John
Smiths) · AI (what generated, how verified, never-alone decisions) · Live change · Hindsight.

## Bonus: deployment
Frontend on Vercel/Netlify; backend on DigitalOcean/Render/Railway (Playwright browser in image);
SSE through the production proxy (buffering, timeouts, heartbeats). Mock mode OK for public demo.

## Deliverables
- Repo (GitHub/GitLab) with readable commit history
- README.md — run with `docker compose up`, mock and live
- DECISIONS.md — CAP investigation, SSE/AI choices, what AI generated
- Live URL (if deployed)
- Optional 3-minute screen recording
