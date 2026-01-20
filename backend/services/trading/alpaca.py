import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from .base import Order, OrderSide, OrderStatus, OrderType, Position, TradingProvider


class AlpacaProvider(TradingProvider):
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.headers = {"APCA-API-KEY-ID": self.api_key, "APCA-API-SECRET-KEY": self.api_secret}

    def get_bars(self, ticker: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        # Alpaca bars endpoint
        # start/end expected as RFC3339 or YYYY-MM-DD
        params = {"symbols": ticker, "timeframe": "1Day", "start": start_date, "end": end_date, "limit": 10000}

        # Use data API URL if different? Alpaca has a separate data URL (data.alpaca.markets).
        # The base_url in provider is 'api.alpaca.markets' or 'paper-api...'.
        # Data API is usually 'https://data.alpaca.markets/v2'.
        # I should probably handle this.

        data_url = "https://data.alpaca.markets/v2"
        url = f"{data_url}/stocks/bars"

        response = requests.get(url, headers=self.headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        bars = data.get("bars", {}).get(ticker, [])
        prices = []
        for b in bars:
            # Map Alpaca bar to Price model dict structure
            # Alpaca: t, o, h, l, c, v
            prices.append({"ticker": ticker, "time": b["t"], "open": b["o"], "high": b["h"], "low": b["l"], "close": b["c"], "volume": b["v"]})
        return prices

    def _request(self, method: str, endpoint: str, data: Dict = None) -> Any:
        url = f"{self.base_url}/{endpoint}"
        response = requests.request(method, url, headers=self.headers, json=data, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_account(self) -> Dict[str, Any]:
        return self._request("GET", "v2/account")

    def get_positions(self) -> List[Position]:
        positions_data = self._request("GET", "v2/positions")
        positions = []
        for p in positions_data:
            positions.append(Position(ticker=p["symbol"], qty=float(p["qty"]), market_value=float(p["market_value"]), cost_basis=float(p["cost_basis"]), unrealized_pl=float(p["unrealized_pl"]), unrealized_plpc=float(p["unrealized_plpc"])))
        return positions

    def submit_order(self, ticker: str, qty: float, side: OrderSide, type: OrderType, limit_price: Optional[float] = None) -> Order:
        data = {"symbol": ticker, "qty": qty, "side": side.value, "type": type.value, "time_in_force": "day"}
        if limit_price and type == OrderType.LIMIT:
            data["limit_price"] = limit_price

        order_data = self._request("POST", "v2/orders", data)
        return self._map_order(order_data)

    def get_order(self, order_id: str) -> Order:
        order_data = self._request("GET", f"v2/orders/{order_id}")
        return self._map_order(order_data)

    def cancel_order(self, order_id: str):
        self._request("DELETE", f"v2/orders/{order_id}")

    def _map_order(self, data: Dict) -> Order:
        return Order(
            id=data["id"],
            client_order_id=data.get("client_order_id"),
            ticker=data["symbol"],
            qty=float(data["qty"]) if data.get("qty") else 0.0,
            side=OrderSide(data["side"]),
            type=OrderType(data["type"]),
            status=OrderStatus(data["status"]) if data["status"] in [s.value for s in OrderStatus] else OrderStatus.PENDING,  # Map unknown to pending or specific mapping needed
            filled_avg_price=float(data["filled_avg_price"]) if data.get("filled_avg_price") else None,
            created_at=data["created_at"],
        )


class AlpacaPaperProvider(AlpacaProvider):
    def __init__(self, api_key: str, api_secret: str):
        super().__init__(api_key, api_secret, "https://paper-api.alpaca.markets")


class AlpacaLiveProvider(AlpacaProvider):
    def __init__(self, api_key: str, api_secret: str):
        super().__init__(api_key, api_secret, "https://api.alpaca.markets")
