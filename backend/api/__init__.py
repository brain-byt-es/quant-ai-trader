from fastapi import APIRouter

from api.analysis import router as analysis_router
from api.api_keys import router as api_keys_router
from api.flow_runs import router as flow_runs_router
from api.flows import router as flows_router
from api.health import router as health_router
from api.hedge_fund import router as hedge_fund_router
from api.language_models import router as language_models_router
from api.ollama import router as ollama_router
from api.portfolio import router as portfolio_router
from api.storage import router as storage_router
from api.trades import router as trades_router

# Main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router, tags=["health"])
api_router.include_router(hedge_fund_router, tags=["hedge-fund"])
api_router.include_router(storage_router, tags=["storage"])
api_router.include_router(flows_router, tags=["flows"])
api_router.include_router(flow_runs_router, tags=["flow-runs"])
api_router.include_router(ollama_router, tags=["ollama"])
api_router.include_router(language_models_router, tags=["language-models"])
api_router.include_router(api_keys_router, tags=["api-keys"])
api_router.include_router(analysis_router, tags=["analysis"])
api_router.include_router(trades_router, tags=["trades"])
api_router.include_router(portfolio_router, tags=["portfolio"])
