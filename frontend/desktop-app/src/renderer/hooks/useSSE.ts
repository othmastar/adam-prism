import { useRef, useCallback } from 'react'
import { connectSSE } from '../lib/sse'
import type { SSEOptions } from '../lib/sse'

export function useSSE() {
  const abortControllerRef = useRef<AbortController | null>(null)

  const connect = useCallback(async (options: Omit<SSEOptions, 'signal'>) => {
    // Close any existing connection
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    const controller = new AbortController()
    abortControllerRef.current = controller

    await connectSSE({
      ...options,
      signal: controller.signal
    })
  }, [])

  const disconnect = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
  }, [])

  return { connect, disconnect }
}
