"""
Forecasting Helper Functions - Modular and Extensible Design

This module provides modular forecasting functions that can be easily extended
to use Prophet ML in the future. Currently uses simple methods, but designed
to support method='prophet' with minimal changes.

Functions:
- forecast_demand_for_segment: Demand forecasting (simple or future Prophet ML)
- forecast_price_for_segment: Price forecasting (PricingEngine or future Prophet ML)
- calculate_revenue_forecast: Revenue calculation (works with any method)
- prepare_historical_data_for_prophet: Data preparation for future Prophet ML
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)


def forecast_demand_for_segment(
    segment_dimensions: Dict[str, Any],
    historical_rides: List[Dict[str, Any]],
    periods: int = 30,
    method: str = 'simple'
) -> Dict[str, Any]:
    """
    Forecast demand (ride count) for a segment.
    
    Current implementation (method='simple'): Simple growth projection
    Future implementation (method='prophet'): Prophet ML forecasting
    
    Args:
        segment_dimensions: Segment dimensions dictionary
        historical_rides: Historical ride data for this segment
        periods: Forecast period in days (30, 60, or 90)
        method: 'simple' (current) or 'prophet' (future)
    
    Returns:
        Dictionary with:
            - predicted_rides_30d: float
            - predicted_rides_60d: float
            - predicted_rides_90d: float
            - confidence: str ('high', 'medium', 'low')
            - method: str (forecasting method used)
    """
    try:
        ride_count = len(historical_rides)
        
        if method == 'simple':
            # Current simple growth projection
            demand_profile = segment_dimensions.get("demand_profile", "MEDIUM")
            
            # Growth rate based on demand profile
            growth_rate = 0.015 if demand_profile == "HIGH" else 0.01 if demand_profile == "MEDIUM" else 0.005
            
            # Calculate forecasts for 30, 60, 90 days
            # Assuming ride_count is monthly, scale to daily then project
            daily_rides = ride_count / 30 if ride_count > 0 else 0  # Rough estimate
            
            predicted_30d = daily_rides * 30 * (1 + growth_rate * 1)
            predicted_60d = daily_rides * 60 * (1 + growth_rate * 2)
            predicted_90d = daily_rides * 90 * (1 + growth_rate * 3)
            
            # Confidence based on data quality
            confidence = "high" if ride_count >= 10 else "medium" if ride_count >= 3 else "low"
            
            return {
                "predicted_rides_30d": round(predicted_30d, 2),
                "predicted_rides_60d": round(predicted_60d, 2),
                "predicted_rides_90d": round(predicted_90d, 2),
                "confidence": confidence,
                "method": "simple"
            }
        
        elif method == 'prophet':
            # Future implementation: Prophet ML forecasting
            # This will be implemented when Prophet ML is added
            logger.warning("Prophet ML method not yet implemented, falling back to simple")
            return forecast_demand_for_segment(segment_dimensions, historical_rides, periods, method='simple')
        
        else:
            raise ValueError(f"Unknown forecasting method: {method}")
            
    except Exception as e:
        logger.error(f"Error forecasting demand for segment: {e}")
        # Return default values on error
        return {
            "predicted_rides_30d": 0.0,
            "predicted_rides_60d": 0.0,
            "predicted_rides_90d": 0.0,
            "confidence": "low",
            "method": method
        }


def forecast_price_for_segment(
    segment_dimensions: Dict[str, Any],
    historical_rides: List[Dict[str, Any]],
    periods: int = 30,
    method: str = 'pricing_engine',
    pricing_engine=None
) -> Dict[str, Any]:
    """
    Forecast price for a segment.
    
    Current implementation (method='pricing_engine'): Use PricingEngine to calculate current price
    Future implementation (method='prophet'): Prophet ML price trend forecasting
    
    Args:
        segment_dimensions: Segment dimensions dictionary
        historical_rides: Historical ride data for this segment
        periods: Forecast period in days (30, 60, or 90)
        method: 'pricing_engine' (current) or 'prophet' (future)
        pricing_engine: PricingEngine instance (required for 'pricing_engine' method)
    
    Returns:
        Dictionary with:
            - predicted_price_30d: float
            - predicted_price_60d: float
            - predicted_price_90d: float
            - confidence: str ('high', 'medium', 'low')
            - method: str (forecasting method used)
    """
    try:
        if method == 'pricing_engine':
            # Current implementation: Use PricingEngine to calculate price
            if pricing_engine is None:
                from app.pricing_engine import PricingEngine
                pricing_engine = PricingEngine()
            
            from app.agents.pricing_helpers import calculate_segment_price_with_engine
            
            # Calculate current price using PricingEngine
            price_result = calculate_segment_price_with_engine(
                segment_dimensions,
                historical_rides,
                pricing_engine
            )
            
            current_price = price_result.get("final_price", 0)
            
            # For now, assume price stays constant (future: use Prophet ML for trends)
            # In future Prophet ML implementation, this will forecast price trends
            predicted_30d = current_price
            predicted_60d = current_price
            predicted_90d = current_price
            
            # Confidence based on data quality
            ride_count = len(historical_rides)
            confidence = "high" if ride_count >= 10 else "medium" if ride_count >= 3 else "low"
            
            return {
                "predicted_price_30d": round(predicted_30d, 2),
                "predicted_price_60d": round(predicted_60d, 2),
                "predicted_price_90d": round(predicted_90d, 2),
                "confidence": confidence,
                "method": "pricing_engine",
                "current_price": round(current_price, 2)
            }
        
        elif method == 'prophet':
            # Future implementation: Prophet ML price forecasting
            # This will use PricingEngine-calculated historical prices as training data
            logger.warning("Prophet ML method not yet implemented, falling back to pricing_engine")
            return forecast_price_for_segment(segment_dimensions, historical_rides, periods, 'pricing_engine', pricing_engine)
        
        else:
            raise ValueError(f"Unknown price forecasting method: {method}")
            
    except Exception as e:
        logger.error(f"Error forecasting price for segment: {e}")
        # Fallback: use historical average
        prices = [r.get("Historical_Cost_of_Ride", 0) for r in historical_rides if r.get("Historical_Cost_of_Ride")]
        avg_price = sum(prices) / len(prices) if prices else 0
        
        return {
            "predicted_price_30d": round(avg_price, 2),
            "predicted_price_60d": round(avg_price, 2),
            "predicted_price_90d": round(avg_price, 2),
            "confidence": "low",
            "method": method
        }


def calculate_revenue_forecast(
    predicted_rides: Dict[str, float],
    predicted_price: Dict[str, float],
    periods: int = 30
) -> Dict[str, Any]:
    """
    Calculate revenue forecast from demand and price forecasts.
    
    This function works with any forecasting method (simple or Prophet ML).
    Simply multiplies predicted rides by predicted price.
    
    Args:
        predicted_rides: Dictionary with predicted_rides_30d, predicted_rides_60d, predicted_rides_90d
        predicted_price: Dictionary with predicted_price_30d, predicted_price_60d, predicted_price_90d
        periods: Forecast period (30, 60, or 90)
    
    Returns:
        Dictionary with:
            - predicted_revenue_30d: float
            - predicted_revenue_60d: float
            - predicted_revenue_90d: float
    """
    try:
        rides_30d = predicted_rides.get("predicted_rides_30d", 0)
        rides_60d = predicted_rides.get("predicted_rides_60d", 0)
        rides_90d = predicted_rides.get("predicted_rides_90d", 0)
        
        price_30d = predicted_price.get("predicted_price_30d", 0)
        price_60d = predicted_price.get("predicted_price_60d", 0)
        price_90d = predicted_price.get("predicted_price_90d", 0)
        
        revenue_30d = rides_30d * price_30d
        revenue_60d = rides_60d * price_60d
        revenue_90d = rides_90d * price_90d
        
        return {
            "predicted_revenue_30d": round(revenue_30d, 2),
            "predicted_revenue_60d": round(revenue_60d, 2),
            "predicted_revenue_90d": round(revenue_90d, 2)
        }
        
    except Exception as e:
        logger.error(f"Error calculating revenue forecast: {e}")
        return {
            "predicted_revenue_30d": 0.0,
            "predicted_revenue_60d": 0.0,
            "predicted_revenue_90d": 0.0
        }


def prepare_historical_data_for_prophet(
    segment_dimensions: Dict[str, Any],
    historical_rides: List[Dict[str, Any]],
    data_type: str = 'demand'
) -> Optional[pd.DataFrame]:
    """
    Prepare historical data in Prophet format for future ML forecasting.
    
    This function prepares time series data in the format Prophet ML expects:
    - ds: Date column (datetime)
    - y: Value column (demand count or price)
    
    Even though Prophet ML is not implemented yet, preparing this data now
    makes future integration straightforward.
    
    Args:
        segment_dimensions: Segment dimensions dictionary
        historical_rides: Historical ride data for this segment
        data_type: 'demand' (ride counts) or 'price' (prices)
    
    Returns:
        pandas DataFrame with columns ['ds', 'y'] ready for Prophet ML
        Returns None if insufficient data or error
    """
    try:
        if not historical_rides or len(historical_rides) < 3:
            return None
        
        # Prepare data list
        data_list = []
        
        for ride in historical_rides:
            # Extract date
            date = None
            for date_field in ['Order_Date', 'completed_at', 'uploaded_at', 'ds']:
                if ride.get(date_field):
                    try:
                        date = pd.to_datetime(ride[date_field])
                        break
                    except:
                        continue
            
            if date is None:
                continue
            
            # Extract value based on data_type
            if data_type == 'demand':
                # For demand: count each ride as 1
                value = 1.0
            elif data_type == 'price':
                # For price: use Historical_Cost_of_Ride or calculated price
                value = ride.get("Historical_Cost_of_Ride", 0)
                if value == 0:
                    value = ride.get("actual_price", 0)
                if value == 0:
                    continue  # Skip if no price data
            else:
                continue
            
            data_list.append({
                'ds': date,
                'y': float(value)
            })
        
        if len(data_list) < 3:
            return None
        
        # Create DataFrame
        df = pd.DataFrame(data_list)
        
        # Aggregate by date (sum for demand, average for price)
        if data_type == 'demand':
            df = df.groupby('ds')['y'].sum().reset_index()
        else:  # price
            df = df.groupby('ds')['y'].mean().reset_index()
        
        # Sort by date (Prophet requires chronological order)
        df = df.sort_values('ds').reset_index(drop=True)
        
        return df
        
    except Exception as e:
        logger.error(f"Error preparing historical data for Prophet: {e}")
        return None

