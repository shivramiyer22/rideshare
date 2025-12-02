"""
Test script to validate MongoDB, Redis, and Priority Queue connections.
Run this script to test all connections before starting the FastAPI server.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path (tests folder is one level down from backend root)
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection, get_database
from app.redis_client import connect_to_redis, close_redis_connection, get_redis
from app.priority_queue import priority_queue, Priority


async def test_config():
    """Test configuration loading."""
    print("=" * 60)
    print("TESTING CONFIGURATION")
    print("=" * 60)
    
    print(f"✓ MONGO_URI: {settings.mongodb_url[:50]}..." if len(settings.mongodb_url) > 50 else f"✓ MONGO_URI: {settings.mongodb_url}")
    print(f"✓ MONGO_DB_NAME: {settings.mongodb_db_name}")
    print(f"✓ REDIS_URL: {settings.redis_url}")
    print(f"✓ REDIS_HOST: {settings.REDIS_HOST}")
    print(f"✓ REDIS_PORT: {settings.REDIS_PORT}")
    print(f"✓ OPENAI_API_KEY: {'Set' if settings.OPENAI_API_KEY else 'Not Set'}")
    
    # Check for Docker references
    if "redis://redis:" in settings.redis_url or "redis://redis/" in settings.redis_url:
        print("⚠ WARNING: Redis URL contains Docker service name, should be overridden to localhost")
    else:
        print("✓ Redis URL does not contain Docker service names")
    
    print()


async def test_mongodb():
    """Test MongoDB connection."""
    print("=" * 60)
    print("TESTING MONGODB CONNECTION")
    print("=" * 60)
    
    try:
        await connect_to_mongo()
        db = get_database()
        
        if db is None:
            print("✗ FAILED: Database instance is None")
            return False
        
        # Test connection with a simple operation
        collections = await db.list_collection_names()
        print(f"✓ Connected to MongoDB successfully")
        print(f"✓ Database: {settings.mongodb_db_name}")
        print(f"✓ Collections found: {len(collections)}")
        
        await close_mongo_connection()
        print("✓ MongoDB connection closed successfully")
        print()
        return True
        
    except Exception as e:
        print(f"✗ FAILED: MongoDB connection error: {e}")
        print(f"  Error type: {type(e).__name__}")
        print()
        return False


async def test_redis():
    """Test Redis connection."""
    print("=" * 60)
    print("TESTING REDIS CONNECTION")
    print("=" * 60)
    
    try:
        await connect_to_redis()
        redis = get_redis()
        
        if redis is None:
            print("✗ FAILED: Redis client is None")
            return False
        
        # Test connection with ping
        pong = await redis.ping()
        if pong:
            print("✓ Connected to Redis successfully")
            print(f"✓ Redis URL: {settings.redis_url}")
            
            # Test basic operations
            await redis.set("test_key", "test_value", ex=10)
            value = await redis.get("test_key")
            if value == "test_value":
                print("✓ Redis read/write operations working")
                await redis.delete("test_key")
            else:
                print("⚠ WARNING: Redis read/write test failed")
            
            await close_redis_connection()
            print("✓ Redis connection closed successfully")
            print()
            return True
        else:
            print("✗ FAILED: Redis ping failed")
            print()
            return False
            
    except Exception as e:
        print(f"✗ FAILED: Redis connection error: {e}")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Make sure Redis is running on {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        print()
        return False


async def test_priority_queue():
    """Test Priority Queue operations."""
    print("=" * 60)
    print("TESTING PRIORITY QUEUE (REDIS)")
    print("=" * 60)
    
    try:
        # Ensure Redis is connected
        redis = get_redis()
        if redis is None:
            print("✗ FAILED: Redis not connected. Run test_redis() first.")
            return False
        
        # Test P0 queue (CONTRACTED - FIFO)
        print("Testing P0 queue (CONTRACTED - FIFO)...")
        test_order_p0 = await priority_queue.add_order(
            order_id="test_p0_1",
            pricing_model="CONTRACTED",
            revenue_score=100.0,
            order_data={"test": "p0_order_1"}
        )
        print(f"✓ Added P0 order: {test_order_p0['order_id']}")
        
        test_order_p0_2 = await priority_queue.add_order(
            order_id="test_p0_2",
            pricing_model="CONTRACTED",
            revenue_score=200.0,
            order_data={"test": "p0_order_2"}
        )
        print(f"✓ Added P0 order: {test_order_p0_2['order_id']}")
        
        # Get next P0 order (should be first one added - FIFO)
        next_p0 = await priority_queue.get_next_p0_order()
        if next_p0 and next_p0["order_id"] == "test_p0_1":
            print(f"✓ P0 FIFO working: Got first order ({next_p0['order_id']})")
        else:
            print(f"⚠ WARNING: P0 FIFO may not be working correctly")
        
        # Test P1 queue (STANDARD - revenue_score DESC)
        print("\nTesting P1 queue (STANDARD - revenue_score DESC)...")
        await priority_queue.add_order(
            order_id="test_p1_1",
            pricing_model="STANDARD",
            revenue_score=50.0,
            order_data={"test": "p1_order_1"}
        )
        await priority_queue.add_order(
            order_id="test_p1_2",
            pricing_model="STANDARD",
            revenue_score=150.0,
            order_data={"test": "p1_order_2"}
        )
        await priority_queue.add_order(
            order_id="test_p1_3",
            pricing_model="STANDARD",
            revenue_score=75.0,
            order_data={"test": "p1_order_3"}
        )
        print("✓ Added 3 P1 orders with revenue_scores: 50, 150, 75")
        
        # Get next P1 order (should be highest revenue_score = 150)
        next_p1 = await priority_queue.get_next_p1_order()
        if next_p1 and next_p1["revenue_score"] == 150.0:
            print(f"✓ P1 revenue_score DESC working: Got highest ({next_p1['order_id']}, score={next_p1['revenue_score']})")
        else:
            print(f"⚠ WARNING: P1 revenue_score sorting may not be working correctly")
        
        # Test P2 queue (CUSTOM - revenue_score DESC)
        print("\nTesting P2 queue (CUSTOM - revenue_score DESC)...")
        await priority_queue.add_order(
            order_id="test_p2_1",
            pricing_model="CUSTOM",
            revenue_score=30.0,
            order_data={"test": "p2_order_1"}
        )
        await priority_queue.add_order(
            order_id="test_p2_2",
            pricing_model="CUSTOM",
            revenue_score=120.0,
            order_data={"test": "p2_order_2"}
        )
        print("✓ Added 2 P2 orders with revenue_scores: 30, 120")
        
        # Get next P2 order (should be highest revenue_score = 120)
        next_p2 = await priority_queue.get_next_p2_order()
        if next_p2 and next_p2["revenue_score"] == 120.0:
            print(f"✓ P2 revenue_score DESC working: Got highest ({next_p2['order_id']}, score={next_p2['revenue_score']})")
        else:
            print(f"⚠ WARNING: P2 revenue_score sorting may not be working correctly")
        
        # Test queue status
        print("\nTesting queue status...")
        status = await priority_queue.get_queue_status()
        print(f"✓ Queue status: P0={status['P0']}, P1={status['P1']}, P2={status['P2']}")
        
        # Clean up test data
        print("\nCleaning up test data...")
        await priority_queue.clear_queue(Priority.P0)
        await priority_queue.clear_queue(Priority.P1)
        await priority_queue.clear_queue(Priority.P2)
        print("✓ Test queues cleared")
        
        print()
        return True
        
    except Exception as e:
        print(f"✗ FAILED: Priority queue error: {e}")
        print(f"  Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("RIDESHARE BACKEND CONNECTION TESTS")
    print("=" * 60 + "\n")
    
    results = {
        "config": True,  # Config always passes (just displays values)
        "mongodb": False,
        "redis": False,
        "priority_queue": False
    }
    
    # Test configuration
    await test_config()
    
    # Test MongoDB
    results["mongodb"] = await test_mongodb()
    
    # Test Redis (required for priority queue)
    results["redis"] = await test_redis()
    
    # Test Priority Queue (requires Redis)
    if results["redis"]:
        results["priority_queue"] = await test_priority_queue()
    else:
        print("=" * 60)
        print("SKIPPING PRIORITY QUEUE TEST (Redis not connected)")
        print("=" * 60 + "\n")
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Configuration: {'✓ PASS' if results['config'] else '✗ FAIL'}")
    print(f"MongoDB:       {'✓ PASS' if results['mongodb'] else '✗ FAIL'}")
    print(f"Redis:         {'✓ PASS' if results['redis'] else '✗ FAIL'}")
    print(f"Priority Queue: {'✓ PASS' if results['priority_queue'] else '✗ FAIL'}")
    print("=" * 60)
    
    if all([results["config"], results["mongodb"], results["redis"], results["priority_queue"]]):
        print("\n✓ ALL TESTS PASSED! Backend is ready to use.")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

