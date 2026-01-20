import json
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from graph.risk_management import InstitutionalRiskModel
from core.execution_planner import ExecutionPlanner
from lean_bridge.contracts import PortfolioTarget
from lean_bridge.context import AlgorithmContext
from utils.progress import progress
from datetime import datetime

def risk_management_agent(state: AgentState, agent_id: str = "risk_management_agent"):
    """
    Hard-coded mathematical gate for the entire portfolio.
    """
    data = state["data"]
    
    # 1. Prepare AlgorithmContext
    context = AlgorithmContext(
        time=datetime.utcnow(),
        universe=data.get("tickers", []),
        portfolio_state=data.get("portfolio", {}),
        config={
            "current_prices": data.get("current_prices", {}),
            "quant_scorecard": data.get("quant_scorecard", {})
        }
    )
    
    # 2. Rehydrate Targets
    targets_data = data.get("portfolio_targets", [])
    targets = [PortfolioTarget(symbol=t["symbol"], quantity=t["quantity"]) for t in targets_data]
    
    progress.update_status(agent_id, None, "Mathematical Risk Gate")
    
    # 3. Risk Management Model
    rm = InstitutionalRiskModel()
    adjusted_targets = rm.adjust_targets(targets, context)
    
    # 4. Final Execution Plan
    execution_planner = ExecutionPlanner()
    execution_plan = execution_planner.execute(adjusted_targets, context)
    
    final_decisions = {}
    for plan in execution_plan:
        final_decisions[plan["ticker"]] = {
            "action": plan["action"],
            "quantity": plan["quantity"],
            "confidence": 1.0,
            "reasoning": f"RISK APPROVED: {plan['reasoning']}"
        }
        
    data["decisions"] = final_decisions
    
    message = HumanMessage(content=json.dumps(final_decisions), name=agent_id)
    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(final_decisions, "Risk Manager")
        
    return {
        "messages": [message],
        "data": data
    }
