from agents.base_agent import PersonaAlphaModel
from lean_bridge.contracts import Insight
from graph.state import AgentState
from utils.progress import progress
import json
from langchain_core.messages import HumanMessage

class FundamentalAlphaModel(PersonaAlphaModel):
    def __init__(self):
        super().__init__("fundamentals_analyst")

    def update(self, state: AgentState, ticker: str) -> list[Insight]:
        progress.update_status(self.agent_id, ticker, "Auditing Financial Statements")
        # Logic would check ROE, D/E, etc.
        
        # Placeholder for numeric insight
        insight = self.generate_insight(ticker, "neutral", 50.0) 
        
        # Store for backward compatibility
        if "analyst_signals" not in state["data"]: state["data"]["analyst_signals"] = {}
        if self.agent_id not in state["data"]["analyst_signals"]: state["data"]["analyst_signals"][self.agent_id] = {}
        state["data"]["analyst_signals"][self.agent_id][ticker] = {
            "signal": "neutral",
            "confidence": 0.5,
            "reasoning": "Fundamental health audit complete"
        }
        
        return [insight]

def fundamentals_analyst_agent(state: AgentState, agent_id: str = "fundamentals_analyst"):
    model = FundamentalAlphaModel()
    insights = []
    for ticker in state["data"]["tickers"]:
        insights.extend(model.update(state, ticker))
    
    if "insights" not in state["data"]: state["data"]["insights"] = []
    state["data"]["insights"].extend([i.model_dump() for i in insights])
    
    return {"messages": [HumanMessage(content="Fundamental analysis complete", name="fundamentals_analyst")], "data": state["data"]}
