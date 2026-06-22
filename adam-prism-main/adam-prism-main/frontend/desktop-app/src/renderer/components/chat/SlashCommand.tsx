import React, { useState, useRef, useEffect } from 'react'
import { MessageSquare, Trash2, Brain, Wrench, Settings, HelpCircle, Sparkles } from 'lucide-react'
import { cn } from '../../lib/utils'

interface SlashCommandProps {
  query: string
  onSelect: (command: string) => void
  onClose: () => void
}

interface Command {
  id: string
  name: string
  nameEn: string
  icon: React.ReactNode
  description: string
}

const commands: Command[] = [
  { id: '/new', name: '/محادثة جديدة', nameEn: '/new', icon: <MessageSquare size={14} />, description: 'بدء محادثة جديدة' },
  { id: '/clear', name: '/مسح', nameEn: '/clear', icon: <Trash2 size={14} />, description: 'مسح المحادثة الحالية' },
  { id: '/memory', name: '/ذاكرة', nameEn: '/memory', icon: <Brain size={14} />, description: 'عرض حالة الذاكرة' },
  { id: '/skills', name: '/مهارات', nameEn: '/skills', icon: <Sparkles size={14} />, description: 'عرض المهارات المتاحة' },
  { id: '/tools', name: '/أدوات', nameEn: '/tools', icon: <Wrench size={14} />, description: 'عرض الأدوات المتاحة' },
  { id: '/settings', name: '/إعدادات', nameEn: '/settings', icon: <Settings size={14} />, description: 'فتح الإعدادات' },
  { id: '/help', name: '/مساعدة', nameEn: '/help', icon: <HelpCircle size={14} />, description: 'عرض المساعدة' }
]

export function SlashCommand({ query, onSelect, onClose }: SlashCommandProps) {
  const [selectedIndex, setSelectedIndex] = useState(0)

  const filtered = commands.filter(
    (cmd) =>
      cmd.name.includes(query) ||
      cmd.nameEn.toLowerCase().includes(query.toLowerCase()) ||
      cmd.description.includes(query)
  )

  useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
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
          if (filtered[selectedIndex]) {
            onSelect(filtered[selectedIndex].id)
          }
          break
        case 'Escape':
          e.preventDefault()
          onClose()
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [filtered, selectedIndex, onSelect, onClose])

  if (filtered.length === 0) return null

  return (
    <div className="absolute bottom-full left-0 right-0 mb-2 bg-dark-800 border border-dark-600 rounded-xl shadow-xl overflow-hidden z-20">
      <div className="py-1.5">
        <div className="px-3 py-1 text-[10px] text-dark-500 uppercase tracking-wider">أوامر سريعة</div>
        {filtered.map((cmd, i) => (
          <button
            key={cmd.id}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2 transition-colors',
              i === selectedIndex ? 'bg-accent/10 text-accent' : 'text-dark-200 hover:bg-dark-700'
            )}
            onClick={() => onSelect(cmd.id)}
            onMouseEnter={() => setSelectedIndex(i)}
          >
            <span className="text-dark-400">{cmd.icon}</span>
            <div className="flex-1 text-right">
              <span className="text-xs font-medium">{cmd.name}</span>
              <span className="text-[10px] text-dark-500 mr-2">{cmd.nameEn}</span>
            </div>
            <span className="text-[10px] text-dark-500">{cmd.description}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
