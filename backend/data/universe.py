from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from screener.engine import run_screener, RankingResult
from screener.eligibility import EligibilityConfig

class UniverseSelectionResult(BaseModel):
    base_count: int
    eligible_count: int
    selected_symbols: List[str]
    ranking: Optional[RankingResult] = None

class UniverseSelectionModel:
    """
    LEAN-faithful Universe Selection Model.
    Determines which symbols exist in the dynamic universe.
    Supports market-wide screening.
    """
    def __init__(self, initial_symbols: List[str] = []):
        self._initial_symbols = initial_symbols

    def select(
        self, 
        dt: datetime, 
        market: str = "US", 
        k: int = 50, 
        config: Optional[EligibilityConfig] = None
    ) -> UniverseSelectionResult:
        """
        Runs the screener to select the top K symbols from the base universe.
        """
        ranking_result = run_screener(market=market, k=k, config=config)
        
        return UniverseSelectionResult(
            base_count=ranking_result.base_count,
            eligible_count=ranking_result.eligible_count,
            selected_symbols=ranking_result.top_k_symbols,
            ranking=ranking_result
        )

    def select_symbols(self, dt: datetime, data: dict) -> List[str]:
        """
        Returns the list of active symbols for the current time step.
        Supports dynamic expansion from data inputs or market-wide screening.
        """
        # 1. Check if market-wide screening is requested
        if "market" in data and "k" in data:
            market = data["market"]
            k = int(data["k"])
            config_data = data.get("screener_config", {})
            config = EligibilityConfig(**config_data) if config_data else None
            
            result = self.select(dt, market, k, config)
            # Store full result in data for downstream access/SSE
            data["universe_selection_result"] = result.model_dump()
            return result.selected_symbols

        # 2. Fallback to static watchlist + manual tickers
        symbols = list(self._initial_symbols)
        if "tickers" in data:
            for ticker in data["tickers"]:
                if ticker not in symbols:
                    symbols.append(ticker)
        
        return symbols
