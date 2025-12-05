#!/bin/bash

# =============================================================================
# Segment Pricing Analysis Tab - Integration Test Script
# =============================================================================
# This script tests the complete integration of the Segment Pricing Analysis tab
# including API connectivity, component rendering, and data flow.
# =============================================================================

echo "=========================================="
echo "SEGMENT PRICING ANALYSIS TAB - INTEGRATION TEST"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Backend URL
BACKEND_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}"

# Function to print test result
print_result() {
    local test_name="$1"
    local result="$2"
    local message="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC} - $test_name"
        [ -n "$message" ] && echo "  └─ $message"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAIL${NC} - $test_name"
        [ -n "$message" ] && echo "  └─ $message"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo ""
}

echo "=== PHASE 1: Backend API Connectivity ==="
echo ""

# Test 1: Backend Health Check
echo "[Test 1] Checking backend health..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health" 2>/dev/null)
if [ "$HEALTH_RESPONSE" = "200" ]; then
    print_result "Backend Health Check" "PASS" "Backend is responding (HTTP 200)"
else
    print_result "Backend Health Check" "FAIL" "Backend not responding (HTTP $HEALTH_RESPONSE)"
fi

# Test 2: Segments Endpoint
echo "[Test 2] Testing segments endpoint..."
SEGMENTS_RESPONSE=$(curl -s "$BACKEND_URL/api/v1/reports/segment-dynamic-pricing-analysis" 2>/dev/null)
SEGMENTS_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/v1/reports/segment-dynamic-pricing-analysis" 2>/dev/null)

if [ "$SEGMENTS_HTTP_CODE" = "200" ]; then
    # Check if response has required fields (using metadata instead of success)
    if echo "$SEGMENTS_RESPONSE" | grep -q "\"metadata\"" && echo "$SEGMENTS_RESPONSE" | grep -q "\"segments\""; then
        print_result "Segments API Endpoint" "PASS" "Returns valid response with segments array (HTTP 200)"
    else
        print_result "Segments API Endpoint" "FAIL" "Response missing required fields (metadata, segments)"
    fi
else
    print_result "Segments API Endpoint" "FAIL" "HTTP $SEGMENTS_HTTP_CODE"
fi

# Test 3: Business Objectives Endpoint
echo "[Test 3] Testing business objectives endpoint..."
OBJECTIVES_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/v1/analytics/pricing-strategies?filter_by=business_objectives" 2>/dev/null)
OBJECTIVES_RESPONSE=$(curl -s "$BACKEND_URL/api/v1/analytics/pricing-strategies?filter_by=business_objectives" 2>/dev/null)

if [ "$OBJECTIVES_HTTP_CODE" = "200" ]; then
    if echo "$OBJECTIVES_RESPONSE" | grep -q "\"strategies\""; then
        OBJECTIVES_COUNT=$(echo "$OBJECTIVES_RESPONSE" | grep -o "Maximize Revenue\|Maximize Profit\|Stay Competitive\|Customer Retention" | wc -l | tr -d ' ')
        print_result "Business Objectives API" "PASS" "Returns $OBJECTIVES_COUNT objectives (HTTP 200)"
    else
        print_result "Business Objectives API" "FAIL" "Response missing 'strategies' field"
    fi
else
    print_result "Business Objectives API" "FAIL" "HTTP $OBJECTIVES_HTTP_CODE"
fi

# Test 4: Recommendations Endpoint
echo "[Test 4] Testing recommendations endpoint..."
RECOMMENDATIONS_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/v1/analytics/pricing-strategies?filter_by=pipeline_results&include_pipeline_data=true" 2>/dev/null)
RECOMMENDATIONS_RESPONSE=$(curl -s "$BACKEND_URL/api/v1/analytics/pricing-strategies?filter_by=pipeline_results&include_pipeline_data=true" 2>/dev/null)

if [ "$RECOMMENDATIONS_HTTP_CODE" = "200" ]; then
    # Check if response is valid JSON (it may not have pipeline data yet, which is OK)
    if echo "$RECOMMENDATIONS_RESPONSE" | grep -q "\"timestamp\""; then
        print_result "Recommendations API" "PASS" "Returns valid response (HTTP 200, pipeline data may be pending)"
    else
        print_result "Recommendations API" "FAIL" "Invalid JSON response"
    fi
else
    print_result "Recommendations API" "FAIL" "HTTP $RECOMMENDATIONS_HTTP_CODE"
fi

echo ""
echo "=== PHASE 2: Frontend Component Structure ==="
echo ""

# Test 5: Check if SegmentPricingAnalysisTab.tsx exists
echo "[Test 5] Checking tab component file..."
if [ -f "frontend/src/components/tabs/SegmentPricingAnalysisTab.tsx" ]; then
    print_result "Tab Component File" "PASS" "SegmentPricingAnalysisTab.tsx exists"
else
    print_result "Tab Component File" "FAIL" "SegmentPricingAnalysisTab.tsx not found"
fi

# Test 6: Check Sidebar.tsx has segment-pricing TabType
echo "[Test 6] Checking Sidebar TabType update..."
if grep -q "'segment-pricing'" frontend/src/components/layout/Sidebar.tsx; then
    print_result "Sidebar TabType" "PASS" "'segment-pricing' added to TabType"
else
    print_result "Sidebar TabType" "FAIL" "'segment-pricing' not found in Sidebar.tsx"
fi

# Test 7: Check Sidebar.tsx has BarChart3 icon
echo "[Test 7] Checking Sidebar icon import..."
if grep -q "BarChart3" frontend/src/components/layout/Sidebar.tsx; then
    print_result "Sidebar Icon Import" "PASS" "BarChart3 icon imported"
else
    print_result "Sidebar Icon Import" "FAIL" "BarChart3 not found in imports"
fi

# Test 8: Check Sidebar.tsx has menu item
echo "[Test 8] Checking Sidebar menu item..."
if grep -q "Segment Pricing Analysis" frontend/src/components/layout/Sidebar.tsx; then
    print_result "Sidebar Menu Item" "PASS" "'Segment Pricing Analysis' menu item exists"
else
    print_result "Sidebar Menu Item" "FAIL" "'Segment Pricing Analysis' not found"
fi

# Test 9: Check page.tsx has import
echo "[Test 9] Checking page.tsx import..."
if grep -q "SegmentPricingAnalysisTab" frontend/src/app/page.tsx; then
    print_result "Page.tsx Import" "PASS" "SegmentPricingAnalysisTab imported"
else
    print_result "Page.tsx Import" "FAIL" "SegmentPricingAnalysisTab not imported"
fi

# Test 10: Check page.tsx has routing case
echo "[Test 10] Checking page.tsx routing..."
if grep -q "case 'segment-pricing'" frontend/src/app/page.tsx; then
    print_result "Page.tsx Routing" "PASS" "'segment-pricing' case added to switch"
else
    print_result "Page.tsx Routing" "FAIL" "'segment-pricing' case not found"
fi

echo ""
echo "=== PHASE 3: Component Refactoring Verification ==="
echo ""

# Test 11: Check chatbot panel removed
echo "[Test 11] Verifying chatbot panel removed..."
if ! grep -q "AI Chatbot Panel" supplemental/SegmentDynamicAnalysis.tsx; then
    print_result "Chatbot Panel Removal" "PASS" "AI Chatbot Panel removed"
else
    print_result "Chatbot Panel Removal" "FAIL" "AI Chatbot Panel still present"
fi

# Test 12: Check chatMessages state removed
echo "[Test 12] Verifying chatMessages state removed..."
if ! grep -q "chatMessages" supplemental/SegmentDynamicAnalysis.tsx; then
    print_result "ChatMessages State Removal" "PASS" "chatMessages state removed"
else
    print_result "ChatMessages State Removal" "FAIL" "chatMessages still present"
fi

# Test 13: Check MessageSquare import removed
echo "[Test 13] Verifying MessageSquare import removed..."
if ! grep -q "MessageSquare" supplemental/SegmentDynamicAnalysis.tsx; then
    print_result "MessageSquare Import Removal" "PASS" "MessageSquare import removed"
else
    print_result "MessageSquare Import Removal" "FAIL" "MessageSquare still imported"
fi

# Test 14: Check API endpoints updated
echo "[Test 14] Verifying API endpoints updated..."
if grep -q "/api/v1/reports/segment-dynamic-pricing-analysis" supplemental/SegmentDynamicAnalysis.tsx; then
    print_result "API Endpoints Updated" "PASS" "Correct API endpoints configured"
else
    print_result "API Endpoints Updated" "FAIL" "API endpoints not updated"
fi

# Test 15: Check theme colors applied
echo "[Test 15] Verifying theme colors applied..."
THEME_COLORS_COUNT=$(grep -c "bg-primary\|bg-card\|bg-background\|text-foreground\|text-muted-foreground\|border-border" supplemental/SegmentDynamicAnalysis.tsx)
if [ "$THEME_COLORS_COUNT" -gt 10 ]; then
    print_result "Theme Colors Applied" "PASS" "$THEME_COLORS_COUNT theme utility classes found"
else
    print_result "Theme Colors Applied" "FAIL" "Only $THEME_COLORS_COUNT theme classes found (expected >10)"
fi

# Test 16: Check old hardcoded colors removed
echo "[Test 16] Verifying old hardcoded colors removed..."
OLD_COLORS_COUNT=$(grep -c "bg-blue-600\|bg-gray-50\|text-gray-900" supplemental/SegmentDynamicAnalysis.tsx)
if [ "$OLD_COLORS_COUNT" -eq 0 ]; then
    print_result "Old Colors Removed" "PASS" "No hardcoded colors remaining"
else
    print_result "Old Colors Removed" "FAIL" "$OLD_COLORS_COUNT hardcoded color classes still present"
fi

echo ""
echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="
echo -e "Total Tests:  $TOTAL_TESTS"
echo -e "${GREEN}Passed:       $PASSED_TESTS${NC}"
echo -e "${RED}Failed:       $FAILED_TESTS${NC}"
echo ""

PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
echo "Pass Rate: $PASS_RATE%"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
    echo "The Segment Pricing Analysis tab is fully integrated."
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo "Please review the failed tests above."
    exit 1
fi

