import { useState, useCallback } from 'react'
import { apiRequest } from '../lib/api'

interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

export function useApi<T = unknown>() {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null
  })

  const execute = useCallback(async (options: {
    method: string
    path: string
    body?: Record<string, unknown>
    headers?: Record<string, string>
  }): Promise<T | null> => {
    setState((prev) => ({ ...prev, loading: true, error: null }))
    try {
      const response = await apiRequest<T>(options)
      if (response.status >= 400) {
        setState({ data: null, loading: false, error: response.error || 'حدث خطأ' })
        return null
      }
      setState({ data: response.data, loading: false, error: null })
      return response.data
    } catch (err) {
      setState({ data: null, loading: false, error: (err as Error).message })
      return null
    }
  }, [])

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null })
  }, [])

  return { ...state, execute, reset }
}
