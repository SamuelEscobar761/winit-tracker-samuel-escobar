import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'
import type { PersonView } from '../../shared/api/api-types'
import { Badge } from '../../shared/ui/badge'
import type { CaseRow } from '../report/case-row'
import { ExplainPanel } from '../ai/explain-panel'
import { MatchBadge } from '../report/match-badge'
import { StatusBadge } from '../report/status-badge'
import { CaseFacts, DetailSections, DetailStatus, MatchReasons } from './detail-sections'
import { RawSourcePanel } from './raw-source-panel'
import { useRawCase } from './use-raw-case'

interface CaseDrawerProps {
  jobId: string
  row: CaseRow
  persons: Record<number, PersonView>
  onClose: () => void
}

export function CaseDrawer({ jobId, row, persons, onClose }: CaseDrawerProps) {
  const panelRef = useRef<HTMLElement>(null)
  const person = persons[row.personIndex]
  const current = person?.cases.find((item) => item.case_key === row.case_key) ?? row
  const live: CaseRow = { ...row, ...current }
  const raw = useRawCase(
    { jobId, personIndex: row.personIndex, caseKey: row.case_key },
    `${live.detail ? 'detail' : 'search'}`,
  )

  useEffect(() => {
    panelRef.current?.focus()
    const close = (event: KeyboardEvent) => event.key === 'Escape' && onClose()
    document.addEventListener('keydown', close)
    return () => document.removeEventListener('keydown', close)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-slate-900/30 backdrop-blur-[2px]" onClick={onClose}>
      <aside
        ref={panelRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label={`Case ${live.case_number}`}
        onClick={(event) => event.stopPropagation()}
        className="animate-slide-in flex h-full w-full max-w-5xl flex-col bg-white shadow-pop outline-none"
      >
        <header className="flex items-start gap-3 border-b border-slate-100 px-6 py-4">
          <div className="min-w-0 flex-1">
            <p className="font-mono text-xs text-slate-400">{live.case_number}</p>
            <h2 className="truncate text-lg font-semibold text-slate-900">{live.caption}</h2>
            <div className="mt-2 flex flex-wrap gap-1.5">
              <StatusBadge status={live.status} isRestricted={live.is_restricted} />
              <MatchBadge value={live.match_label} />
              <Badge>{live.personName}</Badge>
            </div>
          </div>
          <button
            type="button"
            aria-label="Close"
            onClick={onClose}
            className="grid size-8 place-items-center rounded-lg text-slate-500 hover:bg-slate-100"
          >
            <X size={18} />
          </button>
        </header>
        <div className="grid min-h-0 flex-1 overflow-hidden md:grid-cols-2">
          <section className="space-y-6 overflow-y-auto p-6">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Parsed</h3>
            <MatchReasons row={live} />
            <ExplainPanel jobId={jobId} personIndex={row.personIndex} caseKey={row.case_key} />
            <CaseFacts row={live} />
            {live.detail ? <DetailSections detail={live.detail} /> : <DetailStatus row={live} />}
          </section>
          <section className="flex min-h-0 flex-col border-l border-slate-100 bg-slate-950 p-6 text-slate-300">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Raw source (portal JSON)
            </h3>
            <RawSourcePanel state={raw} />
          </section>
        </div>
      </aside>
    </div>
  )
}
