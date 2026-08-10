#!/bin/bash

# Test runner script for Mission Planning Assistant backend
# Runs all unit tests for all API endpoints

set -e

echo "=========================================="
echo "Mission Planning Assistant - Test Runner"
echo "=========================================="
echo ""

# Check if we're in the backend directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Must be run from apps/backend directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install test dependencies if not already installed
echo "Checking test dependencies..."
pip install -q pytest pytest-asyncio httpx

# Set environment variables for testing
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export SPACETRACK_USERNAME="test_user"
export SPACETRACK_PASSWORD="test_pass"
export ANTHROPIC_API_KEY="test_key"
export DATABASE_URL="postgresql://test:test@localhost:5432/test_db"

echo ""
echo "Running all API endpoint tests..."
echo "=========================================="
echo ""

# Run all tests with verbose output
pytest tests/ -v --tb=short

# Check test result
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ All tests passed!"
    echo "=========================================="
    echo ""
    
    # Show test summary
    echo "Test Coverage Summary:"
    echo "----------------------"
    pytest tests/ --collect-only -q | tail -n 1
    
else
    echo ""
    echo "=========================================="
    echo "❌ Some tests failed. See output above."
    echo "=========================================="
    exit 1
fi