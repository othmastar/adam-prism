import React, { useEffect, useCallback } from 'react'
import { AppLayout } from './components/layout/AppLayout'
import { useStore } from './lib/store'
import { initSettings } from './lib/store'

export default function App() {
  const setSettings = useStore((s) => s.setSettings)
  const setOnboardingVisible = useStore((s) => s.setOnboardingVisible)
  const setCommandPaletteOpen = useStore((s) => s.setCommandPaletteOpen)
  const setSettingsOpen = useStore((s) => s.setSettingsOpen)
  const createNewSession = useStore((s) => s.createNewSession)
  const setServerStatus = useStore((s) => s.setServerStatus)

  // Initialize settings from electron store
  useEffect(() => {
    initSettings()
  }, [])

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isMod = e.metaKey || e.ctrlKey

      // Cmd+K: Command palette
      if (isMod && e.key === 'k') {
        e.preventDefault()
        setCommandPaletteOpen(true)
      }

      // Cmd+N: New session
      if (isMod && e.key === 'n') {
        e.preventDefault()
        createNewSession()
      }

      // Cmd+,: Settings
      if (isMod && e.key === ',') {
        e.preventDefault()
        setSettingsOpen(true)
      }

      // Cmd+B: Toggle sidebar
      if (isMod && e.key === 'b') {
        e.preventDefault()
        const store = useStore.getState()
        store.setSidebarOpen(!store.sidebarOpen)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [setCommandPaletteOpen, createNewSession, setSettingsOpen])

  // Listen for IPC events from main process
  useEffect(() => {
    const unsubNewSession = window.api.on('new-session', () => {
      createNewSession()
    })

    const unsubOpenSettings = window.api.on('open-settings', () => {
      setSettingsOpen(true)
    })

    const unsubCheckStatus = window.api.on('check-server-status', async () => {
      try {
        const result = await window.api.checkBackend()
        setServerStatus({
          status: result.connected ? 'online' : 'offline'
        })
      } catch {
        setServerStatus({ status: 'offline' })
      }
    })

    return () => {
      unsubNewSession()
      unsubOpenSettings()
      unsubCheckStatus()
    }
  }, [createNewSession, setSettingsOpen, setServerStatus])

  return <AppLayout />
}
