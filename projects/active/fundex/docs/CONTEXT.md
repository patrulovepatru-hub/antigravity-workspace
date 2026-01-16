# Fundex - Trading Algoritmico

## Objetivo
Script de trading algoritmico con resultados backtested

## Frameworks evaluados
| Framework | Uso | Link |
|-----------|-----|------|
| Backtesting.py | Ligero, rapido | github.com/kernc/backtesting.py |
| Backtrader | Completo, 20K stars | github.com/mementum/backtrader |
| HFTBacktest | HFT, Binance/Bybit | github.com/nkaz001/hftbacktest |
| ML4Trading | ML + backtesting | github.com/stefan-jansen/machine-learning-for-trading |

## Datasets
- Kaggle: Algorithmic Trading Dataset
- QuantConnect: Crypto, forex, stocks (API)
- Binance API: Datos historicos crypto

## Stack propuesto
- Python 3.11+
- Backtesting.py (inicio rapido) o Backtrader (produccion)
- Pandas, NumPy, TA-Lib
- Jupyter notebooks para experimentacion

## Estructura
```
fundex/
├── strategies/    # Estrategias de trading
├── data/          # Datasets descargados
├── backtests/     # Resultados de backtests
└── docs/          # Documentacion
```

## Proximos pasos
1. Instalar dependencias
2. Descargar dataset de prueba (crypto)
3. Implementar estrategia basica (SMA crossover)
4. Ejecutar backtest
5. Analizar resultados
