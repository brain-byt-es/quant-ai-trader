from __future__ import annotations
from typing import List, Dict, Tuple
from datetime import datetime
from lean_bridge.contracts import Insight

class InsightCollection:
    """
    Manages active insights, mimicking LEAN's InsightManager.
    Enforces deterministic replacement: One active insight per (symbol, source_model).
    """
    def __init__(self):
        # Store: { (symbol, source_model): Insight }
        self._active_insights: Dict[Tuple[str, str], Insight] = {}

    def add(self, insights: List[Insight]):
        """
        Adds new insights, overwriting older ones from the same model for the same symbol.
        Deterministic rule: Keep the most recent by generated_time_utc. 
        If timestamps are identical, last write wins (last in list).
        """
        for insight in insights:
            key = (insight.symbol, insight.source_model)
            if key not in self._active_insights:
                self._active_insights[key] = insight
            else:
                # Keep the most recent by timestamp
                if insight.generated_time_utc >= self._active_insights[key].generated_time_utc:
                    self._active_insights[key] = insight

    def remove_expired(self, utc_time: datetime):
        """Removes all insights that have passed their expiry window."""
        expired_keys = [
            key for key, insight in self._active_insights.items()
            if insight.is_expired(utc_time)
        ]
        for key in expired_keys:
            del self._active_insights[key]

    def clear(self, symbols: List[str]):
        """Force-removes all insights for symbols that have left the universe."""
        keys_to_remove = [
            key for key in self._active_insights.keys()
            if key[0] in symbols
        ]
        for key in keys_to_remove:
            del self._active_insights[key]

    def get_active_insights(self, utc_time: datetime) -> List[Insight]:
        """Returns all currently valid, non-expired insights."""
        return [
            i for i in self._active_insights.values()
            if not i.is_expired(utc_time)
        ]