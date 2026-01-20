from __future__ import annotations
from enum import Enum
from typing import Optional, List, Dict, TYPE_CHECKING
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime, timedelta
import math
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from lean_bridge.context import AlgorithmContext

class InsightDirection(int, Enum):
    FLAT = 0
    UP = 1
    DOWN = -1

class InsightType(str, Enum):
    PRICE = "price"
    VOLATILITY = "volatility"

class Insight(BaseModel):
    """
    LEAN-faithful Insight object.
    Immutable (Frozen) to ensure contract integrity.
    """
    model_config = ConfigDict(frozen=True)

    symbol: str
    generated_time_utc: datetime = Field(default_factory=datetime.utcnow)
    period: timedelta
    type: InsightType = InsightType.PRICE
    direction: InsightDirection
    magnitude: float  # Required for MVO
    confidence: float = Field(default=0.0, ge=0.0, le=1.0) # Strict range 0..1
    weight: Optional[float] = None
    source_model: str
    tag: Optional[str] = None

    @field_validator('magnitude')
    @classmethod
    def check_finite_magnitude(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("Magnitude must be a finite number (not NaN or Inf)")
        return v

    @field_validator('period')
    @classmethod
    def check_positive_period(cls, v: timedelta) -> timedelta:
        if v.total_seconds() <= 0:
            raise ValueError("Period must be greater than zero")
        return v

    @classmethod
    def price(cls, symbol: str, period: timedelta, direction: InsightDirection, 
              magnitude: float, confidence: float = 0.0, 
              source_model: str = "", tag: Optional[str] = None):
        return cls(
            symbol=symbol,
            period=period,
            direction=direction,
            magnitude=magnitude,
            confidence=confidence,
            source_model=source_model,
            tag=tag
        )

    def is_expired(self, utc_time: datetime) -> bool:
        return self.generated_time_utc + self.period <= utc_time

class PortfolioTarget(BaseModel):
    """
    LEAN-faithful PortfolioTarget.
    Immutable (Frozen) to ensure target consistency.
    """
    model_config = ConfigDict(frozen=True)

    symbol: str
    quantity: float
    tag: Optional[str] = None

class AlphaModel(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def update(self, context: AlgorithmContext, data: dict) -> List[Insight]:
        pass

class PortfolioConstructionModel(ABC):
    @abstractmethod
    def create_targets(self, insights: List[Insight], context: AlgorithmContext) -> List[PortfolioTarget]:
        pass

class RiskManagementModel(ABC):
    @abstractmethod
    def adjust_targets(self, targets: List[PortfolioTarget], context: AlgorithmContext) -> List[PortfolioTarget]:
        pass
