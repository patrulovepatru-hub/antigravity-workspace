# 📦 WORKSPACE CONTEXT CONSOLIDADO
> Generado: 2026-01-14T21:58 | Ruta: `Vm projects structured`

---

## 🗂️ ESTRUCTURA PRINCIPAL #tiene mi backup en ?

```
Vm projects structured/
├── 📄 PROYECTOS.md              # Índice de proyectos
├── 📄 WORKSPACE_CONTEXT.md      # Este archivo
├── 📁 _Archives/                # Archivos de mudanza (~300MB comprimidos)
│   └── 📄 legacy_projects_list.md  # [NEW] Lista legacy de proyectos (desde wateber)
├── 📁 _Config/                  # Configuraciones (.bashrc, .zshrc, .claude.json)
├── 📁 instagram-dashboard/      # ✅ Dashboard Next.js (COMPILA OK)
├── 📁 public/
│   └── 📄 antigravity_command_center.html  # [NEW] Dashboard UI cyberpunk
├── 📁 projects/
│   ├── active/                  # Proyectos activos (2124 items)
│   ├── archived/                # Archivados (1999 items)
│   ├── ideas/                   # Ideas en desarrollo
│   └── tools/                   # Herramientas
└── 📁 vm shared folder/         # Carpeta compartida VM
```

---

## 🚀 PROYECTOS ACTIVOS #que proyectos tengo activos?

### 1. 📸 Instagram Dashboard
| Campo | Valor |
|-------|-------|
| **Path** | `instagram-dashboard/` |
| **Stack** | Next.js 16.1.1 + React 19 + TailwindCSS 4 + Recharts |
| **Estado Build** | ✅ COMPILA CORRECTAMENTE |
| **Lint** | ✅ SIN ERRORES |
| **Rutas** | `/`, `/dashboard`, `/dashboard/analytics`, `/dashboard/media`, `/dashboard/settings` |
| **Advertencias** | Recharts warnings sobre dimensiones de gráficos (no bloqueante, SSR-related) |

**Comandos:**
```bash
cd instagram-dashboard
npm run dev     # Desarrollo
npm run build   # Producción
npm run lint    # Verificar código
```

---

### 2. 💰 Fundex (Trading Algorítmico)
| Campo | Valor |
|-------|-------|
| **Path** | `projects/active/fundex/` |
| **Stack** | Python + FastAPI (webhook) + Trading strategies |
| **Componentes** | Paper trading, Signal generator, Strategy analyzers |

**Archivos clave:**
- `paper_trading.py` - Simulador de trading
- `webhook_server.py` - Servidor para señales TradingView
- `strategies/` - 7 estrategias (SMA, RSI Bollinger, etc.)

**Docs:** `TRADINGVIEW_SETUP.md`

---

### 3. 🔐 Binance Bug Bounty (BSC Genesis Contracts)
| Campo | Valor |
|-------|-------|
| **Path** | `projects/active/binance/` |
| **Objetivo** | Auditoría seguridad smart contracts BSC |
| **Bounty Range** | $500 - $100,000 USD |

**Vulnerabilidades encontradas:**

| # | Severidad | Nombre | Bounty Est. |
|---|-----------|--------|-------------|
| 1 | 🔴 CRÍTICA | Reentrancy en StakeHub.redelegate() | $50-100k |
| 2 | 🔴 CRÍTICA | Flash Loan Governance Attack | $75-100k |
| 3 | 🟠 ALTA | Unchecked Return Value en distributeReward() | $10-50k |
| 4 | 🟠 ALTA | Slash Reward Manipulation | $10-25k |
| 5 | 🟡 MEDIA | Token Recovery Lock Extension Attack | $5-15k |

**Submissions listos:** 
- ✅ `01_StakeHub_Reentrancy.zip`
- ✅ `02_GovToken_FlashLoan.zip`  
- ✅ `03_Slash_Reward_Manipulation.zip`

---

### 4. 🤖 Autonomous Business
| Campo | Valor |
|-------|-------|
| **Path** | `projects/active/autonomous-business/` |
| **Stack** | Python autonomous engine |
| **Core** | `autonomous_engine.py` (22KB) |
| **Dependencias** | Sites, Analytics, Templates |

---

### 5. 🌐 Web3 DApps Collection
| Campo | Valor |
|-------|-------|
| **Path** | `projects/active/web3-dapps/` |
| **Items** | 1803+ archivos |
| **Contenido** | Targets, scripts, tools para análisis web3 |

---

### 6. 🎮 Otros proyectos activos
- **LoL Analytics** - `projects/active/Lol-analytics/`
- **Key-drop.com** - `projects/active/key-drop.com/` (auditoría)
- **BetFury** - `projects/active/betfury/`
- **inmigra-legal** - `projects/active/inmigra-legal/` (vacío - en setup)

---

## 💡 IDEAS PIPELINE

### Escrow Smart Contracts
- Path: `projects/ideas/escrow-smart-contracts.md`

### Freestyle Adaptativo
- Path: `projects/ideas/freestyle-adaptativo.md`

---

## 🗄️ ARCHIVOS MUDANZA

| Archivo | Tamaño (comprimido) |
|---------|---------------------|
| `mudanza_binance_20260110.tar.gz` | ~21 MB |
| `mudanza_pentest_20260110.tar.gz` | ~265 MB |

---

## ⚠️ PROBLEMAS CONOCIDOS

### PowerShell Execution Policy
```
❌ npm scripts bloqueados en PowerShell
✅ Solución: Usar `cmd /c "npm run ..."` como prefijo
```

### Instagram Dashboard - Recharts
```
⚠️ Warning: The width(-1) and height(-1) of chart should be greater than 0
📝 Impacto: Solo advertencia, no bloquea build
🔧 Fix: Añadir minWidth/minHeight a contenedores de gráficos
```

---

## 📋 ACCIONES PENDIENTES

- [ ] Enviar submissions de Binance Bug Bounty
- [ ] Configurar DeFi Control Bot (Slack/Telegram)
- [ ] Setup inmigra-legal stack (FastAPI + Next.js)
- [ ] Integrar Fundex con prop firm API

---

## 🔧 COMANDOS RÁPIDOS

```bash
# Instagram Dashboard
cmd /c "npm run dev" --prefix instagram-dashboard

# Python projects (activar venv primero)
# fundex: python paper_trading.py
# autonomous-business: python core/autonomous_engine.py

# Binance - Foundry tests
forge test --fork-url https://bsc-dataseed.binance.org/ -vvv
```

---

*Último update: 2026-01-14 21:58 UTC*
