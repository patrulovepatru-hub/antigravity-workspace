#!/bin/bash
# Web3 Bug Bounty Toolkit Setup

set -e

echo "[*] Web3 Security Tools Installer"
echo "=================================="

# Foundry (forge, cast, anvil)
echo "[+] Installing Foundry..."
curl -L https://foundry.paradigm.xyz | bash
source ~/.bashrc
foundryup

# Slither (static analyzer)
echo "[+] Installing Slither..."
pip3 install slither-analyzer

# Mythril (symbolic execution)
echo "[+] Installing Mythril..."
pip3 install mythril

# Solidity compiler
echo "[+] Installing solc-select..."
pip3 install solc-select
solc-select install 0.8.20
solc-select use 0.8.20

# Optional: Echidna (fuzzer) - requires Haskell
# echo "[+] Installing Echidna..."
# Uncomment if needed - large install

echo ""
echo "[*] Installation complete!"
echo ""
echo "Tools installed:"
echo "  - forge/cast/anvil (Foundry)"
echo "  - slither (static analysis)"
echo "  - mythril (symbolic execution)"
echo "  - solc (Solidity compiler)"
echo ""
echo "Quick commands:"
echo "  forge init myproject    # New Foundry project"
echo "  slither .               # Analyze current project"
echo "  cast call <addr> <sig>  # Call contract"
echo "  anvil --fork-url <rpc>  # Local fork"
