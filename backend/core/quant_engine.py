import json
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, cast

import numpy as np
import pandas as pd

from data.universe import UniverseSelectionModel
from lean_bridge.context import AlgorithmContext
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
    if rs.empty or rs.iloc[-1] == -1:
        return 50.0
    return float(100 - (100 / (1 + rs.iloc[-1])))


def calculate_beta(stock_returns: pd.Series, market_returns: pd.Series) -> float:
    if len(stock_returns) < 30:
        return 1.0
    common_idx = stock_returns.index.intersection(market_returns.index)
    if len(common_idx) < 30:
        return 1.0
    s = stock_returns.loc[common_idx]
    m = market_returns.loc[common_idx]
    covariance = np.cov(s, m)[0][1]
    variance = np.var(m)
    return float(covariance / variance) if variance != 0 else 1.0


def calculate_max_drawdown(prices: pd.Series) -> float:
    rolling_max = prices.cummax()
    drawdown = (prices - rolling_max) / rolling_max
    return float(drawdown.min())


def calculate_var(returns: pd.Series, confidence_level: float = 0.05) -> float:
    if len(returns) == 0:
        return 0.0
    return float(np.percentile(returns, confidence_level * 100))


class QuantEngine:
    def __init__(self, tickers: List[str], start_date: str, end_date: str):
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.results = {}

    def run(self) -> Dict[str, Any]:
        raw_data = []

        # 1. Fetch Data & Calculate Raw Metrics
        for ticker in self.tickers:
            progress.update_status("quant_engine", ticker, "Calculating Institutional Factors")
            metrics = self._calculate_ticker_metrics(ticker)
            if metrics:
                metrics_data: Dict[str, Any] = cast(Dict[str, Any], metrics)
                metrics_data["ticker"] = ticker
                raw_data.append(metrics_data)

        if not raw_data:
            return {}

        df = pd.DataFrame(raw_data)

        # 2. Z-Score Normalization
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        z_score_df = df.copy()
        for col in numeric_cols:
            if df[col].std() != 0:
                z_score_df[f"{col}_z"] = (df[col] - df[col].mean()) / df[col].std()
            else:
                z_score_df[f"{col}_z"] = 0.0

        # 3. Structure Output
        final_scorecard = {}
        for _, row in z_score_df.iterrows():
            ticker = str(row["ticker"])
            orig_row = df[df["ticker"] == ticker].iloc[0]
            
            metrics_dict = {str(k): float(v) if pd.notnull(v) else 0.0 for k, v in orig_row.items() if str(k) != "ticker"}
            z_scores_dict = {str(k): float(v) if pd.notnull(v) else 0.0 for k, v in row.items() if str(k).endswith("_z")}
            
            final_scorecard[ticker] = {
                "metrics": metrics_dict,
                "z_scores": z_scores_dict
            }

        progress.update_status("quant_engine", None, "Done")
        return final_scorecard

    def _calculate_ticker_metrics(self, ticker: str) -> Optional[Dict[str, float]]:
        try:
            prices_df = get_price_data(ticker, self.start_date, self.end_date)
            if prices_df.empty:
                return None

            financials = get_financial_metrics(ticker, self.end_date, limit=1)
            line_items = search_line_items(ticker, [
                "revenue", "total_assets", "total_current_assets", 
                "total_current_liabilities", "retained_earnings", "ebit", 
                "total_liabilities"
            ], self.end_date, limit=1)
            market_cap = get_market_cap(ticker, self.end_date)

            latest_fin = financials[0] if financials else None
            latest_line = line_items[0] if line_items else None

            prices = prices_df["close"]
            returns = prices.pct_change().dropna()
            
            mom_12m_1m = 0.0
            if len(prices) > 252:
                mom_12m_1m = float((prices.iloc[-21] / prices.iloc[-252]) - 1)

            rsi = calculate_rsi(prices) if len(prices) > 14 else 50.0
            ma_200 = prices.rolling(window=200).mean().iloc[-1] if len(prices) >= 200 else prices.mean()
            dist_200ma = float((prices.iloc[-1] / ma_200) - 1)

            max_dd = calculate_max_drawdown(prices)
            var_95 = calculate_var(returns)

            pe = getattr(latest_fin, "price_to_earnings_ratio", 0.0) or 0.0
            pb = getattr(latest_fin, "price_to_book_ratio", 0.0) or 0.0
            ev_ebitda = getattr(latest_fin, "enterprise_value_to_ebitda_ratio", 0.0) or 0.0
            fcf_yield = getattr(latest_fin, "free_cash_flow_yield", 0.0) or 0.0

            roe = getattr(latest_fin, "return_on_equity", 0.0) or 0.0
            roic = getattr(latest_fin, "return_on_invested_capital", 0.0) or 0.0
            debt_equity = getattr(latest_fin, "debt_to_equity", 0.0) or 0.0

            altman_z = 0.0
            if latest_line:
                ta = float(getattr(latest_line, "total_assets", 0) or 0)
                if ta > 0:
                    tca = float(getattr(latest_line, "total_current_assets", 0) or 0)
                    tcl = float(getattr(latest_line, "total_current_liabilities", 0) or 0)
                    re = float(getattr(latest_line, "retained_earnings", 0) or 0)
                    ebit = float(getattr(latest_line, "ebit", 0) or 0)
                    tl = float(getattr(latest_line, "total_liabilities", 1) or 1)
                    rev = float(getattr(latest_line, "revenue", 0) or 0)
                    mve = float(market_cap or 0)

                    a = (tca - tcl) / ta
                    b = re / ta
                    c = ebit / ta
                    d = mve / tl
                    e = rev / ta
                    altman_z = 1.2 * a + 1.4 * b + 3.3 * c + 0.6 * d + 1.0 * e

            rev_growth = getattr(latest_fin, "revenue_growth", 0.0) or 0.0
            eps_growth = getattr(latest_fin, "earnings_growth", 0.0) or 0.0

            return {
                "momentum_12m_1m": float(mom_12m_1m),
                "rsi": float(rsi),
                "dist_200ma": float(dist_200ma),
                "max_drawdown": float(max_dd),
                "var_95": float(var_95),
                "pe_ratio": float(pe),
                "pb_ratio": float(pb),
                "ev_ebitda": float(ev_ebitda),
                "fcf_yield": float(fcf_yield),
                "roe": float(roe),
                "roic": float(roic),
                "debt_to_equity": float(debt_equity),
                "altman_z": float(altman_z),
                "revenue_growth": float(rev_growth),
                "eps_growth": float(eps_growth),
            }

        except Exception as e:
            print(f"Error calculating metrics for {ticker}: {e}")
            return None


def universe_selection_node(state: Dict[str, Any]):
    """Fast node to determine active tickers."""
    data = state["data"]
    usm_data = {
        "market": data.get("market") or data.get("portfolio", {}).get("market"),
        "k": data.get("k") or data.get("portfolio", {}).get("k"),
        "tickers": data.get("tickers", [])
    }
    
    usm = UniverseSelectionModel()
    active_symbols = usm.select_symbols(datetime.now(UTC), usm_data)
    data["tickers"] = active_symbols 
    
    if "universe_selection_result" in usm_data:
        res = usm_data["universe_selection_result"]
        data["universe_selection_result"] = res
        progress.update_status(
            "system", 
            None, 
            f"Universe Selected: {res['base_count']} base -> {res['eligible_count']} eligible -> {len(active_symbols)} selected",
            analysis=json.dumps(res)
        )
    return {"data": data}


def factor_calculation_node(state: Dict[str, Any]):
    """Slow node to calculate institutional metrics (background)."""
    data = state["data"]
    active_symbols = data.get("tickers", [])
    
    if not active_symbols:
        return {"data": data}

    engine = QuantEngine(active_symbols, data["start_date"], data["end_date"])
    scorecard = engine.run()

    data["quant_scorecard"] = scorecard
    return {"data": data}
