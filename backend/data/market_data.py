import pandas as pd
import numpy as np
from typing import List, Dict
from tools.api import market_data_client

def get_snapshot(symbols: List[str]) -> pd.DataFrame:
    """
    Returns a snapshot of current data for a list of symbols.
    Columns: price, avg_dollar_volume, market_cap
    """
    # In a real implementation, we'd batch fetch from Alpaca/Alpha Vantage
    # For now, we simulate/mock deterministic data for the screener
    data = []
    for i, symbol in enumerate(symbols):
        # Deterministic dummy data based on symbol name
        seed = sum(ord(c) for c in symbol)
        np.random.seed(seed)
        
        price = 10 + np.random.random() * 500
        adv = 1e6 + np.random.random() * 50e6
        mcap = 100e6 + np.random.random() * 2e12
        
        data.append({
            "symbol": symbol,
            "price": price,
            "avg_dollar_volume": adv,
            "market_cap": mcap,
            "is_etf": False
        })
    
    return pd.DataFrame(data).set_index("symbol")

def get_history(symbols: List[str], lookback_days: int) -> pd.DataFrame:
    """
    Returns historical close prices for symbols.
    Wide format: index = date, columns = symbols
    """
    # Simulate historical data
    dates = pd.date_range(end=pd.Timestamp.now(), periods=lookback_days + 30, freq="D")
    
    # Build columns into a dictionary first to avoid fragmentation (fixes PerformanceWarnings)
    history_data = {}
    for symbol in symbols:
        seed = sum(ord(c) for c in symbol)
        np.random.seed(seed)
        
        # Random walk starting at a deterministic price
        start_price = 10 + np.random.random() * 500
        returns = np.random.normal(0.0005, 0.02, len(dates))
        prices = start_price * np.exp(np.cumsum(returns))
        history_data[symbol] = prices
        
    return pd.DataFrame(history_data, index=dates)
