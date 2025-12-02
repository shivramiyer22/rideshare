#!/usr/bin/env python3
"""
n8n Workflows Verification Script

Verifies that n8n workflows are set up and data is flowing.
Based on CURSOR_IDE_INSTRUCTIONS.md lines 871-877.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

async def check_n8n_collections():
    """Check if n8n data collections exist and have data."""
    print("1. Checking n8n data collections in MongoDB...")
    
    try:
        client = AsyncIOMotorClient(settings.mongodb_url)
        database = client[settings.mongodb_db_name]
        
        collections_to_check = [
            "events_data",
            "traffic_data",
            "news_articles"
        ]
        
        results = []
        for collection_name in collections_to_check:
            collection = database[collection_name]
            count = await collection.count_documents({})
            
            if count > 0:
                print(f"   ✓ {collection_name}: {count} documents")
                results.append(True)
            else:
                print(f"   ⚠️  {collection_name}: No documents (n8n may not have run yet)")
                results.append(False)
        
        client.close()
        return any(results)  # At least one collection has data
        
    except Exception as e:
        print(f"   ⚠️  Could not check MongoDB: {e}")
        return False

def check_n8n_workflow_files():
    """Check if n8n workflow JSON files exist."""
    print("\n2. Checking n8n workflow files...")
    project_root = Path(__file__).parent.parent.parent
    n8n_dir = project_root / "n8n-workflows"
    
    if not n8n_dir.exists():
        print(f"   ⚠️  n8n-workflows directory not found: {n8n_dir}")
        return False
    
    expected_workflows = [
        "eventbrite-poller.json",
        "google-maps-traffic.json",
        "newsapi-poller.json"
    ]
    
    found_workflows = []
    for workflow in expected_workflows:
        workflow_file = n8n_dir / workflow
        if workflow_file.exists():
            found_workflows.append(workflow)
            print(f"   ✓ Found: {workflow}")
        else:
            print(f"   ⚠️  Missing: {workflow}")
    
    if len(found_workflows) == len(expected_workflows):
        print(f"   ✓ All {len(expected_workflows)} workflow files found")
        return True
    else:
        print(f"   ⚠️  Only {len(found_workflows)}/{len(expected_workflows)} workflow files found")
        return False

def check_data_ingestion_for_n8n():
    """Check if Data Ingestion Agent processes n8n data."""
    print("\n3. Checking Data Ingestion Agent processes n8n data...")
    backend_dir = Path(__file__).parent.parent
    agent_file = backend_dir / "app" / "agents" / "data_ingestion.py"
    
    if not agent_file.exists():
        print("   ❌ Data Ingestion Agent not found")
        return False
    
    try:
        with open(agent_file, 'r') as f:
            content = f.read()
            
            n8n_collections = ["events_data", "traffic_data", "news_articles"]
            found_collections = []
            
            for collection in n8n_collections:
                if collection in content:
                    found_collections.append(collection)
            
            if len(found_collections) == len(n8n_collections):
                print(f"   ✓ Data Ingestion Agent monitors all n8n collections")
                return True
            else:
                print(f"   ⚠️  Data Ingestion Agent monitors {len(found_collections)}/{len(n8n_collections)} n8n collections")
                return False
    except Exception as e:
        print(f"   ⚠️  Could not check: {e}")
        return False

async def main():
    """Run all n8n workflows verification checks."""
    print("=" * 80)
    print("n8n Workflows Verification")
    print("Based on CURSOR_IDE_INSTRUCTIONS.md lines 871-877")
    print("=" * 80)
    
    checks = [
        await check_n8n_collections(),
        check_n8n_workflow_files(),
        check_data_ingestion_for_n8n()
    ]
    
    print("\n" + "=" * 80)
    print("Verification Summary")
    print("=" * 80)
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✅ All checks passed: {passed}/{total}")
        return 0
    else:
        print(f"⚠️  Some checks failed: {passed}/{total}")
        print("   Note: n8n workflows need to be active and running")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))

