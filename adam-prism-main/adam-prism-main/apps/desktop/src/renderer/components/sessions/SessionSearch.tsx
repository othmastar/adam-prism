import React, { useState, useRef, useEffect } from 'react'
import { Search, X } from 'lucide-react'
import { useStore } from '../../lib/store'

export function SessionSearch() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Array<{ id: string; title: string; lastMessage?: string }>>([])
  const [isOpen, setIsOpen] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const searchSessions = useStore((s) => s.searchSessions)

  useEffect(() => {
    if (query.trim()) {
      const timer = setTimeout(async () => {
        const sessions = await searchSessions(query)
        setResults(sessions.map((s) => ({ id: s.id, title: s.title, lastMessage: s.lastMessage })))
      }, 300)
      return () => clearTimeout(timer)
    } else {
      setResults([])
    }
  }, [query, searchSessions])

  const loadMessages = useStore((s) => s.loadMessages)
  const setCurrentSession = useStore((s) => s.setCurrentSession)

  const handleSelect = (id: string) => {
    setCurrentSession(id)
    loadMessages(id)
    setQuery('')
    setIsOpen(false)
  }

  return (
    <div className="relative">
      <div className="flex items-center gap-2 bg-dark-700 rounded-lg px-3 py-1.5">
        <Search size={14} className="text-dark-400" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setIsOpen(true) }}
          onFocus={() => setIsOpen(true)}
          placeholder="بحث في المحادثات..."
          className="flex-1 bg-transparent text-xs text-dark-100 placeholder:text-dark-500 focus:outline-none"
        />
        {query && (
          <button onClick={() => { setQuery(''); setIsOpen(false) }} className="text-dark-400 hover:text-dark-100">
            <X size={12} />
          </button>
        )}
      </div>

      {isOpen && query.trim() && results.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-dark-700 border border-dark-600 rounded-lg shadow-xl z-30 max-h-60 overflow-y-auto">
          {results.map((r) => (
            <button
              key={r.id}
              onClick={() => handleSelect(r.id)}
              className="w-full flex items-start gap-2 px-3 py-2 hover:bg-dark-600 transition-colors text-right"
            >
              <div>
                <div className="text-xs font-medium text-dark-100">{r.title}</div>
                {r.lastMessage && (
                  <div className="text-[10px] text-dark-400 truncate mt-0.5">{r.lastMessage}</div>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
