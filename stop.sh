#!/bin/bash
# Stop script for Mission Planning Assistant
# Terminates backend (port 8000) and frontend (port 5173) processes and frees ports.

echo "🛑 Stopping Mission Planning Assistant services..."

# Kill processes listening on ports 8000 and 5173
if command -v fuser >/dev/null 2>&1; then
  fuser -k 8000/tcp 2>/dev/null || true
  fuser -k 5173/tcp 2>/dev/null || true
fi

# Terminate application processes by pattern
pkill -f "app.main" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "bun run preview" 2>/dev/null || true
pkill -f "npm run preview" 2>/dev/null || true

sleep 1
echo "✅ All services stopped and ports (8000, 5173) freed."
