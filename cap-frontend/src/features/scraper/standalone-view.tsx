import { ArrowLeft } from 'lucide-react'
import { liveHash } from '../../shared/routing/hash-route'
import { navigate } from '../../shared/routing/use-hash-route'
import { Badge } from '../../shared/ui/badge'
import { ScraperCard } from './scraper-card'

export function StandaloneView({ lane }: { lane: number }) {
  return (
    <div className="mx-auto flex h-full max-w-5xl flex-col p-6">
      <div className="mb-3 flex items-center gap-3 text-xs text-slate-500">
        <button
          type="button"
          onClick={() => navigate('#/')}
          className="inline-flex items-center gap-1 rounded-lg px-2 py-1 hover:bg-slate-200"
        >
          <ArrowLeft size={14} /> Home
        </button>
        <span>Standalone live view</span>
        <Badge>{liveHash(lane)}</Badge>
      </div>
      <div className="min-h-0 flex-1">
        <ScraperCard lane={lane} slot={lane} isHovered={false} onHover={() => undefined} />
      </div>
    </div>
  )
}
