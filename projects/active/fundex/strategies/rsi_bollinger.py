"""
RSI + Bollinger Bands Strategy
Compra: RSI < 30 + precio toca banda inferior
Vende: RSI > 70 + precio toca banda superior
"""
import pandas as pd
import numpy as np
import yfinance as yf
from backtesting import Backtest, Strategy
import warnings
warnings.filterwarnings('ignore')


def calculate_rsi(close, period=14):
    delta = pd.Series(close).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_bollinger(close, period=20, std_dev=2):
    sma = pd.Series(close).rolling(window=period).mean()
    std = pd.Series(close).rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return sma, upper, lower


class RSIBollinger(Strategy):
    rsi_period = 14
    bb_period = 20
    bb_std = 2
    rsi_oversold = 30
    rsi_overbought = 70

    def init(self):
        close = self.data.Close
        self.rsi = self.I(calculate_rsi, close, self.rsi_period)
        self.bb_mid, self.bb_upper, self.bb_lower = [
            self.I(lambda x, i=i: calculate_bollinger(x, self.bb_period, self.bb_std)[i], close)
            for i in range(3)
        ]

    def next(self):
        price = self.data.Close[-1]
        rsi = self.rsi[-1]

        if pd.isna(rsi) or pd.isna(self.bb_lower[-1]):
            return

        size = max(1, int(self.equity * 0.95 / price))

        # Señal de compra: RSI oversold + precio cerca de banda inferior
        if rsi < self.rsi_oversold and price <= self.bb_lower[-1] * 1.01:
            if not self.position:
                self.buy(size=size)

        # Señal de venta: RSI overbought + precio cerca de banda superior
        elif rsi > self.rsi_overbought and price >= self.bb_upper[-1] * 0.99:
            if self.position:
                self.position.close()

        # Stop loss: precio cruza muy por debajo de BB lower
        elif self.position and price < self.bb_lower[-1] * 0.95:
            self.position.close()


def get_data(symbol="ETH-USD", period="1y"):
    df = yf.download(symbol, period=period, progress=False)
    if hasattr(df.columns, 'levels'):
        df.columns = df.columns.get_level_values(0)
    return df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()


def run_backtest(symbol="ETH-USD"):
    print(f"\n{'='*50}")
    print(f"RSI + BOLLINGER - {symbol}")
    print('='*50)

    data = get_data(symbol)
    print(f"Datos: {len(data)} filas")

    cash = max(100000, data['Close'].iloc[-1] * 100)
    bt = Backtest(data, RSIBollinger, cash=cash, commission=0.001)
    stats = bt.run()

    print(f"\nRetorno:      {stats['Return [%]']:.2f}%")
    print(f"Buy & Hold:   {stats['Buy & Hold Return [%]']:.2f}%")
    print(f"Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate:     {stats['Win Rate [%]']:.2f}%" if pd.notna(stats['Win Rate [%]']) else "Win Rate: N/A")
    print(f"Trades:       {stats['# Trades']}")
    print(f"Sharpe:       {stats['Sharpe Ratio']:.2f}" if pd.notna(stats['Sharpe Ratio']) else "Sharpe: N/A")

    return stats


if __name__ == "__main__":
    # Probar en los mejores pares
    results = []
    for symbol in ["ETH-USD", "BNB-USD", "SOL-USD"]:
        stats = run_backtest(symbol)
        results.append({
            'symbol': symbol,
            'strategy': 'RSI+BB',
            'return': round(stats['Return [%]'], 2),
            'max_dd': round(stats['Max. Drawdown [%]'], 2),
            'sharpe': round(stats['Sharpe Ratio'], 2) if pd.notna(stats['Sharpe Ratio']) else 0,
            'trades': stats['# Trades'],
            'win_rate': round(stats['Win Rate [%]'], 2) if pd.notna(stats['Win Rate [%]']) else 0
        })

    # Guardar
    df = pd.DataFrame(results)
    df.to_csv("/home/l0ve/fundex/backtests/rsi_bollinger_results.csv", index=False)
    print("\n\nResultados guardados.")
