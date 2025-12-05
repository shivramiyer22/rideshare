"""
Forecasting Agent - Handles demand and trend forecasting.

This agent generates forecasts using:
- Prophet ML models for time series predictions
- n8n ingested data (events, traffic) for context
- Historical patterns and trends

The agent provides:
- 30/60/90-day demand forecasts
- Forecast explanations in natural language
- Context from external events (n8n data)
"""
from langchain.agents import create_agent
from langchain.tools import tool
from typing import Dict, Any, List
from datetime import datetime
import asyncio
import json
from app.agents.utils import (
    query_chromadb, 
    fetch_mongodb_documents, 
    format_documents_as_context,
    query_historical_rides,
    query_events_data,
    query_traffic_data,
    query_news_data
)
from app.forecasting_ml import RideshareForecastModel
from app.config import settings
from app.pricing_engine import PricingEngine
from app.agents.forecasting_helpers import (
    forecast_demand_for_segment,
    forecast_price_for_segment,
    calculate_revenue_forecast,
    prepare_historical_data_for_prophet
)


# Initialize forecasting model instance
forecast_model = RideshareForecastModel()

# Initialize PricingEngine instance for price calculations
pricing_engine = PricingEngine()


@tool
def get_historical_demand_data(
    month: str = "",
    pricing_model: str = "",
    limit: int = 100
) -> str:
    """
    Query actual historical ride demand data from MongoDB.
    
    Use this tool to understand past demand patterns for forecasting.
    Returns ride counts, prices, and timing patterns from actual data.
    
    Args:
        month: Month name (e.g., "November") or number (1-12). Empty for all.
        pricing_model: "CONTRACTED", "STANDARD", or "CUSTOM". Empty for all.
        limit: Maximum records (default: 100)
    
    Returns:
        str: JSON string with historical demand statistics
    """
    try:
        results = query_historical_rides(
            month=month,
            pricing_model=pricing_model,
            limit=limit
        )
        
        if not results:
            return json.dumps({"error": "No historical data found", "count": 0})
        
        # Analyze demand patterns
        by_time = {}
        by_location = {}
        by_model = {}
        
        for r in results:
            # By time of day
            time = r.get("Time_of_Ride", "Unknown")
            if time not in by_time:
                by_time[time] = {"count": 0, "total_revenue": 0}
            by_time[time]["count"] += 1
            by_time[time]["total_revenue"] += r.get("Historical_Cost_of_Ride", 0)
            
            # By location
            loc = r.get("Location_Category", "Unknown")
            if loc not in by_location:
                by_location[loc] = {"count": 0, "total_revenue": 0}
            by_location[loc]["count"] += 1
            by_location[loc]["total_revenue"] += r.get("Historical_Cost_of_Ride", 0)
            
            # By pricing model
            model = r.get("Pricing_Model", "Unknown")
            if model not in by_model:
                by_model[model] = {"count": 0, "total_revenue": 0}
            by_model[model]["count"] += 1
            by_model[model]["total_revenue"] += r.get("Historical_Cost_of_Ride", 0)
        
        # Calculate averages
        for time in by_time:
            by_time[time]["avg_revenue"] = round(by_time[time]["total_revenue"] / by_time[time]["count"], 2)
        for loc in by_location:
            by_location[loc]["avg_revenue"] = round(by_location[loc]["total_revenue"] / by_location[loc]["count"], 2)
        for model in by_model:
            by_model[model]["avg_revenue"] = round(by_model[model]["total_revenue"] / by_model[model]["count"], 2)
        
        total_revenue = sum(r.get("Historical_Cost_of_Ride", 0) for r in results)
        
        return json.dumps({
            "total_rides": len(results),
            "total_revenue": round(total_revenue, 2),
            "avg_revenue_per_ride": round(total_revenue / len(results), 2) if results else 0,
            "by_time_of_day": by_time,
            "by_location": by_location,
            "by_pricing_model": by_model
        })
    except Exception as e:
        return json.dumps({"error": f"Error querying historical data: {str(e)}"})


@tool
def get_upcoming_events(
    event_type: str = "",
    location: str = "",
    limit: int = 20
) -> str:
    """
    Query actual events data from MongoDB (n8n Eventbrite integration).
    
    Use this tool to find events that may affect future demand.
    Events like concerts, sports games, conferences impact ride demand.
    
    Args:
        event_type: Filter by type (e.g., "concert", "sports"). Empty for all.
        location: Filter by venue/location. Empty for all.
        limit: Maximum records (default: 20)
    
    Returns:
        str: JSON string with upcoming events that affect demand
    """
    try:
        results = query_events_data(
            event_type=event_type,
            location=location,
            limit=limit
        )
        
        if not results:
            return json.dumps({"message": "No events found", "events": [], "count": 0})
        
        # Format events for forecasting context
        formatted_events = []
        for event in results:
            formatted_events.append({
                "name": event.get("name") or event.get("title", "Unknown Event"),
                "date": str(event.get("event_date") or event.get("date", "Unknown")),
                "venue": event.get("venue") or event.get("location", "Unknown"),
                "type": event.get("event_type") or event.get("category", "Unknown"),
                "expected_attendance": event.get("expected_attendance", "Unknown"),
                "demand_impact": event.get("demand_impact", "High")  # Most events = high impact
            })
        
        return json.dumps({
            "count": len(formatted_events),
            "events": formatted_events,
            "summary": f"Found {len(formatted_events)} events that may affect demand"
        })
    except Exception as e:
        return json.dumps({"error": f"Error querying events: {str(e)}"})


@tool
def get_traffic_conditions(
    location: str = "",
    limit: int = 20
) -> str:
    """
    Query actual traffic data from MongoDB (n8n Google Maps integration).
    
    Use this tool to understand current/recent traffic conditions.
    Traffic affects ride duration and surge pricing decisions.
    
    Args:
        location: Filter by location. Empty for all.
        limit: Maximum records (default: 20)
    
    Returns:
        str: JSON string with traffic conditions data
    """
    try:
        results = query_traffic_data(
            location=location,
            limit=limit
        )
        
        if not results:
            return json.dumps({"message": "No traffic data found", "conditions": [], "count": 0})
        
        # Format traffic data
        formatted_traffic = []
        for t in results:
            formatted_traffic.append({
                "location": t.get("location", "Unknown"),
                "timestamp": str(t.get("timestamp", "Unknown")),
                "congestion_level": t.get("congestion_level") or t.get("traffic_level", "Unknown"),
                "average_speed": t.get("average_speed", "Unknown"),
                "delay_minutes": t.get("delay_minutes") or t.get("delay", 0)
            })
        
        return json.dumps({
            "count": len(formatted_traffic),
            "traffic_conditions": formatted_traffic,
            "summary": f"Traffic data for {len(formatted_traffic)} locations"
        })
    except Exception as e:
        return json.dumps({"error": f"Error querying traffic: {str(e)}"})


@tool
def get_industry_news(
    topic: str = "",
    limit: int = 10
) -> str:
    """
    Query actual rideshare news from MongoDB (n8n NewsAPI integration).
    
    Use this tool to understand industry trends that may affect forecasts.
    News about competitors, regulations, or market changes impact demand.
    
    Args:
        topic: Filter by topic/keyword. Empty for all.
        limit: Maximum articles (default: 10)
    
    Returns:
        str: JSON string with industry news
    """
    try:
        results = query_news_data(
            topic=topic,
            limit=limit
        )
        
        if not results:
            return json.dumps({"message": "No news found", "articles": [], "count": 0})
        
        # Format news for context
        formatted_news = []
        for article in results:
            formatted_news.append({
                "title": article.get("title", "No title"),
                "published": str(article.get("published_at") or article.get("date", "Unknown")),
                "source": article.get("source", "Unknown"),
                "summary": (article.get("summary") or article.get("description", ""))[:200]
            })
        
        return json.dumps({
            "count": len(formatted_news),
            "articles": formatted_news,
            "summary": f"Found {len(formatted_news)} relevant industry news articles"
        })
    except Exception as e:
        return json.dumps({"error": f"Error querying news: {str(e)}"})


@tool
def query_event_context(query: str, n_results: int = 5) -> str:
    """
    Query event context from n8n ingested data.
    
    This tool searches for events, traffic data, and news that might
    affect demand forecasts. Use this to understand external factors
    that could impact future demand (events, traffic patterns, industry news).
    
    Args:
        query: Text description to search for (e.g., "Lakers game Friday evening")
        n_results: Number of similar events to retrieve (default: 5)
    
    Returns:
        str: Formatted context string with events and traffic data
    """
    try:
        # Query ChromaDB for similar events/news
        results = query_chromadb("news_events_vectors", query, n_results)
        
        if not results:
            return "No relevant events or traffic data found."
        
        # Extract MongoDB IDs
        mongodb_ids = [r["mongodb_id"] for r in results]
        
        # Fetch full documents from MongoDB
        # Try multiple collections (events_data, traffic_data, news_articles)
        loop = asyncio.get_event_loop()
        documents = []
        
        for collection_name in ["events_data", "traffic_data", "news_articles"]:
            docs = loop.run_until_complete(
                fetch_mongodb_documents(mongodb_ids, collection_name)
            )
            documents.extend(docs)
        
        # Format as context string
        return format_documents_as_context(documents)
    except Exception as e:
        return f"Error querying event context: {str(e)}"


@tool
def generate_multidimensional_forecast(periods: int = 30) -> str:
    """
    Generate comprehensive multi-dimensional demand forecasts across all customer segments.
    
    This tool generates forecasts for all combinations of:
    - Customer_Loyalty_Status (Gold, Silver, Regular)
    - Vehicle_Type (Premium, Economy)
    - Demand_Profile (HIGH, MEDIUM, LOW) - CALCULATED from driver/rider ratio
    - Pricing_Model (CONTRACTED, STANDARD, CUSTOM)
    - Location_Category (Urban, Suburban, Rural)
    
    Note: Time_of_Ride dimension removed - Demand_Profile already captures time-based patterns.
    
    Total possible segments: 3 × 2 × 3 × 3 × 3 = 162 segments
    
    For segments with insufficient data (< 3 historical rides), aggregated forecasts are used.
    
    Args:
        periods: Number of days to forecast (30, 60, or 90). Default: 30.
    
    Returns:
        str: JSON string with segmented forecasts and confidence levels
    """
    
    def calculate_demand_profile(riders: float, drivers: float) -> str:
        """
        Calculate segment_demand_profile from driver/rider ratio.
        
        Logic:
        - HIGH: driver ratio < 34% (low supply, high demand)
        - MEDIUM: driver ratio 34-67%
        - LOW: driver ratio >= 67% (high supply, low demand)
        """
        if riders == 0 or riders is None:
            return "MEDIUM"  # Default if no data
        
        driver_ratio = (drivers / riders) * 100
        
        if driver_ratio < 34:
            return "HIGH"
        elif driver_ratio < 67:
            return "MEDIUM"
        else:
            return "LOW"
    
    try:
        from pymongo import MongoClient
        from app.config import settings
        import pandas as pd
        
        # Connect to MongoDB
        client = MongoClient(settings.mongodb_url)
        db = client[settings.mongodb_db_name]
        hwco_collection = db["historical_rides"]
        
        # Define dimensions (Time_of_Ride removed - Demand_Profile captures time patterns)
        dimensions = {
            "Customer_Loyalty_Status": ["Gold", "Silver", "Regular"],
            "Vehicle_Type": ["Premium", "Economy"],
            "Demand_Profile": ["HIGH", "MEDIUM", "LOW"],
            "Pricing_Model": ["CONTRACTED", "STANDARD", "CUSTOM"],
            "Location_Category": ["Urban", "Suburban", "Rural"]
        }
        
        # Query all historical rides
        all_rides = list(hwco_collection.find({}))
        
        if not all_rides:
            client.close()
            return json.dumps({"error": "No historical data found", "forecasts": []})
        
        segmented_forecasts = []
        aggregated_forecasts = []
        total_possible = 3 * 2 * 3 * 3 * 3  # 162 segments (removed Time_of_Ride)
        
        # Generate forecasts for each segment combination
        for loyalty in dimensions["Customer_Loyalty_Status"]:
            for vehicle in dimensions["Vehicle_Type"]:
                for demand in dimensions["Demand_Profile"]:
                    for pricing in dimensions["Pricing_Model"]:
                        for location in dimensions["Location_Category"]:
                            # Filter rides for this specific segment
                            # Calculate demand_profile dynamically from driver/rider ratio (not from DB field)
                            segment_rides = []
                            for r in all_rides:
                                if (r.get("Customer_Loyalty_Status") == loyalty
                                    and r.get("Vehicle_Type") == vehicle
                                    and r.get("Pricing_Model") == pricing
                                    and r.get("Location_Category") == location):
                                    # Calculate demand_profile for this ride
                                    riders = r.get("Number_Of_Riders", 0)
                                    drivers = r.get("Number_of_Drivers", 0)
                                    ride_demand_profile = calculate_demand_profile(riders, drivers)
                                    
                                    # Check if it matches target demand profile
                                    if ride_demand_profile == demand:
                                        segment_rides.append(r)
                            
                            ride_count = len(segment_rides)
                            
                            if ride_count >= 3:
                                # Sufficient data for segment-specific forecast
                                # Build segment dimensions
                                segment_dims = {
                                    "loyalty_tier": loyalty,
                                    "vehicle_type": vehicle,
                                    "demand_profile": demand,
                                    "pricing_model": pricing,
                                    "location": location
                                }
                                
                                # Calculate historical averages with NEW duration/unit_price model
                                total_price = sum(r.get("Historical_Cost_of_Ride", 0) for r in segment_rides)
                                total_duration = sum(r.get("Expected_Ride_Duration", 0) for r in segment_rides)
                                total_riders = sum(r.get("Number_Of_Riders", 0) for r in segment_rides)
                                total_drivers = sum(r.get("Number_of_Drivers", 0) for r in segment_rides)
                                
                                avg_price = total_price / ride_count
                                avg_duration = total_duration / ride_count if total_duration > 0 else 20.0  # default 20 min
                                avg_unit_price = (avg_price / avg_duration) if avg_duration > 0 else (avg_price / 20.0)
                                avg_riders = total_riders / ride_count if total_riders > 0 else 1.0
                                avg_drivers = total_drivers / ride_count if total_drivers > 0 else 0.5
                                
                                # Calculate segment_demand_profile from averages
                                segment_demand_profile = calculate_demand_profile(avg_riders, avg_drivers)
                                
                                total_revenue = total_price
                                
                                # Use forecasting helpers (extensible to Prophet ML)
                                try:
                                    # Forecast demand using helper function (method='simple', future: 'prophet')
                                    demand_forecast = forecast_demand_for_segment(
                                        segment_dims,
                                        segment_rides,
                                        periods=periods,
                                        method='simple'  # Change to 'prophet' when Prophet ML is added
                                    )
                                    
                                    # Forecast price using PricingEngine (method='pricing_engine', future: 'prophet')
                                    price_forecast = forecast_price_for_segment(
                                        segment_dims,
                                        segment_rides,
                                        periods=periods,
                                        method='pricing_engine',  # Change to 'prophet' when Prophet ML is added
                                        pricing_engine=pricing_engine
                                    )
                                    
                                    # Calculate revenue forecast
                                    revenue_forecast = calculate_revenue_forecast(
                                        demand_forecast,
                                        price_forecast,
                                        periods=periods
                                    )
                                    
                                    # Prepare historical data for future Prophet ML (not used now, but ready)
                                    prophet_data_demand = prepare_historical_data_for_prophet(
                                        segment_dims,
                                        segment_rides,
                                        data_type='demand'
                                    )
                                    prophet_data_price = prepare_historical_data_for_prophet(
                                        segment_dims,
                                        segment_rides,
                                        data_type='price'
                                    )
                                    
                                    # Use PricingEngine price (or fallback to historical average)
                                    pricing_engine_price = price_forecast.get("predicted_price_30d", avg_price)
                                    
                                except Exception as e:
                                    logger.warning(f"Error using forecasting helpers for segment {segment_dims}, falling back to simple: {e}")
                                    # Fallback to simple calculation
                                    growth_rate = 0.015 if demand == "HIGH" else 0.01 if demand == "MEDIUM" else 0.005
                                    forecast_30d = ride_count * (1 + growth_rate * 1)
                                    forecast_60d = ride_count * (1 + growth_rate * 2)
                                    forecast_90d = ride_count * (1 + growth_rate * 3)
                                    demand_forecast = {
                                        "predicted_rides_30d": forecast_30d,
                                        "predicted_rides_60d": forecast_60d,
                                        "predicted_rides_90d": forecast_90d,
                                        "confidence": "high" if ride_count >= 10 else "medium",
                                        "method": "simple_fallback"
                                    }
                                    revenue_forecast = {
                                        "predicted_revenue_30d": forecast_30d * avg_price,
                                        "predicted_revenue_60d": forecast_60d * avg_price,
                                        "predicted_revenue_90d": forecast_90d * avg_price
                                    }
                                    pricing_engine_price = avg_price
                                
                                confidence = demand_forecast.get("confidence", "medium")
                                
                                # Build forecast output with NEW structure (duration/unit_price model)
                                segmented_forecasts.append({
                                    "dimensions": segment_dims,
                                    "baseline_metrics": {
                                        "historical_ride_count": ride_count,
                                        "segment_avg_fcs_unit_price": round(avg_unit_price, 4),  # NEW: price per minute
                                        "segment_avg_fcs_ride_duration": round(avg_duration, 2),  # NEW: duration in minutes
                                        "segment_avg_riders_per_order": round(avg_riders, 2),  # NEW: riders
                                        "segment_avg_drivers_per_order": round(avg_drivers, 2),  # NEW: drivers
                                        "segment_demand_profile": segment_demand_profile,  # NEW: calculated demand profile
                                        "total_revenue": round(total_revenue, 2),
                                        "avg_monthly_demand": round(ride_count / 3, 2)  # Assuming 3 months of data
                                    },
                                    "forecast_30d": {
                                        "predicted_rides": round(demand_forecast.get("predicted_rides_30d", 0), 2),
                                        "predicted_unit_price": round(avg_unit_price, 4),  # Use historical avg for now
                                        "predicted_ride_duration": round(avg_duration, 2),  # Use historical avg for now
                                        "predicted_revenue": round(revenue_forecast.get("predicted_revenue_30d", 0), 2),
                                        "segment_demand_profile": segment_demand_profile
                                    },
                                    "forecast_60d": {
                                        "predicted_rides": round(demand_forecast.get("predicted_rides_60d", 0), 2),
                                        "predicted_unit_price": round(avg_unit_price, 4),
                                        "predicted_ride_duration": round(avg_duration, 2),
                                        "predicted_revenue": round(revenue_forecast.get("predicted_revenue_60d", 0), 2),
                                        "segment_demand_profile": segment_demand_profile
                                    },
                                    "forecast_90d": {
                                        "predicted_rides": round(demand_forecast.get("predicted_rides_90d", 0), 2),
                                        "predicted_unit_price": round(avg_unit_price, 4),
                                        "predicted_ride_duration": round(avg_duration, 2),
                                        "predicted_revenue": round(revenue_forecast.get("predicted_revenue_90d", 0), 2),
                                        "segment_demand_profile": segment_demand_profile
                                    },
                                    "confidence": confidence,
                                    "data_quality": "sufficient",
                                    "forecast_method": demand_forecast.get("method", "simple")  # Track method used
                                })
                            
                            elif ride_count > 0:
                                # Sparse data - use aggregated forecast
                                # Aggregate to broader segment (location + vehicle only)
                                aggregated_rides = [
                                    r for r in all_rides
                                    if r.get("Location_Category") == location
                                    and r.get("Vehicle_Type") == vehicle
                                ]
                                
                                if len(aggregated_rides) >= 3:
                                    agg_count = len(aggregated_rides)
                                    
                                    # Calculate aggregated metrics with NEW model
                                    agg_total_price = sum(r.get("Historical_Cost_of_Ride", 0) for r in aggregated_rides)
                                    agg_total_duration = sum(r.get("Expected_Ride_Duration", 0) for r in aggregated_rides)
                                    agg_total_riders = sum(r.get("Number_Of_Riders", 0) for r in aggregated_rides)
                                    agg_total_drivers = sum(r.get("Number_of_Drivers", 0) for r in aggregated_rides)
                                    
                                    agg_avg_price = agg_total_price / agg_count
                                    agg_avg_duration = agg_total_duration / agg_count if agg_total_duration > 0 else 20.0
                                    agg_avg_unit_price = (agg_avg_price / agg_avg_duration) if agg_avg_duration > 0 else (agg_avg_price / 20.0)
                                    agg_avg_riders = agg_total_riders / agg_count if agg_total_riders > 0 else 1.0
                                    agg_avg_drivers = agg_total_drivers / agg_count if agg_total_drivers > 0 else 0.5
                                    agg_demand_profile = calculate_demand_profile(agg_avg_riders, agg_avg_drivers)
                                    
                                    # Build segment dimensions for aggregated forecast
                                    segment_dims = {
                                        "loyalty_tier": loyalty,
                                        "vehicle_type": vehicle,
                                        "demand_profile": demand,
                                        "pricing_model": pricing,
                                        "location": location
                                    }
                                    
                                    # Use forecasting helpers with aggregated data
                                    try:
                                        demand_forecast = forecast_demand_for_segment(
                                            segment_dims,
                                            aggregated_rides,  # Use aggregated rides
                                            periods=periods,
                                            method='simple'
                                        )
                                        
                                        price_forecast = forecast_price_for_segment(
                                            segment_dims,
                                            aggregated_rides,  # Use aggregated rides
                                            periods=periods,
                                            method='pricing_engine',
                                            pricing_engine=pricing_engine
                                        )
                                        
                                        revenue_forecast = calculate_revenue_forecast(
                                            demand_forecast,
                                            price_forecast,
                                            periods=periods
                                        )
                                        
                                        # Scale down based on segment proportion
                                        proportion = ride_count / agg_count if agg_count > 0 else 0.1
                                        
                                        forecast_30d = demand_forecast.get("predicted_rides_30d", 0) * proportion
                                        forecast_60d = demand_forecast.get("predicted_rides_60d", 0) * proportion
                                        forecast_90d = demand_forecast.get("predicted_rides_90d", 0) * proportion
                                        
                                        pricing_engine_price = price_forecast.get("predicted_price_30d", avg_price)
                                        
                                    except Exception as e:
                                        logger.warning(f"Error using forecasting helpers for aggregated segment, falling back: {e}")
                                        # Fallback to simple calculation
                                        proportion = ride_count / agg_count if agg_count > 0 else 0.1
                                        forecast_30d = agg_count * proportion * 1.01
                                        forecast_60d = agg_count * proportion * 1.02
                                        forecast_90d = agg_count * proportion * 1.03
                                        revenue_forecast = {
                                            "predicted_revenue_30d": forecast_30d * agg_avg_duration * agg_avg_unit_price,
                                            "predicted_revenue_60d": forecast_60d * agg_avg_duration * agg_avg_unit_price,
                                            "predicted_revenue_90d": forecast_90d * agg_avg_duration * agg_avg_unit_price
                                        }
                                    
                                    # Build aggregated forecast with NEW structure
                                    aggregated_forecasts.append({
                                        "dimensions": segment_dims,
                                        "baseline_metrics": {
                                            "historical_ride_count": ride_count,
                                            "aggregated_from_count": agg_count,
                                            "segment_avg_fcs_unit_price": round(agg_avg_unit_price, 4),
                                            "segment_avg_fcs_ride_duration": round(agg_avg_duration, 2),
                                            "segment_avg_riders_per_order": round(agg_avg_riders, 2),
                                            "segment_avg_drivers_per_order": round(agg_avg_drivers, 2),
                                            "segment_demand_profile": agg_demand_profile,
                                            "proportion": round(proportion, 3)
                                        },
                                        "forecast_30d": {
                                            "predicted_rides": round(forecast_30d, 2),
                                            "predicted_unit_price": round(agg_avg_unit_price, 4),
                                            "predicted_ride_duration": round(agg_avg_duration, 2),
                                            "predicted_revenue": round(revenue_forecast.get("predicted_revenue_30d", forecast_30d * agg_avg_duration * agg_avg_unit_price), 2),
                                            "segment_demand_profile": agg_demand_profile
                                        },
                                        "forecast_60d": {
                                            "predicted_rides": round(forecast_60d, 2),
                                            "predicted_unit_price": round(agg_avg_unit_price, 4),
                                            "predicted_ride_duration": round(agg_avg_duration, 2),
                                            "predicted_revenue": round(revenue_forecast.get("predicted_revenue_60d", forecast_60d * agg_avg_duration * agg_avg_unit_price), 2),
                                            "segment_demand_profile": agg_demand_profile
                                        },
                                        "forecast_90d": {
                                            "predicted_rides": round(forecast_90d, 2),
                                            "predicted_unit_price": round(agg_avg_unit_price, 4),
                                            "predicted_ride_duration": round(agg_avg_duration, 2),
                                            "predicted_revenue": round(revenue_forecast.get("predicted_revenue_90d", forecast_90d * agg_avg_duration * agg_avg_unit_price), 2),
                                            "segment_demand_profile": agg_demand_profile
                                        },
                                        "confidence": "low",
                                        "data_quality": "aggregated",
                                        "forecast_method": "simple_aggregated"
                                    })
        
        client.close()
        
        # Calculate summary statistics
        total_forecasts = len(segmented_forecasts) + len(aggregated_forecasts)
        confidence_distribution = {
            "high": sum(1 for f in segmented_forecasts if f["confidence"] == "high"),
            "medium": sum(1 for f in segmented_forecasts if f["confidence"] == "medium"),
            "low": len(aggregated_forecasts)
        }
        
        # Calculate totals
        total_baseline_revenue = sum(f["baseline_metrics"]["total_revenue"] for f in segmented_forecasts)
        total_30d_revenue = sum(f["forecast_30d"]["predicted_revenue"] for f in segmented_forecasts + aggregated_forecasts)
        total_60d_revenue = sum(f["forecast_60d"]["predicted_revenue"] for f in segmented_forecasts + aggregated_forecasts)
        total_90d_revenue = sum(f["forecast_90d"]["predicted_revenue"] for f in segmented_forecasts + aggregated_forecasts)
        
        result = {
            "summary": {
                "total_possible_segments": total_possible,
                "forecasted_segments": len(segmented_forecasts),
                "aggregated_segments": len(aggregated_forecasts),
                "total_forecasts": total_forecasts,
                "confidence_distribution": confidence_distribution,
                "total_baseline_revenue": round(total_baseline_revenue, 2),
                "total_30d_forecast_revenue": round(total_30d_revenue, 2),
                "total_60d_forecast_revenue": round(total_60d_revenue, 2),
                "total_90d_forecast_revenue": round(total_90d_revenue, 2),
                "revenue_growth_30d_pct": round((total_30d_revenue - total_baseline_revenue) / total_baseline_revenue * 100, 2) if total_baseline_revenue > 0 else 0
            },
            "segmented_forecasts": segmented_forecasts,  # Return ALL segments (removed [:50] limit)
            "aggregated_forecasts": aggregated_forecasts,  # Return ALL aggregated forecasts
            "note": "All forecast data included - 162 segments expected"
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Error generating multi-dimensional forecast: {str(e)}"})


@tool
def generate_prophet_forecast(pricing_model: str, periods: int) -> Dict[str, Any]:
    """
    Generate Prophet ML forecast for specified pricing model and period.
    
    This tool uses the trained Prophet ML model to generate demand forecasts.
    The model predicts future demand based on historical patterns and pricing type.
    
    Args:
        pricing_model: One of "CONTRACTED", "STANDARD", or "CUSTOM"
        periods: Number of days to forecast (30, 60, or 90)
    
    Returns:
        dict: Forecast data with:
            - forecast: List of forecast points with date, predicted_demand, confidence intervals
            - model: "prophet_ml"
            - pricing_model: The pricing model forecasted
            - periods: Number of days forecasted
            - explanation: Natural language explanation (added by explain_forecast)
            - context: Events and traffic patterns (added by explain_forecast)
    """
    try:
        # Generate forecast using Prophet ML model
        # Run in thread pool to avoid blocking (Prophet is synchronous)
        loop = asyncio.get_event_loop()
        forecast_df = loop.run_in_executor(
            None,
            forecast_model.forecast,
            pricing_model,
            periods
        )
        
        # Wait for the result
        forecast_df = loop.run_until_complete(forecast_df)
        
        if forecast_df is None:
            return {
                "error": "Forecast generation failed. Ensure model is trained first.",
                "forecast": []
            }
        
        # Convert DataFrame to list of dictionaries
        forecast_list = forecast_df.to_dict("records")
        
        # Format dates as ISO strings and ensure proper field names
        formatted_forecast = []
        for item in forecast_list:
            formatted_item = {}
            # Map Prophet output fields to expected format
            if "ds" in item:
                date_val = item["ds"]
                formatted_item["date"] = date_val.isoformat() if hasattr(date_val, "isoformat") else str(date_val)
            if "yhat" in item:
                formatted_item["predicted_demand"] = item["yhat"]
            if "yhat_lower" in item:
                formatted_item["confidence_lower"] = item["yhat_lower"]
            if "yhat_upper" in item:
                formatted_item["confidence_upper"] = item["yhat_upper"]
            if "trend" in item:
                formatted_item["trend"] = item["trend"]
            formatted_forecast.append(formatted_item)
        
        return {
            "forecast": formatted_forecast,
            "model": "prophet_ml",
            "pricing_model": pricing_model,
            "periods": periods,
            "confidence": 0.80
        }
    except Exception as e:
        return {
            "error": f"Error generating forecast: {str(e)}",
            "forecast": []
        }


@tool
def explain_forecast(forecast_data: Dict[str, Any], event_context: Any) -> Dict[str, Any]:
    """
    Explain forecast in natural language using OpenAI GPT-4.
    
    This tool takes forecast data and event context, then uses OpenAI GPT-4
    to generate a natural language explanation of the forecast with trend analysis.
    
    Args:
        forecast_data: Forecast data dictionary from generate_prophet_forecast
        event_context: Context string from query_event_context
    
    Returns:
        str: Natural language explanation of the forecast
    """
    try:
        from openai import OpenAI
        
        if "error" in forecast_data:
            return {
                "forecast": [],
                "explanation": f"Forecast error: {forecast_data.get('error')}",
                "method": "prophet_ml",
                "context": {"events_detected": [], "traffic_patterns": []}
            }
        
        pricing_model = forecast_data.get("pricing_model", "UNKNOWN")
        periods = forecast_data.get("periods", 0)
        forecast_points = forecast_data.get("forecast", [])
        
        if not forecast_points:
            return {
                "forecast": [],
                "explanation": "No forecast data available.",
                "method": "prophet_ml",
                "context": {"events_detected": [], "traffic_patterns": []}
            }
        
        if not settings.OPENAI_API_KEY:
            # Fallback to basic explanation if API key not available
            avg_demand = sum(p.get("predicted_demand", 0) for p in forecast_points) / len(forecast_points) if forecast_points else 0
            return {
                "forecast": forecast_points,
                "explanation": (
                    f"Prophet ML forecast for {pricing_model} pricing over {periods} days: "
                    f"Average predicted demand: {avg_demand:.2f} rides/day."
                ),
                "method": "prophet_ml",
                "context": {"events_detected": [], "traffic_patterns": []}
            }
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Calculate trend indicators
        if len(forecast_points) >= 2:
            first_half = forecast_points[:len(forecast_points)//2]
            second_half = forecast_points[len(forecast_points)//2:]
            first_avg = sum(p.get("predicted_demand", 0) for p in first_half) / len(first_half)
            second_avg = sum(p.get("predicted_demand", 0) for p in second_half) / len(second_half)
            trend = "increasing" if second_avg > first_avg * 1.05 else "decreasing" if second_avg < first_avg * 0.95 else "stable"
        else:
            trend = "stable"
        
        avg_demand = sum(p.get("predicted_demand", 0) for p in forecast_points) / len(forecast_points)
        min_demand = min(p.get("predicted_demand", 0) for p in forecast_points)
        max_demand = max(p.get("predicted_demand", 0) for p in forecast_points)
        
        # Extract events and traffic patterns from context
        # event_context can be a dict (from query_event_context) or a string (legacy)
        events_detected = []
        traffic_patterns = []
        context_string = ""
        
        if isinstance(event_context, dict):
            # New format: dict with context_string, events_detected, traffic_patterns
            context_string = event_context.get("context_string", "")
            events_detected = event_context.get("events_detected", [])
            traffic_patterns = event_context.get("traffic_patterns", [])
        elif isinstance(event_context, str):
            # Legacy format: just a string
            context_string = event_context
            if event_context and event_context != "No relevant events or traffic data found.":
                # Simple extraction (can be enhanced)
                if "event" in event_context.lower() or "game" in event_context.lower():
                    events_detected.append("Events detected in forecast period")
                if "traffic" in event_context.lower() or "congestion" in event_context.lower():
                    traffic_patterns.append("Traffic patterns identified")
        
        prompt = f"""
        Explain this Prophet ML demand forecast in natural language for a business analytics dashboard.
        
        Forecast Details:
        - Pricing Model: {pricing_model}
        - Forecast Period: {periods} days
        - Average Predicted Demand: {avg_demand:.2f} rides/day
        - Minimum Demand: {min_demand:.2f} rides/day
        - Maximum Demand: {max_demand:.2f} rides/day
        - Trend: {trend}
        - Confidence Interval: 80%
        
        External Context (from n8n ingested data):
        {context_string[:500] if context_string else "No external events or traffic data available"}
        
        Events Detected: {', '.join(events_detected) if events_detected else "None"}
        Traffic Patterns: {', '.join(traffic_patterns) if traffic_patterns else "None"}
        
        Provide a clear, business-focused explanation that:
        1. Explains the forecasted demand trend
        2. Describes confidence intervals and uncertainty
        3. Incorporates external events and traffic patterns (if available)
        4. Highlights key insights for business decision-making
        5. Is concise but informative (3-4 sentences)
        
        Write in a professional, analytical tone suitable for business stakeholders.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400
        )
        
        explanation_text = response.choices[0].message.content.strip()
        
        # Return exact format as specified
        return {
            "forecast": forecast_data.get("forecast", []),
            "explanation": explanation_text,
            "method": "prophet_ml",
            "context": {
                "events_detected": events_detected,
                "traffic_patterns": traffic_patterns
            }
        }
        
    except Exception as e:
        # Fallback to basic explanation on error
        pricing_model = forecast_data.get("pricing_model", "UNKNOWN")
        periods = forecast_data.get("periods", 0)
        forecast_points = forecast_data.get("forecast", [])
        avg_demand = sum(p.get("predicted_demand", 0) for p in forecast_points) / len(forecast_points) if forecast_points else 0
        
        return {
            "forecast": forecast_points,
            "explanation": (
                f"Prophet ML forecast for {pricing_model} pricing over {periods} days: "
                f"Average predicted demand: {avg_demand:.2f} rides/day. "
                f"Error generating detailed explanation: {str(e)[:100]}"
            ),
            "method": "prophet_ml",
            "context": {
                "events_detected": [],
                "traffic_patterns": []
            }
        }


# Create the forecasting agent
# Handle missing API key gracefully (for testing environments)
try:
    forecasting_agent = create_agent(
        model="openai:gpt-4o-mini",
        tools=[
            # Multi-dimensional forecasting (NEW)
            generate_multidimensional_forecast,
            # MongoDB direct query tools (for ACTUAL data)
            get_historical_demand_data,
            get_upcoming_events,
            get_traffic_conditions,
            get_industry_news,
            # ChromaDB RAG tools (for similar scenarios)
            query_event_context,
            # ML forecasting tools
            generate_prophet_forecast,
            explain_forecast
        ],
        system_prompt=(
            "You are a forecasting specialist predicting future demand using ML models and external data.\n\n"
            
            "🎯 TOOL SELECTION:\n"
            "• Multi-dimensional → generate_multidimensional_forecast (648 segments)\n"
            "• Historical patterns → get_historical_demand_data\n"
            "• Upcoming events → get_upcoming_events\n"
            "• Traffic → get_traffic_conditions\n"
            "• Industry news → get_industry_news\n"
            "• Single forecast → generate_prophet_forecast\n\n"
            
            "📋 RESPONSE FORMAT (STRICTLY FOLLOW):\n"
            "• Use ## (two hashes) for headers with emojis\n"
            "• Use bullet points (•) for ALL findings\n"
            "• Keep under 120 words\n"
            "• Bold key metrics: **+25% demand**, **95% confidence**\n"
            "• Show trend direction clearly\n\n"
            
            "✅ CORRECT:\n"
            "## 📈 30-Day Forecast\n"
            "• Demand: **+15%** vs baseline\n"
            "• Confidence: **95%**\n"
            "• Peak days: **Fri-Sun**\n"
            "• Driver: **Holiday events** (+20%)\n"
        ),
        name="forecasting_agent"
    )
except Exception as e:
    # If API key is missing, set to None (for testing environments)
    if "api_key" in str(e).lower() or "openai" in str(e).lower():
        forecasting_agent = None
    else:
        # Re-raise if it's not an API key issue
        raise
except Exception as e:
    # If API key is missing, set to None (for testing environments)
    if "api_key" in str(e).lower() or "openai" in str(e).lower():
        forecasting_agent = None
    else:
        # Re-raise if it's not an API key issue
        raise


