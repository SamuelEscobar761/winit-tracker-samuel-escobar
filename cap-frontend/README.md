# cap-frontend

React 19 + TypeScript + Tailwind 4 + TanStack Table. Talks to the FastAPI backend in `../cap-backend`.

```
npm install
npm run dev      # http://localhost:5173, proxies the API to http://localhost:8000
npm test         # unit tests (vitest)
npm run lint
npm run build    # type check + production bundle in dist/
```

The backend URL can be changed with `BACKEND_URL`. Start the backend first:

```
cd ../cap-backend
.venv/Scripts/python.exe -m uvicorn app.main:create_app --factory --port 8000
```

## Layout of `src/`

| Folder | What it holds |
|---|---|
| `features/upload` | CSV drop zone, server-side validation report, start form, recent jobs |
| `features/job` | job page, header, SSE stream, snapshot and per-person loading, event helpers |
| `features/workspace` | 2/4-pane layout, pane lists |
| `features/report` | per-worker report card, cases table, filters, event feed |
| `features/scraper` | live view of a worker (WebSocket frames, input), standalone tab |
| `features/case-detail` | case drawer: parsed data next to the raw portal JSON |
| `features/session` | login screen and session state (live mode) |
| `shared` | API client and types, hash routing, formatting, UI atoms |
| `mockup/` | the original throwaway mockup (`mockup.html`), kept only as visual reference |

Technical details of the integration: [../docs/cap-traffic-integration.md](../docs/cap-traffic-integration.md).
