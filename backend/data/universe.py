from typing import List
from datetime import datetime

class UniverseSelectionModel:
    """
    LEAN-faithful Universe Selection Model.
    Determines which symbols exist in the dynamic universe.
    """
    def __init__(self, initial_symbols: List[str] = []):
        self._initial_symbols = initial_symbols

    def select_symbols(self, dt: datetime, data: dict) -> List[str]:
        """
        Returns the list of active symbols for the current time step.
        Supports dynamic expansion from data inputs.
        """
        # Start with static watchlist
        symbols = list(self._initial_symbols)
        
        # Merge with symbols from incoming data (e.g. dynamic API request)
        if "tickers" in data:
            for ticker in data["tickers"]:
                if ticker not in symbols:
                    symbols.append(ticker)
        
        return symbols
