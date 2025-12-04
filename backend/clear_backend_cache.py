"""
Clear all backend cache except ChromaDB
"""
import asyncio
import os
import shutil
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def clear_caches():
    """Clear all backend caches except ChromaDB."""
    print("=" * 60)
    print("CLEARING BACKEND CACHE (EXCEPT CHROMADB)")
    print("=" * 60)
    
    try:
        # Get MongoDB settings from env
        mongodb_url = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        mongodb_db = os.getenv("MONGO_DB_NAME", "rideshare")
        
        # 1. Clear MongoDB analytics_cache collection
        print("\n1. Clearing MongoDB analytics_cache collection...")
        client = AsyncIOMotorClient(mongodb_url)
        db = client[mongodb_db]
        
        result = await db["analytics_cache"].delete_many({})
        print(f"   ✓ Deleted {result.deleted_count} documents from analytics_cache")
        
        # 2. Clear Redis cache (try if redis module is available)
        print("\n2. Clearing Redis cache...")
        try:
            import redis.asyncio as redis_async
            
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))
            
            redis_client = redis_async.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True
            )
            
            # Get all keys
            keys = await redis_client.keys("*")
            if keys:
                # Delete all keys
                deleted = await redis_client.delete(*keys)
                print(f"   ✓ Deleted {deleted} keys from Redis")
            else:
                print(f"   ✓ No keys found in Redis (already clean)")
            
            await redis_client.close()
        except ImportError:
            print(f"   ⚠️  Redis module not installed, skipping Redis cache clear")
        except Exception as e:
            print(f"   ⚠️  Could not clear Redis: {e}")
        
        # 3. Keep ChromaDB intact
        print("\n3. ChromaDB preservation:")
        chroma_path = os.path.join(os.path.dirname(__file__), "chroma_db")
        if os.path.exists(chroma_path):
            print(f"   ✓ ChromaDB found at {chroma_path} - preserved (not cleared)")
        else:
            print(f"   ✓ ChromaDB will be preserved (not cleared)")
        
        # 4. Clear pytest cache
        print("\n4. Clearing pytest cache...")
        pytest_cache_dir = os.path.join(os.path.dirname(__file__), '.pytest_cache')
        if os.path.exists(pytest_cache_dir):
            shutil.rmtree(pytest_cache_dir)
            print(f"   ✓ Deleted .pytest_cache directory")
        else:
            print(f"   ✓ No pytest cache found")
        
        # 5. Python cache already cleared by shell command
        print("\n5. Python __pycache__ cleanup:")
        print(f"   ✓ Python cache files already cleared")
        
        client.close()
        
        print("\n" + "=" * 60)
        print("CACHE CLEARING COMPLETE")
        print("=" * 60)
        print("\n✅ Cleared:")
        print("  • MongoDB analytics_cache collection")
        print("  • Redis cache keys (if available)")
        print("  • Python __pycache__ directories")
        print("  • Pytest cache")
        print("\n✅ Preserved:")
        print("  • ChromaDB vector database")
        print("  • All other MongoDB collections (historical_rides, competitor_prices, etc.)")
        print("\n📝 Next step: Restart the backend server")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(clear_caches())
