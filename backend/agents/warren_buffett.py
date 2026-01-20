from agents.base_agent import PersonaAlphaModel
from lean_bridge.contracts import Insight
from agents.types import AgentDebate
from graph.state import AgentState, show_agent_reasoning
from utils.analyst_rules import ANALYST_CONFIG_RULES
from utils.llm import call_llm
from utils.progress import progress
import json
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

class WarrenBuffettAlphaModel(PersonaAlphaModel):
    def __init__(self):
        super().__init__("warren_buffett")

    def update(self, state: AgentState, ticker: str) -> list[Insight]:
        quant_scorecard = state["data"].get("quant_scorecard", {})
        config = ANALYST_CONFIG_RULES.get(self.agent_id)
        factor_rules = config["factor_rules"]

        progress.update_status(self.agent_id, ticker, "Analyzing Scorecard")
        ticker_data = quant_scorecard.get(ticker, {})
        metrics = ticker_data.get("metrics", {})
        z_scores = ticker_data.get("z_scores", {})
        facts = {"metrics": metrics, "z_scores": z_scores, "rules": factor_rules}

        template = ChatPromptTemplate.from_messages([
            ("system", "You are Warren Buffett. Evaluate the ticker based on metrics and strict rules. YOUR RULES: {rules}. Output JSON only."),
            ("human", "Ticker: {ticker}\nScorecard: {facts}")
        ])
        prompt = template.invoke({"facts": json.dumps(facts), "ticker": ticker, "rules": factor_rules})

        def _default():
            return AgentDebate(persona_id=self.agent_id, signal="neutral", confidence=0.5, sentiment_score=0.0, style_rationale="Insufficient data")

        output = call_llm(prompt=prompt, pydantic_model=AgentDebate, agent_name=self.agent_id, state=state, default_factory=_default)
        
        insight = self.generate_insight(ticker, output.signal, output.confidence)
        progress.update_status(self.agent_id, ticker, "Done", analysis=output.style_rationale)
        
        if "analyst_signals" not in state["data"]:
            state["data"]["analyst_signals"] = {}
        if self.agent_id not in state["data"]["analyst_signals"]:
            state["data"]["analyst_signals"][self.agent_id] = {}
        state["data"]["analyst_signals"][self.agent_id][ticker] = output.model_dump()
        
        return [insight]

def warren_buffett_agent(state: AgentState, agent_id: str = "warren_buffett"):
    model = WarrenBuffettAlphaModel()
    insights = []
    for ticker in state["data"]["tickers"]:
        insights.extend(model.update(state, ticker))
    
    if "insights" not in state["data"]:
        state["data"]["insights"] = []
    state["data"]["insights"].extend([i.model_dump() for i in insights])
    
    return {"messages": [HumanMessage(content=json.dumps(state["data"]["analyst_signals"].get("warren_buffett", {})), name="warren_buffett")], "data": state["data"]}