"""
Debug GET Orders API issue - Check actual data structure
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json

load_dotenv()

async def debug_orders():
    """Debug orders collection to see actual data structure."""
    print("=" * 60)
    print("DEBUGGING GET ORDERS API ISSUE")
    print("=" * 60)
    
    try:
        mongodb_url = os.getenv("MONGO_URI")
        mongodb_db = os.getenv("MONGO_DB_NAME", "rideshare")
        
        client = AsyncIOMotorClient(mongodb_url)
        db = client[mongodb_db]
        
        # Check orders collection
        print("\n1. Checking 'orders' collection:")
        orders_count = await db["orders"].count_documents({})
        print(f"   Total documents: {orders_count}")
        
        if orders_count > 0:
            print("\n2. Sample order structure (first order):")
            order = await db["orders"].find_one({})
            print(json.dumps(order, indent=2, default=str))
            
            print("\n3. All order IDs:")
            cursor = db["orders"].find({}, {"id": 1, "_id": 1, "user_id": 1, "status": 1})
            orders = await cursor.to_list(length=100)
            for i, o in enumerate(orders[:10], 1):
                print(f"   {i}. ID: {o.get('id', 'N/A')}, _id: {o.get('_id')}, user_id: {o.get('user_id', 'N/A')}, status: {o.get('status', 'N/A')}")
            
            print("\n4. Testing the query that the API uses:")
            cursor = db["orders"].find({}).sort("created_at", -1).limit(100)
            api_orders = await cursor.to_list(length=100)
            print(f"   Query returned: {len(api_orders)} orders")
            
            if len(api_orders) == 0:
                print("   ⚠️  Query returned 0 orders even though collection has data!")
                print("   Possible issues:")
                print("   - Sort field 'created_at' might not exist in all documents")
                print("   - Date format might be incorrect")
            
            print("\n5. Checking for 'created_at' field:")
            has_created_at = await db["orders"].count_documents({"created_at": {"$exists": True}})
            print(f"   Documents with 'created_at' field: {has_created_at}/{orders_count}")
            
            if has_created_at < orders_count:
                print("   ⚠️  Some documents missing 'created_at' field!")
                print("   This causes sort to fail silently")
            
        else:
            print("   ⚠️  No orders found!")
        
        client.close()
        
        print("\n" + "=" * 60)
        print("DEBUG COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_orders())
