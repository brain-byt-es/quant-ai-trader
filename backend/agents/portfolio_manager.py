import json
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from core.portfolio_manager import MeanVarianceOptimizationPortfolioConstructionModel
from core.execution_planner import ExecutionPlanner
from lean_bridge.contracts import Insight
from lean_bridge.context import AlgorithmContext
from utils.progress import progress
from datetime import datetime, UTC

def portfolio_management_agent(state: AgentState, agent_id: str = "portfolio_manager"):
    """
    Aggregates insights using LEAN-faithful MVO.
    """
    data = state["data"]
    
    # 1. Prepare AlgorithmContext
    context = AlgorithmContext(
        time=datetime.now(UTC),
        universe=data.get("tickers", []),
        portfolio_state=data.get("portfolio", {}),
        config={
            "current_prices": data.get("current_prices", {}),
            "quant_scorecard": data.get("quant_scorecard", {})
        }
    )
    
    # 2. Rehydrate Insights
    insights_data = data.get("insights", [])
    active_insights = [Insight(**i) for i in insights_data]
    
    progress.update_status(agent_id, None, "Optimizing Weights (MVO)")
    
    # 3. Portfolio Construction (MVO)
    pcm = MeanVarianceOptimizationPortfolioConstructionModel()
    targets = pcm.create_targets(active_insights, context)
    
    # Store targets for Risk Management
    data["portfolio_targets"] = [t.model_dump() for t in targets]
    
    # 4. Preliminary decisions for UI (State-aware)
    execution_planner = ExecutionPlanner()
    execution_plan = execution_planner.execute(targets, context)
    
    decisions = {}
    for plan in execution_plan:
        decisions[plan["ticker"]] = {
            "action": plan["action"],
            "quantity": plan["quantity"],
            "confidence": 1.0,
            "reasoning": plan["reasoning"]
        }
    
    data["decisions"] = decisions
    
    message = HumanMessage(content=json.dumps(decisions), name=agent_id)
    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(decisions, "Portfolio Manager (MVO)")
        
    return {
        "messages": [message],
        "data": data
    }