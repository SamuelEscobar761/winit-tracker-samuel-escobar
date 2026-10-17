import { useState, type ReactNode } from 'react'
import { Inbox } from 'lucide-react'
import type { CaseRow, Job } from './sim'
import { splitJobs, type Layout } from './layout'
import { ReportCard } from './ReportCard'
import { ScraperCard } from './ScraperCard'
import { CaseDrawer } from './CaseDrawer'
import { EmptyState } from './ui'

// fit: every item is exactly one pane tall (scroll-snap), so a single view never needs scrolling.
function Pane({ title, jobs, fit = false, children }: { title: string; jobs: Job[]; fit?: boolean; children: (j: Job) => ReactNode }) {
  return (
    <section className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-3xl bg-slate-200/50 ring-1 ring-slate-200">
      <h2 className="px-4 pb-1 pt-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">{title} · {jobs.length}</h2>
      <div className={`min-h-0 flex-1 overflow-y-auto p-3 pt-1 ${fit ? 'flex snap-y snap-mandatory flex-col gap-3' : 'space-y-3'}`}>
        {jobs.length ? jobs.map((j) => <div key={j.id} className={fit ? 'h-full shrink-0 snap-start' : ''}>{children(j)}</div>) : (
          <EmptyState icon={<Inbox size={20} />} title="No jobs to show" hint="Start more jobs or switch to the 2-pane layout." />
        )}
      </div>
    </section>
  )
}

export function Workspace({ jobs, layout, onSolve }: { jobs: Job[]; layout: Layout; onSolve: (id: string) => void }) {
  const [hovered, setHovered] = useState<string | null>(null)
  const [open, setOpen] = useState<CaseRow | null>(null)
  const groups = splitJobs(jobs, layout)
  const popOut = (id: string) => window.open(`${location.pathname}#/view/${id}`, '_blank')
  const names = layout === 2 ? [''] : ['· top', '· bottom']

  return (
    <div className="grid min-h-0 flex-1 grid-cols-2 gap-3 p-3">
      <div className="flex min-h-0 flex-col gap-3">
        {groups.map((g, i) => (
          <Pane key={i} title={`Reports ${names[i]}`} jobs={g}>
            {(j) => <ReportCard job={j} hovered={hovered === j.id} onHover={setHovered} onOpenCase={setOpen} />}
          </Pane>
        ))}
      </div>
      <div className="flex min-h-0 flex-col gap-3">
        {groups.map((g, i) => (
          <Pane key={i} fit title={`Live scraping ${names[i]}`} jobs={g}>
            {(j) => <ScraperCard job={j} hovered={hovered === j.id} onHover={setHovered} onSolve={onSolve} onPopOut={popOut} />}
          </Pane>
        ))}
      </div>
      {open && <CaseDrawer row={open} onClose={() => setOpen(null)} />}
    </div>
  )
}
