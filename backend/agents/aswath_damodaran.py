from agents.base_agent import PersonaAlphaModel
from lean_bridge.contracts import Insight
from agents.types import AgentDebate
from graph.state import AgentState
from utils.analyst_rules import ANALYST_CONFIG_RULES
from utils.llm import call_llm
from utils.progress import progress
import json
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

class AswathDamodaranAlphaModel(PersonaAlphaModel):
    def __init__(self):
        super().__init__("aswath_damodaran")

    def update(self, state: AgentState, data: str) -> list[Insight]:
        ticker = data
        quant_scorecard = state["data"].get("quant_scorecard", {})
        config = ANALYST_CONFIG_RULES.get(self.agent_id)
        if not config:
            return []
        factor_rules = config["factor_rules"]

        progress.update_status(self.agent_id, ticker, "Intrinsic Valuation Audit")
        ticker_data = quant_scorecard.get(ticker, {})
        metrics = ticker_data.get("metrics", {})
        facts = {"metrics": metrics, "rules": factor_rules}

        template = ChatPromptTemplate.from_messages([
            ("system", "You are Aswath Damodaran. Value the company. YOUR RULES: {rules}. Output JSON only."),
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

def aswath_damodaran_agent(state: AgentState, agent_id: str = "aswath_damodaran"):
    model = AswathDamodaranAlphaModel()
    insights = []
    for ticker in state["data"]["tickers"]:
        insights.extend(model.update(state, ticker))
    
    if "insights" not in state["data"]:
        state["data"]["insights"] = []
    state["data"]["insights"].extend([i.model_dump() for i in insights])
    
    return {"messages": [HumanMessage(content="Analysis complete", name="aswath_damodaran")], "data": state["data"]}
