import React, { useState, useCallback, useRef } from 'react'
import { X, GripHorizontal, GripVertical } from 'lucide-react'
import { useStore } from '../../lib/store'
import { KnowledgePanel } from '../panels/KnowledgePanel'
import { MemoryPanel } from '../panels/MemoryPanel'
import { ToolsPanel } from '../panels/ToolsPanel'
import { TerminalPanel } from '../panels/TerminalPanel'
import { PipelinePanel } from '../panels/PipelinePanel'
import { SubagentsPanel } from '../panels/SubagentsPanel'
import { MCPPanel } from '../panels/MCPPanel'
import type { RightPanelView, BottomPanelView } from '../../types'
import { cn } from '../../lib/utils'

const rightPanelTitles: Record<RightPanelView, string> = {
  knowledge: 'المعرفة',
  memory: 'الذاكرة',
  tools: 'الأدوات',
  subagents: 'الوكلاء الفرعيين',
  mcp: 'MCP',
  files: 'الملفات',
  terminal: 'الطرفية',
  pipeline: 'خط الأنابيب',
  none: ''
}

const bottomPanelTitles: Record<BottomPanelView, string> = {
  terminal: 'الطرفية',
  logs: 'السجلات',
  pipeline: 'خط الأنابيب',
  none: ''
}

function RightPanelContent({ view }: { view: RightPanelView }) {
  switch (view) {
    case 'knowledge': return <KnowledgePanel />
    case 'memory': return <MemoryPanel />
    case 'tools': return <ToolsPanel />
    case 'subagents': return <SubagentsPanel />
    case 'mcp': return <MCPPanel />
    default: return null
  }
}

function BottomPanelContent({ view }: { view: BottomPanelView }) {
  switch (view) {
    case 'terminal': return <TerminalPanel />
    case 'pipeline': return <PipelinePanel />
    case 'logs': return <TerminalPanel />
    default: return null
  }
}

interface ResizeHandleProps {
  direction: 'horizontal' | 'vertical'
  onResize: (delta: number) => void
}

function ResizeHandle({ direction, onResize }: ResizeHandleProps) {
  const isDragging = useRef(false)
  const lastPos = useRef(0)

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault()
      isDragging.current = true
      lastPos.current = direction === 'horizontal' ? e.clientX : e.clientY

      const handleMouseMove = (moveEvent: MouseEvent) => {
        if (!isDragging.current) return
        const currentPos = direction === 'horizontal' ? moveEvent.clientX : moveEvent.clientY
        const delta = currentPos - lastPos.current
        lastPos.current = currentPos
        onResize(-delta) // RTL: negative delta for right panel
      }

      const handleMouseUp = () => {
        isDragging.current = false
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }

      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    },
    [direction, onResize]
  )

  return (
    <div
      className={cn(
        'resize-handle flex items-center justify-center group',
        direction === 'horizontal' ? 'resize-handle-h' : 'resize-handle-v'
      )}
      onMouseDown={handleMouseDown}
    >
      <div
        className={cn(
          'rounded-full transition-opacity opacity-0 group-hover:opacity-100',
          direction === 'horizontal' ? 'w-0.5 h-8' : 'h-0.5 w-8',
          'bg-dark-400'
        )}
      />
    </div>
  )
}

export function PanelLayout({ children }: { children: React.ReactNode }) {
  const rightPanelView = useStore((s) => s.rightPanelView)
  const bottomPanelView = useStore((s) => s.bottomPanelView)
  const setRightPanelView = useStore((s) => s.setRightPanelView)
  const setBottomPanelView = useStore((s) => s.setBottomPanelView)
  const settings = useStore((s) => s.settings)
  const [rightWidth, setRightWidth] = useState(360)
  const [bottomHeight, setBottomHeight] = useState(220)

  const handleRightResize = useCallback((delta: number) => {
    setRightWidth((w) => Math.max(250, Math.min(600, w + delta)))
  }, [])

  const handleBottomResize = useCallback((delta: number) => {
    setBottomHeight((h) => Math.max(120, Math.min(500, h + delta)))
  }, [])

  const showRight = rightPanelView !== 'none'
  const showBottom = bottomPanelView !== 'none'

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* Main content area */}
      <div className="flex-1 flex h-full overflow-hidden">
        {/* Center content */}
        <div className={cn('flex-1 flex flex-col overflow-hidden', showBottom && 'min-h-0')}>
          <div className="flex-1 overflow-hidden">{children}</div>

          {/* Bottom panel */}
          {showBottom && (
            <>
              <ResizeHandle direction="vertical" onResize={handleBottomResize} />
              <div
                className="bg-dark-800 border-t border-dark-700 flex flex-col"
                style={{ height: bottomHeight }}
              >
                <div className="flex items-center justify-between px-3 py-1.5 border-b border-dark-700">
                  <span className="text-xs font-medium text-dark-200">
                    {bottomPanelTitles[bottomPanelView]}
                  </span>
                  <button
                    onClick={() => setBottomPanelView('none')}
                    className="p-0.5 rounded text-dark-400 hover:text-dark-100 hover:bg-dark-700 transition-colors"
                  >
                    <X size={14} />
                  </button>
                </div>
                <div className="flex-1 overflow-hidden">
                  <BottomPanelContent view={bottomPanelView} />
                </div>
              </div>
            </>
          )}
        </div>

        {/* Right panel */}
        {showRight && (
          <>
            <ResizeHandle direction="horizontal" onResize={handleRightResize} />
            <div
              className="bg-dark-800 border-r border-dark-700 flex flex-col"
              style={{ width: rightWidth }}
            >
              <div className="flex items-center justify-between px-3 py-2 border-b border-dark-700">
                <span className="text-xs font-medium text-dark-200">
                  {rightPanelTitles[rightPanelView]}
                </span>
                <button
                  onClick={() => setRightPanelView('none')}
                  className="p-0.5 rounded text-dark-400 hover:text-dark-100 hover:bg-dark-700 transition-colors"
                >
                  <X size={14} />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto">
                <RightPanelContent view={rightPanelView} />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
