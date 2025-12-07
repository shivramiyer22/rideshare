"""
Pricing Helper Functions - Integration between PricingEngine and Agent Tools

This module provides helper functions to:
1. Convert segment dimensions to PricingEngine order_data format
2. Apply pricing rules to order_data
3. Calculate prices using PricingEngine for segments

These functions enable PricingEngine integration into Forecasting, Recommendation, and What-If Analysis.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def build_order_data_from_segment(
    segment_dimensions: Dict[str, Any],
    historical_rides_sample: List[Dict[str, Any]],
    pricing_engine=None
) -> Dict[str, Any]:
    """
    Convert segment dimensions to PricingEngine order_data format.
    
    This function extracts average distance/duration from historical rides
    and maps segment dimensions to PricingEngine-compatible fields.
    
    Args:
        segment_dimensions: Dictionary with keys:
            - loyalty_tier: "Gold", "Silver", or "Regular"
            - vehicle_type: "Premium" or "Economy"
            - demand_profile: "HIGH", "MEDIUM", or "LOW"
            - pricing_model: "CONTRACTED", "STANDARD", or "CUSTOM"
            - location: "Urban", "Suburban", or "Rural"
        historical_rides_sample: List of historical ride documents from MongoDB
        pricing_engine: Optional PricingEngine instance (not used here, but kept for future extensibility)
    
    Returns:
        Dictionary in PricingEngine order_data format ready for calculate_price()
    """
    try:
        # Extract average distance and duration from historical rides
        distances = []
        durations = []
        
        for ride in historical_rides_sample:
            # Try different field names that might exist
            distance = ride.get("Expected_Ride_Duration")  # This might be duration, not distance
            duration = ride.get("Expected_Ride_Duration", 0)
            
            # If we have actual distance/duration fields, use them
            if ride.get("distance"):
                distances.append(float(ride["distance"]))
            if ride.get("duration"):
                durations.append(float(ride["duration"]))
            elif ride.get("Expected_Ride_Duration"):
                # Use Expected_Ride_Duration as a proxy for duration
                durations.append(float(ride["Expected_Ride_Duration"]))
        
        # Calculate averages (with defaults if no data)
        avg_distance = sum(distances) / len(distances) if distances else 10.0  # Default 10 miles
        avg_duration = sum(durations) / len(durations) if durations else 25.0  # Default 25 minutes
        
        # Map segment dimensions to PricingEngine fields
        loyalty_tier = segment_dimensions.get("loyalty_tier", "Regular")
        vehicle_type = segment_dimensions.get("vehicle_type", "Economy")
        location = segment_dimensions.get("location", "Urban")
        pricing_model = segment_dimensions.get("pricing_model", "STANDARD")
        demand_profile = segment_dimensions.get("demand_profile", "MEDIUM")
        
        # Map vehicle_type: "Premium" -> "premium", "Economy" -> "economy"
        vehicle_type_mapped = vehicle_type.lower() if vehicle_type else "economy"
        
        # Map location: "Urban" -> "urban_high_demand" or "urban_regular"
        # "Suburban" -> "suburban", "Rural" -> "suburban" (closest match)
        if location == "Urban":
            location_type = "urban_high_demand" if demand_profile == "HIGH" else "urban_regular"
        elif location == "Suburban":
            location_type = "suburban"
        else:  # Rural
            location_type = "suburban"  # Closest match
        
        # Map demand_profile to supply_demand_ratio
        # HIGH demand = low supply/demand ratio (0.3), MEDIUM = 0.5, LOW = 0.7
        supply_demand_ratio_map = {
            "HIGH": 0.3,
            "MEDIUM": 0.5,
            "LOW": 0.7
        }
        supply_demand_ratio = supply_demand_ratio_map.get(demand_profile.upper(), 0.5)
        
        # Map time_of_day based on demand_profile or use default
        # HIGH demand might indicate rush hour, LOW might indicate regular time
        time_of_day = "evening_rush" if demand_profile == "HIGH" else "regular"
        
        # Build order_data dictionary
        order_data = {
            "pricing_model": pricing_model,
            "distance": round(avg_distance, 2),
            "duration": round(avg_duration, 2),
            "time_of_day": time_of_day,
            "location_type": location_type,
            "vehicle_type": vehicle_type_mapped,
            "supply_demand_ratio": supply_demand_ratio,
            "customer": {
                "loyalty_tier": loyalty_tier
            }
        }
        
        # Add fixed_price for CONTRACTED pricing
        if pricing_model == "CONTRACTED":
            # Use average historical price as fixed_price
            prices = [r.get("Historical_Cost_of_Ride", 0) for r in historical_rides_sample if r.get("Historical_Cost_of_Ride")]
            if prices:
                avg_price = sum(prices) / len(prices)
                order_data["fixed_price"] = round(avg_price, 2)
        
        return order_data
        
    except Exception as e:
        logger.error(f"Error building order_data from segment: {e}")
        # Return default order_data on error
        return {
            "pricing_model": segment_dimensions.get("pricing_model", "STANDARD"),
            "distance": 10.0,
            "duration": 25.0,
            "time_of_day": "regular",
            "location_type": "urban_regular",
            "vehicle_type": "economy",
            "supply_demand_ratio": 0.5,
            "customer": {
                "loyalty_tier": segment_dimensions.get("loyalty_tier", "Regular")
            }
        }


def apply_pricing_rule_to_order_data(order_data: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply a pricing rule's conditions and actions to order_data.
    
    This function checks if a rule applies to the order_data based on rule conditions,
    then applies the rule's action (multiplier) to modify the order_data.
    
    Args:
        order_data: Order data dictionary (from build_order_data_from_segment or similar)
        rule: Pricing rule dictionary with:
            - condition: Dict with field/value pairs to match
            - action: Dict with multiplier or other actions
    
    Returns:
        Modified order_data with rule applied (or original if rule doesn't apply)
    """
    try:
        rule_condition = rule.get("condition", {})
        rule_action = rule.get("action", {})
        
        # Check if rule applies (exact match on conditions)
        applies = True
        for field, value in rule_condition.items():
            if field == "min_rides":
                continue  # Skip min_rides condition
            
            # Map rule condition fields to order_data fields
            if field == "location":
                # Check location_type
                location = order_data.get("location_type", "")
                if value == "Urban":
                    if "urban" not in location:
                        applies = False
                        break
                elif value == "Suburban":
                    if "suburban" not in location:
                        applies = False
                        break
                elif value == "Rural":
                    if "suburban" not in location:  # Closest match
                        applies = False
                        break
            elif field == "loyalty_tier":
                customer = order_data.get("customer", {})
                if customer.get("loyalty_tier") != value:
                    applies = False
                    break
            elif field == "vehicle_type":
                if order_data.get("vehicle_type") != value.lower():
                    applies = False
                    break
            elif field == "pricing_model":
                if order_data.get("pricing_model") != value:
                    applies = False
                    break
            elif field == "demand_profile":
                # Map demand_profile to supply_demand_ratio
                supply_demand_ratio = order_data.get("supply_demand_ratio", 0.5)
                if value == "HIGH" and supply_demand_ratio > 0.4:
                    applies = False
                    break
                elif value == "MEDIUM" and (supply_demand_ratio < 0.4 or supply_demand_ratio > 0.6):
                    applies = False
                    break
                elif value == "LOW" and supply_demand_ratio < 0.6:
                    applies = False
                    break
        
        if not applies:
            return order_data  # Rule doesn't apply, return original
        
        # Apply rule action (multiplier)
        multiplier = rule_action.get("multiplier", rule_action.get("max_multiplier", 1.0))
        
        # Apply multiplier to base price calculation
        # For STANDARD/CUSTOM: multiplier affects the final price
        # For CONTRACTED: multiplier affects fixed_price
        if order_data.get("pricing_model") == "CONTRACTED":
            if "fixed_price" in order_data:
                order_data["fixed_price"] = order_data["fixed_price"] * multiplier
        else:
            # For STANDARD/CUSTOM, we'll apply multiplier via a custom field
            # The PricingEngine will need to handle this, or we modify the base rates
            # For now, store multiplier in order_data for PricingEngine to use
            order_data["rule_multiplier"] = multiplier
        
        return order_data
        
    except Exception as e:
        logger.error(f"Error applying pricing rule to order_data: {e}")
        return order_data  # Return original on error


def calculate_segment_price_with_engine(
    segment_dimensions: Dict[str, Any],
    historical_rides_sample: List[Dict[str, Any]],
    pricing_engine
) -> Dict[str, Any]:
    """
    Calculate price for a segment using PricingEngine.
    
    This is a wrapper function that:
    1. Builds order_data from segment dimensions
    2. Calls PricingEngine.calculate_price()
    3. Returns final_price and breakdown
    
    Args:
        segment_dimensions: Segment dimensions dictionary
        historical_rides_sample: Historical rides for this segment
        pricing_engine: PricingEngine instance
    
    Returns:
        Dictionary with:
            - final_price: Calculated price
            - breakdown: Price breakdown
            - pricing_model: Pricing model used
            - revenue_score: Revenue score
    """
    try:
        # Build order_data from segment
        order_data = build_order_data_from_segment(segment_dimensions, historical_rides_sample)
        
        # Handle rule_multiplier if present (from apply_pricing_rule_to_order_data)
        rule_multiplier = order_data.pop("rule_multiplier", None)
        
        # Calculate price using PricingEngine
        result = pricing_engine.calculate_price(order_data)
        
        # Apply rule multiplier if present (for STANDARD/CUSTOM pricing)
        if rule_multiplier and rule_multiplier != 1.0:
            original_price = result.get("final_price", 0)
            result["final_price"] = round(original_price * rule_multiplier, 2)
            # Update breakdown
            if "breakdown" in result:
                result["breakdown"]["rule_multiplier"] = {
                    "value": rule_multiplier,
                    "description": "Applied from pricing rule"
                }
                result["breakdown"]["final_price"] = result["final_price"]
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating segment price with engine: {e}")
        # Fallback: calculate average from historical data
        prices = [r.get("Historical_Cost_of_Ride", 0) for r in historical_rides_sample if r.get("Historical_Cost_of_Ride")]
        avg_price = sum(prices) / len(prices) if prices else 0
        
        return {
            "final_price": round(avg_price, 2),
            "breakdown": {"error": "Used historical average as fallback"},
            "pricing_model": segment_dimensions.get("pricing_model", "STANDARD"),
            "revenue_score": 0.0
        }

