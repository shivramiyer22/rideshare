"""
Check pricing rules and diagnose pipeline issue
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json

load_dotenv()

async def check_pricing_rules():
    """Check if pricing rules exist."""
    print("=" * 60)
    print("DIAGNOSING PIPELINE FAILURE")
    print("=" * 60)
    
    try:
        mongodb_url = os.getenv("MONGO_URI")
        mongodb_db = os.getenv("MONGO_DB_NAME", "rideshare")
        
        client = AsyncIOMotorClient(mongodb_url)
        db = client[mongodb_db]
        
        # Check pricing_strategies collection
        print("\n1. Checking 'pricing_strategies' collection:")
        strategies = await db["pricing_strategies"].find({}).to_list(length=100)
        print(f"   Total documents: {len(strategies)}")
        
        if strategies:
            for idx, strategy in enumerate(strategies, 1):
                print(f"\n   Strategy {idx}:")
                print(f"   - ID: {strategy.get('_id')}")
                print(f"   - Pipeline Run ID: {strategy.get('pipeline_run_id', 'N/A')}")
                print(f"   - Timestamp: {strategy.get('timestamp', 'N/A')}")
                
                # Check if it has rules
                rules = strategy.get('rules', [])
                objectives = strategy.get('objectives', [])
                per_segment_impacts = strategy.get('per_segment_impacts', {})
                
                print(f"   - Rules: {len(rules)}")
                print(f"   - Objectives: {len(objectives)}")
                print(f"   - Per-segment impacts: {sum(len(v) for v in per_segment_impacts.values())}")
                
                if rules:
                    print(f"\n   Sample rules (first 3):")
                    for rule in rules[:3]:
                        print(f"     • {rule.get('rule_id', 'N/A')}: {rule.get('name', 'N/A')}")
        
        # Check ChromaDB vectors
        print("\n2. Checking for strategy knowledge in ChromaDB:")
        print("   (ChromaDB preserved during cache clear)")
        
        # Check latest pipeline run error
        print("\n3. Checking latest pipeline run details:")
        latest = await db["pipeline_results"].find_one(
            {},
            sort=[("completed_at", -1)]
        )
        
        if latest:
            print(f"   Run ID: {latest.get('run_id')}")
            print(f"   Status: {latest.get('status')}")
            
            results = latest.get('results', {})
            
            # Check each phase
            analysis_data = results.get('analysis', {}).get('data', {})
            forecasts_data = results.get('forecasts', {}).get('data', {})
            recommendations_data = results.get('recommendations', {})
            
            print(f"\n   Phase Results:")
            print(f"   - Analysis: {'✓' if analysis_data else '✗'}")
            print(f"   - Forecasts: {'✓' if forecasts_data else '✗'}")
            print(f"   - Recommendations: {'✗ Failed' if not recommendations_data or 'error' in recommendations_data else '✓'}")
            
            if 'error' in recommendations_data:
                print(f"   - Error: {recommendations_data.get('error')}")
        
        print("\n" + "=" * 60)
        print("DIAGNOSIS")
        print("=" * 60)
        
        if not strategies or all(not s.get('rules') for s in strategies):
            print("\n❌ NO PRICING RULES FOUND")
            print("\nThe pipeline needs pricing rules to generate recommendations.")
            print("\nSolution:")
            print("1. The Analysis Agent should generate rules from ChromaDB")
            print("2. Check if ChromaDB has strategy_knowledge_vectors")
            print("3. Verify OPENAI_API_KEY is set correctly")
            print("\nQuick fix - Run a simpler test:")
            print("  curl http://localhost:8000/api/v1/agent-tests/analysis")
        else:
            print("\n✓ Pricing rules exist")
            print("\nThe pipeline should work. Try running it again:")
            print("  POST /api/v1/pipeline/run")
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_pricing_rules())

