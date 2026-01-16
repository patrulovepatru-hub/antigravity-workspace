"""
Optimización de parámetros EMA Momentum para SOL-USD
"""
import pandas as pd
import numpy as np
import yfinance as yf
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import warnings
warnings.filterwarnings('ignore')

def ema(close, period):
    return pd.Series(close).ewm(span=period, adjust=False).mean()

def rsi(close, period=14):
    delta = pd.Series(close).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

class EMAMomentum(Strategy):
    fast = 9
    slow = 21
    rsi_period = 14
    rsi_upper = 70
    rsi_lower = 30

    def init(self):
        self.ema_fast = self.I(ema, self.data.Close, self.fast)
        self.ema_slow = self.I(ema, self.data.Close, self.slow)
        self.rsi = self.I(rsi, self.data.Close, self.rsi_period)

    def next(self):
        if pd.isna(self.rsi[-1]):
            return
        price = self.data.Close[-1]
        size = max(1, int(self.equity * 0.95 / price))

        if crossover(self.ema_fast, self.ema_slow) and self.rsi[-1] < self.rsi_upper:
            if not self.position:
                self.buy(size=size)
        elif (crossover(self.ema_slow, self.ema_fast) or self.rsi[-1] > 80) and self.position:
            self.position.close()

def get_data(symbol="SOL-USD", period="1y"):
    df = yf.download(symbol, period=period, progress=False)
    if hasattr(df.columns, 'levels'):
        df.columns = df.columns.get_level_values(0)
    return df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

def optimize():
    print("="*60)
    print("OPTIMIZACIÓN EMA MOMENTUM - SOL-USD")
    print("="*60)

    data = get_data("SOL-USD")
    cash = max(100000, data['Close'].iloc[-1] * 100)

    bt = Backtest(data, EMAMomentum, cash=cash, commission=0.001)

    # Optimizar
    stats, heatmap = bt.optimize(
        fast=range(5, 15, 2),
        slow=range(15, 35, 5),
        rsi_period=[10, 14, 21],
        rsi_upper=[65, 70, 75],
        maximize='Sharpe Ratio',
        return_heatmap=True
    )

    print(f"\n{'='*60}")
    print("MEJORES PARÁMETROS")
    print("="*60)
    print(f"Fast EMA:    {stats._strategy.fast}")
    print(f"Slow EMA:    {stats._strategy.slow}")
    print(f"RSI Period:  {stats._strategy.rsi_period}")
    print(f"RSI Upper:   {stats._strategy.rsi_upper}")

    print(f"\n{'='*60}")
    print("RESULTADOS OPTIMIZADOS")
    print("="*60)
    print(f"Return:      {stats['Return [%]']:.2f}%")
    print(f"Sharpe:      {stats['Sharpe Ratio']:.2f}")
    print(f"Max DD:      {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate:    {stats['Win Rate [%]']:.2f}%")
    print(f"Trades:      {stats['# Trades']}")

    # Guardar
    results = {
        'fast': stats._strategy.fast,
        'slow': stats._strategy.slow,
        'rsi_period': stats._strategy.rsi_period,
        'rsi_upper': stats._strategy.rsi_upper,
        'return': round(stats['Return [%]'], 2),
        'sharpe': round(stats['Sharpe Ratio'], 2),
        'max_dd': round(stats['Max. Drawdown [%]'], 2),
        'win_rate': round(stats['Win Rate [%]'], 2),
        'trades': stats['# Trades']
    }

    pd.DataFrame([results]).to_csv("/home/l0ve/fundex/backtests/optimized_params.csv", index=False)
    print("\nParámetros guardados en backtests/optimized_params.csv")

    return stats

if __name__ == "__main__":
    optimize()
