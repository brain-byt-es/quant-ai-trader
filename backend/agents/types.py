from typing import List, Optional

from pydantic import BaseModel, Field


class AgentDebate(BaseModel):
    persona_id: str
    sentiment_score: float = Field(description="Score between -1 (Bearish) and 1 (Bullish)")
    style_rationale: str = Field(description="Reasoning based on the agent's specific style/persona")
    confidence: float = Field(description="Confidence level 0-1")
    signal: str = Field(description="bullish, bearish, or neutral")


class PortfolioDecision(BaseModel):
    action: str
    quantity: int
    confidence: float
    reasoning: str
    persona_contributions: List[AgentDebate] = []
