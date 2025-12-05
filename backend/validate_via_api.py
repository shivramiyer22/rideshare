"""
Validate Pipeline Results via API
==================================
This script uses the backend API to check pipeline results
"""

import requests
import json
from typing import Dict, Any

API_BASE = "http://localhost:8000/api/v1"


def validate_pipeline_via_api():
    """Validate pipeline results using the backend API."""
    
    print("=" * 80)
    print("PIPELINE RESULTS VALIDATION (via API)")
    print("=" * 80)
    print()
    
    # ===================================================================
    # 1. Get pipeline history
    # ===================================================================
    print("1️⃣  FETCHING PIPELINE HISTORY")
    print("-" * 80)
    
    try:
        response = requests.get(f"{API_BASE}/pipeline/history", timeout=10)
        response.raise_for_status()
        result = response.json()
        
        # Handle different response formats
        if isinstance(result, dict) and "runs" in result:
            history = result["runs"]
        elif isinstance(result, list):
            history = result
        else:
            history = []
        
        print(f"   Total pipeline runs: {len(history)}")
        
        if history and len(history) > 0:
            latest = history[0]
            
            print(f"   Latest run_id: {latest.get('run_id')}")
            print(f"   Started at: {latest.get('started_at')}")
            print(f"   Status: {latest.get('status')}")
            
            # Check results structure
            results = latest.get("results", {})
            
            # Forecasting phase
            forecasting = results.get("forecasting", {})
            forecasts = forecasting.get("forecasts", {})
            segmented_forecasts = forecasts.get("segmented_forecasts", [])
            aggregated_forecasts = forecasts.get("aggregated_forecasts", [])
            
            print(f"   Segmented forecasts: {len(segmented_forecasts)}")
            print(f"   Aggregated forecasts: {len(aggregated_forecasts)}")
            
            # Analysis phase
            analysis = results.get("analysis", {})
            pricing_rules = analysis.get("pricing_rules", [])
            print(f"   Pricing rules: {len(pricing_rules)}")
            
            # Show rule categories
            if pricing_rules:
                print()
                print("   Pricing Rule Categories:")
                categories = {}
                for rule in pricing_rules:
                    category = rule.get("category", "Unknown")
                    categories[category] = categories.get(category, 0) + 1
                
                for category, count in sorted(categories.items()):
                    print(f"     - {category}: {count} rule(s)")
            
            # Recommendation phase
            recommendation = results.get("recommendation", {})
            recommendations = recommendation.get("recommendations", [])
            per_segment_impacts = recommendation.get("per_segment_impacts", {})
            
            print()
            print(f"   Recommendations: {len(recommendations)}")
            
            # Check recommendations structure
            if recommendations:
                print()
                print("   Recommendation Details:")
                for rec in recommendations:
                    rec_name = rec.get("name", "Unknown")
                    rule_ids = rec.get("rule_ids", [])
                    objectives_met = rec.get("objectives_met", [])
                    revenue_impact = rec.get("total_revenue_impact_percent", 0)
                    
                    print(f"     - {rec_name}:")
                    print(f"       Rules: {len(rule_ids)} ({', '.join(rule_ids) if len(rule_ids) <= 3 else f'{len(rule_ids)} rules'})")
                    print(f"       Objectives: {len(objectives_met)} ({', '.join(objectives_met) if len(objectives_met) <= 2 else f'{len(objectives_met)} objectives'})")
                    print(f"       Revenue impact: {revenue_impact:.2f}%")
                    
                    if len(rule_ids) == 0:
                        print(f"       ⚠️  WARNING: No rules associated!")
                    elif len(rule_ids) == 1:
                        print(f"       ⚠️  WARNING: Only 1 rule (expected multiple)")
            
            # Count per_segment_impacts
            print()
            if per_segment_impacts:
                total_impacts = sum(len(impacts) for impacts in per_segment_impacts.values())
                
                # Get unique segments across all recommendations
                unique_segments = set()
                for rec_name, impacts in per_segment_impacts.items():
                    print(f"   {rec_name}: {len(impacts)} segment impacts")
                    for impact in impacts:
                        segment_key = impact.get("segment_key")
                        if segment_key:
                            unique_segments.add(segment_key)
                
                print()
                print(f"   Total segment impacts: {total_impacts}")
                print(f"   Unique segments covered: {len(unique_segments)}")
                print()
                
                # Expected: 162 unique segments
                if len(unique_segments) < 162:
                    print(f"   ⚠️  WARNING: Expected 162 unique segments, found {len(unique_segments)}")
                    print(f"   Missing segments: {162 - len(unique_segments)}")
                    
                    # List some missing segments
                    all_segments = generate_all_162_segments()
                    missing = all_segments - unique_segments
                    if missing:
                        print()
                        print(f"   Sample missing segments (first 10):")
                        for i, seg in enumerate(sorted(missing)[:10], 1):
                            print(f"     {i}. {seg}")
                else:
                    print(f"   ✅ All 162 segments covered!")
            else:
                print("   ❌ No per_segment_impacts found")
            
            print()
            
            return {
                "pipeline_count": len(history),
                "latest_run": latest,
                "unique_segments": len(unique_segments) if per_segment_impacts else 0,
                "pricing_rules": len(pricing_rules),
                "recommendations": len(recommendations)
            }
        else:
            print("   ❌ No pipeline runs found")
            return {
                "pipeline_count": 0,
                "error": "No pipeline runs found"
            }
    
    except requests.exceptions.RequestException as e:
        print(f"   ❌ API Error: {e}")
        return {
            "error": str(e)
        }


def generate_all_162_segments() -> set:
    """Generate all 162 expected segment keys."""
    locations = ["Urban", "Suburban", "Rural"]
    loyalty_tiers = ["Gold", "Silver", "Regular"]
    vehicle_types = ["Premium", "Economy"]
    pricing_models = ["STANDARD", "CONTRACTED", "CUSTOM"]
    demand_profiles = ["HIGH", "MEDIUM", "LOW"]
    
    segments = set()
    for loc in locations:
        for loyalty in loyalty_tiers:
            for vehicle in vehicle_types:
                for pricing in pricing_models:
                    for demand in demand_profiles:
                        segment_key = f"{loc}_{loyalty}_{vehicle}_{pricing}_{demand}"
                        segments.add(segment_key)
    
    return segments


if __name__ == "__main__":
    result = validate_pipeline_via_api()
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if "error" in result:
        print(f"❌ Validation failed: {result['error']}")
    else:
        print(f"Pipeline runs: {result.get('pipeline_count', 0)}")
        print(f"Unique segments: {result.get('unique_segments', 0)}/162")
        print(f"Pricing rules: {result.get('pricing_rules', 0)}")
        print(f"Recommendations: {result.get('recommendations', 0)}")
    
    print()

