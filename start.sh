#!/bin/bash

echo "================================================================"
echo "🚀 STARTING QUANTTRADER FULLSTACK (Institutional Build)"
echo "================================================================"

# Function to kill child processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down QuantTrader..."
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# 1. Clean up ghost processes
# Backend Port
BPID=$(lsof -t -i :8000)
if [ ! -z "$BPID" ]; then
    echo "⚠️  Port 8000 is occupied. Terminating PID: $BPID..."
    kill -9 $BPID
    sleep 1
fi

# Frontend Port
FPID=$(lsof -t -i :3000)
if [ ! -z "$FPID" ]; then
    echo "⚠️  Port 3000 is occupied. Terminating PID: $FPID..."
    kill -9 $FPID
    sleep 1
fi

echo "✅ Ports 8000 and 3000 are clear."

# 2. Launch Backend
echo "📡 Launching Backend (FastAPI) on http://localhost:8000..."
export PYTHONPATH=$PYTHONPATH:.
cd backend
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# 3. Launch Frontend
echo "💻 Launching Frontend (Next.js) on http://localhost:3000..."
echo "----------------------------------------------------------------"
cd frontend
npm run dev