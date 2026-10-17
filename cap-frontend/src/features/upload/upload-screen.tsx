import { Loader2, Play } from 'lucide-react'
import type { PublicConfig } from '../../shared/api/api-types'
import { RULES_HASH, jobHash } from '../../shared/routing/hash-route'
import { navigate } from '../../shared/routing/use-hash-route'
import { BrandMark } from '../../shared/ui/brand-mark'
import { DropZone } from './drop-zone'
import { RecentJobs } from './recent-jobs'
import { useUpload } from './use-upload'
import { ValidationReport } from './validation-report'

interface UploadScreenProps {
  config: PublicConfig | null
  onSignOut: (() => void) | null
}

interface ParallelismFieldProps {
  value: number
  max: number
  serverLimit: number
  ready: number
  onChange: (value: number) => void
}

function limitHint({ max, serverLimit, ready }: ParallelismFieldProps): string {
  if (ready > 0 && max < serverLimit) {
    const people = ready === 1 ? '1 person is' : `${ready} people are`
    return `Only ${people} ready, so more than ${max} worker${max === 1 ? '' : 's'} would sit idle (server limit: ${serverLimit}).`
  }
  return `Server limit: ${serverLimit}`
}

function ParallelismField(props: ParallelismFieldProps) {
  const { value, max, onChange } = props
  return (
    <label className="max-w-xs text-xs font-medium text-slate-600">
      Workers at the same time
      <input
        type="number"
        min={1}
        max={max}
        value={Math.min(value, max)}
        onChange={(event) => onChange(Math.min(max, Math.max(1, Number(event.target.value) || 1)))}
        className="mt-1 block w-28 rounded-xl bg-slate-100 px-3 py-2 text-sm outline-none focus:bg-white focus:ring-2 focus:ring-indigo-300"
      />
      <span className="mt-1 block text-[11px] font-normal text-slate-400">{limitHint(props)}</span>
    </label>
  )
}

export function UploadScreen({ config, onSignOut }: UploadScreenProps) {
  const upload = useUpload(config?.default_parallelism ?? 1)
  const serverLimit = config?.max_workers ?? 1
  const maxParallelism = upload.validation?.max_parallelism ?? serverLimit
  const ready = upload.validation?.ready_people ?? 0

  const start = async () => {
    const created = await upload.start()
    if (created) navigate(jobHash(created.job_id))
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto w-full max-w-3xl px-4 py-10">
        <div className="flex items-center justify-between">
          <BrandMark />
          <div className="flex items-center gap-4">
            <a href={RULES_HASH} className="text-xs text-slate-500 hover:text-slate-800">
              Portal rules
            </a>
            {onSignOut && (
              <button type="button" onClick={onSignOut} className="text-xs text-slate-500 hover:text-slate-800">
                Sign out
              </button>
            )}
          </div>
        </div>
        <h1 className="mt-8 text-3xl font-bold tracking-tight text-slate-900">Screen your drivers</h1>
        <p className="mt-2 text-sm text-slate-500">
          Upload a CSV and we search the San Bernardino Superior Court portal for each person, live.
        </p>
        <DropZone onFile={upload.chooseFile} fileName={upload.file?.name ?? null} />
        {upload.error && (
          <p role="alert" className="mt-4 rounded-xl bg-rose-50 p-3 text-sm text-rose-700 ring-1 ring-rose-200">
            {upload.error}
          </p>
        )}
        {upload.validation && <ValidationReport validation={upload.validation} />}
        <div className="mt-6 flex flex-wrap items-end gap-4 rounded-3xl bg-white p-5 shadow-card ring-1 ring-slate-200/70">
          <ParallelismField
            value={upload.parallelism}
            max={maxParallelism}
            serverLimit={serverLimit}
            ready={ready}
            onChange={upload.setParallelism}
          />
          <button
            type="button"
            disabled={ready === 0 || upload.isBusy}
            onClick={start}
            className="ml-auto inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
          >
            {upload.isBusy ? <Loader2 size={15} className="animate-spin" /> : <Play size={15} />}
            Start {ready ? `(${ready} people)` : ''}
          </button>
        </div>
        <RecentJobs />
      </div>
    </div>
  )
}
