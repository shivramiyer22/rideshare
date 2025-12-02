"""
Redis client connection and session management.
"""
import redis.asyncio as redis
from typing import Optional
from urllib.parse import urlparse
from app.config import settings

# Global Redis client
redis_client: Optional[redis.Redis] = None


async def connect_to_redis():
    """Create Redis connection. Gracefully handles connection failures."""
    global redis_client
    try:
        # Use redis_url from config (handles Docker override to localhost)
        redis_url = settings.redis_url
        
        # Parse URL to extract connection details
        parsed = urlparse(redis_url)
        host = parsed.hostname or settings.REDIS_HOST
        port = parsed.port or settings.REDIS_PORT
        db = int(parsed.path.lstrip('/')) if parsed.path else settings.REDIS_DB
        
        # Ensure localhost (NO Docker requirement)
        if host != "localhost" and host != "127.0.0.1":
            print(f"Warning: Redis host is {host}, overriding to localhost (NO Docker requirement)")
            host = "localhost"
        
        redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            socket_connect_timeout=2,  # 2 second timeout
            socket_timeout=2
        )
        
        # Test connection
        await redis_client.ping()
        print(f"✓ Connected to Redis: {host}:{port} (db={db})")
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
        print("⚠️  Continuing without Redis - priority queue features will be unavailable")
        print("⚠️  To enable Redis: Install and start Redis server (e.g., 'brew install redis && brew services start redis')")
        redis_client = None  # Set to None instead of raising


async def close_redis_connection():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        print("Disconnected from Redis")


def get_redis():
    """Get Redis client instance."""
    return redis_client

