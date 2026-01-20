import asyncio
import json
import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from core.workflow import create_investment_committee_workflow
from models.events import CompleteEvent, ProgressUpdateEvent, StartEvent
from services.graph import run_graph_async
from utils.progress import progress

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/factors/{ticker}")
async def get_factor_analysis(ticker: str):
    """
    Get factor analysis (Value, Quality, Momentum) for a ticker.
    In a real app, this would call quant_engine.py.
    """
    # Simulate real quant analysis
    return {
        "value_score": random.randint(60, 140),
        "quality_score": random.randint(60, 140),
        "momentum_score": random.randint(60, 140),
        "growth_score": random.randint(60, 140),
        "risk_score": random.randint(60, 140),
    }


@router.get("/stream/{ticker}")
async def stream_analysis_ticker(ticker: str):
    """
    Stream analysis updates for a single ticker using the shared progress tracker.
    """

    async def event_generator():
        # Setup workflow
        workflow = create_investment_committee_workflow()
        graph = workflow.compile()

        # Queue for progress updates
        progress_queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        # Simple handler to add updates to the queue (thread-safe)
        def progress_handler(agent_name, agent_ticker, status, analysis, timestamp):
            # Log to console for debugging
            print(f"Stream Update: {agent_name} -> {status} ({agent_ticker or 'Global'})")

            # Only care about updates for THIS ticker
            if agent_ticker is None or agent_ticker == ticker:
                # Map internal agent names to frontend AGENTS keys
                name_map = {
                    "warren_buffett_agent": "Buffett",
                    "cathie_wood_agent": "Wood",
                    "charlie_munger_agent": "Munger",
                    "phil_fisher_agent": "Fisher",
                    "bill_ackman_agent": "Ackman",
                    "michael_burry_agent": "Burry",
                    "ben_graham_agent": "Graham",
                    "peter_lynch_agent": "Lynch",
                    "stanley_druckenmiller_agent": "Druckenmiller",
                    "aswath_damodaran_agent": "Damodaran",
                    "mohnish_pabrai_agent": "Pabrai",
                    "rakesh_jhunjhunwala_agent": "Jhunjhunwala",
                    "portfolio_manager": "PortfolioManager",
                    "risk_management_agent": "RiskManager",
                    "technical_analyst_agent": "TechnicalAnalyst",
                    "fundamentals_analyst_agent": "FundamentalAnalyst",
                    "sentiment_analyst_agent": "SentimentAnalyst",
                    "news_sentiment_analyst_agent": "SentimentAnalyst",
                    "growth_analyst_agent": "FundamentalAnalyst",
                    "valuation_analyst_agent": "Damodaran",
                    "quant_engine": "TechnicalAnalyst",
                }

                display_name = name_map.get(agent_name, agent_name.replace("_agent", "").title().replace(" ", ""))

                # Format for the frontend expectations in LiveDebateFloor.tsx
                # LiveDebateFloor expects: { agent, signal, score, content, timestamp }

                signal = "NEUTRAL"
                score = 50
                content = status
                confidence = 0
                magnitude = 0

                if analysis:
                    try:
                        data = None
                        if isinstance(analysis, dict):
                            data = analysis
                        elif isinstance(analysis, str) and analysis.strip().startswith("{"):
                            data = json.loads(analysis)

                        if data:
                            # If it's a ticker-mapped dict, get our ticker's data
                            ticker_data = data.get(ticker) if isinstance(data, dict) else data

                            if isinstance(ticker_data, dict):
                                signal = ticker_data.get("signal", signal)
                                score = ticker_data.get("score", score)
                                confidence = ticker_data.get("confidence", 0)
                                magnitude = ticker_data.get("magnitude", 0)
                                # Use reasoning or style_rationale if available, otherwise keep status
                                content = ticker_data.get("reasoning") or ticker_data.get("style_rationale") or status
                            else:
                                content = str(analysis)
                        else:
                            content = str(analysis)
                    except:
                        content = str(analysis)

                payload = {
                    "schema_version": "1.0",
                    "agent": display_name, 
                    "ticker": ticker,
                    "content": content, 
                    "signal": signal, 
                    "score": score, 
                    "confidence": confidence,
                    "magnitude": magnitude,
                    "timestamp": timestamp,
                    # Placeholders for future enriched DTOs
                    "insight": None,
                    "target": None,
                    "risk": None,
                    "execution": None
                }
                loop.call_soon_threadsafe(progress_queue.put_nowait, f"data: {json.dumps(payload)}\n\n")

        # Register our handler
        progress.register_handler(progress_handler)

        try:
            # Send a large comment to bypass any intermediate proxy buffers (e.g. 2KB)
            yield f": {' ' * 2048}\n\n"

            # Start initial event
            yield f"data: {json.dumps({'agent': 'system', 'content': f'Initializing stream for {ticker}...', 'signal': 'NEUTRAL', 'score': 50, 'timestamp': datetime.now(timezone.utc).isoformat()})}\\n\n"

            # Start graph execution in background
            now = datetime.now(timezone.utc)
            run_task = asyncio.create_task(
                run_graph_async(
                    graph=graph,
                    portfolio={"cash": 100000.0, "positions": {}, "margin_requirement": 0.0, "realized_gains": {}},
                    tickers=[ticker],
                    start_date=(now - timedelta(days=90)).strftime("%Y-%m-%d"),
                    end_date=now.strftime("%Y-%m-%d"),
                    model_name="gpt-4.1",
                    model_provider="OpenAI",
                )
            )

            # Stream from queue
            while not run_task.done() or not progress_queue.empty():
                try:
                    event = await asyncio.wait_for(progress_queue.get(), timeout=0.2)
                    yield event
                except asyncio.TimeoutError:
                    yield ": ping\n\n"

                await asyncio.sleep(0.01)

            # Wait for final result to ensure everything is done
            await run_task

            # Final Done signal
            yield "data: [DONE]\n\n"

        except Exception as e:
            err_payload = {"agent": "system", "content": f"Error: {str(e)}", "signal": "NEUTRAL", "score": 50, "timestamp": datetime.now(timezone.utc).isoformat()}
            yield f"data: {json.dumps(err_payload)}\n\n"
        finally:
            progress.unregister_handler(progress_handler)

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})
