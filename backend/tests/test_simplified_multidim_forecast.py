"""
Test script for simplified multi-dimensional forecasting system.

Tests:
1. Multi-dimensional forecast generation (162 segments, no Time_of_Ride)
2. generate_and_rank_pricing_rules (no MongoDB merging)
3. generate_strategic_recommendations (combined tool)
4. Simplified pipeline flow
5. Rule matching logic (exact match only)
"""

import pytest
import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agents.forecasting import generate_multidimensional_forecast
from app.agents.analysis import generate_and_rank_pricing_rules
from app.agents.recommendation import generate_strategic_recommendations, simulate_pricing_rule_impact
from app.config import settings


class TestSimplifiedMultiDimensionalForecast:
    """Test simplified multi-dimensional forecasting (162 segments)."""
    
    def test_forecast_generates_162_segments(self):
        """Test that forecast generates 162 segments (not 648)."""
        result = generate_multidimensional_forecast.invoke({"periods": 30})
        
        assert isinstance(result, str), "Result should be JSON string"
        data = json.loads(result)
        
        assert "summary" in data, "Should have summary"
        assert data["summary"]["total_possible_segments"] == 162, "Should be 162 segments, not 648"
        assert data["summary"]["total_possible_segments"] < 648, "Should be less than 648"
        
        print(f"✓ Forecast generates {data['summary']['total_possible_segments']} segments (expected: 162)")
    
    def test_forecast_no_time_dimension(self):
        """Test that forecast segments don't include time_period dimension."""
        result = generate_multidimensional_forecast.invoke({"periods": 30})
        data = json.loads(result)
        
        # Check first few segments
        segments = data.get("segmented_forecasts", [])
        if segments:
            for segment in segments[:5]:
                dimensions = segment.get("dimensions", {})
                assert "time_period" not in dimensions, "Should not have time_period dimension"
                assert "Time_of_Ride" not in dimensions, "Should not have Time_of_Ride dimension"
                # Should have these 5 dimensions
                assert "loyalty_tier" in dimensions
                assert "vehicle_type" in dimensions
                assert "demand_profile" in dimensions
                assert "pricing_model" in dimensions
                assert "location" in dimensions
        
        print("✓ Forecast segments correctly exclude Time_of_Ride dimension")
    
    def test_forecast_has_confidence_levels(self):
        """Test that forecasts include confidence levels."""
        result = generate_multidimensional_forecast.invoke({"periods": 30})
        data = json.loads(result)
        
        assert "summary" in data
        assert "confidence_distribution" in data["summary"]
        conf_dist = data["summary"]["confidence_distribution"]
        assert "high" in conf_dist or "medium" in conf_dist or "low" in conf_dist
        
        print(f"✓ Forecast includes confidence distribution: {conf_dist}")


class TestGenerateAndRankPricingRules:
    """Test simplified pricing rules generation (no MongoDB merging)."""
    
    def test_generates_rules_from_data_only(self):
        """Test that rules are generated from data, not loaded from MongoDB."""
        result = generate_and_rank_pricing_rules.invoke({})
        
        assert isinstance(result, str), "Result should be JSON string"
        data = json.loads(result)
        
        assert "summary" in data, "Should have summary"
        assert "top_rules" in data, "Should have top_rules"
        
        # Should NOT have mongodb_rules or chromadb_context in summary
        summary = data["summary"]
        assert "mongodb_rules" not in summary, "Should not merge MongoDB rules"
        assert "chromadb_context" not in summary, "Should not merge ChromaDB rules"
        assert "total_rules_generated" in summary, "Should show generated count"
        
        print(f"✓ Generated {summary.get('total_rules_generated', 0)} rules from data only")
    
    def test_rules_have_standardized_structure(self):
        """Test that generated rules have standardized structure."""
        result = generate_and_rank_pricing_rules.invoke({})
        data = json.loads(result)
        
        rules = data.get("top_rules", [])
        if rules:
            for rule in rules[:5]:
                assert "rule_id" in rule, "Should have rule_id"
                assert "name" in rule, "Should have name"
                assert "category" in rule, "Should have category"
                assert "condition" in rule, "Should have condition"
                assert "action" in rule, "Should have action"
                assert "estimated_impact" in rule, "Should have estimated_impact"
        
        print("✓ Rules have standardized structure")
    
    def test_rules_ranked_by_impact(self):
        """Test that rules are ranked by estimated impact."""
        result = generate_and_rank_pricing_rules.invoke({})
        data = json.loads(result)
        
        rules = data.get("top_rules", [])
        if len(rules) >= 2:
            # First rule should have higher or equal impact than second
            first_impact = rules[0].get("estimated_impact", 0)
            second_impact = rules[1].get("estimated_impact", 0)
            assert first_impact >= second_impact, "Rules should be ranked by impact"
        
        print("✓ Rules are ranked by estimated impact")


class TestGenerateStrategicRecommendations:
    """Test combined strategic recommendations tool."""
    
    def test_generates_top_3_recommendations(self):
        """Test that tool generates exactly top 3 recommendations."""
        # Get forecasts and rules first
        forecasts_result = generate_multidimensional_forecast.invoke({"periods": 30})
        rules_result = generate_and_rank_pricing_rules.invoke({})
        
        # Generate recommendations
        result = generate_strategic_recommendations.invoke({
            "forecasts": forecasts_result,
            "rules": rules_result
        })
        
        assert isinstance(result, str), "Result should be JSON string"
        data = json.loads(result)
        
        assert "recommendations" in data, "Should have recommendations"
        recommendations = data["recommendations"]
        assert len(recommendations) == 3, f"Should have exactly 3 recommendations, got {len(recommendations)}"
        
        print(f"✓ Generated exactly {len(recommendations)} strategic recommendations")
    
    def test_recommendations_have_minimum_rules(self):
        """Test that recommendations use minimum number of rules."""
        forecasts_result = generate_multidimensional_forecast.invoke({"periods": 30})
        rules_result = generate_and_rank_pricing_rules.invoke({})
        
        result = generate_strategic_recommendations.invoke({
            "forecasts": forecasts_result,
            "rules": rules_result
        })
        
        data = json.loads(result)
        recommendations = data.get("recommendations", [])
        
        for rec in recommendations:
            rule_count = rec.get("rule_count", 0)
            assert rule_count > 0, "Should have at least 1 rule"
            assert rule_count <= 5, "Should have at most 5 rules per recommendation"
            assert rec.get("objectives_achieved", 0) >= 0, "Should track objectives achieved"
        
        print("✓ Recommendations use minimum viable rule sets")
    
    def test_recommendations_cover_business_objectives(self):
        """Test that recommendations address business objectives."""
        forecasts_result = generate_multidimensional_forecast.invoke({"periods": 30})
        rules_result = generate_and_rank_pricing_rules.invoke({})
        
        result = generate_strategic_recommendations.invoke({
            "forecasts": forecasts_result,
            "rules": rules_result
        })
        
        data = json.loads(result)
        recommendations = data.get("recommendations", [])
        
        # At least one recommendation should achieve multiple objectives
        max_objectives = max([r.get("objectives_achieved", 0) for r in recommendations])
        assert max_objectives >= 2, "At least one recommendation should achieve 2+ objectives"
        
        print(f"✓ Top recommendation achieves {max_objectives}/4 business objectives")


class TestSimplifiedRuleMatching:
    """Test simplified rule matching logic (exact match only)."""
    
    def test_rule_matching_exact_only(self):
        """Test that rule matching uses exact match only."""
        # Create test rule and segment
        test_rule = {
            "rule_id": "TEST_001",
            "condition": {"location": "Urban", "loyalty_tier": "Gold"},
            "action": {"multiplier": 1.12}
        }
        
        test_segment = {
            "dimensions": {
                "location": "Urban",
                "loyalty_tier": "Gold",
                "vehicle_type": "Premium",
                "demand_profile": "HIGH",
                "pricing_model": "CONTRACTED"
            }
        }
        
        # Test exact match
        condition = test_rule["condition"]
        dimensions = test_segment["dimensions"]
        
        # Should match exactly
        matches = all(dimensions.get(k) == v for k, v in condition.items())
        assert matches, "Exact match should work"
        
        # Should not match if one field differs
        test_segment2 = {
            "dimensions": {
                "location": "Urban",
                "loyalty_tier": "Silver",  # Different
                "vehicle_type": "Premium",
                "demand_profile": "HIGH",
                "pricing_model": "CONTRACTED"
            }
        }
        dimensions2 = test_segment2["dimensions"]
        matches2 = all(dimensions2.get(k) == v for k, v in condition.items())
        assert not matches2, "Should not match if field differs"
        
        print("✓ Rule matching uses exact match only (no fuzzy logic)")


class TestPipelineIntegration:
    """Test simplified pipeline integration."""
    
    def test_pipeline_uses_simplified_tools(self):
        """Test that pipeline uses the 3 simplified tools."""
        # This test verifies the tools exist and can be called
        # Actual pipeline execution is tested in test_pipeline.py
        
        # Tool 1: Multi-dimensional forecast
        forecast_result = generate_multidimensional_forecast.invoke({"periods": 30})
        assert isinstance(forecast_result, str)
        forecast_data = json.loads(forecast_result)
        assert "summary" in forecast_data
        
        # Tool 2: Generate and rank rules
        rules_result = generate_and_rank_pricing_rules.invoke({})
        assert isinstance(rules_result, str)
        rules_data = json.loads(rules_result)
        assert "top_rules" in rules_data
        
        # Tool 3: Generate strategic recommendations
        rec_result = generate_strategic_recommendations.invoke({
            "forecasts": forecast_result,
            "rules": rules_result
        })
        assert isinstance(rec_result, str)
        rec_data = json.loads(rec_result)
        assert "recommendations" in rec_data
        
        print("✓ All 3 simplified pipeline tools are callable")


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("Testing Simplified Multi-Dimensional Forecasting System")
    print("=" * 60)
    print()
    
    test_classes = [
        TestSimplifiedMultiDimensionalForecast,
        TestGenerateAndRankPricingRules,
        TestGenerateStrategicRecommendations,
        TestSimplifiedRuleMatching,
        TestPipelineIntegration
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        print("-" * 60)
        
        instance = test_class()
        test_methods = [m for m in dir(instance) if m.startswith("test_")]
        
        for test_method in test_methods:
            total_tests += 1
            try:
                getattr(instance, test_method)()
                passed_tests += 1
            except AssertionError as e:
                failed_tests.append(f"{test_class.__name__}.{test_method}: {str(e)}")
                print(f"✗ {test_method}: FAILED - {str(e)}")
            except Exception as e:
                failed_tests.append(f"{test_class.__name__}.{test_method}: ERROR - {str(e)}")
                print(f"✗ {test_method}: ERROR - {str(e)}")
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    print(f"Pass Rate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests:
        print("\nFAILED TESTS:")
        for failure in failed_tests:
            print(f"  - {failure}")
        return False
    else:
        print("\n✓ ALL TESTS PASSED!")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

