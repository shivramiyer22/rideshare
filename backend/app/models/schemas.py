"""
Consolidated Pydantic schemas for the application.
"""
from pydantic import BaseModel, EmailStr, Field
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


# ============================================================================
# ORDER ESTIMATION SCHEMAS (for POST /orders/estimate endpoint)
# ============================================================================

class OrderEstimateRequest(BaseModel):
    """Request schema for order price estimation."""
    # Required segment dimensions (from frontend form)
    location_category: str = Field(..., description="Urban, Suburban, or Rural")
    loyalty_tier: str = Field(..., description="Gold, Silver, or Regular")
    vehicle_type: str = Field(..., description="Premium or Economy")
    pricing_model: str = Field(default="STANDARD", description="CONTRACTED, STANDARD, or CUSTOM")
    
    # Optional trip details (if known from route calculation)
    distance: Optional[float] = Field(default=None, description="Trip distance in miles")
    duration: Optional[float] = Field(default=None, description="Trip duration in minutes")
    pickup_location: Optional[Dict[str, Any]] = Field(default=None, description="Pickup location details")
    dropoff_location: Optional[Dict[str, Any]] = Field(default=None, description="Dropoff location details")


class SegmentData(BaseModel):
    """Segment identification data."""
    location_category: str
    loyalty_tier: str
    vehicle_type: str
    pricing_model: str


class HistoricalBaseline(BaseModel):
    """Historical baseline metrics from past rides."""
    avg_price: float = Field(..., description="Average price from historical rides")
    avg_distance: float = Field(..., description="Average distance in miles")
    avg_duration: float = Field(..., description="Average duration in minutes")
    sample_size: int = Field(..., description="Number of historical rides in segment")
    data_source: str = Field(default="historical_rides", description="Data source identifier")


class ForecastPrediction(BaseModel):
    """Forecast prediction data for segment."""
    predicted_price_30d: float = Field(..., description="Predicted average price for next 30 days")
    predicted_demand_30d: float = Field(..., description="Predicted ride count for next 30 days")
    forecast_confidence: Optional[float] = Field(default=None, description="Confidence score 0-1")


class PriceBreakdown(BaseModel):
    """Detailed price breakdown from PricingEngine."""
    base_fare: Optional[float] = Field(default=None, description="Base fare component")
    distance_cost: Optional[float] = Field(default=None, description="Distance-based cost")
    time_cost: Optional[float] = Field(default=None, description="Time-based cost")
    surge_multiplier: Optional[float] = Field(default=None, description="Surge/demand multiplier")
    loyalty_discount: Optional[float] = Field(default=None, description="Loyalty discount applied")
    final_price: float = Field(..., description="Final calculated price")


class OrderEstimateResponse(BaseModel):
    """Response schema for order price estimation."""
    segment: SegmentData
    historical_baseline: HistoricalBaseline
    forecast_prediction: ForecastPrediction
    estimated_price: float = Field(..., description="Recommended price estimate")
    price_breakdown: Optional[PriceBreakdown] = Field(default=None, description="Detailed breakdown if trip details provided")
    explanation: str = Field(..., description="Natural language explanation of estimate")
    assumptions: List[str] = Field(..., description="List of assumptions made in calculation")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of estimation")


# ============================================================================
# ORDER CREATION SCHEMAS (enhanced for POST /orders endpoint)
# ============================================================================

class OrderCreate(BaseModel):
    """Enhanced schema for creating an order."""
    user_id: str
    pickup_location: Dict[str, Any]
    dropoff_location: Dict[str, Any]
    
    # Required segment dimensions (from frontend form)
    location_category: str = Field(..., description="Urban, Suburban, or Rural")
    loyalty_tier: str = Field(..., description="Gold, Silver, or Regular")
    vehicle_type: str = Field(..., description="Premium or Economy")
    pricing_model: str = Field(default="STANDARD", description="CONTRACTED, STANDARD, or CUSTOM")
    
    # Optional trip details
    distance: Optional[float] = Field(default=None, description="Trip distance in miles")
    duration: Optional[float] = Field(default=None, description="Trip duration in minutes")
    
    # Legacy field for backward compatibility
    pricing_tier: str = Field(default="STANDARD", description="Deprecated: use pricing_model instead")
    priority: str = Field(default="P2", description="Priority queue: P0, P1, or P2")


class OrderResponse(BaseModel):
    """Enhanced schema for order response."""
    id: str
    user_id: str
    pickup_location: Dict[str, Any]
    dropoff_location: Dict[str, Any]
    status: OrderStatus
    
    # Segment dimensions
    location_category: str
    loyalty_tier: str
    vehicle_type: str
    pricing_model: str
    
    # Computed pricing fields
    segment_avg_price: Optional[float] = Field(default=None, description="Average price for this segment")
    segment_avg_distance: Optional[float] = Field(default=None, description="Average distance for this segment")
    estimated_price: float = Field(..., description="Estimated price for this order")
    price_breakdown: Optional[Dict[str, Any]] = Field(default=None, description="Detailed price breakdown")
    pricing_explanation: Optional[str] = Field(default=None, description="Explanation of pricing calculation")
    
    # Legacy fields for backward compatibility
    pricing_tier: str
    priority: str
    price: Optional[float] = Field(default=None, description="Final price (same as estimated_price)")
    
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



