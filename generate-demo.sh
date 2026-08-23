#!/bin/bash
# Vigil Station Demo Generator
# Runs Playwright test + generates voiceover video
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/apps/frontend"
BACKEND_DIR="$SCRIPT_DIR/apps/backend"
OUTPUT_DIR="$SCRIPT_DIR/docs/demo"

echo "=== Vigil Station Demo Generator ==="
echo ""

# Check if dev servers are running
FRONTEND_RUNNING=false
BACKEND_RUNNING=false

if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "Frontend server: running"
    FRONTEND_RUNNING=true
fi

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend server: running"
    BACKEND_RUNNING=true
fi

# Start servers if not running
if [ "$FRONTEND_RUNNING" = false ] || [ "$BACKEND_RUNNING" = false ]; then
    echo "Starting servers..."
    
    if [ "$BACKEND_RUNNING" = false ]; then
        cd "$BACKEND_DIR"
        source venv/bin/activate
        nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
        echo "Backend started (PID: $!)"
    fi
    
    if [ "$FRONTEND_RUNNING" = false ]; then
        cd "$FRONTEND_DIR"
        nohup bun run dev > /tmp/frontend.log 2>&1 &
        echo "Frontend started (PID: $!)"
    fi
    
    echo "Waiting for servers..."
    sleep 8
fi

# Clean previous outputs
echo ""
echo "Cleaning previous outputs..."
rm -rf "$FRONTEND_DIR/test-results"
rm -rf "$FRONTEND_DIR/tests/demo/screenshots/"*.png
rm -rf "$FRONTEND_DIR/tests/demo/audio/"*.mp3

# Run Playwright test
echo ""
echo "Running Playwright demo test..."
cd "$FRONTEND_DIR"
bunx playwright test --reporter=list

# Generate voiceover
echo ""
echo "Generating voiceover..."
cd "$BACKEND_DIR"
source venv/bin/activate
cd "$FRONTEND_DIR"
python3 tests/demo/generate_voiceover.py

echo ""
echo "=== Demo Generated! ==="
echo "Output: $OUTPUT_DIR/vigil-station-demo-voiceover.mp4"
echo ""
ls -lh "$OUTPUT_DIR/"
