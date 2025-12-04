# Data Model Refactoring Implementation Guide

## Executive Summary

**STATUS**: Core infrastructure updates COMPLETED (Phases 1-3)
**REMAINING**: Agent logic updates, testing, and execution (Phases 4-15)

### What's Been Done ✅

1. **Pydantic Schemas** - All schemas updated with new field structure
2. **Migration Script** - Complete migration script for 5 MongoDB collections
3. **ML Prophet Model** - 4 numeric regressors added to training

### Critical Next Steps

Before running the migration or tests, the following agent code must be updated:

## Phase 4: Forecasting Agent (CRITICAL)

**File**: `backend/app/agents/forecasting.py`

**Location**: Lines 314-600+ (function `generate_multidimensional_forecast`)

**Required Changes**:

### 1. Update segment dimensions query (line 373-383)
Current code filters by `Demand_Profile` from MongoDB.
**NEW**: Calculate `segment_demand_profile` dynamically from `Number_of_Drivers` and `Number_Of_Riders`

```python
# OLD:
segment_rides = [
    r for r in all_rides
    if r.get("Demand_Profile", "").upper() == demand.upper()
]

# NEW:
def calculate_demand_profile(ride):
    riders = ride.get("Number_Of_Riders", 0)
    drivers = ride.get("Number_of_Drivers", 0)
    if riders == 0:
        return "MEDIUM"
    driver_ratio = (drivers / riders) * 100
    if driver_ratio < 34:
        return "HIGH"
    elif driver_ratio < 67:
        return "MEDIUM"
    else:
        return "LOW"

segment_rides = [
    r for r in all_rides
    if r.get("Customer_Loyalty_Status") == loyalty
    and r.get("Vehicle_Type") == vehicle
    and calculate_demand_profile(r) == demand
    and r.get("Pricing_Model") == pricing  # Use Pricing_Model not pricing_tier
    and r.get("Location_Category") == location
]
```

### 2. Update forecast output structure (lines 399-500)
Change from distance/price to duration/unit_price:

```python
# Calculate historical averages with NEW fields
avg_duration = sum(r.get("Expected_Ride_Duration", 0) for r in segment_rides) / ride_count
total_price = sum(r.get("Historical_Cost_of_Ride", 0) for r in segment_rides)
avg_unit_price = (total_price / ride_count) / avg_duration if avg_duration > 0 else 0

avg_riders = sum(r.get("Number_Of_Riders", 0) for r in segment_rides) / ride_count
avg_drivers = sum(r.get("Number_of_Drivers", 0) for r in segment_rides) / ride_count

# Calculate segment_demand_profile
segment_demand_profile = calculate_demand_profile({
    "Number_Of_Riders": avg_riders,
    "Number_of_Drivers": avg_drivers
})

# Updated output structure
segmented_forecasts.append({
    "dimensions": {
        "loyalty_tier": loyalty,
        "vehicle_type": vehicle,
        "demand_profile": segment_demand_profile,  # Calculated, not from DB
        "pricing_model": pricing,  # NOT pricing_tier
        "location": location
    },
    "baseline_metrics": {
        "historical_rides": ride_count,
        "segment_avg_fcs_unit_price": round(avg_unit_price, 2),
        "segment_avg_fcs_ride_duration": round(avg_duration, 2),
        "segment_avg_riders_per_order": round(avg_riders, 2),
        "segment_avg_drivers_per_order": round(avg_drivers, 2),
        "segment_demand_profile": segment_demand_profile
    },
    "forecast_30d": {
        "predicted_rides": demand_forecast,
        "predicted_unit_price": price_forecast / avg_duration if avg_duration > 0 else price_forecast,
        "predicted_ride_duration": avg_duration,  # For now, use historical avg
        "predicted_revenue": revenue_forecast,
        "segment_demand_profile": segment_demand_profile
    }
})
```

## Phase 5: Analysis Agent

**File**: `backend/app/agents/analysis.py`

**Key Functions to Update**:

### 1. `generate_and_rank_pricing_rules()` (around line 150-400)

```python
# Query using pricing_model not pricing_tier
hwco_data = list(db["historical_rides"].find({
    "Pricing_Model": {"$in": ["CONTRACTED", "STANDARD", "CUSTOM"]}
}))

# Calculate segment_demand_profile when analyzing segments
for doc in hwco_data:
    riders = doc.get("Number_Of_Riders", 0)
    drivers = doc.get("Number_of_Drivers", 0)
    duration = doc.get("Expected_Ride_Duration", 0)
    price = doc.get("Historical_Cost_of_Ride", 0)
    
    # Calculate unit_price
    doc["unit_price"] = price / duration if duration > 0 else 0
    
    # Calculate demand_profile
    if riders > 0:
        driver_ratio = (drivers / riders) * 100
        if driver_ratio < 34:
            doc["segment_demand_profile"] = "HIGH"
        elif driver_ratio < 67:
            doc["segment_demand_profile"] = "MEDIUM"
        else:
            doc["segment_demand_profile"] = "LOW"
    else:
        doc["segment_demand_profile"] = "MEDIUM"
```

### 2. `calculate_segment_estimate()` (around line 600-700)

```python
# Use pricing_model in query
query = {
    "Location_Category": location_category,
    "Customer_Loyalty_Status": loyalty_tier,
    "Vehicle_Type": vehicle_type,
    "Pricing_Model": pricing_model  # NOT pricing_tier
}

# Calculate new metrics
total_duration = sum(r.get("Expected_Ride_Duration", 0) for r in rides)
total_price = sum(r.get("Historical_Cost_of_Ride", 0) for r in rides)
total_riders = sum(r.get("Number_Of_Riders", 0) for r in rides)
total_drivers = sum(r.get("Number_of_Drivers", 0) for r in rides)

avg_duration = total_duration / count
avg_unit_price = (total_price / count) / avg_duration if avg_duration > 0 else 0
avg_riders = total_riders / count
avg_drivers = total_drivers / count

# Calculate demand_profile
driver_ratio = (avg_drivers / avg_riders) * 100 if avg_riders > 0 else 50
if driver_ratio < 34:
    segment_demand_profile = "HIGH"
elif driver_ratio < 67:
    segment_demand_profile = "MEDIUM"
else:
    segment_demand_profile = "LOW"

return {
    "segment_avg_fcs_unit_price": round(avg_unit_price, 2),
    "segment_avg_fcs_ride_duration": round(avg_duration, 2),
    "segment_avg_riders_per_order": round(avg_riders, 2),
    "segment_avg_drivers_per_order": round(avg_drivers, 2),
    "segment_demand_profile": segment_demand_profile,
    "sample_size": count
}
```

## Phase 6: Recommendation Agent

**File**: `backend/app/agents/recommendation.py`

**Function**: `generate_strategic_recommendations()` (around line 200-500)

**Key Change** - Per-segment impact calculation:

```python
# When calculating per_segment_impacts for each recommendation
for segment in forecast_list:
    baseline_unit_price = segment.get("baseline_metrics", {}).get("segment_avg_fcs_unit_price", 0)
    baseline_duration = segment.get("baseline_metrics", {}).get("segment_avg_fcs_ride_duration", 0)
    baseline_rides = segment.get("forecast_30d", {}).get("predicted_rides", 0)
    
    # Apply pricing rules to get new unit price
    combined_multiplier = 1.0
    for rule in applicable_rules:
        multiplier = rule.get("multiplier", 1.0)
        combined_multiplier *= multiplier
    
    new_unit_price = baseline_unit_price * combined_multiplier
    
    # Calculate new total price
    new_total_price = new_unit_price * baseline_duration
    
    # Calculate demand elasticity
    price_change_pct = ((new_unit_price - baseline_unit_price) / baseline_unit_price) * 100
    elasticity = get_elasticity(segment["dimensions"])
    demand_change_pct = -elasticity * price_change_pct
    new_rides = baseline_rides * (1 + demand_change_pct / 100)
    
    # Calculate revenues
    baseline_revenue = baseline_rides * baseline_duration * baseline_unit_price
    new_revenue = new_rides * baseline_duration * new_unit_price
    
    per_segment_impacts[rec_key].append({
        "segment": segment["dimensions"],
        "baseline": {
            "rides_30d": baseline_rides,
            "unit_price_per_minute": baseline_unit_price,
            "ride_duration_minutes": baseline_duration,
            "revenue_30d": baseline_revenue,
            "segment_demand_profile": segment["dimensions"]["demand_profile"]
        },
        "with_recommendation": {
            "rides_30d": new_rides,
            "unit_price_per_minute": new_unit_price,
            "ride_duration_minutes": baseline_duration,  # Duration stays same
            "revenue_30d": new_revenue,
            "segment_demand_profile": segment["dimensions"]["demand_profile"]
        },
        "applied_rules": [{"rule_id": r["id"], "multiplier": r["multiplier"]} for r in applicable_rules],
        "explanation": f"Applied {len(applicable_rules)} pricing rules..."
    })
```

## Phase 7: Pricing Engine

**File**: `backend/app/pricing_engine.py`

**Key Changes**:

```python
def calculate_price(self, order_details: Dict) -> Dict:
    # Get segment baseline
    segment_avg_fcs_unit_price = order_details.get("segment_avg_fcs_unit_price", 3.0)
    segment_avg_fcs_ride_duration = order_details.get("segment_avg_fcs_ride_duration", 20.0)
    pricing_model = order_details.get("pricing_model", "STANDARD")  # NOT pricing_tier
    
    # Get pricing rules using pricing_model
    rules = self._get_pricing_rules(
        location=order_details.get("location_category"),
        loyalty=order_details.get("loyalty_tier"),
        demand_profile=order_details.get("segment_demand_profile"),  # NEW
        pricing_model=pricing_model  # NOT pricing_tier
    )
    
    # Apply rules to unit price
    final_unit_price = segment_avg_fcs_unit_price
    for rule in rules:
        final_unit_price *= rule.get("multiplier", 1.0)
    
    # Calculate final price
    estimated_price = final_unit_price * segment_avg_fcs_ride_duration
    
    return {
        "estimated_price": round(estimated_price, 2),
        "breakdown": {
            "base_unit_price_per_minute": segment_avg_fcs_unit_price,
            "ride_duration_minutes": segment_avg_fcs_ride_duration,
            "applied_multipliers": [...],
            "final_unit_price_per_minute": final_unit_price,
            "final_price": estimated_price
        }
    }
```

## Phase 8: Orders Router

**File**: `backend/app/routers/orders.py`

```python
# In POST /orders endpoint
order_data = {
    "pricing_model": body.pricing_model,  # NOT pricing_tier
    "segment_avg_fcs_unit_price": segment_estimate.get("segment_avg_fcs_unit_price"),
    "segment_avg_fcs_ride_duration": segment_estimate.get("segment_avg_fcs_ride_duration"),
    "segment_avg_riders_per_order": segment_estimate.get("segment_avg_riders_per_order"),
    "segment_avg_drivers_per_order": segment_estimate.get("segment_avg_drivers_per_order"),
    "segment_demand_profile": segment_estimate.get("segment_demand_profile"),
    "estimated_price": pricing_result["estimated_price"]
}

# Remove: pricing_tier, segment_avg_distance, segment_avg_price
```

## Phase 9: Report Generator

**File**: `backend/app/utils/report_generator.py`

**CSV Columns Update** (around line 200-300):

```python
csv_columns = [
    "location_category",
    "loyalty_tier",
    "vehicle_type",
    "segment_demand_profile",  # NEW
    "pricing_model",
    "hwco_rides_30d",
    "hwco_unit_price_per_minute",  # CHANGED from avg_price
    "hwco_ride_duration_minutes",   # NEW
    "hwco_revenue_30d",
    "lyft_rides_30d",
    "lyft_unit_price_per_minute",  # CHANGED
    "lyft_ride_duration_minutes",   # NEW
    "lyft_revenue_30d",
    # ... recommendations ...
]

# Revenue calculation
revenue = rides * duration * unit_price  # NOT rides * price
```

## Execution Sequence

### Step 1: Run Migration Script

```bash
cd backend
python3 migrate_data_model.py
```

**Expected Output**:
- historical_rides: ~2000 documents updated
- competitor_prices: ~2000 documents updated
- orders: ~17 documents updated
- pipeline_results: skipped (will regenerate)
- pricing_strategies: skipped (will regenerate)

### Step 2: Clear Cache & Restart

```bash
python3 clear_backend_cache.py
./restart_backend.sh
```

### Step 3: Retrain ML Model

```bash
curl -X POST http://localhost:8000/api/v1/ml/train
```

**Wait for**: "Model trained successfully" response (may take 2-3 minutes)

### Step 4: Run Pipeline

```bash
curl -X POST http://localhost:8000/api/v1/pipeline/run
```

**Wait for**: All phases to complete (Analysis → Forecasting → Recommendations)

### Step 5: Generate Report

```bash
curl "http://localhost:8000/api/v1/reports/segment-dynamic-pricing-analysis?format=csv" -o report.csv
```

**Verify**: 162 rows (one per segment) with new columns

### Step 6: Validate Data

```bash
# Check orders API
curl http://localhost:8000/api/v1/orders

# Should see new fields:
# - segment_avg_fcs_unit_price
# - segment_avg_fcs_ride_duration
# - segment_demand_profile
# - NO pricing_tier, segment_avg_distance, segment_avg_price
```

## Testing Strategy

### Unit Tests (Create `backend/tests/test_data_model_refactoring.py`)

```python
def test_demand_profile_calculation():
    """Test HIGH/MEDIUM/LOW demand profile calculation"""
    # HIGH: drivers < 34% of riders
    assert calculate_demand_profile(10, 30) == "HIGH"  # 33%
    
    # MEDIUM: drivers 34-67% of riders
    assert calculate_demand_profile(20, 40) == "MEDIUM"  # 50%
    
    # LOW: drivers >= 67% of riders
    assert calculate_demand_profile(70, 100) == "LOW"  # 70%

def test_unit_price_calculation():
    """Test unit price = price / duration"""
    price = 50.0
    duration = 25.0
    unit_price = price / duration
    assert unit_price == 2.0

def test_estimated_price_calculation():
    """Test estimated_price = unit_price × duration"""
    unit_price = 3.5
    duration = 30.0
    estimated_price = unit_price * duration
    assert estimated_price == 105.0
```

### Integration Test

Create end-to-end test that:
1. Migrates test data
2. Trains ML model
3. Runs pipeline
4. Generates report
5. Validates 162 segments with correct calculations

## Rollback Plan

If issues arise:

```bash
# Restore MongoDB from backup
mongorestore --uri="mongodb://localhost:27017" --db=rideshare /path/to/backup

# Revert code changes
git revert <commit-hash>

# Clear cache and restart
python3 clear_backend_cache.py
./restart_backend.sh
```

## Success Criteria

✅ Migration completes without errors
✅ ML model trains with 24 regressors (20 categorical + 4 numeric)
✅ Pipeline generates forecasts for 162 segments
✅ Report includes 162 rows with new column structure
✅ All API endpoints return new field structure
✅ No references to pricing_tier, segment_avg_distance, segment_avg_price
✅ All calculations use duration × unit_price model
✅ segment_demand_profile calculated correctly (HIGH/MEDIUM/LOW)
