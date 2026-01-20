from agents.base_agent import PersonaAlphaModel
from lean_bridge.contracts import Insight
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
import json
from langchain_core.messages import HumanMessage

class ValuationAlphaModel(PersonaAlphaModel):
    def __init__(self):
        super().__init__("valuation_analyst")

    def update(self, state: AgentState, ticker: str) -> list[Insight]:
        progress.update_status(self.agent_id, ticker, "Calculating Intrinsic Value")
        # Logic would perform DCF, Multiples, etc.
        
        insight = self.generate_insight(ticker, "neutral", 50.0) 
        return [insight]

def valuation_analyst_agent(state: AgentState, agent_id: str = "valuation_analyst"):
    model = ValuationAlphaModel()
    insights = []
    for ticker in state["data"]["tickers"]:
        insights.extend(model.update(state, ticker))
    
    if "insights" not in state["data"]: state["data"]["insights"] = []
    state["data"]["insights"].extend([i.model_dump() for i in insights])
    
    return {"messages": [HumanMessage(content="Valuation complete", name="valuation_analyst")], "data": state["data"]}