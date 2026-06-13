import { useCallback, useEffect } from 'react'
import { useStore } from '../lib/store'
import type { Settings } from '../types'

export function useSettings() {
  const settings = useStore((s) => s.settings)
  const setSettings = useStore((s) => s.setSettings)

  const updateSettings = useCallback(async (partial: Partial<Settings>) => {
    setSettings(partial)
    // Persist to electron store
    try {
      await window.api.setSettings(partial as Record<string, unknown>)
    } catch (err) {
      console.error('Failed to persist settings:', err)
    }
  }, [setSettings])

  const updateSetting = useCallback(async <K extends keyof Settings>(key: K, value: Settings[K]) => {
    setSettings({ [key]: value } as Partial<Settings>)
    try {
      await window.api.setSetting(key, value)
    } catch (err) {
      console.error('Failed to persist setting:', err)
    }
  }, [setSettings])

  const loadSettings = useCallback(async () => {
    try {
      const stored = await window.api.getSettings()
      if (stored) {
        setSettings(stored as Partial<Settings>)
      }
    } catch (err) {
      console.error('Failed to load settings:', err)
    }
  }, [setSettings])

  const isRTL = settings.language === 'ar'

  return {
    settings,
    updateSettings,
    updateSetting,
    loadSettings,
    isRTL
  }
}
