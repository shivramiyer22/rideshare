#!/bin/bash

# Comprehensive Testing Script for Forecasting & Segment Analysis
# ================================================================

echo "=================================================="
echo "COMPREHENSIVE TESTING - Forecasting & Segment Analysis"
echo "Date: $(date)"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASS=0
FAIL=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -n "Testing $name... "
    response=$(curl -s "$url" 2>&1)
    
    if echo "$response" | grep -q "$expected"; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Expected: $expected"
        echo "  Got: $(echo "$response" | head -c 100)..."
        ((FAIL++))
        return 1
    fi
}

echo "=================================================="
echo "BACKEND API TESTS"
echo "=================================================="
echo ""

# Test 1: Backend Health
test_endpoint "Backend Health" "http://localhost:8000/health" "healthy"

# Test 2: HWCO Forecast Aggregate (30 days)
echo -n "Testing HWCO Forecast (30d)... "
response=$(curl -s "http://localhost:8000/api/v1/analytics/hwco-forecast-aggregate?pricing_model=STANDARD&periods=30")
rides=$(echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('summary', {}).get('avg_rides_per_day', 0))" 2>/dev/null)
if [ "$rides" != "0" ] && [ "$rides" != "" ]; then
    echo -e "${GREEN}✓ PASS${NC} (${rides} rides/day)"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC} (No valid data)"
    ((FAIL++))
fi

# Test 3: HWCO Forecast Aggregate (60 days)
echo -n "Testing HWCO Forecast (60d)... "
response=$(curl -s "http://localhost:8000/api/v1/analytics/hwco-forecast-aggregate?pricing_model=STANDARD&periods=60")
if echo "$response" | grep -q "avg_rides_per_day"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Test 4: HWCO Forecast Aggregate (90 days)
echo -n "Testing HWCO Forecast (90d)... "
response=$(curl -s "http://localhost:8000/api/v1/analytics/hwco-forecast-aggregate?pricing_model=STANDARD&periods=90")
if echo "$response" | grep -q "avg_rides_per_day"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Test 5: Segment Dynamic Pricing Report
echo -n "Testing Segment Analysis Data... "
response=$(curl -s "http://localhost:8000/api/v1/reports/segment-dynamic-pricing-analysis")
segment_count=$(echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d.get('segments', [])))" 2>/dev/null)
if [ "$segment_count" -gt "100" ]; then
    echo -e "${GREEN}✓ PASS${NC} ($segment_count segments)"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC} (Only $segment_count segments)"
    ((FAIL++))
fi

# Test 6: Business Objectives
test_endpoint "Business Objectives" "http://localhost:8000/api/v1/analytics/pricing-strategies?filter_by=business_objectives" "name"

# Test 7: Recommendations
test_endpoint "Recommendations" "http://localhost:8000/api/v1/analytics/pricing-strategies?filter_by=pipeline_results&include_pipeline_data=true" "recommendations"

# Test 8: Pipeline Last Run
echo -n "Testing Pipeline Status... "
response=$(curl -s "http://localhost:8000/api/v1/pipeline/last-run")
run_id=$(echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('last_run', {}).get('run_id', ''))" 2>/dev/null)
if [ ! -z "$run_id" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Run ID: $run_id)"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

echo ""
echo "=================================================="
echo "DATA QUALITY TESTS"
echo "=================================================="
echo ""

# Test 9: Check for non-zero values
echo -n "Testing Non-Zero Forecasts... "
response=$(curl -s "http://localhost:8000/api/v1/analytics/hwco-forecast-aggregate?pricing_model=STANDARD&periods=30")
rides=$(echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['summary']['avg_rides_per_day'])" 2>/dev/null)
price=$(echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['summary']['avg_unit_price_per_minute'])" 2>/dev/null)
duration=$(echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['summary']['avg_ride_duration_minutes'])" 2>/dev/null)
revenue=$(echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['summary']['total_revenue_forecast'])" 2>/dev/null)

if [ ! -z "$rides" ] && [ "$rides" != "0" ] && [ ! -z "$price" ] && [ "$price" != "0" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    echo "  - Rides: $rides/day"
    echo "  - Price: \$${price}/min"
    echo "  - Duration: ${duration} min"
    echo "  - Revenue: \$${revenue}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC} (Zero values detected)"
    ((FAIL++))
fi

# Test 10: Check for negative rides (should not exist)
echo -n "Testing No Negative Rides... "
daily_forecasts=$(echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(all(day['predicted_rides'] >= 0 for day in d['daily_forecasts']))" 2>/dev/null)
if [ "$daily_forecasts" = "True" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC} (Negative rides detected)"
    ((FAIL++))
fi

echo ""
echo "=================================================="
echo "FRONTEND TESTS"
echo "=================================================="
echo ""

# Test 11: Frontend Health
echo -n "Testing Frontend Server... "
response=$(curl -s http://localhost:3000 2>&1)
if echo "$response" | grep -q "Dynamic Pricing"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

echo ""
echo "=================================================="
echo "SUMMARY"
echo "=================================================="
echo ""
echo -e "Total Tests: $((PASS + FAIL))"
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    exit 1
fi

