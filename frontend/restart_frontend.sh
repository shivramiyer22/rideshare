#!/bin/bash

# Frontend Restart Script
# Fixes npm cache permissions and restarts the frontend

echo "=== Rideshare Frontend Restart Script ==="
echo ""

# Step 1: Fix npm cache permissions (requires sudo)
echo "Step 1: Fixing npm cache permissions..."
sudo chown -R $(id -u):$(id -g) "$HOME/.npm"
echo "✅ npm cache permissions fixed"
echo ""

# Step 2: Navigate to frontend directory
cd "$(dirname "$0")"
echo "Working directory: $(pwd)"
echo ""

# Step 3: Clear caches
echo "Step 2: Clearing caches..."
rm -rf .next node_modules/.cache
echo "✅ Cleared .next and node_modules cache"
echo ""

# Step 4: Kill existing frontend processes
echo "Step 3: Stopping existing frontend processes..."
pkill -f "next dev" 2>/dev/null || echo "No existing frontend processes"
sleep 2
echo "✅ Stopped existing processes"
echo ""

# Step 5: Check if node_modules exists
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
    echo "Step 4: Installing dependencies..."
    npm install
    echo "✅ Dependencies installed"
else
    echo "Step 4: Dependencies already installed (skipping)"
fi
echo ""

# Step 6: Start frontend
echo "Step 5: Starting frontend server..."
echo "Frontend will be available at: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo ""
echo "Starting in development mode..."
npm run dev


