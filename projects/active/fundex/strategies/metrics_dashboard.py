"""
Dashboard de métricas - Correlaciones y análisis entre datos
"""
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

SYMBOLS = ['SOL-USD', 'ETH-USD', 'BNB-USD', 'BTC-USD']

def get_data(symbol, period="1y"):
    df = yf.download(symbol, period=period, progress=False)
    if hasattr(df.columns, 'levels'):
        df.columns = df.columns.get_level_values(0)
    return df['Close']

def calculate_metrics():
    print("="*70)
    print("DASHBOARD DE MÉTRICAS - CORRELACIONES Y ANÁLISIS")
    print("="*70)

    # Obtener datos
    print("\nDescargando datos...")
    prices = pd.DataFrame()
    for symbol in SYMBOLS:
        prices[symbol] = get_data(symbol)

    returns = prices.pct_change().dropna()

    # 1. CORRELACIONES
    print("\n" + "="*70)
    print("📊 MATRIZ DE CORRELACIÓN")
    print("="*70)
    corr = returns.corr()
    print(corr.round(3))

    # 2. VOLATILIDAD
    print("\n" + "="*70)
    print("📈 VOLATILIDAD ANUALIZADA")
    print("="*70)
    vol = returns.std() * np.sqrt(365) * 100
    vol_df = pd.DataFrame({'Symbol': vol.index, 'Volatilidad %': vol.values.round(2)})
    print(vol_df.to_string(index=False))

    # 3. SHARPE RATIO (asumiendo rf=0)
    print("\n" + "="*70)
    print("⚡ SHARPE RATIO (últimos 365 días)")
    print("="*70)
    sharpe = (returns.mean() * 365) / (returns.std() * np.sqrt(365))
    sharpe_df = pd.DataFrame({'Symbol': sharpe.index, 'Sharpe': sharpe.values.round(3)})
    sharpe_df = sharpe_df.sort_values('Sharpe', ascending=False)
    print(sharpe_df.to_string(index=False))

    # 4. MAX DRAWDOWN
    print("\n" + "="*70)
    print("📉 MAX DRAWDOWN")
    print("="*70)
    dd_results = []
    for symbol in SYMBOLS:
        cummax = prices[symbol].cummax()
        drawdown = (prices[symbol] - cummax) / cummax * 100
        max_dd = drawdown.min()
        dd_results.append({'Symbol': symbol, 'Max DD %': round(max_dd, 2)})
    dd_df = pd.DataFrame(dd_results)
    print(dd_df.to_string(index=False))

    # 5. BETA vs BTC
    print("\n" + "="*70)
    print("🎯 BETA vs BTC")
    print("="*70)
    btc_ret = returns['BTC-USD']
    beta_results = []
    for symbol in SYMBOLS:
        if symbol != 'BTC-USD':
            cov = returns[symbol].cov(btc_ret)
            var = btc_ret.var()
            beta = cov / var
            beta_results.append({'Symbol': symbol, 'Beta': round(beta, 3)})
    beta_df = pd.DataFrame(beta_results)
    print(beta_df.to_string(index=False))

    # 6. RENDIMIENTO ACUMULADO
    print("\n" + "="*70)
    print("💰 RENDIMIENTO ACUMULADO (YTD)")
    print("="*70)
    ytd = ((prices.iloc[-1] / prices.iloc[0]) - 1) * 100
    ytd_df = pd.DataFrame({'Symbol': ytd.index, 'YTD %': ytd.values.round(2)})
    ytd_df = ytd_df.sort_values('YTD %', ascending=False)
    print(ytd_df.to_string(index=False))

    # 7. MOMENTUM SCORE
    print("\n" + "="*70)
    print("🚀 MOMENTUM SCORE")
    print("="*70)
    momentum = []
    for symbol in SYMBOLS:
        p = prices[symbol]
        # Score = (precio actual / SMA20 - 1) + (SMA20 / SMA50 - 1)
        sma20 = p.rolling(20).mean().iloc[-1]
        sma50 = p.rolling(50).mean().iloc[-1]
        current = p.iloc[-1]
        score = ((current / sma20 - 1) * 50) + ((sma20 / sma50 - 1) * 50)
        momentum.append({
            'Symbol': symbol,
            'Price': round(current, 2),
            'SMA20': round(sma20, 2),
            'SMA50': round(sma50, 2),
            'Score': round(score, 2)
        })
    mom_df = pd.DataFrame(momentum).sort_values('Score', ascending=False)
    print(mom_df.to_string(index=False))

    # RESUMEN FINAL
    print("\n" + "="*70)
    print("🏆 RANKING FINAL (Sharpe + Momentum - DD)")
    print("="*70)

    final_scores = []
    for symbol in SYMBOLS:
        s = sharpe_df[sharpe_df['Symbol'] == symbol]['Sharpe'].values[0]
        m = mom_df[mom_df['Symbol'] == symbol]['Score'].values[0] / 100
        d = abs(dd_df[dd_df['Symbol'] == symbol]['Max DD %'].values[0]) / 100
        score = s + m - d
        final_scores.append({'Symbol': symbol, 'Score': round(score, 3)})

    final_df = pd.DataFrame(final_scores).sort_values('Score', ascending=False)
    print(final_df.to_string(index=False))

    # Guardar
    metrics = {
        'correlation': corr.to_dict(),
        'volatility': vol.to_dict(),
        'sharpe': sharpe.to_dict(),
        'momentum': {m['Symbol']: m['Score'] for m in momentum},
        'final_ranking': final_df.to_dict('records')
    }

    pd.DataFrame(final_scores).to_csv('/home/l0ve/fundex/backtests/metrics_summary.csv', index=False)
    corr.to_csv('/home/l0ve/fundex/backtests/correlation_matrix.csv')

    print("\n✅ Métricas guardadas en backtests/")

    return metrics

if __name__ == "__main__":
    calculate_metrics()
