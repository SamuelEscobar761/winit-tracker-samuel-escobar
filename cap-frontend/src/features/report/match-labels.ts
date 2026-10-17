import type { MatchLabel } from '../../shared/api/api-types'
import type { Tone } from '../../shared/ui/tone'

export const MATCHES: Record<MatchLabel, { tone: Tone; label: string }> = {
  confirmed: { tone: 'green', label: 'Confirmed' },
  probable: { tone: 'indigo', label: 'Probable' },
  possible: { tone: 'amber', label: 'Possible' },
  unlikely: { tone: 'slate', label: 'Unlikely' },
}

export const MATCH_ORDER: Record<MatchLabel, number> = {
  confirmed: 0,
  probable: 1,
  possible: 2,
  unlikely: 3,
}

export const MATCH_OPTIONS = Object.entries(MATCHES).map(([value, { label }]) => ({ value, label }))
