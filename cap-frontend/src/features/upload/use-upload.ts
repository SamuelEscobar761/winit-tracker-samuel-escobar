import { useCallback, useState } from 'react'
import type { CreatedJob, ValidationResponse } from '../../shared/api/api-types'
import { ApiError } from '../../shared/api/http-client'
import { jobsApi } from '../../shared/api/jobs-api'

type UploadError = string | null

function describe(error: unknown): string {
  return error instanceof Error ? error.message : 'The file could not be processed.'
}

export function useUpload(defaultParallelism: number) {
  const [file, setFile] = useState<File | null>(null)
  const [validation, setValidation] = useState<ValidationResponse | null>(null)
  const [parallelism, setParallelism] = useState(defaultParallelism)
  const [isBusy, setIsBusy] = useState(false)
  const [error, setError] = useState<UploadError>(null)

  const chooseFile = useCallback(async (chosen: File) => {
    setFile(chosen)
    setValidation(null)
    setError(null)
    setIsBusy(true)
    try {
      setValidation(await jobsApi.validate(chosen))
    } catch (caught) {
      setError(describe(caught))
    } finally {
      setIsBusy(false)
    }
  }, [])

  const start = useCallback(async (): Promise<CreatedJob | null> => {
    if (!file) return null
    setIsBusy(true)
    setError(null)
    try {
      return await jobsApi.create(file, parallelism)
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : describe(caught))
      return null
    } finally {
      setIsBusy(false)
    }
  }, [file, parallelism])

  return { file, validation, parallelism, setParallelism, isBusy, error, chooseFile, start }
}
