import pandas as pd
from .momentum import compute_momentum_12_1, compute_momentum_6m
from .risk import compute_volatility_20d, compute_momentum_vol_ratio
from .fundamentals import compute_earnings_yield, compute_fcf_yield

def compute_factor_frame(symbols: list, snapshot_df: pd.DataFrame, history_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes all factors for the given symbols.
    """
    factors = {}
    
    # B: Momentum
    factors["momentum_12_1"] = compute_momentum_12_1(history_df)
    factors["momentum_6m"] = compute_momentum_6m(history_df)
    
    # C: Risk
    factors["volatility_20d"] = compute_volatility_20d(history_df)
    factors["mom_vol_ratio"] = compute_momentum_vol_ratio(factors["momentum_12_1"], factors["volatility_20d"])
    
    # A: Fundamentals (proxies)
    factors["earnings_yield"] = compute_earnings_yield(snapshot_df)
    factors["fcf_yield"] = compute_fcf_yield(snapshot_df)
    
    df = pd.DataFrame(factors)
    # Ensure all requested symbols are in index
    df = df.reindex(symbols)
    
    return df
