"""
Pair Analyzer - Encuentra los mejores pares para el challenge
"""
import pandas as pd
import yfinance as yf
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import warnings
warnings.filterwarnings('ignore')

# Pares comunes en prop firms
FOREX_PAIRS = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X",
    "USDCAD=X", "NZDUSD=X", "USDCHF=X"
]

CRYPTO_PAIRS = [
    "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD"
]

INDICES = [
    "^GSPC", "^DJI", "^IXIC"  # S&P500, Dow, Nasdaq
]


class SMACrossover(Strategy):
    n1 = 10
    n2 = 30

    def init(self):
        close = self.data.Close
        self.sma1 = self.I(lambda x: pd.Series(x).rolling(self.n1).mean(), close)
        self.sma2 = self.I(lambda x: pd.Series(x).rolling(self.n2).mean(), close)

    def next(self):
        price = self.data.Close[-1]
        if price > 0:
            size = max(1, int(self.equity * 0.95 / price))
            if crossover(self.sma1, self.sma2):
                if not self.position:
                    self.buy(size=size)
            elif crossover(self.sma2, self.sma1):
                if self.position:
                    self.position.close()


def analyze_pair(symbol, period="1y"):
    """Analiza un par y retorna métricas"""
    try:
        df = yf.download(symbol, period=period, progress=False)
        if df.empty or len(df) < 50:
            return None

        # Aplanar MultiIndex si existe
        if hasattr(df.columns, 'levels'):
            df.columns = df.columns.get_level_values(0)

        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

        # Calcular volatilidad
        df['returns'] = df['Close'].pct_change()
        volatility = df['returns'].std() * (252 ** 0.5) * 100  # Anualizada

        # Backtest
        cash = max(100000, df['Close'].iloc[-1] * 100)
        bt = Backtest(df, SMACrossover, cash=cash, commission=0.001)
        stats = bt.run()

        return {
            'symbol': symbol,
            'return': round(stats['Return [%]'], 2),
            'buy_hold': round(stats['Buy & Hold Return [%]'], 2),
            'max_dd': round(stats['Max. Drawdown [%]'], 2),
            'sharpe': round(stats['Sharpe Ratio'], 2) if pd.notna(stats['Sharpe Ratio']) else 0,
            'trades': stats['# Trades'],
            'win_rate': round(stats['Win Rate [%]'], 2) if pd.notna(stats['Win Rate [%]']) else 0,
            'volatility': round(volatility, 2)
        }
    except Exception as e:
        return None


def main():
    print("="*70)
    print("ANÁLISIS DE PARES - FUNDEX CHALLENGE")
    print("="*70)

    all_pairs = CRYPTO_PAIRS + FOREX_PAIRS[:4]  # Limitamos forex
    results = []

    for symbol in all_pairs:
        print(f"Analizando {symbol}...", end=" ")
        result = analyze_pair(symbol)
        if result:
            results.append(result)
            print(f"OK - Return: {result['return']}%")
        else:
            print("SKIP")

    if not results:
        print("No se obtuvieron resultados")
        return

    # Ordenar por Sharpe ratio
    df = pd.DataFrame(results)
    df = df.sort_values('sharpe', ascending=False)

    print("\n" + "="*70)
    print("RANKING DE PARES (por Sharpe Ratio)")
    print("="*70)
    print(df.to_string(index=False))

    # Filtrar buenos candidatos
    good = df[(df['sharpe'] > 0.5) & (df['max_dd'] > -40)]

    if len(good) > 0:
        print("\n" + "="*70)
        print("MEJORES CANDIDATOS PARA CHALLENGE")
        print("="*70)
        print(good.to_string(index=False))

    # Guardar resultados
    df.to_csv("/home/l0ve/fundex/backtests/pair_analysis.csv", index=False)
    print("\nResultados guardados en backtests/pair_analysis.csv")


if __name__ == "__main__":
    main()
