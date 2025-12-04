# Data Model Refactoring - Progress Tracker

## Summary
Major data model refactoring to:
1. Remove `pricing_tier` (use `pricing_model` exclusively)
2. Replace distance-based pricing with duration-based pricing
3. Add `segment_demand_profile` (calculated from driver/rider ratio)
4. Add numeric regressors to ML Prophet model

## Completed

### ✅ Phase 1: Pydantic Schemas Updated
**File**: `backend/app/models/schemas.py`

**Changes**:
- ❌ Removed: `pricing_tier`, `segment_avg_distance`, `segment_avg_price`
- ✅ Added: `segment_demand_profile`, `segment_avg_fcs_ride_duration`, `segment_avg_fcs_unit_price`, `segment_avg_riders_per_order`, `segment_avg_drivers_per_order`
- Updated: `HistoricalBaseline`, `ForecastPrediction`, `PriceBreakdown`, `OrderCreate`, `OrderResponse`, `SegmentScenario`

### ✅ Phase 2: Migration Script Created
**File**: `backend/migrate_data_model.py`

**Capabilities**:
- Migrates 5 MongoDB collections: `historical_rides`, `competitor_prices`, `orders`, `pipeline_results`, `pricing_strategies`
- Calculates `segment_demand_profile` from driver/rider ratio:
  - < 34%: HIGH (low supply, high demand)
  - 34-67%: MEDIUM
  - >= 67%: LOW (high supply, low demand)
- Calculates `Historical_Unit_Price` = price / duration
- Removes deprecated fields
- Includes verification step

### ✅ Phase 3: ML Prophet Model Updated (Partial)
**File**: `backend/app/forecasting_ml.py`

**Changes**:
- ✅ Added 4 numeric regressors (lines 437-467):
  - `num_riders` (Number_Of_Riders)
  - `num_drivers` (Number_of_Drivers)
  - `ride_duration` (Expected_Ride_Duration)
  - `unit_price` (Historical_Unit_Price)
- ✅ Updated regressor collection logic (line 515)
- 🔄 **PENDING**: Update forecast output to include new metrics

## In Progress

### 🔄 Phase 4: Forecasting Agent
**File**: `backend/app/agents/forecasting.py`

**TODO**:
- Update `generate_multidimensional_forecast()` function (line 314+)
- Calculate `segment_demand_profile` from forecasted riders/drivers
- Return new field structure with duration/unit_price metrics
- Use `pricing_model` instead of `pricing_tier`

## Pending

### Phase 5: Analysis Agent
**File**: `backend/app/agents/analysis.py`
- Update `generate_and_rank_pricing_rules()`
- Update `calculate_segment_estimate()`
- Use `pricing_model`, calculate new metrics

### Phase 6: Recommendation Agent
**File**: `backend/app/agents/recommendation.py`
- Update `generate_strategic_recommendations()`
- Use forecasted unit_price and duration
- Calculate `new_total_price = unit_price × duration × multiplier`

### Phase 7: Pricing Engine
**File**: `backend/app/pricing_engine.py`
- Use `pricing_model` exclusively
- Calculate `estimated_price = segment_avg_fcs_unit_price × segment_avg_fcs_ride_duration`

### Phase 8: Orders Router
**File**: `backend/app/routers/orders.py`
- Remove old fields, add new fields
- Update estimated_price calculation

### Phase 9: Report Generator
**File**: `backend/app/utils/report_generator.py`
- Replace distance/price columns with duration/unit_price
- Calculate revenue = rides × duration × unit_price

### Phase 10: Pipeline Orchestrator
**File**: `backend/app/pipeline_orchestrator.py`
- Ensure data transformations use new field structure

### Phase 11-12: Tests
- Create comprehensive unit tests
- Create end-to-end integration test

### Phase 13-15: Execution
- Backup MongoDB and run migration
- Clear cache and restart
- Run tests iteratively until 100% pass rate

## Field Mapping Reference

### Old → New
- `pricing_tier` → `pricing_model` (just rename, same values)
- `segment_avg_distance` → `segment_avg_fcs_ride_duration` (miles → minutes)
- `segment_avg_price` → `segment_avg_fcs_unit_price` (total price → price per minute)
- N/A → `segment_demand_profile` (NEW: HIGH/MEDIUM/LOW)
- N/A → `segment_avg_riders_per_order` (NEW: from Number_Of_Riders)
- N/A → `segment_avg_drivers_per_order` (NEW: from Number_of_Drivers)

### Calculation Logic
```python
# Unit price
unit_price = price / duration

# Estimated price
estimated_price = unit_price × duration

# Demand profile
driver_ratio = (drivers / riders) * 100
if driver_ratio < 34: "HIGH"
elif driver_ratio < 67: "MEDIUM"
else: "LOW"

# Revenue
revenue = rides × duration × unit_price
```

## Next Steps
1. Complete Phase 4: Forecasting Agent updates
2. Continue through Phases 5-10
3. Create comprehensive tests
4. Execute migration and verify
