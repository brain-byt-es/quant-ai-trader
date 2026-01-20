from __future__ import annotations
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from lean_bridge.contracts import Insight

class AlgorithmContext(BaseModel):
    """
    LEAN-faithful AlgorithmContext.
    Acts as a state provider for the Algorithm Framework pipeline.
    Provides access to current time, active universe, portfolio state, and configuration.
    """
    time: datetime
    universe: List[str]
    portfolio_state: Dict[str, Any]
    config: Dict[str, Any]
    insights: List[Insight] = Field(default_factory=list)

    @property
    def active_insights(self) -> List[Insight]:
        """Returns all currently valid, non-expired insights."""
        return [
            i for i in self.insights
            if not i.is_expired(self.time)
        ]

    def add_insights(self, insights: List[Insight]):
        """Adds new insights to the context."""
        self.insights.extend(insights)

    def clear_expired_insights(self, utc_time: datetime):
        """Removes all insights that have passed their expiry window."""
        self.insights = [
            i for i in self.insights
            if not i.is_expired(utc_time)
        ]

    def get_history(self, symbols: List[str], lookback: int):
        """
        Placeholder for historical data access. 
        In real LEAN, this would query the data provider.
        """
        from data.market_data import get_history
        return get_history(symbols, lookback)
