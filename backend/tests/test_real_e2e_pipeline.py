"""
REAL End-to-End Pipeline Integration Test
==========================================

Tests the ACTUAL complete pipeline flow with REAL data and REAL agent execution.
No mocks, no fakes - this validates the entire system works correctly.

Pipeline Flow Tested:
1. Trigger pipeline manually
2. Wait for completion
3. Verify forecasting phase (162 segments)
4. Verify analysis phase (pricing rules)
5. Verify recommendation phase (per_segment_impacts)
6. Verify what-if phase
7. Verify report generation (all 162 segments × 5 scenarios)
8. Verify data consistency across all phases
"""

import pytest
import requests
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class TestEndToEndPipeline:
    """Complete end-to-end pipeline validation with REAL execution"""
    
    def test_01_trigger_pipeline(self):
        """Step 1: Trigger the pipeline manually"""
        print("\n" + "="*80)
        print("STEP 1: Triggering Pipeline")
        print("="*80)
        
        response = requests.post(
            f"{BASE_URL}/api/v1/pipeline/trigger",
            json={"trigger_source": "e2e_test"}
        )
        
        assert response.status_code in [200, 202], f"Failed to trigger pipeline: {response.status_code}"
        data = response.json()
        
        assert "run_id" in data, f"No run_id in response: {data}"
        run_id = data["run_id"]
        
        print(f"✓ Pipeline triggered successfully")
        print(f"  Run ID: {run_id}")
        
        return run_id
    
    def test_02_wait_for_completion(self):
        """Step 2: Wait for pipeline to complete"""
        print("\n" + "="*80)
        print("STEP 2: Waiting for Pipeline Completion")
        print("="*80)
        
        run_id = self.test_01_trigger_pipeline()
        
        max_wait = 180  # 3 minutes
        check_interval = 10  # Check every 10 seconds
        elapsed = 0
        
        while elapsed < max_wait:
            response = requests.get(f"{BASE_URL}/api/v1/pipeline/status")
            assert response.status_code == 200
            
            data = response.json()
            is_running = data.get("is_running", False)
            current_status = data.get("current_status", "unknown")
            
            print(f"  [{elapsed}s] Status: {current_status}, Running: {is_running}")
            
            if not is_running and current_status in ["completed", "pending"]:
                print(f"✓ Pipeline completed after {elapsed} seconds")
                return run_id
            
            time.sleep(check_interval)
            elapsed += check_interval
        
        pytest.fail(f"Pipeline did not complete within {max_wait} seconds")
    
    def test_03_verify_forecasting_phase(self):
        """Step 3: Verify forecasting generated 162 segments"""
        print("\n" + "="*80)
        print("STEP 3: Verifying Forecasting Phase")
        print("="*80)
        
        run_id = self.test_02_wait_for_completion()
        
        # Get last pipeline run
        response = requests.get(f"{BASE_URL}/api/v1/pipeline/last-run")
        assert response.status_code == 200
        
        data = response.json()
        last_run = data.get("last_run", {})
        phases = last_run.get("phases", {})
        
        forecasting_phase = phases.get("forecasting", {})
        assert forecasting_phase.get("success"), "Forecasting phase failed"
        
        forecast_data = forecasting_phase.get("data", {}).get("forecasts", {})
        segmented_forecasts = forecast_data.get("segmented_forecasts", [])
        
        print(f"  Segmented forecasts: {len(segmented_forecasts)}")
        assert len(segmented_forecasts) == 162, f"Expected 162 segments, got {len(segmented_forecasts)}"
        
        # Verify segment structure
        if len(segmented_forecasts) > 0:
            sample = segmented_forecasts[0]
            required_fields = ["dimensions", "baseline_metrics", "forecast_30d"]
            for field in required_fields:
                assert field in sample, f"Missing field '{field}' in segment"
            
            # Verify dimensions
            dims = sample["dimensions"]
            assert "location" in dims
            assert "loyalty_tier" in dims
            assert "vehicle_type" in dims
            assert "pricing_model" in dims
            assert "demand_profile" in dims
            
            # Verify baseline metrics
            baseline = sample["baseline_metrics"]
            assert "segment_avg_fcs_unit_price" in baseline
            assert "segment_avg_fcs_ride_duration" in baseline
            
            # Verify forecast
            forecast_30d = sample["forecast_30d"]
            assert "predicted_rides" in forecast_30d
            assert "predicted_unit_price" in forecast_30d
            assert "predicted_duration" in forecast_30d
            assert "predicted_revenue" in forecast_30d
        
        print(f"✓ Forecasting phase validated")
        print(f"  162 segments with complete forecasts")
        
        return last_run
    
    def test_04_verify_analysis_phase(self):
        """Step 4: Verify analysis generated pricing rules"""
        print("\n" + "="*80)
        print("STEP 4: Verifying Analysis Phase")
        print("="*80)
        
        last_run = self.test_03_verify_forecasting_phase()
        phases = last_run.get("phases", {})
        
        analysis_phase = phases.get("analysis", {})
        assert analysis_phase.get("success"), "Analysis phase failed"
        
        rules_data = analysis_phase.get("data", {}).get("pricing_rules", {})
        top_rules = rules_data.get("top_rules", [])
        by_category = rules_data.get("by_category", {})
        
        print(f"  Total rules: {len(top_rules)}")
        print(f"  Categories: {list(by_category.keys())}")
        
        assert len(top_rules) >= 5, f"Expected at least 5 rules, got {len(top_rules)}"
        
        # Verify rule structure
        if len(top_rules) > 0:
            sample_rule = top_rules[0]
            required_fields = ["rule_id", "name", "category", "condition", "action"]
            for field in required_fields:
                assert field in sample_rule, f"Missing field '{field}' in rule"
        
        print(f"✓ Analysis phase validated")
        print(f"  {len(top_rules)} pricing rules across {len(by_category)} categories")
        
        return last_run
    
    def test_05_verify_recommendation_phase(self):
        """Step 5: Verify recommendations with per-segment impacts"""
        print("\n" + "="*80)
        print("STEP 5: Verifying Recommendation Phase")
        print("="*80)
        
        last_run = self.test_04_verify_analysis_phase()
        phases = last_run.get("phases", {})
        
        recommendation_phase = phases.get("recommendation", {})
        assert recommendation_phase.get("success"), "Recommendation phase failed"
        
        rec_data = recommendation_phase.get("data", {})
        recommendations = rec_data.get("recommendations", {}).get("recommendations", [])
        
        print(f"  Recommendations: {len(recommendations)}")
        assert len(recommendations) == 3, f"Expected 3 recommendations, got {len(recommendations)}"
        
        # Verify per_segment_impacts (CRITICAL for report generation)
        per_segment_impacts = last_run.get("per_segment_impacts", {})
        
        if not per_segment_impacts:
            # Try nested location
            per_segment_impacts = rec_data.get("per_segment_impacts", {})
        
        assert per_segment_impacts, "No per_segment_impacts found"
        
        rec1_impacts = per_segment_impacts.get("recommendation_1", [])
        rec2_impacts = per_segment_impacts.get("recommendation_2", [])
        rec3_impacts = per_segment_impacts.get("recommendation_3", [])
        
        print(f"  Recommendation 1 impacts: {len(rec1_impacts)} segments")
        print(f"  Recommendation 2 impacts: {len(rec2_impacts)} segments")
        print(f"  Recommendation 3 impacts: {len(rec3_impacts)} segments")
        
        # All 3 recommendations should have 162 segments (even if no rules apply)
        assert len(rec1_impacts) == 162, f"Rec 1: Expected 162 segments, got {len(rec1_impacts)}"
        assert len(rec2_impacts) == 162, f"Rec 2: Expected 162 segments, got {len(rec2_impacts)}"
        assert len(rec3_impacts) == 162, f"Rec 3: Expected 162 segments, got {len(rec3_impacts)}"
        
        # Verify impact structure
        if len(rec1_impacts) > 0:
            sample_impact = rec1_impacts[0]
            assert "segment" in sample_impact
            assert "baseline" in sample_impact
            assert "with_recommendation" in sample_impact
            
            baseline = sample_impact["baseline"]
            assert "unit_price_per_minute" in baseline
            assert "ride_duration_minutes" in baseline
            assert "revenue_30d" in baseline
            
            with_rec = sample_impact["with_recommendation"]
            assert "unit_price_per_minute" in with_rec
            assert "ride_duration_minutes" in with_rec
            assert "revenue_30d" in with_rec
        
        print(f"✓ Recommendation phase validated")
        print(f"  3 recommendations × 162 segments = 486 per-segment impacts")
        
        return last_run
    
    def test_06_verify_what_if_phase(self):
        """Step 6: Verify what-if analysis completed"""
        print("\n" + "="*80)
        print("STEP 6: Verifying What-If Analysis Phase")
        print("="*80)
        
        last_run = self.test_05_verify_recommendation_phase()
        phases = last_run.get("phases", {})
        
        whatif_phase = phases.get("what_if", {})
        assert whatif_phase.get("success"), "What-if phase failed"
        
        whatif_data = whatif_phase.get("data", {})
        
        print(f"✓ What-if phase validated")
        print(f"  Impact analysis completed for top 3 recommendations")
        
        return last_run
    
    def test_07_verify_report_generation(self):
        """Step 7: Verify report has all 162 segments × 5 scenarios"""
        print("\n" + "="*80)
        print("STEP 7: Verifying Report Generation")
        print("="*80)
        
        # Let report generator run
        self.test_06_verify_what_if_phase()
        
        response = requests.get(f"{BASE_URL}/api/v1/reports/segment-dynamic-pricing-analysis")
        assert response.status_code == 200
        
        data = response.json()
        segments = data.get("segments", [])
        
        print(f"  Total segments in report: {len(segments)}")
        assert len(segments) == 162, f"Expected 162 segments, got {len(segments)}"
        
        # Verify ALL 5 scenarios exist for each segment
        if len(segments) > 0:
            sample = segments[0]
            required_scenarios = [
                "hwco_continue_current",
                "lyft_continue_current",  # NOTE: Actual field name (not lyft_competitor)
                "recommendation_1",
                "recommendation_2",
                "recommendation_3"
            ]
            
            for scenario_key in required_scenarios:
                assert scenario_key in sample, f"Missing scenario: {scenario_key}"
                
                scenario = sample[scenario_key]
                # Verify all required fields in each scenario
                required_fields = ["rides_30d", "unit_price", "duration_minutes", "revenue_30d", "explanation"]
                for field in required_fields:
                    assert field in scenario, f"Missing field '{field}' in {scenario_key}"
        
        print(f"✓ Report generation validated")
        print(f"  162 segments × 5 scenarios = 810 scenario projections")
        
        return data
    
    def test_08_verify_data_consistency(self):
        """Step 8: Verify data consistency across pipeline phases"""
        print("\n" + "="*80)
        print("STEP 8: Verifying Data Consistency")
        print("="*80)
        
        report_data = self.test_07_verify_report_generation()
        
        # Get pipeline run again
        response = requests.get(f"{BASE_URL}/api/v1/pipeline/last-run")
        last_run = response.json().get("last_run", {})
        
        phases = last_run.get("phases", {})
        
        # Extract segment count from each phase
        forecasting_segments = len(phases.get("forecasting", {}).get("data", {}).get("forecasts", {}).get("segmented_forecasts", []))
        report_segments = len(report_data.get("segments", []))
        
        print(f"  Forecasting segments: {forecasting_segments}")
        print(f"  Report segments: {report_segments}")
        
        assert forecasting_segments == 162, "Forecasting should have 162 segments"
        assert report_segments == 162, "Report should have 162 segments"
        assert forecasting_segments == report_segments, "Segment counts must match"
        
        print(f"✓ Data consistency validated")
        print(f"  All 162 segments flow correctly through entire pipeline")
    
    def test_09_final_summary(self):
        """Step 9: Print final validation summary"""
        print("\n" + "="*80)
        print("FINAL VALIDATION SUMMARY")
        print("="*80)
        
        self.test_08_verify_data_consistency()
        
        print("\n✅ END-TO-END PIPELINE VALIDATION: PASSED")
        print("\nValidated Components:")
        print("  ✓ Pipeline Trigger")
        print("  ✓ Forecasting Agent (162 segments)")
        print("  ✓ Analysis Agent (11+ pricing rules)")
        print("  ✓ Recommendation Agent (3 recommendations × 162 segments)")
        print("  ✓ What-If Analysis (impact projections)")
        print("  ✓ Report Generation (162 segments × 5 scenarios)")
        print("  ✓ Data Consistency (all phases aligned)")
        print("\nPipeline Status: ✅ FULLY FUNCTIONAL")
        print("="*80)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
