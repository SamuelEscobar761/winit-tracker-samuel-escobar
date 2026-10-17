import { useEffect, useState } from 'react'
import type { AiStatus } from '../../shared/api/api-types'
import { aiApi } from '../../shared/api/ai-api'

export function useAiStatus(): AiStatus | null {
  const [status, setStatus] = useState<AiStatus | null>(null)

  useEffect(() => {
    let cancelled = false
    aiApi
      .status()
      .then((value) => !cancelled && setStatus(value))
      .catch(() => undefined)
    return () => {
      cancelled = true
    }
  }, [])

  return status
}
