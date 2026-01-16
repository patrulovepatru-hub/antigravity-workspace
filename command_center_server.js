const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3001;
const IS_CLOUD = process.env.K_SERVICE !== undefined; // Cloud Run sets this

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// For Cloud Run, we need to use Pub/Sub to communicate with local PC
// Commands get queued and the local agent picks them up

// In-memory command queue (replace with Pub/Sub in production)
const commandQueue = [];
const commandResults = new Map();

// ===== CLOUD ENDPOINTS =====

// Queue a command for the local agent
app.post('/api/queue-command', (req, res) => {
    const { action, params } = req.body;
    const commandId = Date.now().toString(36) + Math.random().toString(36).substr(2);

    commandQueue.push({
        id: commandId,
        action,
        params,
        timestamp: new Date().toISOString(),
        status: 'pending'
    });

    res.json({
        success: true,
        commandId,
        message: `Comando "${action}" encolado. ID: ${commandId}`
    });
});

// Get pending commands (for local agent polling)
app.get('/api/pending-commands', (req, res) => {
    const pending = commandQueue.filter(c => c.status === 'pending');
    res.json({ commands: pending });
});

// Report command result (from local agent)
app.post('/api/command-result', (req, res) => {
    const { commandId, result, error } = req.body;

    const cmd = commandQueue.find(c => c.id === commandId);
    if (cmd) {
        cmd.status = error ? 'failed' : 'completed';
        cmd.result = result;
        cmd.error = error;
        commandResults.set(commandId, { result, error, completedAt: new Date() });
    }

    res.json({ success: true });
});

// Check command status
app.get('/api/command-status/:id', (req, res) => {
    const cmd = commandQueue.find(c => c.id === req.params.id);
    if (!cmd) {
        return res.json({ found: false });
    }
    res.json({ found: true, ...cmd });
});

// ===== ORIGINAL ENDPOINTS (for local mode) =====

if (!IS_CLOUD) {
    const { exec, spawn } = require('child_process');

    const PATHS = {
        binance: path.join(__dirname, 'projects', 'active', 'binance'),
        fundex: path.join(__dirname, 'projects', 'active', 'fundex'),
        inmigraLegal: path.join(__dirname, 'projects', 'active', 'inmigra-legal'),
        pipeline: path.join(__dirname, 'pipeline')
    };

    const activeProcesses = {};

    // Security - Open Binance folder
    app.post('/api/security/reports', (req, res) => {
        exec(`explorer "${PATHS.binance}"`, (error) => {
            if (error) return res.json({ success: false, error: error.message });
            res.json({ success: true, message: 'Abriendo carpeta de reportes Binance...' });
        });
    });

    // Fundex - Start backtest
    app.post('/api/fundex/backtest', (req, res) => {
        const pythonScript = path.join(PATHS.fundex, 'paper_trading.py');

        if (activeProcesses.fundex) {
            return res.json({ success: false, error: 'Fundex ya está corriendo' });
        }

        const proc = spawn('python', [pythonScript], { cwd: PATHS.fundex, shell: true });
        activeProcesses.fundex = proc;

        proc.on('close', () => { delete activeProcesses.fundex; });

        res.json({ success: true, message: 'Paper Trading iniciado', pid: proc.pid });
    });

    // Fundex - Status
    app.get('/api/fundex/status', (req, res) => {
        res.json({ running: !!activeProcesses.fundex, pid: activeProcesses.fundex?.pid || null });
    });

    // Fundex - Stop
    app.post('/api/fundex/stop', (req, res) => {
        if (activeProcesses.fundex) {
            activeProcesses.fundex.kill();
            delete activeProcesses.fundex;
            res.json({ success: true, message: 'Fundex detenido' });
        } else {
            res.json({ success: false, error: 'Fundex no está corriendo' });
        }
    });

    // Inmigra Legal - Start
    app.post('/api/inmigra/start', (req, res) => {
        res.json({ success: false, message: 'Inmigra-Legal aún no está configurado', setup_needed: true });
    });

    // VM - SSH
    app.post('/api/vm/ssh', (req, res) => {
        const vmIP = req.body.ip || '192.168.192.128';
        exec(`wt ssh l0ve@${vmIP}`, (error) => {
            if (error) {
                exec(`start powershell -NoExit -Command "ssh l0ve@${vmIP}"`, (err2) => {
                    if (err2) return res.json({ success: false, error: err2.message });
                    res.json({ success: true, message: `Conectando a ${vmIP}...` });
                });
            } else {
                res.json({ success: true, message: `Conectando a ${vmIP}...` });
            }
        });
    });
}

// ===== COMMON ENDPOINTS =====

// Stats
app.get('/api/stats', (req, res) => {
    res.json({
        gcpCredits: 1300,
        activeProjects: 4,
        vulnerabilities: 7,
        storageUsed: '512 MB',
        lastSync: new Date().toISOString(),
        mode: IS_CLOUD ? 'cloud' : 'local',
        pendingCommands: commandQueue.filter(c => c.status === 'pending').length
    });
});

// Health check
app.get('/api/health', (req, res) => {
    res.json({ status: 'online', uptime: process.uptime(), mode: IS_CLOUD ? 'cloud' : 'local' });
});

// Serve Command Center
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'antigravity_command_center.html'));
});

app.listen(PORT, () => {
    console.log(`\n🚀 Antigravity Command Center [${IS_CLOUD ? 'CLOUD' : 'LOCAL'} MODE]`);
    console.log(`   http://localhost:${PORT}`);
    if (IS_CLOUD) {
        console.log(`\n☁️  Running in Cloud Run mode`);
        console.log(`   Commands will be queued for local agent pickup`);
    }
    console.log(`\n`);
});
