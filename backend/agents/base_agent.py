from agents.base_alpha import AlphaModel
from lean_bridge.contracts import Insight, InsightDirection
from lean_bridge.context import AlgorithmContext
from typing import List, Optional
from datetime import timedelta
import json

class PersonaAlphaModel(AlphaModel):
    def __init__(self, agent_id: str):
        self._agent_id = agent_id

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def name(self) -> str:
        return self._agent_id

    def generate_insight(self, symbol: str, signal: str, confidence: float, magnitude: Optional[float] = None, tag: Optional[str] = None) -> Insight:
        direction = InsightDirection.FLAT
        if signal.lower() == "bullish":
            direction = InsightDirection.UP
        elif signal.lower() == "bearish":
            direction = InsightDirection.DOWN
        
        # In LEAN MVO, magnitude is required. 
        # If not provided, we derive it from confidence/signal as a placeholder
        if magnitude is None:
            magnitude = 0.05 if direction == InsightDirection.UP else -0.05 if direction == InsightDirection.DOWN else 0.0

        return Insight.price(
            symbol=symbol,
            period=timedelta(days=1),
            direction=direction,
            magnitude=magnitude,
            confidence=confidence / 100.0 if confidence > 1 else confidence,
            source_model=self._agent_id,
            tag=tag
        )