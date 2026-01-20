from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class AgentDebate(BaseModel):
    persona_id: str
    sentiment_score: float = Field(default=0.0, description="Score between -1 (Bearish) and 1 (Bullish)")
    style_rationale: str = Field(default="", description="Reasoning based on the agent's specific style/persona")
    confidence: float = Field(default=0.0, description="Confidence level 0-1")
    signal: str = Field(default="neutral", description="bullish, bearish, or neutral")

    @model_validator(mode="before")
    @classmethod
    def map_synonyms(cls, data: dict) -> dict:
        """
        Institutional Guardrail: Map common LLM synonym keys to our strict schema.
        Handles cases where agents return 'verdict' instead of 'signal'.
        """
        if not isinstance(data, dict):
            return data
            
        # 1. Map 'verdict' or 'decision' to 'signal'
        if "signal" not in data:
            for key in ["verdict", "decision", "rating", "Decision"]:
                if key in data:
                    data["signal"] = str(data[key]).lower()
                    break
        
        # 2. Map 'reason' or 'rationale' to 'style_rationale'
        if "style_rationale" not in data:
            for key in ["reason", "rationale", "Rationale", "conclusion", "comment", "Summary"]:
                if key in data:
                    data["style_rationale"] = str(data[key])
                    break
                    
        # 3. Handle 'confidence' synonyms
        if "confidence" not in data:
            for key in ["Confidence", "score"]:
                if key in data and isinstance(data[key], (int, float)):
                    data["confidence"] = float(data[key])
                    break
                    
        # 4. Default persona_id if missing (should be handled by call_llm but defensive)
        if "persona_id" not in data:
            data["persona_id"] = "unknown"
            
        return data


class PortfolioDecision(BaseModel):
    action: str
    quantity: int
    confidence: float
    reasoning: str
    persona_contributions: List[AgentDebate] = []
    
    @model_validator(mode="before")
    @classmethod
    def map_decision_synonyms(cls, data: dict) -> dict:
        if not isinstance(data, dict):
            return data
            
        if "action" not in data:
            for key in ["consensus_signal", "decision", "verdict"]:
                if key in data:
                    data["action"] = str(data[key])
                    break
                    
        if "reasoning" not in data:
            for key in ["rationale", "reason"]:
                if key in data:
                    data["reasoning"] = str(data[key])
                    break
                    
        if "quantity" not in data:
            data["quantity"] = 0
            
        return data