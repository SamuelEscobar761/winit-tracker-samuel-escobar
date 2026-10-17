import { useEffect, useRef, useState, type ReactNode } from 'react'
import { MoreVertical } from 'lucide-react'
import type { Confidence } from './data'
import type { JobStatus } from './sim'

const TONES = {
  slate: 'bg-slate-100 text-slate-600 ring-slate-200',
  indigo: 'bg-indigo-50 text-indigo-700 ring-indigo-200',
  green: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  amber: 'bg-amber-50 text-amber-700 ring-amber-200',
  red: 'bg-rose-50 text-rose-700 ring-rose-200',
}
export type Tone = keyof typeof TONES

export const Badge = ({ tone = 'slate', children }: { tone?: Tone; children: ReactNode }) => (
  <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${TONES[tone]}`}>
    {children}
  </span>
)

const CONF: Record<Confidence, { tone: Tone; label: string }> = {
  confirmed: { tone: 'green', label: 'Confirmed' },
  probable: { tone: 'indigo', label: 'Probable' },
  possible: { tone: 'amber', label: 'Possible' },
}
export const ConfidenceBadge = ({ value }: { value: Confidence }) => (
  <Badge tone={CONF[value].tone}>{CONF[value].label}</Badge>
)

const JOB: Record<JobStatus, { tone: Tone; label: string }> = {
  queued: { tone: 'slate', label: 'Queued' },
  running: { tone: 'indigo', label: 'Running' },
  captcha: { tone: 'amber', label: 'CAPTCHA required' },
  done: { tone: 'green', label: 'Complete' },
}
export const JobBadge = ({ status }: { status: JobStatus }) => (
  <Badge tone={JOB[status].tone}>
    {status === 'running' && <span className="size-1.5 animate-pulse rounded-full bg-indigo-500" />}
    {JOB[status].label}
  </Badge>
)

export const JobId = ({ id, className = '' }: { id: string; className?: string }) => (
  <span className={`font-mono text-xs font-medium tracking-tight ${className}`}>{id}</span>
)

export function DotsMenu({ items, dark = false }: { items: { label: string; onClick: () => void; icon?: ReactNode }[]; dark?: boolean }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!open) return
    const close = (e: MouseEvent) => !ref.current?.contains(e.target as Node) && setOpen(false)
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [open])
  return (
    <div ref={ref} className="relative">
      <button
        aria-label="Pane menu"
        onClick={() => setOpen((o) => !o)}
        className={`grid size-7 place-items-center rounded-md transition ${dark ? 'text-white/80 hover:bg-white/20' : 'text-slate-500 hover:bg-slate-100'}`}
      >
        <MoreVertical size={16} />
      </button>
      {open && (
        <div className="animate-fade-in absolute right-0 z-20 mt-1 w-52 overflow-hidden rounded-xl bg-white p-1 shadow-pop ring-1 ring-slate-200">
          {items.map((it) => (
            <button
              key={it.label}
              onClick={() => {
                setOpen(false)
                it.onClick()
              }}
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
            >
              {it.icon}
              {it.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export const EmptyState = ({ icon, title, hint, tone = 'slate', action }: { icon: ReactNode; title: string; hint?: string; tone?: Tone; action?: ReactNode }) => (
  <div className="animate-fade-in flex flex-col items-center gap-2 px-6 py-10 text-center">
    <div className={`grid size-11 place-items-center rounded-2xl ring-1 ring-inset ${TONES[tone]}`}>{icon}</div>
    <p className="text-sm font-semibold text-slate-800">{title}</p>
    {hint && <p className="max-w-xs text-xs leading-relaxed text-slate-500">{hint}</p>}
    {action}
  </div>
)
