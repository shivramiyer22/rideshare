"""
Check if pipeline data exists for segment dynamic pricing report
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json

load_dotenv()

async def check_pipeline_data():
    """Check if we have pipeline data with per_segment_impacts."""
    print("=" * 60)
    print("CHECKING PIPELINE DATA FOR REPORTS")
    print("=" * 60)
    
    try:
        mongodb_url = os.getenv("MONGO_URI")
        mongodb_db = os.getenv("MONGO_DB_NAME", "rideshare")
        
        client = AsyncIOMotorClient(mongodb_url)
        db = client[mongodb_db]
        
        # Check 1: pipeline_results collection
        print("\n1. Checking 'pipeline_results' collection:")
        pipeline_count = await db["pipeline_results"].count_documents({})
        print(f"   Total pipeline runs: {pipeline_count}")
        
        if pipeline_count > 0:
            # Get latest pipeline result
            latest = await db["pipeline_results"].find_one(
                {},
                sort=[("completed_at", -1)]
            )
            print(f"\n   Latest pipeline run:")
            print(f"   - ID: {latest.get('_id')}")
            print(f"   - Run ID: {latest.get('run_id')}")
            print(f"   - Status: {latest.get('status')}")
            print(f"   - Completed: {latest.get('completed_at')}")
            
            # Check if it has per_segment_impacts
            results = latest.get('results', {})
            recommendations = results.get('recommendations', {})
            per_segment_impacts = recommendations.get('per_segment_impacts', {})
            
            if per_segment_impacts:
                rec1_count = len(per_segment_impacts.get('recommendation_1', []))
                rec2_count = len(per_segment_impacts.get('recommendation_2', []))
                rec3_count = len(per_segment_impacts.get('recommendation_3', []))
                total = rec1_count + rec2_count + rec3_count
                
                print(f"\n   ✓ Has per_segment_impacts:")
                print(f"   - Recommendation 1: {rec1_count} segments")
                print(f"   - Recommendation 2: {rec2_count} segments")
                print(f"   - Recommendation 3: {rec3_count} segments")
                print(f"   - Total records: {total}")
                
                if total > 0:
                    print(f"\n   ✅ DATA AVAILABLE - Report should work!")
                else:
                    print(f"\n   ⚠️  per_segment_impacts is empty")
            else:
                print(f"\n   ⚠️  No per_segment_impacts found in latest run")
        else:
            print("\n   ⚠️  No pipeline runs found!")
        
        # Check 2: pricing_strategies collection
        print("\n2. Checking 'pricing_strategies' collection:")
        strategies_count = await db["pricing_strategies"].count_documents({})
        print(f"   Total strategies: {strategies_count}")
        
        if strategies_count > 0:
            latest_strategy = await db["pricing_strategies"].find_one(
                {},
                sort=[("timestamp", -1)]
            )
            impacts = latest_strategy.get('per_segment_impacts', {})
            if impacts:
                total = sum(len(v) for v in impacts.values())
                print(f"   ✓ Latest strategy has {total} segment records")
            else:
                print(f"   ⚠️  No per_segment_impacts in latest strategy")
        
        # Check 3: Other required data
        print("\n3. Checking required baseline data:")
        historical_rides = await db["historical_rides"].count_documents({})
        competitor_prices = await db["competitor_prices"].count_documents({})
        
        print(f"   - Historical rides: {historical_rides}")
        print(f"   - Competitor prices: {competitor_prices}")
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        if pipeline_count == 0:
            print("\n❌ NO PIPELINE DATA")
            print("\nTo generate data, you need to:")
            print("1. Run the data ingestion pipeline")
            print("2. Execute: POST /api/v1/pipeline/run")
            print("3. Wait for pipeline to complete (~2-3 minutes)")
            print("4. Then try the report API again")
        elif pipeline_count > 0 and per_segment_impacts and sum(len(v) for v in per_segment_impacts.values()) > 0:
            print("\n✅ DATA AVAILABLE")
            print("\nYou can generate the report!")
            print(f"\nTry: curl 'http://localhost:8000/api/v1/reports/segment-dynamic-pricing-analysis?format=csv'")
        else:
            print("\n⚠️  PIPELINE DATA EXISTS BUT NO SEGMENT IMPACTS")
            print("\nThe pipeline may have run with old code.")
            print("Solution: Re-run the pipeline to generate per_segment_impacts data")
            print("\nExecute: POST /api/v1/pipeline/run")
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_pipeline_data())

