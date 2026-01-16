const express = require('express');
const { exec } = require('child_process');
const path = require('path');
const os = require('os');

const app = express();
const PORT = 3000;

app.use(express.static('public'));
app.use(express.json());

// Helper to get local IP
function getLocalIp() {
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        return iface.address;
      }
    }
  }
  return 'localhost';
}

// Define available actions
const actions = {
  'status': { cmd: 'echo "Everything is fine, Patri! System is online."', label: 'Check Status 🛡️' },
  'stats': { cmd: 'wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value', label: 'System Stats 📊' },
  'open-github': { cmd: 'start https://github.com', label: 'Open GitHub 🐙' },
  'list-processes': { cmd: 'tasklist /FI "STATUS eq RUNNING" /FO TABLE', label: 'Running Tasks 🖥️' },
  'git-status': { cmd: 'git status', label: 'Git Status 🌿' },
  'lock-pc': { cmd: 'rundll32.exe user32.dll,LockWorkStation', label: 'Lock PC 🔒' },
};

app.get('/api/actions', (req, res) => {
  res.json(actions);
});

app.post('/api/execute', (req, res) => {
  const { actionKey } = req.body;
  const action = actions[actionKey];

  if (!action) {
    return res.status(400).json({ error: 'Invalid action' });
  }

  exec(action.cmd, { cwd: __dirname }, (error, stdout, stderr) => {
    if (error) {
      return res.json({ success: false, output: stderr || error.message });
    }
    res.json({ success: true, output: stdout });
  });
});

app.listen(PORT, '0.0.0.0', () => {
  const ip = getLocalIp();
  console.log(`Server running at http://localhost:${PORT}`);
  console.log(`To access from iPhone, go to: http://${ip}:${PORT}`);
});
