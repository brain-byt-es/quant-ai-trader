# 📈 AI Hedge Fund

<div align="center">

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0-009688.svg)

**An autonomous, multi-agent AI hedge fund trading system. Implements LEAN Algorithm Framework semantics (Insight → PortfolioTarget → Risk → Execution) in a custom FastAPI runtime.**

[Features](#-key-features) • [Architecture](#-architecture) • [Getting Started](#-getting-started) • [Usage](#-usage) • [Contributing](#-contributing)

</div>

---

## 📖 Overview

**AI Hedge Fund** is a research project exploring the capabilities of autonomous AI agents in financial markets. It simulates a hedge fund where multiple specialized AI agents—modeled after famous investors like Warren Buffett, Charlie Munger, and Michael Burry—collaborate to analyze market data, assess risk, and make trading decisions.

The system uses a **FastAPI** backend to orchestrate the agent workflow and a **Next.js** frontend to visualize the portfolio, agent interactions, and trading performance.

> ⚠️ **Disclaimer:** This project is for **educational and research purposes only**. It is not intended for real trading or financial advice.

## 🌟 Key Features

### 🤖 Multi-Agent System
A collaborative network of specialized agents:
- **Portfolio Managers**: Buffet, Munger, Ackman, Wood, etc.
- **Analysts**: Fundamental, Technical, Sentiment, Valuation, Growth.
- **Risk Manager**: Evaluates portfolio exposure and approves trades.
- **Chief Investment Officer**: Orchestrates the overall strategy.

### 🧠 Advanced AI Logic
- Powered by **LangChain** and **LangGraph**.
- Supports multiple LLM providers: OpenAI, Anthropic, DeepSeek, Groq, Google Gemini, and more.
- Retrieval Augmented Generation (RAG) for financial data analysis.

### 📊 Modern Tech Stack
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Alembic.
- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui.
- **Data**: Integration with Financial Datasets AI, Yahoo Finance (via libraries).
- **Trading**: Alpaca API integration (Paper/Live).

## 🏗 Architecture

The project is structured as a monorepo:

```text
/
├── backend/            # FastAPI Application (Agents, API, Logic)
│   ├── agents/         # AI Agent definitions (Buffett, Lynch, etc.)
│   ├── api/            # REST API Endpoints
│   ├── core/           # Workflow & Engine logic
│   ├── services/       # External services (Alpaca, Data Providers)
│   └── ...
├── frontend/           # Next.js Application (UI/UX)
│   ├── src/app/        # App Router Pages
│   ├── src/components/ # UI Components (shadcn/ui)
│   └── ...
└── .env                # Centralized Environment Variables
```

## 🚀 Getting Started

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** & npm/yarn/pnpm
- **Poetry** (for Python dependency management)

### 1. Clone the Repository
```bash
git clone https://github.com/virattt/ai-hedge-fund.git
cd ai-hedge-fund
```

### 2. Configure Environment
Create a `.env` file in the root directory and add your API keys.
```bash
cp backend/.env.example .env
```
*Make sure to fill in your keys for OpenAI, Anthropic, Financial Datasets, etc.*

### 3. Backend Setup
```bash
cd backend
poetry install
```

### 4. Frontend Setup
```bash
cd ../frontend
npm install
```

## 🖥 Usage

Run the backend and frontend in separate terminal windows.

### Start Backend
```bash
# From /backend directory
poetry run uvicorn backend.main:app --reload
```
*API will be available at [http://localhost:8000](http://localhost:8000)*  
*Docs at [http://localhost:8000/docs](http://localhost:8000/docs)*

### Start Frontend
```bash
# From /frontend directory
npm run dev
```
*UI will be available at [http://localhost:3000](http://localhost:3000)*

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---
<div align="center">
Built with ❤️ by open-source contributors.
</div>