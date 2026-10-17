import { useMemo, useState } from 'react'
import { CheckCircle2, FileUp, Play, Wand2, XCircle } from 'lucide-react'
import { validateCsv } from './csv'
import type { Person } from './csv'
import { SAMPLE_CSV } from './data'
import { Badge } from './ui'

const MAX_JOBS = 6

export function SetupScreen({ onStart }: { onStart: (n: number, persons: Person[]) => void }) {
  const [text, setText] = useState('')
  const [jobsN, setJobsN] = useState(2)
  const [drag, setDrag] = useState(false)
  const report = useMemo(() => (text ? validateCsv(text) : []), [text])
  const persons = report.flatMap((r) => (r.person ? [r.person] : []))
  const rejected = report.filter((r) => r.status === 'rejected').length

  const readFile = async (f: File) => setText(await f.text())

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10">
      <h1 className="text-3xl font-bold tracking-tight text-slate-900">Screen your drivers</h1>
      <p className="mt-2 text-sm text-slate-500">Upload a CSV and we search the San Bernardino Superior Court portal for each person, live.</p>

      <label
        onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); const f = e.dataTransfer.files[0]; if (f) void readFile(f) }}
        className={`mt-8 flex cursor-pointer flex-col items-center gap-2 rounded-3xl border-2 border-dashed bg-white px-6 py-10 text-center shadow-card transition ${drag ? 'border-indigo-400 bg-indigo-50/40' : 'border-slate-200'}`}
      >
        <div className="grid size-12 place-items-center rounded-2xl bg-indigo-50 text-indigo-600"><FileUp size={22} /></div>
        <p className="text-sm font-semibold text-slate-800">Drop your CSV here, or click to browse</p>
        <p className="text-xs text-slate-500">Columns: first_name, last_name, date_of_birth (optional), external_ref (optional)</p>
        <input type="file" accept=".csv,text/csv" className="hidden" onChange={(e) => e.target.files?.[0] && void readFile(e.target.files[0])} />
        <button type="button" onClick={(e) => { e.preventDefault(); setText(SAMPLE_CSV) }} className="mt-2 inline-flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-700">
          <Wand2 size={13} /> Use sample CSV
        </button>
      </label>

      {report.length > 0 && (
        <section className="animate-fade-in mt-6 overflow-hidden rounded-3xl bg-white shadow-card ring-1 ring-slate-200/70">
          <header className="flex items-center gap-2 px-5 py-4">
            <h2 className="text-sm font-semibold text-slate-900">Validation report</h2>
            <Badge tone="green">{persons.length} ready</Badge>
            {rejected > 0 && <Badge tone="red">{rejected} rejected</Badge>}
          </header>
          <ul className="max-h-72 divide-y divide-slate-50 overflow-y-auto border-t border-slate-100">
            {report.map((r) => (
              <li key={r.line} className="flex items-start gap-3 px-5 py-2.5 text-sm">
                {r.status === 'rejected' ? <XCircle size={16} className="mt-0.5 shrink-0 text-rose-500" /> : <CheckCircle2 size={16} className={`mt-0.5 shrink-0 ${r.status === 'normalized' ? 'text-amber-500' : 'text-emerald-500'}`} />}
                <span className="w-8 shrink-0 font-mono text-xs text-slate-400">L{r.line}</span>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-mono text-xs text-slate-700">{r.raw}</p>
                  {r.reason && <p className={`text-xs ${r.status === 'rejected' ? 'text-rose-600' : 'text-amber-600'}`}>{r.status === 'normalized' ? 'Normalized: ' : ''}{r.reason}</p>}
                </div>
                <Badge tone={r.status === 'rejected' ? 'red' : r.status === 'normalized' ? 'amber' : 'green'}>{r.status}</Badge>
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="mt-6 flex flex-wrap items-end gap-4 rounded-3xl bg-white p-5 shadow-card ring-1 ring-slate-200/70">
        <label className="text-xs font-medium text-slate-600">
          Jobs at the same time
          <input type="number" min={1} max={MAX_JOBS} value={jobsN}
            onChange={(e) => setJobsN(Math.min(MAX_JOBS, Math.max(1, Number(e.target.value) || 1)))}
            className="mt-1 block w-28 rounded-xl bg-slate-100 px-3 py-2 text-sm outline-none focus:bg-white focus:ring-2 focus:ring-indigo-300" />
          <span className="mt-1 block text-[11px] font-normal text-slate-400">Server limit: {MAX_JOBS}</span>
        </label>
        <button
          disabled={!persons.length}
          onClick={() => onStart(jobsN, persons)}
          className="ml-auto inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
        >
          <Play size={15} /> Start {persons.length ? `(${persons.length} people)` : ''}
        </button>
      </div>
    </div>
  )
}
