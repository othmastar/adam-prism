import React, { useState, useEffect, useCallback, useRef } from 'react'
import { Activity, CheckCircle, XCircle, Loader2, RefreshCw, Zap } from 'lucide-react'
import { statusApi, diagnosticsApi } from '../../lib/api'
import type { PipelineEvent } from '../../types'
import { cn } from '../../lib/utils'

export function PipelinePanel() {
  const [events, setEvents] = useState<PipelineEvent[]>([])
  const [health, setHealth] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [connected, setConnected] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    loadHealth()
    return () => {
      abortRef.current?.abort()
    }
  }, [])

  const loadHealth = async () => {
    setLoading(true)
    try {
      const response = await statusApi.getEngineHealth()
      if (response.status === 200) {
        setHealth(response.data as Record<string, unknown>)
      }
    } catch (err) {
      console.error('Failed to load health:', err)
    } finally {
      setLoading(false)
    }
  }

  const connectStream = useCallback(async () => {
    if (abortRef.current) {
      abortRef.current.abort()
    }

    const controller = new AbortController()
    abortRef.current = controller
    setConnected(true)

    try {
      const settings = await window.api.getSettings()
      const baseUrl = settings.backendUrl || 'http://localhost:8000'
      const apiKey = settings.apiKey

      const headers: Record<string, string> = {
        'Accept': 'text/event-stream'
      }
      if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`
      }

      const response = await fetch(`${baseUrl}/api/engine/stream`, {
        headers,
        signal: controller.signal
      })

      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const reader = response.body?.getReader()
      if (!reader) return

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
            if (data === '[DONE]') break
            try {
              const parsed = JSON.parse(data)
              setEvents((prev) => [
                { type: parsed.type, data: parsed, timestamp: new Date().toISOString() },
                ...prev
              ].slice(0, 100))
            } catch {
              // Ignore parse errors
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        console.error('Pipeline stream error:', err)
      }
    } finally {
      setConnected(false)
    }
  }, [])

  const disconnect = () => {
    abortRef.current?.abort()
    setConnected(false)
  }

  const eventIcons: Record<string, React.ReactNode> = {
    step: <Zap size={10} className="text-info" />,
    tool: <Activity size={10} className="text-warning" />,
    thinking: <Loader2 size={10} className="text-accent animate-spin" />,
    error: <XCircle size={10} className="text-danger" />,
    complete: <CheckCircle size={10} className="text-accent" />
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-dark-700">
        <div className="flex items-center gap-2">
          <Activity size={14} className="text-accent" />
          <span className="text-xs font-medium text-dark-200">خط الأنابيب</span>
          {connected && (
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={loadHealth}
            className="p-1 rounded text-dark-400 hover:text-dark-200 hover:bg-dark-700 transition-colors"
            title="تحديث"
          >
            <RefreshCw size={12} />
          </button>
          {connected ? (
            <button
              onClick={disconnect}
              className="px-2 py-0.5 text-[10px] bg-danger/10 text-danger rounded hover:bg-danger/20"
            >
              إيقاف
            </button>
          ) : (
            <button
              onClick={connectStream}
              className="px-2 py-0.5 text-[10px] bg-accent/10 text-accent rounded hover:bg-accent/20"
            >
              اتصال
            </button>
          )}
        </div>
      </div>

      {/* Health info */}
      {health && (
        <div className="px-3 py-2 border-b border-dark-700 bg-dark-800">
          <div className="grid grid-cols-2 gap-2 text-[10px]">
            {Object.entries(health).slice(0, 4).map(([key, value]) => (
              <div key={key}>
                <span className="text-dark-500">{key}:</span>{' '}
                <span className="text-dark-200">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Events */}
      <div className="flex-1 overflow-y-auto p-2">
        {events.length === 0 ? (
          <div className="text-center py-12">
            <Activity size={24} className="mx-auto text-dark-600 mb-2" />
            <p className="text-xs text-dark-400">لا توجد أحداث بعد</p>
            <p className="text-[10px] text-dark-500 mt-1">اضغط "اتصال" لبدء البث المباشر</p>
          </div>
        ) : (
          <div className="space-y-1">
            {events.map((event, i) => (
              <div
                key={i}
                className="flex items-start gap-2 px-2 py-1.5 bg-dark-800 rounded text-[10px] animate-fadeIn"
              >
                <span className="mt-0.5">{eventIcons[event.type] || <Activity size={10} className="text-dark-400" />}</span>
                <div className="flex-1 min-w-0">
                  <span className="text-dark-300">{event.type}</span>
                  {event.data.message && (
                    <p className="text-dark-500 truncate">{event.data.message as string}</p>
                  )}
                </div>
                <span className="text-dark-600 flex-shrink-0">
                  {new Date(event.timestamp).toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
