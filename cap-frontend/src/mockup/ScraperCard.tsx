import { ExternalLink, Lock } from 'lucide-react'
import type { Job } from './sim'
import { DotsMenu, JobId } from './ui'

const NameInput = ({ label, value, typing }: { label: string; value: string; typing: boolean }) => (
  <div className="flex items-center text-[10px]">
    <span className="w-16 rounded-l bg-slate-100 px-1.5 py-1 font-semibold uppercase text-slate-500">{label}</span>
    <span className="h-6 flex-1 rounded-r border border-slate-200 px-1.5 py-1 text-slate-700">{value}<span className="animate-pulse">{value && typing ? '|' : ''}</span></span>
  </div>
)

// Faux render of the CAP page the (simulated) Playwright browser is on.
function FauxCap({ job, onSolve }: { job: Job; onSolve: () => void }) {
  const person = job.persons[job.pi]
  const [first = '', last = ''] = job.typed.split(' ')
  const typing = job.status === 'running' && job.phase === 1
  const body = {
    idle: <p className="grid h-full place-items-center text-xs text-slate-400">Waiting for a worker…</p>,
    done: <p className="grid h-full place-items-center text-xs text-emerald-600">Session closed · job complete</p>,
    search: <p className="grid h-full place-items-center text-xs text-slate-500">Opening Search → Case Information…</p>,
    error: (
      <div className="grid h-full place-items-center text-center text-xs text-rose-600">
        <div><p className="text-2xl font-bold">500</p>CAP returned an error page</div>
      </div>
    ),
    results: (
      <div className="space-y-1.5 p-3">
        <p className="text-[10px] font-bold uppercase text-slate-500">Results — {person ? `${person.lastName}, ${person.firstName}` : ''}</p>
        {[0, 1, 2, 3].map((i) => <div key={i} className="h-4 rounded bg-slate-100" style={{ width: `${95 - i * 12}%` }} />)}
      </div>
    ),
    case: (
      <div className="space-y-1.5 p-3">
        <p className="text-[10px] font-bold uppercase text-slate-500">Case Summary</p>
        {[0, 1, 2, 3, 4].map((i) => <div key={i} className="flex gap-2"><div className="h-3 w-16 rounded bg-slate-200" /><div className="h-3 flex-1 rounded bg-slate-100" /></div>)}
      </div>
    ),
    form: (
      <div className="space-y-2 p-3">
        <p className="rounded bg-slate-600 px-2 py-1 text-[10px] font-bold uppercase text-white">Party Search</p>
        <NameInput label="First" value={first} typing={typing} />
        <NameInput label="Last" value={last} typing={typing} />
      </div>
    ),
    captcha: (
      <div className="grid h-full place-items-center p-3">
        <div className="flex items-center gap-3 rounded border border-slate-300 bg-slate-50 px-3 py-3 shadow-sm">
          <button onClick={onSolve} aria-label="I'm not a robot" className="size-6 cursor-pointer rounded-sm border-2 border-slate-400 bg-white hover:border-indigo-500" />
          <span className="text-xs text-slate-700">I'm not a robot</span>
          <span className="text-[8px] text-slate-400">reCAPTCHA</span>
        </div>
      </div>
    ),
  } as const
  return <div className="h-full bg-white">{body[job.page]}</div>
}

export function ScraperCard({ job, hovered, onHover, onSolve, onPopOut, standalone = false }: { job: Job; hovered: boolean; onHover: (id: string | null) => void; onSolve: (id: string) => void; onPopOut?: (id: string) => void; standalone?: boolean }) {
  const waiting = job.status === 'captcha'
  return (
    <article
      onMouseEnter={() => onHover(job.id)}
      onMouseLeave={() => onHover(null)}
      className={`relative flex h-full flex-col overflow-hidden rounded-2xl bg-slate-900 shadow-card ring-1 transition ${hovered ? 'ring-indigo-400' : 'ring-slate-900/10'}`}
    >
      <div className="flex items-center gap-2 bg-slate-800 px-3 py-1.5 pl-16">
        <Lock size={11} className="text-slate-400" />
        <span className="flex-1 truncate rounded bg-slate-700 px-2 py-0.5 font-mono text-[10px] text-slate-300">cap.sb-court.org/search</span>
        <span className="w-7" />
      </div>

      {/* top-left: job id badge (same id as the report); top-right: pane menu */}
      <span className="absolute left-2 top-1.5 z-10 rounded-md bg-black/35 px-1.5 py-0.5 text-white backdrop-blur-sm"><JobId id={job.id} /></span>
      <div className="absolute right-1.5 top-1 z-10">
        {!standalone && onPopOut && (
          <DotsMenu dark items={[{ label: 'Open in separate tab', icon: <ExternalLink size={14} />, onClick: () => onPopOut(job.id) }]} />
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-hidden"><FauxCap job={job} onSolve={() => onSolve(job.id)} /></div>

      <div className={`flex items-center gap-2 px-3 py-1.5 text-[11px] ${waiting ? 'bg-amber-400 text-amber-950' : 'bg-slate-800 text-slate-400'}`}>
        <span className={`size-1.5 rounded-full ${waiting ? 'bg-amber-900' : job.status === 'running' ? 'animate-pulse bg-emerald-400' : 'bg-slate-500'}`} />
        {waiting ? 'Your turn: click “I’m not a robot” in the page above' : job.status === 'running' ? 'Live · simulated screencast' : job.status === 'done' ? 'Finished' : 'Queued'}
      </div>
    </article>
  )
}
