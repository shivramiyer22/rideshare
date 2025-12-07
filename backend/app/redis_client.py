"""
Redis client connection and session management.
"""
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    print("⚠️  Redis package not installed. Install with: pip install redis")
    
from typing import Optional
from urllib.parse import urlparse
from app.config import settings

# Global Redis client
redis_client: Optional[any] = None


async def connect_to_redis():
    """Create Redis connection. Gracefully handles connection failures."""
    global redis_client
    
    # Check if redis package is available
    if not REDIS_AVAILABLE or redis is None:
        print("⚠️  Redis package not installed - skipping Redis connection")
        print("⚠️  To enable Redis: pip install redis && brew services start redis")
        redis_client = None
        return
    
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
        
        # Try to auto-start Redis if not running
        import subprocess
        try:
            # Check if Redis is running
            result = subprocess.run(
                ["redis-cli", "ping"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode != 0:
                print("⚠️  Redis not running, attempting to start...")
                # Try to start Redis (macOS with Homebrew)
                subprocess.run(
                    ["brew", "services", "start", "redis"],
                    capture_output=True,
                    timeout=5
                )
                # Wait a moment for Redis to start
                import asyncio
                await asyncio.sleep(2)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass  # Redis might not be installed or different setup
        
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

