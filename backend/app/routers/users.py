"""
Defines routes and endpoints related to users.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, EmailStr
from app.database import get_database
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    """Schema for creating a user."""
    email: str
    username: str
    full_name: Optional[str] = None
    loyalty_tier: str = "Regular"  # Gold, Silver, Regular


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    loyalty_tier: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    loyalty_tier: str = "Regular"
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


@router.get("/", response_model=List[UserResponse])
async def get_users(
    limit: int = Query(100, description="Maximum number of users to return"),
    loyalty_tier: Optional[str] = Query(None, description="Filter by loyalty tier (Gold/Silver/Regular)")
):
    """Get all users from MongoDB."""
    try:
        database = get_database()
        if database is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        collection = database["users"]
        
        # Build query
        query = {}
        if loyalty_tier:
            query["loyalty_tier"] = loyalty_tier
        
        cursor = collection.find(query).sort("created_at", -1).limit(limit)
        users = await cursor.to_list(length=limit)
        
        result = []
        for user in users:
            result.append(UserResponse(
                id=user.get("id", str(user.get("_id", ""))),
                email=user.get("email", ""),
                username=user.get("username", ""),
                full_name=user.get("full_name"),
                loyalty_tier=user.get("loyalty_tier", "Regular"),
                is_active=user.get("is_active", True),
                created_at=user.get("created_at", datetime.utcnow()),
                updated_at=user.get("updated_at", datetime.utcnow())
            ))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get a specific user by ID."""
    try:
        database = get_database()
        if database is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        collection = database["users"]
        user = await collection.find_one({"id": user_id})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(
            id=user.get("id", str(user.get("_id", ""))),
            email=user.get("email", ""),
            username=user.get("username", ""),
            full_name=user.get("full_name"),
            loyalty_tier=user.get("loyalty_tier", "Regular"),
            is_active=user.get("is_active", True),
            created_at=user.get("created_at", datetime.utcnow()),
            updated_at=user.get("updated_at", datetime.utcnow())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate):
    """Create a new user."""
    try:
        database = get_database()
        if database is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        collection = database["users"]
        
        # Check if email already exists
        existing = await collection.find_one({"email": user.email})
        if existing:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Check if username already exists
        existing = await collection.find_one({"username": user.username})
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        
        # Generate unique ID
        user_id = f"USR-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.utcnow()
        
        # Create user document
        user_doc = {
            "id": user_id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "loyalty_tier": user.loyalty_tier,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        
        await collection.insert_one(user_doc)
        logger.info(f"Created user {user_id}: {user.username}")
        
        return UserResponse(
            id=user_id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            loyalty_tier=user.loyalty_tier,
            is_active=True,
            created_at=now,
            updated_at=now
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserUpdate):
    """Update an existing user."""
    try:
        database = get_database()
        if database is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        collection = database["users"]
        
        # Check if user exists
        existing = await collection.find_one({"id": user_id})
        if not existing:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build update document
        update_data = {"updated_at": datetime.utcnow()}
        if user_update.email is not None:
            update_data["email"] = user_update.email
        if user_update.username is not None:
            update_data["username"] = user_update.username
        if user_update.full_name is not None:
            update_data["full_name"] = user_update.full_name
        if user_update.loyalty_tier is not None:
            update_data["loyalty_tier"] = user_update.loyalty_tier
        
        await collection.update_one({"id": user_id}, {"$set": update_data})
        
        # Fetch updated user
        updated = await collection.find_one({"id": user_id})
        
        return UserResponse(
            id=updated.get("id", str(updated.get("_id", ""))),
            email=updated.get("email", ""),
            username=updated.get("username", ""),
            full_name=updated.get("full_name"),
            loyalty_tier=updated.get("loyalty_tier", "Regular"),
            is_active=updated.get("is_active", True),
            created_at=updated.get("created_at", datetime.utcnow()),
            updated_at=updated.get("updated_at", datetime.utcnow())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")


@router.delete("/{user_id}")
async def delete_user(user_id: str):
    """Delete a user (soft delete - sets is_active to False)."""
    try:
        database = get_database()
        if database is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        collection = database["users"]
        
        # Check if user exists
        existing = await collection.find_one({"id": user_id})
        if not existing:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Soft delete - set is_active to False
        await collection.update_one(
            {"id": user_id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        
        logger.info(f"Deleted user {user_id}")
        
        return {"message": f"User {user_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")



