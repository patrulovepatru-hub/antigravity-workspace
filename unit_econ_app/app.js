// App State / Data
const STORAGE_KEY = 'unit_econ_data_v1';
let appData = JSON.parse(localStorage.getItem(STORAGE_KEY)) || {
    capital: 0,
    transactions: [],
    monthlyIn: 0,
    monthlyOut: 0
};

// DOM Elements
const views = document.querySelectorAll('.view-section');
const navBtns = document.querySelectorAll('.nav-btn');
const pageTitle = document.getElementById('page-title');

const kpiCapital = document.getElementById('total-capital');
const kpiIn = document.getElementById('monthly-in');
const kpiOut = document.getElementById('monthly-out');
const kpiNet = document.getElementById('net-flow');

const txForm = document.getElementById('transaction-form');
const txList = document.getElementById('transaction-list');

// Charts
let capitalChartInstance = null;
let flowChartInstance = null;

// Currency Formatter
const formatMoney = (amount) => {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
};

// Init
function init() {
    updateDashboard();
    setupNavigation();
    setupForm();
    renderTransactions();
    initCharts();
}

// Navigation
function setupNavigation() {
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetView = btn.dataset.view;

            // UI Toggle
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            views.forEach(view => {
                view.classList.remove('active');
                if (view.id === targetView) {
                    view.classList.add('active');
                }
            });

            // Update Title
            pageTitle.innerText = btn.innerText.trim();

            if (targetView === 'dashboard') {
                updateDashboard(); // Refresh stats
            }
        });
    });
}

// Data Processing
function updateDashboard() {
    // Recalculate totals from transactions to be safe
    let totalCap = 0;
    let mIn = 0;
    let mOut = 0;

    const currentMonth = new Date().getMonth();
    const currentYear = new Date().getFullYear();

    appData.transactions.forEach(tx => {
        const date = new Date(tx.date);

        if (tx.type === 'in') {
            totalCap += tx.amount;
            if (date.getMonth() === currentMonth && date.getFullYear() === currentYear) {
                mIn += tx.amount;
            }
        } else {
            totalCap -= tx.amount;
            if (date.getMonth() === currentMonth && date.getFullYear() === currentYear) {
                mOut += tx.amount;
            }
        }
    });

    // Update Text
    kpiCapital.innerText = formatMoney(totalCap);
    kpiIn.innerText = formatMoney(mIn);
    kpiOut.innerText = formatMoney(mOut);

    const net = mIn - mOut;
    kpiNet.innerText = (net > 0 ? '+' : '') + formatMoney(net);
    kpiNet.className = `value money ${net >= 0 ? 'positive' : 'negative'}`;

    updateCharts();
}

// Transaction Logic
function setupForm() {
    txForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const type = document.querySelector('input[name="type"]:checked').value;
        const amount = parseFloat(document.getElementById('amount').value);
        const description = document.getElementById('description').value;
        const category = document.getElementById('category').value;

        if (!amount || amount <= 0) return;

        const newTx = {
            id: Date.now(),
            date: new Date().toISOString(),
            type,
            amount,
            description,
            category
        };

        appData.transactions.unshift(newTx); // Add to start
        saveData();

        // Reset form
        txForm.reset();

        // Show success/feedback (could act toast here)
        renderTransactions();
        alert('Transaction Logged!'); // Placeholder for better UI
    });
}

function saveData() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(appData));
    updateDashboard();
}

function renderTransactions() {
    txList.innerHTML = '';
    const recent = appData.transactions.slice(0, 10);

    recent.forEach(tx => {
        const li = document.createElement('li');
        li.className = 'transaction-item';
        const isEntrance = tx.type === 'in';

        li.innerHTML = `
            <div class="t-info">
                <h4>${tx.description}</h4>
                <span>${new Date(tx.date).toLocaleDateString()} • ${tx.category}</span>
            </div>
            <div class="t-amount" style="color: var(--${isEntrance ? 'success' : 'danger'})">
                ${isEntrance ? '+' : '-'}${formatMoney(tx.amount)}
            </div>
        `;
        txList.appendChild(li);
    });
}

// Charts (Mock logic for now, real data projection would be complex)
function initCharts() {
    const ctxFlow = document.getElementById('flowChart').getContext('2d');
    const ctxCap = document.getElementById('capitalChart').getContext('2d');

    // Configs... will update in updateCharts
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = 'Inter';

    flowChartInstance = new Chart(ctxFlow, {
        type: 'doughnut',
        data: {
            labels: ['Income', 'Expenses'],
            datasets: [{
                data: [1, 1], // Placeholder
                backgroundColor: ['#10b981', '#ef4444'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right' }
            }
        }
    });

    capitalChartInstance = new Chart(ctxCap, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Capital',
                data: [0, 0, 0, 0, 0, 0],
                borderColor: '#8b5cf6',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } },
                x: { grid: { display: false } }
            }
        }
    });
}

function updateCharts() {
    if (!flowChartInstance || !capitalChartInstance) return;

    // Update Flow Chart (Monthly)
    const currentMonth = new Date().getMonth();
    let mIn = 0;
    let mOut = 0;

    appData.transactions.forEach(tx => {
        const d = new Date(tx.date);
        if (d.getMonth() === currentMonth) {
            if (tx.type === 'in') mIn += tx.amount;
            else mOut += tx.amount;
        }
    });

    // Avoid 0/0
    if (mIn === 0 && mOut === 0) {
        flowChartInstance.data.datasets[0].data = [1, 0]; // Empty state
    } else {
        flowChartInstance.data.datasets[0].data = [mIn, mOut];
    }
    flowChartInstance.update();

    // Update Capital Chart (Mock History for demo - real app needs history tracking)
    // For now we just show a straight line or accumulated tx?
    // Let's bucket transactions by month for the last 6 months.

    // ... logic for proper capital history is needed, but for MVP:
    // We will just show current capital as the last point, and 0 for others to start.
    // Ideally we re-calculate capital at each month end.
}

window.addEventListener('DOMContentLoaded', init);
