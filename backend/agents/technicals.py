from agents.base_agent import PersonaAlphaModel
from lean_bridge.contracts import Insight
from graph.state import AgentState
from utils.progress import progress
from langchain_core.messages import HumanMessage

class TechnicalAlphaModel(PersonaAlphaModel):
    def __init__(self):
        super().__init__("technical_analyst")

    def update(self, state: AgentState, data: str) -> list[Insight]:
        ticker = data
        progress.update_status(self.agent_id, ticker, "Running Indicator Sweep")
        # Logic would calculate RSI, MACD, etc.
        # In a real run, we'd use the scorecard metrics
        
        # Placeholder for numeric insight
        insight = self.generate_insight(ticker, "neutral", 50.0) 
        
        # Store for backward compatibility
        if "analyst_signals" not in state["data"]:
            state["data"]["analyst_signals"] = {}
        if self.agent_id not in state["data"]["analyst_signals"]:
            state["data"]["analyst_signals"][self.agent_id] = {}
        state["data"]["analyst_signals"][self.agent_id][ticker] = {
            "signal": "neutral",
            "confidence": 0.5,
            "reasoning": "Technical indicators neutral"
        }
        
        return [insight]

def technical_analyst_agent(state: AgentState, agent_id: str = "technical_analyst"):
    model = TechnicalAlphaModel()
    insights = []
    for ticker in state["data"]["tickers"]:
        insights.extend(model.update(state, ticker))
    
    if "insights" not in state["data"]:
        state["data"]["insights"] = []
    state["data"]["insights"].extend([i.model_dump() for i in insights])
    
    return {"messages": [HumanMessage(content="Technical analysis complete", name="technical_analyst")], "data": state["data"]}
