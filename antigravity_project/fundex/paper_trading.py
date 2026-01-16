#!/usr/bin/env python3
"""
Paper Trading Bot - Fundex Challenge
Simula trading con la estrategia EMA Momentum optimizada
"""
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import time
import os
import warnings
warnings.filterwarnings('ignore')

# ============ CONFIGURACIÓN ============
CONFIG = {
    'symbol': 'SOL-USD',
    'initial_balance': 5000,      # Challenge 5k
    'risk_per_trade': 0.01,       # 1% por trade
    'max_daily_loss': 0.04,       # 4% max DD diario
    'profit_target': 0.10,        # 10% objetivo
    'fast_ema': 9,
    'slow_ema': 20,
    'rsi_period': 14,
    'rsi_upper': 70,
    'rsi_lower': 30,
}

STATE_FILE = '/home/l0ve/fundex/paper_state.json'
TRADES_FILE = '/home/l0ve/fundex/paper_trades.csv'

# ============ INDICADORES ============
def ema(close, period):
    return pd.Series(close).ewm(span=period, adjust=False).mean()

def rsi(close, period=14):
    delta = pd.Series(close).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ============ ESTADO ============
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        'balance': CONFIG['initial_balance'],
        'position': None,
        'entry_price': 0,
        'position_size': 0,
        'trades': [],
        'daily_pnl': 0,
        'start_date': str(datetime.now().date()),
        'status': 'ACTIVE'
    }

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

# ============ DATA ============
def get_data(symbol, period="5d", interval="1h"):
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if hasattr(df.columns, 'levels'):
        df.columns = df.columns.get_level_values(0)
    return df

# ============ SEÑALES ============
def get_signal(df):
    df['ema_fast'] = ema(df['Close'], CONFIG['fast_ema'])
    df['ema_slow'] = ema(df['Close'], CONFIG['slow_ema'])
    df['rsi'] = rsi(df['Close'], CONFIG['rsi_period'])

    last = df.iloc[-1]
    prev = df.iloc[-2]

    signal = 'HOLD'

    # BUY: EMA cross up + RSI no sobrecomprado
    if prev['ema_fast'] <= prev['ema_slow'] and last['ema_fast'] > last['ema_slow']:
        if last['rsi'] < CONFIG['rsi_upper']:
            signal = 'BUY'

    # SELL: EMA cross down o RSI > 80
    elif prev['ema_fast'] >= prev['ema_slow'] and last['ema_fast'] < last['ema_slow']:
        signal = 'SELL'
    elif last['rsi'] > 80:
        signal = 'SELL'

    return signal, last['Close'], last['rsi']

# ============ TRADING ============
def execute_trade(state, signal, price):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if signal == 'BUY' and state['position'] is None:
        # Calcular tamaño de posición (1% riesgo)
        risk_amount = state['balance'] * CONFIG['risk_per_trade']
        position_size = risk_amount / (price * 0.02)  # Asumiendo 2% stop loss
        position_size = min(position_size, state['balance'] * 0.95 / price)

        cost = position_size * price
        if cost <= state['balance']:
            state['balance'] -= cost
            state['position'] = 'LONG'
            state['entry_price'] = price
            state['position_size'] = position_size

            trade = {
                'timestamp': timestamp,
                'type': 'BUY',
                'price': price,
                'size': position_size,
                'value': cost,
                'balance': state['balance']
            }
            state['trades'].append(trade)
            log_trade(trade)

            print(f"  🟢 BUY  {position_size:.4f} @ ${price:.2f} = ${cost:.2f}")
            return True

    elif signal == 'SELL' and state['position'] == 'LONG':
        value = state['position_size'] * price
        pnl = value - (state['position_size'] * state['entry_price'])
        pnl_pct = (price / state['entry_price'] - 1) * 100

        state['balance'] += value
        state['daily_pnl'] += pnl

        trade = {
            'timestamp': timestamp,
            'type': 'SELL',
            'price': price,
            'size': state['position_size'],
            'value': value,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'balance': state['balance']
        }
        state['trades'].append(trade)
        log_trade(trade)

        emoji = '💰' if pnl > 0 else '📉'
        print(f"  {emoji} SELL {state['position_size']:.4f} @ ${price:.2f} = ${value:.2f} (PnL: ${pnl:.2f} / {pnl_pct:.2f}%)")

        state['position'] = None
        state['entry_price'] = 0
        state['position_size'] = 0
        return True

    return False

def log_trade(trade):
    df = pd.DataFrame([trade])
    df.to_csv(TRADES_FILE, mode='a', header=not os.path.exists(TRADES_FILE), index=False)

# ============ CHECKS ============
def check_limits(state):
    total_pnl = state['balance'] - CONFIG['initial_balance']
    total_pnl_pct = total_pnl / CONFIG['initial_balance'] * 100
    daily_pnl_pct = state['daily_pnl'] / CONFIG['initial_balance'] * 100

    # Check profit target
    if total_pnl_pct >= CONFIG['profit_target'] * 100:
        state['status'] = 'TARGET_REACHED'
        print(f"\n🎯 ¡OBJETIVO ALCANZADO! +{total_pnl_pct:.2f}%")
        return False

    # Check max daily loss
    if daily_pnl_pct <= -CONFIG['max_daily_loss'] * 100:
        state['status'] = 'DAILY_LIMIT'
        print(f"\n🛑 LÍMITE DIARIO ALCANZADO: {daily_pnl_pct:.2f}%")
        return False

    # Check max drawdown
    if total_pnl_pct <= -10:
        state['status'] = 'MAX_DD'
        print(f"\n💀 MAX DRAWDOWN: {total_pnl_pct:.2f}%")
        return False

    return True

# ============ MAIN ============
def run_paper_trading(continuous=False):
    print("="*60)
    print("PAPER TRADING - FUNDEX CHALLENGE")
    print("="*60)
    print(f"Symbol:     {CONFIG['symbol']}")
    print(f"Balance:    ${CONFIG['initial_balance']}")
    print(f"Target:     +{CONFIG['profit_target']*100}%")
    print(f"Max DD:     -{CONFIG['max_daily_loss']*100}%")
    print("="*60)

    state = load_state()

    while True:
        try:
            # Reset daily PnL si es nuevo día
            today = str(datetime.now().date())
            if state.get('start_date') != today:
                state['daily_pnl'] = 0
                state['start_date'] = today

            # Obtener datos y señal
            df = get_data(CONFIG['symbol'])
            signal, price, rsi_val = get_signal(df)

            # Stats
            total_pnl = state['balance'] - CONFIG['initial_balance']
            if state['position']:
                unrealized = (price - state['entry_price']) * state['position_size']
                total_pnl += unrealized

            total_pnl_pct = total_pnl / CONFIG['initial_balance'] * 100

            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {CONFIG['symbol']}")
            print(f"  Price: ${price:.2f} | RSI: {rsi_val:.1f} | Signal: {signal}")
            print(f"  Balance: ${state['balance']:.2f} | PnL: ${total_pnl:.2f} ({total_pnl_pct:+.2f}%)")

            if state['position']:
                print(f"  Position: {state['position']} {state['position_size']:.4f} @ ${state['entry_price']:.2f}")

            # Ejecutar trade si hay señal
            if signal != 'HOLD':
                execute_trade(state, signal, price)

            # Verificar límites
            if not check_limits(state):
                break

            # Guardar estado
            save_state(state)

            if not continuous:
                break

            print("\n  ⏳ Esperando 5 min...")
            time.sleep(300)

        except KeyboardInterrupt:
            print("\n\n⏹️ Paper trading detenido")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            if not continuous:
                break
            time.sleep(60)

    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN PAPER TRADING")
    print("="*60)
    total_pnl = state['balance'] - CONFIG['initial_balance']
    print(f"Balance Final:  ${state['balance']:.2f}")
    print(f"PnL Total:      ${total_pnl:.2f} ({total_pnl/CONFIG['initial_balance']*100:+.2f}%)")
    print(f"Trades:         {len(state['trades'])}")
    print(f"Status:         {state['status']}")

    save_state(state)
    return state

if __name__ == "__main__":
    import sys
    continuous = '--live' in sys.argv
    run_paper_trading(continuous=continuous)
