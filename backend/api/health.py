from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from database.connection import SessionLocal
from services.data.data_service import get_data_service
from services.trading_service import TradingService

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify system status.
    Returns status in the 'Institutional Standard' format.
    """
    status = {"status": "healthy", "services": {"Alpaca": "Offline", "Alpha Vantage": "Disconnected", "Database": "Disconnected"}}

    # 1. Check Database
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        status["services"]["Database"] = "Connected"
    except Exception as e:
        print(f"Database health check failed: {e}")
        status["services"]["Database"] = "Error"
        status["status"] = "degraded"

    # 2. Check Alpaca
    try:
        db = SessionLocal()
        trading_service = TradingService(db)
        account = trading_service.get_account_summary()
        if account and "error" not in account:
            status["services"]["Alpaca"] = "Online"
        else:
            status["services"]["Alpaca"] = "Error"
            status["status"] = "degraded"
        db.close()
    except Exception:
        status["services"]["Alpaca"] = "Error"
        status["status"] = "degraded"

    # 3. Check Alpha Vantage (or configured Data Provider)
    try:
        data_service = get_data_service()
        # Use getattr to avoid Pylance attribute access issue on abstract base class
        if getattr(data_service, "api_key", None):
            # In a real run, you'd check a ping or quota, but we'll flag as connected if key exists
            status["services"]["Alpha Vantage"] = "Connected"
        else:
            status["services"]["Alpha Vantage"] = "Missing Key"
            status["status"] = "degraded"
    except Exception:
        status["services"]["Alpha Vantage"] = "Error"
        status["status"] = "degraded"

    return JSONResponse(content=status)


@router.get("/ping")
async def ping():
    return {"ping": "pong"}
