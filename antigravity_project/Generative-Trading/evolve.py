import numpy as np
# Patch for Numpy 2.0 compatibility with older Bokeh/Backtesting versions
if not hasattr(np, 'bool8'):
    np.bool8 = np.bool

import argparse
from utils import get_crypto_data
from evolution.engine import EvolutionEngine

# A simple seed strategy to start the evolution
SEED_STRATEGY = """
from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd

class CrossoverStrategy(Strategy):
    n1 = 10
    n2 = 20

    def init(self):
        close = self.data.Close
        self.sma1 = self.I(lambda x: pd.Series(x).rolling(self.n1).mean(), close)
        self.sma2 = self.I(lambda x: pd.Series(x).rolling(self.n2).mean(), close)

    def next(self):
        if crossover(self.sma1, self.sma2):
            self.buy()
        elif crossover(self.sma2, self.sma1):
            self.position.close()
"""

def main():
    parser = argparse.ArgumentParser(description="Evolve Trading Strategies")
    parser.add_argument("--symbol", default="BTC-USD", help="Crypto symbol to trade")
    parser.add_argument("--gens", type=int, default=5, help="Number of generations")
    parser.add_argument("--pop", type=int, default=10, help="Population size")
    
    args = parser.parse_args()
    
    print(f"Starting Evolution for {args.symbol}...")
    
    # 1. Get Data
    data = get_crypto_data(args.symbol, start_date="2020-01-01")
    if data.empty:
        print("No data found. Exiting.")
        return

    # 2. Initialize Engine
    engine = EvolutionEngine(data, population_size=args.pop)
    engine.initialize_population([SEED_STRATEGY])
    
    # 3. Evolution Loop
    best_genome = None
    for i in range(args.gens):
        best_genome = engine.run_generation()
        
    print("\n" + "="*50)
    print("EVOLUTION COMPLETE")
    print(f"Best Fitness (Sharpe): {best_genome.fitness:.4f}")
    print("="*50)
    print("\nBest Code:\n")
    print(best_genome.code)
    
    # Optionally save best code
    with open("best_strategy.py", "w") as f:
        f.write(best_genome.code)
        print("\nSaved to best_strategy.py")

if __name__ == "__main__":
    main()
