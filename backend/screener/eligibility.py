from typing import List, Optional
import pandas as pd
from pydantic import BaseModel

class EligibilityConfig(BaseModel):
    min_price: float = 5.0
    min_adv: float = 5e6
    min_mcap: Optional[float] = None
    exclude_etfs: bool = False

def filter_eligible(symbols: List[str], snapshot_df: pd.DataFrame, config: EligibilityConfig) -> List[str]:
    """
    Filters symbols based on tradability and liquidity criteria.
    """
    df = snapshot_df.copy()
    
    # Apply filters
    mask = df["price"] >= config.min_price
    mask &= df["avg_dollar_volume"] >= config.min_adv
    
    if config.min_mcap:
        mask &= df["market_cap"] >= config.min_mcap
        
    if config.exclude_etfs and "is_etf" in df.columns:
        mask &= ~df["is_etf"]
        
    eligible_df = df[mask]
    return eligible_df.index.tolist()
