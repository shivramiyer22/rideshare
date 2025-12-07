"""
Validate Pipeline Results in MongoDB
=====================================
This script checks:
1. How many documents are in pipeline_results collection
2. How many documents are in pricing_strategies collection
3. The structure of per_segment_impacts
4. Total unique segments covered
5. Recommendations and pricing rules counts
"""

import os
import sys
import pymongo
from dotenv import load_dotenv
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

load_dotenv()


def validate_pipeline_results():
    """Validate pipeline results in MongoDB."""
    
    print("=" * 80)
    print("PIPELINE RESULTS VALIDATION")
    print("=" * 80)
    print()
    
    # Connect to MongoDB
    mongodb_url = os.getenv("MONGO_URI")
    mongodb_db = os.getenv("MONGO_DB_NAME", "rideshare")
    
    print(f"📊 Connecting to MongoDB: {mongodb_db}")
    print()
    
    client = pymongo.MongoClient(mongodb_url)
    db = client[mongodb_db]
    
    # ===================================================================
    # 1. Check pipeline_results collection
    # ===================================================================
    print("1️⃣  PIPELINE_RESULTS COLLECTION")
    print("-" * 80)
    
    pipeline_results = db["pipeline_results"]
    pipeline_count = pipeline_results.count_documents({})
    
    print(f"   Total pipeline runs: {pipeline_count}")
    
    if pipeline_count > 0:
        # Get latest pipeline run
        latest_pipeline = pipeline_results.find_one(
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
            
            # Analysis phase
            analysis = results.get("analysis", {})
            pricing_rules = analysis.get("pricing_rules", [])
            print(f"   Pricing rules: {len(pricing_rules)}")
            
            # Recommendation phase
            recommendation = results.get("recommendation", {})
            recommendations = recommendation.get("recommendations", [])
            per_segment_impacts = recommendation.get("per_segment_impacts", {})
            
            print(f"   Recommendations: {len(recommendations)}")
            
            # Count per_segment_impacts
            if per_segment_impacts:
                total_impacts = sum(len(impacts) for impacts in per_segment_impacts.values())
                
                # Get unique segments across all recommendations
                unique_segments = set()
                for rec_name, impacts in per_segment_impacts.items():
                    print(f"     - {rec_name}: {len(impacts)} segment impacts")
                    for impact in impacts:
                        segment_key = impact.get("segment_key")
                        if segment_key:
                            unique_segments.add(segment_key)
                
                print(f"   Total segment impacts: {total_impacts}")
                print(f"   Unique segments covered: {len(unique_segments)}")
                print()
                
                # Expected: 162 unique segments
                if len(unique_segments) < 162:
                    print(f"   ⚠️  WARNING: Expected 162 unique segments, found {len(unique_segments)}")
                    print(f"   Missing segments: {162 - len(unique_segments)}")
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
    strategies_count = pricing_strategies.count_documents({})
    
    print(f"   Total documents: {strategies_count}")
    
    if strategies_count > 0:
        # Get latest strategy document
        latest_strategy = pricing_strategies.find_one(
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
            
            # Check pricing rules per recommendation
            if recommendations:
                print()
                print("   Pricing Rules per Recommendation:")
                for rec in recommendations:
                    rec_name = rec.get("name", "Unknown")
                    rule_ids = rec.get("rule_ids", [])
                    print(f"     - {rec_name}: {len(rule_ids)} rules")
                    
                    if len(rule_ids) == 0:
                        print(f"       ⚠️  WARNING: No rules associated!")
                    elif len(rule_ids) == 1:
                        print(f"       ⚠️  WARNING: Only 1 rule (expected multiple)")
            
            print()
            print(f"   Metadata:")
            print(f"     - Total segments: {metadata.get('total_segments')}")
            print(f"     - Recommendation count: {metadata.get('recommendation_count')}")
            print(f"     - Pricing rules count: {metadata.get('pricing_rules_count')}")
            
            # Check per_segment_impacts
            if per_segment_impacts:
                unique_segments = set()
                for rec_name, impacts in per_segment_impacts.items():
                    for impact in impacts:
                        segment_key = impact.get("segment_key")
                        if segment_key:
                            unique_segments.add(segment_key)
                
                print(f"     - Unique segments: {len(unique_segments)}")
                
                if len(unique_segments) < 162:
                    print(f"     ⚠️  WARNING: Expected 162 unique segments, found {len(unique_segments)}")
                else:
                    print(f"     ✅ All 162 segments covered!")
            
            print()
    else:
        print("   ❌ No pricing strategies found")
        print()
    
    # ===================================================================
    # 3. Summary and Recommendations
    # ===================================================================
    print("3️⃣  SUMMARY & RECOMMENDATIONS")
    print("-" * 80)
    print()
    
    issues = []
    
    # Check if we have pipeline results
    if pipeline_count == 0:
        issues.append("No pipeline runs found - need to trigger pipeline")
    
    # Check unique segments
    if pipeline_count > 0 and latest_pipeline:
        results = latest_pipeline.get("results", {})
        recommendation = results.get("recommendation", {})
        per_segment_impacts = recommendation.get("per_segment_impacts", {})
        
        if per_segment_impacts:
            unique_segments = set()
            for rec_name, impacts in per_segment_impacts.items():
                for impact in impacts:
                    segment_key = impact.get("segment_key")
                    if segment_key:
                        unique_segments.add(segment_key)
            
            if len(unique_segments) < 162:
                issues.append(f"Only {len(unique_segments)}/162 unique segments covered - need to improve forecast coverage")
    
    # Check pricing rules
    if strategies_count > 0 and latest_strategy:
        recommendations = latest_strategy.get("recommendations", [])
        pricing_rules = latest_strategy.get("pricing_rules", [])
        
        if len(pricing_rules) < 9:
            issues.append(f"Only {len(pricing_rules)} pricing rules (expected at least 9 for all categories)")
        
        # Check rules per recommendation
        for rec in recommendations:
            rec_name = rec.get("name", "Unknown")
            rule_ids = rec.get("rule_ids", [])
            if len(rule_ids) <= 1:
                issues.append(f"Recommendation '{rec_name}' has {len(rule_ids)} rule(s) - should have multiple")
    
    if issues:
        print("⚠️  ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print("✅ All validations passed!")
    
    print()
    print("=" * 80)
    
    client.close()
    
    return {
        "pipeline_count": pipeline_count,
        "strategies_count": strategies_count,
        "issues": issues
    }


if __name__ == "__main__":
    result = validate_pipeline_results()
    
    # Exit with error code if issues found
    if result["issues"]:
        sys.exit(1)
    else:
        sys.exit(0)


