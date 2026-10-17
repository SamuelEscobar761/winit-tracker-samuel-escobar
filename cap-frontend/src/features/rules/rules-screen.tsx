import type { ReactNode } from 'react'
import { ArrowLeft } from 'lucide-react'
import { rulesApi } from '../../shared/api/ai-api'
import type { RulesOverview } from '../../shared/api/api-types'
import { navigate } from '../../shared/routing/use-hash-route'
import { Badge } from '../../shared/ui/badge'
import { BrandMark } from '../../shared/ui/brand-mark'
import { ChangeLog } from './change-log'
import { IncidentList } from './incident-list'
import { ProposalList } from './proposal-list'
import { useRules } from './use-rules'

function Section({ title, hint, children }: { title: string; hint?: string; children: ReactNode }) {
  return (
    <section className="mt-6 rounded-3xl bg-white p-5 shadow-card ring-1 ring-slate-200/70">
      <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
      {hint && <p className="mt-0.5 text-xs text-slate-500">{hint}</p>}
      <div className="mt-3">{children}</div>
    </section>
  )
}

function AiBanner({ ai }: { ai: RulesOverview['ai'] }) {
  if (!ai.available) {
    return <Badge tone="slate">AI off · changes are only recorded ({ai.reason})</Badge>
  }
  const policy = ai.rules_auto_apply ? 'verified repairs apply automatically' : 'repairs wait for approval'
  return (
    <Badge tone="indigo">
      AI on ({ai.mode}) · {policy}
    </Badge>
  )
}

export function RulesScreen() {
  const { state, actionError, act } = useRules()

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto w-full max-w-3xl px-4 py-10">
        <div className="flex items-center justify-between">
          <BrandMark />
          <button
            type="button"
            onClick={() => navigate('#/')}
            className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-800"
          >
            <ArrowLeft size={13} /> Back
          </button>
        </div>
        <h1 className="mt-8 text-3xl font-bold tracking-tight text-slate-900">Portal rules</h1>
        <p className="mt-2 text-sm text-slate-500">
          What the scraper knows about the court site lives here as data. When the site changes, the agent proposes new
          rules, proves them with a test search and records every change.
        </p>
        {actionError && (
          <p role="alert" className="mt-4 rounded-xl bg-rose-50 p-3 text-sm text-rose-700 ring-1 ring-rose-200">
            {actionError}
          </p>
        )}
        {state.status === 'loading' && <p className="mt-8 text-sm text-slate-400">Loading…</p>}
        {state.status === 'error' && (
          <p role="alert" className="mt-8 text-sm text-rose-600">
            {state.message}
          </p>
        )}
        {state.status === 'ready' && (
          <>
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <Badge tone="green">Active version {state.overview.active.version}</Badge>
              <AiBanner ai={state.overview.ai} />
            </div>
            <Section title="Waiting for review" hint="Proposals that need a person before they go live.">
              <ProposalList
                proposals={state.overview.proposals}
                onApprove={(id) => void act(() => rulesApi.approve(id))}
                onReject={(id) => void act(() => rulesApi.reject(id))}
              />
            </Section>
            <Section title="Portal changes detected" hint="Created when a step stops matching the site.">
              <IncidentList
                incidents={state.overview.incidents}
                ai={state.overview.ai}
                onRepair={(id) => void act(() => rulesApi.repair(id))}
              />
            </Section>
            <Section title="Change log" hint="Every version, who made it and why. Rolling back creates a new version.">
              <ChangeLog
                entries={state.overview.changelog}
                activeVersion={state.overview.active.version}
                onRollback={(version) => void act(() => rulesApi.rollback(version))}
              />
            </Section>
          </>
        )}
      </div>
    </div>
  )
}
