import React, { useEffect } from 'react'
import { MessageSquare, Plus } from 'lucide-react'
import { useStore } from '../../lib/store'
import { SessionItem } from './SessionItem'
import { SessionSearch } from './SessionSearch'
import { formatDate } from '../../lib/utils'
import type { Session } from '../../types'

export function SessionList() {
  const sessions = useStore((s) => s.sessions)
  const currentSessionId = useStore((s) => s.currentSessionId)
  const loadSessions = useStore((s) => s.loadSessions)
  const loadMessages = useStore((s) => s.loadMessages)
  const setCurrentSession = useStore((s) => s.setCurrentSession)
  const deleteSession = useStore((s) => s.deleteSession)
  const setSessions = useStore((s) => s.setSessions)

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  // Group sessions by date
  const grouped = sessions.reduce<Record<string, Session[]>>((acc, session) => {
    const dateKey = formatDate(session.updatedAt)
    if (!acc[dateKey]) acc[dateKey] = []
    acc[dateKey].push(session)
    return acc
  }, {})

  // Sort: pinned first, then by date
  const sortedGroups = Object.entries(grouped).sort(([a], [b]) => {
    if (a === 'اليوم') return -1
    if (b === 'اليوم') return 1
    if (a === 'أمس') return -1
    if (b === 'أمس') return 1
    return 0
  })

  return (
    <div className="py-2">
      {/* Search */}
      <div className="px-3 mb-2">
        <SessionSearch />
      </div>

      {/* Sessions */}
      {sortedGroups.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-dark-400">
          <MessageSquare size={32} className="mb-2 opacity-30" />
          <p className="text-xs">لا توجد محادثات بعد</p>
          <p className="text-[10px] mt-1">ابدأ محادثة جديدة للتفاعل مع آدم</p>
        </div>
      ) : (
        sortedGroups.map(([dateKey, groupSessions]) => (
          <div key={dateKey}>
            <div className="px-3 py-1.5">
              <span className="text-[10px] font-medium text-dark-500 uppercase tracking-wider">
                {dateKey}
              </span>
            </div>
            {groupSessions
              .sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0) || b.updatedAt - a.updatedAt)
              .map((session) => (
                <SessionItem
                  key={session.id}
                  session={session}
                  isActive={currentSessionId === session.id}
                  onClick={() => {
                    setCurrentSession(session.id)
                    loadMessages(session.id)
                  }}
                  onDelete={() => deleteSession(session.id)}
                  onRename={(name) => {
                    setSessions(
                      sessions.map((s) =>
                        s.id === session.id ? { ...s, title: name, updatedAt: Date.now() } : s
                      )
                    )
                  }}
                  onPin={() => {
                    setSessions(
                      sessions.map((s) =>
                        s.id === session.id ? { ...s, pinned: !s.pinned } : s
                      )
                    )
                  }}
                />
              ))}
          </div>
        ))
      )}
    </div>
  )
}
