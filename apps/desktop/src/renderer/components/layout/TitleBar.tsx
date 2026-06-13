import React, { useEffect, useState } from 'react'
import { Minus, Square, X, ChevronDown } from 'lucide-react'
import { useStore } from '../../lib/store'
import { cn } from '../../lib/utils'

export function TitleBar() {
  const [isMaximized, setIsMaximized] = useState(false)
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking')
  const serverStatus = useStore((s) => s.serverStatus)

  useEffect(() => {
    window.api.windowIsMaximized().then(setIsMaximized)
    window.api.on('window-maximized', () => setIsMaximized(true))
    window.api.on('window-unmaximized', () => setIsMaximized(false))
  }, [])

  useEffect(() => {
    if (serverStatus.status === 'online') setBackendStatus('connected')
    else if (serverStatus.status === 'offline') setBackendStatus('disconnected')
    else setBackendStatus('checking')
  }, [serverStatus])

  const handleMinimize = () => window.api.windowMinimize()
  const handleMaximize = () => {
    window.api.windowMaximize()
    setIsMaximized(!isMaximized)
  }
  const handleClose = () => window.api.windowClose()

  return (
    <div className="titlebar-drag flex items-center h-10 bg-dark-800 border-b border-dark-700 select-none px-3">
      {/* App icon and title */}
      <div className="flex items-center gap-2 flex-1">
        <div className="w-5 h-5 rounded bg-gradient-to-br from-accent to-emerald-400 flex items-center justify-center">
          <span className="text-[8px] font-bold text-white">A</span>
        </div>
        <span className="text-xs font-medium text-dark-200">Adam Prism</span>
        <div className="flex items-center gap-1.5 mr-2">
          <div
            className={cn(
              'w-2 h-2 rounded-full',
              backendStatus === 'connected' && 'bg-accent',
              backendStatus === 'disconnected' && 'bg-danger',
              backendStatus === 'checking' && 'bg-warning animate-pulse'
            )}
          />
          <span className="text-[10px] text-dark-400">
            {backendStatus === 'connected' ? 'متصل' : backendStatus === 'disconnected' ? 'غير متصل' : 'جاري الفحص...'}
          </span>
        </div>
      </div>

      {/* Window controls */}
      <div className="titlebar-no-drag flex items-center gap-0.5">
        <button
          onClick={handleMinimize}
          className="w-8 h-8 flex items-center justify-center rounded hover:bg-dark-600 text-dark-400 hover:text-dark-100 transition-colors"
        >
          <Minus size={14} />
        </button>
        <button
          onClick={handleMaximize}
          className="w-8 h-8 flex items-center justify-center rounded hover:bg-dark-600 text-dark-400 hover:text-dark-100 transition-colors"
        >
          {isMaximized ? <ChevronDown size={14} className="rotate-180" /> : <Square size={12} />}
        </button>
        <button
          onClick={handleClose}
          className="w-8 h-8 flex items-center justify-center rounded hover:bg-danger/20 text-dark-400 hover:text-danger transition-colors"
        >
          <X size={14} />
        </button>
      </div>
    </div>
  )
}
