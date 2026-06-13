import React, { useState } from 'react'
import { MessageSquare, Pin, Trash2, MoreHorizontal, Edit3, Check, X } from 'lucide-react'
import type { Session } from '../../types'
import { useStore } from '../../lib/store'
import { cn, truncateText, formatDate } from '../../lib/utils'

interface SessionItemProps {
  session: Session
  isActive: boolean
  onClick: () => void
  onDelete: () => void
  onRename: (name: string) => void
  onPin: () => void
}

export function SessionItem({ session, isActive, onClick, onDelete, onRename, onPin }: SessionItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(session.title)
  const [showMenu, setShowMenu] = useState(false)

  const handleRename = () => {
    if (editValue.trim()) {
      onRename(editValue.trim())
    }
    setIsEditing(false)
  }

  return (
    <div
      className={cn(
        'group relative flex items-start gap-2 px-3 py-2.5 cursor-pointer transition-all duration-100',
        isActive ? 'bg-accent/10 border-r-2 border-accent' : 'hover:bg-dark-700'
      )}
      onClick={onClick}
    >
      <MessageSquare size={14} className="mt-0.5 text-dark-400 flex-shrink-0" />

      <div className="flex-1 min-w-0">
        {isEditing ? (
          <div className="flex items-center gap-1">
            <input
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleRename()
                if (e.key === 'Escape') setIsEditing(false)
              }}
              className="flex-1 bg-dark-600 text-xs text-dark-100 px-1.5 py-0.5 rounded focus:outline-none focus:ring-1 focus:ring-accent"
              autoFocus
              onClick={(e) => e.stopPropagation()}
            />
            <button
              onClick={(e) => { e.stopPropagation(); handleRename() }}
              className="p-0.5 text-accent hover:text-accent-hover"
            >
              <Check size={12} />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); setIsEditing(false) }}
              className="p-0.5 text-dark-400 hover:text-dark-100"
            >
              <X size={12} />
            </button>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-1">
              <span className="text-xs font-medium text-dark-100 truncate flex-1">
                {session.title}
              </span>
              {session.pinned && <Pin size={10} className="text-accent flex-shrink-0" />}
            </div>
            {session.lastMessage && (
              <p className="text-[10px] text-dark-400 truncate mt-0.5">
                {truncateText(session.lastMessage, 40)}
              </p>
            )}
            <div className="flex items-center gap-2 mt-1">
              <span className="text-[9px] text-dark-500">{formatDate(session.updatedAt)}</span>
              {session.messageCount > 0 && (
                <span className="text-[9px] text-dark-500">{session.messageCount} رسالة</span>
              )}
            </div>
          </>
        )}
      </div>

      {/* Action menu */}
      {!isEditing && (
        <div className="opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
          <button
            onClick={(e) => {
              e.stopPropagation()
              setShowMenu(!showMenu)
            }}
            className="p-0.5 rounded text-dark-400 hover:text-dark-100 hover:bg-dark-600 transition-colors"
          >
            <MoreHorizontal size={14} />
          </button>
        </div>
      )}

      {/* Context menu */}
      {showMenu && (
        <div className="absolute left-2 top-full z-20 bg-dark-700 border border-dark-600 rounded-lg shadow-xl py-1 min-w-[120px]" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => { setIsEditing(true); setShowMenu(false) }}
            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-dark-200 hover:bg-dark-600 transition-colors"
          >
            <Edit3 size={12} />
            إعادة تسمية
          </button>
          <button
            onClick={() => { onPin(); setShowMenu(false) }}
            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-dark-200 hover:bg-dark-600 transition-colors"
          >
            <Pin size={12} />
            {session.pinned ? 'إلغاء التثبيت' : 'تثبيت'}
          </button>
          <div className="h-px bg-dark-600 my-1" />
          <button
            onClick={() => { onDelete(); setShowMenu(false) }}
            className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-danger hover:bg-danger/10 transition-colors"
          >
            <Trash2 size={12} />
            حذف
          </button>
        </div>
      )}
    </div>
  )
}
