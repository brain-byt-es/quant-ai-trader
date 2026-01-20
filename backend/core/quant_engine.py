from typing import Any, Dict, List

import numpy as np
import pandas as pd

from tools.api import (
    get_financial_metrics,
    get_market_cap,
    get_price_data,
    search_line_items,
)
from utils.progress import progress


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs.iloc[-1]))


def calculate_beta(stock_returns: pd.Series, market_returns: pd.Series) -> float:
    # Simplified Beta calculation assuming aligned dates
    # In production, ensure dates are strictly aligned
    if len(stock_returns) < 30:
        return 1.0

    # Align
    common_idx = stock_returns.index.intersection(market_returns.index)
    if len(common_idx) < 30:
        return 1.0

    s = stock_returns.loc[common_idx]
    m = market_returns.loc[common_idx]

    covariance = np.cov(s, m)[0][1]
    variance = np.var(m)
    return covariance / variance if variance != 0 else 1.0


def calculate_max_drawdown(prices: pd.Series) -> float:
    rolling_max = prices.cummax()
    drawdown = (prices - rolling_max) / rolling_max
    return drawdown.min()


def calculate_var(returns: pd.Series, confidence_level: float = 0.05) -> float:
    if len(returns) == 0:
        return 0.0
    return np.percentile(returns, confidence_level * 100)


class QuantEngine:
    def __init__(self, tickers: List[str], start_date: str, end_date: str):
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.results = {}

    def run(self) -> Dict[str, Any]:
        """
        Main execution method.
        Calculates factors for all tickers and computes Z-scores.
        """
        raw_data = []

        # 1. Fetch Data & Calculate Raw Metrics
        for ticker in self.tickers:
            progress.update_status("quant_engine", ticker, "Calculating Factors")
            metrics = self._calculate_ticker_metrics(ticker)
            if metrics:
                metrics["ticker"] = ticker
                raw_data.append(metrics)

        if not raw_data:
            return {}

        df = pd.DataFrame(raw_data)

        # 2. Z-Score Normalization (Sector-neutral if possible, otherwise Universe-relative)
        # Using Universe-relative for this implementation
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        # Calculate Z-Scores
        z_score_df = df.copy()
        for col in numeric_cols:
            if df[col].std() != 0:
                z_score_df[f"{col}_z"] = (df[col] - df[col].mean()) / df[col].std()
            else:
                z_score_df[f"{col}_z"] = 0.0

        # 3. Structure Output
        final_scorecard = {}
        for _, row in z_score_df.iterrows():
            ticker = row["ticker"]
            final_scorecard[ticker] = {"metrics": {k: float(v) if pd.notnull(v) else None for k, v in df[df["ticker"] == ticker].iloc[0].items() if k != "ticker"}, "z_scores": {k: float(v) if pd.notnull(v) else 0.0 for k, v in row.items() if k.endswith("_z")}}

        progress.update_status("quant_engine", None, "Done")
        return final_scorecard

    def _calculate_ticker_metrics(self, ticker: str) -> Dict[str, float]:
        try:
            # Fetch Data
            progress.update_status("quant_engine", ticker, "Fetching prices")
            prices_df = get_price_data(ticker, self.start_date, self.end_date)

            progress.update_status("quant_engine", ticker, "Fetching financials")
            financials = get_financial_metrics(ticker, self.end_date, limit=1)

            progress.update_status("quant_engine", ticker, "Fetching statement line items")
            line_items = search_line_items(ticker, ["research_and_development", "revenue", "total_assets", "total_current_assets", "total_current_liabilities", "retained_earnings", "ebit", "total_liabilities"], self.end_date, limit=1)

            progress.update_status("quant_engine", ticker, "Fetching market cap")
            market_cap = get_market_cap(ticker, self.end_date)

            progress.update_status("quant_engine", ticker, "Calculating technical clusters")
            if prices_df.empty or not financials:
                return None

            latest_fin = financials[0]
            latest_line = line_items[0] if line_items else None

            # --- Momentum Cluster ---
            prices = prices_df["close"]
            returns = prices.pct_change().dropna()

            # 12m-1m Momentum (approx 252 trading days)
            mom_12m_1m = 0.0
            if len(prices) > 252:
                price_1m_ago = prices.iloc[-21]
                price_12m_ago = prices.iloc[-252]
                mom_12m_1m = (price_1m_ago / price_12m_ago) - 1

            # RSI(14)
            rsi = calculate_rsi(prices) if len(prices) > 14 else 50.0

            # Distance from 200d MA
            ma_200 = prices.rolling(window=200).mean().iloc[-1] if len(prices) >= 200 else prices.mean()
            dist_200ma = (prices.iloc[-1] / ma_200) - 1

            # --- Risk Cluster ---
            # Beta (Simplified vs 'Market' - effectively correlating with itself if single ticker,
            # ideally fetch SPY. For now, use volatility as proxy or placeholder)
            beta = 1.0  # Placeholder without SPY data
            max_dd = calculate_max_drawdown(prices)
            var_95 = calculate_var(returns)

            # --- Value Cluster ---
            pe = latest_fin.price_to_earnings_ratio or 0.0
            pb = latest_fin.price_to_book_ratio or 0.0
            ev_ebitda = latest_fin.enterprise_value_to_ebitda_ratio or 0.0
            fcf_yield = latest_fin.free_cash_flow_yield or 0.0

            # --- Quality Cluster ---
            roe = latest_fin.return_on_equity or 0.0
            roic = latest_fin.return_on_invested_capital or 0.0
            debt_equity = latest_fin.debt_to_equity or 0.0

            # Altman Z-Score (Simplified 1.2A + 1.4B + 3.3C + 0.6D + 1.0E)
            # A = Working Capital / Total Assets
            # B = Retained Earnings / Total Assets
            # C = EBIT / Total Assets
            # D = Market Value of Equity / Total Liabilities
            # E = Sales / Total Assets
            altman_z = 0.0
            if latest_line and latest_line.total_assets:
                ta = latest_line.total_assets
                wc = latest_line.total_current_assets - latest_line.total_current_liabilities
                re = latest_line.retained_earnings or 0
                ebit = latest_line.ebit or 0
                tl = latest_line.total_liabilities or 1
                rev = latest_line.revenue or 0
                mve = market_cap or 0

                a = wc / ta
                b = re / ta
                c = ebit / ta
                d_ratio = mve / tl
                e = rev / ta

                altman_z = 1.2 * a + 1.4 * b + 3.3 * c + 0.6 * d_ratio + 1.0 * e

            # --- Growth Cluster ---
            rev_growth = latest_fin.revenue_growth or 0.0  # 1y growth approx
            eps_growth = latest_fin.earnings_growth or 0.0
            rnd_sales = 0.0
            if latest_line and latest_line.revenue and latest_line.research_and_development:
                rnd_sales = latest_line.research_and_development / latest_line.revenue

            return {
                # Momentum
                "momentum_12m_1m": mom_12m_1m,
                "rsi": rsi,
                "dist_200ma": dist_200ma,
                # Risk
                "beta": beta,
                "max_drawdown": max_dd,
                "var_95": var_95,
                # Value
                "pe_ratio": pe,
                "pb_ratio": pb,
                "ev_ebitda": ev_ebitda,
                "fcf_yield": fcf_yield,
                # Quality
                "roe": roe,
                "roic": roic,
                "debt_to_equity": debt_equity,
                "altman_z": altman_z,
                # Growth
                "revenue_growth": rev_growth,
                "eps_growth": eps_growth,
                "rnd_to_sales": rnd_sales,
            }

        except Exception as e:
            print(f"Error calculating metrics for {ticker}: {e}")
            return None


from data.universe import UniverseSelectionModel
from datetime import datetime

def quant_engine_node(state: Dict[str, Any]):
    """LangGraph node for the Quant Engine. Handles dynamic Universe Selection."""
    data = state["data"]
    
    # 0. Track Previous Universe for Changes
    previous_tickers = set(data.get("tickers", []))
    
    # 1. Universe Selection
    usm = UniverseSelectionModel()
    active_symbols = usm.select_symbols(datetime.utcnow(), data)
    data["tickers"] = active_symbols # Update state with active dynamic universe
    
    # Handle Security Changes (LEAN-faithful cleanup)
    removed_tickers = list(previous_tickers - set(active_symbols))
    if removed_tickers:
        from core.portfolio_manager import MeanVarianceOptimizationPortfolioConstructionModel
        # In a real run, we'd use the persistent PCM instance from the session/context
        pcm = MeanVarianceOptimizationPortfolioConstructionModel()
        pcm.on_securities_changed(None, {"removed": removed_tickers})

    # Emit progress for universe selection if screening occurred
    if "universe_selection_result" in data:
        res = data["universe_selection_result"]
        progress.update_status(
            "system", 
            None, 
            f"Universe Selected: {res['base_count']} base -> {res['eligible_count']} eligible -> {len(active_symbols)} selected",
            analysis=json.dumps(res)
        )

    start_date = data["start_date"]
    end_date = data["end_date"]

    # 2. Factor Calculation
    engine = QuantEngine(active_symbols, start_date, end_date)
    scorecard = engine.run()

    state["data"]["quant_scorecard"] = scorecard
    return {"data": state["data"]}
