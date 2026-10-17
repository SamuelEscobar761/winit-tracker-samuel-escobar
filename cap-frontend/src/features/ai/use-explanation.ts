import { useState } from 'react'
import type { MatchExplanation } from '../../shared/api/api-types'
import { aiApi } from '../../shared/api/ai-api'

export type ExplanationState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'ready'; explanation: MatchExplanation }
  | { status: 'error'; message: string }

export function useExplanation(jobId: string, personIndex: number, caseKey: string) {
  const [state, setState] = useState<ExplanationState>({ status: 'idle' })

  const explain = async () => {
    setState({ status: 'loading' })
    try {
      const explanation = await aiApi.explainMatch(jobId, personIndex, caseKey)
      setState({ status: 'ready', explanation })
    } catch (caught) {
      setState({ status: 'error', message: caught instanceof Error ? caught.message : 'The request failed.' })
    }
  }

  return { state, explain }
}
