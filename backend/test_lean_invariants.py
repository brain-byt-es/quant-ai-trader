import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import asyncio
from datetime import datetime, timedelta
import numpy as np
import random
from lean_bridge.contracts import Insight, InsightDirection, PortfolioTarget
from lean_bridge.context import AlgorithmContext
from core.portfolio_manager import MeanVarianceOptimizationPortfolioConstructionModel
from core.execution_planner import ExecutionPlanner
from graph.risk_management import InstitutionalRiskModel
from pydantic import ValidationError

async def test_lean_invariants():
    print("🧪 Hardened Deterministic Invariant Verification")
    
    # 0. Fixed Seed for Determinism
    np.random.seed(42)
    random.seed(42)

    # --- 1. Immutability Check ---
    print("Checking Invariant 1: Immutability (Frozen Models)")
    insight = Insight.price("AAPL", timedelta(days=1), InsightDirection.UP, 0.05, 0.8, "ModelA")
    try:
        # In Pydantic v2, assigning to frozen fields raises ValidationError
        insight.magnitude = 0.1
        raise AssertionError("FAILED: Insight is mutable")
    except (ValidationError, TypeError):
        print("  - [PASS] Insight is frozen")

    target = PortfolioTarget(symbol="AAPL", quantity=100.0)
    try:
        target.quantity = 200.0
        raise AssertionError("FAILED: PortfolioTarget is mutable")
    except (ValidationError, TypeError):
        print("  - [PASS] PortfolioTarget is frozen")

    # --- 2. Deterministic Insight Replacement ---
    print("Checking Invariant 2: Deterministic Lifecycle")
    from lean_bridge.insight_collection import InsightCollection
    collection = InsightCollection()
    
    t1 = datetime(2026, 1, 20, 12, 0, 0)
    t2 = t1 + timedelta(seconds=1)
    
    i1 = Insight(symbol="AAPL", generated_time_utc=t1, period=timedelta(days=1), direction=InsightDirection.UP, magnitude=0.05, source_model="M1")
    i2 = Insight(symbol="AAPL", generated_time_utc=t2, period=timedelta(days=1), direction=InsightDirection.DOWN, magnitude=-0.02, source_model="M1")
    
    collection.add([i1, i2])
    active = collection.get_active_insights(t2)
    assert len(active) == 1, f"Expected 1 insight, got {len(active)}"
    assert active[0].direction == InsightDirection.DOWN, "Tie-break failed: newest insight did not win"
    print("  - [PASS] Deterministic replacement (symbol, source_model) confirmed")

    # --- 3. MVO Pipeline Alignment & Constraints ---
    print("Checking Invariant 3: MVO Alignment and Constraints")
    equity = 100000.0
    context = AlgorithmContext(
        time=datetime(2026, 1, 20, 12, 0, 0),
        universe=["AAPL", "NVDA", "TSLA"],
        portfolio_state={"equity": equity, "positions": {"AAPL": {"long": 100, "short": 0}}},
        config={
            "current_prices": {"AAPL": 150.0, "TSLA": 200.0, "NVDA": 500.0},
            "quant_scorecard": {
                "AAPL": {"metrics": {"altman_z": 3.5}},
                "TSLA": {"metrics": {"altman_z": 1.2}}, # Risk distress
                "NVDA": {"metrics": {"altman_z": 4.0}}
            }
        }
    )

    insights = [
        Insight.price("AAPL", timedelta(days=1), InsightDirection.UP, 0.05, 0.8, "A1"),
        Insight.price("NVDA", timedelta(days=1), InsightDirection.DOWN, -0.02, 0.7, "A2"),
        # ADDED: TSLA insight to verify risk veto logic
        Insight.price("TSLA", timedelta(days=1), InsightDirection.UP, 0.03, 0.6, "A3")
    ]

    pcm = MeanVarianceOptimizationPortfolioConstructionModel(target_return=0.01)
    targets = pcm.create_targets(insights, context)
    
    # Verify Sum(Weights) == 1 via implied weights from targets
    implied_weights = []
    for t in targets:
        price = context.config["current_prices"][t.symbol]
        implied_weights.append((t.quantity * price) / equity)
    
    net_exposure = sum(implied_weights)
    print(f"  - Implied Net Exposure: {net_exposure:.6f}")
    assert abs(net_exposure - 1.0) < 1e-6, f"Sum(w) mismatch: net exposure {net_exposure:.6f} != 1.0"
    print("  - [PASS] Optimizer sum(w)=1 constraint verified via implied weights")

    # --- 4. Risk Gates ---
    print("Checking Invariant 4: Risk Veto & Cap")
    risk_model = InstitutionalRiskModel(min_altman_z=1.8, max_concentration=0.20)
    adjusted_targets = risk_model.adjust_targets(targets, context)
    
    tsla_target = next((t for t in adjusted_targets if t.symbol == "TSLA"), None)
    assert tsla_target is not None, "TSLA should be in targets (pre-veto)"
    assert tsla_target.quantity == 0, f"FAILED: TSLA (Altman Z=1.2) was not vetoed. Qty: {tsla_target.quantity}"
    print("  - [PASS] Risk Veto (Altman Z < 1.8) confirmed")
    
    for t in adjusted_targets:
        price = context.config["current_prices"][t.symbol]
        weight = abs(t.quantity * price) / equity
        assert weight <= 0.200001, f"FAILED: Concentration cap exceeded for {t.symbol} (weight {weight:.4f})"
    print("  - [PASS] Position Concentration Cap (20%) confirmed")

    # --- 5. Idempotent Execution ---
    print("Checking Invariant 5: Diff-based Orders")
    planner = ExecutionPlanner()
    orders = planner.execute(adjusted_targets, context)
    
    for o in orders:
        if o['ticker'] == "AAPL":
            # Target ~20k / 150 = 133. Current = 100. Delta = 33.
            assert o['quantity'] == 33, f"Delta calculation failed: expected 33, got {o['quantity']}"
    print("  - [PASS] Idempotent delta trading (Target - Current) confirmed")

    print("\n✅ PROOF BUNDLE VERIFIED: Architecture is LEAN-faithful and hardened.")

if __name__ == "__main__":
    asyncio.run(test_lean_invariants())