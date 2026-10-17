import { useEffect, useState } from 'react'
import { Columns2, Grid2x2, RotateCcw, Scale } from 'lucide-react'
import { SetupScreen } from './SetupScreen'
import { Workspace } from './Workspace'
import type { Layout } from './layout'
import { ScraperCard } from './ScraperCard'
import { Badge } from './ui'
import { buildJobs, useRun } from './sim'
import type { Person } from './csv'

const DEMO: Person[] = ['John Smith', 'Pedro Rodriguez', 'Luis Hernandez', 'Ana Torres', 'Carlos Mendoza', 'Maria Gonzalez'].map((n, i) => {
  const [firstName, lastName] = n.split(' ')
  return { id: `P-0${i + 1}`, firstName, lastName, ref: '', key: n.toLowerCase() }
})

// Separate-tab view (#/view/J-02). Mockup: it runs its own independent simulation.
function Standalone({ id }: { id: string }) {
  const run = useRun()
  const { setJobs } = run
  useEffect(() => {
    const idx = Math.max(1, parseInt(id.slice(2), 10) || 1)
    setJobs(buildJobs(1, [DEMO[(idx - 1) % DEMO.length]], idx))
  }, [id, setJobs])
  const job = run.jobs[0]
  return (
    <div className="mx-auto max-w-4xl p-6">
      <p className="mb-3 text-xs text-slate-500">Standalone live view · <Badge>mockup: independent simulation</Badge></p>
      {job && <div className="h-[75vh]"><ScraperCard job={job} hovered={false} onHover={() => {}} onSolve={run.solveCaptcha} standalone /></div>}
    </div>
  )
}

export default function MockupApp() {
  const run = useRun()
  const [layout, setLayout] = useState<Layout>(4)
  const hash = location.hash.match(/^#\/view\/(J-\d+)$/)
  if (hash) return <Standalone id={hash[1]} />

  const { jobs } = run
  const persons = jobs.flatMap((j) => j.persons).length
  const finished = jobs.reduce((s, j) => s + Object.keys(j.outcomes).length, 0)
  const pct = persons ? Math.round((finished / persons) * 100) : 0
  const allDone = jobs.length > 0 && jobs.every((j) => j.status === 'done')

  if (!jobs.length) return <div className="h-full overflow-y-auto"><SetupScreen onStart={run.start} /></div>

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-4 border-b border-slate-200 bg-white px-4 py-2.5">
        <div className="flex items-center gap-2 font-semibold text-slate-900"><span className="grid size-7 place-items-center rounded-lg bg-slate-900 text-white"><Scale size={15} /></span> Court Case Tracker</div>
        <Badge tone="amber">Mock mode</Badge>
        <div className="mx-4 flex flex-1 items-center gap-3">
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-500" style={{ width: `${pct}%` }} />
          </div>
          <span className="w-28 text-xs text-slate-500">{allDone ? 'All jobs complete' : `${finished} / ${persons} people`}</span>
        </div>
        <div className="flex rounded-lg bg-slate-100 p-0.5" role="group" aria-label="Layout">
          {([2, 4] as const).map((l) => (
            <button key={l} onClick={() => setLayout(l)} aria-pressed={layout === l}
              className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition ${layout === l ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}>
              {l === 2 ? <Columns2 size={14} /> : <Grid2x2 size={14} />} {l} panes
            </button>
          ))}
        </div>
        <button onClick={run.reset} className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100"><RotateCcw size={14} /> New run</button>
      </header>
      <Workspace jobs={jobs} layout={layout} onSolve={run.solveCaptcha} />
    </div>
  )
}
