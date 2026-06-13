import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Search, Hash, MessageSquare, Settings, Wrench, BookOpen, Cpu, Terminal, ChevronLeft } from 'lucide-react'
import { useStore } from '../../lib/store'
import { cn } from '../../lib/utils'

interface CommandItem {
  id: string
  label: string
  labelEn?: string
  icon: React.ReactNode
  category: string
  action: () => void
  shortcut?: string
}

export function CommandPalette() {
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const isOpen = useStore((s) => s.commandPaletteOpen)
  const setCommandPaletteOpen = useStore((s) => s.setCommandPaletteOpen)
  const store = useStore()

  const commands: CommandItem[] = [
    {
      id: 'new-session',
      label: 'محادثة جديدة',
      labelEn: 'New Session',
      icon: <MessageSquare size={16} />,
      category: 'محادثات',
      action: () => store.createNewSession(),
      shortcut: '⌘N'
    },
    {
      id: 'search-sessions',
      label: 'البحث في المحادثات',
      labelEn: 'Search Sessions',
      icon: <Search size={16} />,
      category: 'محادثات',
      action: () => {}
    },
    {
      id: 'toggle-sidebar',
      label: 'تبديل الشريط الجانبي',
      labelEn: 'Toggle Sidebar',
      icon: <ChevronLeft size={16} />,
      category: 'واجهة',
      action: () => store.setSidebarOpen(!store.sidebarOpen),
      shortcut: '⌘B'
    },
    {
      id: 'open-knowledge',
      label: 'لوحة المعرفة',
      labelEn: 'Knowledge Panel',
      icon: <BookOpen size={16} />,
      category: 'لوحات',
      action: () => store.setRightPanelView(store.rightPanelView === 'knowledge' ? 'none' : 'knowledge')
    },
    {
      id: 'open-memory',
      label: 'لوحة الذاكرة',
      labelEn: 'Memory Panel',
      icon: <Cpu size={16} />,
      category: 'لوحات',
      action: () => store.setRightPanelView(store.rightPanelView === 'memory' ? 'none' : 'memory')
    },
    {
      id: 'open-tools',
      label: 'لوحة الأدوات',
      labelEn: 'Tools Panel',
      icon: <Wrench size={16} />,
      category: 'لوحات',
      action: () => store.setRightPanelView(store.rightPanelView === 'tools' ? 'none' : 'tools')
    },
    {
      id: 'open-terminal',
      label: 'الطرفية',
      labelEn: 'Terminal',
      icon: <Terminal size={16} />,
      category: 'لوحات',
      action: () => store.setBottomPanelView(store.bottomPanelView === 'terminal' ? 'none' : 'terminal')
    },
    {
      id: 'open-pipeline',
      label: 'مراقب خط الأنابيب',
      labelEn: 'Pipeline Monitor',
      icon: <Hash size={16} />,
      category: 'لوحات',
      action: () => store.setBottomPanelView(store.bottomPanelView === 'pipeline' ? 'none' : 'pipeline')
    },
    {
      id: 'open-settings',
      label: 'الإعدادات',
      labelEn: 'Settings',
      icon: <Settings size={16} />,
      category: 'تطبيق',
      action: () => store.setSettingsOpen(true),
      shortcut: '⌘,'
    }
  ]

  const filtered = commands.filter(
    (cmd) =>
      cmd.label.includes(query) ||
      (cmd.labelEn && cmd.labelEn.toLowerCase().includes(query.toLowerCase()))
  )

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus()
      setQuery('')
      setSelectedIndex(0)
    }
  }, [isOpen])

  useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  const executeSelected = useCallback(() => {
    if (filtered[selectedIndex]) {
      filtered[selectedIndex].action()
      setCommandPaletteOpen(false)
    }
  }, [filtered, selectedIndex, setCommandPaletteOpen])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setSelectedIndex((i) => Math.min(i + 1, filtered.length - 1))
          break
        case 'ArrowUp':
          e.preventDefault()
          setSelectedIndex((i) => Math.max(i - 1, 0))
          break
        case 'Enter':
          e.preventDefault()
          executeSelected()
          break
        case 'Escape':
          e.preventDefault()
          setCommandPaletteOpen(false)
          break
      }
    },
    [filtered.length, executeSelected, setCommandPaletteOpen]
  )

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setCommandPaletteOpen(false)} />
      <div className="relative w-full max-w-lg mx-4 bg-dark-800 border border-dark-600 rounded-xl shadow-2xl overflow-hidden animate-fadeIn">
        <div className="flex items-center gap-3 px-4 py-3 border-b border-dark-600">
          <Search size={18} className="text-dark-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="اكتب أمراً..."
            className="flex-1 bg-transparent text-sm text-dark-100 placeholder:text-dark-400 focus:outline-none"
          />
          <kbd className="px-1.5 py-0.5 text-[10px] bg-dark-700 text-dark-400 rounded border border-dark-500">
            ESC
          </kbd>
        </div>
        <div className="max-h-80 overflow-y-auto py-2">
          {filtered.length === 0 && (
            <div className="px-4 py-8 text-center text-dark-400 text-sm">لا توجد نتائج</div>
          )}
          {filtered.map((cmd, i) => (
            <button
              key={cmd.id}
              className={cn(
                'w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors',
                i === selectedIndex ? 'bg-accent/10 text-accent' : 'text-dark-200 hover:bg-dark-700'
              )}
              onClick={() => {
                cmd.action()
                setCommandPaletteOpen(false)
              }}
              onMouseEnter={() => setSelectedIndex(i)}
            >
              <span className="text-dark-400">{cmd.icon}</span>
              <span className="flex-1 text-right">{cmd.label}</span>
              {cmd.shortcut && (
                <kbd className="px-1.5 py-0.5 text-[10px] bg-dark-700 text-dark-400 rounded border border-dark-500">
                  {cmd.shortcut}
                </kbd>
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
