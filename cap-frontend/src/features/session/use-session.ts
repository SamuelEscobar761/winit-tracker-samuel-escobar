import { useCallback, useEffect, useState } from 'react'
import type { SessionInfo } from '../../shared/api/api-types'
import { sessionApi } from '../../shared/api/jobs-api'

export type SessionState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; info: SessionInfo }

const UNREACHABLE: SessionState = { status: 'error', message: 'The server is not reachable.' }

export function useSession() {
  const [state, setState] = useState<SessionState>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false
    sessionApi
      .get()
      .then((info) => !cancelled && setState({ status: 'ready', info }))
      .catch(() => !cancelled && setState(UNREACHABLE))
    return () => {
      cancelled = true
    }
  }, [])

  const refresh = useCallback(async () => {
    try {
      setState({ status: 'ready', info: await sessionApi.get() })
    } catch {
      setState(UNREACHABLE)
    }
  }, [])
  const login = useCallback(
    async (token: string) => {
      await sessionApi.login(token)
      await refresh()
    },
    [refresh],
  )
  const logout = useCallback(async () => {
    await sessionApi.logout()
    await refresh()
  }, [refresh])

  return { state, login, logout }
}
