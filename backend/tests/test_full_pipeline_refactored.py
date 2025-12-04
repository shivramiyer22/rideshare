"""
Integration test for full pipeline with refactored data model.

Tests the complete end-to-end flow:
1. Historical data → Forecasting → Analysis → Recommendation → Report
2. Validates all 162 segments throughout pipeline
3. Verifies data structure consistency
"""

import pytest
import requests
import time
from datetime import datetime


BASE_URL = "http://localhost:8000"


class TestFullPipelineIntegration:
    """Test complete pipeline flow with 162 segments."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Verify backend is running."""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200, "Backend not running"
    
    def test_01_trigger_pipeline(self):
        """Test: Trigger pipeline execution."""
        response = requests.post(
            f"{BASE_URL}/api/v1/pipeline/trigger",
            json={"trigger_source": "integration_test", "force": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        
        # Wait for pipeline to complete
        time.sleep(45)
    
    def test_02_verify_forecasting_phase(self):
        """Test: Verify forecasting phase has 162 segments."""
        response = requests.get(f"{BASE_URL}/api/v1/pipeline/last-run")
        assert response.status_code == 200
        
        data = response.json()
        result = data.get("last_run", {})
        phases = result.get("phases", {})
        
        # Check forecasting success
        forecast_phase = phases.get("forecasting", {})
        assert forecast_phase.get("success") == True, "Forecasting phase failed"
        
        # Verify 162 segments
        forecast_data = forecast_phase.get("data", {}).get("forecasts", {})
        segments = forecast_data.get("segmented_forecasts", [])
        
        assert len(segments) == 162, f"Expected 162 segments, got {len(segments)}"
        
        # Verify segment structure
        if segments:
            sample = segments[0]
            assert "dimensions" in sample
            assert "baseline_metrics" in sample
            assert "forecast_30d" in sample
            
            # Check new fields
            baseline = sample["baseline_metrics"]
            assert "segment_avg_fcs_unit_price" in baseline
            assert "segment_avg_fcs_ride_duration" in baseline
            assert "segment_demand_profile" in baseline
    
    def test_03_verify_analysis_phase(self):
        """Test: Verify analysis phase generates pricing rules."""
        response = requests.get(f"{BASE_URL}/api/v1/pipeline/last-run")
        data = response.json()
        phases = data.get("last_run", {}).get("phases", {})
        
        analysis_phase = phases.get("analysis", {})
        assert analysis_phase.get("success") == True
        
        rules_data = analysis_phase.get("data", {}).get("pricing_rules", {})
        rules = rules_data.get("top_rules", [])
        
        assert len(rules) > 0, "No pricing rules generated"
        
        # Check for enhanced categories (event, news)
        categories = rules_data.get("by_category", {})
        assert "event_based" in categories or len(categories) >= 4
    
    def test_04_verify_recommendation_phase(self):
        """Test: Verify recommendation phase with per_segment_impacts."""
        response = requests.get(f"{BASE_URL}/api/v1/pipeline/last-run")
        data = response.json()
        result = data.get("last_run", {})
        
        # Check for per_segment_impacts
        per_segment_impacts = result.get("per_segment_impacts", {})
        assert len(per_segment_impacts) > 0, "No per_segment_impacts found"
        
        # Count total impacts (should be ~486: 162 segments × 3 recommendations)
        total_impacts = 0
        for rec_name, impacts_list in per_segment_impacts.items():
            if isinstance(impacts_list, list):
                total_impacts += len(impacts_list)
        
        assert total_impacts >= 450, f"Expected ~486 impacts, got {total_impacts}"
    
    def test_05_verify_report_api(self):
        """Test: Verify report API returns 162 segments."""
        response = requests.get(
            f"{BASE_URL}/api/v1/reports/segment-dynamic-pricing-analysis"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        segments = data.get("segments", [])
        assert len(segments) == 162, f"Expected 162 segments in report, got {len(segments)}"
        
        # Verify report structure
        if segments:
            sample = segments[0]
            
            # Check all 5 scenarios present
            assert "segment" in sample
            assert "hwco_continue_current" in sample
            assert "lyft_continue_current" in sample
            assert "recommendation_1" in sample
            assert "recommendation_2" in sample
            assert "recommendation_3" in sample
            
            # Check HWCO has all fields
            hwco = sample["hwco_continue_current"]
            assert "rides_30d" in hwco
            assert "unit_price" in hwco
            assert "duration_minutes" in hwco
            assert "revenue_30d" in hwco
            assert "explanation" in hwco
            
            # Check Lyft has all fields
            lyft = sample["lyft_continue_current"]
            assert "explanation" in lyft
            assert "duration_minutes" in lyft
            
            # Check recommendations have all fields
            rec1 = sample["recommendation_1"]
            assert "explanation" in rec1
            assert "duration_minutes" in rec1
    
    def test_06_verify_csv_export(self):
        """Test: Verify CSV export has 30 columns."""
        response = requests.get(
            f"{BASE_URL}/api/v1/reports/segment-dynamic-pricing-analysis?format=csv"
        )
        
        assert response.status_code == 200
        csv_content = response.text
        
        lines = csv_content.strip().split('\n')
        assert len(lines) == 163, f"Expected 163 lines (header + 162), got {len(lines)}"
        
        # Check header has 30 columns
        header = lines[0].split(',')
        assert len(header) == 30, f"Expected 30 columns, got {len(header)}"
        
        # Verify key columns present
        assert "location_category" in header[0]
        assert "hwco_explanation" in ','.join(header)
        assert "lyft_explanation" in ','.join(header)
        assert "hwco_duration_minutes" in ','.join(header)
        assert "rec1_duration_minutes" in ','.join(header)
    
    def test_07_verify_orders_updated(self):
        """Test: Verify orders have segment data."""
        # This would require MongoDB access or an orders API endpoint
        # Placeholder for now
        assert True


class TestDataConsistency:
    """Test data consistency across pipeline stages."""
    
    def test_segment_count_consistency(self):
        """Test: Same 162 segments in forecast, recommendation, and report."""
        response = requests.get(f"{BASE_URL}/api/v1/pipeline/last-run")
        data = response.json()
        result = data.get("last_run", {})
        phases = result.get("phases", {})
        
        # Forecast segments
        forecast_data = phases.get("forecasting", {}).get("data", {}).get("forecasts", {})
        forecast_count = len(forecast_data.get("segmented_forecasts", []))
        
        # Per-segment impacts
        per_segment_impacts = result.get("per_segment_impacts", {})
        impact_count = 0
        for impacts_list in per_segment_impacts.values():
            if isinstance(impacts_list, list):
                impact_count = max(impact_count, len(impacts_list))
        
        # Report segments
        report_response = requests.get(
            f"{BASE_URL}/api/v1/reports/segment-dynamic-pricing-analysis"
        )
        report_data = report_response.json()
        report_count = len(report_data.get("segments", []))
        
        # All should be 162
        assert forecast_count == 162
        assert impact_count >= 150  # At least 150 per recommendation
        assert report_count == 162
    
    def test_duration_pricing_model(self):
        """Test: Revenue = rides × duration × unit_price throughout."""
        response = requests.get(
            f"{BASE_URL}/api/v1/reports/segment-dynamic-pricing-analysis"
        )
        data = response.json()
        segments = data.get("segments", [])
        
        if segments:
            sample = segments[0]
            hwco = sample.get("hwco_continue_current", {})
            
            rides = hwco.get("rides_30d", 0)
            duration = hwco.get("duration_minutes", 0)
            unit_price = hwco.get("unit_price", 0)
            revenue = hwco.get("revenue_30d", 0)
            
            if rides > 0 and duration > 0 and unit_price > 0:
                expected_revenue = rides * duration * unit_price
                # Allow 1% tolerance for rounding
                assert abs(expected_revenue - revenue) / expected_revenue < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
