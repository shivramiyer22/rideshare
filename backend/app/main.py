"""
Initializes the FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import connect_to_mongo, close_mongo_connection
from app.redis_client import connect_to_redis, close_redis_connection
from app.routers import orders, upload, ml, analytics, chatbot, users, pipeline
from app.background_tasks import start_background_tasks, stop_background_tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    await connect_to_mongo()
    await connect_to_redis()
    start_background_tasks()  # Start analytics pre-computation scheduler
    yield
    # Shutdown
    stop_background_tasks()  # Stop background scheduler
    await close_mongo_connection()
    await close_redis_connection()


app = FastAPI(
    title="Rideshare API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS (Cross-Origin Resource Sharing)
# This allows the frontend (localhost:3000) to make requests to the backend (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js frontend
        "http://127.0.0.1:3000",  # Alternative localhost format
    ],
    allow_credentials=True,  # Allow cookies and authentication headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers (needed for file uploads with FormData)
    expose_headers=["*"],  # Expose all headers in response
)

# Include routers
app.include_router(orders.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")
app.include_router(ml.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(chatbot.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(pipeline.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to Rideshare API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

