import React from 'react'
import { Wrench, Loader, Check, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
import type { ToolCall } from '../../types'
import { cn } from '../../lib/utils'

interface ToolIndicatorProps {
  tool: ToolCall
}

export function ToolIndicator({ tool }: ToolIndicatorProps) {
  const [expanded, setExpanded] = React.useState(false)

  const statusConfig = {
    pending: { icon: <Wrench size={12} />, color: 'text-dark-400', bg: 'bg-dark-700', label: 'في الانتظار' },
    running: { icon: <Loader size={12} className="animate-spin" />, color: 'text-warning', bg: 'bg-warning/10', label: 'قيد التنفيذ' },
    completed: { icon: <Check size={12} />, color: 'text-accent', bg: 'bg-accent/10', label: 'مكتمل' },
    error: { icon: <AlertCircle size={12} />, color: 'text-danger', bg: 'bg-danger/10', label: 'خطأ' }
  }

  const config = statusConfig[tool.status]

  return (
    <div className={cn('rounded-lg border border-dark-600 overflow-hidden my-1.5', config.bg)}>
      <button
        className="w-full flex items-center gap-2 px-3 py-1.5 text-xs"
        onClick={() => setExpanded(!expanded)}
      >
        <span className={config.color}>{config.icon}</span>
        <span className="font-medium text-dark-200">{tool.name}</span>
        <span className={cn('px-1.5 py-0.5 rounded text-[9px]', config.bg, config.color)}>
          {config.label}
        </span>
        {tool.duration && (
          <span className="text-dark-500 text-[10px] mr-auto">{tool.duration}ms</span>
        )}
        {expanded ? <ChevronUp size={12} className="text-dark-400" /> : <ChevronDown size={12} className="text-dark-400" />}
      </button>

      {expanded && (
        <div className="px-3 py-2 border-t border-dark-600">
          {Object.keys(tool.params).length > 0 && (
            <div className="mb-2">
              <span className="text-[10px] text-dark-500">المعلمات:</span>
              <pre className="text-[10px] text-dark-300 mt-1 bg-dark-800 rounded p-2 overflow-x-auto">
                {JSON.stringify(tool.params, null, 2)}
              </pre>
            </div>
          )}
          {tool.result && (
            <div>
              <span className="text-[10px] text-dark-500">النتيجة:</span>
              <pre className="text-[10px] text-dark-300 mt-1 bg-dark-800 rounded p-2 overflow-x-auto max-h-40">
                {tool.result}
              </pre>
            </div>
          )}
          {tool.error && (
            <div>
              <span className="text-[10px] text-danger">الخطأ:</span>
              <pre className="text-[10px] text-danger mt-1 bg-dark-800 rounded p-2">{tool.error}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
