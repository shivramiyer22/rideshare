"""
Defines routes and endpoints related to items.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/")
async def get_items():
    """Get all items."""
    return {"items": []}


@router.get("/{item_id}")
async def get_item(item_id: int):
    """Get a specific item by ID."""
    return {"item_id": item_id}



