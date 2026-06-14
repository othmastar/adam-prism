import { autoUpdater, ProgressInfo, UpdateInfo } from 'electron-updater'
import { app, dialog } from 'electron'
import { sendToRenderer } from './windows'
import log from 'electron-log'

// [PHASE2] Auto-update with security hardening
// - Only allows update from configured GitHub releases
// - Verifies update signatures (electron-updater does this by default)
// - Shows user-friendly dialogs for update events
// - Logs all events for auditability

export function initUpdater(): void {
  // [PHASE2-SECURITY] Don't allow downgrade
  autoUpdater.allowDowngrade = false
  // [PHASE2-SECURITY] Don't allow prerelease by default
  autoUpdater.allowPrerelease = false
  // [PHASE2-SECURITY] Set source URL to GitHub releases only
  autoUpdater.setFeedURL({
    provider: 'github',
    owner: 'othmastar',
    repo: 'adam-prism',
    releaseType: 'release'
  })
  // Manual download for user control
  autoUpdater.autoDownload = false
  autoUpdater.autoInstallOnAppQuit = true

  autoUpdater.on('checking-for-update', () => {
    log.info('[UPDATER] Checking for update...')
    sendToRenderer('update-status', { status: 'checking' })
  })

  autoUpdater.on('update-available', (info: UpdateInfo) => {
    log.info(`[UPDATER] Update available: ${info.version}`)
    sendToRenderer('update-status', { status: 'available', version: info.version })
    // Show user prompt
    dialog
      .showMessageBox({
        type: 'info',
        title: 'Update Available',
        message: `Adam Prism ${info.version} is available.`,
        detail: 'Would you like to download and install it now?',
        buttons: ['Download', 'Later'],
        defaultId: 0,
        cancelId: 1
      })
      .then((result) => {
        if (result.response === 0) {
          autoUpdater.downloadUpdate()
        }
      })
  })

  autoUpdater.on('update-not-available', (info: UpdateInfo) => {
    log.info(`[UPDATER] Up to date: ${info.version}`)
    sendToRenderer('update-status', { status: 'up-to-date' })
  })

  autoUpdater.on('download-progress', (progress: ProgressInfo) => {
    sendToRenderer('update-status', {
      status: 'downloading',
      percent: progress.percent,
      speed: progress.bytesPerSecond
    })
  })

  autoUpdater.on('update-downloaded', (info: UpdateInfo) => {
    log.info(`[UPDATER] Update downloaded: ${info.version}`)
    sendToRenderer('update-status', { status: 'ready', version: info.version })
    // Prompt user to install
    dialog
      .showMessageBox({
        type: 'info',
        title: 'Update Ready',
        message: `Adam Prism ${info.version} has been downloaded.`,
        detail: 'Restart the application to apply the update.',
        buttons: ['Restart Now', 'On Next Launch'],
        defaultId: 0,
        cancelId: 1
      })
      .then((result) => {
        if (result.response === 0) {
          autoUpdater.quitAndInstall()
        }
      })
  })

  autoUpdater.on('error', (err: Error) => {
    log.error(`[UPDATER] Error: ${err.message}`)
    sendToRenderer('update-status', { status: 'error', message: err.message })
  })
}

export function checkForUpdates(): void {
  if (app.isPackaged) {
    // Only check for updates in production builds
    autoUpdater.checkForUpdates().catch((err) => {
      log.error(`[UPDATER] Check failed: ${err.message}`)
    })
  } else {
    log.info('[UPDATER] Skipped (dev mode)')
  }
}

export function installUpdate(): void {
  autoUpdater.quitAndInstall()
}
