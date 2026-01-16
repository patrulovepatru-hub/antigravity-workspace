/**
 * Local Agent - Runs on your PC and executes commands from Cloud Run
 * 
 * This agent polls the cloud server for pending commands,
 * executes them locally, and reports results back.
 */

const { exec, spawn } = require('child_process');
const path = require('path');

// Configuration
const CLOUD_URL = process.env.CLOUD_URL || 'https://command-center-XXXXX-uc.a.run.app';
const POLL_INTERVAL = 5000; // 5 seconds
const LOCAL_SERVER = 'http://localhost:3001';

const PATHS = {
    binance: path.join(__dirname, 'projects', 'active', 'binance'),
    fundex: path.join(__dirname, 'projects', 'active', 'fundex'),
    inmigraLegal: path.join(__dirname, 'projects', 'active', 'inmigra-legal'),
    pipeline: path.join(__dirname, 'pipeline')
};

const activeProcesses = {};

// Action handlers
const handlers = {
    'security/reports': async () => {
        return new Promise((resolve, reject) => {
            exec(`explorer "${PATHS.binance}"`, (error) => {
                if (error) reject(error);
                else resolve('Carpeta de Binance abierta');
            });
        });
    },

    'fundex/backtest': async () => {
        if (activeProcesses.fundex) {
            throw new Error('Fundex ya está corriendo');
        }

        const pythonScript = path.join(PATHS.fundex, 'paper_trading.py');
        const proc = spawn('python', [pythonScript], { cwd: PATHS.fundex, shell: true });
        activeProcesses.fundex = proc;

        proc.on('close', () => { delete activeProcesses.fundex; });

        return `Paper Trading iniciado (PID: ${proc.pid})`;
    },

    'fundex/stop': async () => {
        if (activeProcesses.fundex) {
            activeProcesses.fundex.kill();
            delete activeProcesses.fundex;
            return 'Fundex detenido';
        }
        throw new Error('Fundex no está corriendo');
    },

    'vm/ssh': async (params) => {
        const vmIP = params?.ip || '192.168.192.128';
        return new Promise((resolve, reject) => {
            exec(`wt ssh l0ve@${vmIP}`, (error) => {
                if (error) {
                    exec(`start powershell -NoExit -Command "ssh l0ve@${vmIP}"`, (err2) => {
                        if (err2) reject(err2);
                        else resolve(`Conectando a ${vmIP}...`);
                    });
                } else {
                    resolve(`Conectando a ${vmIP}...`);
                }
            });
        });
    }
};

// Poll for commands and execute them
async function pollCommands() {
    try {
        const url = process.env.USE_LOCAL ? LOCAL_SERVER : CLOUD_URL;
        const response = await fetch(`${url}/api/pending-commands`);
        const data = await response.json();

        for (const cmd of data.commands || []) {
            console.log(`📥 Recibido comando: ${cmd.action} (ID: ${cmd.id})`);

            try {
                const handler = handlers[cmd.action];
                if (!handler) {
                    throw new Error(`Handler no encontrado para: ${cmd.action}`);
                }

                const result = await handler(cmd.params);
                console.log(`✅ Comando ejecutado: ${result}`);

                // Report success
                await fetch(`${url}/api/command-result`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ commandId: cmd.id, result })
                });

            } catch (error) {
                console.error(`❌ Error ejecutando comando: ${error.message}`);

                // Report failure
                await fetch(`${url}/api/command-result`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ commandId: cmd.id, error: error.message })
                });
            }
        }
    } catch (error) {
        // Server not reachable - silently continue
        if (!error.message.includes('fetch')) {
            console.error('Error polling:', error.message);
        }
    }
}

// Main loop
console.log(`
🤖 Antigravity Local Agent
   Polling: ${process.env.USE_LOCAL ? LOCAL_SERVER : CLOUD_URL}
   Interval: ${POLL_INTERVAL}ms
   
   Press Ctrl+C to stop
`);

// Start polling
setInterval(pollCommands, POLL_INTERVAL);

// Also run immediately
pollCommands();

// Keep alive
process.on('SIGINT', () => {
    console.log('\n👋 Agent detenido');
    process.exit(0);
});
