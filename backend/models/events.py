from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


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

    type: Literal["start"] = "start"
    timestamp: Optional[str] = None


class ProgressUpdateEvent(BaseEvent):
    """Event containing an agent's progress update"""

    type: Literal["progress"] = "progress"
    agent: str
    ticker: Optional[str] = None
    content: str
    timestamp: Optional[str] = None
    analysis: Optional[str] = None


class ErrorEvent(BaseEvent):
    """Event indicating an error occurred"""

    type: Literal["error"] = "error"
    content: str
    timestamp: Optional[str] = None


class UniverseEvent(BaseEvent):
    """Event containing universe selection metrics"""

    type: Literal["universe"] = "universe"
    base_count: int
    eligible_count: int
    selected_symbols: List[str]
    timestamp: Optional[str] = None


class RankingEvent(BaseEvent):
    """Event containing top K ranking results"""

    type: Literal["ranking"] = "ranking"
    top_k: List[Dict[str, Any]]  # List of {symbol, score, factors...}
    timestamp: Optional[str] = None


class CompleteEvent(BaseEvent):
    """Event indicating successful completion with results"""

    type: Literal["complete"] = "complete"
    data: Dict[str, Any]
    timestamp: Optional[str] = None
