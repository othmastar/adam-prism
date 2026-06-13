import React, { useRef, useEffect, useCallback, useState } from 'react'
import { Sparkles, Wifi, WifiOff, AlertTriangle } from 'lucide-react'
import { useStore } from '../../lib/store'
import { MessageBubble } from './MessageBubble'
import { ChatInput } from './ChatInput'
import { cn } from '../../lib/utils'

export function ChatInterface() {
  const messages = useStore((s) => s.messages)
  const sendMessage = useStore((s) => s.sendMessage)
  const isStreaming = useStore((s) => s.isStreaming)
  const serverStatus = useStore((s) => s.serverStatus)
  const currentSessionId = useStore((s) => s.currentSessionId)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Check server status on mount
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const result = await window.api.checkBackend()
        useStore.getState().setServerStatus({
          status: result.connected ? 'online' : 'offline',
          version: undefined,
          model: undefined
        })
      } catch {
        useStore.getState().setServerStatus({ status: 'offline' })
      }
    }
    checkStatus()
    const interval = setInterval(checkStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleSend = useCallback(
    (content: string) => {
      sendMessage(content)
    },
    [sendMessage]
  )

  const handleStop = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    useStore.getState().setIsStreaming(false)
  }, [])

  const isOffline = serverStatus.status === 'offline'

  return (
    <div className="flex flex-col h-full bg-dark-900">
      {/* Offline banner */}
      {isOffline && (
        <div className="flex items-center gap-2 px-4 py-2 bg-danger/10 border-b border-danger/20">
          <WifiOff size={14} className="text-danger" />
          <span className="text-xs text-danger">غير متصل بالخادم</span>
          <button
            onClick={async () => {
              const result = await window.api.checkBackend()
              useStore.getState().setServerStatus({
                status: result.connected ? 'online' : 'offline'
              })
            }}
            className="text-xs text-danger hover:text-danger/80 underline mr-auto"
          >
            إعادة المحاولة
          </button>
        </div>
      )}

      {/* Messages area */}
      <div ref={containerRef} className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="py-4">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <ChatInput onSend={handleSend} onStop={handleStop} />
    </div>
  )
}

function EmptyState() {
  const sendMessage = useStore((s) => s.sendMessage)

  const quickPrompts = [
    { text: 'ما هو آدم بريزم؟', icon: '🤖' },
    { text: 'ساعدني في كتابة كود', icon: '💻' },
    { text: 'اشرح لي مفهوم الذكاء الاصطناعي', icon: '🧠' },
    { text: 'ما هي الأدوات المتاحة؟', icon: '🔧' }
  ]

  return (
    <div className="flex flex-col items-center justify-center h-full px-4">
      <div className="max-w-md text-center">
        {/* Logo */}
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-accent to-emerald-400 flex items-center justify-center mx-auto mb-6 shadow-lg shadow-accent/20">
          <span className="text-3xl font-bold text-white">A</span>
        </div>

        <h1 className="text-2xl font-bold text-dark-100 mb-2">مرحباً بك في آدم بريزم</h1>
        <p className="text-sm text-dark-400 mb-8">
          وكيل ذكاء اصطناعي متقدم للبرمجة والمحادثة. ابدأ محادثة أو اختر من الاقتراحات أدناه.
        </p>

        {/* Quick prompts */}
        <div className="grid grid-cols-2 gap-3">
          {quickPrompts.map((prompt, i) => (
            <button
              key={i}
              onClick={() => sendMessage(prompt.text)}
              className="flex items-center gap-2 px-4 py-3 bg-dark-800 border border-dark-600 rounded-xl text-sm text-dark-200 hover:bg-dark-700 hover:border-dark-500 transition-all duration-150 text-right"
            >
              <span className="text-lg">{prompt.icon}</span>
              <span>{prompt.text}</span>
            </button>
          ))}
        </div>

        {/* Shortcuts */}
        <div className="flex items-center justify-center gap-4 mt-8 text-dark-500 text-xs">
          <span>⌘K أوامر</span>
          <span>⌘N محادثة جديدة</span>
          <span>/ أوامر سريعة</span>
        </div>
      </div>
    </div>
  )
}
