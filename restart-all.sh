#!/bin/bash

# Restart All Script
# Restarts Redis, backend, frontend, Data Ingestion Agent, and all required services
# Also clears all caches and ensures ML cron jobs are configured

set -e

echo "🔄 Restarting All Applications..."
echo "=================================="
echo ""

# Get the project root directory
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0
    else
        return 1
    fi
}

# Clear all caches
echo "📦 Clearing all caches..."
echo "------------------------"

# Clear Python caches
echo "   Clearing Python caches..."
find "$PROJECT_ROOT/backend" -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
find "$PROJECT_ROOT/backend" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$PROJECT_ROOT/backend" -type f -name "*.pyo" -delete 2>/dev/null || true
find "$PROJECT_ROOT/backend" -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
rm -rf "$PROJECT_ROOT/backend/.pytest_cache" 2>/dev/null || true
echo "   ✓ Python caches cleared"

# Clear Next.js caches
echo "   Clearing Next.js caches..."
rm -rf "$PROJECT_ROOT/frontend/.next" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/frontend/.turbo" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/frontend/node_modules/.cache" 2>/dev/null || true
npm cache clean --force 2>/dev/null || true
echo "   ✓ Next.js caches cleared"

echo "   ✓ All caches cleared"
echo ""

# Kill existing processes
echo "🛑 Stopping existing processes..."
echo "--------------------------------"

# Stop Data Ingestion Agent
echo "   Stopping Data Ingestion Agent..."
pkill -f "data_ingestion.py" 2>/dev/null || true
sleep 1
echo "   ✓ Data Ingestion Agent stopped"

# Stop backend
if check_port 8000; then
    echo "   Stopping backend on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
    echo "   ✓ Backend stopped"
fi

# Stop frontend
if check_port 3000; then
    echo "   Stopping frontend on port 3000..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    sleep 2
    echo "   ✓ Frontend stopped"
fi

echo "   ✓ All processes stopped"
echo ""

# Start Redis
echo "🔴 Starting Redis..."
echo "-------------------"
if [ -f "$PROJECT_ROOT/start-redis.sh" ]; then
    bash "$PROJECT_ROOT/start-redis.sh" || echo "   ⚠️  Redis startup failed, continuing anyway..."
else
    echo "   ⚠️  Redis startup script not found, skipping..."
fi
echo ""

# Create log directories
mkdir -p "$PROJECT_ROOT/logs" 2>/dev/null || true
mkdir -p "$PROJECT_ROOT/backend/logs" 2>/dev/null || true

# Check ML retraining cron job
echo "🤖 Checking ML Retraining Cron Job..."
echo "--------------------------------------"
CRON_CMD="0 3 * * 0"
CRON_JOB="$CRON_CMD $PROJECT_ROOT/backend/venv/bin/python $PROJECT_ROOT/backend/scripts/retrain_models.py"
if crontab -l 2>/dev/null | grep -q "retrain_models.py"; then
    echo "   ✓ ML retraining cron job is configured (Sunday 3 AM)"
else
    echo "   ⚠️  ML retraining cron job not found"
    echo "   📝 To set up, run:"
    echo "      (crontab -l 2>/dev/null; echo \"$CRON_JOB\") | crontab -"
fi
echo ""

# Start backend first
echo "🚀 Starting Backend..."
echo "---------------------"
cd "$PROJECT_ROOT/backend"
chmod +x start.sh 2>/dev/null || true

# Run backend in background and capture output
nohup ./start.sh > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
BACKEND_PID=$!

echo "   Backend PID: $BACKEND_PID"
echo "   Logs: $PROJECT_ROOT/logs/backend.log"
echo "   Data Ingestion Agent logs: $PROJECT_ROOT/backend/logs/data_ingestion.log"

# Wait for backend to be ready
echo ""
echo "⏳ Waiting for backend to start (15 seconds)..."
sleep 15

# Check if backend is running
if check_port 8000; then
    echo "   ✓ Backend is running on port 8000"
else
    echo "   ⚠️  Backend may still be starting... (check logs if issues)"
fi

# Check if Data Ingestion Agent is running
if ps aux | grep -v grep | grep -q "data_ingestion.py"; then
    DATA_INGESTION_PID=$(ps aux | grep -v grep | grep "data_ingestion.py" | awk '{print $2}' | head -1)
    echo "   ✓ Data Ingestion Agent is running (PID: $DATA_INGESTION_PID)"
else
    echo "   ⚠️  Data Ingestion Agent may not be running (check logs)"
fi

echo ""

# Start frontend
echo "🚀 Starting Frontend..."
echo "----------------------"
cd "$PROJECT_ROOT/frontend"
chmod +x start.sh 2>/dev/null || true

# Run frontend in background and capture output
nohup ./start.sh > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!

echo "   Frontend PID: $FRONTEND_PID"
echo "   Logs: $PROJECT_ROOT/logs/frontend.log"

# Wait for frontend to be ready
echo ""
echo "⏳ Waiting for frontend to start (10 seconds)..."
sleep 10

# Check if frontend is running
if check_port 3000; then
    echo "   ✓ Frontend is running on port 3000"
else
    echo "   ⚠️  Frontend may still be starting... (check logs if issues)"
fi

echo ""
echo "=================================="
echo "✅ All applications started!"
echo ""
echo "📍 Services:"
echo "   Backend API:        http://localhost:8000"
echo "   API Docs:          http://localhost:8000/docs"
echo "   Frontend:           http://localhost:3000"
echo "   Redis:              localhost:6379"
echo ""
echo "📋 Process IDs:"
echo "   Backend:            $BACKEND_PID"
echo "   Frontend:           $FRONTEND_PID"
if [ ! -z "$DATA_INGESTION_PID" ]; then
    echo "   Data Ingestion:      $DATA_INGESTION_PID"
fi
echo ""
echo "📝 View logs:"
echo "   Backend:            tail -f $PROJECT_ROOT/logs/backend.log"
echo "   Frontend:           tail -f $PROJECT_ROOT/logs/frontend.log"
echo "   Data Ingestion:     tail -f $PROJECT_ROOT/backend/logs/data_ingestion.log"
echo ""
echo "🔄 Background Services:"
echo "   Analytics Pre-computation: Runs every 5 minutes (APScheduler)"
echo "   ML Retraining:             Sunday 3 AM (cron job)"
echo ""
echo "🛑 To stop all services:"
echo "   pkill -f 'uvicorn app.main:app'"
echo "   pkill -f 'next dev'"
echo "   pkill -f 'data_ingestion.py'"
echo ""

