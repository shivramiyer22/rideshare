"""
Defines routes and endpoints related to users.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
async def get_users():
    """Get all users."""
    return {"users": []}


@router.get("/{user_id}")
async def get_user(user_id: int):
    """Get a specific user by ID."""
    return {"user_id": user_id}



