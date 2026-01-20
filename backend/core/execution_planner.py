from __future__ import annotations
from typing import List, Dict, Any
from lean_bridge.contracts import PortfolioTarget
from lean_bridge.context import AlgorithmContext

class ExecutionPlanner:
    """
    LEAN-faithful Execution Model.
    Translates state-aware targets into specific orders with cost awareness.
    """
    def __init__(self, min_trade_value: float = 500.0, slippage_pct: float = 0.0005):
        self.min_trade_value = min_trade_value
        self.slippage_pct = slippage_pct

    def execute(self, targets: List[PortfolioTarget], context: AlgorithmContext) -> List[Dict[str, Any]]:
        """
        Compares current holdings vs target quantity and generates order instructions.
        Applies trade shrinkage for deltas below the cost threshold.
        """
        portfolio = context.portfolio_state
        positions = portfolio.get("positions", {})
        current_prices = context.config.get("current_prices", {})
        
        execution_plan = []
        
        for target in targets:
            symbol = target.symbol
            price = float(current_prices.get(symbol, 0.0))
            if price <= 0: continue

            # Current position (Long - Short)
            pos = positions.get(symbol, {"long": 0, "short": 0})
            current_qty = float(pos.get("long", 0) - pos.get("short", 0))
            
            diff = float(target.quantity) - current_qty
            trade_value = abs(diff * price)

            # Transaction Cost Awareness (Move 3)
            if trade_value < self.min_trade_value:
                # print(f"Execution: Skipping {symbol} due to low trade value (${trade_value:.2f})")
                continue
                
            action = "hold"
            if diff > 0:
                action = "buy"
            elif diff < 0:
                action = "sell"
                
            execution_plan.append({
                "ticker": symbol,
                "action": action,
                "quantity": abs(diff),
                "trade_value": trade_value,
                "cost_estimate": trade_value * self.slippage_pct,
                "reasoning": f"Adjusting {current_qty} -> {target.quantity} (${trade_value:.2f} move)"
            })
            
        return execution_plan
