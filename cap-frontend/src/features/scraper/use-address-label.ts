import { useEffect, useState } from 'react'
import { configApi } from '../../shared/api/jobs-api'

const LABELS = {
  live: 'cap.sb-court.org/traffic',
  replica: 'local replica of cap.sb-court.org/traffic',
  mock: 'simulated portal (no browser)',
} as const

export function useAddressLabel(): string {
  const [label, setLabel] = useState<string>(LABELS.live)

  useEffect(() => {
    let cancelled = false
    configApi
      .get()
      .then((config) => !cancelled && setLabel(LABELS[config.provider]))
      .catch(() => undefined)
    return () => {
      cancelled = true
    }
  }, [])

  return label
}
