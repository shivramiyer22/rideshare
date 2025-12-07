# Order Price Estimation API - Testing Documentation

## Overview

This document describes the test suite for the Order Price Estimation API, which enables frontend applications to preview ride prices before order creation and enhances order records with comprehensive pricing data.

## Test Coverage

### 1. Segment Analysis Tests (`TestSegmentAnalysis`)

**Purpose:** Validate the core segment analysis helper functions.

| Test Case | Description | Validates |
|-----------|-------------|-----------|
| `test_analyze_segment_historical_data` | Query historical rides for segment | Returns avg_price, avg_distance, avg_duration, sample_size |
| `test_get_segment_forecast_data` | Retrieve forecast predictions | Returns predicted_price_30d, predicted_demand_30d, forecast_confidence |
| `test_calculate_segment_estimate_without_trip_details` | Calculate estimate using segment average | Uses historical average when no trip details provided |
| `test_calculate_segment_estimate_with_trip_details` | Calculate estimate using PricingEngine | Uses PricingEngine for exact price when distance/duration provided |

**Key Validations:**
- Historical data aggregation (averages calculation)
- Forecast data retrieval from pipeline results
- Segment average fallback logic
- PricingEngine integration for exact pricing
- Explanation and assumptions generation

### 2. Estimate Endpoint Tests (`TestEstimateEndpoint`)

**Purpose:** Validate the `POST /orders/estimate` API endpoint.

| Test Case | Description | Expected Behavior |
|-----------|-------------|-------------------|
| `test_estimate_endpoint_without_trip_details` | Request estimate without distance/duration | Returns segment average with historical baseline |
| `test_estimate_endpoint_with_trip_details` | Request estimate with distance/duration | Returns PricingEngine calculation with detailed breakdown |

**API Endpoint:** `POST /api/v1/orders/estimate`

**Request Schema:**
```json
{
  "location_category": "Urban",
  "loyalty_tier": "Gold",
  "vehicle_type": "Premium",
  "pricing_model": "STANDARD",
  "distance": 10.5,        // Optional
  "duration": 25.0         // Optional
}
```

**Response Schema:**
```json
{
  "segment": { "location_category": "...", "loyalty_tier": "...", ... },
  "historical_baseline": { "avg_price": 45.23, "avg_distance": 10.2, ... },
  "forecast_prediction": { "predicted_price_30d": 46.50, ... },
  "estimated_price": 45.80,
  "price_breakdown": { "base_fare": 4.00, "distance_cost": 21.00, ... },
  "explanation": "Exact price calculated using PricingEngine...",
  "assumptions": ["Using PricingEngine with provided trip details"],
  "timestamp": "2025-12-03T10:30:00Z"
}
```

**Key Validations:**
- Endpoint returns 200 OK with valid request
- Response matches OrderEstimateResponse schema
- Estimated price is calculated correctly
- Explanation and assumptions are provided
- Price breakdown included when trip details provided

### 3. Enhanced Order Creation Tests (`TestEnhancedOrderCreation`)

**Purpose:** Validate the enhanced `POST /orders` endpoint stores computed fields.

| Test Case | Description | Expected Behavior |
|-----------|-------------|-------------------|
| `test_order_creation_with_computed_fields` | Create order with segment analysis | Order document includes segment_avg_price, segment_avg_distance, estimated_price, price_breakdown, pricing_explanation |

**API Endpoint:** `POST /api/v1/orders`

**Enhanced Request Schema:**
```json
{
  "user_id": "user123",
  "pickup_location": { "lat": 37.7749, "lng": -122.4194 },
  "dropoff_location": { "lat": 37.8049, "lng": -122.4094 },
  "location_category": "Urban",
  "loyalty_tier": "Gold",
  "vehicle_type": "Premium",
  "pricing_model": "STANDARD",
  "distance": 10.5,        // Optional
  "duration": 25.0,        // Optional
  "priority": "P2"
}
```

**Enhanced Response Schema:**
```json
{
  "id": "uuid-here",
  "user_id": "user123",
  "status": "PENDING",
  "location_category": "Urban",
  "loyalty_tier": "Gold",
  "vehicle_type": "Premium",
  "pricing_model": "STANDARD",
  "segment_avg_price": 42.50,
  "segment_avg_distance": 9.8,
  "estimated_price": 45.80,
  "price_breakdown": { "base_fare": 4.00, ... },
  "pricing_explanation": "Exact price calculated using PricingEngine...",
  "price": 45.80,
  "created_at": "...",
  "updated_at": "..."
}
```

**Key Validations:**
- Order created successfully with UUID
- All computed pricing fields stored in MongoDB
- segment_avg_price and segment_avg_distance populated
- estimated_price matches calculation
- price_breakdown stored if trip details provided
- pricing_explanation included

### 4. Chatbot Price Estimation Tests (`TestChatbotPriceEstimation`)

**Purpose:** Validate chatbot can handle price estimation queries.

| Test Case | Description | Expected Behavior |
|-----------|-------------|-------------------|
| `test_chatbot_estimate_query` | User asks "what would this cost?" | Pricing Agent uses estimate_ride_price tool, returns comprehensive estimate |
| `test_chatbot_estimate_with_trip_details` | User provides distance/duration | Returns exact price with breakdown |

**Example Queries:**
- "What would a Premium ride in Urban area cost for a Gold member?"
- "How much for an Economy ride in Suburban area?"
- "Price estimate for 15 miles, 30 minutes, Premium vehicle, Regular customer?"

**Chatbot Flow:**
1. User sends query to Orchestrator Agent
2. Orchestrator routes to Pricing Agent (based on "price" keyword)
3. Pricing Agent calls `estimate_ride_price` tool
4. Tool returns JSON with estimate
5. Pricing Agent formats response naturally
6. Orchestrator returns to user

**Key Validations:**
- estimate_ride_price tool exists in Pricing Agent
- Tool returns valid JSON response
- Response includes estimated_price and explanation
- Natural language explanation generated
- Pricing Agent accessible via chatbot

### 5. Edge Case Tests (`TestEdgeCases`)

**Purpose:** Validate error handling and fallback behavior.

| Test Case | Description | Expected Behavior |
|-----------|-------------|-------------------|
| `test_no_historical_data` | Segment with zero historical rides | Returns sample_size=0, avg_price=0.0, graceful fallback |
| `test_invalid_segment_dimensions` | Invalid pricing_model or other field | Returns fallback estimate or raises descriptive error |
| `test_missing_trip_details` | Estimate without distance/duration | Uses segment average, no price_breakdown |

**Edge Cases Covered:**
- New segments with no historical data
- Invalid segment dimension values
- Missing optional trip details
- Database connection failures
- PricingEngine errors

**Key Validations:**
- System doesn't crash on edge cases
- Graceful fallbacks to conservative estimates
- Clear error messages when validation fails
- Assumptions documented in response

## Test Execution

### Running Tests

```bash
# Navigate to backend directory
cd backend

# Run all order estimation tests
python tests/test_order_estimation.py

# Expected output: 13+ tests, 100% pass rate
```

### Test Results Format

```
================================================================================
ORDER PRICE ESTIMATION API - TEST SUITE
================================================================================

────────────────────────────────────────────────────────────────────────────────
Testing: Segment Analysis
────────────────────────────────────────────────────────────────────────────────

✓ Historical data analysis: 245 rides, avg_price=$42.35
✓ Forecast data retrieval: predicted_price=$43.20
✓ Segment estimate (no trip details): $42.35
  Explanation: Segment average price from 245 historical rides...
✓ Segment estimate (with trip details): $45.80
  Breakdown: base=4.00, distance=21.00, time=7.50

────────────────────────────────────────────────────────────────────────────────
Testing: Estimate Endpoint
────────────────────────────────────────────────────────────────────────────────

✓ Estimate endpoint (no trip details): $38.50
✓ Estimate endpoint (with trip details): $52.30

────────────────────────────────────────────────────────────────────────────────
Testing: Enhanced Order Creation
────────────────────────────────────────────────────────────────────────────────

✓ Order creation with computed fields: estimated_price=$35.20
  Segment avg: $34.80

────────────────────────────────────────────────────────────────────────────────
Testing: Chatbot Price Estimation
────────────────────────────────────────────────────────────────────────────────

✓ Chatbot estimate query: $47.50
  Explanation: Exact price calculated using PricingEngine: $47.50 | Based on...
✓ Chatbot estimate with trip details: $55.20

────────────────────────────────────────────────────────────────────────────────
Testing: Edge Cases
────────────────────────────────────────────────────────────────────────────────

✓ No historical data handled gracefully: sample_size=0
✓ Invalid segment handled with fallback: $15.00
✓ Missing trip details uses segment average: $42.35

================================================================================
TEST SUMMARY: 13/13 tests passed
================================================================================
✓ ALL TESTS PASSED
```

## API Testing via Swagger UI

### Testing POST /orders/estimate

1. Navigate to `http://localhost:8000/docs`
2. Expand `POST /api/v1/orders/estimate`
3. Click "Try it out"
4. Enter request body:

```json
{
  "location_category": "Urban",
  "loyalty_tier": "Gold",
  "vehicle_type": "Premium",
  "pricing_model": "STANDARD",
  "distance": 10.5,
  "duration": 25.0
}
```

5. Click "Execute"
6. Verify 200 OK response with estimate

### Testing Enhanced POST /orders

1. Expand `POST /api/v1/orders`
2. Enter request body with segment dimensions:

```json
{
  "user_id": "test_user",
  "pickup_location": {"lat": 37.7749, "lng": -122.4194},
  "dropoff_location": {"lat": 37.8049, "lng": -122.4094},
  "location_category": "Urban",
  "loyalty_tier": "Gold",
  "vehicle_type": "Premium",
  "pricing_model": "STANDARD",
  "distance": 10.5,
  "duration": 25.0
}
```

3. Verify order created with computed fields

### Testing Chatbot Price Estimation

1. Expand `POST /api/v1/chatbot/chat`
2. Enter message:

```json
{
  "message": "What would a Premium ride in Urban area cost for a Gold member?",
  "context": {}
}
```

3. Verify chatbot routes to Pricing Agent and returns estimate

## Performance Benchmarks

Expected performance for each operation:

| Operation | Average Time | P95 Time | Database Queries |
|-----------|--------------|----------|------------------|
| POST /orders/estimate (no trip details) | 50-100ms | 200ms | 2 (historical + forecast) |
| POST /orders/estimate (with trip details) | 80-150ms | 250ms | 2 + PricingEngine |
| POST /orders (enhanced) | 100-200ms | 300ms | 2 + MongoDB insert + Redis queue |
| Chatbot price estimation | 500-1000ms | 2000ms | Agent routing + tool execution |

## Data Requirements

For meaningful test results, the system should have:

- **Historical Rides:** 300+ rides across multiple segments
- **Competitor Prices:** 100+ competitor ride records
- **Pipeline Results:** At least one completed forecast run in `pricing_strategies` collection
- **MongoDB Connection:** Active connection to rideshare database
- **OpenAI API Key:** Valid key for GPT-4o-mini (chatbot tests)

## Known Limitations

1. **Forecast Data:** Tests may return `predicted_price_30d=0` if pipeline hasn't run yet
2. **Historical Data:** New segments with no rides return conservative fallback estimates
3. **Chatbot Tests:** Require OpenAI API key; will fail gracefully if missing
4. **Async Operations:** Tests use synchronous calls to segment_analysis functions

## Troubleshooting

### Test Failures

**"No historical data found"**
- Solution: Upload historical rides data via POST /api/v1/upload/historical-rides
- Minimum: 100+ rides across common segments

**"Forecast confidence: None"**
- Solution: Run pipeline trigger via POST /api/v1/pipeline/trigger
- Wait for pipeline completion (~30-60 seconds)

**"PricingEngine failed, using segment average"**
- Solution: Verify PricingEngine initialization in segment_analysis.py
- Check PricingEngine handles all pricing models correctly

**"Chatbot agent not initialized"**
- Solution: Set OPENAI_API_KEY environment variable
- Verify .env file in project root

## Next Steps

After all tests pass:

1. **Frontend Integration:** Use POST /orders/estimate endpoint for price preview
2. **Order Creation:** Use enhanced POST /orders with segment dimensions
3. **Chatbot Queries:** Test natural language price estimation queries
4. **Performance Monitoring:** Track API response times in production
5. **Data Quality:** Monitor segment coverage and forecast accuracy

