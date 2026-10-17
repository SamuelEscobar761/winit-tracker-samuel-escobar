import type { ReactNode } from 'react'
import { TONES, type Tone } from './tone'

interface BadgeProps {
  tone?: Tone
  children: ReactNode
}

export function Badge({ tone = 'slate', children }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${TONES[tone]}`}
    >
      {children}
    </span>
  )
}
