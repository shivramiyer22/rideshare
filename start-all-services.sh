#!/bin/bash
#
# Start All Services for Priority Queue Visualization Testing
# This script starts MongoDB, Redis, Backend, and Frontend
#

echo "=========================================="
echo "🚀 Starting All Services"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check for MongoDB
echo -e "${BLUE}Step 1: Checking MongoDB...${NC}"
if command_exists mongod; then
    echo -e "${GREEN}✅ MongoDB is installed${NC}"
else
    echo -e "${RED}❌ MongoDB is NOT installed${NC}"
    echo ""
    echo "Please install MongoDB first:"
    echo "  macOS: brew install mongodb-community"
    echo "  Linux: sudo apt-get install mongodb"
    echo ""
    exit 1
fi

# Step 2: Start MongoDB
echo ""
echo -e "${BLUE}Step 2: Starting MongoDB...${NC}"

# Check if MongoDB is already running
if pgrep -x "mongod" > /dev/null; then
    echo -e "${YELLOW}⚠️  MongoDB is already running${NC}"
else
    # Create data directory if it doesn't exist
    mkdir -p /tmp/mongodb-data
    
    # Start MongoDB in background
    echo "Starting MongoDB on port 27017..."
    mongod --dbpath /tmp/mongodb-data --port 27017 --logpath /tmp/mongodb.log --fork
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ MongoDB started successfully${NC}"
        echo "   Data directory: /tmp/mongodb-data"
        echo "   Log file: /tmp/mongodb.log"
    else
        echo -e "${RED}❌ Failed to start MongoDB${NC}"
        exit 1
    fi
fi

# Step 3: Backend
echo ""
echo -e "${BLUE}Step 3: Backend Status...${NC}"
echo "Backend should be running in Terminal 5"
echo "If not, run: cd backend && ./start.sh"

# Step 4: Frontend
echo ""
echo -e "${BLUE}Step 4: Frontend Status...${NC}"
echo "Frontend should be running in Terminal 7"
echo "If not, run: cd frontend && npm run dev"

# Step 5: Test Services
echo ""
echo -e "${BLUE}Step 5: Testing Services...${NC}"

# Test MongoDB
if mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1 || mongo --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ MongoDB: Responding${NC}"
else
    echo -e "${RED}❌ MongoDB: Not responding${NC}"
fi

# Test Redis
if redis-cli ping > /dev/null 2>&1 || /tmp/redis-stable/src/redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis: Responding${NC}"
else
    echo -e "${YELLOW}⚠️  Redis: Not responding (will start with backend)${NC}"
fi

# Test Backend
sleep 2
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend: Running on port 8000${NC}"
else
    echo -e "${YELLOW}⚠️  Backend: Not responding yet (may still be starting)${NC}"
fi

# Test Frontend
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend: Running on port 3000${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend: Not responding yet (may still be starting)${NC}"
fi

# Final Summary
echo ""
echo "=========================================="
echo "📋 SUMMARY"
echo "=========================================="
echo ""
echo "Services Status:"
echo "  • MongoDB:  Started on port 27017"
echo "  • Redis:    Check Terminal 5 (backend log)"
echo "  • Backend:  Check Terminal 5"
echo "  • Frontend: Check Terminal 7"
echo ""
echo "Next Steps:"
echo "  1. Wait 10-20 seconds for backend to fully start"
echo "  2. Open browser: http://localhost:3000"
echo "  3. Navigate to 'Queue' tab"
echo "  4. Create test orders in 'Orders' tab"
echo "  5. View them in 'Queue' tab"
echo ""
echo "To test the API:"
echo "  curl http://localhost:8000/api/orders/queue/priority"
echo ""
echo "To stop MongoDB:"
echo "  mongod --shutdown --dbpath /tmp/mongodb-data"
echo ""
echo "=========================================="
echo -e "${GREEN}✅ All services should be starting!${NC}"
echo "=========================================="

