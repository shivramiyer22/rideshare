"""
Defines schemas for items.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ItemBase(BaseModel):
    """Base schema for item."""
    name: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    """Schema for creating an item."""
    pass


class ItemUpdate(BaseModel):
    """Schema for updating an item."""
    name: Optional[str] = None
    description: Optional[str] = None


class Item(ItemBase):
    """Schema for item response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True



