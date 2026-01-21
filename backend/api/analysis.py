import asyncio
import json
import random
import re
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, cast

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.runnables import RunnableConfig

from core.workflow import create_investment_committee_workflow
from models.events import CompleteEvent, ProgressUpdateEvent, StartEvent, UniverseEvent, RankingEvent
from utils.progress import progress
from screener.engine import run_screener
from screener.eligibility import EligibilityConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/factors/{ticker}")
async def get_factor_analysis(ticker: str):
    return {
        "value_score": random.randint(60, 140),
        "quality_score": random.randint(60, 140),
        "momentum_score": random.randint(60, 140),
        "growth_score": random.randint(60, 140),
        "risk_score": random.randint(60, 140),
    }


def extract_base_agent_key(unique_id: str) -> str:
    if not unique_id:
        return "unknown"
    parts = unique_id.split("_")
    if len(parts) >= 2:
        last_part = parts[-1]
        if len(last_part) == 6 and re.match(r"^[a-z0-9]+$", last_part):
            return "_".join(parts[:-1])
    return unique_id


@router.post("/screener/run")
async def run_screener_api(market: str = "US", k: int = 50, config: Optional[EligibilityConfig] = None):
    return run_screener(market=market, k=k, config=config)


@router.get("/stream/{ticker}")
async def stream_analysis_ticker(ticker: str, market: Optional[str] = None, k: Optional[int] = None):
    """
    Stream analysis updates using async LangGraph event streaming.
    """

    async def event_generator():
        print(f"SSE: New client connected for ticker: {ticker}")
        workflow = create_investment_committee_workflow()
        graph = workflow.compile()

        progress_queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def progress_handler(agent_name, agent_ticker, status, analysis, timestamp):
            try:
                if analysis and agent_name == "system" and "Universe Selected" in status:
                    try:
                        res = json.loads(analysis)
                        univ_event = UniverseEvent(
                            base_count=res["base_count"],
                            eligible_count=res["eligible_count"],
                            selected_symbols=res["selected_symbols"],
                            timestamp=timestamp
                        )
                        loop.call_soon_threadsafe(progress_queue.put_nowait, univ_event.to_sse())
                        
                        if "ranking" in res and res["ranking"]:
                            rank = res["ranking"]
                            top_k = []
                            for sym in rank["top_k_symbols"]:
                                factors = rank["scores_table"].get(sym, {})
                                top_k.append({
                                    "symbol": sym,
                                    "score": factors.get("composite_score", 0.0),
                                    "factors": factors
                                })
                            rank_event = RankingEvent(top_k=top_k, timestamp=timestamp)
                            loop.call_soon_threadsafe(progress_queue.put_nowait, rank_event.to_sse())
                    except: pass

                base_agent_name = extract_base_agent_key(agent_name)
                name_map = {
                    "warren_buffett_agent": "Buffett", "warren_buffett": "Buffett",
                    "cathie_wood_agent": "Wood", "cathie_wood": "Wood",
                    "charlie_munger_agent": "Munger", "charlie_munger": "Munger",
                    "phil_fisher_agent": "Fisher", "phil_fisher": "Fisher",
                    "bill_ackman_agent": "Ackman", "bill_ackman": "Ackman",
                    "michael_burry_agent": "Burry", "michael_burry": "Burry",
                    "ben_graham_agent": "Graham", "ben_graham": "Graham",
                    "peter_lynch_agent": "Lynch", "peter_lynch": "Lynch",
                    "stanley_druckenmiller_agent": "Druckenmiller", "stanley_druckenmiller": "Druckenmiller",
                    "aswath_damodaran_agent": "Damodaran", "aswath_damodaran": "Damodaran",
                    "mohnish_pabrai_agent": "Pabrai", "mohnish_pabrai": "Pabrai",
                    "rakesh_jhunjhunwala_agent": "Jhunjhunwala", "rakesh_jhunjhunwala": "Jhunjhunwala",
                    "portfolio_manager": "PortfolioManager",
                    "risk_management_agent": "RiskManager",
                    "technical_analyst_agent": "TechnicalAnalyst", "technical_analyst": "TechnicalAnalyst",
                    "fundamentals_analyst_agent": "FundamentalAnalyst", "fundamentals_analyst": "FundamentalAnalyst",
                    "sentiment_analyst_agent": "SentimentAnalyst", "sentiment_analyst": "SentimentAnalyst",
                    "news_sentiment_analyst_agent": "SentimentAnalyst", "news_sentiment_analyst": "SentimentAnalyst",
                    "growth_analyst_agent": "FundamentalAnalyst", "growth_analyst": "FundamentalAnalyst",
                    "valuation_analyst_agent": "Damodaran", "valuation_analyst": "Damodaran",
                    "quant_engine": "TechnicalAnalyst",
                    "system": "System"
                }

                display_name = name_map.get(base_agent_name, base_agent_name.replace("_agent", "").title().replace(" ", "").replace("_", ""))
                
                signal = "NEUTRAL"
                score = 50
                content = status
                confidence = 0
                magnitude = 0

                if analysis:
                    try:
                        data = json.loads(analysis) if isinstance(analysis, str) and analysis.strip().startswith("{") else analysis
                        if isinstance(data, dict):
                            lookup_ticker = agent_ticker if agent_ticker and agent_ticker != "GLOBAL" else (ticker if ticker != "GLOBAL" else None)
                            ticker_data = data.get(lookup_ticker) if lookup_ticker else data
                            if isinstance(ticker_data, dict):
                                signal = ticker_data.get("signal", signal)
                                score = ticker_data.get("score", score)
                                confidence = ticker_data.get("confidence", 0)
                                magnitude = ticker_data.get("magnitude", 0)
                                content = ticker_data.get("reasoning") or ticker_data.get("style_rationale") or status
                    except: pass

                payload = {
                    "schema_version": "1.0",
                    "agent": display_name, 
                    "ticker": agent_ticker or ticker,
                    "content": content, 
                    "signal": signal, 
                    "score": score, 
                    "confidence": confidence,
                    "magnitude": magnitude,
                    "timestamp": timestamp,
                    "insight": None, "target": None, "risk": None, "execution": None
                }
                event_data = ProgressUpdateEvent(type="progress", **payload)
                loop.call_soon_threadsafe(progress_queue.put_nowait, event_data.to_sse())
            except Exception as e:
                print(f"SSE Progress Error: {e}")

        progress.register_handler(progress_handler)

        try:
            yield f": {' ' * 2048}\n\n"
            # Start initial event
            yield StartEvent(timestamp=datetime.now(timezone.utc).isoformat()).to_sse()

            # Confirm engine is active
            progress.update_status("system", ticker, "Framework Engine Active")
            
            if ticker == "GLOBAL" and market:
                progress.update_status("system", None, f"Scanning {market} market for top {k} candidates...")

            now = datetime.now(timezone.utc)
            target_tickers = [ticker]
            effective_market = market
            effective_k = k
            
            if ticker == "GLOBAL" and not market:
                effective_market = "US"
                effective_k = 10
                target_tickers = []
            elif ticker == "GLOBAL":
                target_tickers = []

            # Prepare state
            initial_state = {
                "messages": [],
                "data": {
                    "tickers": target_tickers,
                    "portfolio": {"cash": 100000.0, "positions": {}, "market": effective_market, "k": effective_k},
                    "start_date": (now - timedelta(days=90)).strftime("%Y-%m-%d"),
                    "end_date": now.strftime("%Y-%m-%d"),
                    "analyst_signals": {},
                    "market": effective_market,
                    "k": effective_k
                }
            }
            
            graph_config = cast(RunnableConfig, {
                "configurable": {
                    "model_name": "gpt-4.1",
                    "model_provider": "OpenAI",
                }
            })

            # Start the graph in a separate task
            async def run_logic():
                # Use astream_events for more granular control if needed, 
                # but astream is sufficient for now since we use custom progress handlers
                async for _ in graph.astream(initial_state, graph_config):
                    await asyncio.sleep(0.01)

            logic_task = asyncio.create_task(run_logic())

            # Yield events from the queue while the task is running
            while not logic_task.done() or not progress_queue.empty():
                try:
                    event = await asyncio.wait_for(progress_queue.get(), timeout=1.0)
                    yield event
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                except Exception as e:
                    print(f"SSE Yield Error: {e}")
                    await asyncio.sleep(0.1)

            yield "data: [DONE]\n\n"

        except Exception as e:
            print(f"SSE Stream Error: {e}")
            yield CompleteEvent(data={"error": str(e)}, timestamp=datetime.now(timezone.utc).isoformat()).to_sse()
        finally:
            progress.unregister_handler(progress_handler)
            print(f"SSE: Client disconnected for {ticker}")

    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream", 
        headers={
            "Cache-Control": "no-cache, no-transform", 
            "Connection": "keep-alive", 
            "X-Accel-Buffering": "no"
        }
    )