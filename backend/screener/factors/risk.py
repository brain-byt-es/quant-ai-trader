import pandas as pd
import numpy as np

def compute_volatility_20d(history_df: pd.DataFrame) -> pd.Series:
    """20d volatility."""
    returns = history_df.pct_change().dropna()
    return returns.tail(20).std() * np.sqrt(252)

def compute_momentum_vol_ratio(momentum: pd.Series, volatility: pd.Series) -> pd.Series:
    """Simple signal / vol ratio."""
    return momentum / volatility
