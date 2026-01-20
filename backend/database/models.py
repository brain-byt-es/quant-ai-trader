from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .connection import Base


class HedgeFundFlow(Base):
    """Table to store React Flow configurations (nodes, edges, viewport)"""

    __tablename__ = "hedge_fund_flows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Flow metadata
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # React Flow state
    nodes: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)
    edges: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)
    viewport: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Additional metadata
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)


class HedgeFundFlowRun(Base):
    """Table to track individual execution runs of a hedge fund flow"""

    __tablename__ = "hedge_fund_flow_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    flow_id: Mapped[int] = mapped_column(Integer, ForeignKey("hedge_fund_flows.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Run execution tracking
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="IDLE")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Run configuration
    trading_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="one-time")
    schedule: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    duration: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Run data
    request_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    initial_portfolio: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    final_portfolio: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    results: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    run_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class HedgeFundFlowRunCycle(Base):
    """Individual analysis cycles within a trading session"""

    __tablename__ = "hedge_fund_flow_run_cycles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    flow_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("hedge_fund_flow_runs.id"), nullable=False, index=True)
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Analysis results
    analyst_signals: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    trading_decisions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    executed_trades: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    # Portfolio state after this cycle
    portfolio_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Performance metrics for this cycle
    performance_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Execution tracking
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="IN_PROGRESS")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cost tracking
    llm_calls_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    api_calls_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    estimated_cost: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Metadata
    trigger_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    market_conditions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)


class ApiKey(Base):
    """Table to store API keys for various services"""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # API key details
    provider: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    key_value: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Optional metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Trade(Base):
    """Table to store trade execution requests and their status (Safety Gate)"""

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Link to the flow run that generated this trade
    flow_run_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("hedge_fund_flow_runs.id"), nullable=True, index=True)

    # Trade Details
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    order_type: Mapped[str] = mapped_column(String(20), default="market")
    limit_price: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Analysis & Consensus
    risk_score: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    persona_rationale: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Safety Gate & Execution Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING_APPROVAL", index=True)

    manual_approval_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Execution Details (from Brokerage)
    brokerage_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    execution_price: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    execution_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ScreenerRun(Base):
    """Persistence for market-wide screener runs (Ranking as a contract)"""

    __tablename__ = "screener_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    market: Mapped[str] = mapped_column(String(50), nullable=False)
    k: Mapped[int] = mapped_column(Integer, nullable=False)

    base_count: Mapped[int] = mapped_column(Integer, nullable=False)
    eligible_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Store top K and full factor table
    selected_symbols: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    ranking_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Configuration used
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    weights: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)


class ProposedTrade(Base):
    """Table to store trades proposed by the Investment Committee for HITL approval."""

    __tablename__ = "proposed_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    persona_logic: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    approval_token: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    flow_run_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("hedge_fund_flow_runs.id"), nullable=True)