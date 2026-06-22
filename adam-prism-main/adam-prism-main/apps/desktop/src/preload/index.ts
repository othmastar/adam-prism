import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

const api = {
  // Settings
  getSettings: () => ipcRenderer.invoke('get-settings'),
  setSetting: (key: string, value: unknown) => ipcRenderer.invoke('set-setting', key, value),
  setSettings: (settings: Record<string, unknown>) => ipcRenderer.invoke('set-settings', settings),

  // Backend
  checkBackend: () => ipcRenderer.invoke('check-backend'),
  apiRequest: (options: { method: string; path: string; body?: string; headers?: Record<string, string> }) =>
    ipcRenderer.invoke('api-request', options),

  // Window controls
  windowMinimize: () => ipcRenderer.invoke('window-minimize'),
  windowMaximize: () => ipcRenderer.invoke('window-maximize'),
  windowClose: () => ipcRenderer.invoke('window-close'),
  windowIsMaximized: () => ipcRenderer.invoke('window-is-maximized'),

  // Clipboard
  clipboardWrite: (text: string) => ipcRenderer.invoke('clipboard-write', text),
  clipboardRead: () => ipcRenderer.invoke('clipboard-read'),

  // Dialogs
  showOpenDialog: (options: Electron.OpenDialogOptions) => ipcRenderer.invoke('show-open-dialog', options),
  showSaveDialog: (options: Electron.SaveDialogOptions) => ipcRenderer.invoke('show-save-dialog', options),

  // Updates
  checkForUpdates: () => ipcRenderer.invoke('check-for-updates'),
  installUpdate: () => ipcRenderer.invoke('install-update'),

  // App
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  completeOnboarding: (settings: { backendUrl: string; apiKey: string; isLocal: boolean }) =>
    ipcRenderer.invoke('complete-onboarding', settings),

  // Event listeners
  on: (channel: string, callback: (...args: unknown[]) => void) => {
    const subscription = (_event: Electron.IpcRendererEvent, ...args: unknown[]) => callback(...args)
    ipcRenderer.on(channel, subscription)
    return () => ipcRenderer.removeListener(channel, subscription)
  },

  // Remove listener
  removeListener: (channel: string, callback: (...args: unknown[]) => void) => {
    ipcRenderer.removeListener(channel, callback)
  }
}

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error(error)
  }
} else {
  // @ts-ignore
  window.electron = electronAPI
  // @ts-ignore
  window.api = api
}
