import type { ReactNode } from 'react'
import { AlertTriangle, Lock } from 'lucide-react'
import { formatDate, formatMoney } from '../../shared/lib/format'
import type { CaseDetail } from '../../shared/api/api-types'
import { Badge } from '../../shared/ui/badge'
import type { CaseRow } from '../report/case-row'

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-[11px] font-medium uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className="mt-0.5 text-sm text-slate-800">{children}</dd>
    </div>
  )
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <h4 className="mb-2 text-xs font-semibold text-slate-700">{title}</h4>
      {children}
    </div>
  )
}

export function MatchReasons({ row }: { row: CaseRow }) {
  return (
    <div className="rounded-xl bg-slate-50 p-4 ring-1 ring-slate-100">
      <p className="text-xs font-semibold text-slate-700">Why this match?</p>
      <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-slate-600">
        {row.match_reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>
      <p className="mt-2 text-[11px] text-slate-400">Searched for: {row.personName}</p>
    </div>
  )
}

export function CaseFacts({ row }: { row: CaseRow }) {
  return (
    <dl className="grid grid-cols-2 gap-4">
      <Field label="File date (portal: violation date)">{formatDate(row.file_date)}</Field>
      <Field label="Citation number">{row.citation_number ?? '—'}</Field>
      <Field label="Date of birth">{formatDate(row.date_of_birth)}</Field>
      <Field label="Driver's license">{row.drivers_license ?? '—'}</Field>
      <Field label="Name on case">{row.caption}</Field>
      <Field label="Identity group">{row.groupLabel}</Field>
    </dl>
  )
}

function PlanSection({ detail }: { detail: CaseDetail }) {
  const plan = detail.payment_plan
  if (!plan) return null
  return (
    <Section title="Active payment plan">
      <dl className="grid grid-cols-3 gap-4">
        <Field label="Monthly">{formatMoney(plan.monthly_amount)}</Field>
        <Field label="Past due">{formatMoney(plan.past_amount_due)}</Field>
        <Field label="Remaining">{formatMoney(plan.remaining_balance)}</Field>
      </dl>
    </Section>
  )
}

export function DetailSections({ detail }: { detail: CaseDetail }) {
  return (
    <>
      <Section title="Charges">
        {detail.charges.length ? (
          detail.charges.map((charge) => (
            <p key={charge.statute} className="text-sm text-slate-700">
              <span className="font-mono text-xs">{charge.statute}</span> {charge.description}
            </p>
          ))
        ) : (
          <p className="text-sm text-slate-400">None shown by the portal.</p>
        )}
      </Section>
      <dl className="grid grid-cols-2 gap-4">
        <Field label="Amount due">{formatMoney(detail.amount_due)}</Field>
        <Field label="Proof of correction">
          {detail.proof_of_correction_required ? <Badge tone="amber">Required</Badge> : 'Not required'}
        </Field>
        {detail.is_extension_eligible && (
          <Field label="Extension">
            {formatDate(detail.original_date)} → {formatDate(detail.extended_date)}
          </Field>
        )}
      </dl>
      <PlanSection detail={detail} />
      {detail.notices.map((notice) => (
        <p key={notice} className="rounded-lg bg-amber-50 p-3 text-xs text-amber-800 ring-1 ring-amber-200">
          {notice}
        </p>
      ))}
    </>
  )
}

export function DetailStatus({ row }: { row: CaseRow }) {
  if (row.is_restricted) {
    return (
      <p className="flex items-start gap-2 rounded-lg bg-rose-50 p-3 text-xs text-rose-800 ring-1 ring-rose-200">
        <Lock size={14} className="mt-0.5 shrink-0" />
        The portal restricts this case. Its status and details are not shown or requested.
      </p>
    )
  }
  if (row.detail_error) {
    return (
      <p className="flex items-start gap-2 rounded-lg bg-amber-50 p-3 text-xs text-amber-800 ring-1 ring-amber-200">
        <AlertTriangle size={14} className="mt-0.5 shrink-0" />
        Details could not be loaded: {row.detail_error}
      </p>
    )
  }
  if (row.status === 'Closed') {
    return <p className="text-sm text-slate-400">Closed cases have no payment details on the portal.</p>
  }
  return <p className="animate-pulse text-sm text-slate-400">Details are being loaded…</p>
}
