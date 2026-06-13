import { autoUpdater } from 'electron-updater'
import { sendToRenderer } from './windows'

export function initUpdater(): void {
  autoUpdater.autoDownload = false
  autoUpdater.autoInstallOnAppQuit = true

  autoUpdater.on('checking-for-update', () => {
    sendToRenderer('update-status', { status: 'checking' })
  })

  autoUpdater.on('update-available', (info) => {
    sendToRenderer('update-status', { status: 'available', version: info.version })
    autoUpdater.downloadUpdate()
  })

  autoUpdater.on('update-not-available', () => {
    sendToRenderer('update-status', { status: 'up-to-date' })
  })

  autoUpdater.on('download-progress', (progress) => {
    sendToRenderer('update-status', {
      status: 'downloading',
      percent: progress.percent,
      speed: progress.bytesPerSecond
    })
  })

  autoUpdater.on('update-downloaded', () => {
    sendToRenderer('update-status', { status: 'ready' })
  })

  autoUpdater.on('error', (err) => {
    sendToRenderer('update-status', { status: 'error', message: err.message })
  })
}

export function checkForUpdates(): void {
  autoUpdater.checkForUpdates()
}

export function installUpdate(): void {
  autoUpdater.quitAndInstall()
}
