import { Lock } from 'lucide-react'
import { Badge } from '../../shared/ui/badge'
import type { Tone } from '../../shared/ui/tone'

const STATUS_TONES: Record<string, Tone> = {
  Active: 'indigo',
  'AR Fine': 'amber',
  Probation: 'amber',
  'Pending Adjudication': 'amber',
  'Traffic School Pending': 'amber',
  Inactive: 'slate',
  Closed: 'slate',
}

interface StatusBadgeProps {
  status: string
  isRestricted: boolean
}

export function StatusBadge({ status, isRestricted }: StatusBadgeProps) {
  if (isRestricted) {
    return (
      <Badge tone="red">
        <Lock size={10} /> {status}
      </Badge>
    )
  }
  return <Badge tone={STATUS_TONES[status] ?? 'slate'}>{status}</Badge>
}
