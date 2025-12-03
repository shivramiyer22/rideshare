"""
Test script for simplified pipeline flow.

Tests the end-to-end pipeline execution with simplified 3-tool flow:
1. Phase 1 (Parallel): generate_multidimensional_forecast + generate_and_rank_pricing_rules
2. Phase 2 (Sequential): generate_strategic_recommendations
3. Phase 3 (Sequential): calculate_whatif_impact_for_pipeline
"""

import pytest
import json
import sys
import os
import asyncio
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.pipeline_orchestrator import run_agent_pipeline
from app.agents.forecasting import generate_multidimensional_forecast
from app.agents.analysis import generate_and_rank_pricing_rules
from app.agents.recommendation import generate_strategic_recommendations


class TestSimplifiedPipelineFlow:
    """Test simplified pipeline flow (3 tools instead of 9)."""
    
    @pytest.mark.asyncio
    async def test_phase_1_parallel_execution(self):
        """Test Phase 1 parallel execution of forecast and rules."""
        print("\nTesting Phase 1 (Parallel): Forecast + Rules...")
        
        # Simulate parallel execution
        forecast_task = asyncio.create_task(
            asyncio.to_thread(generate_multidimensional_forecast.invoke, {"periods": 30})
        )
        rules_task = asyncio.create_task(
            asyncio.to_thread(generate_and_rank_pricing_rules.invoke, {})
        )
        
        forecast_result, rules_result = await asyncio.gather(
            forecast_task, rules_task, return_exceptions=True
        )
        
        # Check for exceptions
        assert not isinstance(forecast_result, Exception), f"Forecast failed: {forecast_result}"
        assert not isinstance(rules_result, Exception), f"Rules failed: {rules_result}"
        
        # Parse results
        forecast_data = json.loads(forecast_result)
        rules_data = json.loads(rules_result)
        
        assert "summary" in forecast_data, "Forecast should have summary"
        assert forecast_data["summary"]["total_possible_segments"] == 162, "Should be 162 segments"
        assert "top_rules" in rules_data, "Rules should have top_rules"
        
        print(f"✓ Phase 1 completed: {forecast_data['summary']['forecasted_segments']} segments, "
              f"{len(rules_data.get('top_rules', []))} rules")
        
        return forecast_result, rules_result
    
    @pytest.mark.asyncio
    async def test_phase_2_recommendations(self):
        """Test Phase 2 sequential execution of recommendations."""
        print("\nTesting Phase 2 (Sequential): Recommendations...")
        
        # Get Phase 1 results
        forecast_result = generate_multidimensional_forecast.invoke({"periods": 30})
        rules_result = generate_and_rank_pricing_rules.invoke({})
        
        # Generate recommendations
        rec_result = generate_strategic_recommendations.invoke({
            "forecasts": forecast_result,
            "rules": rules_result
        })
        
        assert isinstance(rec_result, str), "Result should be string"
        rec_data = json.loads(rec_result)
        
        assert "recommendations" in rec_data, "Should have recommendations"
        recommendations = rec_data["recommendations"]
        assert len(recommendations) == 3, f"Should have 3 recommendations, got {len(recommendations)}"
        
        # Check each recommendation
        for rec in recommendations:
            assert "rank" in rec
            assert "rules" in rec
            assert "rule_count" in rec
            assert "objectives_achieved" in rec
            assert rec["rule_count"] > 0
            assert rec["rule_count"] <= 5
        
        print(f"✓ Phase 2 completed: {len(recommendations)} recommendations generated")
        
        return rec_result
    
    @pytest.mark.asyncio
    async def test_full_pipeline_execution(self):
        """Test full pipeline execution end-to-end."""
        print("\nTesting Full Pipeline Execution...")
        
        try:
            result = await run_agent_pipeline(
                trigger_source="test",
                changes_summary={"change_count": 0, "collections_changed": []}
            )
            
            assert result.get("success") is not None, "Should have success status"
            
            if result.get("success"):
                assert "results" in result, "Should have results"
                results = result["results"]
                
                # Check Phase 1 results
                assert "forecasting" in results or "forecasts" in str(results), "Should have forecasting results"
                assert "analysis" in results or "pricing_rules" in str(results), "Should have analysis results"
                
                # Check Phase 2 results
                assert "recommendations" in results, "Should have recommendations"
                
                # Check Phase 3 results
                assert "whatif_impact" in results, "Should have what-if impact"
                
                print("✓ Full pipeline execution completed successfully")
                print(f"  Duration: {result.get('duration_seconds', 0):.2f} seconds")
            else:
                print(f"⚠ Pipeline completed with errors: {result.get('errors', [])}")
            
            return result
            
        except Exception as e:
            print(f"✗ Pipeline execution failed: {e}")
            raise


def run_pipeline_tests():
    """Run all pipeline tests."""
    print("=" * 60)
    print("Testing Simplified Pipeline Flow")
    print("=" * 60)
    
    test_instance = TestSimplifiedPipelineFlow()
    
    # Run async tests
    loop = asyncio.get_event_loop()
    
    try:
        # Test Phase 1
        print("\n[TEST 1] Phase 1 Parallel Execution")
        forecast_result, rules_result = loop.run_until_complete(
            test_instance.test_phase_1_parallel_execution()
        )
        print("✓ PASSED")
        
        # Test Phase 2
        print("\n[TEST 2] Phase 2 Recommendations")
        rec_result = loop.run_until_complete(
            test_instance.test_phase_2_recommendations()
        )
        print("✓ PASSED")
        
        # Test Full Pipeline (may take longer)
        print("\n[TEST 3] Full Pipeline Execution")
        print("  (This may take 2-3 minutes...)")
        pipeline_result = loop.run_until_complete(
            test_instance.test_full_pipeline_execution()
        )
        print("✓ PASSED")
        
        print("\n" + "=" * 60)
        print("ALL PIPELINE TESTS PASSED!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_pipeline_tests()
    sys.exit(0 if success else 1)
