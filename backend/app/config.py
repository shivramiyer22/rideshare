"""
Configuration settings for the application.
NO Docker configuration - using native services.
Reads from root .env file.
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


# Get the root directory (2 levels up from backend/app/)
ROOT_DIR = Path(__file__).parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB Configuration - from root .env
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "rideshare")
    
    # Also support MONGODB_URL for compatibility
    MONGODB_URL: Optional[str] = os.getenv("MONGODB_URL")
    MONGODB_DB_NAME: Optional[str] = os.getenv("MONGODB_DB_NAME")
    
    # Redis Configuration - handle Docker references
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # ChromaDB Configuration
    CHROMADB_PATH: str = os.getenv("CHROMADB_PATH", "./chroma_db")
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # LangChain Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    LANGSMITH_API_KEY: Optional[str] = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    LANGSMITH_PROJECT: Optional[str] = os.getenv("LANGSMITH_PROJECT")
    
    class Config:
        env_file = str(ENV_FILE) if ENV_FILE.exists() else None
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env that aren't defined in Settings
    
    @property
    def mongodb_url(self) -> str:
        """Get MongoDB URL, preferring MONGO_URI from root .env."""
        if self.MONGO_URI:
            return self.MONGO_URI
        elif self.MONGODB_URL:
            return self.MONGODB_URL
        else:
            return "mongodb://localhost:27017"
    
    @property
    def mongodb_db_name(self) -> str:
        """Get MongoDB database name, preferring MONGO_DB_NAME from root .env."""
        if self.MONGO_DB_NAME:
            return self.MONGO_DB_NAME
        elif self.MONGODB_DB_NAME:
            return self.MONGODB_DB_NAME
        else:
            return "rideshare"
    
    @property
    def redis_url(self) -> str:
        """Get Redis URL, overriding Docker service names to localhost."""
        if self.REDIS_URL:
            # Check if it contains Docker service name and override
            if "redis://redis:" in self.REDIS_URL or "redis://redis/" in self.REDIS_URL:
                # Override Docker service name to localhost (NO Docker requirement)
                return f"redis://localhost:{self.REDIS_PORT}/{self.REDIS_DB}"
            return self.REDIS_URL
        else:
            # Build from host/port/db
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()

