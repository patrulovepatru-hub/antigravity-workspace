#!/usr/bin/env python3
"""
Webhook Server para TradingView
Recibe alertas y ejecuta operaciones
Deploy: Google Cloud Run
"""
from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# Estado del bot
STATE = {
    'balance': 5000,
    'position': None,
    'entry_price': 0,
    'trades': [],
    'status': 'ACTIVE'
}

# Configuración
CONFIG = {
    'initial_balance': 5000,
    'risk_per_trade': 0.01,
    'max_daily_loss': 0.04,
    'profit_target': 0.10,
    'secret': os.getenv('WEBHOOK_SECRET', 'fundex2024')
}

def log_event(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'balance': STATE['balance']})

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Recibe alertas de TradingView
    Formato esperado:
    {
        "secret": "fundex2024",
        "action": "BUY" o "SELL",
        "symbol": "SOLUSD",
        "price": 136.50
    }
    """
    try:
        data = request.json
        log_event(f"Webhook recibido: {data}")

        # Verificar secret
        if data.get('secret') != CONFIG['secret']:
            return jsonify({'error': 'Invalid secret'}), 401

        action = data.get('action', '').upper()
        price = float(data.get('price', 0))
        symbol = data.get('symbol', '')

        if action == 'BUY' and STATE['position'] is None:
            # Calcular tamaño
            risk = STATE['balance'] * CONFIG['risk_per_trade']
            size = risk / (price * 0.02)

            STATE['position'] = 'LONG'
            STATE['entry_price'] = price
            STATE['position_size'] = size

            trade = {
                'time': str(datetime.now()),
                'action': 'BUY',
                'symbol': symbol,
                'price': price,
                'size': size
            }
            STATE['trades'].append(trade)
            log_event(f"🟢 BUY {size:.4f} {symbol} @ ${price}")

            return jsonify({
                'status': 'executed',
                'action': 'BUY',
                'size': size,
                'price': price
            })

        elif action == 'SELL' and STATE['position'] == 'LONG':
            pnl = (price - STATE['entry_price']) * STATE['position_size']
            STATE['balance'] += STATE['position_size'] * price

            trade = {
                'time': str(datetime.now()),
                'action': 'SELL',
                'symbol': symbol,
                'price': price,
                'pnl': pnl
            }
            STATE['trades'].append(trade)

            STATE['position'] = None
            STATE['entry_price'] = 0

            emoji = '💰' if pnl > 0 else '📉'
            log_event(f"{emoji} SELL @ ${price} | PnL: ${pnl:.2f}")

            # Check si pasó el challenge
            total_pnl = STATE['balance'] - CONFIG['initial_balance']
            if total_pnl >= CONFIG['initial_balance'] * CONFIG['profit_target']:
                STATE['status'] = 'CHALLENGE_PASSED'
                log_event("🎯 ¡CHALLENGE PASADO!")

            return jsonify({
                'status': 'executed',
                'action': 'SELL',
                'pnl': pnl,
                'balance': STATE['balance']
            })

        return jsonify({'status': 'no_action', 'reason': 'Conditions not met'})

    except Exception as e:
        log_event(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    total_pnl = STATE['balance'] - CONFIG['initial_balance']
    return jsonify({
        'balance': STATE['balance'],
        'pnl': total_pnl,
        'pnl_pct': total_pnl / CONFIG['initial_balance'] * 100,
        'position': STATE['position'],
        'trades': len(STATE['trades']),
        'status': STATE['status']
    })

@app.route('/reset', methods=['POST'])
def reset():
    data = request.json or {}
    if data.get('secret') != CONFIG['secret']:
        return jsonify({'error': 'Invalid secret'}), 401

    STATE['balance'] = CONFIG['initial_balance']
    STATE['position'] = None
    STATE['trades'] = []
    STATE['status'] = 'ACTIVE'
    return jsonify({'status': 'reset', 'balance': STATE['balance']})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    log_event(f"🚀 Webhook server en puerto {port}")
    app.run(host='0.0.0.0', port=port)
