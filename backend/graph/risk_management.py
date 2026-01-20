from __future__ import annotations
from typing import List
from lean_bridge.contracts import PortfolioTarget
from lean_bridge.context import AlgorithmContext

class InstitutionalRiskModel:
    """
    LEAN-faithful Risk Management Model.
    Intercepts and adjusts PortfolioTargets before execution.
    """
    def __init__(self, max_concentration: float = 0.20, min_altman_z: float = 1.8):
        self.max_concentration = max_concentration
        self.min_altman_z = min_altman_z

    def adjust_targets(self, targets: List[PortfolioTarget], context: AlgorithmContext) -> List[PortfolioTarget]:
        """
        Applies mathematical gates:
        1. Altman Z-Score distress filter.
        2. Position concentration cap.
        """
        quant_scorecard = context.config.get("quant_scorecard", {})
        portfolio = context.portfolio_state
        total_equity = float(portfolio.get("equity", 100000.0))
        current_prices = context.config.get("current_prices", {})

        adjusted_targets = []
        for target in targets:
            symbol = target.symbol
            scorecard = quant_scorecard.get(symbol, {})
            metrics = scorecard.get("metrics", {})
            
            # Use original value as base for adjustment
            new_quantity = target.quantity
            
            # 1. Altman Z-Score Check (Institutional Distress Gate)
            z_score = metrics.get("altman_z", 0.0)
            if z_score < self.min_altman_z and z_score != 0:
                print(f"RISK VETO: {symbol} Altman Z-Score {z_score:.2f} < {self.min_altman_z} (Distress)")
                new_quantity = 0 
            
            # 2. Concentration Cap
            price = float(current_prices.get(symbol, 0.0))
            if price > 0:
                target_value = abs(new_quantity * price)
                if target_value > total_equity * self.max_concentration:
                    print(f"RISK LIMIT: Capping {symbol} size to {self.max_concentration:.0%} of equity")
                    new_quantity = int((total_equity * self.max_concentration * (1 if new_quantity > 0 else -1)) // price)

            # Create NEW immutable instance with adjusted quantity
            adjusted_targets.append(PortfolioTarget(
                symbol=symbol, 
                quantity=new_quantity, 
                tag=target.tag
            ))

        return adjusted_targets