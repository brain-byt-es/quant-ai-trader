import os
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import requests

from data.cache import get_cache
from data.models import (
    CompanyFactsResponse,
    CompanyNews,
    FinancialMetrics,
    InsiderTrade,
    LineItem,
    Price,
)
from services.data.data_service import DataService


class AlphaVantageService(DataService):
    """Implementation of DataService using Alpha Vantage."""

    # Class-level lock to ensure only one thread hits the API at a time
    _api_lock = threading.Lock()
    # Track the last time we made an API call
    _last_call_time = 0.0

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ALPHA_VANTAGE_API_KEY")
        self.base_url = "https://www.alphavantage.co/query"
        self.cache = get_cache()

    def _make_request(self, function: str, symbol: str = None, max_retries: int = 3, **kwargs) -> Dict:
        params = {"function": function, "apikey": self.api_key, **kwargs}
        if symbol:
            params["symbol"] = symbol

        with self._api_lock:
            for attempt in range(max_retries):
                # Ensure at least 12 seconds between calls (5 calls per minute)
                now = time.time()
                elapsed = now - AlphaVantageService._last_call_time
                if elapsed < 12.0:
                    wait_time = 12.0 - elapsed
                    print(f"Alpha Vantage: Throttling request for {function} ({symbol}). Waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)

                try:
                    response = requests.get(self.base_url, params=params, timeout=10)
                    AlphaVantageService._last_call_time = time.time()
                    response.raise_for_status()
                    data = response.json()

                    if "Error Message" in data:
                        print(f"Alpha Vantage Error: {data['Error Message']}")
                        return {}

                    if "Note" in data:  # Rate limit hit
                        print(f"Alpha Vantage Rate Limit: {data['Note']}")
                        if attempt < max_retries - 1:
                            # Sleep much longer if we hit rate limit despite throttling
                            time.sleep(20 * (attempt + 1))
                            continue
                        return {}

                    return data
                except Exception as e:
                    print(f"Alpha Vantage Request Error (Attempt {attempt+1}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(5 * (attempt + 1))
                        continue
                    return {}
        return {}

    def get_prices(self, ticker: str, start_date: str, end_date: str) -> List[Price]:
        """Fetch historical daily adjusted prices from Alpha Vantage."""
        cache_key = f"{ticker}_{start_date}_{end_date}"
        if cached_data := self.cache.get_prices(cache_key):
            return [Price(**price) for price in cached_data]

        data = self._make_request("TIME_SERIES_DAILY_ADJUSTED", symbol=ticker, outputsize="full")

        time_series = data.get("Time Series (Daily)", {})
        prices = []

        for date_str, values in time_series.items():
            # Filter by date range
            if start_date <= date_str <= end_date:
                try:
                    prices.append(Price(time=date_str, open=float(values["1. open"]), high=float(values["2. high"]), low=float(values["3. low"]), close=float(values["4. close"]), volume=int(values["6. volume"])))
                except (ValueError, KeyError) as e:
                    print(f"Error parsing price for {date_str}: {e}")
                    continue

        # Sort by date ascending
        prices.sort(key=lambda x: x.time)

        if prices:
            self.cache.set_prices(cache_key, [p.model_dump() for p in prices])

        return prices

    def get_financial_metrics(self, ticker: str, end_date: str, period: str = "ttm", limit: int = 10) -> List[FinancialMetrics]:
        cache_key = f"{ticker}_{period}_{end_date}_{limit}"
        if cached_data := self.cache.get_financial_metrics(cache_key):
            return [FinancialMetrics(**metric) for metric in cached_data]

        # If limit is 1, OVERVIEW is enough and faster
        if limit == 1:
            data = self._make_request("OVERVIEW", symbol=ticker)
            if not data:
                return []
            try:
                metric = self._map_overview_to_metric(ticker, end_date, period, data)
                self.cache.set_financial_metrics(cache_key, [metric.model_dump()])
                return [metric]
            except Exception as e:
                print(f"Error mapping AV overview: {e}")
                return []

        # For historical metrics, we need to merge statements
        line_items = self.search_line_items(ticker, [], end_date, period, limit)
        if not line_items:
            # Fallback to overview if statements fail
            return self.get_financial_metrics(ticker, end_date, period, 1)

        metrics = []
        for li in line_items:
            try:
                # Calculate basic ratios from line items
                pe = 0.0
                if hasattr(li, "net_income") and li.net_income and li.net_income > 0:
                    # We'd need price at that time for historical PE,
                    # but we'll use 0 or latest if not available easily here.
                    pass

                metric = FinancialMetrics(
                    ticker=ticker,
                    report_period=li.report_period,
                    period=period,
                    currency=li.currency,
                    market_cap=0.0,  # Historical market cap is hard without historical prices
                    revenue_growth=0.0,  # Needs calculation between periods
                    earnings_growth=0.0,
                    # Map what we have
                    return_on_equity=li.net_income / li.shareholders_equity if li.shareholders_equity else 0.0,
                    net_margin=li.net_income / li.revenue if li.revenue else 0.0,
                    operating_margin=li.ebit / li.revenue if li.revenue else 0.0,
                    debt_to_equity=(li.long_term_debt + li.short_term_debt) / li.shareholders_equity if li.shareholders_equity else 0.0,
                    current_ratio=li.total_current_assets / li.total_current_liabilities if li.total_current_liabilities else 0.0,
                    earnings_per_share=li.net_income / li.outstanding_shares if li.outstanding_shares else 0.0,
                    free_cash_flow_per_share=li.free_cash_flow / li.outstanding_shares if li.outstanding_shares else 0.0,
                    # Add defaults for missing fields
                    enterprise_value=0.0,
                    price_to_earnings_ratio=0.0,
                    price_to_book_ratio=0.0,
                    price_to_sales_ratio=0.0,
                    enterprise_value_to_ebitda_ratio=0.0,
                    enterprise_value_to_revenue_ratio=0.0,
                    free_cash_flow_yield=0.0,
                    peg_ratio=0.0,
                    gross_margin=0.0,
                    return_on_assets=li.net_income / li.total_assets if li.total_assets else 0.0,
                    return_on_invested_capital=li.ebit / (li.shareholders_equity + li.long_term_debt) if (li.shareholders_equity + li.long_term_debt) else 0.0,
                    asset_turnover=li.revenue / li.total_assets if li.total_assets else 0.0,
                    inventory_turnover=0.0,
                    receivables_turnover=0.0,
                    days_sales_outstanding=0.0,
                    operating_cycle=0.0,
                    working_capital_turnover=0.0,
                    quick_ratio=0.0,
                    cash_ratio=0.0,
                    operating_cash_flow_ratio=0.0,
                    debt_to_assets=li.total_liabilities / li.total_assets if li.total_assets else 0.0,
                    interest_coverage=li.ebit / abs(li.interest_expense) if li.interest_expense else 0.0,
                    book_value_growth=0.0,
                    earnings_per_share_growth=0.0,
                    free_cash_flow_growth=0.0,
                    operating_income_growth=0.0,
                    ebitda_growth=0.0,
                    payout_ratio=0.0,
                    book_value_per_share=li.shareholders_equity / li.outstanding_shares if li.outstanding_shares else 0.0,
                )
                metrics.append(metric)
            except Exception as e:
                print(f"Error creating FinancialMetric from LineItem: {e}")
                continue

        # Add historical growth calculations if we have multiple periods
        for i in range(len(metrics) - 1):
            curr = metrics[i]
            prev = metrics[i + 1]
            if prev.earnings_per_share and prev.earnings_per_share > 0:
                curr.earnings_per_share_growth = (curr.earnings_per_share / prev.earnings_per_share) - 1
            # Add other growth metrics...

        if metrics:
            self.cache.set_financial_metrics(cache_key, [m.model_dump() for m in metrics])

        return metrics

    def _map_overview_to_metric(self, ticker: str, end_date: str, period: str, data: Dict) -> FinancialMetrics:
        return FinancialMetrics(
            ticker=ticker,
            report_period=end_date,
            period=period,
            currency=data.get("Currency", "USD"),
            market_cap=float(data.get("MarketCapitalization", 0) or 0),
            price_to_earnings_ratio=float(data.get("PERatio", 0) or 0),
            price_to_book_ratio=float(data.get("PriceToBookRatio", 0) or 0),
            price_to_sales_ratio=float(data.get("PriceToSalesRatioTTM", 0) or 0),
            enterprise_value_to_ebitda_ratio=float(data.get("EVToEBITDA", 0) or 0),
            enterprise_value_to_revenue_ratio=float(data.get("EVToRevenue", 0) or 0),
            peg_ratio=float(data.get("PEGRatio", 0) or 0),
            gross_margin=float(data.get("GrossProfitTTM", 0) or 0) / float(data.get("RevenueTTM", 1) or 1),
            operating_margin=float(data.get("OperatingMarginTTM", 0) or 0),
            net_margin=float(data.get("ProfitMargin", 0) or 0),
            return_on_equity=float(data.get("ReturnOnEquityTTM", 0) or 0),
            return_on_assets=float(data.get("ReturnOnAssetsTTM", 0) or 0),
            debt_to_equity=float(data.get("DebtToEquityTTM", 0) or 0) if "DebtToEquityTTM" in data else 0.0,
            book_value_per_share=float(data.get("BookValue", 0) or 0),
            earnings_per_share=float(data.get("EPS", 0) or 0),
            # Missing fields or fields requiring other data
            enterprise_value=0.0,
            free_cash_flow_yield=0.0,
            return_on_invested_capital=0.0,
            current_ratio=0.0,
            quick_ratio=0.0,
            inventory_turnover=0.0,
            receivables_turnover=0.0,
            days_sales_outstanding=0.0,
            operating_cycle=0.0,
            working_capital_turnover=0.0,
            cash_ratio=0.0,
            operating_cash_flow_ratio=0.0,
            debt_to_assets=0.0,
            interest_coverage=0.0,
            revenue_growth=float(data.get("QuarterlyRevenueGrowthYOY", 0) or 0),
            earnings_growth=float(data.get("QuarterlyEarningsGrowthYOY", 0) or 0),
            book_value_growth=0.0,
            earnings_per_share_growth=0.0,
            free_cash_flow_growth=0.0,
            operating_income_growth=0.0,
            ebitda_growth=0.0,
            payout_ratio=0.0,
            free_cash_flow_per_share=0.0,
        )

    def search_line_items(self, ticker: str, line_items: List[str], end_date: str, period: str = "ttm", limit: int = 10) -> List[LineItem]:
        cache_key = f"line_{ticker}_{period}_{end_date}_{limit}"
        if cached_data := self.cache.get_line_items(cache_key):
            return [LineItem(**item) for item in cached_data]

        # Fetch Income Statement, Balance Sheet, Cash Flow
        # Using annual by default or quarterly if period != annual
        # AV returns 'annualReports' and 'quarterlyReports'

        income = self._make_request("INCOME_STATEMENT", symbol=ticker)
        balance = self._make_request("BALANCE_SHEET", symbol=ticker)
        cash = self._make_request("CASH_FLOW", symbol=ticker)

        report_key = "annualReports" if period == "annual" else "quarterlyReports"

        # Merge data by date
        # This is a bit complex to implement perfectly in one go, simplifying:
        # We will just take the latest N reports from INCOME_STATEMENT as the base

        reports = []
        if income and report_key in income:
            inc_reports = income[report_key][:limit]
            for inc in inc_reports:
                date = inc.get("fiscalDateEnding")

                # Find matching BS and CF
                bs = next((x for x in balance.get(report_key, []) if x.get("fiscalDateEnding") == date), {}) if balance else {}
                cf = next((x for x in cash.get(report_key, []) if x.get("fiscalDateEnding") == date), {}) if cash else {}

                # Construct LineItem
                try:
                    item = LineItem(
                        ticker=ticker,
                        report_period=date,
                        period=period,
                        currency=inc.get("reportedCurrency", "USD"),
                        # Map common fields requested by QuantEngine
                        revenue=float(inc.get("totalRevenue", 0) or 0),
                        net_income=float(inc.get("netIncome", 0) or 0),
                        depreciation_and_amortization=float(inc.get("depreciationAndAmortization", 0) or 0) or float(cf.get("depreciation", 0) or 0),
                        capital_expenditure=float(cf.get("capitalExpenditures", 0) or 0),
                        research_and_development=float(inc.get("researchAndDevelopment", 0) or 0),
                        total_assets=float(bs.get("totalAssets", 0) or 0),
                        total_liabilities=float(bs.get("totalLiabilities", 0) or 0),
                        total_current_assets=float(bs.get("totalCurrentAssets", 0) or 0),
                        total_current_liabilities=float(bs.get("totalCurrentLiabilities", 0) or 0),
                        shareholders_equity=float(bs.get("totalShareholderEquity", 0) or 0),
                        long_term_debt=float(bs.get("longTermDebt", 0) or 0),
                        short_term_debt=float(bs.get("shortTermDebt", 0) or 0),
                        interest_expense=float(inc.get("interestExpense", 0) or 0),
                        ebitda=float(inc.get("ebitda", 0) or 0),
                        ebit=float(inc.get("ebit", 0) or 0),
                        outstanding_shares=float(bs.get("commonStockSharesOutstanding", 0) or 0),  # Often not in BS history accurately but latest is in OVERVIEW
                    )
                    reports.append(item)
                except Exception as e:
                    print(f"Error parsing line item for {date}: {e}")
                    continue

        if reports:
            self.cache.set_line_items(cache_key, [r.model_dump() for r in reports])

        return reports

    def get_insider_trades(self, ticker: str, end_date: str, start_date: Optional[str] = None, limit: int = 1000) -> List[InsiderTrade]:
        # Alpha Vantage doesn't have a direct Insider Trade endpoint in the free tier standard list usually,
        # checking docs... INSIDER_TRANSACTIONS function exists but might be premium.
        # For now return empty or implement if needed.
        return []

    def get_company_news(self, ticker: str, end_date: str, start_date: Optional[str] = None, limit: int = 1000) -> List[CompanyNews]:
        cache_key = f"news_{ticker}_{start_date}_{end_date}_{limit}"
        if cached_data := self.cache.get_company_news(cache_key):
            return [CompanyNews(**news) for news in cached_data]

        # NEWS_SENTIMENT endpoint
        data = self._make_request("NEWS_SENTIMENT", tickers=ticker, limit=limit)
        news_list = []
        if "feed" in data:
            for item in data["feed"]:
                try:
                    # Parse date string "20230101T123000"
                    date_str = item.get("time_published", "")
                    dt = datetime.strptime(date_str, "%Y%m%dT%H%M%S")

                    news = CompanyNews(ticker=ticker, title=item.get("title", ""), date=dt.isoformat(), source=item.get("source", ""), url=item.get("url", ""), summary=item.get("summary", ""), sentiment=item.get("overall_sentiment_label", "neutral"), sentiment_score=float(item.get("overall_sentiment_score", 0)))
                    news_list.append(news)
                except Exception:
                    continue

        if news_list:
            self.cache.set_company_news(cache_key, [n.model_dump() for n in news_list])

        return news_list

    def get_market_cap(self, ticker: str, end_date: str) -> Optional[float]:
        """Get market capitalization, checking cache first."""
        # Try to find in metrics cache first (limit=1 call uses OVERVIEW)
        cache_key = f"{ticker}_ttm_{end_date}_1"
        if cached_data := self.cache.get_financial_metrics(cache_key):
            if isinstance(cached_data[0], dict):
                return cached_data[0].get("market_cap")
            elif hasattr(cached_data[0], "market_cap"):
                return cached_data[0].market_cap

        data = self._make_request("OVERVIEW", symbol=ticker)
        mcap = float(data.get("MarketCapitalization", 0) or 0)

        # If we fetched it, we might as well cache the whole overview as a metric
        try:
            metric = self._map_overview_to_metric(ticker, end_date, "ttm", data)
            self.cache.set_financial_metrics(cache_key, [metric.model_dump()])
        except:
            pass

        return mcap
