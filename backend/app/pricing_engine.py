"""
Pricing Engine - Handles CONTRACTED, STANDARD, and CUSTOM pricing models.

This engine calculates dynamic prices for ride orders with detailed multiplier breakdowns.

Pricing Models:
- CONTRACTED: Fixed price (no multipliers) - like a subscription, predictable cost
- STANDARD: Base price + multipliers (time, location, vehicle, surge) + loyalty discount
- CUSTOM: Same as STANDARD but with different base rates (negotiated rates)

The engine calculates revenue_score which is used to prioritize orders in queues:
- P0 (CONTRACTED): FIFO (first in, first out)
- P1 (STANDARD): Sorted by revenue_score DESC (highest value first)
- P2 (CUSTOM): Sorted by revenue_score DESC (highest value first)
"""

from typing import Dict, Any, Literal, Optional
from enum import Enum
from datetime import datetime


class PricingModel(str, Enum):
    """Pricing model enumeration."""
    CONTRACTED = "CONTRACTED"
    STANDARD = "STANDARD"
    CUSTOM = "CUSTOM"


class PricingEngine:
    """
    Pricing engine for calculating ride prices with detailed breakdowns.
    
    This engine handles three pricing models:
    1. CONTRACTED: Fixed price (no multipliers) - for subscription-based customers
    2. STANDARD: Dynamic pricing with multipliers - for regular customers
    3. CUSTOM: Dynamic pricing with different base rates - for negotiated contracts
    
    Usage:
        engine = PricingEngine()
        result = engine.calculate_price({
            "pricing_model": "STANDARD",
            "distance": 10.5,
            "duration": 25.0,
            "time_of_day": "evening_rush",
            "location_type": "urban_high_demand",
            "vehicle_type": "premium",
            "supply_demand_ratio": 0.4,
            "customer": {"loyalty_tier": "Gold"},
            "fixed_price": 45.00  # Only for CONTRACTED
        })
    """
    
    def __init__(self):
        """
        Initialize pricing engine with base rates.
        
        Base rates are the starting point for price calculation.
        Think of them as the "menu price" before any adjustments.
        """
        # Base fare (starting cost for any ride)
        self.base_fare = {
            PricingModel.STANDARD: 4.00,
            PricingModel.CUSTOM: 5.00
            # CONTRACTED doesn't use base_fare (uses fixed_price instead)
        }
        
        # Rate per mile (distance-based pricing)
        self.rate_per_mile = {
            PricingModel.STANDARD: 2.00,
            PricingModel.CUSTOM: 2.50
        }
        
        # Rate per minute (time-based pricing)
        self.rate_per_minute = {
            PricingModel.STANDARD: 0.30,
            PricingModel.CUSTOM: 0.35
        }
    
    def calculate_base_price(self, distance: float, duration: float, pricing_model: PricingModel) -> float:
        """
        Calculate base price from distance and duration.
        
        Formula: base_fare + (distance * rate_per_mile) + (duration * rate_per_minute)
        
        Think of this as the "base menu price" before any multipliers are applied.
        Like ordering a pizza - base price + toppings (multipliers).
        
        Args:
            distance: Distance in miles
            duration: Duration in minutes
            pricing_model: STANDARD or CUSTOM (CONTRACTED doesn't use this)
            
        Returns:
            Base price as float
        """
        base_fare = self.base_fare[pricing_model]
        distance_cost = distance * self.rate_per_mile[pricing_model]
        time_cost = duration * self.rate_per_minute[pricing_model]
        
        base_price = base_fare + distance_cost + time_cost
        return round(base_price, 2)
    
    def _calculate_time_multiplier(self, time_of_day: str) -> Dict[str, Any]:
        """
        Calculate time-of-day multiplier.
        
        Different times of day have different demand:
        - Morning rush: People going to work (1.3x)
        - Evening rush: People going home (1.4x - busiest!)
        - Night: Late night rides (1.2x)
        - Regular: Normal times (1.0x - no multiplier)
        
        Args:
            time_of_day: One of "morning_rush", "evening_rush", "night", "regular"
            
        Returns:
            Dictionary with multiplier value and description
        """
        multipliers = {
            "morning_rush": 1.3,
            "evening_rush": 1.4,  # Highest multiplier - most demand
            "night": 1.2,
            "regular": 1.0
        }
        
        multiplier = multipliers.get(time_of_day.lower(), 1.0)
        descriptions = {
            "morning_rush": "Morning rush hour (1.3x)",
            "evening_rush": "Evening rush hour (1.4x)",
            "night": "Late night hours (1.2x)",
            "regular": "Regular hours (1.0x)"
        }
        
        return {
            "value": multiplier,
            "description": descriptions.get(time_of_day.lower(), "Regular hours (1.0x)")
        }
    
    def _calculate_location_multiplier(self, location_type: str) -> Dict[str, Any]:
        """
        Calculate location-based multiplier.
        
        Some locations have higher demand than others:
        - Urban high demand: Downtown, airports, events (1.3x)
        - Urban regular: Regular city areas (1.15x)
        - Suburban: Less demand (1.0x - no multiplier)
        
        Args:
            location_type: One of "urban_high_demand", "urban_regular", "suburban"
            
        Returns:
            Dictionary with multiplier value and description
        """
        multipliers = {
            "urban_high_demand": 1.3,
            "urban_regular": 1.15,
            "suburban": 1.0
        }
        
        multiplier = multipliers.get(location_type.lower(), 1.0)
        descriptions = {
            "urban_high_demand": "Urban high demand area (1.3x)",
            "urban_regular": "Urban regular area (1.15x)",
            "suburban": "Suburban area (1.0x)"
        }
        
        return {
            "value": multiplier,
            "description": descriptions.get(location_type.lower(), "Suburban area (1.0x)")
        }
    
    def _calculate_vehicle_multiplier(self, vehicle_type: str) -> Dict[str, Any]:
        """
        Calculate vehicle type multiplier.
        
        Premium vehicles cost more:
        - Premium: Luxury vehicles (1.6x)
        - Economy: Standard vehicles (1.0x - no multiplier)
        
        Args:
            vehicle_type: One of "premium", "economy"
            
        Returns:
            Dictionary with multiplier value and description
        """
        multipliers = {
            "premium": 1.6,
            "economy": 1.0
        }
        
        multiplier = multipliers.get(vehicle_type.lower(), 1.0)
        descriptions = {
            "premium": "Premium vehicle (1.6x)",
            "economy": "Economy vehicle (1.0x)"
        }
        
        return {
            "value": multiplier,
            "description": descriptions.get(vehicle_type.lower(), "Economy vehicle (1.0x)")
        }
    
    def _calculate_surge_multiplier(self, supply_demand_ratio: float) -> Dict[str, Any]:
        """
        Calculate surge pricing multiplier based on supply/demand ratio.
        
        Surge pricing adjusts prices when demand is high and supply is low.
        Think of it like Uber's surge pricing - when there are more riders than drivers.
        
        Formula: supply_demand_ratio = number_of_drivers / number_of_riders
        - Lower ratio = fewer drivers per rider = higher surge
        - Higher ratio = more drivers per rider = lower surge
        
        Thresholds:
        - < 0.3: Very high demand, very low supply (2.0x - maximum surge)
        - 0.3-0.5: High demand, low supply (1.6x)
        - 0.5-0.7: Moderate demand (1.3x)
        - >= 0.9: Balanced or oversupply (1.0x - no surge)
        
        Args:
            supply_demand_ratio: Ratio of drivers to riders (0.0 to 1.0+)
            
        Returns:
            Dictionary with multiplier value and description
        """
        if supply_demand_ratio < 0.3:
            multiplier = 2.0
            description = "Very high demand, low supply (2.0x surge)"
        elif supply_demand_ratio < 0.5:
            multiplier = 1.6
            description = "High demand, low supply (1.6x surge)"
        elif supply_demand_ratio < 0.7:
            multiplier = 1.3
            description = "Moderate demand (1.3x surge)"
        else:  # >= 0.7
            multiplier = 1.0
            description = "Balanced supply/demand (1.0x - no surge)"
        
        return {
            "value": multiplier,
            "description": description
        }
    
    def _calculate_loyalty_discount(self, loyalty_tier: str) -> Dict[str, Any]:
        """
        Calculate loyalty discount.
        
        Loyal customers get discounts:
        - Gold: 15% discount (0.15) - best customers
        - Silver: 10% discount (0.10) - good customers
        - Regular: 0% discount (0.0) - no discount
        
        Args:
            loyalty_tier: One of "Gold", "Silver", "Regular"
            
        Returns:
            Dictionary with discount percentage and amount
        """
        discounts = {
            "gold": 0.15,  # 15% discount
            "silver": 0.10,  # 10% discount
            "regular": 0.0  # No discount
        }
        
        discount_percentage = discounts.get(loyalty_tier.lower(), 0.0)
        
        return {
            "percentage": discount_percentage,
            "tier": loyalty_tier
        }
    
    def _calculate_revenue_score(self, final_price: float, loyalty_tier: str) -> float:
        """
        Calculate revenue score for queue prioritization.
        
        Revenue score helps prioritize orders in queues (P1 and P2).
        Higher revenue score = more valuable customer = process first.
        
        Formula: final_price * (1 + loyalty_multiplier)
        - Gold customers: +20% to revenue score (they're valuable long-term)
        - Silver customers: +10% to revenue score
        - Regular customers: No bonus
        
        This means a Gold customer's $50 ride is worth $60 in revenue score.
        
        Args:
            final_price: Final calculated price
            loyalty_tier: Customer loyalty tier
            
        Returns:
            Revenue score as float
        """
        loyalty_multipliers = {
            "gold": 0.2,  # 20% bonus
            "silver": 0.1,  # 10% bonus
            "regular": 0.0  # No bonus
        }
        
        loyalty_multiplier = loyalty_multipliers.get(loyalty_tier.lower(), 0.0)
        revenue_score = final_price * (1 + loyalty_multiplier)
        
        return round(revenue_score, 2)
    
    def calculate_price(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate price for a ride order with detailed breakdown.
        
        This is the main method that orchestrates all pricing calculations.
        
        Process:
        1. Determine pricing_model (CONTRACTED/STANDARD/CUSTOM)
        2. If CONTRACTED: Return fixed_price (no multipliers)
        3. If STANDARD/CUSTOM:
           a. Calculate base_price from distance and duration
           b. Apply multipliers (time, location, vehicle, surge)
           c. Apply loyalty discount
           d. Calculate final_price
           e. Calculate revenue_score
        
        Args:
            order_data: Dictionary containing:
                - pricing_model: "CONTRACTED", "STANDARD", or "CUSTOM"
                - distance: Distance in miles (for STANDARD/CUSTOM)
                - duration: Duration in minutes (for STANDARD/CUSTOM)
                - time_of_day: "morning_rush", "evening_rush", "night", "regular"
                - location_type: "urban_high_demand", "urban_regular", "suburban"
                - vehicle_type: "premium", "economy"
                - supply_demand_ratio: Float (0.0 to 1.0+)
                - customer: Dict with "loyalty_tier" ("Gold", "Silver", "Regular")
                - fixed_price: Float (only for CONTRACTED)
        
        Returns:
            Dictionary with:
                - final_price: Calculated final price
                - breakdown: Detailed breakdown of all calculations
                - revenue_score: Revenue score for queue prioritization
                - pricing_model: CONTRACTED/STANDARD/CUSTOM
        """
        # Step 1: Determine pricing model
        pricing_model_str = order_data.get("pricing_model", "STANDARD").upper()
        
        try:
            pricing_model = PricingModel(pricing_model_str)
        except ValueError:
            raise ValueError(f"Invalid pricing_model: {pricing_model_str}. Must be CONTRACTED, STANDARD, or CUSTOM")
        
        # Step 2: Handle CONTRACTED pricing (fixed price, no multipliers)
        if pricing_model == PricingModel.CONTRACTED:
            fixed_price = order_data.get("fixed_price")
            if fixed_price is None:
                raise ValueError("CONTRACTED pricing requires 'fixed_price' in order_data")
            
            customer = order_data.get("customer", {})
            loyalty_tier = customer.get("loyalty_tier", "Regular")
            
            # CONTRACTED still gets loyalty discount
            loyalty_discount = self._calculate_loyalty_discount(loyalty_tier)
            discount_amount = fixed_price * loyalty_discount["percentage"]
            final_price = fixed_price - discount_amount
            
            # Calculate revenue score
            revenue_score = self._calculate_revenue_score(final_price, loyalty_tier)
            
            return {
                "final_price": round(final_price, 2),
                "breakdown": {
                    "base_price": fixed_price,
                    "pricing_model": "CONTRACTED (fixed price)",
                    "multipliers": {
                        "time_of_day": {"value": 1.0, "description": "No multipliers for CONTRACTED"},
                        "location": {"value": 1.0, "description": "No multipliers for CONTRACTED"},
                        "vehicle": {"value": 1.0, "description": "No multipliers for CONTRACTED"},
                        "surge": {"value": 1.0, "description": "No multipliers for CONTRACTED"}
                    },
                    "multiplier_product": 1.0,
                    "loyalty_discount": {
                        "percentage": loyalty_discount["percentage"],
                        "amount": round(discount_amount, 2),
                        "tier": loyalty_tier
                    },
                    "final_price": round(final_price, 2)
                },
                "revenue_score": revenue_score,
                "pricing_model": "CONTRACTED"
            }
        
        # Step 3: Handle STANDARD and CUSTOM pricing (with multipliers)
        # Extract required fields
        distance = order_data.get("distance")
        duration = order_data.get("duration")
        
        if distance is None or duration is None:
            raise ValueError(f"{pricing_model.value} pricing requires 'distance' and 'duration' in order_data")
        
        time_of_day = order_data.get("time_of_day", "regular")
        location_type = order_data.get("location_type", "suburban")
        vehicle_type = order_data.get("vehicle_type", "economy")
        supply_demand_ratio = order_data.get("supply_demand_ratio", 1.0)
        customer = order_data.get("customer", {})
        loyalty_tier = customer.get("loyalty_tier", "Regular")
        
        # Step 3a: Calculate base price
        base_price = self.calculate_base_price(distance, duration, pricing_model)
        
        # Step 3b: Calculate all multipliers
        time_mult = self._calculate_time_multiplier(time_of_day)
        location_mult = self._calculate_location_multiplier(location_type)
        vehicle_mult = self._calculate_vehicle_multiplier(vehicle_type)
        surge_mult = self._calculate_surge_multiplier(supply_demand_ratio)
        
        # Step 3c: Calculate multiplier product
        # This is like compound interest - each multiplier multiplies the price
        multiplier_product = time_mult["value"] * location_mult["value"] * vehicle_mult["value"] * surge_mult["value"]
        
        # Step 3d: Apply multipliers to base price
        price_after_multipliers = base_price * multiplier_product
        
        # Step 3e: Apply loyalty discount
        loyalty_discount = self._calculate_loyalty_discount(loyalty_tier)
        discount_amount = price_after_multipliers * loyalty_discount["percentage"]
        final_price = price_after_multipliers - discount_amount
        
        # Step 3f: Calculate revenue score
        revenue_score = self._calculate_revenue_score(final_price, loyalty_tier)
        
        # Step 4: Build detailed breakdown
        breakdown = {
            "base_price": base_price,
            "pricing_model": pricing_model.value,
            "multipliers": {
                "time_of_day": time_mult,
                "location": location_mult,
                "vehicle": vehicle_mult,
                "surge": surge_mult
            },
            "multiplier_product": round(multiplier_product, 4),
            "price_after_multipliers": round(price_after_multipliers, 2),
            "loyalty_discount": {
                "percentage": loyalty_discount["percentage"],
                "amount": round(discount_amount, 2),
                "tier": loyalty_tier
            },
            "final_price": round(final_price, 2)
        }
        
        return {
            "final_price": round(final_price, 2),
            "breakdown": breakdown,
            "revenue_score": revenue_score,
            "pricing_model": pricing_model.value
        }


# Global pricing engine instance
# This can be imported and used throughout the application
pricing_engine = PricingEngine()
