import pandas as pd
from typing import List, Dict, Any, cast
from pydantic import BaseModel

class RankingResult(BaseModel):
    base_count: int
    eligible_count: int
    ranked_count: int
    top_k_symbols: List[str]
    scores_table: Dict[str, Dict[str, float]] # symbol -> {factor: score}

def winsorize(s: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    """Winsorize extreme values."""
    quantiles = s.quantile([lower, upper])
    return s.clip(lower=float(quantiles.iloc[0]), upper=float(quantiles.iloc[1]))

def zscore(s: pd.Series) -> pd.Series:
    """Compute z-score."""
    std = float(s.std())
    if std == 0:
        return pd.Series(0.0, index=s.index)
    return (s - float(s.mean())) / std

def rank_cross_section(df: pd.DataFrame) -> pd.DataFrame:
    """
    Winsorize and z-score all factors.
    """
    ranked_df = pd.DataFrame(index=df.index)
    for col in df.columns:
        s = df[col].dropna()
        if s.empty:
            ranked_df[col] = 0.0
            continue
        s_winsorized = winsorize(s)
        ranked_df[col] = zscore(s_winsorized)
    
    return ranked_df.fillna(0.0)

def compute_composite_score(df_ranked: pd.DataFrame, weights: Dict[str, float]) -> pd.Series:
    """
    Computes a weighted sum of ranked factors.
    """
    composite = pd.Series(0.0, index=df_ranked.index)
    
    # Directionality: For now assume all factors are "higher is better" 
    # except volatility where "lower is better" (we'll flip sign if needed)
    
    for factor, weight in weights.items():
        if factor in df_ranked.columns:
            val = df_ranked[factor]
            if factor == "volatility_20d": # Higher vol is worse
                val = -val
            composite += val * weight
            
    return composite

def get_ranking_result(
    base_count: int,
    eligible_symbols: List[str],
    factor_df: pd.DataFrame,
    weights: Dict[str, float],
    k: int
) -> RankingResult:
    """
    Orchestrates the ranking process and returns a RankingResult.
    """
    # 1. Rank cross-section
    df_ranked = rank_cross_section(factor_df)
    
    # 2. Compute composite score
    composite_scores = compute_composite_score(df_ranked, weights)
    df_ranked["composite_score"] = composite_scores
    
    # 3. Select Top K
    # top_k should be List[str]
    top_k = [str(s) for s in composite_scores.sort_values(ascending=False).head(k).index.tolist()]
    
    # 4. Prepare scores table for Top K
    # Explicitly convert to Dict[str, Dict[str, float]] to satisfy Pylance
    top_k_df = df_ranked.loc[top_k]
    
    # We must be very explicit to satisfy the linter's invariant dict requirement
    final_scores_table: Dict[str, Dict[str, float]] = {}
    
    # Iterate through the DataFrame rows to build the nested dictionary manually
    for symbol_idx, row in top_k_df.iterrows():
        symbol_str = str(symbol_idx)
        factor_scores: Dict[str, float] = {}
        for factor_name, score_val in row.items():
            factor_scores[str(factor_name)] = float(score_val)
        final_scores_table[symbol_str] = factor_scores
    
    return RankingResult(
        base_count=base_count,
        eligible_count=len(eligible_symbols),
        ranked_count=len(factor_df),
        top_k_symbols=top_k,
        scores_table=final_scores_table
    )
