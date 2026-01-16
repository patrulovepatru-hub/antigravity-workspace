"""
Análisis de sesiones horarias para trading
"""
import pandas as pd
import numpy as np
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

def get_hourly_data(symbol="SOL-USD", period="60d"):
    """Obtiene datos horarios"""
    df = yf.download(symbol, period=period, interval="1h", progress=False)
    if hasattr(df.columns, 'levels'):
        df.columns = df.columns.get_level_values(0)
    return df

def analyze_sessions(symbol="SOL-USD"):
    print("="*60)
    print(f"ANÁLISIS DE SESIONES - {symbol}")
    print("="*60)

    df = get_hourly_data(symbol)
    if df.empty:
        print("No hay datos horarios disponibles")
        return

    df['returns'] = df['Close'].pct_change() * 100
    df['hour'] = df.index.hour
    df['day'] = df.index.dayofweek
    df['volatility'] = df['returns'].abs()

    # Sesiones
    def get_session(hour):
        if 0 <= hour < 8:
            return 'Asia'
        elif 8 <= hour < 14:
            return 'London'
        elif 14 <= hour < 21:
            return 'New York'
        else:
            return 'After Hours'

    df['session'] = df['hour'].apply(get_session)

    # Análisis por sesión
    print("\n📊 VOLATILIDAD POR SESIÓN")
    print("-"*40)
    session_stats = df.groupby('session').agg({
        'returns': ['mean', 'std', 'count'],
        'volatility': 'mean',
        'Volume': 'mean'
    }).round(4)
    print(session_stats)

    # Mejores horas
    print("\n⏰ MEJORES HORAS (por volatilidad)")
    print("-"*40)
    hourly = df.groupby('hour').agg({
        'returns': 'mean',
        'volatility': 'mean'
    }).round(4)
    hourly = hourly.sort_values('volatility', ascending=False)
    print(hourly.head(10))

    # Mejores días
    print("\n📅 RENDIMIENTO POR DÍA")
    print("-"*40)
    days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    daily = df.groupby('day').agg({
        'returns': ['mean', 'sum'],
        'volatility': 'mean'
    }).round(4)
    daily.index = [days[i] for i in daily.index]
    print(daily)

    # Heatmap data
    heatmap = df.pivot_table(
        values='volatility',
        index='hour',
        columns='day',
        aggfunc='mean'
    ).round(4)

    print("\n🔥 HEATMAP VOLATILIDAD (Hora x Día)")
    print("-"*40)
    print(heatmap)

    # Guardar
    session_summary = {
        'session': [],
        'avg_return': [],
        'volatility': [],
        'recommendation': []
    }

    for sess in ['Asia', 'London', 'New York']:
        sess_data = df[df['session'] == sess]
        avg_ret = sess_data['returns'].mean()
        vol = sess_data['volatility'].mean()
        rec = 'TRADE' if vol > df['volatility'].mean() else 'SKIP'
        session_summary['session'].append(sess)
        session_summary['avg_return'].append(round(avg_ret, 4))
        session_summary['volatility'].append(round(vol, 4))
        session_summary['recommendation'].append(rec)

    pd.DataFrame(session_summary).to_csv("/home/l0ve/fundex/backtests/session_analysis.csv", index=False)

    print("\n" + "="*60)
    print("RECOMENDACIONES")
    print("="*60)
    best_session = max(session_summary['volatility'])
    idx = session_summary['volatility'].index(best_session)
    print(f"✅ Mejor sesión: {session_summary['session'][idx]}")
    print(f"   Volatilidad: {best_session:.4f}")

    return session_summary

if __name__ == "__main__":
    analyze_sessions("SOL-USD")
    print("\n")
    analyze_sessions("ETH-USD")
