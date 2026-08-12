#!/bin/bash
# Start Mission Planning Assistant: backend (background) + frontend (foreground)
# The frontend is served as a production build via vite preview, which is
# reliable behind the platform's preview proxy (the dev server can hang there).

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/apps/backend"
FRONTEND_DIR="$ROOT_DIR/apps/frontend"

# Free ports and stop any running instances first
"$ROOT_DIR/stop.sh"

# Build the frontend production bundle
echo "Building frontend with bun..."
cd "$FRONTEND_DIR"
bun run build

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

# Serve the production build in foreground (this is the exposed port)
cd "$FRONTEND_DIR"
bun run preview
