import os
from typing import List, Any, Dict, Optional

import pandas as pd

from data.cache import get_cache
from data.models import Price
from services.data.alpha_vantage import AlphaVantageService
from services.trading.alpaca import AlpacaLiveProvider, AlpacaPaperProvider


class MarketDataClient:
    def __init__(self):
        self.av_service = AlphaVantageService()  # Primary for Fundamentals/News/Technicals
        self.cache = get_cache()
        self.alpaca = self._get_alpaca_provider()  # Primary for Prices/Execution

    def _get_alpaca_provider(self):
        api_key = os.environ.get("ALPACA_API_KEY")
        api_secret = os.environ.get("ALPACA_SECRET_KEY")
        if not api_key or not api_secret:
            return None
            
        mode = os.environ.get("TRADING_MODE", "paper").lower()
        if mode == "live":
            return AlpacaLiveProvider(api_key, api_secret)
        return AlpacaPaperProvider(api_key, api_secret)

    def get_price_data(self, ticker: str, start_date: str, end_date: str) -> List[Price]:
        # Ticker check - prevent 'GLOBAL' leaking
        if not ticker or ticker.upper() == "GLOBAL" or ticker.upper() == "SYSTEM":
            return []

        # 1. Try Alpaca (with fallback)
        prices = []
        if self.alpaca:
            try:
                # Alpaca get_bars returns list of dicts
                # We try to use IEX feed by default for broad coverage on free tier
                bar_data = self.alpaca.get_bars(ticker, start_date, end_date)
                if bar_data:
                    prices = [Price(**b) for b in bar_data]
            except Exception as e:
                print(f"Alpaca price fetch failed for {ticker}: {e}")

        # 2. Fallback to Alpha Vantage if Alpaca fails or returns no data
        if not prices:
            try:
                print(f"Falling back to Alpha Vantage for {ticker} prices...")
                prices = self.av_service.get_prices(ticker, start_date, end_date)
            except Exception as e:
                print(f"Alpha Vantage price fetch failed for {ticker}: {e}")

        return prices

    def get_financial_metrics(self, ticker: str, end_date: str, period="ttm", limit=10):
        if not ticker or ticker.upper() == "GLOBAL": return []
        return self.av_service.get_financial_metrics(ticker, end_date, period, limit)

    def get_company_news(self, ticker: str, end_date: str, limit=10):
        if not ticker or ticker.upper() == "GLOBAL": return []
        return self.av_service.get_company_news(ticker, end_date, limit=limit)

    def get_insider_trades(self, ticker: str, end_date: str, limit=10):
        if not ticker or ticker.upper() == "GLOBAL": return []
        return self.av_service.get_insider_trades(ticker, end_date, limit=limit)

    def search_line_items(self, ticker: str, line_items: list, end_date: str, period="ttm", limit=10):
        if not ticker or ticker.upper() == "GLOBAL": return []
        return self.av_service.search_line_items(ticker, line_items, end_date, period, limit)

    def get_market_cap(self, ticker: str, end_date: str):
        if not ticker or ticker.upper() == "GLOBAL": return None
        return self.av_service.get_market_cap(ticker, end_date)

    def get_account_summary(self):
        if self.alpaca:
            return self.alpaca.get_account()
        return {"error": "Alpaca not configured"}

    def prices_to_df(self, prices: List[Price]) -> pd.DataFrame:
        if not prices:
            return pd.DataFrame()
        df = pd.DataFrame([p.model_dump() for p in prices])
        df["Date"] = pd.to_datetime(df["time"])
        df.set_index("Date", inplace=True)
        numeric_cols = ["open", "close", "high", "low", "volume"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df.sort_index(inplace=True)
        return df


# Singleton instance
market_data_client = MarketDataClient()


# Backward compatibility wrappers
def get_prices(ticker, start_date, end_date, api_key=None):
    return market_data_client.get_price_data(ticker, start_date, end_date)


def get_financial_metrics(ticker, end_date, period="ttm", limit=10, api_key=None):
    return market_data_client.get_financial_metrics(ticker, end_date, period, limit)


def search_line_items(ticker, line_items, end_date, period="ttm", limit=10, api_key=None):
    return market_data_client.search_line_items(ticker, line_items, end_date, period, limit)


def get_company_news(ticker, end_date, start_date=None, limit=1000, api_key=None):
    return market_data_client.get_company_news(ticker, end_date, limit=limit)


def get_insider_trades(ticker, end_date, start_date=None, limit=1000, api_key=None):
    return market_data_client.get_insider_trades(ticker, end_date, limit=limit)


def get_market_cap(ticker, end_date, api_key=None):
    return market_data_client.get_market_cap(ticker, end_date)


def get_account_summary():
    return market_data_client.get_account_summary()


def get_price_data(ticker, start_date, end_date, api_key=None):
    prices = get_prices(ticker, start_date, end_date)
    return market_data_client.prices_to_df(prices)


def prices_to_df(prices):
    return market_data_client.prices_to_df(prices)