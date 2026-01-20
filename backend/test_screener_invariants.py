import pytest
import pandas as pd
import numpy as np
from screener.engine import run_screener
from screener.eligibility import filter_eligible, EligibilityConfig
from screener.ranker import rank_cross_section, compute_composite_score
from data.universe_provider import get_base_universe
from data.market_data import get_snapshot, get_history

def test_base_universe_loading():
    symbols = get_base_universe("US")
    assert len(symbols) >= 1000
    assert "AAPL" in symbols

def test_eligibility_filter():
    symbols = ["HIGH", "LOW", "ILLIQUID"]
    snapshot_df = pd.DataFrame({
        "price": [10.0, 2.0, 100.0],
        "avg_dollar_volume": [10e6, 10e6, 1e6]
    }, index=symbols)
    
    config = EligibilityConfig(min_price=5.0, min_adv=5e6)
    eligible = filter_eligible(symbols, snapshot_df, config)
    
    assert "HIGH" in eligible
    assert "LOW" not in eligible
    assert "ILLIQUID" not in eligible

def test_ranking_determinism():
    symbols = ["A", "B", "C"]
    factor_df = pd.DataFrame({
        "momentum_12_1": [0.1, 0.2, 0.3],
        "volatility_20d": [0.15, 0.15, 0.15]
    }, index=symbols)
    
    weights = {"momentum_12_1": 1.0, "volatility_20d": 0.0}
    
    # Run twice
    res1 = run_screener(k=2, weights=weights)
    res2 = run_screener(k=2, weights=weights)
    
    assert res1.top_k_symbols == res2.top_k_symbols
    assert len(res1.top_k_symbols) == 2

def test_factor_directionality():
    # Volatility should be lower is better (ranked higher)
    symbols = ["STABLE", "VOLATILE"]
    factor_df = pd.DataFrame({
        "volatility_20d": [0.1, 0.5]
    }, index=symbols)
    
    ranked_df = rank_cross_section(factor_df)
    weights = {"volatility_20d": 1.0}
    
    composite = compute_composite_score(ranked_df, weights)
    
    # STABLE should have higher composite score because lower vol is better
    assert composite["STABLE"] > composite["VOLATILE"]

def test_screener_persistence():
    from database.connection import SessionLocal, engine
    from database.models import ScreenerRun, Base
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Run screener
    res = run_screener(k=5)
    
    # Check DB
    session = SessionLocal()
    last_run = session.query(ScreenerRun).order_by(ScreenerRun.created_at.desc()).first()
    
    assert last_run is not None
    assert last_run.base_count >= 1000
    assert len(last_run.selected_symbols) <= 5
    session.close()

def test_regime_detection():
    from core.regime import detect_regime
    
    # Normal
    normal = detect_regime({"vix": 15.0})
    assert normal.regime_type == "NORMAL"
    assert normal.risk_multiplier == 1.0
    
    # Stress
    stress = detect_regime({"vix": 25.0})
    assert stress.regime_type == "VOLATILE"
    assert stress.risk_multiplier == 0.7
    
    # Crash
    crash = detect_regime({"vix": 40.0})
    assert crash.regime_type == "CRASH"
    assert crash.risk_multiplier == 0.3

def test_execution_shrinkage():
    from core.execution_planner import ExecutionPlanner
    from lean_bridge.contracts import PortfolioTarget
    from lean_bridge.context import AlgorithmContext
    from datetime import datetime, UTC
    
    planner = ExecutionPlanner(min_trade_value=1000.0)
    context = AlgorithmContext(
        time=datetime.now(UTC),
        universe=["AAPL"],
        portfolio_state={"positions": {}},
        config={"current_prices": {"AAPL": 150.0}}
    )
    
    # Move too small ($150 trade value)
    small_target = [PortfolioTarget(symbol="AAPL", quantity=1.0)]
    plan = planner.execute(small_target, context)
    assert len(plan) == 0
    
    # Move large enough ($1500 trade value)
    large_target = [PortfolioTarget(symbol="AAPL", quantity=10.0)]
    plan = planner.execute(large_target, context)
    assert len(plan) == 1
    assert plan[0]["ticker"] == "AAPL"
