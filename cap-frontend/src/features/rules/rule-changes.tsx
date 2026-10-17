import type { RuleChange } from '../../shared/api/api-types'

const show = (value: unknown) => (typeof value === 'string' ? value : JSON.stringify(value))

export function RuleChanges({ changes }: { changes: RuleChange[] }) {
  if (changes.length === 0) return <p className="text-xs text-slate-400">No rule values changed.</p>
  return (
    <ul className="space-y-1 font-mono text-[11px]">
      {changes.map((change) => (
        <li key={change.path} className="break-all">
          <span className="text-slate-500">{change.path}</span>{' '}
          <span className="text-rose-600 line-through">{show(change.before)}</span>{' '}
          <span className="text-emerald-700">{show(change.after)}</span>
        </li>
      ))}
    </ul>
  )
}
