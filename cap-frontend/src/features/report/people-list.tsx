import { CheckCircle2, CircleDashed, Loader2, ShieldAlert, XCircle } from 'lucide-react'
import type { PersonState, PersonSummary } from '../../shared/api/api-types'
import { fullName, pluralize } from '../../shared/lib/format'

const STATE_ICONS: Record<PersonState, React.ReactNode> = {
  queued: <CircleDashed size={14} className="text-slate-300" />,
  running: <Loader2 size={14} className="animate-spin text-indigo-500" />,
  done: <CheckCircle2 size={14} className="text-emerald-500" />,
  failed: <XCircle size={14} className="text-rose-500" />,
  blocked_captcha: <ShieldAlert size={14} className="text-amber-500" />,
  cancelled: <XCircle size={14} className="text-slate-400" />,
}

function describe(person: PersonSummary): string {
  if (person.failure_reason) return person.failure_reason
  if (person.state === 'queued') return 'Waiting'
  const details = person.eligible_for_details
    ? ` · details ${person.details_loaded}/${person.eligible_for_details}`
    : ''
  return `${pluralize(person.cases_found, 'case')}${details}`
}

export function PeopleList({ people }: { people: PersonSummary[] }) {
  if (people.length === 0) return null
  return (
    <ul className="mx-4 mb-3 max-h-24 divide-y divide-slate-100 overflow-y-auto rounded-xl ring-1 ring-slate-100">
      {people.map((person) => (
        <li key={person.index} className="flex items-center gap-2 px-3 py-1.5 text-xs">
          {STATE_ICONS[person.state]}
          <span className="font-medium text-slate-800">{fullName(person)}</span>
          {person.date_of_birth && <span className="text-slate-400">DOB {person.date_of_birth}</span>}
          <span className={`ml-auto truncate ${person.failure_reason ? 'text-rose-600' : 'text-slate-500'}`}>
            {describe(person)}
          </span>
        </li>
      ))}
    </ul>
  )
}
