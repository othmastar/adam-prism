import React, { useEffect, useRef, useState } from 'react'
import { Terminal as TerminalIcon, Loader2 } from 'lucide-react'

export function TerminalPanel() {
  const terminalRef = useRef<HTMLDivElement>(null)
  const [output, setOutput] = useState<string[]>([
    '\x1b[32mAdam Prism Terminal\x1b[0m',
    '\x1b[90mType commands below...\x1b[0m',
    ''
  ])
  const [input, setInput] = useState('')
  const [history, setHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)

  const handleCommand = (cmd: string) => {
    const newOutput = [...output, `\x1b[36m$\x1b[0m ${cmd}`]
    setHistory([cmd, ...history])

    // Simple command processing
    switch (cmd.trim()) {
      case 'help':
        newOutput.push(
          'الأوامر المتاحة:',
          '  help     - عرض هذه المساعدة',
          '  clear    - مسح الشاشة',
          '  status   - حالة الخادم',
          '  sessions - عرض المحادثات',
          ''
        )
        break
      case 'clear':
        setOutput([])
        setInput('')
        return
      case 'status':
        newOutput.push('جاري فحص حالة الخادم...')
        window.api.checkBackend().then((result) => {
          setOutput((prev) => [
            ...prev,
            result.connected
              ? '\x1b[32m✓ الخادم متصل\x1b[0m'
              : '\x1b[31m✗ الخادم غير متصل\x1b[0m',
            ''
          ])
        })
        break
      default:
        if (cmd.trim()) {
          newOutput.push(`\x1b[33mأمر غير معروف: ${cmd}\x1b[0m`, '')
        }
    }

    setOutput(newOutput)
    setInput('')
    setHistoryIndex(-1)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleCommand(input)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      const newIndex = Math.min(historyIndex + 1, history.length - 1)
      setHistoryIndex(newIndex)
      if (history[newIndex]) setInput(history[newIndex])
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      const newIndex = Math.max(historyIndex - 1, -1)
      setHistoryIndex(newIndex)
      setInput(newIndex >= 0 ? history[newIndex] : '')
    }
  }

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [output])

  // [PHASE1-SECURITY] XSS-safe ANSI to React rendering
  // Parse ANSI codes into segments with class names instead of raw HTML
  // This prevents XSS attacks from malicious terminal output
  type AnsiSegment = { text: string; className: string }

  const ansiToClass = (code: string): string => {
    const map: Record<string, string> = {
      '32': 'text-accent',
      '36': 'text-info',
      '33': 'text-warning',
      '31': 'text-danger',
      '90': 'text-dark-400'
    }
    return map[code] || ''
  }

  const renderLine = (line: string): AnsiSegment[] => {
    const segments: AnsiSegment[] = []
    // Match ANSI escape sequences: \x1b[<code>m
    const ansiRegex = /\x1b\[(\d+)m/g
    let lastIndex = 0
    let currentClass = ''
    let match: RegExpExecArray | null

    while ((match = ansiRegex.exec(line)) !== null) {
      // Add text before this escape sequence
      if (match.index > lastIndex) {
        segments.push({
          text: line.slice(lastIndex, match.index),
          className: currentClass
        })
      }
      // 0 = reset, otherwise look up class
      const code = match[1]
      currentClass = code === '0' ? '' : ansiToClass(code)
      lastIndex = ansiRegex.lastIndex
    }
    // Add remaining text
    if (lastIndex < line.length) {
      segments.push({
        text: line.slice(lastIndex),
        className: currentClass
      })
    }
    // If no segments were created, return a single segment
    if (segments.length === 0) {
      segments.push({ text: line, className: '' })
    }
    return segments
  }

  return (
    <div className="flex flex-col h-full bg-[#0d0d14]">
      {/* Terminal output - XSS-safe React rendering */}
      <div ref={terminalRef} className="flex-1 overflow-y-auto p-3 font-mono text-xs leading-relaxed">
        {output.map((line, i) => {
          const segments = renderLine(line)
          return (
            <div key={i}>
              {segments.map((seg, j) => (
                <span key={j} className={seg.className}>{seg.text}</span>
              ))}
            </div>
          )
        })}
      </div>

      {/* Input */}
      <div className="flex items-center gap-2 px-3 py-2 border-t border-dark-700">
        <span className="text-accent text-xs font-mono">$</span>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1 bg-transparent text-xs text-dark-100 font-mono focus:outline-none"
          placeholder="اكتب أمراً..."
          autoFocus
        />
      </div>
    </div>
  )
}
