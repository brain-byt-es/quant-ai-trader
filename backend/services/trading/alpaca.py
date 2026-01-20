import os
from typing import Any, Dict, List, Optional, cast

import requests

from .base import Order, OrderSide, OrderStatus, OrderType, Position, TradingProvider


class AlpacaProvider(TradingProvider):
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        
        # Use strictly what is provided in .env or the constructor
        env_base = os.environ.get("ALPACA_API_BASE_URL")
        final_base = env_base if env_base else base_url
        
        # Ensure the base URL is clean (no trailing /v2 or /)
        self.base_url = final_base.rstrip("/").replace("/v2", "")
        
        self.headers = {
            "APCA-API-KEY-ID": self.api_key, 
            "APCA-API-SECRET-KEY": self.api_secret,
            "Accept": "application/json"
        }

    def get_bars(self, ticker: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Fetch daily bars using the Alpaca Data API.
        """
        # Hardcoded to official data domain as it's standard for all Alpaca accounts
        url = "https://data.alpaca.markets/v2/stocks/bars"
        
        params = {
            "symbols": ticker, 
            "timeframe": "1Day", 
            "start": start_date, 
            "end": end_date, 
            "limit": 1000,
            "feed": "iex",
            "adjustment": "all"
        }

        print(f"Alpaca: Fetching bars for {ticker} (Feed: IEX)...")
        response = requests.get(url, headers=self.headers, params=params, timeout=10)
        
        if response.status_code == 403:
            print(f"Alpaca 403: Retrying without explicit IEX feed for {ticker}...")
            params.pop("feed", None)
            response = requests.get(url, headers=self.headers, params=params, timeout=10)

        response.raise_for_status()
        data = response.json()

        bars = data.get("bars", {}).get(ticker, [])
        prices = []
        for b in bars:
            prices.append({
                "ticker": ticker, 
                "time": b["t"], 
                "open": float(b["o"]), 
                "high": float(b["h"]), 
                "low": float(b["l"]), 
                "close": float(b["c"]), 
                "volume": int(b["v"])
            })
        return prices

    def _request(self, method: str, endpoint: str, data: Dict[str, Any] | None = None) -> Any:
        # Manually ensure v2 prefix for all trading endpoints
        path = endpoint if endpoint.startswith("v2/") else f"v2/{endpoint}"
        url = f"{self.base_url}/{path}"
        
        response = requests.request(method, url, headers=self.headers, json=data, timeout=10)
        
        if response.status_code == 204:
            return {}
            
        response.raise_for_status()
        return response.json()

    def get_account(self) -> Dict[str, Any]:
        return self._request("GET", "account")

    def get_positions(self) -> List[Position]:
        positions_data = self._request("GET", "positions")
        positions = []
        for p in positions_data:
            positions.append(Position(ticker=str(p["symbol"]), qty=float(p["qty"]), market_value=float(p["market_value"]), cost_basis=float(p["cost_basis"]), unrealized_pl=float(p["unrealized_pl"]), unrealized_plpc=float(p["unrealized_plpc"])))
        return positions

    def submit_order(self, ticker: str, qty: float, side: OrderSide, type: OrderType, limit_price: Optional[float] = None) -> Order:
        data: Dict[str, Any] = {"symbol": ticker, "qty": qty, "side": side.value, "type": type.value, "time_in_force": "day"}
        if limit_price and type == OrderType.LIMIT:
            data["limit_price"] = limit_price

        order_data = self._request("POST", "orders", data)
        return self._map_order(order_data)

    def get_order(self, order_id: str) -> Order:
        order_data = self._request("GET", f"orders/{order_id}")
        return self._map_order(order_data)

    def cancel_order(self, order_id: str):
        self._request("DELETE", f"orders/{order_id}")

    def liquidate_all_positions(self, cancel_orders: bool = True) -> List[Dict[str, Any]]:
        params = f"?cancel_orders={str(cancel_orders).lower()}"
        return self._request("DELETE", f"positions{params}")

    def _map_order(self, data: Dict[str, Any]) -> Order:
        return Order(
            id=str(data["id"]),
            client_order_id=data.get("client_order_id"),
            ticker=str(data["symbol"]),
            qty=float(data["qty"]) if data.get("qty") else 0.0,
            side=OrderSide(data["side"]),
            type=OrderType(data["type"]),
            status=OrderStatus(data["status"]) if data["status"] in [s.value for s in OrderStatus] else OrderStatus.PENDING,
            filled_avg_price=float(data["filled_avg_price"]) if data.get("filled_avg_price") else None,
            created_at=str(data["created_at"]),
        )


class AlpacaPaperProvider(AlpacaProvider):
    def __init__(self, api_key: str, api_secret: str):
        super().__init__(api_key, api_secret, "https://paper-api.alpaca.markets")


class AlpacaLiveProvider(AlpacaProvider):
    def __init__(self, api_key: str, api_secret: str):
        super().__init__(api_key, api_secret, "https://api.alpaca.markets")
