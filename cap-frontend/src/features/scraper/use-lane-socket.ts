import { useCallback, useEffect, useRef, useState } from 'react'
import type { InputEvent, InputOutcome, LaneStatus } from '../../shared/api/api-types'
import type { FrameSize } from './frame-input'

export type SocketState = 'connecting' | 'open' | 'reconnecting'

const RECONNECT_DELAY_MS = 1500

interface FrameMessage {
  type: 'frame'
  mime_type: string
  data: string
  width: number
  height: number
}

type ServerMessage =
  | FrameMessage
  | ({ type: 'status' } & LaneStatus)
  | { type: 'input'; outcome: InputOutcome }

function socketUrl(lane: number): string {
  const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${scheme}://${window.location.host}/ws/lanes/${lane}`
}

export function useLaneSocket(lane: number | null) {
  const imageRef = useRef<HTMLImageElement | null>(null)
  const frameSize = useRef<FrameSize>({ width: 0, height: 0 })
  const socketRef = useRef<WebSocket | null>(null)
  const [status, setStatus] = useState<LaneStatus | null>(null)
  const [state, setState] = useState<SocketState>('connecting')
  const [hasFrame, setHasFrame] = useState(false)
  const [lastOutcome, setLastOutcome] = useState<InputOutcome | null>(null)

  useEffect(() => {
    if (lane === null) return
    let stopped = false
    let retryTimer: ReturnType<typeof setTimeout> | undefined

    const handle = (message: ServerMessage) => {
      if (message.type === 'frame') {
        if (imageRef.current) imageRef.current.src = `data:${message.mime_type};base64,${message.data}`
        frameSize.current = { width: message.width, height: message.height }
        setHasFrame(true)
      } else if (message.type === 'status') {
        setStatus(message)
      } else {
        setLastOutcome(message.outcome)
      }
    }
    const connect = () => {
      const socket = new WebSocket(socketUrl(lane))
      socketRef.current = socket
      socket.onopen = () => setState('open')
      socket.onmessage = (event) => handle(JSON.parse(event.data as string) as ServerMessage)
      socket.onclose = () => {
        if (stopped) return
        setState('reconnecting')
        retryTimer = setTimeout(connect, RECONNECT_DELAY_MS)
      }
    }
    connect()

    return () => {
      stopped = true
      clearTimeout(retryTimer)
      socketRef.current?.close()
    }
  }, [lane])

  const sendInput = useCallback((event: InputEvent) => {
    const socket = socketRef.current
    if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(event))
  }, [])

  return { imageRef, frameSize, status, state, hasFrame, lastOutcome, sendInput }
}
