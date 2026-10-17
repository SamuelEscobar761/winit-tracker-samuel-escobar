import type { ReactNode } from 'react'
import { X } from 'lucide-react'
import { rawFor } from './data'
import type { CaseRow } from './sim'
import { Badge, ConfidenceBadge } from './ui'

const Field = ({ label, children }: { label: string; children: ReactNode }) => (
  <div>
    <dt className="text-[11px] font-medium uppercase tracking-wide text-slate-400">{label}</dt>
    <dd className="mt-0.5 text-sm text-slate-800">{children}</dd>
  </div>
)

export function CaseDrawer({ row, onClose }: { row: CaseRow; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-slate-900/30 backdrop-blur-[2px]" onClick={onClose}>
      <aside onClick={(e) => e.stopPropagation()} className="animate-slide-in flex h-full w-full max-w-5xl flex-col bg-white shadow-pop">
        <header className="flex items-start gap-3 border-b border-slate-100 px-6 py-4">
          <div className="min-w-0 flex-1">
            <p className="font-mono text-xs text-slate-400">{row.caseNumber} · {row.jobId}</p>
            <h2 className="truncate text-lg font-semibold text-slate-900">{row.title}</h2>
            <div className="mt-2 flex flex-wrap gap-1.5">
              <Badge tone="indigo">{row.type}</Badge>
              <Badge>{row.status}</Badge>
              <ConfidenceBadge value={row.confidence} />
              {row.limited && <Badge tone="amber">Limited online data</Badge>}
            </div>
          </div>
          <button aria-label="Close" onClick={onClose} className="grid size-8 place-items-center rounded-lg text-slate-500 hover:bg-slate-100"><X size={18} /></button>
        </header>

        <div className="grid min-h-0 flex-1 gap-0 overflow-hidden md:grid-cols-2">
          <section className="space-y-6 overflow-y-auto p-6">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Parsed</h3>
            <div className="rounded-xl bg-slate-50 p-4 ring-1 ring-slate-100">
              <p className="text-xs font-semibold text-slate-700">Why this match?</p>
              <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-slate-600">
                {row.reasons.map((r) => <li key={r}>{r}</li>)}
              </ul>
              <p className="mt-2 text-[11px] text-slate-400">Searched as: {row.personName}</p>
            </div>
            <dl className="grid grid-cols-2 gap-4">
              <Field label="Filing date">{row.filingDate}</Field>
              <Field label="Next hearing">{row.nextHearing ?? '—'}</Field>
              <Field label="Court location">{row.location}</Field>
              <Field label="Case type">{row.type}</Field>
            </dl>
            <div>
              <h4 className="mb-2 text-xs font-semibold text-slate-700">Parties</h4>
              {row.parties.map((p) => <p key={p.name} className="text-sm text-slate-700">{p.name} <span className="text-slate-400">· {p.role}{p.dob ? ` · DOB ${p.dob}` : ' · DOB not shown'}</span></p>)}
            </div>
            <div>
              <h4 className="mb-2 text-xs font-semibold text-slate-700">Charges</h4>
              {row.charges.length ? row.charges.map((c) => <p key={c.code} className="text-sm text-slate-700"><span className="font-mono text-xs">{c.code}</span> {c.description} <Badge>{c.severity}</Badge></p>)
                : <p className="text-sm text-slate-400">{row.limited ? 'Not available online for criminal cases (CRC 2.503).' : 'None shown by CAP.'}</p>}
            </div>
            <div>
              <h4 className="mb-2 text-xs font-semibold text-slate-700">Hearings</h4>
              <ul className="space-y-1.5">
                {row.hearings.map((h) => (
                  <li key={h.date + h.type} className="flex items-center gap-2 text-sm text-slate-700">
                    <span className={`size-2 rounded-full ${h.past ? 'bg-slate-300' : 'bg-emerald-500'}`} />
                    {h.date} {h.time} · Dept {h.dept} · {h.type}
                    {!h.past && <Badge tone="green">Upcoming</Badge>}
                  </li>
                ))}
              </ul>
            </div>
          </section>
          <section className="flex min-h-0 flex-col border-l border-slate-100 bg-slate-950 p-6 text-slate-300">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Raw source (CAP HTML snapshot)</h3>
            <pre className="min-h-0 flex-1 overflow-auto whitespace-pre-wrap font-mono text-xs leading-relaxed">{rawFor(row)}</pre>
            <p className="mt-3 text-[11px] text-slate-500">Source: https://cap.sb-court.org/search · scraped_at {new Date().toISOString().slice(0, 19)}Z</p>
          </section>
        </div>
      </aside>
    </div>
  )
}
