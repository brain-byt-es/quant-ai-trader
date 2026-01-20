import os
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from database.models import ProposedTrade
from services.trading.alpaca import AlpacaLiveProvider, AlpacaPaperProvider
from services.trading.base import OrderSide, OrderType


class BrokerageService:
    def __init__(self, db: Session):
        self.db = db
        self.mode = os.environ.get("TRADING_MODE", "paper").upper()  # DEMO/LIVE/PAPER
        self.provider = self._get_provider()

    def _get_provider(self):
        api_key = os.environ.get("ALPACA_API_KEY")
        api_secret = os.environ.get("ALPACA_SECRET_KEY")

        if not api_key or not api_secret:
            print("Warning: Alpaca credentials not found.")
            return None

        if self.mode == "LIVE":
            return AlpacaLiveProvider(api_key, api_secret)
        else:
            return AlpacaPaperProvider(api_key, api_secret)

    def propose_trade(self, ticker: str, action: str, quantity: int, persona_logic: Dict, flow_run_id: Optional[int] = None) -> ProposedTrade:
        """
        Creates a ProposedTrade with PENDING status and a unique approval token.
        Does NOT execute the trade yet.
        """
        token = str(uuid.uuid4())

        trade = ProposedTrade(ticker=ticker, action=action.upper(), quantity=quantity, persona_logic=persona_logic, status="PENDING", approval_token=token, flow_run_id=flow_run_id)
        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)

        return trade

    def execute_trade_by_token(self, token: str) -> Dict[str, Any]:
        """
        Executes the trade if the token is valid and status is PENDING.
        """
        trade = self.db.query(ProposedTrade).filter(ProposedTrade.approval_token == token).first()
        if not trade:
            return {"error": "Invalid token"}

        if trade.status != "PENDING":
            return {"error": f"Trade already {trade.status}"}

        if not self.provider:
            return {"error": "Brokerage provider not configured"}

        try:
            # Execute via Alpaca
            side = OrderSide.BUY if trade.action == "BUY" else OrderSide.SELL
            # Market order for simplicity as per prompt "submit_order" implication
            order = self.provider.submit_order(ticker=trade.ticker, qty=trade.quantity, side=side, type=OrderType.MARKET)

            trade.status = "EXECUTED"  # or SUBMITTED
            # potentially store order id if we added a column for it, but ProposedTrade schema in prompt didn't specify it.
            # We can store it in persona_logic or just log it.

            self.db.commit()
            return {"status": "success", "order_id": order.id, "trade_id": trade.id}

        except Exception as e:
            trade.status = "FAILED"
            self.db.commit()
            return {"error": str(e)}

    def get_portfolio(self) -> Dict[str, Any]:
        if not self.provider:
            return {}
        return self.provider.get_account()

    def get_positions(self) -> List[Dict[str, Any]]:
        if not self.provider:
            return []
        positions = self.provider.get_positions()
        return [p.model_dump() for p in positions]
