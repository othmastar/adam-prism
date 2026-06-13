import React, { useState, useRef, useCallback, useEffect } from 'react'
import { Send, Mic, MicOff, Paperclip, Image, StopCircle } from 'lucide-react'
import { useStore } from '../../lib/store'
import { SlashCommand } from './SlashCommand'
import { cn } from '../../lib/utils'

interface ChatInputProps {
  onSend: (message: string) => void
  onStop?: () => void
}

export function ChatInput({ onSend, onStop }: ChatInputProps) {
  const [message, setMessage] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [showSlash, setShowSlash] = useState(false)
  const [history, setHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const isStreaming = useStore((s) => s.isStreaming)
  const settings = useStore((s) => s.settings)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px'
    }
  }, [message])

  const handleSend = useCallback(() => {
    const trimmed = message.trim()
    if (!trimmed || isStreaming) return

    onSend(trimmed)
    setHistory((prev) => [trimmed, ...prev].slice(0, 50))
    setMessage('')
    setHistoryIndex(-1)
    setShowSlash(false)

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [message, isStreaming, onSend])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      // Slash commands
      if (message.startsWith('/') && !showSlash) {
        setShowSlash(true)
      }

      // Enter to send (without Shift)
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        if (showSlash) return
        handleSend()
      }

      // History navigation
      if (e.key === 'ArrowUp' && !message) {
        e.preventDefault()
        setHistoryIndex((i) => Math.min(i + 1, history.length - 1))
        if (history[historyIndex + 1]) {
          setMessage(history[historyIndex + 1])
        }
      }
      if (e.key === 'ArrowDown' && historyIndex >= 0) {
        e.preventDefault()
        const newIndex = historyIndex - 1
        setHistoryIndex(newIndex)
        setMessage(newIndex >= 0 ? history[newIndex] : '')
      }

      // Escape
      if (e.key === 'Escape') {
        setShowSlash(false)
      }
    },
    [message, showSlash, handleSend, history, historyIndex]
  )

  const handleSlashSelect = useCallback(
    (command: string) => {
      switch (command) {
        case '/new':
          useStore.getState().createNewSession()
          break
        case '/clear':
          useStore.getState().setMessages([])
          break
        case '/memory':
          useStore.getState().setRightPanelView('memory')
          break
        case '/tools':
          useStore.getState().setRightPanelView('tools')
          break
        case '/skills':
          useStore.getState().setRightPanelView('tools')
          break
        case '/settings':
          useStore.getState().setSettingsOpen(true)
          break
        case '/help':
          break
      }
      setMessage('')
      setShowSlash(false)
      textareaRef.current?.focus()
    },
    []
  )

  const handleVoice = useCallback(async () => {
    if (isRecording) {
      setIsRecording(false)
      return
    }

    try {
      setIsRecording(true)
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      const chunks: BlobPart[] = []

      mediaRecorder.ondataavailable = (e) => {
        chunks.push(e.data)
      }

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        setIsRecording(false)

        // In a real app, send to /api/voice/transcribe
        // For now, just add a placeholder
        setMessage((prev) => prev + ' [صوت]')
      }

      mediaRecorder.start()
      setTimeout(() => mediaRecorder.stop(), 5000) // Max 5 seconds
    } catch (err) {
      setIsRecording(false)
      console.error('Voice input error:', err)
    }
  }, [isRecording])

  const handlePaste = useCallback((e: React.ClipboardEvent) => {
    const items = e.clipboardData.items
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        e.preventDefault()
        // Handle image paste
        break
      }
    }
  }, [])

  const slashQuery = message.startsWith('/') ? message : ''

  return (
    <div className="relative border-t border-dark-700 bg-dark-800">
      {/* Slash commands popup */}
      {showSlash && slashQuery && (
        <SlashCommand
          query={slashQuery}
          onSelect={handleSlashSelect}
          onClose={() => setShowSlash(false)}
        />
      )}

      <div className="flex items-end gap-2 px-4 py-3">
        {/* Attachment button */}
        <button
          className="p-2 rounded-lg text-dark-400 hover:text-dark-200 hover:bg-dark-700 transition-colors flex-shrink-0"
          title="إرفاق ملف"
        >
          <Paperclip size={18} />
        </button>

        {/* Text input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => {
              setMessage(e.target.value)
              if (e.target.value.startsWith('/') && !showSlash) setShowSlash(true)
              if (!e.target.value.startsWith('/')) setShowSlash(false)
            }}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
            placeholder="اكتب رسالتك لآدم... (/ للأوامر السريعة)"
            className="w-full bg-dark-700 border border-dark-600 rounded-xl px-4 py-2.5 text-sm text-dark-100 placeholder:text-dark-500 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 resize-none max-h-[200px] transition-colors"
            rows={1}
            dir="auto"
          />
        </div>

        {/* Voice button */}
        {settings.voiceEnabled && (
          <button
            onClick={handleVoice}
            className={cn(
              'p-2 rounded-lg transition-colors flex-shrink-0',
              isRecording
                ? 'bg-danger/20 text-danger hover:bg-danger/30'
                : 'text-dark-400 hover:text-dark-200 hover:bg-dark-700'
            )}
            title={isRecording ? 'إيقاف التسجيل' : 'إدخال صوتي'}
          >
            {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
          </button>
        )}

        {/* Send/Stop button */}
        {isStreaming ? (
          <button
            onClick={onStop}
            className="p-2 rounded-lg bg-danger/20 text-danger hover:bg-danger/30 transition-colors flex-shrink-0"
            title="إيقاف"
          >
            <StopCircle size={18} />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!message.trim()}
            className={cn(
              'p-2 rounded-lg transition-colors flex-shrink-0',
              message.trim()
                ? 'bg-accent text-white hover:bg-accent-hover'
                : 'bg-dark-700 text-dark-500 cursor-not-allowed'
            )}
            title="إرسال"
          >
            <Send size={18} />
          </button>
        )}
      </div>

      {/* Composer hint */}
      <div className="flex items-center justify-between px-4 pb-2">
        <span className="text-[10px] text-dark-500">
          Enter للإرسال • Shift+Enter لسطر جديد • ↑↓ للسجل
        </span>
      </div>
    </div>
  )
}
