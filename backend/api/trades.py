from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from services.trading_service import TradingService

router = APIRouter(prefix="/trading", tags=["trading"])


@router.post("/kill-switch")
async def kill_switch(db: Session = Depends(get_db)):
    """
    Emergency Mass Liquidation: 
    1. Cancels all open orders.
    2. Closes all active positions at market price.
    """
    try:
        trading_service = TradingService(db)
        if not trading_service.provider:
            raise HTTPException(status_code=400, detail="Trading provider not configured")
            
        # The AlpacaProvider now handles mass liquidation via the DELETE /v2/positions endpoint
        # We access the provider directly through the service for this administrative task
        results = trading_service.provider.liquidate_all_positions(cancel_orders=True)
        
        return {
            "status": "success",
            "message": "Mass liquidation triggered successfully",
            "orders_created": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kill Switch Failed: {str(e)}")


@router.get("/account")
async def get_account(db: Session = Depends(get_db)):
    """Get account information."""
    trading_service = TradingService(db)
    return trading_service.get_account_summary()


@router.get("/positions")
async def get_positions(db: Session = Depends(get_db)):
    """Get current portfolio positions."""
    trading_service = TradingService(db)
    return {"positions": trading_service.get_portfolio_positions()}