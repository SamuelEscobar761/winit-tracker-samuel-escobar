import { useEffect, useRef } from 'react'
import { Loader2 } from 'lucide-react'
import type { JobEvent } from '../../shared/api/api-types'
import { formatClock } from '../../shared/lib/format'
import { feedToneOf, type FeedTone } from '../job/job-events'

const DOT_COLORS: Record<FeedTone, string> = {
  search: 'bg-indigo-500',
  found: 'bg-emerald-500',
  warning: 'bg-amber-500',
  error: 'bg-rose-500',
  info: 'bg-slate-300',
  done: 'bg-emerald-600',
}

interface EventFeedProps {
  events: JobEvent[]
  emptyLabel: string
}

export function EventFeed({ events, emptyLabel }: EventFeedProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const lastId = events[events.length - 1]?.id

  useEffect(() => {
    const container = containerRef.current
    if (container) container.scrollTop = container.scrollHeight
  }, [lastId])

  return (
    <div
      ref={containerRef}
      role="log"
      aria-label="Live activity"
      className="mx-4 mb-3 max-h-28 space-y-1.5 overflow-y-auto rounded-xl bg-slate-50 p-3"
    >
      {events.length === 0 && (
        <p className="flex items-center gap-2 text-xs text-slate-400">
          <Loader2 size={12} className="animate-spin" /> {emptyLabel}
        </p>
      )}
      {events.map((event) => (
        <p key={event.id} className="flex items-start gap-2 text-xs text-slate-600">
          <span className="w-16 shrink-0 font-mono text-slate-400">{formatClock(event.timestamp)}</span>
          <span className={`mt-1.5 size-1.5 shrink-0 rounded-full ${DOT_COLORS[feedToneOf(event.type)]}`} />
          <span>{event.message}</span>
        </p>
      ))}
    </div>
  )
}
