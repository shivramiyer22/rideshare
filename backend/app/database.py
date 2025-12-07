"""
MongoDB database connection and session management.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from app.config import settings

# Global database client
client: Optional[AsyncIOMotorClient] = None
database = None


async def connect_to_mongo():
    """
    Create database connection with graceful degradation.
    Application will start even if MongoDB is unavailable.
    """
    global client, database
    try:
        # Use MONGO_URI from root .env (via config)
        mongo_url = settings.mongodb_url
        db_name = settings.mongodb_db_name
        
        client = AsyncIOMotorClient(
            mongo_url,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        database = client[db_name]
        
        # Test connection (non-blocking with short timeout)
        await client.admin.command('ping')
        print(f"✅ Connected to MongoDB: {db_name} at {mongo_url.split('@')[-1] if '@' in mongo_url else mongo_url}")
    except Exception as e:
        print(f"⚠️  MongoDB connection failed: {e}")
        print(f"⚠️  Application will continue without MongoDB (some features may be limited)")
        # Don't raise - allow app to start without MongoDB
        client = None
        database = None


async def close_mongo_connection():
    """Close database connection."""
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")


def get_database():
    """Get database instance."""
    return database

