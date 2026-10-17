import { useCallback, useEffect, useState } from 'react'
import type { RulesOverview } from '../../shared/api/api-types'
import { rulesApi } from '../../shared/api/ai-api'

export type RulesState =
  | { status: 'loading' }
  | { status: 'ready'; overview: RulesOverview }
  | { status: 'error'; message: string }

const messageOf = (caught: unknown, fallback: string) => (caught instanceof Error ? caught.message : fallback)

export function useRules() {
  const [state, setState] = useState<RulesState>({ status: 'loading' })
  const [actionError, setActionError] = useState<string | null>(null)
  const [reloadCount, setReloadCount] = useState(0)

  useEffect(() => {
    let cancelled = false
    rulesApi
      .overview()
      .then((overview) => !cancelled && setState({ status: 'ready', overview }))
      .catch((caught) => !cancelled && setState({ status: 'error', message: messageOf(caught, 'The request failed.') }))
    return () => {
      cancelled = true
    }
  }, [reloadCount])

  const act = useCallback(async (action: () => Promise<unknown>) => {
    setActionError(null)
    try {
      await action()
    } catch (caught) {
      setActionError(messageOf(caught, 'The action failed.'))
    }
    setReloadCount((count) => count + 1)
  }, [])

  return { state, actionError, act }
}
