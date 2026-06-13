import React, { useState, useEffect } from 'react'
import { Settings as SettingsIcon, Globe, Key, Monitor, Volume2, Bell, Shield, Server, Palette, Languages } from 'lucide-react'
import { Modal } from '../ui/Modal'
import { Button } from '../ui/Button'
import { useStore } from '../../lib/store'
import { modelsApi } from '../../lib/api'
import type { Settings } from '../../types'
import { cn } from '../../lib/utils'

export function SettingsModal() {
  const settings = useStore((s) => s.settings)
  const setSettingsOpen = useStore((s) => s.setSettingsOpen)
  const setSetting = useStore((s) => s.setSettings)
  const [localSettings, setLocalSettings] = useState<Settings>(settings)
  const [activeSection, setActiveSection] = useState('general')
  const [models, setModels] = useState<string[]>([])
  const [checkingBackend, setCheckingBackend] = useState(false)
  const [backendStatus, setBackendStatus] = useState<'unknown' | 'connected' | 'disconnected'>('unknown')

  useEffect(() => {
    setLocalSettings(settings)
  }, [settings])

  useEffect(() => {
    if (settings.backendUrl) {
      loadModels()
    }
  }, [settings.backendUrl])

  const loadModels = async () => {
    try {
      const response = await modelsApi.getModels()
      if (response.status === 200 && Array.isArray(response.data)) {
        const modelList = response.data as Array<Record<string, unknown>>
        setModels(modelList.map((m) => (m.name as string) || (m.model as string) || '').filter(Boolean))
      }
    } catch {
      // Ignore model loading errors
    }
  }

  const handleCheckBackend = async () => {
    setCheckingBackend(true)
    try {
      // Temporarily save URL and key
      await window.api.setSettings({
        backendUrl: localSettings.backendUrl,
        apiKey: localSettings.apiKey,
        isLocal: localSettings.isLocal
      })
      const result = await window.api.checkBackend()
      setBackendStatus(result.connected ? 'connected' : 'disconnected')
      if (result.connected) {
        loadModels()
      }
    } catch {
      setBackendStatus('disconnected')
    } finally {
      setCheckingBackend(false)
    }
  }

  const handleSave = async () => {
    await window.api.setSettings(localSettings as unknown as Record<string, unknown>)
    setSetting(localSettings)
    setSettingsOpen(false)
  }

  const updateLocal = <K extends keyof Settings>(key: K, value: Settings[K]) => {
    setLocalSettings((prev) => ({ ...prev, [key]: value }))
  }

  const sections = [
    { id: 'general', label: 'عام', icon: <SettingsIcon size={16} /> },
    { id: 'backend', label: 'الاتصال', icon: <Server size={16} /> },
    { id: 'appearance', label: 'المظهر', icon: <Palette size={16} /> },
    { id: 'voice', label: 'الصوت', icon: <Volume2 size={16} /> },
    { id: 'notifications', label: 'الإشعارات', icon: <Bell size={16} /> }
  ]

  return (
    <Modal
      isOpen={true}
      onClose={() => setSettingsOpen(false)}
      title="الإعدادات"
      size="lg"
    >
      <div className="flex gap-6" dir="rtl">
        {/* Sidebar */}
        <div className="w-40 flex-shrink-0">
          <div className="space-y-1">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={cn(
                  'w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs transition-colors',
                  activeSection === section.id
                    ? 'bg-accent/10 text-accent'
                    : 'text-dark-300 hover:bg-dark-700 hover:text-dark-100'
                )}
              >
                {section.icon}
                {section.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {activeSection === 'general' && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-dark-200 mb-1.5">النموذج</label>
                <select
                  value={localSettings.model}
                  onChange={(e) => updateLocal('model', e.target.value)}
                  className="w-full bg-dark-700 border border-dark-500 rounded-lg px-3 py-2 text-sm text-dark-100 focus:outline-none focus:border-accent"
                >
                  <option value="adam">آدم (الافتراضي)</option>
                  {models.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-dark-200 mb-1.5">اللغة</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => updateLocal('language', 'ar')}
                    className={cn(
                      'flex-1 py-2 rounded-lg text-xs font-medium transition-colors',
                      localSettings.language === 'ar' ? 'bg-accent/10 text-accent border border-accent/30' : 'bg-dark-700 text-dark-300 border border-dark-600 hover:bg-dark-600'
                    )}
                  >
                    العربية
                  </button>
                  <button
                    onClick={() => updateLocal('language', 'en')}
                    className={cn(
                      'flex-1 py-2 rounded-lg text-xs font-medium transition-colors',
                      localSettings.language === 'en' ? 'bg-accent/10 text-accent border border-accent/30' : 'bg-dark-700 text-dark-300 border border-dark-600 hover:bg-dark-600'
                    )}
                  >
                    English
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'backend' && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-dark-200 mb-1.5">نوع الاتصال</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => updateLocal('isLocal', true)}
                    className={cn(
                      'flex-1 py-2 rounded-lg text-xs font-medium transition-colors',
                      localSettings.isLocal ? 'bg-accent/10 text-accent border border-accent/30' : 'bg-dark-700 text-dark-300 border border-dark-600'
                    )}
                  >
                    محلي
                  </button>
                  <button
                    onClick={() => updateLocal('isLocal', false)}
                    className={cn(
                      'flex-1 py-2 rounded-lg text-xs font-medium transition-colors',
                      !localSettings.isLocal ? 'bg-accent/10 text-accent border border-accent/30' : 'bg-dark-700 text-dark-300 border border-dark-600'
                    )}
                  >
                    عن بُعد
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-dark-200 mb-1.5">عنوان الخادم</label>
                <input
                  type="text"
                  value={localSettings.backendUrl}
                  onChange={(e) => updateLocal('backendUrl', e.target.value)}
                  placeholder="http://localhost:8000"
                  className="w-full bg-dark-700 border border-dark-500 rounded-lg px-3 py-2 text-sm text-dark-100 placeholder:text-dark-500 focus:outline-none focus:border-accent"
                  dir="ltr"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-dark-200 mb-1.5">مفتاح API</label>
                <input
                  type="password"
                  value={localSettings.apiKey}
                  onChange={(e) => updateLocal('apiKey', e.target.value)}
                  placeholder="أدخل مفتاح API"
                  className="w-full bg-dark-700 border border-dark-500 rounded-lg px-3 py-2 text-sm text-dark-100 placeholder:text-dark-500 focus:outline-none focus:border-accent"
                  dir="ltr"
                />
              </div>

              <div className="flex items-center gap-3">
                <Button
                  onClick={handleCheckBackend}
                  loading={checkingBackend}
                  size="sm"
                >
                  فحص الاتصال
                </Button>
                {backendStatus === 'connected' && (
                  <span className="text-xs text-accent flex items-center gap-1">
                    <div className="w-2 h-2 rounded-full bg-accent" />
                    متصل
                  </span>
                )}
                {backendStatus === 'disconnected' && (
                  <span className="text-xs text-danger flex items-center gap-1">
                    <div className="w-2 h-2 rounded-full bg-danger" />
                    غير متصل
                  </span>
                )}
              </div>
            </div>
          )}

          {activeSection === 'appearance' && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-dark-200 mb-1.5">السمة</label>
                <div className="flex gap-2">
                  {(['dark', 'light', 'system'] as const).map((theme) => (
                    <button
                      key={theme}
                      onClick={() => updateLocal('theme', theme)}
                      className={cn(
                        'flex-1 py-2 rounded-lg text-xs font-medium transition-colors',
                        localSettings.theme === theme ? 'bg-accent/10 text-accent border border-accent/30' : 'bg-dark-700 text-dark-300 border border-dark-600'
                      )}
                    >
                      {theme === 'dark' ? 'داكن' : theme === 'light' ? 'فاتح' : 'النظام'}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeSection === 'voice' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-dark-200">تفعيل الصوت</label>
                <button
                  onClick={() => updateLocal('voiceEnabled', !localSettings.voiceEnabled)}
                  className={cn(
                    'w-10 h-5 rounded-full transition-colors relative',
                    localSettings.voiceEnabled ? 'bg-accent' : 'bg-dark-600'
                  )}
                >
                  <div className={cn(
                    'w-4 h-4 rounded-full bg-white absolute top-0.5 transition-all',
                    localSettings.voiceEnabled ? 'right-0.5' : 'right-5'
                  )} />
                </button>
              </div>

              <div>
                <label className="block text-xs font-medium text-dark-200 mb-1.5">لغة التعرف على الكلام</label>
                <select
                  value={localSettings.voiceSttLanguage}
                  onChange={(e) => updateLocal('voiceSttLanguage', e.target.value)}
                  className="w-full bg-dark-700 border border-dark-500 rounded-lg px-3 py-2 text-sm text-dark-100 focus:outline-none focus:border-accent"
                >
                  <option value="ar">العربية</option>
                  <option value="en">English</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-dark-200 mb-1.5">لغة تحويل النص لكلام</label>
                <select
                  value={localSettings.voiceTtsLanguage}
                  onChange={(e) => updateLocal('voiceTtsLanguage', e.target.value)}
                  className="w-full bg-dark-700 border border-dark-500 rounded-lg px-3 py-2 text-sm text-dark-100 focus:outline-none focus:border-accent"
                >
                  <option value="ar">العربية</option>
                  <option value="en">English</option>
                </select>
              </div>
            </div>
          )}

          {activeSection === 'notifications' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-dark-200">تفعيل الإشعارات</label>
                <button
                  onClick={() => updateLocal('notificationsEnabled', !localSettings.notificationsEnabled)}
                  className={cn(
                    'w-10 h-5 rounded-full transition-colors relative',
                    localSettings.notificationsEnabled ? 'bg-accent' : 'bg-dark-600'
                  )}
                >
                  <div className={cn(
                    'w-4 h-4 rounded-full bg-white absolute top-0.5 transition-all',
                    localSettings.notificationsEnabled ? 'right-0.5' : 'right-5'
                  )} />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="flex justify-end gap-2 mt-6 pt-4 border-t border-dark-600">
        <Button variant="secondary" onClick={() => setSettingsOpen(false)}>
          إلغاء
        </Button>
        <Button onClick={handleSave}>
          حفظ
        </Button>
      </div>
    </Modal>
  )
}
