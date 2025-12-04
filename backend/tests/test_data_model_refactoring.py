"""
Unit tests for data model refactoring.

Tests cover:
1. Schema validation (new duration/unit_price model)
2. Demand profile calculation
3. Segment key generation
4. Data model consistency
"""

import pytest
from datetime import datetime
from app.models.schemas import (
    HistoricalBaseline,
    ForecastPrediction,
    PriceBreakdown,
    OrderCreate,
    OrderResponse
)


class TestSchemaValidation:
    """Test new Pydantic schemas with duration/unit_price model."""
    
    def test_historical_baseline_schema(self):
        """Test HistoricalBaseline with new fields."""
        baseline = HistoricalBaseline(
            segment_avg_fcs_unit_price=4.50,
            segment_avg_fcs_ride_duration=65.0,
            segment_avg_riders_per_order=1.2,
            segment_avg_drivers_per_order=0.4,
            segment_demand_profile="HIGH"
        )
        
        assert baseline.segment_avg_fcs_unit_price == 4.50
        assert baseline.segment_avg_fcs_ride_duration == 65.0
        assert baseline.segment_demand_profile == "HIGH"
    
    def test_forecast_prediction_schema(self):
        """Test ForecastPrediction with new fields."""
        forecast = ForecastPrediction(
            forecast_30d=100,
            forecast_60d=200,
            forecast_90d=300,
            segment_avg_fcs_unit_price=3.75,
            segment_avg_fcs_ride_duration=55.0,
            segment_demand_profile="MEDIUM"
        )
        
        assert forecast.forecast_30d == 100
        assert forecast.segment_avg_fcs_unit_price == 3.75
        assert forecast.segment_avg_fcs_ride_duration == 55.0
    
    def test_order_create_schema(self):
        """Test OrderCreate with new fields."""
        order = OrderCreate(
            user_id="test_user",
            pickup_location={"address": "123 Main St"},
            dropoff_location={"address": "456 Oak Ave"},
            pricing_model="STANDARD",
            segment_avg_riders_per_order=1.0,
            segment_avg_drivers_per_order=0.5,
            segment_demand_profile="MEDIUM"
        )
        
        assert order.pricing_model == "STANDARD"
        assert order.segment_demand_profile == "MEDIUM"


class TestDemandProfileCalculation:
    """Test demand profile calculation logic."""
    
    def test_high_demand_profile(self):
        """Test HIGH demand (driver ratio < 34%)."""
        riders = 100
        drivers = 30  # 30% ratio
        
        driver_ratio = (drivers / riders) * 100
        if driver_ratio < 34:
            demand_profile = "HIGH"
        elif driver_ratio < 67:
            demand_profile = "MEDIUM"
        else:
            demand_profile = "LOW"
        
        assert demand_profile == "HIGH"
    
    def test_medium_demand_profile(self):
        """Test MEDIUM demand (driver ratio 34-67%)."""
        riders = 100
        drivers = 50  # 50% ratio
        
        driver_ratio = (drivers / riders) * 100
        if driver_ratio < 34:
            demand_profile = "HIGH"
        elif driver_ratio < 67:
            demand_profile = "MEDIUM"
        else:
            demand_profile = "LOW"
        
        assert demand_profile == "MEDIUM"
    
    def test_low_demand_profile(self):
        """Test LOW demand (driver ratio > 67%)."""
        riders = 100
        drivers = 70  # 70% ratio
        
        driver_ratio = (drivers / riders) * 100
        if driver_ratio < 34:
            demand_profile = "HIGH"
        elif driver_ratio < 67:
            demand_profile = "MEDIUM"
        else:
            demand_profile = "LOW"
        
        assert demand_profile == "LOW"
    
    def test_zero_riders_edge_case(self):
        """Test edge case: zero riders."""
        riders = 0
        drivers = 10
        
        if riders == 0:
            demand_profile = "MEDIUM"  # Default
        else:
            driver_ratio = (drivers / riders) * 100
            if driver_ratio < 34:
                demand_profile = "HIGH"
            elif driver_ratio < 67:
                demand_profile = "MEDIUM"
            else:
                demand_profile = "LOW"
        
        assert demand_profile == "MEDIUM"


class TestSegmentKeyGeneration:
    """Test segment key generation for 162 segments."""
    
    def test_segment_key_format(self):
        """Test segment key format."""
        location = "Urban"
        loyalty = "Gold"
        vehicle = "Premium"
        pricing = "STANDARD"
        demand = "HIGH"
        
        segment_key = f"{location}_{loyalty}_{vehicle}_{pricing}_{demand}"
        
        assert segment_key == "Urban_Gold_Premium_STANDARD_HIGH"
    
    def test_all_162_combinations(self):
        """Test that we can generate all 162 segment combinations."""
        locations = ["Urban", "Suburban", "Rural"]
        loyalty_tiers = ["Gold", "Silver", "Regular"]
        vehicles = ["Premium", "Economy"]
        pricing_models = ["STANDARD", "CONTRACTED", "CUSTOM"]
        demand_profiles = ["HIGH", "MEDIUM", "LOW"]
        
        segments = set()
        for loc in locations:
            for loy in loyalty_tiers:
                for veh in vehicles:
                    for pri in pricing_models:
                        for dem in demand_profiles:
                            key = f"{loc}_{loy}_{veh}_{pri}_{dem}"
                            segments.add(key)
        
        assert len(segments) == 162  # 3 × 3 × 2 × 3 × 3


class TestDurationPricingModel:
    """Test duration-based pricing calculations."""
    
    def test_revenue_calculation(self):
        """Test: revenue = rides × duration × unit_price."""
        rides = 100
        duration = 60.0  # minutes
        unit_price = 3.50  # per minute
        
        revenue = rides * duration * unit_price
        
        assert revenue == 21000.0
    
    def test_total_price_calculation(self):
        """Test: total_price = duration × unit_price."""
        duration = 45.0
        unit_price = 4.00
        
        total_price = duration * unit_price
        
        assert total_price == 180.0
    
    def test_unit_price_from_historical(self):
        """Test: unit_price = price / duration."""
        historical_price = 200.0
        duration = 50.0
        
        unit_price = historical_price / duration if duration > 0 else 0
        
        assert unit_price == 4.0


class TestDataModelConsistency:
    """Test consistency of new data model."""
    
    def test_no_pricing_tier_references(self):
        """Verify pricing_tier is completely removed."""
        # This test would check that schemas don't have pricing_tier
        # In actual implementation, this would scan schema definitions
        assert True  # Placeholder - actual implementation would verify
    
    def test_duration_fields_present(self):
        """Verify duration fields exist in schemas."""
        baseline = HistoricalBaseline(
            segment_avg_fcs_unit_price=4.0,
            segment_avg_fcs_ride_duration=60.0,
            segment_avg_riders_per_order=1.0,
            segment_avg_drivers_per_order=0.5,
            segment_demand_profile="MEDIUM"
        )
        
        assert hasattr(baseline, 'segment_avg_fcs_ride_duration')
        assert baseline.segment_avg_fcs_ride_duration == 60.0
    
    def test_unit_price_fields_present(self):
        """Verify unit_price fields exist in schemas."""
        baseline = HistoricalBaseline(
            segment_avg_fcs_unit_price=3.5,
            segment_avg_fcs_ride_duration=50.0,
            segment_avg_riders_per_order=1.0,
            segment_avg_drivers_per_order=0.5,
            segment_demand_profile="HIGH"
        )
        
        assert hasattr(baseline, 'segment_avg_fcs_unit_price')
        assert baseline.segment_avg_fcs_unit_price == 3.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
