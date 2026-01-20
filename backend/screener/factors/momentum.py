import pandas as pd

def compute_momentum_12_1(history_df: pd.DataFrame) -> pd.Series:
    """12-1 momentum (12m return excluding last month)."""
    # Assuming daily frequency
    if len(history_df) < 252:
        return pd.Series(0.0, index=history_df.columns)
    
    # Approx trading days
    return (history_df.iloc[-21] / history_df.iloc[-252]) - 1

def compute_momentum_6m(history_df: pd.DataFrame) -> pd.Series:
    """6m momentum."""
    if len(history_df) < 126:
        return pd.Series(0.0, index=history_df.columns)
    
    return (history_df.iloc[-1] / history_df.iloc[-126]) - 1
