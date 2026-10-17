import { Loader2 } from 'lucide-react'
import type { JobEvent, JobSnapshot, PersonView } from '../../shared/api/api-types'
import { Badge } from '../../shared/ui/badge'
import { ProgressBar } from '../../shared/ui/progress-bar'
import { SkeletonRows } from '../../shared/ui/skeleton-rows'
import { fullName, pluralize, shortJobId } from '../../shared/lib/format'
import { feedEvents, isCaptchaPending } from '../job/job-events'
import type { CaseRow } from './case-row'
import { CasesTable } from './cases-table'
import { EventFeed } from './event-feed'
import { laneLabel } from './lane-label'
import { PeopleList } from './people-list'
import { CaptchaBanner, NoCasesState, PortalFailureState, QueuedState } from './report-states'
import { summarizeLane, type LaneSummary } from './lane-summary'

interface ReportCardProps {
  lane: number | null
  slot: number
  job: JobSnapshot
  events: JobEvent[]
  results: Record<number, PersonView>
  isHovered: boolean
  onHover: (slot: number | null) => void
  onOpenCase: (row: CaseRow) => void
}

function Title({ summary, lane }: { summary: LaneSummary; lane: number | null }) {
  if (lane === null) return <>Waiting for a free worker…</>
  if (summary.running) return <>Searching {fullName(summary.running)}…</>
  return <>{summary.isIdle ? 'Worker idle' : 'Report'}</>
}

function Body({ summary, lane }: { summary: LaneSummary; lane: number | null }) {
  if (lane === null || summary.people.length === 0) return <QueuedState />
  if (summary.rows.length > 0) return null
  if (summary.allFailed) return <PortalFailureState />
  if (summary.isIdle && !summary.hasCases) return <NoCasesState />
  return <SkeletonRows count={2} />
}

export function ReportCard({ lane, slot, job, events, results, isHovered, onHover, onOpenCase }: ReportCardProps) {
  const summary = summarizeLane(job.people, lane, results)
  const percent = summary.people.length ? Math.round((summary.finished / summary.people.length) * 100) : 0
  const laneEvents = feedEvents(events, lane, false)
  const waiting = isCaptchaPending(events, lane)

  return (
    <article
      onMouseEnter={() => onHover(slot)}
      onMouseLeave={() => onHover(null)}
      aria-label={`Report ${laneLabel(slot)}`}
      className={`overflow-hidden rounded-2xl bg-white shadow-card ring-1 transition ${isHovered ? 'ring-indigo-400' : 'ring-slate-200/70'}`}
    >
      <header className="flex items-center gap-3 px-4 pt-4">
        <span className="rounded-md bg-slate-900 px-2 py-1 font-mono text-xs font-medium text-white">
          {laneLabel(slot)}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-slate-900">
            <Title summary={summary} lane={lane} />
          </p>
          <p className="text-xs text-slate-500">
            Job {shortJobId(job.job_id)} · {summary.finished} of {pluralize(summary.people.length, 'person', 'people')} ·{' '}
            {pluralize(summary.rows.length, 'case')}
            {summary.failed.length > 0 && ` · ${summary.failed.length} failed`}
          </p>
        </div>
        {summary.running ? (
          <Badge tone="indigo">
            <Loader2 size={11} className="animate-spin" /> Running
          </Badge>
        ) : (
          <Badge tone={summary.isIdle ? 'green' : 'slate'}>{summary.isIdle ? 'Idle' : 'Queued'}</Badge>
        )}
      </header>
      <div className="px-4 pb-3 pt-3">
        <ProgressBar percent={percent} label={`Progress of ${laneLabel(slot)}`} />
      </div>
      {waiting && <CaptchaBanner />}
      <EventFeed events={laneEvents} emptyLabel="Waiting for a free worker…" />
      <PeopleList people={summary.people} />
      {summary.rows.length > 0 && <CasesTable rows={summary.rows} onOpen={onOpenCase} />}
      <Body summary={summary} lane={lane} />
    </article>
  )
}
