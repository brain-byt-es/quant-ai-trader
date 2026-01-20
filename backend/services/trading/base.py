from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"
    REJECTED = "rejected"


class Position(BaseModel):
    ticker: str
    qty: float
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_plpc: float


class Order(BaseModel):
    id: str
    client_order_id: Optional[str]
    ticker: str
    qty: float
    side: OrderSide
    type: OrderType
    status: OrderStatus
    filled_avg_price: Optional[float]
    created_at: str


class TradingProvider(ABC):
    @abstractmethod
    def get_account(self) -> Dict[str, Any]:
        """Get account details (cash, buying power, etc.)"""
        pass

    @abstractmethod
    def get_positions(self) -> List[Position]:
        """Get current positions."""
        pass

    @abstractmethod
    def submit_order(self, ticker: str, qty: float, side: OrderSide, type: OrderType, limit_price: Optional[float] = None) -> Order:
        """Submit an order."""
        pass

    @abstractmethod
    def get_order(self, order_id: str) -> Order:
        """Get order status."""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str):
        """Cancel an order."""
        pass
