"""
Direct MongoDB Validation - Check Pipeline Results
===================================================
This script connects directly to MongoDB async (like the backend does)
to validate pipeline results.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from typing import Dict, Any, Set
import json

load_dotenv()


async def validate_pipeline_results():
    """Validate pipeline results in MongoDB (async)."""
    
    print("=" * 80)
    print("PIPELINE RESULTS VALIDATION (Direct MongoDB)")
    print("=" * 80)
    print()
    
    # Connect to MongoDB
    mongodb_url = os.getenv("MONGO_URI")
    mongodb_db = os.getenv("MONGO_DB_NAME", "rideshare")
    
    print(f"📊 Connecting to MongoDB: {mongodb_db}")
    print()
    
    client = AsyncIOMotorClient(mongodb_url)
    db = client[mongodb_db]
    
    # ===================================================================
    # 1. Check pipeline_results collection
    # ===================================================================
    print("1️⃣  PIPELINE_RESULTS COLLECTION")
    print("-" * 80)
    
    pipeline_results = db["pipeline_results"]
    pipeline_count = await pipeline_results.count_documents({})
    
    print(f"   Total pipeline runs: {pipeline_count}")
    
    if pipeline_count > 0:
        # Get latest pipeline run
        latest_pipeline = await pipeline_results.find_one(
            {},
            sort=[("started_at", -1)]
        )
        
        if latest_pipeline:
            print(f"   Latest run_id: {latest_pipeline.get('run_id')}")
            print(f"   Started at: {latest_pipeline.get('started_at')}")
            print(f"   Status: {latest_pipeline.get('status')}")
            
            # Check results structure
            results = latest_pipeline.get("results", {})
            
            # Forecasting phase
            forecasting = results.get("forecasting", {})
            forecasts = forecasting.get("forecasts", {})
            segmented_forecasts = forecasts.get("segmented_forecasts", [])
            aggregated_forecasts = forecasts.get("aggregated_forecasts", [])
            
            print(f"   Segmented forecasts: {len(segmented_forecasts)}")
            print(f"   Aggregated forecasts: {len(aggregated_forecasts)}")
            print(f"   TOTAL forecasts: {len(segmented_forecasts) + len(aggregated_forecasts)}")
            
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
                    rule_ids = rec.get("rules", [])  # Note: might be "rules" not "rule_ids"
                    objectives_met = rec.get("objectives_achieved", 0)
                    revenue_impact = rec.get("revenue_impact", "0%")
                    
                    print(f"     - {rec_name}:")
                    print(f"       Rules: {len(rule_ids)}")
                    print(f"       Objectives met: {objectives_met}")
                    print(f"       Revenue impact: {revenue_impact}")
                    
                    if len(rule_ids) == 0:
                        print(f"       ⚠️  WARNING: No rules associated!")
                    elif len(rule_ids) == 1:
                        print(f"       ⚠️  WARNING: Only 1 rule (expected multiple)")
            
            # Count per_segment_impacts
            print()
            if per_segment_impacts:
                total_impacts = sum(len(impacts) for impacts in per_segment_impacts.values())
                
                # Get unique segments across all recommendations
                unique_segments: Set[str] = set()
                for rec_name, impacts in per_segment_impacts.items():
                    print(f"   {rec_name}: {len(impacts)} segment impacts")
                    for impact in impacts:
                        segment_key = impact.get("segment_key")
                        if segment_key:
                            unique_segments.add(segment_key)
                        else:
                            # Build segment_key from segment dict
                            segment = impact.get("segment", {})
                            segment_key = f"{segment.get('location_category')}_{segment.get('loyalty_tier')}_{segment.get('vehicle_type')}_{segment.get('pricing_model')}_{segment.get('demand_profile')}"
                            if segment_key != "____":  # Valid key
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
    else:
        print("   ❌ No pipeline runs found")
        print()
    
    # ===================================================================
    # 2. Check pricing_strategies collection
    # ===================================================================
    print("2️⃣  PRICING_STRATEGIES COLLECTION")
    print("-" * 80)
    
    pricing_strategies = db["pricing_strategies"]
    strategies_count = await pricing_strategies.count_documents({})
    
    print(f"   Total documents: {strategies_count}")
    
    if strategies_count > 0:
        # Get latest strategy document
        latest_strategy = await pricing_strategies.find_one(
            {},
            sort=[("timestamp", -1)]
        )
        
        if latest_strategy:
            print(f"   Latest pipeline_run_id: {latest_strategy.get('pipeline_run_id')}")
            print(f"   Timestamp: {latest_strategy.get('timestamp')}")
            
            recommendations = latest_strategy.get("recommendations", [])
            pricing_rules = latest_strategy.get("pricing_rules", [])
            per_segment_impacts = latest_strategy.get("per_segment_impacts", {})
            metadata = latest_strategy.get("metadata", {})
            
            print(f"   Recommendations: {len(recommendations)}")
            print(f"   Pricing rules: {len(pricing_rules)}")
            
            if per_segment_impacts:
                unique_segments: Set[str] = set()
                for rec_name, impacts in per_segment_impacts.items():
                    for impact in impacts:
                        segment_key = impact.get("segment_key")
                        if segment_key:
                            unique_segments.add(segment_key)
                        else:
                            segment = impact.get("segment", {})
                            segment_key = f"{segment.get('location_category')}_{segment.get('loyalty_tier')}_{segment.get('vehicle_type')}_{segment.get('pricing_model')}_{segment.get('demand_profile')}"
                            if segment_key != "____":
                                unique_segments.add(segment_key)
                
                print(f"   Unique segments: {len(unique_segments)}")
                
                if len(unique_segments) < 162:
                    print(f"   ⚠️  Expected 162, found {len(unique_segments)}")
                else:
                    print(f"   ✅ All 162 segments covered!")
            
            print()
    else:
        print("   ❌ No pricing strategies found")
        print()
    
    client.close()
    
    print("=" * 80)


def generate_all_162_segments() -> Set[str]:
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
    asyncio.run(validate_pipeline_results())


