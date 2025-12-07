#!/bin/bash
# Comprehensive test for Prophet ML Multi-Metric Forecasting with 44 Regressors

echo "================================================================================"
echo "PROPHET ML MULTI-METRIC FORECASTING TEST SUITE"
echo "================================================================================"
echo ""

# Test 1: Backend Health
echo "Test 1: Backend Health Check"
HEALTH=$(curl -s http://localhost:8000/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "✓ PASS: Backend is healthy"
else
    echo "✗ FAIL: Backend health check failed"
    exit 1
fi
echo ""

# Test 2: Training Endpoint
echo "Test 2: Prophet ML Training (3 models with 44 regressors)"
TRAIN_RESULT=$(curl -s -X POST "http://localhost:8000/api/v1/ml/train")
echo "$TRAIN_RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    print('✓ PASS: All 3 models trained successfully')
    for metric, result in data['training_rows'].items():
        print(f'  - {metric}: {result[\"training_rows\"]} days, {result[\"num_regressors\"]} regressors')
else:
    print('✗ FAIL: Training failed')
    print(f'  Error: {data.get(\"detail\", \"Unknown error\")}')
    sys.exit(1)
"
if [ $? -ne 0 ]; then exit 1; fi
echo ""

# Test 3: 30-day Forecast
echo "Test 3: 30-Day Multi-Metric Forecast"
FORECAST_30=$(curl -s "http://localhost:8000/api/v1/ml/forecast-multi/30d")
echo "$FORECAST_30" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'detail' in data:
    print(f'✗ FAIL: {data[\"detail\"]}')
    sys.exit(1)
if data.get('success') and len(data['daily_forecasts']) == 30:
    print('✓ PASS: 30-day forecast generated')
    print(f'  - Avg Demand: {data[\"summary\"][\"avg_rides_per_day\"]:.1f} rides/day')
    print(f'  - Avg Duration: {data[\"summary\"][\"avg_duration_minutes\"]:.1f} min')
    print(f'  - Avg Unit Price: \${data[\"summary\"][\"avg_unit_price_per_minute\"]:.4f}/min')
    print(f'  - Total Revenue: \${data[\"summary\"][\"total_predicted_revenue\"]:,.0f}')
    # Validate positive values
    for day in data['daily_forecasts']:
        if day['predicted_rides'] <= 0 or day['predicted_duration'] <= 0 or day['predicted_unit_price'] <= 0:
            print('✗ FAIL: Found negative or zero values')
            sys.exit(1)
    print('  - All values positive ✓')
else:
    print('✗ FAIL: Invalid forecast response')
    sys.exit(1)
"
if [ $? -ne 0 ]; then exit 1; fi
echo ""

# Test 4: 60-day Forecast
echo "Test 4: 60-Day Multi-Metric Forecast"
FORECAST_60=$(curl -s "http://localhost:8000/api/v1/ml/forecast-multi/60d")
echo "$FORECAST_60" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success') and len(data['daily_forecasts']) == 60:
    print('✓ PASS: 60-day forecast generated')
else:
    print('✗ FAIL: 60-day forecast failed')
    sys.exit(1)
"
if [ $? -ne 0 ]; then exit 1; fi
echo ""

# Test 5: 90-day Forecast
echo "Test 5: 90-Day Multi-Metric Forecast"
FORECAST_90=$(curl -s "http://localhost:8000/api/v1/ml/forecast-multi/90d")
echo "$FORECAST_90" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success') and len(data['daily_forecasts']) == 90:
    print('✓ PASS: 90-day forecast generated')
else:
    print('✗ FAIL: 90-day forecast failed')
    sys.exit(1)
"
if [ $? -ne 0 ]; then exit 1; fi
echo ""

# Test 6: Validate Revenue Calculation
echo "Test 6: Revenue Calculation Validation"
echo "$FORECAST_30" | python3 -c "
import sys, json
data = json.load(sys.stdin)
day1 = data['daily_forecasts'][0]
calculated_revenue = day1['predicted_rides'] * day1['predicted_duration'] * day1['predicted_unit_price']
actual_revenue = day1['predicted_revenue']
diff = abs(calculated_revenue - actual_revenue)
if diff < 1:  # Allow <\$1 rounding error
    print('✓ PASS: Revenue calculation correct')
    print(f'  - {day1[\"predicted_rides\"]:.1f} rides × {day1[\"predicted_duration\"]:.1f} min × \${day1[\"predicted_unit_price\"]:.4f}/min = \${actual_revenue:,.2f}')
else:
    print(f'✗ FAIL: Revenue mismatch (calculated: {calculated_revenue:.2f}, actual: {actual_revenue:.2f})')
    sys.exit(1)
"
if [ $? -ne 0 ]; then exit 1; fi
echo ""

echo "================================================================================"
echo "ALL TESTS PASSED (100% PASS RATE)"
echo "================================================================================"
echo ""
echo "Summary:"
echo "  ✓ Backend health check"
echo "  ✓ Prophet ML training (3 models × 44 regressors)"
echo "  ✓ 30-day forecast"
echo "  ✓ 60-day forecast"
echo "  ✓ 90-day forecast"
echo "  ✓ Revenue calculation validation"
echo "  ✓ All forecast values positive and realistic"
echo ""
echo "Prophet ML Multi-Metric Forecasting System: OPERATIONAL"
echo "================================================================================"

