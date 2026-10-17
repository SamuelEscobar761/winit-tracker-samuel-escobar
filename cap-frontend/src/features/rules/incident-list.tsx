import type { DriftIncident, IncidentStatus, RulesOverview } from '../../shared/api/api-types'
import { Badge } from '../../shared/ui/badge'
import type { Tone } from '../../shared/ui/tone'

const TONE: Record<IncidentStatus, Tone> = {
  open: 'amber',
  repairing: 'indigo',
  repaired: 'green',
  awaiting_review: 'amber',
  failed: 'red',
  dismissed: 'slate',
}

interface IncidentListProps {
  incidents: DriftIncident[]
  ai: RulesOverview['ai']
  onRepair: (incidentId: string) => void
}

export function IncidentList({ incidents, ai, onRepair }: IncidentListProps) {
  if (incidents.length === 0) return <p className="text-sm text-slate-400">No portal changes detected.</p>
  return (
    <ul className="divide-y divide-slate-100">
      {incidents.map((incident) => (
        <li key={incident.id} className="flex flex-wrap items-start gap-3 py-3">
          <Badge tone={TONE[incident.status]}>{incident.status.replace('_', ' ')}</Badge>
          <div className="min-w-0 flex-1">
            <p className="break-words text-xs text-slate-700">{incident.message}</p>
            <p className="mt-0.5 text-[11px] text-slate-400">
              {incident.kind} · rules v{incident.rules_version} · {new Date(incident.at).toLocaleString()}
              {incident.outcome ? ` · ${incident.outcome}` : ''}
            </p>
          </div>
          {ai.available && (incident.status === 'open' || incident.status === 'failed') && (
            <button
              type="button"
              onClick={() => onRepair(incident.id)}
              className="rounded-lg px-2.5 py-1 text-xs font-medium text-indigo-700 ring-1 ring-indigo-200 hover:bg-indigo-50"
            >
              Ask AI to repair
            </button>
          )}
        </li>
      ))}
    </ul>
  )
}
