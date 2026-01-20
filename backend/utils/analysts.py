"""Constants and utilities related to analysts configuration."""

from utils.analyst_rules import ANALYST_CONFIG_RULES

# 1. First, define the configuration skeleton from the rules
ANALYST_CONFIG = {key: value.copy() for key, value in ANALYST_CONFIG_RULES.items()}

# 2. Now import the agents (this can cause circular imports if the agents import ANALYST_CONFIG)
# but now we will guide agents to import from analyst_rules instead.
from agents.aswath_damodaran import aswath_damodaran_agent
from agents.ben_graham import ben_graham_agent
from agents.bill_ackman import bill_ackman_agent
from agents.cathie_wood import cathie_wood_agent
from agents.charlie_munger import charlie_munger_agent
from agents.fundamentals import fundamentals_analyst_agent
from agents.growth_agent import growth_analyst_agent
from agents.michael_burry import michael_burry_agent
from agents.mohnish_pabrai import mohnish_pabrai_agent
from agents.news_sentiment import news_sentiment_agent
from agents.peter_lynch import peter_lynch_agent
from agents.phil_fisher import phil_fisher_agent
from agents.rakesh_jhunjhunwala import rakesh_jhunjhunwala_agent
from agents.sentiment import sentiment_analyst_agent
from agents.stanley_druckenmiller import stanley_druckenmiller_agent
from agents.technicals import technical_analyst_agent
from agents.valuation import valuation_analyst_agent
from agents.warren_buffett import warren_buffett_agent

# 3. Add the agent functions to the config
ANALYST_CONFIG["aswath_damodaran"]["agent_func"] = aswath_damodaran_agent
ANALYST_CONFIG["ben_graham"]["agent_func"] = ben_graham_agent
ANALYST_CONFIG["bill_ackman"]["agent_func"] = bill_ackman_agent
ANALYST_CONFIG["cathie_wood"]["agent_func"] = cathie_wood_agent
ANALYST_CONFIG["charlie_munger"]["agent_func"] = charlie_munger_agent
ANALYST_CONFIG["michael_burry"]["agent_func"] = michael_burry_agent
ANALYST_CONFIG["mohnish_pabrai"]["agent_func"] = mohnish_pabrai_agent
ANALYST_CONFIG["peter_lynch"]["agent_func"] = peter_lynch_agent
ANALYST_CONFIG["phil_fisher"]["agent_func"] = phil_fisher_agent
ANALYST_CONFIG["rakesh_jhunjhunwala"]["agent_func"] = rakesh_jhunjhunwala_agent
ANALYST_CONFIG["stanley_druckenmiller"]["agent_func"] = stanley_druckenmiller_agent
ANALYST_CONFIG["warren_buffett"]["agent_func"] = warren_buffett_agent
ANALYST_CONFIG["technical_analyst"]["agent_func"] = technical_analyst_agent
ANALYST_CONFIG["fundamentals_analyst"]["agent_func"] = fundamentals_analyst_agent
ANALYST_CONFIG["growth_analyst"]["agent_func"] = growth_analyst_agent
ANALYST_CONFIG["news_sentiment_analyst"]["agent_func"] = news_sentiment_agent
ANALYST_CONFIG["sentiment_analyst"]["agent_func"] = sentiment_analyst_agent
ANALYST_CONFIG["valuation_analyst"]["agent_func"] = valuation_analyst_agent

# Derive ANALYST_ORDER from ANALYST_CONFIG for backwards compatibility
ANALYST_ORDER = [(config["display_name"], key) for key, config in sorted(ANALYST_CONFIG.items(), key=lambda x: x[1]["order"])]


def get_analyst_nodes():
    """Get the mapping of analyst keys to their (node_name, agent_func) tuples."""
    return {key: (f"{key}_agent", config["agent_func"]) for key, config in ANALYST_CONFIG.items()}


def get_agents_list():
    """Get the list of agents for API responses."""
    return [{"key": key, "display_name": config["display_name"], "description": config["description"], "investing_style": config["investing_style"], "order": config["order"]} for key, config in sorted(ANALYST_CONFIG.items(), key=lambda x: x[1]["order"])]
