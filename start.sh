#!/bin/bash

# --- AI HEDGE FUND LAUNCH SCRIPT ---

echo "🚀 Initializing QuantTrader Monorepo..."

# Function to kill processes on exit
cleanup() {
  echo "🛑 Shutting down..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  exit
}

trap cleanup SIGINT

# 1. Start Backend
echo "📈 Starting FastAPI Backend on port 8000..."
cd backend
# Using full path to poetry if needed, otherwise 'poetry'
if command -v poetry &> /dev/null; then
    POETRY_CMD="poetry"
else
    POETRY_CMD="/Users/henrik/Library/Python/3.9/bin/poetry"
fi
$POETRY_CMD run uvicorn main:app --reload --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "   PID: $BACKEND_PID"
cd ..

# 2. Start Frontend
echo "💻 Starting Next.js Frontend on port 3000..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   PID: $FRONTEND_PID"
cd ..

echo "✅ System Online!"
echo "   Backend Health: http://localhost:8000/health"
echo "   Frontend Dashboard: http://localhost:3000"
echo ""
echo "📝 Logs are being written to backend.log and frontend.log"
echo "   Press CTRL+C to stop both servers."

wait
