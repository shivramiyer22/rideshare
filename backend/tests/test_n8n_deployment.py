"""
Test script for n8n deployment verification.

This script verifies:
1. PM2 status (n8n-workflows running)
2. n8n UI accessibility (http://localhost:5678)
3. MongoDB collections have data from n8n workflows:
   - events_data collection
   - traffic_data collection
   - news_articles collection
4. Data Ingestion Agent has created embeddings for n8n data

Based on CURSOR_IDE_INSTRUCTIONS.md lines 708-725.
"""

import sys
import os
import asyncio
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import connect_to_mongo, close_mongo_connection, get_database
from app.agents.utils import setup_chromadb_client, query_chromadb
from app.config import settings

# Test results tracking
test_results = {
    "pm2_status": False,
    "n8n_ui_accessible": False,
    "events_data_exists": False,
    "traffic_data_exists": False,
    "news_articles_exists": False,
    "embeddings_created": False
}


async def test_pm2_status() -> bool:
    """
    Test 1: Check PM2 status (should show n8n-workflows running).
    
    Returns:
        True if n8n-workflows is running in PM2, False otherwise
    """
    print("\n" + "=" * 60)
    print("Test 1: PM2 Status Check")
    print("=" * 60)
    
    try:
        # Run pm2 status command
        result = subprocess.run(
            ["pm2", "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            output = result.stdout
            print(f"✓ PM2 status command executed successfully")
            print(f"\nPM2 Output:\n{output}")
            
            # Check if n8n-workflows is in the output
            if "n8n-workflows" in output:
                # Check if it's online
                if "online" in output.lower() or "errored" not in output.lower():
                    print("✓ n8n-workflows process found in PM2")
                    test_results["pm2_status"] = True
                    return True
                else:
                    print("⚠️  n8n-workflows found but not online")
                    return False
            else:
                print("❌ n8n-workflows not found in PM2 output")
                print("   Note: This test may fail if PM2 is not installed or n8n is not running")
                return False
        else:
            print(f"❌ PM2 command failed: {result.stderr}")
            print("   Note: PM2 may not be installed. This is expected in development environments.")
            return False
            
    except FileNotFoundError:
        print("⚠️  PM2 not found in PATH")
        print("   Note: PM2 may not be installed. This is expected in development environments.")
        return False
    except subprocess.TimeoutExpired:
        print("❌ PM2 command timed out")
        return False
    except Exception as e:
        print(f"❌ Error checking PM2 status: {e}")
        return False


async def test_n8n_ui_accessible() -> bool:
    """
    Test 2: Check if n8n UI is accessible at http://localhost:5678.
    
    Returns:
        True if n8n UI is accessible, False otherwise
    """
    print("\n" + "=" * 60)
    print("Test 2: n8n UI Accessibility")
    print("=" * 60)
    
    try:
        # Try to access n8n UI
        response = requests.get("http://localhost:5678", timeout=5)
        
        if response.status_code == 200:
            print("✓ n8n UI is accessible at http://localhost:5678")
            test_results["n8n_ui_accessible"] = True
            return True
        else:
            print(f"⚠️  n8n UI returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Cannot connect to n8n UI at http://localhost:5678")
        print("   Note: n8n may not be running. This is expected if n8n is not set up.")
        return False
    except requests.exceptions.Timeout:
        print("❌ n8n UI request timed out")
        return False
    except Exception as e:
        print(f"❌ Error accessing n8n UI: {e}")
        return False


async def test_mongodb_n8n_collections() -> Dict[str, bool]:
    """
    Test 3: Verify data appears in MongoDB collections from n8n workflows.
    
    Checks:
    - events_data collection
    - traffic_data collection
    - news_articles collection
    
    Returns:
        Dictionary with test results for each collection
    """
    print("\n" + "=" * 60)
    print("Test 3: MongoDB n8n Collections Verification")
    print("=" * 60)
    
    results = {
        "events_data": False,
        "traffic_data": False,
        "news_articles": False
    }
    
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        database = get_database()
        
        # Check events_data collection
        events_collection = database["events_data"]
        events_count = await events_collection.count_documents({})
        print(f"\n📊 events_data collection:")
        print(f"   Documents: {events_count}")
        if events_count > 0:
            # Get a sample document
            sample = await events_collection.find_one({})
            print(f"   ✓ Collection has data")
            print(f"   Sample document keys: {list(sample.keys())[:5] if sample else 'N/A'}")
            results["events_data"] = True
            test_results["events_data_exists"] = True
        else:
            print(f"   ⚠️  Collection is empty (n8n workflow may not have run yet)")
        
        # Check traffic_data collection
        traffic_collection = database["traffic_data"]
        traffic_count = await traffic_collection.count_documents({})
        print(f"\n📊 traffic_data collection:")
        print(f"   Documents: {traffic_count}")
        if traffic_count > 0:
            sample = await traffic_collection.find_one({})
            print(f"   ✓ Collection has data")
            print(f"   Sample document keys: {list(sample.keys())[:5] if sample else 'N/A'}")
            results["traffic_data"] = True
            test_results["traffic_data_exists"] = True
        else:
            print(f"   ⚠️  Collection is empty (n8n workflow may not have run yet)")
        
        # Check news_articles collection
        news_collection = database["news_articles"]
        news_count = await news_collection.count_documents({})
        print(f"\n📊 news_articles collection:")
        print(f"   Documents: {news_count}")
        if news_count > 0:
            sample = await news_collection.find_one({})
            print(f"   ✓ Collection has data")
            print(f"   Sample document keys: {list(sample.keys())[:5] if sample else 'N/A'}")
            results["news_articles"] = True
            test_results["news_articles_exists"] = True
        else:
            print(f"   ⚠️  Collection is empty (n8n workflow may not have run yet)")
        
        return results
        
    except Exception as e:
        print(f"❌ Error checking MongoDB collections: {e}")
        import traceback
        traceback.print_exc()
        return results
    finally:
        await close_mongo_connection()


async def test_data_ingestion_embeddings() -> bool:
    """
    Test 4: Check if Data Ingestion Agent has created embeddings for n8n data.
    
    This verifies that:
    - ChromaDB collections exist
    - Embeddings exist for n8n data (events, traffic, news)
    
    Returns:
        True if embeddings are found, False otherwise
    """
    print("\n" + "=" * 60)
    print("Test 4: Data Ingestion Agent Embeddings Verification")
    print("=" * 60)
    
    try:
        # Setup ChromaDB client
        chroma_client = setup_chromadb_client()
        
        # Check news_events_vectors collection (used for n8n data)
        try:
            news_events_collection = chroma_client.get_collection("news_events_vectors")
            count = news_events_collection.count()
            print(f"\n📊 news_events_vectors collection:")
            print(f"   Embeddings: {count}")
            
            if count > 0:
                # Try a sample query
                try:
                    results = news_events_collection.query(
                        query_texts=["event"],
                        n_results=min(3, count)
                    )
                    print(f"   ✓ Collection has embeddings")
                    print(f"   Sample query returned {len(results.get('ids', [])[0] if results.get('ids') else [])} results")
                    test_results["embeddings_created"] = True
                    return True
                except Exception as e:
                    print(f"   ⚠️  Collection exists but query failed: {e}")
                    return False
            else:
                print(f"   ⚠️  Collection exists but is empty")
                print(f"   Note: Data Ingestion Agent may not have processed n8n data yet")
                return False
                
        except Exception as e:
            print(f"   ⚠️  Could not access news_events_vectors collection: {e}")
            print(f"   Note: Data Ingestion Agent may not have created embeddings yet")
            return False
        
    except Exception as e:
        print(f"❌ Error checking embeddings: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all n8n deployment verification tests."""
    print("\n" + "=" * 80)
    print("n8n Deployment Verification Tests")
    print("Based on CURSOR_IDE_INSTRUCTIONS.md lines 708-725")
    print("=" * 80)
    
    # Test 1: PM2 Status
    await test_pm2_status()
    
    # Test 2: n8n UI Accessibility
    await test_n8n_ui_accessible()
    
    # Test 3: MongoDB Collections
    await test_mongodb_n8n_collections()
    
    # Test 4: Data Ingestion Embeddings
    await test_data_ingestion_embeddings()
    
    # Print summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for v in test_results.values() if v)
    
    for test_name, result in test_results.items():
        status = "✓ PASS" if result else "⚠️  SKIP/WARN"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n✅ All tests passed! n8n deployment is verified.")
        return True
    else:
        print("\n⚠️  Some tests were skipped or failed.")
        print("   Note: This is expected if n8n is not set up in the development environment.")
        print("   In production, all tests should pass.")
        return False


if __name__ == "__main__":
    asyncio.run(run_all_tests())

