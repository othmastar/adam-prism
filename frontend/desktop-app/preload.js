const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('adamAPI', {
  getConfig: () => ipcRenderer.invoke('get-config'),
  saveConfig: (config) => ipcRenderer.invoke('save-config', config),
  minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
  closeWindow: () => ipcRenderer.invoke('close-window'),
  onOpenSettings: (cb) => ipcRenderer.on('open-settings', cb),
});
