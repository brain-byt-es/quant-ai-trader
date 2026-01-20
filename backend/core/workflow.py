from langgraph.graph import END, StateGraph

from agents.chief_investment_officer import chief_investment_officer_agent
from agents.portfolio_manager import portfolio_management_agent
from agents.risk_manager import risk_management_agent
from core.quant_engine import quant_engine_node
from graph.state import AgentState
from utils.analysts import get_analyst_nodes


def start(state: AgentState):
    return state


def create_investment_committee_workflow(selected_analysts=None):
    workflow = StateGraph(AgentState)
    workflow.add_node("start_node", start)

    # Separate Analytical Agents and Personas
    # Hardcoded set of analytical agents based on prompt
    analytical_keys = {"technical_analyst", "fundamentals_analyst", "sentiment_analyst", "growth_analyst", "valuation_analyst", "news_sentiment_analyst"}

    analyst_nodes = get_analyst_nodes()

    # If selected_analysts is provided, filter. Otherwise use all.
    if selected_analysts is None:
        selected_analysts = list(analyst_nodes.keys())

    # Split selected into analytical vs personas
    selected_analytical = [k for k in selected_analysts if k in analytical_keys]
    selected_personas = [k for k in selected_analysts if k not in analytical_keys]

    # 1. Run Analytical Agents (Data Gathering) - Sequential to avoid race conditions
    last_node = "start_node"
    for key in selected_analytical:
        node_name, node_func = analyst_nodes[key]
        workflow.add_node(node_name, node_func)
        workflow.add_edge(last_node, node_name)
        last_node = node_name

    # 2. Quant Engine (Calculates Scorecard)
    workflow.add_node("quant_engine", quant_engine_node)

    # Connect last analytical agent to Quant Engine
    workflow.add_edge(last_node, "quant_engine")

    # 3. Run Persona Agents (Debate Scorecard)
    for key in selected_personas:
        node_name, node_func = analyst_nodes[key]
        workflow.add_node(node_name, node_func)
        # Quant Engine -> Personas
        workflow.add_edge("quant_engine", node_name)

    # 4. Consensus (CIO)
    workflow.add_node("chief_investment_officer", chief_investment_officer_agent)

    # Personas -> CIO
    for key in selected_personas:
        node_name = analyst_nodes[key][0]
        workflow.add_edge(node_name, "chief_investment_officer")

    # 5. Portfolio Manager (Sizing)
    workflow.add_node("portfolio_manager", portfolio_management_agent)
    workflow.add_edge("chief_investment_officer", "portfolio_manager")

    # 6. Risk Manager (Gate)
    workflow.add_node("risk_management_agent", risk_management_agent)
    workflow.add_edge("portfolio_manager", "risk_management_agent")
    workflow.add_edge("risk_management_agent", END)

    workflow.set_entry_point("start_node")
    return workflow
