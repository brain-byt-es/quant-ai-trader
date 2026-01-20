import pandas as pd
import numpy as np

def compute_earnings_yield(snapshot_df: pd.DataFrame) -> pd.Series:
    """Earnings yield proxy (placeholder)."""
    # In a real app, we'd use EBIT/EV
    return pd.Series(0.0, index=snapshot_df.index)

def compute_fcf_yield(snapshot_df: pd.DataFrame) -> pd.Series:
    """FCF yield proxy (placeholder)."""
    return pd.Series(0.0, index=snapshot_df.index)
