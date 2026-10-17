import { useEffect, useState } from 'react'
import type { PublicConfig } from '../../shared/api/api-types'
import { configApi } from '../../shared/api/jobs-api'

export function usePublicConfig(isAllowed: boolean): PublicConfig | null {
  const [config, setConfig] = useState<PublicConfig | null>(null)

  useEffect(() => {
    if (!isAllowed) return
    let cancelled = false
    configApi
      .get()
      .then((value) => !cancelled && setConfig(value))
      .catch(() => undefined)
    return () => {
      cancelled = true
    }
  }, [isAllowed])

  return isAllowed ? config : null
}
