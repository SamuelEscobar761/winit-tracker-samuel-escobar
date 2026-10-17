import { useEffect, useRef } from 'react'
import { AlertTriangle, CheckCircle2, FileSearch, Loader2, ShieldAlert, WifiOff } from 'lucide-react'
import type { CaseRow, EventKind, Job } from './sim'
import { CasesTable } from './CasesTable'
import { EmptyState, JobBadge, JobId } from './ui'

const DOT: Record<EventKind, string> = {
  search: 'bg-indigo-500',
  found: 'bg-emerald-500',
  captcha: 'bg-amber-500',
  error: 'bg-rose-500',
  info: 'bg-slate-300',
  done: 'bg-emerald-600',
}

export function ReportCard({ job, hovered, onHover, onOpenCase }: { job: Job; hovered: boolean; onHover: (id: string | null) => void; onOpenCase: (c: CaseRow) => void }) {
  const feedRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: 'smooth' })
  }, [job.events.length])

  const total = job.persons.length
  const finished = Object.keys(job.outcomes).length
  const pct = total ? Math.round((finished / total) * 100) : 100
  const failed = Object.values(job.outcomes).filter((o) => o === 'failed').length
  const allEmpty = job.status === 'done' && job.cases.length === 0

  return (
    <article
      onMouseEnter={() => onHover(job.id)}
      onMouseLeave={() => onHover(null)}
      className={`overflow-hidden rounded-2xl bg-white shadow-card ring-1 transition ${hovered ? 'ring-indigo-400' : 'ring-slate-200/70'}`}
    >
      <header className="flex items-center gap-3 px-4 pt-4">
        <span className="rounded-md bg-slate-900 px-2 py-1 text-white"><JobId id={job.id} /></span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-slate-900">
            {job.persons[job.pi] && job.status !== 'done' ? `Searching ${job.persons[job.pi].firstName} ${job.persons[job.pi].lastName}…` : 'Report'}
          </p>
          <p className="text-xs text-slate-500">{finished} of {total} people · {job.cases.length} cases{failed ? ` · ${failed} failed` : ''}</p>
        </div>
        <JobBadge status={job.status} />
      </header>

      <div className="px-4 pb-3 pt-3">
        <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-500" style={{ width: `${pct}%` }} />
        </div>
      </div>

      {job.status === 'captcha' && (
        <div className="mx-4 mb-3 flex items-start gap-2 rounded-xl bg-amber-50 p-3 text-xs text-amber-800 ring-1 ring-amber-200">
          <ShieldAlert size={16} className="mt-0.5 shrink-0" />
          <span><b>CAPTCHA required.</b> This job is paused until you solve it in the live view on the right.</span>
        </div>
      )}

      <div ref={feedRef} className="mx-4 mb-3 max-h-28 space-y-1.5 overflow-y-auto rounded-xl bg-slate-50 p-3">
        {job.events.length === 0 && <p className="flex items-center gap-2 text-xs text-slate-400"><Loader2 size={12} className="animate-spin" /> Waiting for a free worker…</p>}
        {job.events.map((e) => (
          <p key={e.id} className="animate-fade-in flex items-start gap-2 text-xs text-slate-600">
            <span className="w-9 shrink-0 font-mono text-slate-400">{e.t}</span>
            <span className={`mt-1.5 size-1.5 shrink-0 rounded-full ${DOT[e.kind]}`} />
            <span>{e.text}</span>
          </p>
        ))}
      </div>

      {job.cases.length > 0 ? (
        <CasesTable rows={job.cases} onOpen={onOpenCase} />
      ) : job.status === 'queued' ? (
        <div className="space-y-2 px-4 pb-5">
          {[0, 1, 2].map((i) => <div key={i} className="h-8 animate-pulse rounded-lg bg-slate-100" />)}
        </div>
      ) : allEmpty && failed === total ? (
        <EmptyState tone="red" icon={<WifiOff size={20} />} title="CAP is not responding" hint="Every search in this job failed. CAP may be down or in its 12:00–3:00 AM maintenance window." />
      ) : allEmpty ? (
        <EmptyState icon={<FileSearch size={20} />} title="No cases found" hint="CAP returned no public cases for these people. Criminal and family records are not available online (CRC 2.503)." />
      ) : null}

      {job.status === 'done' && job.cases.length > 0 && (
        <p className="flex items-center gap-2 border-t border-slate-100 px-4 py-2.5 text-xs text-slate-500">
          {failed ? <AlertTriangle size={14} className="text-rose-500" /> : <CheckCircle2 size={14} className="text-emerald-500" />}
          {failed ? `${failed} search failed — the rest completed. Retry available.` : 'All searches completed.'}
          <span className="ml-auto">Matches are candidates: no date of birth, so none is confirmed.</span>
        </p>
      )}
    </article>
  )
}
