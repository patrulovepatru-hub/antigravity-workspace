# CLAUDE.md

WebExploit Toolkit - Plataforma de pentesting para formación en ciberseguridad.

## Project Overview

Toolkit modular de pentesting con GUI y CLI. Incluye módulos para:
- Reconocimiento (subdomain, DNS, OSINT)
- Scanning (ports, directories, fuzzing)
- Vulnerability Assessment (SQLi, XSS, LFI, SSRF)
- Exploitation (payloads, encoders, WAF bypass)
- Post-Exploitation (credentials, exfiltration)
- Web3/Blockchain (contracts, DeFi, tokens)
- Reporting (HTML, Markdown, Bug Bounty)

## Build & Run Commands

```bash
# GUI
python gui.py

# CLI - List tools
python toolkit.py --list

# CLI - Run tool
python toolkit.py <module> <tool> <target> [args]

# Examples
python toolkit.py recon subdomain example.com
python toolkit.py vuln sqli "https://example.com?id=1"
python toolkit.py web3 contract 0x... --network ethereum

# Attack Chains
python core/chain_runner.py --list
python core/chain_runner.py full_web_audit https://target.com
```

## Architecture

```
Tools/
├── gui.py              # GUI principal (Tkinter)
├── toolkit.py          # CLI launcher
├── lib/                # Librerías compartidas
│   ├── colors.py       # Output coloreado
│   ├── http_client.py  # HTTPClient con sessions
│   └── utils.py        # Utilidades comunes
├── core/               # Core infrastructure
│   ├── wizard.py       # Attack Wizard (flujo automatizado)
│   ├── chain_runner.py # Attack Chains executor
│   └── evidence.py     # Evidence collector
├── config/             # Configuración YAML
│   ├── presets.yaml    # Presets por herramienta
│   ├── tool_forms.yaml # Formularios dinámicos GUI
│   └── attack_chains.yaml
├── 01-recon/           # Módulo reconocimiento
├── 02-scanning/        # Módulo scanning
├── 03-vuln-assessment/ # Módulo vulnerabilidades
├── 04-exploitation/    # Módulo explotación
├── 05-post-exploitation/
├── 06-reporting/       # Generación de reportes
└── 07-web3/            # Módulo Web3/Blockchain
    ├── smart-contracts/
    ├── defi/
    └── wallet/
```

## Key Files

| Archivo | Propósito |
|---------|-----------|
| `gui.py` | GUI con 3 tabs: Tools, Wizard, Chains |
| `toolkit.py` | CLI launcher principal |
| `core/wizard.py` | Flujo automatizado de ataque |
| `core/chain_runner.py` | Ejecutor de attack chains |
| `config/presets.yaml` | Presets (quick/standard/deep) |
| `07-web3/smart-contracts/contract_analyzer.py` | Análisis de Solidity |
| `07-web3/defi/token_analyzer.py` | Análisis de tokens |

## Patterns

- Cada herramienta: clase principal + argparse main()
- Output JSON con `-o output.json`
- Presets: quick, standard, deep, stealth
- HTTPClient compartido para requests
- Colors: success(), error(), warning(), info(), banner()
