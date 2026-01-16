import yfinance as yf
import pandas as pd
import os

def get_crypto_data(symbol="BTC-USD", start_date="2020-01-01", data_dir="data"):
    """
    Downloads crypto data from Yahoo Finance and caches it locally.
    """
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    file_path = os.path.join(data_dir, f"{symbol}_{start_date}.csv")
    
    if os.path.exists(file_path):
        # Load from cache
        try:
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            print(f"Loaded {symbol} data from cache.")
            return df
        except Exception as e:
            print(f"Error loading cache: {e}, downloading new data...")
            
    # Download fresh data
    print(f"Downloading {symbol} data...")
    df = yf.download(symbol, start=start_date, progress=False)
    
    # Handle yfinance MultiIndex if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
    
    # Save to cache
    df.to_csv(file_path)
    return df
