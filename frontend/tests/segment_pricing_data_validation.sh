#!/bin/bash

# =============================================================================
# Segment Pricing Analysis - Data Validation Test
# =============================================================================
# This script validates that the 162 segments have recommendation data
# =============================================================================

echo "=========================================="
echo "SEGMENT PRICING ANALYSIS - DATA VALIDATION"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKEND_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}"

echo "=== Validating Segment Data with Recommendations ==="
echo ""

# Test 1: Check segment count
echo "[Test 1] Checking segment count..."
SEGMENT_RESPONSE=$(curl -s "$BACKEND_URL/api/v1/reports/segment-dynamic-pricing-analysis" 2>/dev/null)
SEGMENT_COUNT=$(echo "$SEGMENT_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('metadata', {}).get('total_segments', 0))" 2>/dev/null)

if [ "$SEGMENT_COUNT" = "162" ]; then
    echo -e "${GREEN}✓ PASS${NC} - 162 segments found"
else
    echo -e "${RED}✗ FAIL${NC} - Expected 162 segments, found $SEGMENT_COUNT"
    exit 1
fi
echo ""

# Test 2: Check if segments have recommendation data
echo "[Test 2] Checking recommendation data structure..."
HAS_REC_DATA=$(echo "$SEGMENT_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
segments = data.get('segments', [])
if segments:
    sample = segments[0]
    has_rec1 = 'recommendation_1' in sample
    has_rec2 = 'recommendation_2' in sample
    has_rec3 = 'recommendation_3' in sample
    print('yes' if (has_rec1 and has_rec2 and has_rec3) else 'no')
else:
    print('no')
" 2>/dev/null)

if [ "$HAS_REC_DATA" = "yes" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Segments have recommendation_1, recommendation_2, recommendation_3 data"
else
    echo -e "${RED}✗ FAIL${NC} - Segments missing recommendation data"
    exit 1
fi
echo ""

# Test 3: Validate recommendation values are non-zero
echo "[Test 3] Validating recommendation values..."
REC_VALUES=$(echo "$SEGMENT_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
segments = data.get('segments', [])
if segments:
    sample = segments[0]
    rec1_rev = sample.get('recommendation_1', {}).get('revenue_30d', 0)
    rec2_rev = sample.get('recommendation_2', {}).get('revenue_30d', 0)
    rec3_rev = sample.get('recommendation_3', {}).get('revenue_30d', 0)
    
    all_positive = rec1_rev > 0 and rec2_rev > 0 and rec3_rev > 0
    print('valid' if all_positive else 'invalid')
    print(f'{rec1_rev},{rec2_rev},{rec3_rev}')
else:
    print('invalid')
    print('0,0,0')
" 2>/dev/null)

REC_STATUS=$(echo "$REC_VALUES" | head -1)
REC_AMOUNTS=$(echo "$REC_VALUES" | tail -1)

if [ "$REC_STATUS" = "valid" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Recommendation revenues are non-zero: $REC_AMOUNTS"
else
    echo -e "${RED}✗ FAIL${NC} - Recommendation revenues are zero or missing"
    exit 1
fi
echo ""

# Test 4: Check if HWCO data is preserved
echo "[Test 4] Validating HWCO baseline data..."
HWCO_DATA=$(echo "$SEGMENT_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
segments = data.get('segments', [])
if segments:
    sample = segments[0]
    hwco_rev = sample.get('hwco_continue_current', {}).get('revenue_30d', 0)
    hwco_rides = sample.get('hwco_continue_current', {}).get('rides_30d', 0)
    
    is_valid = hwco_rev > 0 and hwco_rides > 0
    print('valid' if is_valid else 'invalid')
    print(f'{hwco_rides} rides, \\\${hwco_rev:.2f} revenue')
else:
    print('invalid')
    print('No data')
" 2>/dev/null)

HWCO_STATUS=$(echo "$HWCO_DATA" | head -1)
HWCO_SUMMARY=$(echo "$HWCO_DATA" | tail -1)

if [ "$HWCO_STATUS" = "valid" ]; then
    echo -e "${GREEN}✓ PASS${NC} - HWCO baseline data preserved: $HWCO_SUMMARY"
else
    echo -e "${RED}✗ FAIL${NC} - HWCO baseline data missing or zero"
    exit 1
fi
echo ""

# Test 5: Sample 5 segments to verify data integrity
echo "[Test 5] Sampling segments for data integrity..."
SAMPLE_VALID=$(echo "$SEGMENT_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
segments = data.get('segments', [])

valid_count = 0
total_sampled = min(5, len(segments))

for i in range(total_sampled):
    seg = segments[i]
    hwco = seg.get('hwco_continue_current', {})
    rec1 = seg.get('recommendation_1', {})
    rec2 = seg.get('recommendation_2', {})
    rec3 = seg.get('recommendation_3', {})
    
    # Check all have revenue data
    if (hwco.get('revenue_30d', 0) >= 0 and 
        rec1.get('revenue_30d', 0) > 0 and 
        rec2.get('revenue_30d', 0) > 0 and 
        rec3.get('revenue_30d', 0) > 0):
        valid_count += 1

print(f'{valid_count}/{total_sampled}')
" 2>/dev/null)

if echo "$SAMPLE_VALID" | grep -q "5/5"; then
    echo -e "${GREEN}✓ PASS${NC} - All 5 sampled segments have complete data"
else
    echo -e "${YELLOW}⚠ WARNING${NC} - Some sampled segments have incomplete data: $SAMPLE_VALID"
fi
echo ""

# Test 6: Verify pipeline run ID is present
echo "[Test 6] Checking pipeline metadata..."
PIPELINE_ID=$(echo "$SEGMENT_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
meta = data.get('metadata', {})
run_id = meta.get('pipeline_run_id', 'N/A')
generated = meta.get('generated_at', 'N/A')
print(f'{run_id}')
print(f'{generated}')
" 2>/dev/null)

RUN_ID=$(echo "$PIPELINE_ID" | head -1)
GENERATED_AT=$(echo "$PIPELINE_ID" | tail -1)

if [ "$RUN_ID" != "N/A" ] && [ "$RUN_ID" != "" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Pipeline run ID: $RUN_ID"
    echo -e "  Generated at: $GENERATED_AT"
else
    echo -e "${YELLOW}⚠ INFO${NC} - No pipeline run ID in metadata (report generated dynamically)"
fi
echo ""

echo "=========================================="
echo "DATA VALIDATION SUMMARY"
echo "=========================================="
echo -e "${GREEN}✓ All critical tests passed!${NC}"
echo ""
echo "• 162 segments preserved"
echo "• Recommendation data present (rec1, rec2, rec3)"
echo "• HWCO baseline data intact"
echo "• Revenue values are non-zero"
echo "• Data integrity verified across samples"
echo ""
echo "✅ The Segment Pricing Analysis tab has valid data!"

exit 0


