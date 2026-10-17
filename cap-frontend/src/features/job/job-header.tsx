import { useState } from 'react'
import { Ban, LogOut, RotateCcw, Upload } from 'lucide-react'
import type { JobSnapshot, PublicConfig } from '../../shared/api/api-types'
import { Badge } from '../../shared/ui/badge'
import { BrandMark } from '../../shared/ui/brand-mark'
import { ProgressBar } from '../../shared/ui/progress-bar'
import { LayoutSwitch } from '../workspace/layout-switch'
import type { Layout } from '../workspace/layout'

export type JobView = 'workspace' | 'results'

interface JobHeaderProps {
  job: JobSnapshot
  provider: PublicConfig['provider'] | null
  view: JobView
  onViewChange: (view: JobView) => void
  layout: Layout
  onLayoutChange: (layout: Layout) => void
  onCancel: () => Promise<void>
  onRetryFailed: () => Promise<void>
  onNewRun: () => void
  onSignOut: (() => void) | null
}

const PROVIDER_LABELS: Record<NonNullable<JobHeaderProps['provider']>, string> = {
  mock: 'Mock mode',
  replica: 'Mock mode · local portal replica',
  live: 'Live mode',
}

const VIEWS: { id: JobView; label: string }[] = [
  { id: 'workspace', label: 'Workspace' },
  { id: 'results', label: 'All results' },
]

function ViewTabs({ view, onChange }: { view: JobView; onChange: (view: JobView) => void }) {
  return (
    <div className="flex rounded-lg bg-slate-100 p-0.5" role="group" aria-label="View">
      {VIEWS.map((item) => (
        <button
          key={item.id}
          type="button"
          aria-pressed={view === item.id}
          onClick={() => onChange(item.id)}
          className={`rounded-md px-2.5 py-1 text-xs font-medium transition ${view === item.id ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
        >
          {item.label}
        </button>
      ))}
    </div>
  )
}

function ActionButton({ label, icon, onClick, disabled }: { label: string; icon: React.ReactNode; onClick: () => void; disabled: boolean }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-40"
    >
      {icon} {label}
    </button>
  )
}

function progressLabel(job: JobSnapshot): string {
  const { progress } = job
  if (job.state === 'cancelled') return 'Cancelled'
  const failed = progress.failed + progress.blocked_captcha
  if (job.state === 'completed' && failed > 0) return `Finished · ${failed} failed`
  if (job.state === 'completed') return `Complete · ${progress.total} people`
  return `${progress.finished} / ${progress.total} people`
}

export function JobHeader(props: JobHeaderProps) {
  const { job, provider, view, layout } = props
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const run = async (action: () => Promise<void>) => {
    setBusy(true)
    setError(null)
    try {
      await action()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'The action failed.')
    } finally {
      setBusy(false)
    }
  }
  const failed = job.progress.failed + job.progress.blocked_captcha
  const isActive = job.state === 'queued' || job.state === 'running'

  return (
    <header className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-slate-200 bg-white px-4 py-2.5">
      <BrandMark />
      {provider && <Badge tone={provider === 'live' ? 'green' : 'amber'}>{PROVIDER_LABELS[provider]}</Badge>}
      <div className="mx-2 flex min-w-48 flex-1 items-center gap-3">
        <ProgressBar percent={job.progress.percent} label="Job progress" />
        <span className="w-36 text-xs text-slate-500">{progressLabel(job)}</span>
      </div>
      {error && <span role="alert" className="text-xs text-rose-600">{error}</span>}
      <ViewTabs view={view} onChange={props.onViewChange} />
      {view === 'workspace' && <LayoutSwitch layout={layout} onChange={props.onLayoutChange} />}
      <ActionButton label="Retry failed" icon={<RotateCcw size={14} />} disabled={busy || failed === 0 || job.state === 'cancelled'} onClick={() => run(props.onRetryFailed)} />
      <ActionButton label="Cancel" icon={<Ban size={14} />} disabled={busy || !isActive} onClick={() => run(props.onCancel)} />
      <ActionButton label="New run" icon={<Upload size={14} />} disabled={false} onClick={props.onNewRun} />
      {props.onSignOut && <ActionButton label="Sign out" icon={<LogOut size={14} />} disabled={false} onClick={props.onSignOut} />}
    </header>
  )
}
