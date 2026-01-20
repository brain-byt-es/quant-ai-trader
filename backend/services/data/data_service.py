import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Any, Dict

import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables from root .env
load_dotenv("../.env")

from data.cache import get_cache
from data.models import (
    CompanyFactsResponse,
    CompanyNews,
    CompanyNewsResponse,
    FinancialMetrics,
    FinancialMetricsResponse,
    InsiderTrade,
    InsiderTradeResponse,
    LineItem,
    LineItemResponse,
    Price,
    PriceResponse,
)


class DataService(ABC):
    """Abstract base class for financial data services."""

    @abstractmethod
    def get_prices(self, ticker: str, start_date: str, end_date: str) -> List[Price]:
        pass

    @abstractmethod
    def get_financial_metrics(self, ticker: str, end_date: str, period: str = "ttm", limit: int = 10) -> List[FinancialMetrics]:
        pass

    @abstractmethod
    def search_line_items(self, ticker: str, line_items: List[str], end_date: str, period: str = "ttm", limit: int = 10) -> List[LineItem]:
        pass

    @abstractmethod
    def get_insider_trades(self, ticker: str, end_date: str, start_date: Optional[str] = None, limit: int = 1000) -> List[InsiderTrade]:
        pass

    @abstractmethod
    def get_company_news(self, ticker: str, end_date: str, start_date: Optional[str] = None, limit: int = 1000) -> List[CompanyNews]:
        pass

    @abstractmethod
    def get_market_cap(self, ticker: str, end_date: str) -> Optional[float]:
        pass

    def prices_to_df(self, prices: List[Price]) -> pd.DataFrame:
        """Convert prices to a DataFrame."""
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


class FinancialDatasetsService(DataService):
    """Implementation of DataService using financialdatasets.ai."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
        self.cache = get_cache()
        self.base_url = "https://api.financialdatasets.ai"

    def _make_api_request(self, url: str, method: str = "GET", json_data: Optional[Dict[str, Any]] = None, max_retries: int = 3) -> requests.Response:
        headers = {}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key

        response = requests.Response()  # Initialize to avoid unbound errors
        for attempt in range(max_retries + 1):
            if method.upper() == "POST":
                response = requests.post(url, headers=headers, json=json_data)
            else:
                response = requests.get(url, headers=headers)

            if response.status_code == 429 and attempt < max_retries:
                delay = 60 + (30 * attempt)
                print(f"Rate limited (429). Attempt {attempt + 1}/{max_retries + 1}. Waiting {delay}s before retrying...")
                time.sleep(delay)
                continue

            return response
        return response

    def get_prices(self, ticker: str, start_date: str, end_date: str) -> List[Price]:
        cache_key = f"{ticker}_{start_date}_{end_date}"
        if cached_data := self.cache.get_prices(cache_key):
            return [Price(**price) for price in cached_data]

        url = f"{self.base_url}/prices/?ticker={ticker}&interval=day&interval_multiplier=1&start_date={start_date}&end_date={end_date}"
        response = self._make_api_request(url)

        if response.status_code != 200:
            return []

        try:
            price_response = PriceResponse(**response.json())
            prices = price_response.prices
            if prices:
                self.cache.set_prices(cache_key, [p.model_dump() for p in prices])
            return prices
        except Exception as e:
            print(f"Error parsing prices: {e}")
            return []

    def get_financial_metrics(self, ticker: str, end_date: str, period: str = "ttm", limit: int = 10) -> List[FinancialMetrics]:
        cache_key = f"{ticker}_{period}_{end_date}_{limit}"
        if cached_data := self.cache.get_financial_metrics(cache_key):
            return [FinancialMetrics(**metric) for metric in cached_data]

        url = f"{self.base_url}/financial-metrics/?ticker={ticker}&report_period_lte={end_date}&limit={limit}&period={period}"
        response = self._make_api_request(url)

        if response.status_code != 200:
            return []

        try:
            metrics_response = FinancialMetricsResponse(**response.json())
            metrics = metrics_response.financial_metrics
            if metrics:
                self.cache.set_financial_metrics(cache_key, [m.model_dump() for m in metrics])
            return metrics
        except Exception:
            return []

    def search_line_items(self, ticker: str, line_items: List[str], end_date: str, period: str = "ttm", limit: int = 10) -> List[LineItem]:
        url = f"{self.base_url}/financials/search/line-items"
        body = {
            "tickers": [ticker],
            "line_items": line_items,
            "end_date": end_date,
            "period": period,
            "limit": limit,
        }

        response = self._make_api_request(url, method="POST", json_data=body)

        if response.status_code != 200:
            return []

        try:
            response_model = LineItemResponse(**response.json())
            return response_model.search_results[:limit]
        except Exception:
            return []

    def get_insider_trades(self, ticker: str, end_date: str, start_date: Optional[str] = None, limit: int = 1000) -> List[InsiderTrade]:
        cache_key = f"{ticker}_{start_date or 'none'}_{end_date}_{limit}"
        if cached_data := self.cache.get_insider_trades(cache_key):
            return [InsiderTrade(**trade) for trade in cached_data]

        all_trades = []
        current_end_date = end_date

        while True:
            url = f"{self.base_url}/insider-trades/?ticker={ticker}&filing_date_lte={current_end_date}"
            if start_date:
                url += f"&filing_date_gte={start_date}"
            url += f"&limit={limit}"

            response = self._make_api_request(url)
            if response.status_code != 200:
                break

            try:
                response_model = InsiderTradeResponse(**response.json())
                trades = response_model.insider_trades
            except Exception:
                break

            if not trades:
                break

            all_trades.extend(trades)

            if not start_date or len(trades) < limit:
                break

            current_end_date = min(trade.filing_date for trade in trades).split("T")[0]
            if current_end_date <= start_date:
                break

        if all_trades:
            self.cache.set_insider_trades(cache_key, [t.model_dump() for t in all_trades])

        return all_trades

    def get_company_news(self, ticker: str, end_date: str, start_date: Optional[str] = None, limit: int = 1000) -> List[CompanyNews]:
        cache_key = f"{ticker}_{start_date or 'none'}_{end_date}_{limit}"
        if cached_data := self.cache.get_company_news(cache_key):
            return [CompanyNews(**news) for news in cached_data]

        all_news = []
        current_end_date = end_date

        while True:
            url = f"{self.base_url}/news/?ticker={ticker}&end_date={current_end_date}"
            if start_date:
                url += f"&start_date={start_date}"
            url += f"&limit={limit}"

            response = self._make_api_request(url)
            if response.status_code != 200:
                break

            try:
                response_model = CompanyNewsResponse(**response.json())
                news_items = response_model.news
            except Exception:
                break

            if not news_items:
                break

            all_news.extend(news_items)

            if not start_date or len(news_items) < limit:
                break

            current_end_date = min(n.date for n in news_items).split("T")[0]
            if current_end_date <= start_date:
                break

        if all_news:
            self.cache.set_company_news(cache_key, [n.model_dump() for n in all_news])

        return all_news

    def get_market_cap(self, ticker: str, end_date: str) -> Optional[float]:
        # If end_date is today, use company facts
        if end_date == datetime.now().strftime("%Y-%m-%d"):
            url = f"{self.base_url}/company/facts/?ticker={ticker}"
            response = self._make_api_request(url)
            if response.status_code == 200:
                try:
                    data = response.json()
                    return CompanyFactsResponse(**data).company_facts.market_cap
                except:
                    pass

        # Fallback to financial metrics
        metrics = self.get_financial_metrics(ticker, end_date, limit=1)
        if metrics:
            return metrics[0].market_cap
        return None


# Factory to get the appropriate service
def get_data_service(provider: str = "financialdatasets") -> DataService:
    if provider == "financialdatasets":
        return FinancialDatasetsService()
    else:
        raise ValueError(f"Unknown provider: {provider}")