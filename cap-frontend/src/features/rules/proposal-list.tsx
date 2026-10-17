import type { RulesProposal } from '../../shared/api/api-types'
import { Badge } from '../../shared/ui/badge'
import { RuleChanges } from './rule-changes'

interface ProposalListProps {
  proposals: RulesProposal[]
  onApprove: (proposalId: string) => void
  onReject: (proposalId: string) => void
}

export function ProposalList({ proposals, onApprove, onReject }: ProposalListProps) {
  const pending = proposals.filter((proposal) => proposal.status === 'pending')
  if (pending.length === 0) return <p className="text-sm text-slate-400">Nothing is waiting for review.</p>
  return (
    <ul className="space-y-4">
      {pending.map((proposal) => (
        <li key={proposal.id} className="rounded-xl bg-amber-50/60 p-4 ring-1 ring-amber-200">
          <p className="text-sm font-medium text-slate-800">{proposal.diagnosis}</p>
          <div className="mt-2">
            <RuleChanges changes={proposal.changes} />
          </div>
          <p className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
            <Badge tone={proposal.canary.passed ? 'green' : 'red'}>
              canary {proposal.canary.passed ? 'passed' : 'failed'}
            </Badge>
            {proposal.canary.detail} · {proposal.model}
          </p>
          <div className="mt-3 flex gap-2">
            <button
              type="button"
              onClick={() => onApprove(proposal.id)}
              className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700"
            >
              Approve and activate
            </button>
            <button
              type="button"
              onClick={() => onReject(proposal.id)}
              className="rounded-lg px-3 py-1.5 text-xs font-medium text-slate-600 ring-1 ring-slate-200 hover:bg-white"
            >
              Reject
            </button>
          </div>
        </li>
      ))}
    </ul>
  )
}
