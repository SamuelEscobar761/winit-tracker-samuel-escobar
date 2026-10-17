import type { ReactNode } from 'react'
import { Inbox } from 'lucide-react'
import { EmptyState } from '../../shared/ui/empty-state'

interface PaneListProps<T> {
  title: string
  items: T[]
  fit?: boolean
  keyOf: (item: T) => number
  children: (item: T) => ReactNode
}

export function PaneList<T>({ title, items, fit = false, keyOf, children }: PaneListProps<T>) {
  const layout = fit ? 'flex snap-y snap-mandatory flex-col gap-3' : 'space-y-3'
  return (
    <section
      aria-label={title}
      className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-3xl bg-slate-200/50 ring-1 ring-slate-200"
    >
      <h2 className="px-4 pb-1 pt-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
        {title} · {items.length}
      </h2>
      <div className={`min-h-0 flex-1 overflow-y-auto p-3 pt-1 ${layout}`}>
        {items.length ? (
          items.map((item) => (
            <div key={keyOf(item)} className={fit ? 'h-full shrink-0 snap-start' : ''}>
              {children(item)}
            </div>
          ))
        ) : (
          <EmptyState icon={<Inbox size={20} />} title="No jobs to show" hint="Raise the parallelism or switch to the 2-pane layout." />
        )}
      </div>
    </section>
  )
}
