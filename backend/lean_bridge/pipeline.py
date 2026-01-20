from typing import List
from lean_bridge.contracts import Insight, PortfolioTarget, AlphaModel
from lean_bridge.context import AlgorithmContext

def run_lean_pipeline(
    context: AlgorithmContext, 
    alpha_models: List[AlphaModel],
    portfolio_model,
    risk_model,
    execution_model,
    data: dict
):
    """
    Executes the LEAN Algorithm Framework assembly line.
    """
    # 1. Alpha Layer: Generate Insights
    new_insights = []
    for model in alpha_models:
        insights = model.update(context, data)
        new_insights.extend(insights)
    
    context.add_insights(new_insights)
    context.clear_expired_insights(context.time)

    # 2. Portfolio Construction: Insights -> Targets
    targets = portfolio_model.create_targets(context.active_insights, context)

    # 3. Risk Management: Adjust Targets
    adjusted_targets = risk_model.adjust_targets(targets, context)

    # 4. Execution: Targets -> Orders
    execution_plan = execution_model.execute(adjusted_targets, context)

    return execution_plan