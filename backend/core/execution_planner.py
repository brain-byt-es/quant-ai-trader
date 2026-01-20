from __future__ import annotations
from typing import List, Dict, Any
from lean_bridge.contracts import PortfolioTarget
from lean_bridge.context import AlgorithmContext

class ExecutionPlanner:
    """
    LEAN-faithful Execution Model.
    Translates state-aware targets into specific orders.
    """
    def execute(self, targets: List[PortfolioTarget], context: AlgorithmContext) -> List[Dict[str, Any]]:
        """
        Compares current holdings vs target quantity and generates order instructions.
        """
        portfolio = context.portfolio_state
        positions = portfolio.get("positions", {})
        
        execution_plan = []
        
        for target in targets:
            symbol = target.symbol
            # Current position (Long - Short)
            pos = positions.get(symbol, {"long": 0, "short": 0})
            current_qty = float(pos.get("long", 0) - pos.get("short", 0))
            
            # target.quantity is now float for precision
            diff = float(target.quantity) - current_qty
            
            if diff == 0:
                continue
                
            action = "hold"
            if diff > 0:
                # If currently short, we might need to cover then buy
                action = "buy"
            elif diff < 0:
                # If currently long, we might need to sell then short
                action = "sell"
                
            execution_plan.append({
                "ticker": symbol,
                "action": action,
                "quantity": abs(diff),
                "reasoning": f"Adjusting {current_qty} -> {target.quantity} ({target.tag or 'Execution Plan'})"
            })
            
        return execution_plan
