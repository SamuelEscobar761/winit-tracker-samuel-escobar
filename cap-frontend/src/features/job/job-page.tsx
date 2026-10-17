import { useState } from 'react'
import { SearchX } from 'lucide-react'
import type { PublicConfig } from '../../shared/api/api-types'
import { navigate } from '../../shared/routing/use-hash-route'
import { EmptyState } from '../../shared/ui/empty-state'
import { CaseDrawer } from '../case-detail/case-drawer'
import type { CaseRow } from '../report/case-row'
import type { Layout } from '../workspace/layout'
import { Workspace } from '../workspace/workspace'
import { AllResults } from './all-results'
import { JobHeader, type JobView } from './job-header'
import { laneSlots, portalStatus } from './job-events'
import { PortalBanner } from './portal-banner'
import { usePersonResults } from './use-person-results'
import { useJob } from './use-job'

interface JobPageProps {
  jobId: string
  provider: PublicConfig['provider'] | null
  onSignOut: (() => void) | null
}

function JobNotFound({ message }: { message: string }) {
  return (
    <div className="grid h-full place-items-center">
      <EmptyState
        tone="red"
        icon={<SearchX size={20} />}
        title="Job not available"
        hint={message}
        action={
          <button type="button" onClick={() => navigate('#/')} className="mt-2 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-medium text-white">
            Back to upload
          </button>
        }
      />
    </div>
  )
}

export function JobPage({ jobId, provider, onSignOut }: JobPageProps) {
  const job = useJob(jobId)
  const results = usePersonResults(jobId, job.snapshot?.people ?? [])
  const [view, setView] = useState<JobView>('workspace')
  const [layout, setLayout] = useState<Layout>(4)
  const [openCase, setOpenCase] = useState<CaseRow | null>(null)

  if (job.loadError && !job.snapshot) return <JobNotFound message={job.loadError} />
  if (!job.snapshot) return <div className="grid h-full place-items-center text-sm text-slate-400">Loading the job…</div>
  const snapshot = job.snapshot
  const lanes = laneSlots(job.events, snapshot.people, snapshot.parallelism)

  return (
    <div className="flex h-full flex-col">
      <JobHeader
        job={snapshot}
        provider={provider}
        view={view}
        onViewChange={setView}
        layout={layout}
        onLayoutChange={setLayout}
        onCancel={job.cancel}
        onRetryFailed={job.retryFailed}
        onNewRun={() => navigate('#/')}
        onSignOut={onSignOut}
      />
      <PortalBanner portal={portalStatus(job.events)} stream={job.streamState} />
      {view === 'workspace' ? (
        <Workspace job={snapshot} events={job.events} results={results} lanes={lanes} layout={layout} onOpenCase={setOpenCase} />
      ) : (
        <AllResults job={snapshot} results={results} onOpenCase={setOpenCase} />
      )}
      {openCase && <CaseDrawer jobId={jobId} row={openCase} persons={results} onClose={() => setOpenCase(null)} />}
    </div>
  )
}
