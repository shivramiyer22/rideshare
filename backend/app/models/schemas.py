"""
Consolidated Pydantic schemas for the application.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Order Schemas
class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class OrderCreate(BaseModel):
    """Schema for creating an order."""
    user_id: str
    pickup_location: Dict[str, Any]
    dropoff_location: Dict[str, Any]
    pricing_tier: str = "STANDARD"
    priority: str = "P2"


class OrderResponse(BaseModel):
    """Schema for order response."""
    id: str
    user_id: str
    pickup_location: Dict[str, Any]
    dropoff_location: Dict[str, Any]
    status: OrderStatus
    pricing_tier: str
    priority: str
    price: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User Schemas (consolidated from schemas/user.py)
class UserBase(BaseModel):
    """Base schema for user."""
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True



