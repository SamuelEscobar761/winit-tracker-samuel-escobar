import { useEffect, useState } from 'react'
import type { JobEvent } from '../../shared/api/api-types'
import { CLOSING_EVENT_TYPES, EVENT_TYPES } from '../../shared/api/event-types'

export type StreamState = 'connecting' | 'open' | 'reconnecting' | 'closed'

const FLUSH_INTERVAL_MS = 150

export function useEventStream(
  jobId: string,
  streamKey: number,
  onBatch: (events: JobEvent[]) => void,
): StreamState {
  const [state, setState] = useState<StreamState>('connecting')

  useEffect(() => {
    const source = new EventSource(`/jobs/${jobId}/events`, { withCredentials: true })
    let buffer: JobEvent[] = []

    const flush = () => {
      if (buffer.length === 0) return
      const batch = buffer
      buffer = []
      onBatch(batch)
    }
    const handle = (message: MessageEvent<string>) => {
      const event = JSON.parse(message.data) as JobEvent
      buffer.push(event)
      if (!CLOSING_EVENT_TYPES.has(event.type)) return
      flush()
      source.close()
      setState('closed')
    }

    EVENT_TYPES.forEach((type) => source.addEventListener(type, handle as EventListener))
    source.onopen = () => setState('open')
    source.onerror = () => setState(source.readyState === EventSource.CLOSED ? 'closed' : 'reconnecting')
    const timer = setInterval(flush, FLUSH_INTERVAL_MS)

    return () => {
      clearInterval(timer)
      source.close()
    }
  }, [jobId, streamKey, onBatch])

  return state
}
