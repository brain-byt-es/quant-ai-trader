from pydantic import BaseModel
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from datetime import datetime

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from datetime import datetime, UTC

class RegimeContext(BaseModel):
    """
    Institutional Regime Context.
    Outputs constraints and risk multipliers to adaptive the system behavior.
    """
    risk_multiplier: float = 1.0 # 0..1 scale
    max_position_cap: float = 0.2 # 20% default
    leverage_allowed: bool = False
    regime_type: str = "NORMAL" # NORMAL, STRESS, VOLATILE, CRASH
    market_volatility: float = 0.15 # Ann. volatility
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

def detect_regime(market_data: Optional[Dict[str, Any]] = None) -> RegimeContext:
    """
    Detects the current market regime based on volatility and other macro proxies.
    Used to shape downstream constraints in MVO and Risk Management.
    """
    # In a real implementation, we'd fetch VIX or SPY 20d Vol
    # and compare to historical percentiles.
    
    # Placeholder Logic:
    # If market_data contains 'vix', use it. Otherwise assume Normal.
    vix = 15.0
    if market_data and "vix" in market_data:
        vix = float(market_data["vix"])
    
    risk_multiplier = 1.0
    position_cap = 0.20
    regime_type = "NORMAL"
    
    if vix > 30:
        regime_type = "CRASH"
        risk_multiplier = 0.3
        position_cap = 0.05
    elif vix > 20:
        regime_type = "VOLATILE"
        risk_multiplier = 0.7
        position_cap = 0.10
        
    return RegimeContext(
        risk_multiplier=risk_multiplier,
        max_position_cap=position_cap,
        regime_type=regime_type,
        market_volatility=vix / 100.0,
        timestamp=datetime.now(UTC)
    )
