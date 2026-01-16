"""
SMA Crossover Strategy - Fundex
Estrategia basica de cruce de medias moviles
"""
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import yfinance as yf

class SMACrossover(Strategy):
    """
    Compra cuando SMA rapida cruza por encima de SMA lenta
    Vende cuando SMA rapida cruza por debajo de SMA lenta
    """
    n1 = 10  # SMA rapida
    n2 = 30  # SMA lenta

    def init(self):
        close = self.data.Close
        self.sma1 = self.I(lambda x: pd.Series(x).rolling(self.n1).mean(), close)
        self.sma2 = self.I(lambda x: pd.Series(x).rolling(self.n2).mean(), close)

    def next(self):
        price = self.data.Close[-1]
        size = int(self.equity * 0.95 / price)  # 95% del capital

        if crossover(self.sma1, self.sma2):
            if not self.position:
                self.buy(size=size)
        elif crossover(self.sma2, self.sma1):
            if self.position:
                self.position.close()


def get_crypto_data(symbol="BTC-USD", period="1y"):
    """Descarga datos de crypto via yfinance"""
    df = yf.download(symbol, period=period, progress=False)
    df.columns = df.columns.get_level_values(0)  # Aplanar MultiIndex
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    return df


def run_backtest(data, strategy=SMACrossover, cash=10000, commission=0.001):
    """Ejecuta backtest y retorna resultados"""
    bt = Backtest(data, strategy, cash=cash, commission=commission)
    stats = bt.run()
    return bt, stats


if __name__ == "__main__":
    print("Descargando ETH-USD (1 año)...")
    data = get_crypto_data("ETH-USD", "1y")
    print(f"Datos: {len(data)} filas")

    print("\nEjecutando backtest SMA Crossover...")
    bt, stats = run_backtest(data, cash=100000)  # 100k para poder operar

    print("\n" + "="*50)
    print("RESULTADOS")
    print("="*50)
    print(f"Retorno:        {stats['Return [%]']:.2f}%")
    print(f"Buy & Hold:     {stats['Buy & Hold Return [%]']:.2f}%")
    print(f"Max Drawdown:   {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate:       {stats['Win Rate [%]']:.2f}%")
    print(f"# Trades:       {stats['# Trades']}")
    print(f"Sharpe Ratio:   {stats['Sharpe Ratio']:.2f}")
    print("="*50)

    # Guardar resultados
    stats_df = pd.DataFrame([stats])
    stats_df.to_csv("/home/l0ve/fundex/backtests/sma_crossover_results.csv", index=False)
    print("\nResultados guardados en backtests/sma_crossover_results.csv")
