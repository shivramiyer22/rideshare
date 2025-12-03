"""
Segment Analysis Module - Provides price estimation based on segment dimensions.

This module analyzes ride segments (defined by location, loyalty, vehicle, pricing model)
and provides comprehensive price estimates by combining:
1. Historical data analysis (past rides in the segment)
2. Forecast predictions (future demand/pricing trends)
3. PricingEngine calculations (exact price if trip details available)

Used by:
- POST /api/v1/orders/estimate endpoint (price estimation for frontend)
- POST /api/v1/orders endpoint (order creation with computed fields)
- Chatbot Pricing Agent (price estimation queries)

LangChain Version: v1.0+
Documentation Reference: Backend pricing and forecasting integration
Last Updated: 2025-12-03
"""

import logging
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from app.database import get_database
from app.pricing_engine import PricingEngine

logger = logging.getLogger(__name__)


def analyze_segment_historical_data(
    location_category: str,
    loyalty_tier: str,
    vehicle_type: str,
    pricing_model: str
) -> Dict[str, Any]:
    """
    Query historical_rides collection for matching segment.
    
    This function finds past rides that match the given segment dimensions
    and calculates aggregate statistics (averages for price, distance, duration).
    
    Think of this as looking at "what similar rides cost in the past".
    
    Args:
        location_category: "Urban", "Suburban", or "Rural"
        loyalty_tier: "Gold", "Silver", or "Regular"
        vehicle_type: "Premium" or "Economy"
        pricing_model: "CONTRACTED", "STANDARD", or "CUSTOM"
    
    Returns:
        Dictionary with:
        - avg_price: Average historical cost of rides in this segment
        - avg_distance: Average distance (miles) for this segment
        - avg_duration: Average duration (minutes) for this segment
        - sample_size: Number of historical rides found
        - data_source: "historical_rides"
    """
    try:
        # Get MongoDB database
        database = get_database()
        if not database:
            logger.warning("Database not available for segment analysis")
            return {
                "avg_price": 0.0,
                "avg_distance": 0.0,
                "avg_duration": 0.0,
                "sample_size": 0,
                "data_source": "historical_rides"
            }
        
        collection = database["historical_rides"]
        
        # Build query filter (case-insensitive matching)
        # MongoDB field names: Location_Category, Customer_Loyalty_Status, Vehicle_Type, Pricing_Model
        query_filter = {
            "Location_Category": {"$regex": f"^{location_category}$", "$options": "i"},
            "Customer_Loyalty_Status": {"$regex": f"^{loyalty_tier}$", "$options": "i"},
            "Vehicle_Type": {"$regex": f"^{vehicle_type}$", "$options": "i"},
            "Pricing_Model": {"$regex": f"^{pricing_model}$", "$options": "i"}
        }
        
        # Query historical rides
        cursor = collection.find(query_filter).limit(1000)
        rides = list(cursor)
        
        if not rides or len(rides) == 0:
            logger.info(f"No historical data found for segment: {location_category}/{loyalty_tier}/{vehicle_type}/{pricing_model}")
            return {
                "avg_price": 0.0,
                "avg_distance": 0.0,
                "avg_duration": 0.0,
                "sample_size": 0,
                "data_source": "historical_rides"
            }
        
        # Calculate averages
        total_price = 0.0
        total_distance = 0.0
        total_duration = 0.0
        valid_count = 0
        
        for ride in rides:
            price = ride.get("Historical_Cost_of_Ride", 0)
            distance = ride.get("Distance", 0)
            duration = ride.get("Time", 0)
            
            if price > 0 and distance > 0:  # Only count valid rides
                total_price += price
                total_distance += distance
                total_duration += duration
                valid_count += 1
        
        if valid_count == 0:
            return {
                "avg_price": 0.0,
                "avg_distance": 0.0,
                "avg_duration": 0.0,
                "sample_size": 0,
                "data_source": "historical_rides"
            }
        
        # Calculate and return averages
        result = {
            "avg_price": round(total_price / valid_count, 2),
            "avg_distance": round(total_distance / valid_count, 2),
            "avg_duration": round(total_duration / valid_count, 2),
            "sample_size": valid_count,
            "data_source": "historical_rides"
        }
        
        logger.info(f"Segment analysis: {valid_count} rides, avg_price=${result['avg_price']}, avg_distance={result['avg_distance']}mi")
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing segment historical data: {e}")
        return {
            "avg_price": 0.0,
            "avg_distance": 0.0,
            "avg_duration": 0.0,
            "sample_size": 0,
            "data_source": "historical_rides",
            "error": str(e)
        }


def get_segment_forecast_data(
    location_category: str,
    loyalty_tier: str,
    vehicle_type: str,
    pricing_model: str,
    periods: int = 30
) -> Dict[str, Any]:
    """
    Query forecasting data for segment predictions.
    
    This function retrieves forecast predictions from the pricing_strategies collection
    (where pipeline results are stored) or returns conservative estimates if no forecast available.
    
    Think of this as "what we expect similar rides to cost in the next 30 days".
    
    Args:
        location_category: "Urban", "Suburban", or "Rural"
        loyalty_tier: "Gold", "Silver", or "Regular"
        vehicle_type: "Premium" or "Economy"
        pricing_model: "CONTRACTED", "STANDARD", or "CUSTOM"
        periods: Forecast period in days (default: 30)
    
    Returns:
        Dictionary with:
        - predicted_price_30d: Forecasted average price for next 30 days
        - predicted_demand_30d: Forecasted ride count for next 30 days
        - forecast_confidence: Confidence score (0-1) or None if unavailable
    """
    try:
        # Get MongoDB database
        database = get_database()
        if not database:
            logger.warning("Database not available for forecast data")
            return {
                "predicted_price_30d": 0.0,
                "predicted_demand_30d": 0.0,
                "forecast_confidence": None
            }
        
        collection = database["pricing_strategies"]
        
        # Query for latest forecast results (stored by pipeline)
        pipeline_result = collection.find_one(
            {"type": "pipeline_result"},
            sort=[("timestamp", -1)]
        )
        
        if not pipeline_result or "forecasts" not in pipeline_result:
            logger.info("No forecast data available, using conservative estimates")
            return {
                "predicted_price_30d": 0.0,
                "predicted_demand_30d": 0.0,
                "forecast_confidence": None
            }
        
        # Extract forecasts
        forecasts_data = pipeline_result.get("forecasts", {})
        segmented_forecasts = forecasts_data.get("segmented_forecasts", [])
        
        # Find matching segment (case-insensitive)
        for segment in segmented_forecasts:
            dims = segment.get("dimensions", {})
            if (dims.get("location", "").lower() == location_category.lower() and
                dims.get("loyalty_tier", "").lower() == loyalty_tier.lower() and
                dims.get("vehicle_type", "").lower() == vehicle_type.lower() and
                dims.get("pricing_model", "").lower() == pricing_model.lower()):
                
                # Extract 30-day forecast
                forecast_30d = segment.get("forecast_30d", {})
                baseline = segment.get("baseline_metrics", {})
                
                return {
                    "predicted_price_30d": round(baseline.get("pricing_engine_price", baseline.get("avg_price", 0.0)), 2),
                    "predicted_demand_30d": round(forecast_30d.get("predicted_rides", 0.0), 2),
                    "forecast_confidence": 0.8  # Default confidence
                }
        
        # No matching segment found
        logger.info(f"No forecast found for segment: {location_category}/{loyalty_tier}/{vehicle_type}/{pricing_model}")
        return {
            "predicted_price_30d": 0.0,
            "predicted_demand_30d": 0.0,
            "forecast_confidence": None
        }
    
    except Exception as e:
        logger.error(f"Error getting segment forecast data: {e}")
        return {
            "predicted_price_30d": 0.0,
            "predicted_demand_30d": 0.0,
            "forecast_confidence": None,
            "error": str(e)
        }


def calculate_segment_estimate(
    segment_dimensions: Dict[str, str],
    trip_details: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Main estimation function combining historical + forecast + PricingEngine.
    
    This is the core function that provides comprehensive price estimates.
    It combines three data sources:
    1. Historical baseline (what similar rides cost in the past)
    2. Forecast prediction (what we expect for the future)
    3. PricingEngine calculation (exact price if trip details available)
    
    Strategy:
    - If trip_details provided (distance, duration): Use PricingEngine for exact calculation
    - Otherwise: Use segment average from historical data as estimate
    - Always provide both historical baseline and forecast for context
    
    Args:
        segment_dimensions: Dict with location_category, loyalty_tier, vehicle_type, pricing_model
        trip_details: Optional dict with distance (miles) and duration (minutes)
    
    Returns:
        Dictionary with:
        - segment: The segment dimensions
        - historical_baseline: {avg_price, avg_distance, avg_duration, sample_size}
        - forecast_prediction: {predicted_price_30d, predicted_demand_30d}
        - estimated_price: The recommended price estimate
        - price_breakdown: Detailed breakdown (if trip_details provided)
        - explanation: Natural language explanation
        - assumptions: List of assumptions made
    """
    try:
        # Extract segment dimensions
        location_category = segment_dimensions.get("location_category", "Urban")
        loyalty_tier = segment_dimensions.get("loyalty_tier", "Regular")
        vehicle_type = segment_dimensions.get("vehicle_type", "Economy")
        pricing_model = segment_dimensions.get("pricing_model", "STANDARD")
        
        logger.info(f"Calculating estimate for segment: {location_category}/{loyalty_tier}/{vehicle_type}/{pricing_model}")
        
        # 1. Get historical baseline
        historical = analyze_segment_historical_data(
            location_category, loyalty_tier, vehicle_type, pricing_model
        )
        
        # 2. Get forecast prediction
        forecast = get_segment_forecast_data(
            location_category, loyalty_tier, vehicle_type, pricing_model
        )
        
        # 3. Calculate estimated price
        estimated_price = 0.0
        price_breakdown = None
        explanation_parts = []
        assumptions = []
        
        # Case A: Trip details provided - use PricingEngine for exact calculation
        if trip_details and trip_details.get("distance") and trip_details.get("duration"):
            try:
                pricing_engine = PricingEngine()
                
                # Build order_data for PricingEngine
                order_data = {
                    "pricing_model": pricing_model.upper(),
                    "distance": trip_details["distance"],
                    "duration": trip_details["duration"],
                    "time_of_day": "regular",  # Default
                    "location_type": "urban_regular" if location_category.lower() == "urban" else "suburban",
                    "vehicle_type": vehicle_type.lower(),
                    "supply_demand_ratio": 0.7,  # Default
                    "customer": {"loyalty_tier": loyalty_tier}
                }
                
                # Calculate price using PricingEngine
                result = pricing_engine.calculate_price(order_data)
                estimated_price = result.get("final_price", 0.0)
                
                # Extract breakdown
                price_breakdown = {
                    "base_fare": result.get("base_fare"),
                    "distance_cost": result.get("distance_cost"),
                    "time_cost": result.get("time_cost"),
                    "surge_multiplier": result.get("multipliers", {}).get("surge", {}).get("value", 1.0),
                    "loyalty_discount": result.get("discounts", {}).get("loyalty", {}).get("value", 0.0),
                    "final_price": estimated_price
                }
                
                explanation_parts.append(f"Exact price calculated using PricingEngine: ${estimated_price:.2f}")
                explanation_parts.append(f"Based on {trip_details['distance']:.1f} miles and {trip_details['duration']:.1f} minutes")
                assumptions.append("Using PricingEngine with provided trip details")
                
            except Exception as e:
                logger.warning(f"PricingEngine failed, using segment average: {e}")
                estimated_price = historical["avg_price"]
                explanation_parts.append(f"Using segment average price: ${estimated_price:.2f}")
                assumptions.append("PricingEngine unavailable, using historical average")
        
        # Case B: No trip details - use segment average
        else:
            estimated_price = historical["avg_price"]
            
            if estimated_price > 0:
                explanation_parts.append(f"Segment average price from {historical['sample_size']} historical rides: ${estimated_price:.2f}")
                explanation_parts.append(f"Average trip: {historical['avg_distance']:.1f} miles, {historical['avg_duration']:.1f} minutes")
            else:
                # No historical data - use forecast or conservative estimate
                if forecast["predicted_price_30d"] > 0:
                    estimated_price = forecast["predicted_price_30d"]
                    explanation_parts.append(f"Using forecasted price (no historical data): ${estimated_price:.2f}")
                    assumptions.append("Limited historical data, using forecast prediction")
                else:
                    estimated_price = 15.0  # Conservative default
                    explanation_parts.append(f"Using conservative default estimate: ${estimated_price:.2f}")
                    assumptions.append("No historical or forecast data available")
        
        # Add forecast context
        if forecast["predicted_price_30d"] > 0:
            explanation_parts.append(f"30-day forecast: ${forecast['predicted_price_30d']:.2f} per ride, {forecast['predicted_demand_30d']:.0f} rides expected")
        
        # Add segment context
        explanation_parts.append(f"Segment: {location_category} / {loyalty_tier} / {vehicle_type} / {pricing_model}")
        
        # Build assumptions
        if historical["sample_size"] > 0:
            assumptions.append(f"Historical data from {historical['sample_size']} similar rides")
        if forecast["forecast_confidence"]:
            assumptions.append(f"Forecast confidence: {forecast['forecast_confidence']*100:.0f}%")
        assumptions.append("Prices may vary based on real-time demand, traffic, and events")
        
        # Combine explanation
        explanation = " | ".join(explanation_parts)
        
        # Build result
        result = {
            "segment": segment_dimensions,
            "historical_baseline": historical,
            "forecast_prediction": forecast,
            "estimated_price": round(estimated_price, 2),
            "price_breakdown": price_breakdown,
            "explanation": explanation,
            "assumptions": assumptions
        }
        
        logger.info(f"Estimate calculated: ${estimated_price:.2f}")
        return result
    
    except Exception as e:
        logger.error(f"Error calculating segment estimate: {e}")
        
        # Return conservative fallback
        return {
            "segment": segment_dimensions,
            "historical_baseline": {
                "avg_price": 15.0,
                "avg_distance": 5.0,
                "avg_duration": 15.0,
                "sample_size": 0,
                "data_source": "fallback"
            },
            "forecast_prediction": {
                "predicted_price_30d": 15.0,
                "predicted_demand_30d": 0.0,
                "forecast_confidence": None
            },
            "estimated_price": 15.0,
            "price_breakdown": None,
            "explanation": f"Conservative estimate due to error: {str(e)}",
            "assumptions": ["Fallback estimate used due to system error"]
        }
