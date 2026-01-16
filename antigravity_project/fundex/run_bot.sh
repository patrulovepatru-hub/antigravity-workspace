#!/bin/bash
# Fundex Paper Trading Bot
# Uso: ./run_bot.sh [--live]

cd /home/l0ve/fundex
source venv/bin/activate

if [ "$1" == "--live" ]; then
    echo "🤖 Iniciando bot en modo LIVE (Ctrl+C para detener)"
    python paper_trading.py --live
else
    echo "📊 Ejecutando check único"
    python paper_trading.py
fi
