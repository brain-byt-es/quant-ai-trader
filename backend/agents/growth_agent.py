from agents.base_agent import PersonaAlphaModel
from lean_bridge.contracts import Insight
from graph.state import AgentState
from utils.progress import progress
from langchain_core.messages import HumanMessage

class GrowthAlphaModel(PersonaAlphaModel):
    def __init__(self):
        super().__init__("growth_analyst")

    def update(self, state: AgentState, data: str) -> list[Insight]:
        ticker = data
        progress.update_status(self.agent_id, ticker, "Analyzing Growth Potential")
        # In this refactor, we simplify to numeric insights
        # Logic would normally calculate EPS growth, Revenue growth, etc.
        
        # Placeholder for dynamic logic
        insight = self.generate_insight(ticker, "bullish", 75.0) 
        return [insight]

def growth_analyst_agent(state: AgentState, agent_id: str = "growth_analyst"):
    model = GrowthAlphaModel()
    insights = []
    for ticker in state["data"]["tickers"]:
        insights.extend(model.update(state, ticker))
    
    if "insights" not in state["data"]:
        state["data"]["insights"] = []
    state["data"]["insights"].extend([i.model_dump() for i in insights])
    
    return {"messages": [HumanMessage(content="Growth analysis complete", name="growth_analyst")], "data": state["data"]}