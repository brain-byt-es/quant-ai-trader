from langgraph.graph import END, StateGraph

from agents.chief_investment_officer import chief_investment_officer_agent
from agents.portfolio_manager import portfolio_management_agent
from agents.risk_manager import risk_management_agent
from core.quant_engine import universe_selection_node, factor_calculation_node
from graph.state import AgentState
from utils.analysts import get_analyst_nodes


def start(state: AgentState):
    return state


def create_investment_committee_workflow(selected_analysts=None):
    """
    Creates an optimized committee workflow.
    Ensures data is present before personas begin reasoning.
    """
    workflow = StateGraph(AgentState)
    workflow.add_node("start_node", start)

    # 1. DISCOVERY PHASE (FAST)
    # Finds the tickers (GLOBAL -> US Market -> Selected Symbols)
    workflow.add_node("discovery", universe_selection_node)
    workflow.add_edge("start_node", "discovery")

    # analysts nodes
    analyst_nodes = get_analyst_nodes()
    if selected_analysts is None:
        selected_analysts = list(analyst_nodes.keys())

    # We split agents into 'Data/Sentiment Analysts' and 'Strategy Personas'
    analytical_keys = {
        "technical_analyst", "fundamentals_analyst", "sentiment_analyst", 
        "growth_analyst", "valuation_analyst", "news_sentiment_analyst"
    }
    
    # 2. PARALLEL DATA PHASE
    # These agents and the Quant Engine run as soon as tickers are found.
    # They provide the 'facts' for the personas.
    workflow.add_node("quant_engine", factor_calculation_node)
    workflow.add_edge("discovery", "quant_engine")

    all_analytical_node_ids = []
    selected_personas = []

    for key in selected_analysts:
        node_name, node_func = analyst_nodes[key]
        if key in analytical_keys:
            workflow.add_node(node_name, node_func)
            workflow.add_edge("discovery", node_name)
            all_analytical_node_ids.append(node_name)
        else:
            selected_personas.append((node_name, node_func))

    # 3. REASONING PHASE
    # Personas start ONLY after the Quant Engine has finished the fundamental math.
    for node_name, node_func in selected_personas:
        workflow.add_node(node_name, node_func)
        workflow.add_edge("quant_engine", node_name)

    # 4. SYNTHESIS PHASE
    workflow.add_node("chief_investment_officer", chief_investment_officer_agent)

    # CIO waits for everyone
    workflow.add_edge("quant_engine", "chief_investment_officer")
    for node_id in all_analytical_node_ids:
        workflow.add_edge(node_id, "chief_investment_officer")
    for node_name, _ in selected_personas:
        workflow.add_edge(node_name, "chief_investment_officer")

    # 5. EXECUTION PHASE
    workflow.add_node("portfolio_manager", portfolio_management_agent)
    workflow.add_edge("chief_investment_officer", "portfolio_manager")

    workflow.add_node("risk_management_agent", risk_management_agent)
    workflow.add_edge("portfolio_manager", "risk_management_agent")
    workflow.add_edge("risk_management_agent", END)

    workflow.set_entry_point("start_node")
    return workflow
