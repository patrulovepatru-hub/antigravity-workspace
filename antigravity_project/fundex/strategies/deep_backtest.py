"""
Backtest de Ultra-Largo Plazo (Desde 2016)
Estrategia: EMA Momentum Optimizada
Símbolo: BTC-USD, ETH-USD, SOL-USD
"""
import pandas as pd
import numpy as np
import yfinance as yf
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import warnings
import os
from datetime import datetime

warnings.filterwarnings('ignore')

def ema(close, period):
    return pd.Series(close).ewm(span=period, adjust=False).mean()

def rsi(close, period=14):
    delta = pd.Series(close).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

class Strategy2016(Strategy):
    fast = 9
    slow = 21
    rsi_period = 14
    rsi_upper = 70
    
    def init(self):
        self.ema_fast = self.I(ema, self.data.Close, self.fast)
        self.ema_slow = self.I(ema, self.data.Close, self.slow)
        self.rsi = self.I(rsi, self.data.Close, self.rsi_period)

    def next(self):
        if pd.isna(self.rsi[-1]):
            return
        
        price = self.data.Close[-1]
        
        # El tamao debe ser entero para evitar errores en algunas versiones
        size = int(self.equity * 0.9 / price)
        if size < 1: size = 1

        # Entrada: Cruce al alza + RSI no sobrecomprado
        if crossover(self.ema_fast, self.ema_slow) and self.rsi[-1] < self.rsi_upper:
            if not self.position:
                self.buy(size=size)
        
        # Salida: Cruce a la baja O RSI extremo
        elif (crossover(self.ema_slow, self.ema_fast) or self.rsi[-1] > 85) and self.position:
            self.position.close()

def run_deep_backtest(symbol, start_date="2016-01-01"):
    print(f"\n{'#'*60}")
    print(f" ANALIZANDO: {symbol} DESDE {start_date}")
    print(f"{'#'*60}")

    # Descargar datos
    data = yf.download(symbol, start=start_date, end=datetime.now().strftime("%Y-%m-%d"), progress=False)
    
    if data.empty:
        print(f"Error: No hay datos para {symbol}")
        return None

    # Limpiar columnas de yfinance (a veces vienen con multi-index)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    data = data[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
    
    # Backtest
    bt = Backtest(data, Strategy2016, cash=100000, commission=.002, trade_on_close=True)
    stats = bt.run()
    
    print(f"\n--- RESULTADOS CLAVE ---")
    print(f"Retorno Final:    {stats['Return [%]']:.2f}%")
    print(f"Buy & Hold:       {stats['Buy & Hold Return [%]']:.2f}%")
    print(f"Max Drawdown:     {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Sharpe Ratio:     {stats['Sharpe Ratio']:.2f}")
    print(f"Total Trades:     {stats['# Trades']}")
    print(f"Win Rate:         {stats['Win Rate [%]']:.2f}%")
    
    return stats, data

if __name__ == "__main__":
    # Creamos carpeta de resultados si no existe
    save_path = r"c:\Users\patri\Documents\wateber\antigravity_project\fundex\backtests"
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    symbols = ["BTC-USD", "ETH-USD"] # SOL no exista en 2016
    all_results = []

    for sym in symbols:
        res = run_deep_backtest(sym)
        if res:
            stats, _ = res
            all_results.append({
                "Symbol": sym,
                "Return": stats['Return [%]'],
                "MaxDD": stats['Max. Drawdown [%]'],
                "Sharpe": stats['Sharpe Ratio'],
                "Trades": stats['# Trades']
            })

    # Guardar resumen
    summary_df = pd.DataFrame(all_results)
    summary_df.to_csv(os.path.join(save_path, "deep_backtest_since_2016.csv"), index=False)
    print(f"\n✅ Resumen guardado en {save_path}")
