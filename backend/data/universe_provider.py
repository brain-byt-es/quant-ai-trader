import csv
import os
from pathlib import Path
from typing import List

def get_base_universe(market: str = "US") -> List[str]:
    """
    Returns the base universe symbols for a given market.
    Currently supports 'US' with a static CSV.
    """
    if market.upper() != "US":
        return []
    
    csv_path = Path(__file__).parent / "universes" / "us_equities.csv"
    if not csv_path.exists():
        # Fallback if file doesn't exist
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD", "NFLX", "PLTR"]
    
    symbols = []
    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                symbols.append(row[0])
    
    return symbols
