const { app, BrowserWindow, Menu, Tray, nativeImage, shell, ipcMain } = require('electron');
const path = require('path');
const http = require('http');

// ============================================================
// Config
// ============================================================
const SERVER_PORT = 8788;  // Desktop app uses 8788 to avoid conflicts
const SERVER_DIR = path.join(__dirname, '..');
const STATIC_DIR = path.join(__dirname, '..', 'static');

let mainWindow = null;
let tray = null;
let serverProcess = null;

// ============================================================
// Server Management
// ============================================================
function startServer() {
  return new Promise((resolve, reject) => {
    const { spawn } = require('child_process');
    const python = path.join('/app/venv/bin/python');

    console.log(`Starting server: ${python} -m uvicorn main:app --host 127.0.0.1 --port ${SERVER_PORT}`);
    serverProcess = spawn(python, [
      '-m', 'uvicorn', 'main:app',
      '--host', '127.0.0.1',
      '--port', String(SERVER_PORT)
    ], {
      cwd: SERVER_DIR,
      env: { ...process.env, HF_HUB_OFFLINE: '1', PORT: String(SERVER_PORT) }
    });

    serverProcess.stdout.on('data', (data) => {
      const msg = data.toString();
      console.log('[Server]', msg.trim());
      if (msg.includes('Application startup complete') || msg.includes('Uvicorn running')) {
        resolve();
      }
    });

    serverProcess.stderr.on('data', (data) => {
      console.error('[Server Err]', data.toString().trim());
    });

    serverProcess.on('error', (err) => {
      console.error('Failed to start server:', err);
      reject(err);
    });

    // Timeout after 120s
    setTimeout(() => resolve(), 120000);
  });
}

function stopServer() {
  if (serverProcess) {
    serverProcess.kill('SIGTERM');
    serverProcess = null;
  }
}

function checkServer() {
  return new Promise((resolve) => {
    const req = http.get(`http://127.0.0.1:${SERVER_PORT}/api/stats`, (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(3000, () => { req.destroy(); resolve(false); });
  });
}

// ============================================================
// Window
// ============================================================
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 480,
    height: 800,
    minWidth: 380,
    minHeight: 600,
    title: '😂 Анекдот в тему',
    icon: path.join(STATIC_DIR, 'icon-512.png'),
    backgroundColor: '#0f0f1a',
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    }
  });

  // Load the SPA
  mainWindow.loadURL(`http://127.0.0.1:${SERVER_PORT}/`);

  // Open external links in browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('close', (e) => {
    e.preventDefault();
    mainWindow.hide();
  });
}

// ============================================================
// Tray
// ============================================================
function createTray() {
  const icon = nativeImage.createFromPath(path.join(STATIC_DIR, 'icon-192.png'));
  tray = new Tray(icon.resize({ width: 16, height: 16 }));

  const contextMenu = Menu.buildFromTemplate([
    { label: '😂 Анекдот в тему', enabled: false },
    { type: 'separator' },
    { label: 'Открыть', click: () => { mainWindow.show(); mainWindow.focus(); } },
    { label: 'Случайный анекдот', click: () => sendRandomJoke() },
    { type: 'separator' },
    { label: 'Выход', click: () => { stopServer(); tray = null; mainWindow.destroy(); app.quit(); } }
  ]);

  tray.setToolTip('😂 Анекдот в тему');
  tray.setContextMenu(contextMenu);
  tray.on('click', () => { mainWindow.show(); mainWindow.focus(); });
}

function sendRandomJoke() {
  if (!mainWindow) return;
  mainWindow.show();
  mainWindow.focus();
  mainWindow.webContents.executeJavaScript(`
    if (typeof randomJoke === 'function') {
      document.querySelector('[data-tab="random"]')?.click();
      randomJoke();
    }
  `);
}

// ============================================================
// IPC
// ============================================================
ipcMain.handle('get-server-url', () => `http://127.0.0.1:${SERVER_PORT}`);
ipcMain.handle('get-joke-random', async () => {
  return new Promise((resolve) => {
    http.get(`http://127.0.0.1:${SERVER_PORT}/api/joke/random`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch { resolve(null); }
      });
    }).on('error', () => resolve(null));
  });
});

// ============================================================
// App Lifecycle
// ============================================================
app.whenReady().then(async () => {
  console.log('Checking if server is already running...');
  let running = await checkServer();

  if (!running) {
    console.log('Starting backend server...');
    try {
      await startServer();
      console.log('Server started!');
    } catch (err) {
      console.error('Server failed:', err);
    }

    // Verify server is up
    for (let i = 0; i < 30; i++) {
      running = await checkServer();
      if (running) break;
      await new Promise(r => setTimeout(r, 2000));
    }
  }

  if (running) {
    createWindow();
    createTray();
    console.log(`App ready at http://127.0.0.1:${SERVER_PORT}/`);
  } else {
    console.error('Server failed to start. Opening error page.');
    mainWindow = new BrowserWindow({ width: 480, height: 400 });
    mainWindow.loadURL(`data:text/html,<h2 style="color:red;font-family:sans-serif;padding:20px">❌ Ошибка запуска сервера</h2><p style="font-family:sans-serif;padding:20px">Проверьте логи в консоли.</p>`);
  }
});

app.on('window-all-closed', (e) => {
  // Don't quit — stay in tray
});

app.on('before-quit', () => {
  stopServer();
});

app.on('activate', () => {
  if (mainWindow) mainWindow.show();
});
