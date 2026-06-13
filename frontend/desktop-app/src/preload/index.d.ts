import { ElectronAPI } from '@electron-toolkit/preload'

interface AdamAPI {
  getSettings(): Promise<Record<string, unknown>>
  setSetting(key: string, value: unknown): Promise<boolean>
  setSettings(settings: Record<string, unknown>): Promise<boolean>
  checkBackend(): Promise<{ connected: boolean; status: number; data: string }>
  apiRequest(options: { method: string; path: string; body?: string; headers?: Record<string, string> }): Promise<{ status: number; data: string }>
  windowMinimize(): Promise<void>
  windowMaximize(): Promise<void>
  windowClose(): Promise<void>
  windowIsMaximized(): Promise<boolean>
  clipboardWrite(text: string): Promise<void>
  clipboardRead(): Promise<string>
  showOpenDialog(options: Electron.OpenDialogOptions): Promise<Electron.OpenDialogReturnValue>
  showSaveDialog(options: Electron.SaveDialogOptions): Promise<Electron.SaveDialogReturnValue>
  checkForUpdates(): Promise<void>
  installUpdate(): Promise<void>
  getAppVersion(): Promise<string>
  completeOnboarding(settings: { backendUrl: string; apiKey: string; isLocal: boolean }): Promise<boolean>
  on(channel: string, callback: (...args: unknown[]) => void): () => void
  removeListener(channel: string, callback: (...args: unknown[]) => void): void
}

declare global {
  interface Window {
    electron: ElectronAPI
    api: AdamAPI
  }
}
