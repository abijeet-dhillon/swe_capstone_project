import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  getAppVersion: (): Promise<string> => ipcRenderer.invoke('get-app-version'),
  selectZipFile: (): Promise<{ containerPath: string; fileName: string } | null> =>
    ipcRenderer.invoke('select-zip-file'),
  prepareZipForUpload: (
    filePath: string,
  ): Promise<{ containerPath: string; fileName: string } | null> =>
    ipcRenderer.invoke('prepare-zip-for-upload', filePath),
  prepareDroppedZipForUpload: (
    fileName: string,
    bytes: Uint8Array,
  ): Promise<{ containerPath: string; fileName: string } | null> =>
    ipcRenderer.invoke('prepare-dropped-zip-for-upload', { fileName, bytes }),
  platform: process.platform,
})
