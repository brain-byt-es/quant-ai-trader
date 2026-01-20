from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from database.connection import get_db
from services.brokerage import BrokerageService

router = APIRouter(prefix="/api/v1/trades", tags=["trades"])


@router.post("/approve/{token}")
async def approve_trade(token: str = Path(..., description="Approval token for the trade"), db: Session = Depends(get_db)):
    """
    Execute a trade that is in PENDING status using its approval token.
    HITL: This endpoint is called when the human user clicks 'Approve'.
    """
    service = BrokerageService(db)
    result = service.execute_trade_by_token(token)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
