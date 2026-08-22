#!/bin/bash

# Kill any existing processes
echo "🛑 Stopping existing instances..."
pkill -f "uvicorn app.main" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 2

# Start Backend
echo "🚀 Starting Backend..."
cd apps/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for Backend to be ready
echo "⏳ Waiting for backend to start..."
while ! curl -s http://localhost:8000/health > /dev/null; do
    sleep 1
done
echo "✅ Backend is running!"

# Start Frontend
echo "🚀 Starting Frontend..."
cd frontend
bun run dev &
FRONTEND_PID=$!
cd ..

# Wait for Frontend to be ready
echo "⏳ Waiting for frontend to start..."
while ! curl -s http://localhost:5173 > /dev/null; do
    sleep 1
done
echo "✅ Frontend is running!"

# Open Browser
echo "🌐 Opening browser..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:5173
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open http://localhost:5173
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    start http://localhost:5173
fi

# Keep script running to maintain child processes
wait
