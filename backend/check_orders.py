"""
Quick diagnostic script to check orders in MongoDB
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import get_database
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

async def check_orders():
    """Check orders in MongoDB."""
    print("=" * 60)
    print("ORDERS DIAGNOSTIC CHECK")
    print("=" * 60)
    
    # Check connection
    print(f"\n1. MongoDB URI: {settings.mongodb_url[:30]}...")
    print(f"   Database: {settings.mongodb_db_name}")
    
    try:
        # Connect directly
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.mongodb_db_name]
        
        # List all collections
        print("\n2. Available Collections:")
        collections = await db.list_collection_names()
        for coll in collections:
            count = await db[coll].count_documents({})
            print(f"   - {coll}: {count} documents")
        
        # Check ride_orders specifically
        print("\n3. Checking 'ride_orders' collection:")
        ride_orders_count = await db["ride_orders"].count_documents({})
        print(f"   Total documents: {ride_orders_count}")
        
        if ride_orders_count > 0:
            print("\n4. Sample orders (first 3):")
            cursor = db["ride_orders"].find({}).limit(3)
            orders = await cursor.to_list(length=3)
            for i, order in enumerate(orders, 1):
                print(f"\n   Order {i}:")
                print(f"      ID: {order.get('id', order.get('_id', 'N/A'))}")
                print(f"      User: {order.get('user_id', 'N/A')}")
                print(f"      Status: {order.get('status', 'N/A')}")
                print(f"      Created: {order.get('created_at', 'N/A')}")
                print(f"      Estimated Price: ${order.get('estimated_price', order.get('price', 0))}")
        else:
            print("   ⚠️  No orders found in 'ride_orders' collection!")
            print("\n   Possible reasons:")
            print("   1. No orders have been created yet via POST /orders")
            print("   2. Orders might be in a different collection")
            print("   3. Database name mismatch")
        
        # Check for orders in other potential collections
        print("\n5. Checking other potential order collections:")
        for coll_name in ["orders", "ride_order", "order"]:
            if coll_name in collections:
                count = await db[coll_name].count_documents({})
                print(f"   - {coll_name}: {count} documents")
                if count > 0:
                    sample = await db[coll_name].find_one({})
                    print(f"     Sample ID: {sample.get('id', sample.get('_id'))}")
        
        print("\n" + "=" * 60)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 60)
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease check:")
        print("1. MongoDB is running")
        print("2. MONGO_URI in .env is correct")
        print("3. Database name in .env matches your setup")

if __name__ == "__main__":
    asyncio.run(check_orders())
