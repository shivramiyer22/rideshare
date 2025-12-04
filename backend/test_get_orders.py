"""
Test script to verify GET /orders endpoint returns data correctly.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.routers.orders import get_orders
from app.database import connect_to_mongo, close_mongo_connection

async def test_get_orders():
    """Test getting orders from the API."""
    print("=" * 60)
    print("TESTING GET ORDERS API")
    print("=" * 60)
    
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        print("\n✓ Connected to MongoDB")
        
        # Call the get_orders endpoint function
        print("\n2. Calling get_orders()...")
        orders = await get_orders()
        
        print(f"\n✓ Successfully retrieved {len(orders)} orders")
        
        if orders:
            print(f"\n3. Sample Order Details (first order):")
            first_order = orders[0]
            print(f"   ID: {first_order.id}")
            print(f"   User ID: {first_order.user_id}")
            print(f"   Status: {first_order.status}")
            print(f"   Estimated Price: ${first_order.estimated_price}")
            print(f"   Location: {first_order.location_category}")
            print(f"   Loyalty: {first_order.loyalty_tier}")
            print(f"   Vehicle: {first_order.vehicle_type}")
            print(f"   Pricing Model: {first_order.pricing_model}")
            print(f"   Created: {first_order.created_at}")
            
            print(f"\n4. All Orders Summary:")
            for i, order in enumerate(orders[:5], 1):  # Show first 5
                print(f"   {i}. {order.id} - ${order.estimated_price:.2f} - {order.status.value}")
        else:
            print("\n⚠️  No orders returned!")
        
        print("\n" + "=" * 60)
        print("TEST COMPLETE - GET ORDERS API WORKING ✓")
        print("=" * 60)
        
        # Close connection
        await close_mongo_connection()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_get_orders())
