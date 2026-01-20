from typing import List, Dict, Optional
import pandas as pd
from data.universe_provider import get_base_universe
from data.market_data import get_snapshot, get_history
from screener.eligibility import filter_eligible, EligibilityConfig
from screener.factors import compute_factor_frame
from screener.ranker import get_ranking_result, RankingResult

def run_screener(
    market: str = "US",
    k: int = 50,
    config: Optional[EligibilityConfig] = None,
    weights: Optional[Dict[str, float]] = None,
    db = None
) -> RankingResult:
    """
    Runs the full screening and ranking pipeline and persists results.
    """
    if config is None:
        config = EligibilityConfig()
    
    if weights is None:
        # Default weights: A=0.4, B=0.3, C=0.3
        # Since A (fundamentals) is currently empty, we re-normalize B and C
        weights = {
            "momentum_12_1": 0.25,
            "momentum_6m": 0.25,
            "volatility_20d": 0.25,
            "mom_vol_ratio": 0.25,
            "earnings_yield": 0.0,
            "fcf_yield": 0.0
        }

    # 1. Get Base Universe
    base_symbols = get_base_universe(market)
    
    # 2. Batch Data Fetch
    snapshot_df = get_snapshot(base_symbols)
    
    # 3. Eligibility Filter
    eligible_symbols = filter_eligible(base_symbols, snapshot_df, config)
    
    if not eligible_symbols:
        return RankingResult(
            base_count=len(base_symbols),
            eligible_count=0,
            ranked_count=0,
            top_k_symbols=[],
            scores_table={}
        )

    # 4. History Data for Factors
    history_df = get_history(eligible_symbols, lookback_days=300)
    
    # 5. Compute Factors
    factor_df = compute_factor_frame(eligible_symbols, snapshot_df.loc[eligible_symbols], history_df)
    
    # 6. Ranking + selection
    result = get_ranking_result(
        base_count=len(base_symbols),
        eligible_symbols=eligible_symbols,
        factor_df=factor_df,
        weights=weights,
        k=k
    )
    
    # 7. Persistence (Move 1: Ranking as a Contract)
    try:
        from database.connection import SessionLocal
        from database.models import ScreenerRun
        
        session = db or SessionLocal()
        run_record = ScreenerRun(
            market=market,
            k=k,
            base_count=result.base_count,
            eligible_count=result.eligible_count,
            selected_symbols=result.top_k_symbols,
            ranking_data=result.model_dump(),
            config=config.model_dump(),
            weights=weights
        )
        session.add(run_record)
        session.commit()
        if not db: session.close()
    except Exception as e:
        print(f"Warning: Failed to persist screener run: {e}")
    
    return result
