#!/bin/bash
# Start Mission Planning Assistant: backend (background) + frontend (foreground)
# Backend is started first so the vite proxy target is available immediately.

set -e

BACKEND_DIR="$(cd "$(dirname "$0")/apps/backend" && pwd)"
FRONTEND_DIR="$(cd "$(dirname "$0")/apps/frontend" && pwd)"

# Start backend in background
cd "$BACKEND_DIR"
./venv/bin/python -m app.main &
BACKEND_PID=$!

# Kill backend when the script exits
trap 'kill "$BACKEND_PID" 2>/dev/null || true' EXIT

# Wait for the backend to be ready
echo "Waiting for backend on http://localhost:8000 ..."
for i in {1..30}; do
  if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "Backend is ready"
    break
  fi
  sleep 1
done

# Start frontend in foreground (this is the exposed port)
cd "$FRONTEND_DIR"
bun run dev --host
