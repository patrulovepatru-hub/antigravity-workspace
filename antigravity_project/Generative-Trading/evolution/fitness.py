from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import sys
import types

# Ensure necessary imports are available for the dynamic code
# The strategies will assume these are imported
SAFE_GLOBALS = {
    'Strategy': Strategy,
    'crossover': crossover,
    'pd': pd,
    'abs': abs,
    'min': min,
    'max': max,
    'int': int,
    'len': len
}

def evaluate_fitness(genome, data):
    """
    Compiles the genome code and runs a backtest.
    Returns: Sharpe Ratio (float).
    """
    code = genome.code
    
    # 1. Dynamic Compilation
    try:
        # Create a new module to hold the strategy execution
        module_name = f"strategy_{genome.id}"
        dynamic_module = types.ModuleType(module_name)
        
        # Execute code in the module's namespace
        # WARNING: exec() is dangerous if code comes from untrusted sources.
        # Here we assume the "Generative Model" is the source.
        exec(code, SAFE_GLOBALS, dynamic_module.__dict__)
        
        # Find the strategy class (must inherit from Strategy)
        strategy_class = None
        for name, obj in dynamic_module.__dict__.items():
            if isinstance(obj, type) and issubclass(obj, Strategy) and obj is not Strategy:
                strategy_class = obj
                break
        
        if not strategy_class:
            print(f"Genome {genome.id}: No valid Strategy class found.")
            genome.fitness = -999
            return -999

    except Exception as e:
        print(f"Genome {genome.id}: Compilation/Execution Error: {e}")
        genome.fitness = -999
        return -999

    # 2. Run Backtest
    try:
        bt = Backtest(data, strategy_class, cash=10000, commission=.002)
        stats = bt.run()
        
        # Store full stats in genome for analysis
        genome.stats = stats.to_dict()
        
        # Metric: Sharpe Ratio
        # Handle cases where Sharpe is NaN (e.g. flat line)
        sharpe = stats['Sharpe Ratio']
        if pd.isna(sharpe):
            sharpe = 0.0
            
        genome.fitness = sharpe
        return sharpe

    except Exception as e:
        print(f"Genome {genome.id}: Backtest Runtime Error: {e}")
        genome.fitness = -999
        return -999
