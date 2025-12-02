#!/bin/bash

# Backend Start Script
# Clears caches and restarts the FastAPI backend application

# Don't exit on error - we want to continue even if Data Ingestion Agent fails
set +e

echo "🚀 Starting Backend Application..."
echo "=================================="

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Clear Python cache files
echo "📦 Clearing Python cache..."
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
echo "   ✓ Cleared Python cache files"

# Clear pytest cache
echo "📦 Clearing pytest cache..."
rm -rf .pytest_cache 2>/dev/null || true
rm -rf tests/__pycache__ 2>/dev/null || true
echo "   ✓ Cleared pytest cache"

# Start Redis server (if not already running)
echo "🔴 Starting Redis server..."
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
if [ -f "$PROJECT_ROOT/start-redis.sh" ]; then
    bash "$PROJECT_ROOT/start-redis.sh" || echo "   ⚠️  Redis startup failed, continuing anyway..."
else
    echo "   ⚠️  Redis startup script not found, skipping..."
fi

# Kill any existing uvicorn processes on port 8000
echo "🛑 Stopping existing processes on port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
echo "   ✓ Port 8000 cleared"

# Kill any existing Data Ingestion Agent processes
echo "🛑 Stopping existing Data Ingestion Agent processes..."
pkill -f "data_ingestion.py" 2>/dev/null || true
sleep 1
echo "   ✓ Data Ingestion Agent processes stopped"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📥 Creating virtual environment..."
    python3 -m venv venv
    echo "   ✓ Virtual environment created"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "   ✓ Virtual environment activated"

# Install/update dependencies
echo "📥 Installing/updating dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo "   ✓ Dependencies installed"

# Start Data Ingestion Agent in background
echo "🤖 Starting Data Ingestion Agent..."
LOG_DIR="$PROJECT_ROOT/backend/logs"
mkdir -p "$LOG_DIR" 2>/dev/null || true
# Use python -m to ensure proper module resolution
nohup python -m app.agents.data_ingestion > "$LOG_DIR/data_ingestion.log" 2>&1 &
DATA_INGESTION_PID=$!
sleep 3
if ps -p $DATA_INGESTION_PID > /dev/null 2>&1; then
    echo "   ✓ Data Ingestion Agent started (PID: $DATA_INGESTION_PID)"
    echo "   📄 Logs: $LOG_DIR/data_ingestion.log"
else
    echo "   ⚠️  Data Ingestion Agent may have failed to start"
    echo "   📄 Check logs: $LOG_DIR/data_ingestion.log"
fi

# Start the FastAPI server
echo ""
echo "🚀 Starting FastAPI server..."
echo "   Backend API will be available at http://localhost:8000"
echo "   API docs available at http://localhost:8000/docs"
echo "   Data Ingestion Agent logs: $LOG_DIR/data_ingestion.log"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload


