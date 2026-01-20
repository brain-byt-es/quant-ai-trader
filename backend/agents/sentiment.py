from agents.base_agent import PersonaAlphaModel
from lean_bridge.contracts import Insight
from graph.state import AgentState
from utils.progress import progress
from langchain_core.messages import HumanMessage

class SentimentAlphaModel(PersonaAlphaModel):
    def __init__(self):
        super().__init__("sentiment_analyst")

    def update(self, state: AgentState, data: str) -> list[Insight]:
        ticker = data
        progress.update_status(self.agent_id, ticker, "Aggregating Social Sentiment")
        insight = self.generate_insight(ticker, "neutral", 50.0) 
        return [insight]

def sentiment_analyst_agent(state: AgentState, agent_id: str = "sentiment_analyst"):
    model = SentimentAlphaModel()
    insights = []
    for ticker in state["data"]["tickers"]:
        insights.extend(model.update(state, ticker))
    
    if "insights" not in state["data"]:
        state["data"]["insights"] = []
    state["data"]["insights"].extend([i.model_dump() for i in insights])
    
    return {"messages": [HumanMessage(content="Sentiment analysis complete", name="sentiment_analyst")], "data": state["data"]}