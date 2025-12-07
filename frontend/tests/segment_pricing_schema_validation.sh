#!/bin/bash

# =============================================================================
# Data Schema Validation Test
# =============================================================================
# Validates that all data fields used in the component exist in API responses
# =============================================================================

echo "=========================================="
echo "DATA SCHEMA VALIDATION TEST"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKEND_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}"
PASS_COUNT=0
FAIL_COUNT=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC} - $2"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "${RED}✗ FAIL${NC} - $2"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

echo "=== Test 1: Segment Report Structure ==="
echo ""

SEGMENT_VALIDATION=$(curl -s "$BACKEND_URL/api/v1/reports/segment-dynamic-pricing-analysis" | python3 -c "
import sys, json
data = json.load(sys.stdin)

# Required top-level fields
required_metadata = ['report_type', 'generated_at', 'total_segments']
required_segment_keys = ['segment', 'hwco_continue_current', 'lyft_continue_current', 
                         'recommendation_1', 'recommendation_2', 'recommendation_3']

# Required nested fields
required_segment_fields = ['location_category', 'loyalty_tier', 'vehicle_type', 
                           'demand_profile', 'pricing_model']
required_scenario_fields = ['rides_30d', 'unit_price', 'duration_minutes', 
                            'revenue_30d', 'explanation']

errors = []

# Check metadata
meta = data.get('metadata', {})
for field in required_metadata:
    if field not in meta:
        errors.append(f'Missing metadata field: {field}')

# Check segments
segments = data.get('segments', [])
if not segments:
    errors.append('No segments found in response')
else:
    sample = segments[0]
    
    # Check top-level keys
    for key in required_segment_keys:
        if key not in sample:
            errors.append(f'Missing segment key: {key}')
    
    # Check segment fields
    if 'segment' in sample:
        for field in required_segment_fields:
            if field not in sample['segment']:
                errors.append(f'Missing segment.{field}')
    
    # Check scenario fields (hwco, lyft, rec1, rec2, rec3)
    for scenario_key in ['hwco_continue_current', 'lyft_continue_current', 
                         'recommendation_1', 'recommendation_2', 'recommendation_3']:
        if scenario_key in sample:
            for field in required_scenario_fields:
                if field not in sample[scenario_key]:
                    errors.append(f'Missing {scenario_key}.{field}')

if errors:
    print('FAIL')
    for error in errors:
        print(error)
else:
    print('PASS')
    print('All segment report fields valid')
" 2>&1)

if echo "$SEGMENT_VALIDATION" | head -1 | grep -q "PASS"; then
    test_result 0 "Segment Report Schema"
    echo "$SEGMENT_VALIDATION" | tail -n +2 | sed 's/^/  └─ /'
else
    test_result 1 "Segment Report Schema"
    echo "$SEGMENT_VALIDATION" | tail -n +2 | sed 's/^/  └─ /'
fi
echo ""

echo "=== Test 2: Business Objectives Structure ==="
echo ""

OBJECTIVES_VALIDATION=$(curl -s "$BACKEND_URL/api/v1/analytics/pricing-strategies?filter_by=business_objectives" | python3 -c "
import sys, json
data = json.load(sys.stdin)

required_fields = ['name', 'objective', 'target', 'metric', 'priority']
errors = []

strategies = data.get('strategies', [])
if not strategies:
    errors.append('No strategies found')
else:
    # Check objectives
    objectives = [s for s in strategies if s.get('category') == 'business_objectives']
    if not objectives:
        errors.append('No business objectives found (category=business_objectives)')
    else:
        sample = objectives[0]
        for field in required_fields:
            if field not in sample:
                errors.append(f'Missing field: {field}')

if errors:
    print('FAIL')
    for error in errors:
        print(error)
else:
    print('PASS')
    print(f'Found {len(objectives)} objectives with all required fields')
" 2>&1)

if echo "$OBJECTIVES_VALIDATION" | head -1 | grep -q "PASS"; then
    test_result 0 "Business Objectives Schema"
    echo "$OBJECTIVES_VALIDATION" | tail -n +2 | sed 's/^/  └─ /'
else
    test_result 1 "Business Objectives Schema"
    echo "$OBJECTIVES_VALIDATION" | tail -n +2 | sed 's/^/  └─ /'
fi
echo ""

echo "=== Test 3: Component Interface Matching ==="
echo ""

# Test that component transformation matches API structure
TRANSFORM_TEST=$(curl -s "$BACKEND_URL/api/v1/reports/segment-dynamic-pricing-analysis" | python3 -c "
import sys, json
data = json.load(sys.stdin)

segments = data.get('segments', [])
if not segments:
    print('FAIL')
    print('No segments to validate')
    sys.exit(0)

sample = segments[0]

# Fields the component expects after transformation
expected_flat_fields = [
    'location_category', 'loyalty_tier', 'vehicle_type', 'demand_profile', 'pricing_model',
    'hwco_rides_30d', 'hwco_unit_price', 'hwco_duration_minutes', 'hwco_revenue_30d', 'hwco_explanation',
    'lyft_rides_30d', 'lyft_unit_price', 'lyft_duration_minutes', 'lyft_revenue_30d', 'lyft_explanation',
    'rec1_rides_30d', 'rec1_unit_price', 'rec1_duration_minutes', 'rec1_revenue_30d', 'rec1_explanation',
    'rec2_rides_30d', 'rec2_unit_price', 'rec2_duration_minutes', 'rec2_revenue_30d', 'rec2_explanation',
    'rec3_rides_30d', 'rec3_unit_price', 'rec3_duration_minutes', 'rec3_revenue_30d', 'rec3_explanation'
]

# Simulate transformation
transformed = {}
errors = []

try:
    # Transform segment fields
    for field in ['location_category', 'loyalty_tier', 'vehicle_type', 'demand_profile', 'pricing_model']:
        transformed[field] = sample['segment'][field]
    
    # Transform hwco fields
    for field in ['rides_30d', 'unit_price', 'duration_minutes', 'revenue_30d', 'explanation']:
        transformed[f'hwco_{field}'] = sample['hwco_continue_current'][field]
    
    # Transform lyft fields
    for field in ['rides_30d', 'unit_price', 'duration_minutes', 'revenue_30d', 'explanation']:
        transformed[f'lyft_{field}'] = sample['lyft_continue_current'][field]
    
    # Transform recommendation fields
    for i in range(1, 4):
        for field in ['rides_30d', 'unit_price', 'duration_minutes', 'revenue_30d', 'explanation']:
            transformed[f'rec{i}_{field}'] = sample[f'recommendation_{i}'][field]
    
    # Verify all expected fields were populated
    for field in expected_flat_fields:
        if field not in transformed:
            errors.append(f'Failed to transform: {field}')
    
    if errors:
        print('FAIL')
        for error in errors:
            print(error)
    else:
        print('PASS')
        print(f'Successfully transformed all {len(expected_flat_fields)} fields')
        
except KeyError as e:
    print('FAIL')
    print(f'Missing key during transformation: {e}')
except Exception as e:
    print('FAIL')
    print(f'Transformation error: {e}')
" 2>&1)

if echo "$TRANSFORM_TEST" | head -1 | grep -q "PASS"; then
    test_result 0 "Component Transformation"
    echo "$TRANSFORM_TEST" | tail -n +2 | sed 's/^/  └─ /'
else
    test_result 1 "Component Transformation"
    echo "$TRANSFORM_TEST" | tail -n +2 | sed 's/^/  └─ /'
fi
echo ""

echo "=== Test 4: Recommendations Data Source ==="
echo ""

# Verify recommendations come from valid pipeline results
RECS_VALIDATION=$(curl -s "$BACKEND_URL/api/v1/analytics/pricing-strategies?filter_by=pipeline_results&include_pipeline_data=true" | python3 -c "
import sys, json
data = json.load(sys.stdin)

# The component loads recommendations from pipeline data
# Verify the endpoint returns valid data structure

if 'timestamp' in data and 'filter_applied' in data:
    print('PASS')
    print('Recommendations endpoint returns valid response')
    print(f'Filter applied: {data.get(\"filter_applied\")}')
else:
    print('FAIL')
    print('Invalid response structure')
" 2>&1)

if echo "$RECS_VALIDATION" | head -1 | grep -q "PASS"; then
    test_result 0 "Recommendations API"
    echo "$RECS_VALIDATION" | tail -n +2 | sed 's/^/  └─ /'
else
    test_result 1 "Recommendations API"
    echo "$RECS_VALIDATION" | tail -n +2 | sed 's/^/  └─ /'
fi
echo ""

echo "=========================================="
echo "SCHEMA VALIDATION SUMMARY"
echo "=========================================="
echo -e "Passed: ${GREEN}$PASS_COUNT${NC}"
echo -e "Failed: ${RED}$FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ ALL SCHEMA VALIDATIONS PASSED!${NC}"
    echo ""
    echo "All component data fields match MongoDB collections:"
    echo "  • Segment report structure validated"
    echo "  • Business objectives fields validated"
    echo "  • Component transformation verified"
    echo "  • Recommendations API validated"
    echo ""
    exit 0
else
    echo -e "${RED}✗ SOME VALIDATIONS FAILED${NC}"
    echo "Please review the errors above."
    echo ""
    exit 1
fi


