import React from 'react'
import { MessageSquare, Plus, Search, Settings, BookOpen, Cpu, Wrench, Terminal, Hash, Users, Plug, ChevronRight, Pin, Trash2 } from 'lucide-react'
import { useStore } from '../../lib/store'
import { SessionList } from '../sessions/SessionList'
import { cn } from '../../lib/utils'

export function Sidebar() {
  const sidebarOpen = useStore((s) => s.sidebarOpen)
  const setSidebarOpen = useStore((s) => s.setSidebarOpen)
  const setSettingsOpen = useStore((s) => s.setSettingsOpen)
  const setRightPanelView = useStore((s) => s.setRightPanelView)
  const setBottomPanelView = useStore((s) => s.setBottomPanelView)
  const createNewSession = useStore((s) => s.createNewSession)
  const setCommandPaletteOpen = useStore((s) => s.setCommandPaletteOpen)

  const quickActions = [
    { icon: <BookOpen size={16} />, label: 'المعرفة', action: () => setRightPanelView('knowledge') },
    { icon: <Cpu size={16} />, label: 'الذاكرة', action: () => setRightPanelView('memory') },
    { icon: <Wrench size={16} />, label: 'الأدوات', action: () => setRightPanelView('tools') },
    { icon: <Terminal size={16} />, label: 'الطرفية', action: () => setBottomPanelView('terminal') },
    { icon: <Hash size={16} />, label: 'خط الأنابيب', action: () => setBottomPanelView('pipeline') },
    { icon: <Users size={16} />, label: 'الوكلاء', action: () => setRightPanelView('subagents') },
    { icon: <Plug size={16} />, label: 'MCP', action: () => setRightPanelView('mcp') }
  ]

  if (!sidebarOpen) {
    return (
      <div className="w-12 bg-dark-800 border-l border-dark-700 flex flex-col items-center py-2 gap-1">
        <button
          onClick={() => setSidebarOpen(true)}
          className="w-8 h-8 flex items-center justify-center rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-700 transition-colors"
        >
          <ChevronRight size={16} className="rotate-180" />
        </button>
        <div className="w-6 h-px bg-dark-600 my-1" />
        {quickActions.map((action, i) => (
          <button
            key={i}
            onClick={action.action}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-700 transition-colors"
            title={action.label}
          >
            {action.icon}
          </button>
        ))}
      </div>
    )
  }

  return (
    <div className="w-72 bg-dark-800 border-l border-dark-700 flex flex-col h-full animate-slideInLeft">
      {/* Header */}
      <div className="px-3 py-3 border-b border-dark-700">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-accent to-emerald-400 flex items-center justify-center">
              <span className="text-[10px] font-bold text-white">A</span>
            </div>
            <span className="text-sm font-semibold text-dark-100">آدم بريزم</span>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-1 rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-700 transition-colors"
          >
            <ChevronRight size={16} />
          </button>
        </div>

        {/* New Session + Search */}
        <div className="flex gap-2">
          <button
            onClick={createNewSession}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent/10 text-accent text-xs font-medium hover:bg-accent/20 transition-colors"
          >
            <Plus size={14} />
            محادثة جديدة
          </button>
          <button
            onClick={() => setCommandPaletteOpen(true)}
            className="p-1.5 rounded-lg bg-dark-700 text-dark-400 hover:text-dark-100 hover:bg-dark-600 transition-colors"
            title="بحث (⌘K)"
          >
            <Search size={14} />
          </button>
        </div>
      </div>

      {/* Sessions list */}
      <div className="flex-1 overflow-y-auto">
        <SessionList />
      </div>

      {/* Quick actions */}
      <div className="border-t border-dark-700 p-2">
        <div className="grid grid-cols-4 gap-1">
          {quickActions.map((action, i) => (
            <button
              key={i}
              onClick={action.action}
              className="flex flex-col items-center gap-0.5 p-1.5 rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-700 transition-colors"
              title={action.label}
            >
              {action.icon}
              <span className="text-[9px]">{action.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Settings */}
      <div className="border-t border-dark-700 p-2">
        <button
          onClick={() => setSettingsOpen(true)}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-700 transition-colors text-xs"
        >
          <Settings size={14} />
          الإعدادات
        </button>
      </div>
    </div>
  )
}
