import { useRef, useCallback, useEffect } from 'react'

interface WebSocketOptions {
  onMessage: (data: string) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
}

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const optionsRef = useRef<WebSocketOptions | null>(null)

  const connect = useCallback((url: string, options: WebSocketOptions) => {
    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close()
    }

    optionsRef.current = options

    const ws = new WebSocket(url)

    ws.onopen = () => {
      options.onOpen?.()
    }

    ws.onmessage = (event) => {
      options.onMessage(event.data)
    }

    ws.onclose = () => {
      options.onClose?.()
    }

    ws.onerror = (error) => {
      options.onError?.(error)
    }

    wsRef.current = ws
  }, [])

  const send = useCallback((data: string | Record<string, unknown>) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data)
      wsRef.current.send(message)
    }
  }, [])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  return { connect, send, disconnect }
}
