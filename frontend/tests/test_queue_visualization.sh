#!/bin/bash
#
# Priority Queue Visualization - Testing Script
# This script helps verify the queue visualization is working correctly
#

echo "=========================================="
echo "Priority Queue Visualization - Test Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Backend
echo "Step 1: Checking Backend Status..."
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running on port 8000${NC}"
else
    echo -e "${RED}❌ Backend is NOT running${NC}"
    echo "   Please start backend: cd backend && ./start.sh"
    exit 1
fi
echo ""

# Step 2: Check Redis
echo "Step 2: Checking Redis Status..."
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${RED}❌ Redis is NOT running${NC}"
    echo "   Please start Redis: redis-server"
    exit 1
fi
echo ""

# Step 3: Check Frontend
echo "Step 3: Checking Frontend Status..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is running on port 3000${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend might not be running${NC}"
    echo "   Please start frontend: cd frontend && npm run dev"
fi
echo ""

# Step 4: Test Priority Queue Endpoint
echo "Step 4: Testing Priority Queue API Endpoint..."
RESPONSE=$(curl -s http://localhost:8000/api/orders/queue/priority)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ API endpoint is accessible${NC}"
    
    # Check if response contains expected structure
    if echo "$RESPONSE" | grep -q '"P0"' && echo "$RESPONSE" | grep -q '"P1"' && echo "$RESPONSE" | grep -q '"P2"'; then
        echo -e "${GREEN}✅ Response contains P0, P1, P2 queues${NC}"
        
        # Extract counts
        P0_COUNT=$(echo "$RESPONSE" | grep -o '"P0":[0-9]*' | grep -o '[0-9]*')
        P1_COUNT=$(echo "$RESPONSE" | grep -o '"P1":[0-9]*' | grep -o '[0-9]*')
        P2_COUNT=$(echo "$RESPONSE" | grep -o '"P2":[0-9]*' | grep -o '[0-9]*')
        
        echo ""
        echo "Current Queue Status:"
        echo "  🔴 P0 (CONTRACTED): $P0_COUNT orders"
        echo "  🟡 P1 (STANDARD):   $P1_COUNT orders"
        echo "  🟢 P2 (CUSTOM):     $P2_COUNT orders"
        
        TOTAL=$((P0_COUNT + P1_COUNT + P2_COUNT))
        echo "  📊 TOTAL:           $TOTAL orders"
    else
        echo -e "${RED}❌ Response structure is incorrect${NC}"
        echo "Response: $RESPONSE"
        exit 1
    fi
else
    echo -e "${RED}❌ Failed to connect to API endpoint${NC}"
    exit 1
fi
echo ""

# Step 5: Check if queue visualization files exist
echo "Step 5: Checking Queue Visualization Files..."
FILES_TO_CHECK=(
    "src/types/queue.ts"
    "src/components/queue/OrderCard.tsx"
    "src/components/queue/QueueColumn.tsx"
    "src/components/queue/QueueStats.tsx"
    "src/components/queue/PriorityQueueViz.tsx"
    "src/components/tabs/QueueTab.tsx"
)

ALL_FILES_EXIST=true
for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ $file NOT FOUND${NC}"
        ALL_FILES_EXIST=false
    fi
done

if [ "$ALL_FILES_EXIST" = false ]; then
    echo -e "${RED}❌ Some files are missing${NC}"
    exit 1
fi
echo ""

# Summary
echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="
echo -e "${GREEN}✅ Backend: Running${NC}"
echo -e "${GREEN}✅ Redis: Running${NC}"
echo -e "${GREEN}✅ API Endpoint: Working${NC}"
echo -e "${GREEN}✅ Queue Files: All present${NC}"
echo ""
echo -e "${GREEN}🎉 All checks passed!${NC}"
echo ""
echo "=========================================="
echo "NEXT STEPS - Manual Testing"
echo "=========================================="
echo ""
echo "1. Open browser: http://localhost:3000"
echo "2. Navigate to 'Queue' or 'Priority Queue' tab"
echo "3. Verify you see 3 columns (P0, P1, P2)"
echo "4. Check colors: P0=Red, P1=Amber, P2=Green"
echo ""
echo "If no orders are showing:"
echo "  a) Go to 'Orders' tab"
echo "  b) Create 2-3 orders of each type"
echo "  c) Return to 'Queue' tab"
echo "  d) Wait 5 seconds for auto-refresh"
echo ""
echo "Test features:"
echo "  ✓ Auto-refresh (wait 5 seconds)"
echo "  ✓ Manual refresh button"
echo "  ✓ Responsive design (resize window)"
echo "  ✓ Order details display correctly"
echo ""
echo "=========================================="

