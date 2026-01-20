# 📈 QuantTrader (Institutional Refactor)

<div align="center">

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0-009688.svg)

**A professional systematic equity platform with a market-wide multi-factor screener, LEAN-faithful pipeline integration, and an institutionally-stable codebase.**

[Features](#-key-features) • [Architecture](#-architecture) • [Getting Started](#-getting-started) • [Development](#-development)

</div>

---

## 📖 Overview

**QuantTrader** is an autonomous, multi-agent AI hedge fund trading system. Unlike traditional "wrapper" projects, QuantTrader implements strict **LEAN Algorithm Framework** semantics (Insight → PortfolioTarget → Risk → Execution) within a modern FastAPI/Next.js stack.

This repository represents the **Institutional Refactor** phase, where the codebase was hardened for production-grade stability, modern SQLAlchemy 2.0 typing, and resilient LLM adapter patterns.

## 🌟 Key Features

### 🤖 Multi-Agent Systematic Logic
- **Discovery (Screener):** Market-wide vectorized factor ranking (A: Mispricing, B: Momentum, C: Risk).
- **Depth (Agents):** 19 specialized agents (Buffett, Munger, Burry, etc.) providing Bayesian prior updates.
- **Allocation (MVO):** Institutional Mean-Variance Optimization for target weight generation.
- **Risk (Institutional):** Regime-aware adaptive risk multipliers and "Kill Switch" safety protocols.

### 🧠 Hardened AI Orchestration
- **Safe LLM Factory:** Runtime signature introspection to prevent library version drift crashes.
- **Vectorized Screening:** Scalable multi-factor ranking computed using Pandas/NumPy.
- **Type-Safe Pipeline:** Strict Pydantic V2 models ensuring contract integrity across the Alpha, Portfolio, and Risk layers.

### 📊 Modern Tech Stack
- **Backend:** Python 3.13, FastAPI, SQLAlchemy 2.0 (Mapped/mapped_column), Alembic.
- **Frontend:** Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui.
- **Standards:** Ruff for high-performance linting, Mypy for static type verification.

## 🏗 Architecture

The project is a flattened monolith optimized for developer velocity and static analysis:

```text
/
├── backend/            # FastAPI Application
│   ├── agents/         # 19 specialized investment personas
│   ├── core/           # Quant Engine & Regime Detection
│   ├── screener/       # Vectorized ranking & factor analysis
│   ├── lean_bridge/    # QuantConnect LEAN compatibility layer
│   ├── database/       # SQLAlchemy 2.0 Models
│   └── ...
├── frontend/           # Next.js 15 Dashboard
└── GEMINI.md           # Documentation of the Institutional Refactor
```

## 🚀 Getting Started

### Prerequisites
- **Python 3.13+**
- **Node.js 20+**
- **Poetry**

### 1. Installation
```bash
# Backend
cd backend && poetry install

# Frontend
cd ../frontend && npm install
```

### 2. Environment Setup
```bash
cp .env.example .env
# Fill in credentials for Alpaca, Financial Datasets, and LLM Providers
```

### 3. Execution
```bash
# Backend
poetry run uvicorn main:app --reload

# Frontend
npm run dev
```

## 🛡 Institutional Guardrails

- **Finite-Math Guards:** All vectorized operations are checked for NaN/Inf pollution before ranking.
- **Signature Introspection:** LLM constructors are validated at runtime to ensure forward compatibility with vendor updates.
- **Shadowing Protection:** Strict ruff rules prevent shadowing of Python built-ins.

---
<div align="center">
Built for professional systematic equity research.
</div>
