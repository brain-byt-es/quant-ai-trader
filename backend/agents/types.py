from typing import List, Optional, Any, Dict

from pydantic import BaseModel, Field, model_validator


class AgentDebate(BaseModel):
    persona_id: str
    sentiment_score: float = Field(default=0.0, description="Score between -1 (Bearish) and 1 (Bullish)")
    style_rationale: str = Field(default="", description="Reasoning based on the agent's specific style/persona")
    confidence: float = Field(default=0.0, description="Confidence level 0-1")
    signal: str = Field(default="neutral", description="bullish, bearish, or neutral")

    @model_validator(mode="before")
    @classmethod
    def map_synonyms(cls, data: Any) -> Any:
        """
        Institutional Guardrail: Map common LLM synonym keys to our strict schema.
        Handles cases where agents return 'verdict' instead of 'signal'.
        """
        if not isinstance(data, dict):
            return data
            
        # 1. Look for common root keys if nested (LLMs sometimes wrap in a ticker key)
        # If the dict has exactly one key and it matches a ticker pattern (all caps, 1-5 chars), 
        # or if it has an 'analysis' or 'evaluation' key, flatten it.
        for wrapper in ["analysis", "evaluation", "valuation", "checklist"]:
            if wrapper in data and isinstance(data[wrapper], dict):
                # Merge the nested data into the top level
                for k, v in data[wrapper].items():
                    if k not in data:
                        data[k] = v
        
        # 2. Map 'verdict' or 'decision' to 'signal'
        if "signal" not in data:
            for key in ["verdict", "decision", "rating", "Decision", "consensus_signal"]:
                if key in data:
                    data["signal"] = str(data[key]).lower()
                    break
        
        # 3. Map 'reason' or 'rationale' to 'style_rationale'
        if "style_rationale" not in data:
            for key in ["reason", "rationale", "Rationale", "conclusion", "comment", "Summary", "style_rationale", "reasoning"]:
                if key in data:
                    data["style_rationale"] = str(data[key])
                    break
                    
        # 4. Handle 'confidence' synonyms
        if "confidence" not in data:
            for key in ["Confidence", "score"]:
                if key in data and isinstance(data[key], (int, float)):
                    data["confidence"] = float(data[key])
                    break
                    
        # 5. Default persona_id if missing
        if "persona_id" not in data:
            data["persona_id"] = "unknown"
            
        return data


class ConsensusSignal(BaseModel):
    """Signal produced by the Chief Investment Officer or Portfolio Manager."""
    action: str = Field(default="HOLD")
    quantity: int = Field(default=0)
    confidence: float = Field(default=0.0)
    reasoning: str = Field(default="")

    @model_validator(mode="before")
    @classmethod
    def map_consensus_synonyms(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
            
        if "action" not in data:
            for key in ["consensus_signal", "decision", "verdict", "action", "Action"]:
                if key in data:
                    data["action"] = str(data[key]).upper()
                    break
                    
        if "reasoning" not in data:
            for key in ["rationale", "reason", "reasoning", "Rationale", "conclusion"]:
                if key in data:
                    data["reasoning"] = str(data[key])
                    break
                    
        if "quantity" not in data:
            data["quantity"] = 0
            
        return data


class PortfolioDecision(BaseModel):
    action: str
    quantity: int
    confidence: float
    reasoning: str
    persona_contributions: List[AgentDebate] = []
    
    @model_validator(mode="before")
    @classmethod
    def map_decision_synonyms(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
            
        if "action" not in data:
            for key in ["consensus_signal", "decision", "verdict", "action"]:
                if key in data:
                    data["action"] = str(data[key]).upper()
                    break
                    
        if "reasoning" not in data:
            for key in ["rationale", "reason", "reasoning"]:
                if key in data:
                    data["reasoning"] = str(data[key])
                    break
                    
        if "quantity" not in data:
            data["quantity"] = 0
            
        return data
