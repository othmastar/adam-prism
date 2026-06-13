import { Tray, Menu, nativeImage, app } from 'electron'
import { join } from 'path'
import { getMainWindow } from './windows'

let tray: Tray | null = null

export function createTray(): Tray {
  const icon = nativeImage.createFromPath(join(__dirname, '../../resources/icon.png'))
  tray = new Tray(icon.resize({ width: 16, height: 16 }))

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'فتح آدم بريزم',
      click: () => {
        const win = getMainWindow()
        if (win) {
          win.show()
          win.focus()
        }
      }
    },
    {
      label: 'محادثة جديدة',
      click: () => {
        const win = getMainWindow()
        if (win) {
          win.show()
          win.focus()
          win.webContents.send('new-session')
        }
      }
    },
    { type: 'separator' },
    {
      label: 'حالة الخادم',
      click: () => {
        const win = getMainWindow()
        if (win) {
          win.show()
          win.webContents.send('check-server-status')
        }
      }
    },
    { type: 'separator' },
    {
      label: 'إعدادات',
      click: () => {
        const win = getMainWindow()
        if (win) {
          win.show()
          win.focus()
          win.webContents.send('open-settings')
        }
      }
    },
    { type: 'separator' },
    {
      label: 'خروج',
      click: () => {
        app.quit()
      }
    }
  ])

  tray.setToolTip('Adam Prism')
  tray.setContextMenu(contextMenu)

  tray.on('double-click', () => {
    const win = getMainWindow()
    if (win) {
      win.show()
      win.focus()
    }
  })

  return tray
}

export function updateTrayStatus(status: 'connected' | 'disconnected' | 'error'): void {
  if (!tray) return
  const statusLabels = {
    connected: '🟢 آدم بريزم - متصل',
    disconnected: '🔴 آدم بريزم - غير متصل',
    error: '⚠️ آدم بريزم - خطأ'
  }
  tray.setToolTip(statusLabels[status])
}

export function destroyTray(): void {
  if (tray) {
    tray.destroy()
    tray = null
  }
}
