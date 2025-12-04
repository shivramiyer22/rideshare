#!/bin/bash

# Kill old backend process and restart
# This script handles the "Address already in use" error

echo "======================================================================"
echo "KILLING OLD BACKEND PROCESS AND RESTARTING"
echo "======================================================================"
echo ""

# Step 1: Find process using port 8000
echo "1. Finding process using port 8000..."
PID=$(lsof -ti:8000)

if [ -z "$PID" ]; then
    echo "   ℹ️  No process found on port 8000"
else
    echo "   Found process: $PID"
    echo ""
    echo "2. Killing process $PID..."
    kill -9 $PID
    sleep 2
    
    # Verify it's killed
    if lsof -ti:8000 > /dev/null 2>&1; then
        echo "   ⚠️  Process still running, trying force kill..."
        kill -9 $PID 2>/dev/null
        sleep 1
    fi
    
    echo "   ✓ Process killed"
fi

echo ""
echo "3. Waiting 2 seconds for port to be released..."
sleep 2

echo ""
echo "4. Starting backend server..."
echo "   Command: uvicorn app.main:app --reload"
echo ""
echo "======================================================================"
echo "STARTING SERVER..."
echo "======================================================================"
echo ""

# Navigate to backend directory and start server
cd "$(dirname "$0")"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start the server
uvicorn app.main:app --reload
