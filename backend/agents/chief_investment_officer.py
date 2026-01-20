
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from graph.state import AgentState
from utils.llm import call_llm


class ConsensusSignal(BaseModel):
    action: str = Field(description="BUY, SELL, or HOLD")
    quantity: int = Field(description="Suggested quantity")
    confidence: float = Field(description="Confidence 0-1")
    reasoning: str = Field(description="Consensus reasoning")


def chief_investment_officer_agent(state: AgentState, agent_id: str = "chief_investment_officer"):
    """
    Synthesizes conflicting signals from personas into a single consensus.
    """
    analyst_signals = state["data"].get("analyst_signals", {})
    tickers = state["data"]["tickers"]

    consensus_decisions = {}

    for ticker in tickers:
        # Collect signals for this ticker
        debate_log = []
        for agent_name, ticker_signals in analyst_signals.items():
            if ticker in ticker_signals:
                signal_data = ticker_signals[ticker]
                # Assuming signal_data is a dict (from model_dump())
                if isinstance(signal_data, dict):
                    signal = signal_data.get("signal")
                    conf = signal_data.get("confidence")
                    reasoning = signal_data.get("reasoning") or signal_data.get("style_rationale")
                    debate_log.append(f"{agent_name}: {signal} (Conf: {conf}) - {reasoning}")
                else:
                    debate_log.append(f"{agent_name}: {str(signal_data)}")

        if not debate_log:
            continue

        debate_text = "\n".join(debate_log)

        # LLM Call for Consensus
        template = ChatPromptTemplate.from_messages([("system", "You are the Chief Investment Officer. Synthesize the debate below into a final trading decision."), ("human", "Ticker: {ticker}\nDebate:\n{debate_text}\n\nProvide ConsensusSignal JSON.")])

        # We need a default factory
        def default_consensus():
            return ConsensusSignal(action="HOLD", quantity=0, confidence=0.0, reasoning="No consensus")

        result = call_llm(prompt=template.invoke({"ticker": ticker, "debate_text": debate_text}), pydantic_model=ConsensusSignal, agent_name=agent_id, state=state, default_factory=default_consensus)

        consensus_decisions[ticker] = result.model_dump()

    # Store in state
    state["data"]["consensus"] = consensus_decisions

    return {"messages": [HumanMessage(content="Consensus Reached")], "data": state["data"]}
