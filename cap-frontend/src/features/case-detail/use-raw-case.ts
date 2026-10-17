import { useEffect, useState } from 'react'
import type { RawCase } from '../../shared/api/api-types'
import { jobsApi } from '../../shared/api/jobs-api'

export type RawCaseState =
  | { status: 'loading' }
  | { status: 'ready'; raw: RawCase }
  | { status: 'error' }

interface RawCaseRequest {
  jobId: string
  personIndex: number
  caseKey: string
}

export function useRawCase({ jobId, personIndex, caseKey }: RawCaseRequest, reloadKey: string): RawCaseState {
  const [state, setState] = useState<{ key: string; value: RawCaseState }>({
    key: '',
    value: { status: 'loading' },
  })
  const requestKey = `${jobId}/${personIndex}/${caseKey}/${reloadKey}`

  useEffect(() => {
    let cancelled = false
    jobsApi
      .getRawCase(jobId, personIndex, caseKey)
      .then((raw) => !cancelled && setState({ key: requestKey, value: { status: 'ready', raw } }))
      .catch(() => !cancelled && setState({ key: requestKey, value: { status: 'error' } }))
    return () => {
      cancelled = true
    }
  }, [jobId, personIndex, caseKey, requestKey])

  return state.key === requestKey ? state.value : { status: 'loading' }
}
