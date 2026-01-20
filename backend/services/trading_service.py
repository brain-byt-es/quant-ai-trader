import os
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Load environment variables from root .env
load_dotenv("../.env")

from database.models import Trade
from services.trading.alpaca import AlpacaLiveProvider, AlpacaPaperProvider
from services.trading.base import OrderSide, OrderStatus, OrderType, TradingProvider


class TradingService:
    def __init__(self, db: Session):
        self.db = db
        self.mode = os.environ.get("TRADING_MODE", "paper").lower()
        self.provider = self._get_provider()

    def _get_provider(self) -> Optional[TradingProvider]:
        # Strictly use your environment keys
        api_key = os.environ.get("ALPACA_API_KEY")
        api_secret = os.environ.get("ALPACA_SECRET_KEY")

        if not api_key or not api_secret:
            print("Warning: Alpaca credentials (ALPACA_API_KEY/ALPACA_SECRET_KEY) not found. Trading service disabled.")
            return None

        if self.mode == "live":
            return AlpacaLiveProvider(api_key, api_secret)
        else:
            return AlpacaPaperProvider(api_key, api_secret)

    def get_account_summary(self) -> Dict:
        if not self.provider:
            return {"error": "Trading provider not configured"}
        return self.provider.get_account()

    def get_portfolio_positions(self) -> List[Dict]:
        if not self.provider:
            return []
        positions = self.provider.get_positions()
        return [p.model_dump() for p in positions]

    def create_trade_request(self, ticker: str, action: str, quantity: int, rationale: Dict, flow_run_id: Optional[int] = None, risk_score: Optional[float] = None, limit_price: Optional[float] = None) -> Trade:
        """
        Creates a trade request in the database.
        """
        trade = Trade(ticker=ticker, action=action.upper(), quantity=quantity, order_type="limit" if limit_price else "market", limit_price=str(limit_price) if limit_price else None, persona_rationale=rationale, risk_score=str(risk_score) if risk_score is not None else None, flow_run_id=flow_run_id, status="PENDING_APPROVAL")
        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)

        if self.mode == "paper":
            self.execute_trade(trade.id)

        return trade

    def execute_trade(self, trade_id: int, approver: str = "SYSTEM") -> Trade:
        trade = self.db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            raise ValueError("Trade not found")

        if trade.status in ["EXECUTED", "REJECTED", "FAILED"]:
            return trade

        if self.mode == "live" and not trade.manual_approval_timestamp:
            trade.manual_approval_timestamp = datetime.now()
            trade.approved_by = approver

        if not self.provider:
            trade.status = "FAILED"
            trade.error_message = "No trading provider configured"
            self.db.commit()
            return trade

        try:
            side = OrderSide.BUY if trade.action == "BUY" else OrderSide.SELL
            type = OrderType.LIMIT if trade.order_type == "limit" else OrderType.MARKET
            limit_price = float(trade.limit_price) if trade.limit_price else None

            order = self.provider.submit_order(ticker=trade.ticker, qty=trade.quantity, side=side, type=type, limit_price=limit_price)

            trade.status = "SUBMITTED"
            trade.brokerage_order_id = order.id
            trade.execution_time = datetime.now()

            if order.status == OrderStatus.FILLED:
                trade.status = "EXECUTED"
                trade.execution_price = str(order.filled_avg_price)

        except Exception as e:
            trade.status = "FAILED"
            trade.error_message = str(e)

        self.db.commit()
        self.db.refresh(trade)
        return trade

    def reject_trade(self, trade_id: int, user: str):
        trade = self.db.query(Trade).filter(Trade.id == trade_id).first()
        if trade and trade.status == "PENDING_APPROVAL":
            trade.status = "REJECTED"
            trade.approved_by = user
            self.db.commit()