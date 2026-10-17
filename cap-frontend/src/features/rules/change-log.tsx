import type { ChangeEntry } from '../../shared/api/api-types'
import { Badge } from '../../shared/ui/badge'
import { RuleChanges } from './rule-changes'

interface ChangeLogProps {
  entries: ChangeEntry[]
  activeVersion: number
  onRollback: (version: number) => void
}

export function ChangeLog({ entries, activeVersion, onRollback }: ChangeLogProps) {
  return (
    <ol className="space-y-4">
      {entries.map((entry) => (
        <li key={entry.version} className="rounded-xl p-4 ring-1 ring-slate-200">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-slate-900">Version {entry.version}</span>
            <Badge tone={entry.actor === 'agent' ? 'indigo' : 'slate'}>{entry.actor}</Badge>
            {entry.version === activeVersion && <Badge tone="green">active</Badge>}
            <span className="text-[11px] text-slate-400">{new Date(entry.at).toLocaleString()}</span>
            {entry.version !== activeVersion && (
              <button
                type="button"
                onClick={() => onRollback(entry.version)}
                className="ml-auto text-xs font-medium text-indigo-700 hover:underline"
              >
                Roll back to this version
              </button>
            )}
          </div>
          <p className="mt-1 text-xs text-slate-600">{entry.reason}</p>
          {entry.canary && (
            <p className="mt-1 text-[11px] text-slate-400">
              Canary: {entry.canary}
              {entry.model ? ` · ${entry.model}` : ''}
            </p>
          )}
          {entry.changes.length > 0 && (
            <div className="mt-2">
              <RuleChanges changes={entry.changes} />
            </div>
          )}
        </li>
      ))}
    </ol>
  )
}
