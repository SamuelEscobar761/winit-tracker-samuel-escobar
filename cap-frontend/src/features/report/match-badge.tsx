import type { MatchLabel } from '../../shared/api/api-types'
import { Badge } from '../../shared/ui/badge'
import { MATCHES } from './match-labels'

export function MatchBadge({ value }: { value: MatchLabel }) {
  return <Badge tone={MATCHES[value].tone}>{MATCHES[value].label}</Badge>
}
