import { app, BrowserWindow, dialog, ipcMain } from 'electron'
import path from 'path'
import fs from 'fs'

// Resolve the uploads directory relative to the project root.
// In dev, __dirname is frontend/out/main/ — walk up to find the project root.
function getUploadsDir(): string {
  // Try to locate the project root by looking for docker-compose.yml
  let dir = path.resolve(__dirname)
  for (let i = 0; i < 6; i++) {
    if (fs.existsSync(path.join(dir, 'docker-compose.yml'))) {
      const uploads = path.join(dir, 'uploads')
      if (!fs.existsSync(uploads)) fs.mkdirSync(uploads, { recursive: true })
      return uploads
    }
    dir = path.dirname(dir)
  }
  // Fallback: use a directory next to the app
  const fallback = path.join(app.getPath('userData'), 'uploads')
  if (!fs.existsSync(fallback)) fs.mkdirSync(fallback, { recursive: true })
  return fallback
}

function createWindow(): void {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    title: 'Digital Work Artifact Miner',
  })

  // In development, load from Vite dev server
  if (process.env.VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL)
    mainWindow.webContents.openDevTools()
  } else {
    // In production, load the built files
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'))
  }
}

// Select a ZIP file via native dialog, copy it to the uploads dir,
// and return the container-accessible path (/uploads/filename.zip).
ipcMain.handle('select-zip-file', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [{ name: 'ZIP Archives', extensions: ['zip'] }],
  })
  if (result.canceled || result.filePaths.length === 0) return null
  return copyToUploads(result.filePaths[0])
})

// Copy an arbitrary file path into the uploads dir and return the
// Docker-container-accessible path.
ipcMain.handle('prepare-zip-for-upload', async (_event, filePath: string) => {
  if (!filePath || !fs.existsSync(filePath)) return null
  return copyToUploads(filePath)
})

function copyToUploads(srcPath: string): { containerPath: string; fileName: string } {
  const uploadsDir = getUploadsDir()
  const baseName = path.basename(srcPath)
  // Avoid collisions with a timestamp prefix
  const destName = `${Date.now()}_${baseName}`
  const destPath = path.join(uploadsDir, destName)
  fs.copyFileSync(srcPath, destPath)
  // The Docker container sees this as /uploads/<file>
  return { containerPath: `/uploads/${destName}`, fileName: baseName }
}

app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
