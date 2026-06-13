import { ipcMain, app, dialog, clipboard, nativeImage } from 'electron'
import { store, getAllSettings, setStoreValue } from './store'
import { getMainWindow } from './windows'
import { checkForUpdates, installUpdate } from './updater'
import { updateTrayStatus } from './tray'
import http from 'http'
import https from 'https'

function fetchUrl(url: string, options?: { method?: string; headers?: Record<string, string>; body?: string }): Promise<{ status: number; data: string }> {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url)
    const isHttps = parsedUrl.protocol === 'https:'
    const lib = isHttps ? https : http
    const reqOptions = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || (isHttps ? 443 : 80),
      path: parsedUrl.pathname + parsedUrl.search,
      method: options?.method || 'GET',
      headers: options?.headers || {}
    }
    const req = lib.request(reqOptions, (res) => {
      let data = ''
      res.on('data', (chunk) => { data += chunk })
      res.on('end', () => resolve({ status: res.statusCode || 0, data }))
    })
    req.on('error', reject)
    req.setTimeout(10000, () => { req.destroy(); reject(new Error('Request timeout')) })
    if (options?.body) req.write(options.body)
    req.end()
  })
}

export function registerIpcHandlers(): void {
  // Settings
  ipcMain.handle('get-settings', () => getAllSettings())

  ipcMain.handle('set-setting', (_event, key: string, value: unknown) => {
    setStoreValue(key as never, value as never)
    return true
  })

  ipcMain.handle('set-settings', (_event, settings: Record<string, unknown>) => {
    for (const [key, value] of Object.entries(settings)) {
      store.set(key as never, value as never)
    }
    return true
  })

  // Backend health check
  ipcMain.handle('check-backend', async () => {
    try {
      const backendUrl = store.get('backendUrl')
      const apiKey = store.get('apiKey')
      const headers: Record<string, string> = {}
      if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`
      }
      const response = await fetchUrl(`${backendUrl}/api/status`, { headers })
      const isConnected = response.status === 200
      updateTrayStatus(isConnected ? 'connected' : 'error')
      return { connected: isConnected, status: response.status, data: response.data }
    } catch (err) {
      updateTrayStatus('disconnected')
      return { connected: false, status: 0, data: (err as Error).message }
    }
  })

  // API proxy
  ipcMain.handle('api-request', async (_event, options: {
    method: string
    path: string
    body?: string
    headers?: Record<string, string>
    stream?: boolean
  }) => {
    try {
      const backendUrl = store.get('backendUrl')
      const apiKey = store.get('apiKey')
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...options.headers
      }
      if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`
      }
      const response = await fetchUrl(`${backendUrl}${options.path}`, {
        method: options.method,
        headers,
        body: options.body
      })
      return { status: response.status, data: response.data }
    } catch (err) {
      return { status: 0, data: (err as Error).message }
    }
  })

  // Window controls
  ipcMain.handle('window-minimize', () => {
    const win = getMainWindow()
    if (win) win.minimize()
  })

  ipcMain.handle('window-maximize', () => {
    const win = getMainWindow()
    if (win) {
      if (win.isMaximized()) {
        win.unmaximize()
      } else {
        win.maximize()
      }
    }
  })

  ipcMain.handle('window-close', () => {
    const win = getMainWindow()
    if (win) win.close()
  })

  ipcMain.handle('window-is-maximized', () => {
    const win = getMainWindow()
    return win ? win.isMaximized() : false
  })

  // Clipboard
  ipcMain.handle('clipboard-write', (_event, text: string) => {
    clipboard.writeText(text)
  })

  ipcMain.handle('clipboard-read', () => {
    return clipboard.readText()
  })

  // Dialogs
  ipcMain.handle('show-open-dialog', async (_event, options: Electron.OpenDialogOptions) => {
    const win = getMainWindow()
    if (!win) return { canceled: true, filePaths: [] }
    return dialog.showOpenDialog(win, options)
  })

  ipcMain.handle('show-save-dialog', async (_event, options: Electron.SaveDialogOptions) => {
    const win = getMainWindow()
    if (!win) return { canceled: true, filePath: '' }
    return dialog.showSaveDialog(win, options)
  })

  // Updates
  ipcMain.handle('check-for-updates', () => checkForUpdates())
  ipcMain.handle('install-update', () => installUpdate())

  // App info
  ipcMain.handle('get-app-version', () => app.getVersion())

  // Onboarding complete
  ipcMain.handle('complete-onboarding', (_event, settings: { backendUrl: string; apiKey: string; isLocal: boolean }) => {
    store.set('backendUrl', settings.backendUrl)
    store.set('apiKey', settings.apiKey)
    store.set('isLocal', settings.isLocal)
    store.set('onboardingComplete', true)
    return true
  })
}
