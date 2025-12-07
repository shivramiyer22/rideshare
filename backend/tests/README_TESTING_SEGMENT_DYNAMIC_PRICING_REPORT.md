# Testing Guide: Segment Dynamic Pricing Report

## Overview
This document describes the comprehensive test suite for the Segment Dynamic Pricing Report functionality, which provides detailed per-segment forecast analytics including historical baselines, competitor baselines, and three strategic recommendations.

## Test File
**Location:** `backend/tests/test_segment_dynamic_pricing_report.py`

## Test Coverage

### 1. **Report Generator - Full Report Generation**
**Test:** `test_generate_segment_dynamic_pricing_report_full()`

**What it tests:**
- Complete report generation with all 162 segments
- Per-segment impacts from all 3 recommendations
- Historical baseline (HWCO Continue Current) calculation
- Competitor baseline (Lyft Continue Current) calculation
- Proper data structure and metadata

**Expected behavior:**
- Returns report with metadata and segments array
- Each segment contains 5 dimensions + 5 scenarios (HWCO, Lyft, Rec1, Rec2, Rec3)
- All numeric fields are properly calculated

### 2. **Report Generator - CSV Conversion**
**Test:** `test_convert_report_to_csv()`

**What it tests:**
- Conversion of JSON report to CSV format
- CSV header row contains all 25 columns
- Data rows properly formatted
- All segment dimensions and scenarios included

**Expected behavior:**
- Returns valid CSV string
- Header: 5 dimension columns + 20 scenario data columns (4 per scenario × 5 scenarios)
- Data rows match segment count

### 3. **API Endpoint - JSON Format**
**Test:** `test_api_segment_dynamic_pricing_json()`

**What it tests:**
- `GET /api/v1/reports/segment-dynamic-pricing-analysis?format=json` endpoint
- JSON response structure
- Proper HTTP status codes

**Expected behavior:**
- 200 OK status
- JSON response with metadata and segments
- Content-Type: application/json

### 4. **API Endpoint - CSV Format**
**Test:** `test_api_segment_dynamic_pricing_csv()`

**What it tests:**
- `GET /api/v1/reports/segment-dynamic-pricing-analysis?format=csv` endpoint
- CSV file download
- Proper HTTP headers for file attachment

**Expected behavior:**
- 200 OK status
- Content-Type: text/csv
- Content-Disposition header with filename
- CSV content in response body

### 5. **Competitor Segment Baseline Tool**
**Test:** `test_get_competitor_segment_baseline()`

**What it tests:**
- `get_competitor_segment_baseline()` tool functionality
- Query Lyft pricing for specific segment dimensions
- Calculate average price, distance, and price per mile
- Proper filtering by segment dimensions

**Expected behavior:**
- Returns JSON with segment, competitor, and baseline fields
- Baseline includes avg_price, avg_distance, price_per_mile, ride_count
- Explanation string describes the baseline

### 6. **Chatbot Tool - Query Segment Report**
**Test:** `test_query_segment_dynamic_pricing_report_tool()`

**What it tests:**
- `query_segment_dynamic_pricing_report()` chatbot tool
- Filtering by segment dimensions
- Returning all segments when no filter applied
- Returning filtered segments when dimensions provided

**Expected behavior:**
- Without filters: Returns all segments
- With filters: Returns only matching segments
- Result includes metadata, filter_applied, segments_returned, and segments array

### 7. **API Endpoint - Summary**
**Test:** `test_api_segment_dynamic_pricing_summary()`

**What it tests:**
- `GET /api/v1/reports/segment-dynamic-pricing-analysis/summary` endpoint
- Aggregate revenue calculations across all segments
- Revenue uplift percentages (Rec1 vs HWCO, Rec2 vs HWCO, Rec3 vs HWCO)

**Expected behavior:**
- 200 OK status
- Metadata with report info
- aggregate_revenue_30d for all 5 scenarios
- revenue_uplift percentages showing % change from HWCO baseline

## Running the Tests

### Run all segment report tests:
```bash
cd backend
pytest tests/test_segment_dynamic_pricing_report.py -v
```

### Run specific test:
```bash
pytest tests/test_segment_dynamic_pricing_report.py::test_api_segment_dynamic_pricing_json -v
```

### Run with coverage:
```bash
pytest tests/test_segment_dynamic_pricing_report.py --cov=app.utils.report_generator --cov=app.routers.reports -v
```

## API Endpoints Summary

### 1. Get Full Report (JSON)
```bash
curl -X GET "http://localhost:8000/api/v1/reports/segment-dynamic-pricing-analysis?format=json"
```

### 2. Get Full Report (CSV)
```bash
curl -X GET "http://localhost:8000/api/v1/reports/segment-dynamic-pricing-analysis?format=csv" --output segment_report.csv
```

### 3. Get Summary Only
```bash
curl -X GET "http://localhost:8000/api/v1/reports/segment-dynamic-pricing-analysis/summary"
```

### 4. Get Specific Pipeline Result
```bash
curl -X GET "http://localhost:8000/api/v1/reports/segment-dynamic-pricing-analysis?pipeline_result_id=<id>&format=json"
```

## Chatbot Query Examples

Users can query the segment dynamic pricing report through the chatbot:

1. **"Show me the segment pricing report for Urban Gold Premium segments"**
   - Routes to Analysis Agent
   - Calls `query_segment_dynamic_pricing_report` tool with filters
   - Returns filtered segment data

2. **"What are the forecasted prices for all segments?"**
   - Routes to Analysis Agent
   - Calls `query_segment_dynamic_pricing_report` tool without filters
   - Returns all 162 segments

3. **"Compare HWCO vs Lyft pricing for Suburban segments"**
   - Routes to Analysis Agent
   - Calls `query_segment_dynamic_pricing_report` tool with location_category filter
   - Returns comparison data for matching segments

## Data Flow

1. **Pipeline Execution** → Generates per_segment_impacts for 3 recommendations (162 segments × 3 = 486 records)
2. **Storage** → Stores in both `pipeline_results` and `pricing_strategies` MongoDB collections
3. **Report Generation** → `generate_segment_dynamic_pricing_report()` combines pipeline data with historical/competitor baselines
4. **API Access** → Endpoints serve report in JSON or CSV format
5. **Chatbot Access** → `query_segment_dynamic_pricing_report` tool enables natural language queries

## Troubleshooting

### Test Failures

**Issue:** Tests fail with "No pipeline results found"
**Solution:** Ensure mock data includes per_segment_impacts in pipeline_results

**Issue:** CSV conversion fails
**Solution:** Verify all segment records have complete structure with all 5 scenarios

**Issue:** API returns 404
**Solution:** Check that reports router is registered in main.py with correct prefix

### Common Errors

**Error:** `KeyError: 'per_segment_impacts'`
**Fix:** Recommendation agent must be updated to return per_segment_impacts field

**Error:** `AttributeError: 'NoneType' object has no attribute 'get'`
**Fix:** Ensure pipeline_results collection has data before generating report

## Integration with Frontend

The frontend can use this API to:
1. Display interactive segment pricing dashboard
2. Allow filtering by segment dimensions
3. Show HWCO vs Lyft vs Recommendations comparison
4. Export data as CSV for offline analysis
5. Enable chatbot queries for specific segments

## Next Steps

After all tests pass:
1. Run manual API testing via Swagger UI at http://localhost:8000/docs
2. Test chatbot integration by asking segment pricing questions
3. Verify CSV download works in browser
4. Check frontend integration (if applicable)
5. Monitor MongoDB collections for proper per_segment_impacts storage

