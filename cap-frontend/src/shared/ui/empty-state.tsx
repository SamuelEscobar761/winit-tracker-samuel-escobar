import type { ReactNode } from 'react'
import { TONES, type Tone } from './tone'

interface EmptyStateProps {
  icon: ReactNode
  title: string
  hint?: string
  tone?: Tone
  action?: ReactNode
}

export function EmptyState({ icon, title, hint, tone = 'slate', action }: EmptyStateProps) {
  return (
    <div className="animate-fade-in flex flex-col items-center gap-2 px-6 py-10 text-center">
      <div className={`grid size-11 place-items-center rounded-2xl ring-1 ring-inset ${TONES[tone]}`}>
        {icon}
      </div>
      <p className="text-sm font-semibold text-slate-800">{title}</p>
      {hint && <p className="max-w-xs text-xs leading-relaxed text-slate-500">{hint}</p>}
      {action}
    </div>
  )
}
