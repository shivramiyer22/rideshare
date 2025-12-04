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
    segment_avg_fcs_unit_price: float = Field(..., description="Average unit price per minute")
    segment_avg_fcs_ride_duration: float = Field(..., description="Average ride duration in minutes")
    segment_avg_riders_per_order: float = Field(..., description="Average riders per order")
    segment_avg_drivers_per_order: float = Field(..., description="Average drivers available per order")
    segment_demand_profile: str = Field(..., description="HIGH, MEDIUM, or LOW based on driver/rider ratio")
    sample_size: int = Field(..., description="Number of historical rides in segment")
    data_source: str = Field(default="historical_rides", description="Data source identifier")


class ForecastPrediction(BaseModel):
    """Forecast prediction data for segment."""
    predicted_unit_price_30d: float = Field(..., description="Predicted average unit price (per minute) for next 30 days")
    predicted_ride_duration_30d: float = Field(..., description="Predicted average ride duration in minutes for next 30 days")
    predicted_demand_30d: float = Field(..., description="Predicted ride count for next 30 days")
    predicted_riders_30d: float = Field(..., description="Predicted average riders per order for next 30 days")
    predicted_drivers_30d: float = Field(..., description="Predicted average drivers per order for next 30 days")
    segment_demand_profile: str = Field(..., description="HIGH, MEDIUM, or LOW based on forecasted driver/rider ratio")
    forecast_confidence: Optional[float] = Field(default=None, description="Confidence score 0-1")


class PriceBreakdown(BaseModel):
    """Detailed price breakdown from PricingEngine."""
    base_unit_price_per_minute: Optional[float] = Field(default=None, description="Base unit price per minute")
    ride_duration_minutes: Optional[float] = Field(default=None, description="Ride duration in minutes")
    surge_multiplier: Optional[float] = Field(default=None, description="Surge/demand multiplier")
    loyalty_discount: Optional[float] = Field(default=None, description="Loyalty discount applied")
    final_price: float = Field(..., description="Final calculated price (unit_price × duration × multiplier)")


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
    distance: Optional[float] = Field(default=None, description="Trip distance in miles (deprecated, for backward compatibility)")
    duration: Optional[float] = Field(default=None, description="Trip duration in minutes")
    
    # Priority queue
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
    
    # Computed pricing fields (new duration-based model)
    segment_avg_fcs_unit_price: Optional[float] = Field(default=None, description="Average unit price per minute for this segment")
    segment_avg_fcs_ride_duration: Optional[float] = Field(default=None, description="Average ride duration in minutes for this segment")
    segment_avg_riders_per_order: Optional[float] = Field(default=None, description="Average riders per order for this segment")
    segment_avg_drivers_per_order: Optional[float] = Field(default=None, description="Average drivers per order for this segment")
    segment_demand_profile: Optional[str] = Field(default=None, description="HIGH, MEDIUM, or LOW based on driver/rider ratio")
    estimated_price: float = Field(..., description="Estimated price for this order (unit_price × duration)")
    price_breakdown: Optional[Dict[str, Any]] = Field(default=None, description="Detailed price breakdown")
    pricing_explanation: Optional[str] = Field(default=None, description="Explanation of pricing calculation")
    
    # Priority queue
    priority: str
    
    # Timestamps
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


# Segment Dynamic Pricing Report Schemas
class SegmentIdentifier(BaseModel):
    """Identifies a unique segment by its 5 dimensions."""
    location_category: str = Field(..., description="Urban, Suburban, or Rural")
    loyalty_tier: str = Field(..., description="Gold, Silver, or Regular")
    vehicle_type: str = Field(..., description="Economy, Premium, etc.")
    demand_profile: str = Field(..., description="HIGH, MEDIUM, or LOW")
    pricing_model: str = Field(default="STANDARD", description="STANDARD, SUBSCRIPTION, etc.")


class SegmentScenario(BaseModel):
    """Metrics for a specific pricing scenario (Continue Current or Recommendation)."""
    rides_30d: float = Field(..., description="Forecasted rides over 30 days")
    unit_price_per_minute: float = Field(..., description="Average unit price per minute")
    ride_duration_minutes: float = Field(..., description="Average ride duration in minutes")
    revenue_30d: float = Field(..., description="Total revenue over 30 days (rides × duration × unit_price)")
    segment_demand_profile: str = Field(..., description="HIGH, MEDIUM, or LOW based on driver/rider ratio")
    explanation: str = Field(..., description="Short explanation of how metrics were calculated")


class SegmentDynamicPricingRow(BaseModel):
    """Complete row for one segment containing all scenarios."""
    segment: SegmentIdentifier
    hwco_continue_current: SegmentScenario
    lyft_continue_current: SegmentScenario
    recommendation_1: SegmentScenario
    recommendation_2: SegmentScenario
    recommendation_3: SegmentScenario


class ReportMetadata(BaseModel):
    """Metadata for segment dynamic pricing report."""
    report_type: str = Field(default="segment_dynamic_pricing_analysis")
    generated_at: str = Field(..., description="ISO timestamp of report generation")
    pipeline_result_id: str = Field(..., description="MongoDB ID of pipeline result used")
    pipeline_timestamp: str = Field(..., description="Timestamp of pipeline execution")
    total_segments: int = Field(..., description="Total number of segments (should be 162)")
    dimensions: List[str] = Field(
        default=["location_category", "loyalty_tier", "vehicle_type", "demand_profile", "pricing_model"],
        description="List of segment dimensions"
    )


class SegmentDynamicPricingReport(BaseModel):
    """Complete segment dynamic pricing report response (JSON format)."""
    metadata: ReportMetadata
    segments: List[SegmentDynamicPricingRow]


class SegmentDynamicPricingReportRequest(BaseModel):
    """Request parameters for segment dynamic pricing report."""
    pipeline_result_id: Optional[str] = Field(
        default=None,
        description="Specific pipeline result ID (optional, uses latest if not provided)"
    )
    format: str = Field(
        default="json",
        description="Output format: 'json' or 'csv'"
    )


# Legacy export for backward compatibility
__all__ = [
    "OrderEstimateRequest",
    "SegmentData",
    "HistoricalBaseline",
    "ForecastPrediction",
    "PriceBreakdown",
    "OrderEstimateResponse",
    "OrderCreate",
    "OrderResponse",
    "UserBase",
    "UserCreate",
    "UserResponse",
    "SegmentIdentifier",
    "SegmentScenario",
    "SegmentDynamicPricingRow",
    "ReportMetadata",
    "SegmentDynamicPricingReport",
    "SegmentDynamicPricingReportRequest"
]



