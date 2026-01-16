const grid = document.getElementById('actions-grid');
const output = document.getElementById('output');
const status = document.getElementById('connection-status');

function log(msg) {
    const line = document.createElement('div');
    line.textContent = `> ${msg}`;
    output.appendChild(line);
    output.scrollTop = output.scrollHeight;
}

async function fetchActions() {
    try {
        const res = await fetch('/api/actions');
        const actions = await res.json();
        status.innerHTML = '<span class="status-dot"></span> CONNECTED';
        status.style.color = '#22c55e';
        renderButtons(actions);
    } catch (e) {
        status.innerHTML = '<span class="status-dot"></span> DISCONNECTED';
        status.style.color = '#ef4444';
        log('Error connecting to server');
    }
}

function renderButtons(actions) {
    grid.innerHTML = '';
    Object.entries(actions).forEach(([key, action]) => {
        const btn = document.createElement('button');
        btn.className = 'action-btn';
        if (key === 'status') btn.className += ' full-width';

        // Extract emoji icon if present
        const emojiMatch = action.label.match(/([\p{Emoji_Presentation}\p{Emoji}\u200d]+)/u);
        const icon = emojiMatch ? emojiMatch[0] : '⚡';
        const labelText = action.label.replace(icon, '').trim();

        btn.innerHTML = `
            <div class="icon">${icon}</div>
            <span>${labelText}</span>
        `;
        btn.onclick = () => execute(key);
        grid.appendChild(btn);
    });
}

async function execute(actionKey) {
    // Haptic feedback if available
    if (window.navigator && window.navigator.vibrate) {
        window.navigator.vibrate(20);
    }

    log(`Executing ${actionKey}...`);
    try {
        const res = await fetch('/api/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ actionKey })
        });
        const data = await res.json();
        if (data.success) {
            log(data.output.trim());
        } else {
            log(`Error: ${data.output}`);
        }
    } catch (e) {
        log(`Network Error: ${e.message}`);
    }
}

fetchActions();

