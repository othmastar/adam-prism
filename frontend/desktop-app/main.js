const { app, BrowserWindow, Tray, Menu, nativeImage, ipcMain, shell } = require('electron');
const path = require('path');

let mainWindow = null;
let tray = null;

const ENDPOINT_DEFAULT = 'http://localhost:8000';

// ── Main Window ────────────────────────────

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 420,
    height: 680,
    minWidth: 340,
    minHeight: 480,
    resizable: true,
    frame: false,
    transparent: false,
    backgroundColor: '#1a1b26',
    icon: path.join(__dirname, 'renderer', 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  mainWindow.on('close', (e) => {
    if (!app.isQuitting) {
      e.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => { mainWindow = null; });
}

// ── System Tray ────────────────────────────

function createTray() {
  const iconSize = process.platform === 'darwin' ? 22 : 16;
  let trayIcon;
  try {
    trayIcon = nativeImage.createFromPath(path.join(__dirname, 'renderer', 'icon.png'));
    trayIcon = trayIcon.resize({ width: iconSize, height: iconSize });
  } catch {
    trayIcon = nativeImage.createEmpty();
  }

  tray = new Tray(trayIcon);
  tray.setToolTip('Adam Prism');

  const contextMenu = Menu.buildFromTemplate([
    { label: '🟢 فتح آدم', click: () => mainWindow?.show() },
    { type: 'separator' },
    { label: '⚙️ الإعدادات', click: () => mainWindow?.webContents.send('open-settings') },
    { label: '📖 التعليمات', click: () => shell.openExternal('https://github.com/othmastar/adam-prism') },
    { type: 'separator' },
    { label: '🚪 خروج', click: () => { app.isQuitting = true; app.quit(); } },
  ]);

  tray.setContextMenu(contextMenu);
  tray.on('click', () => mainWindow?.show());
}

// ── IPC Handlers ───────────────────────────

ipcMain.handle('get-config', () => {
  const store = loadStore();
  return { endpoint: store.endpoint || ENDPOINT_DEFAULT };
});

ipcMain.handle('save-config', (_, config) => {
  saveStore(config);
});

ipcMain.handle('minimize-window', () => {
  mainWindow?.minimize();
});

ipcMain.handle('close-window', () => {
  mainWindow?.hide();
});

// ── Simple JSON Store ─────────────────────

const fs = require('fs');
const STORE_PATH = path.join(app.getPath('userData'), 'config.json');

function loadStore() {
  try {
    if (fs.existsSync(STORE_PATH)) {
      return JSON.parse(fs.readFileSync(STORE_PATH, 'utf-8'));
    }
  } catch { /* ignore */ }
  return { endpoint: ENDPOINT_DEFAULT };
}

function saveStore(config) {
  try {
    fs.writeFileSync(STORE_PATH, JSON.stringify(config, null, 2));
  } catch { /* ignore */ }
}

// ── App Lifecycle ──────────────────────────

app.whenReady().then(() => {
  createWindow();
  createTray();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (mainWindow === null) createWindow();
  else mainWindow.show();
});

app.isQuitting = false;
