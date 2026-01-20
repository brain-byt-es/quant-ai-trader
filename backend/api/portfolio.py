from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from services.trading_service import TradingService

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/stats")
async def get_portfolio_stats(db: Session = Depends(get_db)):
    """
    Get real-time portfolio statistics from Alpaca.
    """
    trading_service = TradingService(db)
    account = trading_service.get_account_summary()

    if "error" in account:
        # Fallback for UI if no keys
        return {"equity": 0, "buying_power": 0, "day_change_percent": 0}

    return {"equity": float(account.get("equity", 0)), "buying_power": float(account.get("buying_power", 0)), "day_change_percent": float(account.get("equity_change_percent", 0)) * 100}


@router.get("/positions")
async def get_portfolio_positions(db: Session = Depends(get_db)):
    """
    Get real-time portfolio positions from Alpaca.
    """
    trading_service = TradingService(db)
    positions = trading_service.get_portfolio_positions()
    return {"positions": positions}
