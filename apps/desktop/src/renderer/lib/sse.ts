import { getSettings } from './store'

export interface SSEOptions {
  path: string
  body?: Record<string, unknown>
  onMessage: (data: string) => void
  onError?: (error: Error) => void
  onComplete?: () => void
  signal?: AbortSignal
}

export async function connectSSE(options: SSEOptions): Promise<void> {
  const settings = getSettings()
  const baseUrl = settings.backendUrl || 'http://localhost:8000'
  const apiKey = settings.apiKey

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream'
  }

  if (apiKey) {
    headers['Authorization'] = `Bearer ${apiKey}`
  }

  try {
    const response = await fetch(`${baseUrl}${options.path}`, {
      method: options.body ? 'POST' : 'GET',
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
      signal: options.signal
    })

    if (!response.ok) {
      throw new Error(`SSE connection failed: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) throw new Error('No response body')

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.substring(6)
          if (data === '[DONE]') {
            options.onComplete?.()
            return
          }
          options.onMessage(data)
        }
      }
    }

    options.onComplete?.()
  } catch (err) {
    if ((err as Error).name !== 'AbortError') {
      options.onError?.(err as Error)
    }
  }
}

export interface ChatSSEOptions {
  message: string
  sessionId?: string
  voice?: boolean
  onToken: (token: string) => void
  onToolCall?: (tool: { name: string; params: Record<string, unknown>; status: string }) => void
  onComplete: (fullResponse: string) => void
  onError?: (error: Error) => void
  signal?: AbortSignal
}

export async function streamChat(options: ChatSSEOptions): Promise<void> {
  let fullResponse = ''

  await connectSSE({
    path: '/api/chat',
    body: {
      message: options.message,
      session_id: options.sessionId,
      voice: options.voice ?? true
    },
    onMessage: (data) => {
      try {
        const parsed = JSON.parse(data)

        if (parsed.type === 'token' || parsed.type === 'content') {
          const token = parsed.content || parsed.token || ''
          fullResponse += token
          options.onToken(token)
        } else if (parsed.type === 'tool_call' || parsed.type === 'tool') {
          options.onToolCall?.({
            name: parsed.name || parsed.tool,
            params: parsed.params || parsed.parameters || {},
            status: parsed.status || 'running'
          })
        } else if (parsed.type === 'error') {
          options.onError?.(new Error(parsed.message || 'Stream error'))
        } else if (parsed.response || parsed.message) {
          const content = parsed.response || parsed.message
          if (typeof content === 'string') {
            fullResponse = content
            options.onToken(content)
          }
        }
      } catch {
        // If not JSON, treat as raw token
        if (data.trim()) {
          fullResponse += data
          options.onToken(data)
        }
      }
    },
    onComplete: () => {
      options.onComplete(fullResponse)
    },
    onError: options.onError,
    signal: options.signal
  })
}
