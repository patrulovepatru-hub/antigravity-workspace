"""
Generador de señales en tiempo real - EMA Momentum
"""
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

# Parámetros optimizados (se actualizan tras optimización)
PARAMS = {
    'fast': 9,
    'slow': 21,
    'rsi_period': 14,
    'rsi_upper': 70,
    'symbols': ['SOL-USD', 'ETH-USD', 'BNB-USD']
}

def ema(close, period):
    return pd.Series(close).ewm(span=period, adjust=False).mean()

def rsi(close, period=14):
    delta = pd.Series(close).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_latest_data(symbol, period="5d", interval="1h"):
    """Obtiene datos recientes"""
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if hasattr(df.columns, 'levels'):
        df.columns = df.columns.get_level_values(0)
    return df

def calculate_signals(symbol):
    """Calcula señales para un símbolo"""
    df = get_latest_data(symbol)
    if df.empty or len(df) < PARAMS['slow'] + 5:
        return None

    df['ema_fast'] = ema(df['Close'], PARAMS['fast'])
    df['ema_slow'] = ema(df['Close'], PARAMS['slow'])
    df['rsi'] = rsi(df['Close'], PARAMS['rsi_period'])

    # Última fila
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Detectar señales
    signal = 'HOLD'
    strength = 0

    # Cruce alcista
    if prev['ema_fast'] <= prev['ema_slow'] and last['ema_fast'] > last['ema_slow']:
        if last['rsi'] < PARAMS['rsi_upper']:
            signal = 'BUY'
            strength = min(100, (PARAMS['rsi_upper'] - last['rsi']) * 2)

    # Cruce bajista
    elif prev['ema_fast'] >= prev['ema_slow'] and last['ema_fast'] < last['ema_slow']:
        signal = 'SELL'
        strength = min(100, last['rsi'])

    # RSI extremo
    if last['rsi'] > 80:
        signal = 'SELL'
        strength = 90

    return {
        'symbol': symbol,
        'timestamp': str(datetime.now()),
        'price': round(last['Close'], 2),
        'ema_fast': round(last['ema_fast'], 2),
        'ema_slow': round(last['ema_slow'], 2),
        'rsi': round(last['rsi'], 2),
        'signal': signal,
        'strength': round(strength, 1),
        'trend': 'UP' if last['ema_fast'] > last['ema_slow'] else 'DOWN'
    }

def generate_all_signals():
    """Genera señales para todos los símbolos"""
    print("="*60)
    print(f"SEÑALES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    signals = []
    for symbol in PARAMS['symbols']:
        sig = calculate_signals(symbol)
        if sig:
            signals.append(sig)
            emoji = '🟢' if sig['signal'] == 'BUY' else '🔴' if sig['signal'] == 'SELL' else '⚪'
            print(f"\n{emoji} {sig['symbol']}")
            print(f"   Price:  ${sig['price']}")
            print(f"   Signal: {sig['signal']} (strength: {sig['strength']}%)")
            print(f"   RSI:    {sig['rsi']}")
            print(f"   Trend:  {sig['trend']}")

    # Guardar señales
    with open('/home/l0ve/fundex/signals/latest_signals.json', 'w') as f:
        json.dump(signals, f, indent=2)

    # También CSV
    pd.DataFrame(signals).to_csv('/home/l0ve/fundex/signals/signals_log.csv',
                                  mode='a', header=False, index=False)

    print("\n" + "="*60)
    active = [s for s in signals if s['signal'] != 'HOLD']
    if active:
        print(f"⚡ {len(active)} SEÑALES ACTIVAS")
        for s in active:
            print(f"   → {s['signal']} {s['symbol']} @ ${s['price']}")
    else:
        print("😴 Sin señales activas")

    return signals

if __name__ == "__main__":
    generate_all_signals()
