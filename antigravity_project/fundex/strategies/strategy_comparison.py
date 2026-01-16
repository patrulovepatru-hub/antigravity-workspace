"""
Comparación de múltiples estrategias para Fundex Challenge
"""
import pandas as pd
import numpy as np
import yfinance as yf
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import warnings
warnings.filterwarnings('ignore')


# ============ INDICADORES ============

def sma(close, period):
    return pd.Series(close).rolling(period).mean()

def ema(close, period):
    return pd.Series(close).ewm(span=period, adjust=False).mean()

def rsi(close, period=14):
    delta = pd.Series(close).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def macd(close, fast=12, slow=26, signal=9):
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line


# ============ ESTRATEGIAS ============

class SMACrossover(Strategy):
    """SMA 10/30 Crossover"""
    n1, n2 = 10, 30

    def init(self):
        self.sma1 = self.I(sma, self.data.Close, self.n1)
        self.sma2 = self.I(sma, self.data.Close, self.n2)

    def next(self):
        price = self.data.Close[-1]
        size = max(1, int(self.equity * 0.95 / price))
        if crossover(self.sma1, self.sma2) and not self.position:
            self.buy(size=size)
        elif crossover(self.sma2, self.sma1) and self.position:
            self.position.close()


class EMAMomentum(Strategy):
    """EMA 9/21 con filtro de momentum"""
    fast, slow = 9, 21

    def init(self):
        self.ema_fast = self.I(ema, self.data.Close, self.fast)
        self.ema_slow = self.I(ema, self.data.Close, self.slow)
        self.rsi = self.I(rsi, self.data.Close, 14)

    def next(self):
        if pd.isna(self.rsi[-1]):
            return
        price = self.data.Close[-1]
        size = max(1, int(self.equity * 0.95 / price))

        # Compra: EMA cross up + RSI no sobrecomprado
        if crossover(self.ema_fast, self.ema_slow) and self.rsi[-1] < 70:
            if not self.position:
                self.buy(size=size)
        # Venta: EMA cross down o RSI sobrecomprado
        elif (crossover(self.ema_slow, self.ema_fast) or self.rsi[-1] > 80) and self.position:
            self.position.close()


class MACDStrategy(Strategy):
    """MACD crossover"""
    def init(self):
        macd_line, signal_line = macd(self.data.Close)
        self.macd = self.I(lambda: macd_line)
        self.signal = self.I(lambda: signal_line)

    def next(self):
        if pd.isna(self.macd[-1]) or pd.isna(self.signal[-1]):
            return
        price = self.data.Close[-1]
        size = max(1, int(self.equity * 0.95 / price))

        if crossover(self.macd, self.signal) and not self.position:
            self.buy(size=size)
        elif crossover(self.signal, self.macd) and self.position:
            self.position.close()


class TripleEMA(Strategy):
    """Triple EMA: 5/13/34"""
    def init(self):
        self.ema5 = self.I(ema, self.data.Close, 5)
        self.ema13 = self.I(ema, self.data.Close, 13)
        self.ema34 = self.I(ema, self.data.Close, 34)

    def next(self):
        price = self.data.Close[-1]
        size = max(1, int(self.equity * 0.95 / price))

        # Tendencia alcista: EMA5 > EMA13 > EMA34
        if self.ema5[-1] > self.ema13[-1] > self.ema34[-1]:
            if not self.position:
                self.buy(size=size)
        # Tendencia bajista: EMA5 < EMA13 < EMA34
        elif self.ema5[-1] < self.ema13[-1] < self.ema34[-1]:
            if self.position:
                self.position.close()


# ============ MAIN ============

def get_data(symbol, period="1y"):
    df = yf.download(symbol, period=period, progress=False)
    if hasattr(df.columns, 'levels'):
        df.columns = df.columns.get_level_values(0)
    return df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()


def run_comparison():
    symbols = ["ETH-USD", "SOL-USD", "BNB-USD"]
    strategies = [
        ("SMA Crossover", SMACrossover),
        ("EMA Momentum", EMAMomentum),
        ("MACD", MACDStrategy),
        ("Triple EMA", TripleEMA),
    ]

    results = []

    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f"PROBANDO: {symbol}")
        print('='*60)

        data = get_data(symbol)
        cash = max(100000, data['Close'].iloc[-1] * 100)

        for name, strat in strategies:
            try:
                bt = Backtest(data, strat, cash=cash, commission=0.001)
                stats = bt.run()

                result = {
                    'symbol': symbol,
                    'strategy': name,
                    'return': round(stats['Return [%]'], 2),
                    'buy_hold': round(stats['Buy & Hold Return [%]'], 2),
                    'max_dd': round(stats['Max. Drawdown [%]'], 2),
                    'sharpe': round(stats['Sharpe Ratio'], 2) if pd.notna(stats['Sharpe Ratio']) else 0,
                    'trades': stats['# Trades'],
                    'win_rate': round(stats['Win Rate [%]'], 2) if pd.notna(stats['Win Rate [%]']) else 0
                }
                results.append(result)
                print(f"  {name:15} → Return: {result['return']:7.2f}%, Sharpe: {result['sharpe']:.2f}, WinRate: {result['win_rate']}%")
            except Exception as e:
                print(f"  {name:15} → ERROR: {e}")

    # Crear DataFrame y ordenar
    df = pd.DataFrame(results)

    print("\n" + "="*80)
    print("RANKING GLOBAL (ordenado por Sharpe)")
    print("="*80)
    df_sorted = df.sort_values('sharpe', ascending=False)
    print(df_sorted.to_string(index=False))

    # Mejores combinaciones
    print("\n" + "="*80)
    print("TOP 5 MEJORES COMBINACIONES")
    print("="*80)
    top5 = df_sorted.head(5)
    for _, row in top5.iterrows():
        score = row['sharpe'] + (row['win_rate']/100) - abs(row['max_dd']/100)
        print(f"  {row['symbol']:10} + {row['strategy']:15} → Score: {score:.2f}")

    # Guardar
    df_sorted.to_csv("/home/l0ve/fundex/backtests/strategy_comparison.csv", index=False)
    print("\n\nResultados guardados en backtests/strategy_comparison.csv")

    return df_sorted


if __name__ == "__main__":
    run_comparison()
