#!/bin/bash
echo "🧪 Testing Mission Planning Assistant..."

# Wait for backend to be ready
echo "Waiting for backend..."
for i in {1..20}; do
  curl -s http://localhost:8000/ > /dev/null 2>&1 && break
  sleep 1
done

echo "1. Testing backend health..."
curl -s http://localhost:8000/ | grep -q "Mission Planning" && echo "✅ Backend OK" || echo "❌ Backend failed"

echo "2. Testing satellites endpoint..."
curl -s http://localhost:8000/satellites | grep -q "satellites" && echo "✅ Satellites OK" || echo "❌ Satellites failed"

echo "3. Testing ground stations..."
curl -s http://localhost:8000/ground-stations | grep -q "Jakarta" && echo "✅ Ground stations OK" || echo "❌ Ground stations failed"

echo "4. Testing frontend..."
curl -s http://localhost:5173 | grep -q "Mission Planning" && echo "✅ Frontend OK" || echo "❌ Frontend failed"

echo "✅ All tests complete!"
