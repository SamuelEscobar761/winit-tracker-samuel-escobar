import { Scale } from 'lucide-react'

export function BrandMark() {
  return (
    <div className="flex items-center gap-2 font-semibold text-slate-900">
      <span className="grid size-7 place-items-center rounded-lg bg-slate-900 text-white">
        <Scale size={15} />
      </span>
      Court Case Tracker
    </div>
  )
}
