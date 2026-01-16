#!/usr/bin/env node
/**
 * ANTIGRAVITY - Direct Chat Agent
 * Uses Gemini (GCP) with fallback to local LLM
 */

import chalk from 'chalk';
import ora from 'ora';
import figlet from 'figlet';
import gradient from 'gradient-string';
import readline from 'readline';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ═══════════════════════ CONFIG ═══════════════════════
const CONFIG = {
    gemini: {
        project: 'gen-lang-client-0988614926',
        location: 'us-central1',
        model: 'gemini-1.5-flash'
    },
    localLLM: 'http://localhost:1234/v1/chat/completions',
    serviceAccountPath: path.join(__dirname, '..', 'pipeline', 'keys', 'service-account.json')
};

let history = [];
let accessToken = null;

// ═══════════════════════ AUTH ═══════════════════════
async function getGoogleAccessToken() {
    try {
        const keyFile = JSON.parse(fs.readFileSync(CONFIG.serviceAccountPath, 'utf8'));

        // Create JWT
        const now = Math.floor(Date.now() / 1000);
        const header = Buffer.from(JSON.stringify({ alg: 'RS256', typ: 'JWT' })).toString('base64url');
        const payload = Buffer.from(JSON.stringify({
            iss: keyFile.client_email,
            scope: 'https://www.googleapis.com/auth/cloud-platform',
            aud: 'https://oauth2.googleapis.com/token',
            iat: now,
            exp: now + 3600
        })).toString('base64url');

        // Sign JWT (using native crypto)
        const crypto = await import('crypto');
        const sign = crypto.createSign('RSA-SHA256');
        sign.update(`${header}.${payload}`);
        const signature = sign.sign(keyFile.private_key, 'base64url');

        const jwt = `${header}.${payload}.${signature}`;

        // Exchange JWT for access token
        const response = await fetch('https://oauth2.googleapis.com/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=${jwt}`
        });

        const data = await response.json();
        return data.access_token;
    } catch (error) {
        return null;
    }
}

// ═══════════════════════ LLM PROVIDERS ═══════════════════════
async function askGemini(message, history) {
    if (!accessToken) {
        accessToken = await getGoogleAccessToken();
    }
    if (!accessToken) return null;

    const url = `https://${CONFIG.gemini.location}-aiplatform.googleapis.com/v1/projects/${CONFIG.gemini.project}/locations/${CONFIG.gemini.location}/publishers/google/models/${CONFIG.gemini.model}:generateContent`;

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            contents: [
                ...history.map(h => ({
                    role: h.role === 'assistant' ? 'model' : 'user',
                    parts: [{ text: h.content }]
                })),
                { role: 'user', parts: [{ text: message }] }
            ],
            generationConfig: {
                temperature: 0.7,
                maxOutputTokens: 1024
            },
            systemInstruction: {
                parts: [{ text: 'You are Antigravity, an expert AI coding assistant. Be concise, helpful, and friendly. Use emojis occasionally.' }]
            }
        })
    });

    const data = await response.json();
    return data.candidates?.[0]?.content?.parts?.[0]?.text || null;
}

async function askLocal(message, history) {
    const response = await fetch(CONFIG.localLLM, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            model: 'local-model',
            messages: [
                { role: 'system', content: 'You are Antigravity, an expert AI coding assistant. Be concise, helpful, and friendly. Use emojis occasionally.' },
                ...history,
                { role: 'user', content: message }
            ],
            temperature: 0.7,
            max_tokens: 800
        })
    });

    const data = await response.json();
    return data.choices?.[0]?.message?.content || null;
}

// ═══════════════════════ MAIN CHAT ═══════════════════════
async function chat(message) {
    history.push({ role: 'user', content: message });

    const spinner = ora({
        text: chalk.hex('#00d2ff')(' thinking...'),
        spinner: 'dots12',
        color: 'magenta'
    }).start();

    let reply = null;
    let provider = null;

    // Try Gemini first
    try {
        reply = await askGemini(message, history.slice(-20));
        if (reply) provider = 'Gemini';
    } catch (e) { }

    // Fallback to local
    if (!reply) {
        try {
            reply = await askLocal(message, history.slice(-20));
            if (reply) provider = 'Local';
        } catch (e) { }
    }

    spinner.stop();

    if (reply) {
        history.push({ role: 'assistant', content: reply });
        const badge = provider === 'Gemini' ? chalk.hex('#4285f4')('[Gemini]') : chalk.hex('#00ff85')('[Local]');
        console.log('');
        console.log(chalk.hex('#bc13fe')('  🤖 ') + chalk.gray(badge) + ' ' + chalk.white(reply));
        console.log('');
    } else {
        console.log('');
        console.log(chalk.hex('#ff5f56')('  ⚠️  No LLM available. Start LM Studio or check GCP credentials.'));
        console.log('');
    }
}

// ═══════════════════════ UI ═══════════════════════
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const neon = gradient(['#bc13fe', '#00d2ff', '#00ff85']);

async function intro() {
    console.clear();

    const lines = figlet.textSync('ANTIGRAVITY', { font: 'ANSI Shadow' }).split('\n');
    for (const line of lines) {
        console.log(neon(line));
        await sleep(60);
    }

    console.log('');
    await sleep(200);

    // Status check
    const hasGemini = fs.existsSync(CONFIG.serviceAccountPath);
    const geminiStatus = hasGemini ? chalk.hex('#00ff85')('✓ Gemini') : chalk.hex('#ff5f56')('✗ Gemini');
    const localStatus = chalk.hex('#ffbd2e')('? Local LLM');

    console.log(chalk.gray(`  Providers: ${geminiStatus} ${localStatus}`));
    console.log('');

    // Welcome
    const welcome = "  Hello! I'm your AI coding assistant. How can I help you today?";
    process.stdout.write(chalk.hex('#00d2ff')('\n  🤖 '));
    for (const char of welcome) {
        process.stdout.write(chalk.white(char));
        await sleep(15);
    }

    console.log('\n');
    console.log(chalk.gray('  ─────────────────────────────────────────────────────'));
    console.log(chalk.gray('  Type your message and press Enter. Type "exit" to quit.'));
    console.log(chalk.gray('  ─────────────────────────────────────────────────────'));
    console.log('');
}

// ═══════════════════════ MAIN ═══════════════════════
async function main() {
    await intro();

    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });

    const prompt = () => {
        rl.question(chalk.hex('#00ff85')('  You: '), async (input) => {
            const trimmed = input.trim();

            if (trimmed.toLowerCase() === 'exit') {
                console.log(chalk.gray('\n  👋 Goodbye!\n'));
                rl.close();
                process.exit(0);
            }

            if (trimmed) {
                await chat(trimmed);
            }

            prompt();
        });
    };

    prompt();
}

main().catch(console.error);
