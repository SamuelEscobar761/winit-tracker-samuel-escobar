import { Columns2, Grid2x2 } from 'lucide-react'
import type { Layout } from './layout'

interface LayoutSwitchProps {
  layout: Layout
  onChange: (layout: Layout) => void
}

export function LayoutSwitch({ layout, onChange }: LayoutSwitchProps) {
  return (
    <div className="flex rounded-lg bg-slate-100 p-0.5" role="group" aria-label="Layout">
      {([2, 4] as const).map((option) => (
        <button
          key={option}
          type="button"
          onClick={() => onChange(option)}
          aria-pressed={layout === option}
          className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition ${layout === option ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
        >
          {option === 2 ? <Columns2 size={14} /> : <Grid2x2 size={14} />} {option} panes
        </button>
      ))}
    </div>
  )
}
