#!/bin/bash

# Backend Server Restart Script
# This script stops the current backend server and restarts it with a clean cache

echo "======================================================================"
echo "BACKEND SERVER RESTART"
echo "======================================================================"

# Navigate to backend directory
cd "$(dirname "$0")"

echo ""
echo "1. Checking for running uvicorn processes..."
PIDS=$(pgrep -f "uvicorn app.main:app")

if [ -z "$PIDS" ]; then
    echo "   ℹ️  No running uvicorn processes found"
else
    echo "   Found uvicorn process(es): $PIDS"
    echo "   Please stop the backend server manually:"
    echo "   → In the terminal where uvicorn is running, press Ctrl+C"
    echo ""
    echo "   Or kill the process(es) with: kill $PIDS"
    exit 1
fi

echo ""
echo "2. Activating virtual environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "   ✓ Virtual environment activated"
else
    echo "   ⚠️  Virtual environment not found, using system Python"
fi

echo ""
echo "3. Starting backend server with auto-reload..."
echo "   Command: uvicorn app.main:app --reload"
echo ""
echo "======================================================================"
echo "STARTING SERVER..."
echo "======================================================================"
echo ""

# Start the server
uvicorn app.main:app --reload

