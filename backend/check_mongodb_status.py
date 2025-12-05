#!/usr/bin/env python3
"""
Quick MongoDB Database Check
Checks all collections and their document counts
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Import after path is set
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

async def check_mongodb():
    """Check MongoDB collections and data."""
    print("=" * 70)
    print("🗄️  MONGODB DATABASE STATUS CHECK")
    print("=" * 70)
    
    try:
        # Connection info
        mongo_url = settings.mongodb_url
        db_name = settings.mongodb_db_name
        
        # Hide sensitive parts of URL
        display_url = mongo_url.split('@')[-1] if '@' in mongo_url else mongo_url
        
        print(f"\n📍 Connection Info:")
        print(f"   Database: {db_name}")
        print(f"   Host: {display_url}")
        
        # Connect
        print(f"\n🔌 Connecting to MongoDB...")
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Test connection
        await client.admin.command('ping')
        print(f"   ✅ Connection successful!")
        
        # List all collections
        print(f"\n📂 Collections in database '{db_name}':")
        collections = await db.list_collection_names()
        
        if not collections:
            print("   ⚠️  No collections found in database")
            return
        
        # Count documents in each collection
        collection_data = []
        for coll_name in sorted(collections):
            try:
                count = await db[coll_name].count_documents({})
                collection_data.append((coll_name, count))
            except Exception as e:
                collection_data.append((coll_name, f"Error: {e}"))
        
        # Display results
        max_name_len = max(len(name) for name, _ in collection_data)
        
        for coll_name, count in collection_data:
            if isinstance(count, int):
                status = "✅" if count > 0 else "⚠️ "
                print(f"   {status} {coll_name:<{max_name_len}} : {count:>6} documents")
            else:
                print(f"   ❌ {coll_name:<{max_name_len}} : {count}")
        
        # Check specific important collections
        print(f"\n🔍 Key Collections Status:")
        
        important_collections = {
            "historical_rides": "Historical ride data for pricing",
            "orders": "Created ride orders",
            "ride_orders": "Alternative orders collection",
            "events_data": "Event data from n8n",
            "traffic_data": "Traffic data from n8n",
            "news_articles": "News data from n8n",
            "pipeline_results": "Agent pipeline results"
        }
        
        for coll_name, description in important_collections.items():
            try:
                count = await db[coll_name].count_documents({})
                if count > 0:
                    print(f"   ✅ {coll_name}: {count} documents")
                    print(f"      └─ {description}")
                    
                    # Show sample document
                    sample = await db[coll_name].find_one({})
                    if sample:
                        # Show a few key fields
                        sample_keys = list(sample.keys())[:5]
                        print(f"      └─ Sample fields: {', '.join(sample_keys)}")
                else:
                    print(f"   ⚠️  {coll_name}: Empty")
                    print(f"      └─ {description}")
            except Exception as e:
                print(f"   ⚠️  {coll_name}: Error checking - {e}")
        
        # Summary
        print(f"\n📊 Summary:")
        total_collections = len(collections)
        non_empty_collections = sum(1 for _, count in collection_data if isinstance(count, int) and count > 0)
        total_documents = sum(count for _, count in collection_data if isinstance(count, int))
        
        print(f"   Total Collections: {total_collections}")
        print(f"   Non-Empty Collections: {non_empty_collections}")
        print(f"   Total Documents: {total_documents}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        has_historical = await db["historical_rides"].count_documents({}) > 0
        has_orders = await db["orders"].count_documents({}) > 0
        
        if not has_historical:
            print(f"   ⚠️  No historical data found")
            print(f"      └─ Upload historical ride data via the Data Upload tab")
            print(f"      └─ This data is needed for accurate price estimation")
        
        if not has_orders:
            print(f"   ℹ️  No orders created yet")
            print(f"      └─ Create orders via the Create Order tab to test the system")
        
        if has_historical:
            print(f"   ✅ Historical data available - pricing estimates will be accurate")
        
        # Close connection
        client.close()
        print(f"\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\n💡 Troubleshooting:")
        print(f"   1. Check if MongoDB is running")
        print(f"   2. Verify MONGO_URI in .env file")
        print(f"   3. Check network connection")
        return

if __name__ == "__main__":
    asyncio.run(check_mongodb())

