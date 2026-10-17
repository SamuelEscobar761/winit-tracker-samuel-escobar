import { useCallback, useEffect, useRef, useState } from 'react'
import type { JobEvent, JobSnapshot } from '../../shared/api/api-types'
import { SNAPSHOT_EVENT_TYPES } from '../../shared/api/event-types'
import { jobsApi } from '../../shared/api/jobs-api'
import { ApiError } from '../../shared/api/http-client'
import { appendEvents, emptyEventLog, type EventLog } from './job-events'
import { useEventStream } from './use-event-stream'

const REFRESH_DELAY_MS = 400

function useThrottledAction(action: () => void, delayMs: number) {
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)
  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current)
    },
    [],
  )
  return useCallback(() => {
    if (timer.current) return
    timer.current = setTimeout(() => {
      timer.current = null
      action()
    }, delayMs)
  }, [action, delayMs])
}

function describeError(error: unknown): string {
  if (error instanceof ApiError && error.status === 404) return 'This job does not exist (anymore).'
  return error instanceof Error ? error.message : 'The job could not be loaded.'
}

export function useJob(jobId: string) {
  const [snapshot, setSnapshot] = useState<JobSnapshot | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [log, setLog] = useState<EventLog>(emptyEventLog)
  const [streamKey, setStreamKey] = useState(0)

  const loadSnapshot = useCallback(() => {
    jobsApi
      .get(jobId)
      .then((value) => {
        setSnapshot(value)
        setLoadError(null)
      })
      .catch((error: unknown) => setLoadError(describeError(error)))
  }, [jobId])
  const scheduleRefresh = useThrottledAction(loadSnapshot, REFRESH_DELAY_MS)

  useEffect(() => {
    loadSnapshot()
  }, [loadSnapshot])

  const onBatch = useCallback(
    (batch: JobEvent[]) => {
      setLog((previous) => appendEvents(previous, batch))
      if (batch.some((event) => SNAPSHOT_EVENT_TYPES.has(event.type))) scheduleRefresh()
    },
    [scheduleRefresh],
  )
  const streamState = useEventStream(jobId, streamKey, onBatch)

  const cancel = useCallback(async () => setSnapshot(await jobsApi.cancel(jobId)), [jobId])
  const retryFailed = useCallback(async () => {
    setSnapshot(await jobsApi.retryFailed(jobId))
    setStreamKey((key) => key + 1)
  }, [jobId])
  const markCaptchaSolved = useCallback(
    (personIndex: number) => jobsApi.markCaptchaSolved(jobId, personIndex),
    [jobId],
  )

  return { snapshot, loadError, events: log.events, streamState, cancel, retryFailed, markCaptchaSolved }
}
