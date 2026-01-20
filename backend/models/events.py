from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """Base class for all Server-Sent Event events"""

    type: str
    schema_version: str = "1.0"

    def to_sse(self) -> str:
        """Convert to Server-Sent Event format"""
        event_type = self.type.lower()
        return f"event: {event_type}\ndata: {self.model_dump_json()}\n\n"


class StartEvent(BaseEvent):
    """Event indicating the start of processing"""

    type: str = Field(default="start")
    timestamp: Optional[str] = None


class ProgressUpdateEvent(BaseEvent):
    """Event containing an agent's progress update"""

    type: str = Field(default="progress")
    agent: str
    ticker: Optional[str] = None
    content: str
    timestamp: Optional[str] = None
    analysis: Optional[str] = None


class ErrorEvent(BaseEvent):
    """Event indicating an error occurred"""

    type: str = Field(default="error")
    content: str
    timestamp: Optional[str] = None


class UniverseEvent(BaseEvent):
    """Event containing universe selection metrics"""

    type: str = Field(default="universe")
    base_count: int
    eligible_count: int
    selected_symbols: List[str]
    timestamp: Optional[str] = None


class RankingEvent(BaseEvent):
    """Event containing top K ranking results"""

    type: str = Field(default="ranking")
    top_k: List[Dict[str, Any]]  # List of {symbol, score, factors...}
    timestamp: Optional[str] = None


class CompleteEvent(BaseEvent):
    """Event indicating successful completion with results"""

    type: str = Field(default="complete")
    data: Dict[str, Any]
    timestamp: Optional[str] = None