#!/bin/bash

# Test Backend After Restart
# Run this script after restarting the backend to verify all fixes

echo "======================================================================"
echo "TESTING BACKEND AFTER RESTART"
echo "======================================================================"
echo ""

# Test 1: Check if server is running
echo "Test 1: Checking if backend server is running..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$HTTP_CODE" == "200" ]; then
    echo "   ✅ Backend server is running"
else
    echo "   ❌ Backend server is NOT running (HTTP $HTTP_CODE)"
    echo "   Please restart the backend server first!"
    exit 1
fi
echo ""

# Test 2: Check OpenAPI schema for reports endpoints
echo "Test 2: Checking if reports endpoints are in OpenAPI schema..."
REPORTS=$(curl -s http://localhost:8000/openapi.json | python3 -c "import sys, json; data=json.load(sys.stdin); print([k for k in data.get('paths', {}).keys() if 'report' in k])" 2>/dev/null)
if [[ "$REPORTS" == *"segment-dynamic-pricing-analysis"* ]]; then
    echo "   ✅ Reports endpoints found in OpenAPI schema"
    echo "   $REPORTS"
else
    echo "   ❌ Reports endpoints NOT found"
    echo "   Found: $REPORTS"
fi
echo ""

# Test 3: Test GET orders endpoint
echo "Test 3: Testing GET /api/v1/orders/ endpoint..."
ORDERS_COUNT=$(curl -s http://localhost:8000/api/v1/orders/ | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data))" 2>/dev/null)
if [ "$ORDERS_COUNT" -gt "0" ]; then
    echo "   ✅ GET orders returns $ORDERS_COUNT orders"
else
    echo "   ❌ GET orders returned 0 orders (expected 17)"
fi
echo ""

# Test 4: Test reports summary endpoint
echo "Test 4: Testing GET /api/v1/reports/segment-dynamic-pricing-analysis/summary..."
SUMMARY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/reports/segment-dynamic-pricing-analysis/summary)
if [ "$SUMMARY_STATUS" == "200" ]; then
    echo "   ✅ Reports summary endpoint accessible (HTTP 200)"
else
    echo "   ⚠️  Reports summary endpoint returned HTTP $SUMMARY_STATUS"
    echo "   (404 is expected if no pipeline data exists yet)"
fi
echo ""

# Test 5: Test CSV format parameter
echo "Test 5: Testing CSV format parameter..."
CSV_HEADER=$(curl -s "http://localhost:8000/api/v1/reports/segment-dynamic-pricing-analysis?format=csv" 2>/dev/null | head -1)
if [[ "$CSV_HEADER" == *"location_category"* ]]; then
    echo "   ✅ CSV format works - header row found"
    echo "   Header: ${CSV_HEADER:0:100}..."
else
    echo "   ⚠️  CSV format test inconclusive"
    echo "   Response: ${CSV_HEADER:0:100}"
fi
echo ""

# Test 6: Check Swagger docs page
echo "Test 6: Checking if Swagger docs page loads..."
SWAGGER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
if [ "$SWAGGER_STATUS" == "200" ]; then
    echo "   ✅ Swagger docs page accessible at http://localhost:8000/docs"
else
    echo "   ❌ Swagger docs page not accessible (HTTP $SWAGGER_STATUS)"
fi
echo ""

echo "======================================================================"
echo "TEST SUMMARY"
echo "======================================================================"
echo ""
echo "✅ Verify in Swagger UI:"
echo "   1. Navigate to http://localhost:8000/docs"
echo "   2. Look for 'reports' section"
echo "   3. Test 'GET /api/v1/reports/segment-dynamic-pricing-analysis'"
echo "   4. Try both format=json and format=csv"
echo ""
echo "✅ Verify GET orders works:"
echo "   curl http://localhost:8000/api/v1/orders/ | python3 -m json.tool"
echo ""
echo "======================================================================"
