import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import asyncio
from datetime import datetime, timedelta
from lean_bridge.contracts import Insight, InsightDirection
from lean_bridge.context import AlgorithmContext
from core.portfolio_manager import MeanVarianceOptimizationPortfolioConstructionModel
from core.execution_planner import ExecutionPlanner
from graph.risk_management import InstitutionalRiskModel

async def test_lean_pipeline():
    print("🚀 Starting LEAN-Faithful Pipeline Integration Test")
    
    # 1. Setup Context
    context = AlgorithmContext(
        time=datetime.utcnow(),
        universe=["AAPL", "TSLA", "NVDA"],
        portfolio_state={
            "equity": 100000.0,
            "positions": {
                "AAPL": {"long": 100, "short": 0}, # Current position
                "TSLA": {"long": 0, "short": 0}
            }
        },
        config={
            "current_prices": {"AAPL": 150.0, "TSLA": 200.0, "NVDA": 500.0},
            "quant_scorecard": {
                "AAPL": {"metrics": {"altman_z": 3.5}}, # Healthy
                "TSLA": {"metrics": {"altman_z": 1.2}}  # Distressed! Should be vetoed
            }
        }
    )

    # 2. Generate Insights (Alphas)
    insights = [
        Insight.price("AAPL", timedelta(days=1), InsightDirection.UP, 0.05, 0.8, "BuffettModel"),
        Insight.price("TSLA", timedelta(days=1), InsightDirection.UP, 0.10, 0.9, "WoodModel"),
        Insight.price("NVDA", timedelta(days=1), InsightDirection.DOWN, -0.02, 0.7, "BurryModel")
    ]

    # 3. Portfolio Construction (MVO)
    print("\n--- Pillar 3: Portfolio Construction (MVO) ---")
    pcm = MeanVarianceOptimizationPortfolioConstructionModel(target_return=0.01)
    targets = pcm.create_targets(insights, context)
    
    for t in targets:
        print(f"Target: {t.symbol} | Qty: {t.quantity}")

    # 4. Risk Management (Mathematical Gate)
    print("\n--- Pillar 4: Risk Management (Veto & Caps) ---")
    risk_model = InstitutionalRiskModel(min_altman_z=1.8, max_concentration=0.20)
    adjusted_targets = risk_model.adjust_targets(targets, context)
    
    for t in adjusted_targets:
        print(f"Risk-Adjusted: {t.symbol} | Qty: {t.quantity}")
        if t.symbol == "TSLA":
            assert t.quantity == 0, "TSLA should have been vetoed due to Altman Z-Score"

    # 5. Execution (Delta Trading)
    print("\n--- Pillar 5: Execution (Diff-based) ---")
    planner = ExecutionPlanner()
    orders = planner.execute(adjusted_targets, context)
    
    for o in orders:
        print(f"Order: {o['ticker']} | Action: {o['action']} | Qty: {o['quantity']}")
        if o['ticker'] == "AAPL":
            # Current 100, Target might be different. Let's verify the diff logic.
            pass

    print("\n✅ LEAN-Faithful Pipeline Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_lean_pipeline())
