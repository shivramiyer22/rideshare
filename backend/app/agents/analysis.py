"""
Analysis Agent - Performs data analysis and insights generation.

This agent analyzes business data to provide insights about:
- Revenue, profit, and KPIs
- Customer segments and behavior
- Ride patterns and trends
- n8n ingested data (events, traffic, news)

The agent uses RAG (Retrieval-Augmented Generation):
1. Query ChromaDB for similar past scenarios
2. Fetch full documents from MongoDB (using sync PyMongo)
3. Analyze the data using OpenAI GPT-4
4. Generate actionable insights

REFACTORED: Uses synchronous PyMongo for reliable database access
from LangChain tools (which run in sync context).
"""
from langchain.agents import create_agent
from langchain.tools import tool
from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timedelta
import pymongo
from app.config import settings
from app.agents.utils import (
    query_chromadb, 
    format_documents_as_context,
    query_events_data,
    query_traffic_data,
    query_news_data
)
import logging

logger = logging.getLogger(__name__)


def get_sync_mongodb_client():
    """Get a synchronous MongoDB client for use in LangChain tools."""
    return pymongo.MongoClient(settings.mongodb_url)


def get_sync_collection(collection_name: str):
    """Get a synchronous MongoDB collection."""
    client = get_sync_mongodb_client()
    db = client[settings.mongodb_db_name]
    return client, db[collection_name]


@tool
def query_ride_scenarios(query: str, n_results: int = 5) -> str:
    """
    Query past ride scenarios for pattern analysis.
    
    This tool searches ChromaDB for similar past rides, then fetches
    full details from MongoDB. Use this to analyze ride patterns,
    pricing trends, and customer behavior.
    
    Args:
        query: Text description to search for (e.g., "urban evening rush premium")
        n_results: Number of similar scenarios to retrieve (default: 5)
    
    Returns:
        str: Formatted context string with past ride scenarios
    """
    try:
        # Query ChromaDB for similar scenarios
        results = query_chromadb("ride_scenarios_vectors", query, n_results)
        
        if not results:
            return "No similar ride scenarios found in ChromaDB."
        
        # Extract MongoDB IDs
        mongodb_ids = [r.get("mongodb_id") for r in results if r.get("mongodb_id")]
        
        if not mongodb_ids:
            return "No MongoDB IDs found in ChromaDB results."
        
        # Fetch from MongoDB using sync client
        client, collection = get_sync_collection("historical_rides")
        try:
            documents = list(collection.find({"_id": {"$in": mongodb_ids}}).limit(n_results))
            if not documents:
                # Try ride_orders collection
                collection = client[settings.mongodb_db_name]["ride_orders"]
                documents = list(collection.find({"_id": {"$in": mongodb_ids}}).limit(n_results))
        finally:
            client.close()
        
        return format_documents_as_context(documents)
    except Exception as e:
        return f"Error querying ride scenarios: {str(e)}"


@tool
def query_news_events(query: str, n_results: int = 5) -> str:
    """
    Query news and events from n8n ingested data.
    
    This tool searches for events, traffic data, and news articles
    that were ingested by n8n workflows. Use this to understand
    external factors affecting demand (events, traffic, industry news).
    
    Args:
        query: Text description to search for (e.g., "Lakers game Friday evening")
        n_results: Number of similar events to retrieve (default: 5)
    
    Returns:
        str: Formatted context string with events and news
    """
    try:
        # Query ChromaDB for similar events/news
        results = query_chromadb("news_events_vectors", query, n_results)
        
        if not results:
            return "No similar events or news found."
        
        # Extract MongoDB IDs
        mongodb_ids = [r.get("mongodb_id") for r in results if r.get("mongodb_id")]
        
        if not mongodb_ids:
            return "No MongoDB IDs found in ChromaDB results."
        
        # Fetch from multiple collections
        client = get_sync_mongodb_client()
        db = client[settings.mongodb_db_name]
        documents = []
        
        try:
            for collection_name in ["events_data", "traffic_data", "news_articles"]:
                collection = db[collection_name]
                docs = list(collection.find({"_id": {"$in": mongodb_ids}}).limit(n_results))
                documents.extend(docs)
        finally:
            client.close()
        
        return format_documents_as_context(documents)
    except Exception as e:
        return f"Error querying news/events: {str(e)}"


@tool
def query_customer_behavior(query: str, n_results: int = 5) -> str:
    """
    Query customer behavior patterns.
    
    This tool searches for customer behavioral patterns to understand
    customer segments, loyalty tiers, and usage patterns.
    
    Args:
        query: Text description to search for (e.g., "Gold tier customer patterns")
        n_results: Number of similar patterns to retrieve (default: 5)
    
    Returns:
        str: Formatted context string with customer behavior data
    """
    try:
        # Query ChromaDB for customer behavior patterns
        results = query_chromadb("customer_behavior_vectors", query, n_results)
        
        if not results:
            return "No customer behavior patterns found."
        
        # Extract MongoDB IDs
        mongodb_ids = [r.get("mongodb_id") for r in results if r.get("mongodb_id")]
        
        if not mongodb_ids:
            return "No MongoDB IDs found in ChromaDB results."
        
        # Fetch from MongoDB
        client, collection = get_sync_collection("customers")
        try:
            documents = list(collection.find({"_id": {"$in": mongodb_ids}}).limit(n_results))
        finally:
            client.close()
        
        return format_documents_as_context(documents)
    except Exception as e:
        return f"Error querying customer behavior: {str(e)}"


@tool
def query_competitor_data(query: str, n_results: int = 5) -> str:
    """
    Query competitor pricing data.
    
    This tool searches for competitor pricing information to understand
    market positioning and competitive landscape.
    
    Args:
        query: Text description to search for (e.g., "competitor pricing downtown")
        n_results: Number of similar records to retrieve (default: 5)
    
    Returns:
        str: Formatted context string with competitor pricing data
    """
    try:
        # Query ChromaDB for competitor data
        results = query_chromadb("competitor_analysis_vectors", query, n_results)
        
        if not results:
            return "No competitor data found."
        
        # Extract MongoDB IDs
        mongodb_ids = [r.get("mongodb_id") for r in results if r.get("mongodb_id")]
        
        if not mongodb_ids:
            return "No MongoDB IDs found in ChromaDB results."
        
        # Fetch from MongoDB
        client, collection = get_sync_collection("competitor_prices")
        try:
            documents = list(collection.find({"_id": {"$in": mongodb_ids}}).limit(n_results))
        finally:
            client.close()
        
        return format_documents_as_context(documents)
    except Exception as e:
        return f"Error querying competitor data: {str(e)}"


@tool
def calculate_revenue_kpis(time_period: str = "30d") -> str:
    """
    Calculate revenue KPIs for specified time period.
    
    Calculates:
    - Total revenue
    - Average revenue per ride
    - Revenue growth (compared to previous period)
    
    Args:
        time_period: Time period for analysis ("7d", "30d", "90d")
    
    Returns:
        str: JSON string with revenue KPIs
    """
    try:
        client = get_sync_mongodb_client()
        db = client[settings.mongodb_db_name]
        
        # Calculate date range
        end_date = datetime.utcnow()
        if time_period == "7d":
            start_date = end_date - timedelta(days=7)
            prev_start_date = start_date - timedelta(days=7)
        elif time_period == "30d":
            start_date = end_date - timedelta(days=30)
            prev_start_date = start_date - timedelta(days=30)
        elif time_period == "90d":
            start_date = end_date - timedelta(days=90)
            prev_start_date = start_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
            prev_start_date = start_date - timedelta(days=30)
        
        try:
            # Try historical_rides first (new format)
            collection = db["historical_rides"]
            count = collection.count_documents({})
            
            if count > 0:
                # Use historical_rides with new field names
                current_orders = list(collection.find({
                    "Order_Date": {"$gte": start_date, "$lte": end_date}
                }))
                prev_orders = list(collection.find({
                    "Order_Date": {"$gte": prev_start_date, "$lt": start_date}
                }))
                
                # Calculate revenue using Historical_Cost_of_Ride
                total_revenue = sum(
                    order.get("Historical_Cost_of_Ride", 0) 
                    for order in current_orders
                )
                prev_revenue = sum(
                    order.get("Historical_Cost_of_Ride", 0) 
                    for order in prev_orders
                )
            else:
                # Fallback to ride_orders
                collection = db["ride_orders"]
                current_orders = list(collection.find({
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }))
                prev_orders = list(collection.find({
                    "created_at": {"$gte": prev_start_date, "$lt": start_date}
                }))
                
                total_revenue = sum(
                    order.get("final_price", order.get("price", 0)) 
                    for order in current_orders
                )
                prev_revenue = sum(
                    order.get("final_price", order.get("price", 0)) 
                    for order in prev_orders
                )
        finally:
            client.close()
        
        # Calculate metrics
        ride_count = len(current_orders)
        avg_revenue_per_ride = total_revenue / ride_count if ride_count > 0 else 0
        
        revenue_growth = 0.0
        if prev_revenue > 0:
            revenue_growth = ((total_revenue - prev_revenue) / prev_revenue) * 100
        
        return json.dumps({
            "total_revenue": round(total_revenue, 2),
            "average_revenue_per_ride": round(avg_revenue_per_ride, 2),
            "revenue_growth_percent": round(revenue_growth, 2),
            "ride_count": ride_count,
            "time_period": time_period
        })
    except Exception as e:
        return json.dumps({"error": f"Error calculating revenue KPIs: {str(e)}"})


@tool
def calculate_profit_metrics(time_period: str = "30d") -> str:
    """
    Calculate profit metrics for specified time period.
    
    Note: Profit calculation requires cost data. If cost data is not available,
    this will estimate based on industry averages or return revenue as proxy.
    
    Args:
        time_period: Time period for analysis ("7d", "30d", "90d")
    
    Returns:
        str: JSON string with profit metrics
    """
    try:
        client = get_sync_mongodb_client()
        db = client[settings.mongodb_db_name]
        
        # Calculate date range
        end_date = datetime.utcnow()
        if time_period == "7d":
            start_date = end_date - timedelta(days=7)
        elif time_period == "30d":
            start_date = end_date - timedelta(days=30)
        elif time_period == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
        
        try:
            # Try historical_rides first
            collection = db["historical_rides"]
            count = collection.count_documents({})
            
            if count > 0:
                orders = list(collection.find({
                    "Order_Date": {"$gte": start_date, "$lte": end_date}
                }))
                total_revenue = sum(order.get("Historical_Cost_of_Ride", 0) for order in orders)
            else:
                collection = db["ride_orders"]
                orders = list(collection.find({
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }))
                total_revenue = sum(
                    order.get("final_price", order.get("price", 0)) 
                    for order in orders
                )
        finally:
            client.close()
        
        # Estimate costs (60% of revenue as industry estimate)
        estimated_costs = total_revenue * 0.60
        profit = total_revenue - estimated_costs
        profit_margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
        
        return json.dumps({
            "total_revenue": round(total_revenue, 2),
            "estimated_costs": round(estimated_costs, 2),
            "profit": round(profit, 2),
            "profit_margin_percent": round(profit_margin, 2),
            "time_period": time_period,
            "note": "Costs are estimated (60% of revenue). Actual cost data needed for precise calculation."
        })
    except Exception as e:
        return json.dumps({"error": f"Error calculating profit metrics: {str(e)}"})


@tool
def calculate_rides_count(time_period: str = "30d") -> str:
    """
    Calculate ride counts by pricing model for specified time period.
    
    Args:
        time_period: Time period for analysis ("7d", "30d", "90d")
    
    Returns:
        str: JSON string with ride counts by pricing model
    """
    try:
        client = get_sync_mongodb_client()
        db = client[settings.mongodb_db_name]
        
        # Calculate date range
        end_date = datetime.utcnow()
        if time_period == "7d":
            start_date = end_date - timedelta(days=7)
        elif time_period == "30d":
            start_date = end_date - timedelta(days=30)
        elif time_period == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
        
        try:
            # Try historical_rides first
            collection = db["historical_rides"]
            count = collection.count_documents({})
            
            if count > 0:
                orders = list(collection.find({
                    "Order_Date": {"$gte": start_date, "$lte": end_date}
                }))
                pricing_field = "Pricing_Model"
            else:
                collection = db["ride_orders"]
                orders = list(collection.find({
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }))
                pricing_field = "pricing_model"
        finally:
            client.close()
        
        # Count by pricing model
        contracted_count = sum(1 for o in orders if o.get(pricing_field) == "CONTRACTED")
        standard_count = sum(1 for o in orders if o.get(pricing_field) == "STANDARD")
        custom_count = sum(1 for o in orders if o.get(pricing_field) == "CUSTOM")
        total_count = len(orders)
        
        return json.dumps({
            "total_rides": total_count,
            "contracted_rides": contracted_count,
            "standard_rides": standard_count,
            "custom_rides": custom_count,
            "time_period": time_period
        })
    except Exception as e:
        return json.dumps({"error": f"Error calculating ride counts: {str(e)}"})


@tool
def get_top_revenue_rides(month: str = "", year: str = "", limit: int = 10) -> str:
    """
    Get top rides by revenue from historical data.
    
    Queries the historical_rides collection to find rides with highest revenue.
    Can filter by month and year.
    
    Args:
        month: Month name (e.g., "November", "January") or number (1-12). Leave empty for all months.
        year: Year (e.g., "2024"). Leave empty for all years.
        limit: Number of top rides to return (default: 10)
    
    Returns:
        str: JSON string with top revenue rides
    """
    try:
        client = get_sync_mongodb_client()
        db = client[settings.mongodb_db_name]
        collection = db["historical_rides"]
        
        # Map month names to numbers
        month_map = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }
        
        # Parse month
        month_num = None
        if month:
            if month.lower() in month_map:
                month_num = month_map[month.lower()]
            elif month.isdigit():
                month_num = int(month)
        
        # Parse year
        year_num = None
        if year and year.isdigit():
            year_num = int(year)
        
        try:
            # Build query with date filtering if specified
            if month_num:
                # Use aggregation for month filtering
                pipeline = [
                    {"$addFields": {"order_month": {"$month": "$Order_Date"}}},
                    {"$match": {"order_month": month_num}},
                    {"$sort": {"Historical_Cost_of_Ride": -1}},
                    {"$limit": limit}
                ]
                rides = list(collection.aggregate(pipeline))
            else:
                # Simple query without month filter
                rides = list(collection.find({}).sort("Historical_Cost_of_Ride", -1).limit(limit))
        finally:
            client.close()
        
        # Format results
        formatted_rides = []
        for i, ride in enumerate(rides, 1):
            formatted_rides.append({
                "rank": i,
                "revenue": round(ride.get("Historical_Cost_of_Ride", 0), 2),
                "order_date": str(ride.get("Order_Date", "N/A"))[:10],
                "pricing_model": ride.get("Pricing_Model", "N/A"),
                "location": ride.get("Location_Category", "N/A"),
                "time_of_day": ride.get("Time_of_Ride", "N/A"),
                "customer_loyalty": ride.get("Customer_Loyalty_Status", "N/A"),
                "vehicle_type": ride.get("Vehicle_Type", "N/A"),
                "demand_profile": ride.get("Demand_Profile", "N/A")
            })
        
        return json.dumps({
            "top_rides": formatted_rides,
            "count": len(formatted_rides),
            "filter": {
                "month": month if month else "all",
                "year": year if year else "all"
            },
            "sorted_by": "revenue (highest first)"
        })
    except Exception as e:
        return json.dumps({"error": f"Error getting top revenue rides: {str(e)}"})


@tool
def get_monthly_price_statistics(month: str = "", year: str = "") -> str:
    """
    Get average unit price and other price statistics for a specific month.
    
    Calculates average price per ride, total revenue, ride count, and price distribution
    for the specified month from historical_rides data.
    
    Args:
        month: Month name (e.g., "November", "January") or number (1-12). Required.
        year: Year (e.g., "2024"). Optional - if not provided, aggregates across all years.
    
    Returns:
        str: JSON string with monthly price statistics including average_unit_price
    """
    try:
        client = get_sync_mongodb_client()
        db = client[settings.mongodb_db_name]
        collection = db["historical_rides"]
        
        # Map month names to numbers
        month_map = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }
        
        # Parse month
        month_num = None
        if month:
            if month.lower() in month_map:
                month_num = month_map[month.lower()]
            elif month.isdigit():
                month_num = int(month)
        
        if not month_num:
            return json.dumps({
                "error": "Month is required. Provide month name (e.g., 'November') or number (1-12)."
            })
        
        # Parse year
        year_num = None
        if year and year.isdigit():
            year_num = int(year)
        
        try:
            # Build aggregation pipeline for monthly statistics
            match_stage = {"$addFields": {"order_month": {"$month": "$Order_Date"}}}
            
            pipeline = [
                match_stage,
                {"$match": {"order_month": month_num}}
            ]
            
            # Add year filter if specified
            if year_num:
                pipeline[0] = {"$addFields": {
                    "order_month": {"$month": "$Order_Date"},
                    "order_year": {"$year": "$Order_Date"}
                }}
                pipeline[1] = {"$match": {"order_month": month_num, "order_year": year_num}}
            
            # Add aggregation for statistics
            pipeline.extend([
                {
                    "$group": {
                        "_id": None,
                        "total_revenue": {"$sum": "$Historical_Cost_of_Ride"},
                        "total_rides": {"$sum": 1},
                        "average_unit_price": {"$avg": "$Historical_Cost_of_Ride"},
                        "min_price": {"$min": "$Historical_Cost_of_Ride"},
                        "max_price": {"$max": "$Historical_Cost_of_Ride"},
                        "total_duration": {"$sum": "$Expected_Ride_Duration"}
                    }
                }
            ])
            
            result = list(collection.aggregate(pipeline))
            
            # Get price by pricing model
            pricing_model_pipeline = [
                {"$addFields": {"order_month": {"$month": "$Order_Date"}}},
                {"$match": {"order_month": month_num}},
                {
                    "$group": {
                        "_id": "$Pricing_Model",
                        "count": {"$sum": 1},
                        "avg_price": {"$avg": "$Historical_Cost_of_Ride"},
                        "total_revenue": {"$sum": "$Historical_Cost_of_Ride"}
                    }
                }
            ]
            
            if year_num:
                pricing_model_pipeline[0] = {"$addFields": {
                    "order_month": {"$month": "$Order_Date"},
                    "order_year": {"$year": "$Order_Date"}
                }}
                pricing_model_pipeline[1] = {"$match": {"order_month": month_num, "order_year": year_num}}
            
            pricing_breakdown = list(collection.aggregate(pricing_model_pipeline))
            
            # Get price by location
            location_pipeline = [
                {"$addFields": {"order_month": {"$month": "$Order_Date"}}},
                {"$match": {"order_month": month_num}},
                {
                    "$group": {
                        "_id": "$Location_Category",
                        "count": {"$sum": 1},
                        "avg_price": {"$avg": "$Historical_Cost_of_Ride"}
                    }
                }
            ]
            
            if year_num:
                location_pipeline[0] = {"$addFields": {
                    "order_month": {"$month": "$Order_Date"},
                    "order_year": {"$year": "$Order_Date"}
                }}
                location_pipeline[1] = {"$match": {"order_month": month_num, "order_year": year_num}}
            
            location_breakdown = list(collection.aggregate(location_pipeline))
            
        finally:
            client.close()
        
        if not result:
            month_name = list(month_map.keys())[month_num - 1].title()
            return json.dumps({
                "error": f"No data found for {month_name}" + (f" {year_num}" if year_num else ""),
                "month": month_name,
                "year": year if year else "all"
            })
        
        stats = result[0]
        month_name = list(month_map.keys())[month_num - 1].title()
        
        # Format pricing model breakdown
        pricing_by_model = {}
        for pm in pricing_breakdown:
            pricing_by_model[pm["_id"]] = {
                "count": pm["count"],
                "average_price": round(pm["avg_price"], 2),
                "total_revenue": round(pm["total_revenue"], 2)
            }
        
        # Format location breakdown
        pricing_by_location = {}
        for loc in location_breakdown:
            pricing_by_location[loc["_id"]] = {
                "count": loc["count"],
                "average_price": round(loc["avg_price"], 2)
            }
        
        # Calculate average duration per ride
        avg_duration = stats["total_duration"] / stats["total_rides"] if stats["total_rides"] > 0 else 0
        
        return json.dumps({
            "month": month_name,
            "year": year if year else "all years",
            "statistics": {
                "average_unit_price": round(stats["average_unit_price"], 2),
                "total_revenue": round(stats["total_revenue"], 2),
                "total_rides": stats["total_rides"],
                "min_price": round(stats["min_price"], 2),
                "max_price": round(stats["max_price"], 2),
                "average_ride_duration_minutes": round(avg_duration, 1)
            },
            "by_pricing_model": pricing_by_model,
            "by_location": pricing_by_location,
            "summary": f"{month_name} average unit price is ${stats['average_unit_price']:.2f} across {stats['total_rides']} rides with total revenue of ${stats['total_revenue']:,.2f}"
        })
    except Exception as e:
        return json.dumps({"error": f"Error getting monthly price statistics: {str(e)}"})


@tool
def analyze_customer_segments() -> str:
    """
    Analyze customer distribution by loyalty tier.
    
    Calculates:
    - Distribution of Gold, Silver, Regular customers
    - Average revenue per segment
    - Segment metrics
    
    Returns:
        str: JSON string with customer segment analysis
    """
    try:
        client = get_sync_mongodb_client()
        db = client[settings.mongodb_db_name]
        
        try:
            # Try historical_rides first
            collection = db["historical_rides"]
            count = collection.count_documents({})
            
            if count > 0:
                orders = list(collection.find({}).limit(1000))
                loyalty_field = "Customer_Loyalty_Status"
                price_field = "Historical_Cost_of_Ride"
            else:
                collection = db["ride_orders"]
                orders = list(collection.find({}).limit(1000))
                loyalty_field = "customer.loyalty_tier"
                price_field = "final_price"
        finally:
            client.close()
        
        # Count by loyalty tier
        gold_count = 0
        silver_count = 0
        regular_count = 0
        gold_revenue = 0.0
        silver_revenue = 0.0
        regular_revenue = 0.0
        
        for order in orders:
            # Get loyalty tier (handle nested field for ride_orders)
            if "." in loyalty_field:
                parts = loyalty_field.split(".")
                loyalty_tier = order.get(parts[0], {}).get(parts[1], "Regular")
            else:
                loyalty_tier = order.get(loyalty_field, "Regular")
            
            price = order.get(price_field, 0)
            
            if loyalty_tier == "Gold":
                gold_count += 1
                gold_revenue += price
            elif loyalty_tier == "Silver":
                silver_count += 1
                silver_revenue += price
            else:
                regular_count += 1
                regular_revenue += price
        
        total_customers = gold_count + silver_count + regular_count
        
        return json.dumps({
            "total_customers": total_customers,
            "gold_customers": gold_count,
            "silver_customers": silver_count,
            "regular_customers": regular_count,
            "gold_percentage": round((gold_count / total_customers * 100) if total_customers > 0 else 0, 2),
            "silver_percentage": round((silver_count / total_customers * 100) if total_customers > 0 else 0, 2),
            "regular_percentage": round((regular_count / total_customers * 100) if total_customers > 0 else 0, 2),
            "avg_revenue_gold": round(gold_revenue / gold_count if gold_count > 0 else 0, 2),
            "avg_revenue_silver": round(silver_revenue / silver_count if silver_count > 0 else 0, 2),
            "avg_revenue_regular": round(regular_revenue / regular_count if regular_count > 0 else 0, 2)
        })
    except Exception as e:
        return json.dumps({"error": f"Error analyzing customer segments: {str(e)}"})


@tool
def analyze_location_performance() -> str:
    """
    Analyze performance by location category (Urban, Suburban, Rural).
    
    Calculates:
    - Ride count by location
    - Revenue by location
    - Average revenue per ride by location
    
    Returns:
        str: JSON string with location performance analysis
    """
    try:
        client = get_sync_mongodb_client()
        db = client[settings.mongodb_db_name]
        collection = db["historical_rides"]
        
        try:
            # Aggregate by location
            pipeline = [
                {
                    "$group": {
                        "_id": "$Location_Category",
                        "count": {"$sum": 1},
                        "total_revenue": {"$sum": "$Historical_Cost_of_Ride"},
                        "avg_revenue": {"$avg": "$Historical_Cost_of_Ride"}
                    }
                },
                {"$sort": {"total_revenue": -1}}
            ]
            results = list(collection.aggregate(pipeline))
        finally:
            client.close()
        
        location_data = {}
        for r in results:
            location = r.get("_id", "Unknown")
            location_data[location] = {
                "ride_count": r.get("count", 0),
                "total_revenue": round(r.get("total_revenue", 0), 2),
                "avg_revenue_per_ride": round(r.get("avg_revenue", 0), 2)
            }
        
        return json.dumps({
            "location_performance": location_data,
            "sorted_by": "total revenue (highest first)"
        })
    except Exception as e:
        return json.dumps({"error": f"Error analyzing location performance: {str(e)}"})


@tool
def analyze_time_patterns() -> str:
    """
    Analyze ride patterns by time of day (Morning, Afternoon, Evening, Night).
    
    Calculates:
    - Ride count by time period
    - Revenue by time period
    - Average revenue per ride by time period
    
    Returns:
        str: JSON string with time pattern analysis
    """
    try:
        client = get_sync_mongodb_client()
        db = client[settings.mongodb_db_name]
        collection = db["historical_rides"]
        
        try:
            # Aggregate by time of day
            pipeline = [
                {
                    "$group": {
                        "_id": "$Time_of_Ride",
                        "count": {"$sum": 1},
                        "total_revenue": {"$sum": "$Historical_Cost_of_Ride"},
                        "avg_revenue": {"$avg": "$Historical_Cost_of_Ride"}
                    }
                },
                {"$sort": {"count": -1}}
            ]
            results = list(collection.aggregate(pipeline))
        finally:
            client.close()
        
        time_data = {}
        for r in results:
            time_period = r.get("_id", "Unknown")
            time_data[time_period] = {
                "ride_count": r.get("count", 0),
                "total_revenue": round(r.get("total_revenue", 0), 2),
                "avg_revenue_per_ride": round(r.get("avg_revenue", 0), 2)
            }
        
        return json.dumps({
            "time_patterns": time_data,
            "sorted_by": "ride count (highest first)"
        })
    except Exception as e:
        return json.dumps({"error": f"Error analyzing time patterns: {str(e)}"})


@tool
def compare_with_competitors() -> str:
    """
    Compare HWCO pricing with competitor pricing from MongoDB.
    
    Queries both historical_rides (HWCO) and competitor_prices (Lyft) collections
    to calculate and compare average prices, totals, and identify pricing gaps.
    
    Returns:
        str: JSON string with HWCO vs competitor comparison including:
            - HWCO metrics (rides, revenue, avg price)
            - Competitor metrics (rides, revenue, avg price)
            - Price gap percentage
            - Breakdown by location
    """
    try:
        client = get_sync_mongodb_client()
        db = client[settings.mongodb_db_name]
        
        try:
            # Get HWCO data from historical_rides
            hwco_collection = db["historical_rides"]
            hwco_data = list(hwco_collection.find({}).limit(500))
            
            # Get competitor data from competitor_prices
            comp_collection = db["competitor_prices"]
            comp_data = list(comp_collection.find({}).limit(500))
        finally:
            client.close()
        
        if not hwco_data and not comp_data:
            return json.dumps({"error": "No data found for comparison", "hwco_count": 0, "competitor_count": 0})
        
        # Calculate HWCO metrics
        hwco_prices = [float(r.get("Historical_Cost_of_Ride", 0)) for r in hwco_data if r.get("Historical_Cost_of_Ride")]
        hwco_avg = sum(hwco_prices) / len(hwco_prices) if hwco_prices else 0
        hwco_total = sum(hwco_prices)
        
        # Calculate competitor metrics
        comp_prices = []
        for r in comp_data:
            price = r.get("Historical_Cost_of_Ride") or r.get("price", 0)
            if price:
                comp_prices.append(float(price))
        
        comp_avg = sum(comp_prices) / len(comp_prices) if comp_prices else 0
        comp_total = sum(comp_prices)
        
        # Calculate gap
        price_gap = ((hwco_avg - comp_avg) / comp_avg * 100) if comp_avg > 0 else 0
        
        # By location comparison
        hwco_by_loc = {}
        for r in hwco_data:
            loc = r.get("Location_Category", "Unknown")
            price = float(r.get("Historical_Cost_of_Ride", 0))
            if loc not in hwco_by_loc:
                hwco_by_loc[loc] = {"count": 0, "total": 0}
            hwco_by_loc[loc]["count"] += 1
            hwco_by_loc[loc]["total"] += price
        
        comp_by_loc = {}
        for r in comp_data:
            loc = r.get("Location_Category", "Unknown")
            price = float(r.get("Historical_Cost_of_Ride") or r.get("price", 0))
            if loc not in comp_by_loc:
                comp_by_loc[loc] = {"count": 0, "total": 0}
            comp_by_loc[loc]["count"] += 1
            comp_by_loc[loc]["total"] += price
        
        # Calculate averages by location
        location_comparison = {}
        for loc in set(list(hwco_by_loc.keys()) + list(comp_by_loc.keys())):
            hwco_loc_avg = hwco_by_loc.get(loc, {}).get("total", 0) / hwco_by_loc.get(loc, {}).get("count", 1) if hwco_by_loc.get(loc, {}).get("count", 0) > 0 else 0
            comp_loc_avg = comp_by_loc.get(loc, {}).get("total", 0) / comp_by_loc.get(loc, {}).get("count", 1) if comp_by_loc.get(loc, {}).get("count", 0) > 0 else 0
            gap = ((hwco_loc_avg - comp_loc_avg) / comp_loc_avg * 100) if comp_loc_avg > 0 else 0
            location_comparison[loc] = {
                "hwco_avg": round(hwco_loc_avg, 2),
                "competitor_avg": round(comp_loc_avg, 2),
                "gap_percent": round(gap, 2)
            }
        
        return json.dumps({
            "hwco": {
                "ride_count": len(hwco_data),
                "total_revenue": round(hwco_total, 2),
                "average_price": round(hwco_avg, 2)
            },
            "competitor": {
                "ride_count": len(comp_data),
                "total_revenue": round(comp_total, 2),
                "average_price": round(comp_avg, 2)
            },
            "comparison": {
                "overall_price_gap_percent": round(price_gap, 2),
                "hwco_is_higher": price_gap > 0,
                "summary": f"HWCO avg ${hwco_avg:.2f} vs Competitor avg ${comp_avg:.2f} (gap: {price_gap:.1f}%)"
            },
            "by_location": location_comparison
        })
    except Exception as e:
        return json.dumps({"error": f"Error comparing with competitors: {str(e)}"})


@tool
def analyze_event_impact_on_demand(event_type: str = "", location: str = "") -> str:
    """
    Query and analyze events from MongoDB to understand demand impact.
    
    This tool queries ACTUAL events data from n8n Eventbrite workflow and
    analyzes how events affect ride demand and pricing opportunities.
    
    Args:
        event_type: Filter by event type (e.g., "concert", "sports"). Empty for all.
        location: Filter by venue/location. Empty for all.
    
    Returns:
        str: JSON analysis of events and their demand impact
    """
    try:
        # Query actual events from MongoDB
        events = query_events_data(event_type=event_type, location=location, limit=20)
        
        if not events:
            return json.dumps({
                "message": "No events found in database",
                "events": [],
                "demand_impact": "Unable to assess - no data"
            })
        
        # Analyze events
        formatted_events = []
        high_impact_events = 0
        
        for e in events:
            event_info = {
                "name": e.get("name") or e.get("title", "Unknown"),
                "date": str(e.get("event_date") or e.get("date", "Unknown")),
                "venue": e.get("venue", "Unknown"),
                "type": e.get("event_type", "Unknown"),
                "expected_attendance": e.get("expected_attendance", "Unknown")
            }
            formatted_events.append(event_info)
            
            # Count high-impact events (sports, concerts tend to have high demand)
            etype = str(e.get("event_type", "")).lower()
            if any(t in etype for t in ["concert", "sport", "game", "festival"]):
                high_impact_events += 1
        
        demand_increase = "20-40%" if high_impact_events > 0 else "10-20%"
        surge_recommendation = "1.5x-2.0x during event hours" if high_impact_events > 2 else "1.3x-1.5x during event hours"
        
        return json.dumps({
            "events_count": len(formatted_events),
            "events": formatted_events[:10],
            "high_impact_events": high_impact_events,
            "demand_impact_estimate": demand_increase,
            "surge_recommendation": surge_recommendation,
            "analysis": f"Found {len(formatted_events)} events, {high_impact_events} high-impact. Expected demand increase: {demand_increase}."
        })
    except Exception as e:
        return json.dumps({"error": f"Error analyzing events: {str(e)}"})


@tool
def analyze_traffic_patterns(location: str = "") -> str:
    """
    Query and analyze traffic data from MongoDB for surge pricing opportunities.
    
    This tool queries ACTUAL traffic data from n8n Google Maps workflow
    and identifies surge pricing opportunities based on congestion.
    
    Args:
        location: Filter by location. Empty for all locations.
    
    Returns:
        str: JSON analysis of traffic patterns and surge recommendations
    """
    try:
        # Query actual traffic from MongoDB
        traffic = query_traffic_data(location=location, limit=30)
        
        if not traffic:
            return json.dumps({
                "message": "No traffic data found in database",
                "conditions": [],
                "surge_recommendation": "Unable to assess - no data"
            })
        
        # Analyze traffic patterns
        formatted_traffic = []
        congested_count = 0
        
        for t in traffic:
            congestion = t.get("congestion_level") or t.get("traffic_level", "")
            traffic_info = {
                "location": t.get("location", "Unknown"),
                "timestamp": str(t.get("timestamp", "Unknown")),
                "congestion_level": congestion,
                "delay_minutes": t.get("delay_minutes") or t.get("delay", 0)
            }
            formatted_traffic.append(traffic_info)
            
            # Count congested areas
            if congestion and any(c in str(congestion).lower() for c in ["heavy", "high", "severe"]):
                congested_count += 1
        
        # Surge pricing recommendation based on congestion
        if congested_count > len(traffic) * 0.5:
            surge = "1.5x-1.8x"
            assessment = "High congestion detected"
        elif congested_count > len(traffic) * 0.25:
            surge = "1.3x-1.5x"
            assessment = "Moderate congestion detected"
        else:
            surge = "1.0x-1.2x"
            assessment = "Normal traffic conditions"
        
        return json.dumps({
            "data_points": len(formatted_traffic),
            "traffic_conditions": formatted_traffic[:10],
            "congested_locations": congested_count,
            "traffic_assessment": assessment,
            "surge_recommendation": surge,
            "analysis": f"Analyzed {len(traffic)} traffic reports. {congested_count} show congestion. Recommended surge: {surge}."
        })
    except Exception as e:
        return json.dumps({"error": f"Error analyzing traffic: {str(e)}"})


@tool
def analyze_industry_trends(topic: str = "") -> str:
    """
    Query and analyze rideshare news from MongoDB for industry trends.
    
    This tool queries ACTUAL news data from n8n NewsAPI workflow
    and identifies trends affecting rideshare demand or strategy.
    
    Args:
        topic: Filter by topic/keyword. Empty for all news.
    
    Returns:
        str: JSON analysis of industry trends
    """
    try:
        # Query actual news from MongoDB
        news = query_news_data(topic=topic, limit=15)
        
        if not news:
            return json.dumps({
                "message": "No news found in database",
                "articles": [],
                "trends": "Unable to assess - no data"
            })
        
        # Analyze news for trends
        formatted_news = []
        topics_found = {}
        
        for n in news:
            title = n.get("title", "")
            article_info = {
                "title": title,
                "published": str(n.get("published_at") or n.get("date", "Unknown")),
                "source": n.get("source", "Unknown"),
                "summary": (n.get("summary") or n.get("description", ""))[:150]
            }
            formatted_news.append(article_info)
            
            # Track topics
            title_lower = title.lower()
            if any(w in title_lower for w in ["price", "pricing", "fare"]):
                topics_found["pricing"] = topics_found.get("pricing", 0) + 1
            if any(w in title_lower for w in ["regulation", "law", "policy"]):
                topics_found["regulation"] = topics_found.get("regulation", 0) + 1
            if any(w in title_lower for w in ["competition", "uber", "lyft", "competitor"]):
                topics_found["competition"] = topics_found.get("competition", 0) + 1
            if any(w in title_lower for w in ["demand", "growth", "expand"]):
                topics_found["demand"] = topics_found.get("demand", 0) + 1
        
        # Generate trend summary
        trend_summary = []
        if topics_found.get("regulation", 0) > 0:
            trend_summary.append("Regulatory changes may affect operations")
        if topics_found.get("competition", 0) > 0:
            trend_summary.append("Competitive moves in the market")
        if topics_found.get("pricing", 0) > 0:
            trend_summary.append("Pricing discussions in the industry")
        if topics_found.get("demand", 0) > 0:
            trend_summary.append("Demand patterns changing")
        
        return json.dumps({
            "articles_count": len(formatted_news),
            "articles": formatted_news[:10],
            "topics_detected": topics_found,
            "trend_summary": trend_summary if trend_summary else ["No significant trends detected"],
            "analysis": f"Analyzed {len(news)} articles. Topics: {topics_found}"
        })
    except Exception as e:
        return json.dumps({"error": f"Error analyzing news: {str(e)}"})


@tool
def get_n8n_data_summary() -> str:
    """
    Get a summary of all n8n ingested data from MongoDB.
    
    This tool provides an overview of events, traffic, and news data
    available from n8n workflows, helping understand data availability.
    
    Returns:
        str: JSON summary of n8n data collections
    """
    try:
        events = query_events_data(limit=5)
        traffic = query_traffic_data(limit=5)
        news = query_news_data(limit=5)
        
        # Count totals
        client = get_sync_mongodb_client()
        db = client[settings.mongodb_db_name]
        
        try:
            events_count = db["events_data"].count_documents({})
            traffic_count = db["traffic_data"].count_documents({})
            news_count = db["rideshare_news"].count_documents({})
            if news_count == 0:
                news_count = db["news_articles"].count_documents({})
        finally:
            client.close()
        
        return json.dumps({
            "data_summary": {
                "events_data": {
                    "total_count": events_count,
                    "sample": [{"name": e.get("name") or e.get("title", "Unknown")} for e in events]
                },
                "traffic_data": {
                    "total_count": traffic_count,
                    "sample": [{"location": t.get("location", "Unknown")} for t in traffic]
                },
                "news_data": {
                    "total_count": news_count,
                    "sample": [{"title": n.get("title", "Unknown")} for n in news]
                }
            },
            "data_available": events_count > 0 or traffic_count > 0 or news_count > 0
        })
    except Exception as e:
        return json.dumps({"error": f"Error getting data summary: {str(e)}"})


# ============================================================================
# PIPELINE-SPECIFIC TOOLS
# These tools are used by the Pipeline Orchestrator for automated analysis
# They run independently of chatbot queries and don't affect existing functionality
# ============================================================================

@tool
def analyze_competitor_data_for_pipeline() -> str:
    """
    Analyze HWCO historical data vs competitor data for the pipeline.
    
    This tool performs comprehensive competitor analysis comparing:
    - HWCO pricing vs Lyft pricing
    - Revenue metrics comparison
    - Pricing model distribution
    - Location and time-based pricing gaps
    
    Used by: Pipeline Orchestrator (Analysis Phase)
    
    Returns:
        str: JSON string with competitor analysis results
    """
    try:
        client = get_sync_mongodb_client()
        db = client[settings.mongodb_db_name]
        
        try:
            # Get HWCO data from historical_rides
            hwco_collection = db["historical_rides"]
            hwco_data = list(hwco_collection.find({"Rideshare_Company": "HWCO"}).limit(1000))
            
            # Get competitor data
            competitor_collection = db["competitor_prices"]
            competitor_data = list(competitor_collection.find({}).limit(1000))
            
            # Calculate HWCO metrics
            hwco_total_revenue = sum(d.get("Historical_Cost_of_Ride", 0) for d in hwco_data)
            hwco_count = len(hwco_data)
            hwco_avg_price = hwco_total_revenue / hwco_count if hwco_count > 0 else 0
            
            # Calculate competitor metrics
            competitor_total_revenue = sum(d.get("Historical_Cost_of_Ride", d.get("price", 0)) for d in competitor_data)
            competitor_count = len(competitor_data)
            competitor_avg_price = competitor_total_revenue / competitor_count if competitor_count > 0 else 0
            
            # Pricing by location
            hwco_by_location = {}
            for d in hwco_data:
                loc = d.get("Location_Category", "Unknown")
                if loc not in hwco_by_location:
                    hwco_by_location[loc] = {"count": 0, "total": 0}
                hwco_by_location[loc]["count"] += 1
                hwco_by_location[loc]["total"] += d.get("Historical_Cost_of_Ride", 0)
            
            for loc in hwco_by_location:
                hwco_by_location[loc]["avg"] = round(
                    hwco_by_location[loc]["total"] / hwco_by_location[loc]["count"], 2
                ) if hwco_by_location[loc]["count"] > 0 else 0
            
            # Revenue gap
            revenue_gap_pct = ((competitor_total_revenue - hwco_total_revenue) / hwco_total_revenue * 100) if hwco_total_revenue > 0 else 0
            
        finally:
            client.close()
        
        # Generate natural language explanation using GPT-4
        explanation = _generate_competitor_explanation(
            hwco_total_revenue, hwco_count, hwco_avg_price,
            competitor_total_revenue, competitor_count, competitor_avg_price,
            revenue_gap_pct, hwco_by_location
        )
        
        return json.dumps({
            "hwco": {
                "total_revenue": round(hwco_total_revenue, 2),
                "ride_count": hwco_count,
                "avg_price": round(hwco_avg_price, 2),
                "by_location": hwco_by_location
            },
            "competitor": {
                "total_revenue": round(competitor_total_revenue, 2),
                "ride_count": competitor_count,
                "avg_price": round(competitor_avg_price, 2)
            },
            "comparison": {
                "revenue_gap_percent": round(revenue_gap_pct, 2),
                "price_gap_percent": round((competitor_avg_price - hwco_avg_price) / hwco_avg_price * 100, 2) if hwco_avg_price > 0 else 0,
                "hwco_needs_increase": revenue_gap_pct > 0
            },
            "explanation": explanation,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        return json.dumps({"error": f"Error in competitor analysis: {str(e)}"})


def _generate_competitor_explanation(
    hwco_revenue, hwco_count, hwco_avg,
    comp_revenue, comp_count, comp_avg,
    revenue_gap, by_location
) -> str:
    """Generate natural language explanation for competitor analysis using GPT-4."""
    try:
        from openai import OpenAI
        
        if not settings.OPENAI_API_KEY:
            # Fallback explanation without GPT-4
            if revenue_gap > 0:
                return f"HWCO is underperforming vs competitors by {abs(revenue_gap):.1f}%. Average price ${hwco_avg:.2f} vs competitor ${comp_avg:.2f}. Consider strategic price adjustments."
            else:
                return f"HWCO is outperforming competitors by {abs(revenue_gap):.1f}%. Maintain current pricing strategy while monitoring market changes."
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Find best/worst performing locations
        locations_sorted = sorted(by_location.items(), key=lambda x: x[1].get("avg", 0), reverse=True)
        top_locations = locations_sorted[:3] if len(locations_sorted) >= 3 else locations_sorted
        
        prompt = f"""
        Analyze this competitor comparison data and provide a concise business insight (2-3 sentences):

        HWCO Performance:
        - Total Revenue: ${hwco_revenue:,.2f}
        - Total Rides: {hwco_count}
        - Average Price: ${hwco_avg:.2f}
        
        Competitor Performance:
        - Total Revenue: ${comp_revenue:,.2f}
        - Total Rides: {comp_count}
        - Average Price: ${comp_avg:.2f}
        
        Revenue Gap: {revenue_gap:.1f}% (positive = HWCO behind, negative = HWCO ahead)
        
        Top Performing HWCO Locations: {', '.join(f"{loc}: ${data.get('avg', 0):.2f}" for loc, data in top_locations)}
        
        Provide actionable insights for business decision-making. Focus on pricing opportunities and competitive positioning.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        # Fallback on error
        if revenue_gap > 0:
            return f"HWCO is underperforming vs competitors by {abs(revenue_gap):.1f}%. Consider strategic price adjustments."
        else:
            return f"HWCO is outperforming competitors by {abs(revenue_gap):.1f}%. Maintain current strategy."


@tool
def analyze_external_data_for_pipeline() -> str:
    """
    Analyze external data (news, events, traffic) for the pipeline.
    
    This tool synthesizes data from n8n workflows:
    - Events from Eventbrite (demand impact)
    - Traffic from Google Maps (surge opportunities)
    - News from NewsAPI (industry trends)
    
    Used by: Pipeline Orchestrator (Analysis Phase)
    
    Returns:
        str: JSON string with external data analysis
    """
    try:
        client = get_sync_mongodb_client()
        db = client[settings.mongodb_db_name]
        
        try:
            # Get events data
            events_collection = db["events_data"]
            events = list(events_collection.find({}).sort("event_date", -1).limit(50))
            
            # Get traffic data
            traffic_collection = db["traffic_data"]
            traffic = list(traffic_collection.find({}).sort("timestamp", -1).limit(50))
            
            # Get news data
            news_collection = db["rideshare_news"]
            news = list(news_collection.find({}).sort("published_at", -1).limit(20))
            
            # Analyze events for demand impact
            high_impact_events = [e for e in events if e.get("expected_attendees", 0) > 5000]
            
            # Analyze traffic for surge opportunities
            heavy_traffic = [t for t in traffic if "heavy" in str(t.get("traffic_level", "")).lower()]
            
            # Count news articles
            news_count = len(news)
            
        finally:
            client.close()
        
        # Generate natural language explanation
        explanation = _generate_external_data_explanation(
            len(events), len(high_impact_events), high_impact_events[:3],
            len(traffic), len(heavy_traffic),
            news_count, [n.get("title", "N/A")[:50] for n in news[:3]]
        )
        
        return json.dumps({
            "events": {
                "total_count": len(events),
                "high_impact_events": len(high_impact_events),
                "sample_events": [
                    {
                        "name": e.get("event_name", e.get("name", "Unknown")),
                        "attendees": e.get("expected_attendees", "N/A"),
                        "date": str(e.get("event_date", "N/A"))[:10]
                    } for e in high_impact_events[:5]
                ]
            },
            "traffic": {
                "total_records": len(traffic),
                "heavy_traffic_count": len(heavy_traffic),
                "surge_opportunities": len(heavy_traffic)
            },
            "news": {
                "article_count": news_count,
                "recent_headlines": [n.get("title", "N/A")[:80] for n in news[:5]]
            },
            "demand_indicators": {
                "event_driven_surge_opportunities": len(high_impact_events),
                "traffic_driven_surge_opportunities": len(heavy_traffic),
                "total_surge_opportunities": len(high_impact_events) + len(heavy_traffic)
            },
            "explanation": explanation,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        return json.dumps({"error": f"Error analyzing external data: {str(e)}"})


def _generate_external_data_explanation(
    events_count, high_impact_count, sample_events,
    traffic_count, heavy_traffic_count,
    news_count, headlines
) -> str:
    """Generate natural language explanation for external data analysis using GPT-4."""
    try:
        from openai import OpenAI
        
        surge_opportunities = high_impact_count + heavy_traffic_count
        
        if not settings.OPENAI_API_KEY:
            # Fallback explanation
            if surge_opportunities > 0:
                return f"Identified {surge_opportunities} surge pricing opportunities: {high_impact_count} high-impact events and {heavy_traffic_count} heavy traffic periods. Consider implementing dynamic pricing during these times."
            else:
                return "No immediate surge opportunities detected. Monitor for upcoming events and traffic patterns."
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        event_names = [e.get("event_name", e.get("name", "Unknown")) for e in sample_events]
        
        prompt = f"""
        Analyze this external data and provide a concise business insight (2-3 sentences):

        Events Data:
        - Total events: {events_count}
        - High-impact events (5000+ attendees): {high_impact_count}
        - Sample events: {', '.join(event_names) if event_names else 'None'}
        
        Traffic Data:
        - Total records: {traffic_count}
        - Heavy traffic periods: {heavy_traffic_count}
        
        News:
        - Article count: {news_count}
        - Recent headlines: {'; '.join(headlines) if headlines else 'None'}
        
        Identify surge pricing opportunities and demand drivers. Focus on actionable insights for revenue optimization.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        surge_opportunities = high_impact_count + heavy_traffic_count
        if surge_opportunities > 0:
            return f"Identified {surge_opportunities} surge pricing opportunities from events and traffic. Consider dynamic pricing."
        return "External data analysis complete. Monitor for emerging opportunities."


@tool
def get_combined_pricing_rules() -> str:
    """
    Get combined pricing rules from MongoDB pricing_strategies collection and newly generated rules.
    
    This tool combines:
    1. Existing rules from pricing_strategies MongoDB collection
    2. Rules from ChromaDB strategy_knowledge_vectors  
    3. Newly generated rules from current data analysis
    
    Returns merged, deduplicated pricing rules for recommendation analysis.
    
    Returns:
        str: JSON string with combined pricing rules
    """
    try:
        client = get_sync_mongodb_client()
        db = client[settings.mongodb_db_name]
        
        try:
            # 1. Load existing rules from MongoDB pricing_strategies
            strategies_collection = db["pricing_strategies"]
            existing_rules = list(strategies_collection.find({}))
            
            # Extract rules from nested structure
            mongodb_rules = []
            for strategy in existing_rules:
                if "pricing_rules" in strategy and isinstance(strategy["pricing_rules"], dict):
                    # Handle nested structure from dynamic_pricing_rules.json
                    for category, rules_list in strategy["pricing_rules"].items():
                        if isinstance(rules_list, list):
                            for rule in rules_list:
                                rule_copy = rule.copy()
                                rule_copy["source"] = "mongodb"
                                rule_copy["category"] = category
                                mongodb_rules.append(rule_copy)
            
            # 2. Query ChromaDB for strategy knowledge
            chromadb_rules = []
            try:
                strategy_docs = query_chromadb("strategy_knowledge_vectors", "pricing rules location time loyalty", n_results=20)
                for doc in strategy_docs:
                    if "content" in doc:
                        # Extract rule-like information from content
                        content = doc["content"]
                        if "multiplier" in content.lower() or "surge" in content.lower():
                            chromadb_rules.append({
                                "source": "chromadb",
                                "content": content[:200],
                                "mongodb_id": doc.get("mongodb_id", "")
                            })
            except:
                pass  # ChromaDB query failed, continue with MongoDB rules only
            
            # 3. Generate new rules from current data patterns
            hwco_collection = db["historical_rides"]
            competitor_collection = db["competitor_prices"]
            
            # Analyze current patterns for new rules
            hwco_data = list(hwco_collection.find({}).limit(500))
            competitor_data = list(competitor_collection.find({}).limit(500))
            
            generated_rules = []
            
            # Analyze loyalty tier patterns
            loyalty_stats = {}
            for ride in hwco_data:
                loyalty = ride.get("Customer_Loyalty_Status", "Unknown")
                ride_count = loyalty_stats.get(loyalty, {"count": 0, "total_price": 0})
                ride_count["count"] += 1
                ride_count["total_price"] += ride.get("Historical_Cost_of_Ride", 0)
                loyalty_stats[loyalty] = ride_count
            
            # Generate loyalty-based rules
            for loyalty, stats in loyalty_stats.items():
                if stats["count"] >= 25:
                    avg_price = stats["total_price"] / stats["count"]
                    generated_rules.append({
                        "rule_id": f"GEN_LOYAL_{loyalty.upper()}",
                        "name": f"{loyalty} Tier Pricing Pattern",
                        "description": f"Detected pattern for {loyalty} customers ({stats['count']} rides)",
                        "category": "loyalty_based",
                        "condition": {"loyalty_tier": loyalty},
                        "current_avg_price": round(avg_price, 2),
                        "ride_count": stats["count"],
                        "source": "generated",
                        "confidence": "high" if stats["count"] >= 50 else "medium"
                    })
            
            # Analyze demand profile patterns
            demand_stats = {}
            for ride in hwco_data:
                demand = ride.get("Demand_Profile", "Unknown")
                demand_count = demand_stats.get(demand, {"count": 0, "total_price": 0})
                demand_count["count"] += 1
                demand_count["total_price"] += ride.get("Historical_Cost_of_Ride", 0)
                demand_stats[demand] = demand_count
            
            # Generate demand-based rules
            for demand, stats in demand_stats.items():
                if stats["count"] >= 20:
                    avg_price = stats["total_price"] / stats["count"]
                    generated_rules.append({
                        "rule_id": f"GEN_DEMAND_{demand}",
                        "name": f"{demand} Demand Pricing",
                        "description": f"Detected {demand} demand pattern ({stats['count']} rides)",
                        "category": "demand_based",
                        "condition": {"demand_profile": demand},
                        "current_avg_price": round(avg_price, 2),
                        "ride_count": stats["count"],
                        "source": "generated",
                        "confidence": "high" if stats["count"] >= 50 else "medium"
                    })
            
        finally:
            client.close()
        
        # 4. Merge and deduplicate
        all_rules = mongodb_rules + generated_rules
        
        # Deduplicate by rule_id (prefer mongodb over generated)
        seen_ids = set()
        combined_rules = []
        
        # First add MongoDB rules
        for rule in mongodb_rules:
            rule_id = rule.get("rule_id", "")
            if rule_id and rule_id not in seen_ids:
                combined_rules.append(rule)
                seen_ids.add(rule_id)
        
        # Then add generated rules if not duplicate
        for rule in generated_rules:
            rule_id = rule.get("rule_id", "")
            if rule_id and rule_id not in seen_ids:
                combined_rules.append(rule)
                seen_ids.add(rule_id)
        
        # Categorize rules
        by_category = {
            "location_based": [],
            "time_based": [],
            "loyalty_based": [],
            "demand_based": [],
            "other": []
        }
        
        for rule in combined_rules:
            category = rule.get("category", "other")
            by_category.get(category, by_category["other"]).append(rule)
        
        result = {
            "summary": {
                "total_rules": len(combined_rules),
                "mongodb_rules": len(mongodb_rules),
                "chromadb_context": len(chromadb_rules),
                "generated_rules": len(generated_rules),
                "by_category": {k: len(v) for k, v in by_category.items()}
            },
            "combined_rules": combined_rules,
            "by_category": by_category
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Error combining pricing rules: {str(e)}", "combined_rules": []})


@tool
def generate_pricing_rules_for_pipeline() -> str:
    """
    Generate dynamic pricing rules based on latest data analysis.
    
    This tool creates pricing rules by analyzing:
    - Current HWCO vs competitor pricing gaps
    - Demand patterns by location and time
    - Customer segment behavior
    
    Rules are stored in the pricing_strategies MongoDB collection.
    
    Used by: Pipeline Orchestrator (Analysis Phase)
    
    Returns:
        str: JSON string with generated pricing rules summary
    """
    try:
        client = get_sync_mongodb_client()
        db = client[settings.mongodb_db_name]
        
        try:
            # Get current data for analysis
            hwco_collection = db["historical_rides"]
            
            # Analyze by location
            location_pipeline = [
                {"$group": {
                    "_id": "$Location_Category",
                    "avg_price": {"$avg": "$Historical_Cost_of_Ride"},
                    "count": {"$sum": 1}
                }}
            ]
            location_stats = {r["_id"]: r for r in hwco_collection.aggregate(location_pipeline)}
            
            # Analyze by time
            time_pipeline = [
                {"$group": {
                    "_id": "$Time_of_Ride",
                    "avg_price": {"$avg": "$Historical_Cost_of_Ride"},
                    "count": {"$sum": 1}
                }}
            ]
            time_stats = {r["_id"]: r for r in hwco_collection.aggregate(time_pipeline)}
            
            # Generate rules based on analysis
            generated_rules = []
            
            # Location-based rules
            for loc, stats in location_stats.items():
                if loc and stats["count"] > 10:
                    rule = {
                        "rule_id": f"AUTO_LOC_{loc.upper()[:3]}",
                        "name": f"Auto-generated {loc} pricing",
                        "category": "location_based",
                        "condition": {"location_category": loc},
                        "current_avg_price": round(stats["avg_price"], 2),
                        "ride_count": stats["count"],
                        "generated_at": datetime.now().isoformat(),
                        "source": "pipeline_auto_generated"
                    }
                    generated_rules.append(rule)
            
            # Time-based rules
            for time_period, stats in time_stats.items():
                if time_period and stats["count"] > 10:
                    rule = {
                        "rule_id": f"AUTO_TIME_{time_period.upper()[:3]}",
                        "name": f"Auto-generated {time_period} pricing",
                        "category": "time_based",
                        "condition": {"time_of_day": time_period},
                        "current_avg_price": round(stats["avg_price"], 2),
                        "ride_count": stats["count"],
                        "generated_at": datetime.now().isoformat(),
                        "source": "pipeline_auto_generated"
                    }
                    generated_rules.append(rule)
            
            # Store generated rules in pricing_strategies
            if generated_rules:
                strategies_collection = db["pricing_strategies"]
                # Remove old auto-generated rules
                strategies_collection.delete_many({"source": "pipeline_auto_generated"})
                # Insert new rules
                strategies_collection.insert_many(generated_rules)
            
        finally:
            client.close()
        
        # Generate explanation for the rules
        explanation = _generate_pricing_rules_explanation(generated_rules, location_stats, time_stats)
        
        return json.dumps({
            "rules_generated": len(generated_rules),
            "categories": list(set(r["category"] for r in generated_rules)),
            "rules": generated_rules,
            "stored_in": "pricing_strategies",
            "explanation": explanation,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        return json.dumps({"error": f"Error generating pricing rules: {str(e)}"})


def _generate_pricing_rules_explanation(rules, location_stats, time_stats) -> str:
    """Generate natural language explanation for pricing rules using GPT-4."""
    try:
        from openai import OpenAI
        
        if not settings.OPENAI_API_KEY:
            loc_count = sum(1 for r in rules if r.get("category") == "location_based")
            time_count = sum(1 for r in rules if r.get("category") == "time_based")
            return f"Generated {len(rules)} pricing rules: {loc_count} location-based and {time_count} time-based rules. Rules stored in pricing_strategies collection for agent access."
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Get summary stats
        loc_rules = [r for r in rules if r.get("category") == "location_based"]
        time_rules = [r for r in rules if r.get("category") == "time_based"]
        
        prompt = f"""
        Summarize these auto-generated pricing rules in 2-3 sentences for business users:

        Location-Based Rules ({len(loc_rules)}):
        {'; '.join(f"{r['name']}: ${r['current_avg_price']:.2f} avg ({r['ride_count']} rides)" for r in loc_rules[:5])}
        
        Time-Based Rules ({len(time_rules)}):
        {'; '.join(f"{r['name']}: ${r['current_avg_price']:.2f} avg ({r['ride_count']} rides)" for r in time_rules[:5])}
        
        Explain what these rules mean for pricing strategy and revenue optimization.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        loc_count = sum(1 for r in rules if r.get("category") == "location_based")
        time_count = sum(1 for r in rules if r.get("category") == "time_based")
        return f"Generated {len(rules)} pricing rules: {loc_count} location-based and {time_count} time-based. Rules ready for pricing optimization."


@tool
def calculate_whatif_impact_for_pipeline(recommendations: str) -> str:
    """
    Calculate what-if impact analysis for pipeline recommendations across all 4 business objectives.
    
    This tool estimates the KPI impact of proposed recommendations mapped to:
    1. Revenue (15-25% increase target)
    2. Profit Margin (optimize without losing customers)
    3. Competitive Position (achieve market parity/leadership)
    4. Customer Retention (10-15% churn reduction)
    
    Used by: Pipeline Orchestrator (What-If Phase)
    
    Args:
        recommendations: JSON string with recommendations from Recommendation Agent
                        Expected structure: recommendations_by_objective with revenue, profit_margin, competitive, retention
    
    Returns:
        str: JSON string with impact analysis mapped to 4 objectives
    """
    try:
        # Parse recommendations
        try:
            recs = json.loads(recommendations) if isinstance(recommendations, str) else recommendations
        except:
            recs = {"raw": str(recommendations)}
        
        client = get_sync_mongodb_client()
        db = client[settings.mongodb_db_name]
        
        try:
            # Get baseline KPIs
            hwco_collection = db["historical_rides"]
            
            baseline_revenue = 0
            baseline_rides = 0
            
            for doc in hwco_collection.find({}).limit(1000):
                baseline_revenue += doc.get("Historical_Cost_of_Ride", 0)
                baseline_rides += 1
            
            baseline_avg = baseline_revenue / baseline_rides if baseline_rides > 0 else 0
            
        finally:
            client.close()
        
        # Extract expected impact from new recommendation structure
        expected_impact = recs.get("expected_impact", {})
        
        # Parse percentages
        def extract_percentage(value: str) -> float:
            if not value:
                return 0
            value = value.replace("%", "").strip()
            if "-" in value:
                parts = value.split("-")
                return (float(parts[0]) + float(parts[1])) / 2
            try:
                return float(value)
            except:
                return 0
        
        revenue_impact_pct = extract_percentage(expected_impact.get("revenue_increase", "0"))
        margin_impact_pct = extract_percentage(expected_impact.get("profit_margin_improvement", "0"))
        churn_reduction_pct = extract_percentage(expected_impact.get("churn_reduction", "0"))
        
        # If not in expected_impact, estimate from recommendations_by_objective
        if revenue_impact_pct == 0:
            recs_by_obj = recs.get("recommendations_by_objective", {})
            rec_text = json.dumps(recs_by_obj).lower()
            
            # Estimate based on recommendation content
            if "surge" in rec_text or "multiplier" in rec_text:
                revenue_impact_pct += 15
                margin_impact_pct += 8
            if "loyalty" in rec_text or "gold" in rec_text or "retention" in rec_text:
                churn_reduction_pct += 12
                revenue_impact_pct += 5
            if "competitive" in rec_text or "competitor" in rec_text or "gap" in rec_text:
                revenue_impact_pct += 8
                churn_reduction_pct += 5
            if "urban" in rec_text or "location" in rec_text:
                revenue_impact_pct += 10
                margin_impact_pct += 5
            if "rush" in rec_text or "peak" in rec_text or "evening" in rec_text or "morning" in rec_text:
                revenue_impact_pct += 12
                margin_impact_pct += 7
            
            # Cap at targets
            revenue_impact_pct = min(revenue_impact_pct, 25)
            churn_reduction_pct = min(churn_reduction_pct, 15)
            margin_impact_pct = min(margin_impact_pct, 12)
        
        # Calculate projected values
        projected_revenue = baseline_revenue * (1 + revenue_impact_pct / 100)
        revenue_increase = projected_revenue - baseline_revenue
        
        # Calculate impact by business objective
        objectives_impact = {
            "revenue": {
                "objective": "Maximize Revenue: Increase 15-25%",
                "baseline_value": round(baseline_revenue, 2),
                "projected_value": round(projected_revenue, 2),
                "increase_pct": round(revenue_impact_pct, 1),
                "increase_amount": round(revenue_increase, 2),
                "target_met": revenue_impact_pct >= 15 and revenue_impact_pct <= 25,
                "actions_from_recommendations": recs.get("recommendations_by_objective", {}).get("revenue", {}).get("actions", [])
            },
            "profit_margin": {
                "objective": "Maximize Profit Margins",
                "baseline_margin_pct": 40.0,
                "projected_margin_pct": round(40.0 + margin_impact_pct, 1),
                "improvement_pct": round(margin_impact_pct, 1),
                "target_met": margin_impact_pct >= 5,
                "actions_from_recommendations": recs.get("recommendations_by_objective", {}).get("profit_margin", {}).get("actions", [])
            },
            "competitive": {
                "objective": "Stay Competitive",
                "current_position": "5% behind competitors",
                "projected_position": "competitive parity" if revenue_impact_pct >= 15 else "3% behind",
                "gap_closed_pct": round(min(revenue_impact_pct / 3, 5), 1),
                "target_met": revenue_impact_pct >= 15,
                "actions_from_recommendations": recs.get("recommendations_by_objective", {}).get("competitive", {}).get("actions", [])
            },
            "retention": {
                "objective": "Customer Retention: Reduce churn 10-15%",
                "baseline_churn_pct": 25.0,
                "projected_churn_pct": round(25.0 - churn_reduction_pct, 1),
                "churn_reduction_pct": round(churn_reduction_pct, 1),
                "target_met": churn_reduction_pct >= 10 and churn_reduction_pct <= 15,
                "actions_from_recommendations": recs.get("recommendations_by_objective", {}).get("retention", {}).get("actions", [])
            }
        }
        
        # Generate natural language explanation
        explanation = _generate_whatif_explanation(
            baseline_revenue, baseline_rides, baseline_avg,
            revenue_impact_pct, churn_reduction_pct, margin_impact_pct,
            projected_revenue, revenue_increase, recs
        )
        
        return json.dumps({
            "baseline": {
                "total_revenue": round(baseline_revenue, 2),
                "ride_count": baseline_rides,
                "avg_revenue_per_ride": round(baseline_avg, 2),
                "profit_margin_pct": 40.0,
                "churn_rate_pct": 25.0
            },
            "projected_impact": {
                "revenue_increase_pct": revenue_impact_pct,
                "retention_improvement_pct": churn_reduction_pct,
                "margin_improvement_pct": margin_impact_pct,
                "projected_revenue": round(projected_revenue, 2),
                "revenue_increase_amount": round(revenue_increase, 2)
            },
            "business_objectives_impact": objectives_impact,
            "business_objectives_alignment": {
                "revenue_target_met": objectives_impact["revenue"]["target_met"],
                "profit_margin_target_met": objectives_impact["profit_margin"]["target_met"],
                "competitive_target_met": objectives_impact["competitive"]["target_met"],
                "retention_target_met": objectives_impact["retention"]["target_met"],
                "all_targets_met": all(objectives_impact[obj]["target_met"] for obj in objectives_impact)
            },
            "confidence": "high" if all(objectives_impact[obj]["target_met"] for obj in objectives_impact) else "medium",
            "explanation": explanation,
            "recommendations_analyzed": recs,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        return json.dumps({"error": f"Error calculating what-if impact: {str(e)}"})


def _generate_whatif_explanation(
    baseline_revenue, baseline_rides, baseline_avg,
    revenue_pct, retention_pct, margin_pct,
    projected_revenue, revenue_increase, recs
) -> str:
    """Generate natural language explanation for what-if impact analysis using GPT-4."""
    try:
        from openai import OpenAI
        
        targets_met = revenue_pct >= 15 and retention_pct >= 10
        
        if not settings.OPENAI_API_KEY:
            # Fallback explanation
            status = "meet" if targets_met else "partially meet"
            return f"Impact analysis shows potential {revenue_pct}% revenue increase (${revenue_increase:,.2f}) and {retention_pct}% retention improvement. These recommendations would {status} business objectives."
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        prompt = f"""
        Summarize this what-if impact analysis in 2-3 sentences for business decision-makers:

        Current Baseline:
        - Total Revenue: ${baseline_revenue:,.2f}
        - Total Rides: {baseline_rides}
        - Average Revenue/Ride: ${baseline_avg:.2f}
        
        Projected Impact from Recommendations:
        - Revenue Increase: {revenue_pct}% (${revenue_increase:,.2f})
        - Customer Retention Improvement: {retention_pct}%
        - Profit Margin Improvement: {margin_pct}%
        - Projected Total Revenue: ${projected_revenue:,.2f}
        
        Business Objectives:
        - Revenue Target: 15-25% increase {'✓ MET' if revenue_pct >= 15 else '✗ NOT MET'}
        - Retention Target: 10-15% improvement {'✓ MET' if retention_pct >= 10 else '✗ NOT MET'}
        
        Provide executive summary of whether to proceed with recommendations and key risks/benefits.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        targets_met = revenue_pct >= 15 and retention_pct >= 10
        status = "meet" if targets_met else "partially meet"
        return f"Impact analysis: {revenue_pct}% revenue increase, {retention_pct}% retention improvement. Recommendations would {status} business objectives."


@tool
def generate_structured_insights(
    kpis: str,
    context: str = "",
    time_period: str = "30d"
) -> str:
    """
    Generate structured insights using OpenAI GPT-4.
    
    Combines KPI data with ChromaDB context to generate
    actionable insights for the analytics dashboard.
    
    Args:
        kpis: JSON string with KPI data (from calculate_revenue_kpis, etc.)
        context: Additional context from ChromaDB queries
        time_period: Time period analyzed
    
    Returns:
        str: JSON string with structured insights
    """
    try:
        from openai import OpenAI
        
        if not settings.OPENAI_API_KEY:
            return json.dumps({"error": "OPENAI_API_KEY not configured"})
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Parse KPIs if it's a string
        try:
            kpi_dict = json.loads(kpis) if isinstance(kpis, str) else kpis
        except:
            kpi_dict = {"raw": str(kpis)}
        
        prompt = f"""
        Analyze the following KPIs and context to generate structured insights for a rideshare analytics dashboard.
        
        KPIs: {json.dumps(kpi_dict, indent=2)}
        Context: {context[:500] if context else "No additional context"}
        Time Period: {time_period}
        
        Generate structured insights in JSON format with:
        1. key_findings: List of 3-5 key findings
        2. trends: List of identified trends (increasing, decreasing, stable)
        3. recommendations: List of actionable recommendations
        4. data_sources: List of data sources used
        5. confidence: Confidence level (high, medium, low)
        
        Focus on insights that help achieve business objectives:
        - Revenue increase (15-25% target)
        - Customer retention (10-15% churn reduction target)
        - Competitive positioning
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return json.dumps({"error": f"Error generating structured insights: {str(e)}"})


# Create the analysis agent
# Handle missing API key gracefully (for testing environments)
try:
    analysis_agent = create_agent(
        model="openai:gpt-4o-mini",
        tools=[
            # MongoDB KPI tools (USE THESE FOR ACTUAL DATA) - PRIMARY
            calculate_revenue_kpis,
            calculate_profit_metrics,
            calculate_rides_count,
            get_top_revenue_rides,
            get_monthly_price_statistics,
            analyze_customer_segments,
            analyze_location_performance,
            analyze_time_patterns,
            # n8n MongoDB data tools (USE THESE FOR EVENTS/TRAFFIC/NEWS)
            analyze_event_impact_on_demand,
            analyze_traffic_patterns,
            analyze_industry_trends,
            get_n8n_data_summary,
            # Competitor comparison
            compare_with_competitors,
            # ChromaDB RAG tools (for semantic search only, not actual data)
            query_ride_scenarios,
            query_news_events,
            query_customer_behavior,
            # Structured insights generation
            generate_structured_insights
        ],
        system_prompt=(
            "You are a data analysis specialist for a rideshare company. "
            "Your role is to analyze data, identify patterns, and generate actionable insights. "
            "\n\n"
            "CRITICAL - USE MONGODB TOOLS FOR ACTUAL DATA: "
            "- For monthly price queries: ALWAYS use get_monthly_price_statistics(month='...') "
            "- For KPIs: use calculate_revenue_kpis, calculate_profit_metrics "
            "- For competitor comparison: use compare_with_competitors "
            "- For events: use analyze_event_impact_on_demand (queries MongoDB) "
            "- For traffic: use analyze_traffic_patterns (queries MongoDB) "
            "- For news: use analyze_industry_trends (queries MongoDB) "
            "- For n8n data summary: use get_n8n_data_summary "
            "\n\n"
            "DO NOT use ChromaDB/RAG tools (query_ride_scenarios, query_news_events, etc.) "
            "for questions about ACTUAL DATA. Only use ChromaDB for semantic/context searches. "
            "\n\n"
            "Key workflow: "
            "1. For 'November average price': use get_monthly_price_statistics(month='November') "
            "2. For 'competitor comparison': use compare_with_competitors "
            "3. For 'events affecting demand': use analyze_event_impact_on_demand() "
            "4. For 'traffic patterns': use analyze_traffic_patterns() "
            "5. For 'industry news': use analyze_industry_trends() "
            "\n\n"
            "ALWAYS return ACTUAL NUMBERS from the MongoDB data!"
            "\n\n"
            "Always provide clear, data-driven answers with ACTUAL NUMBERS from the database. "
            "Help achieve business objectives: revenue increase 15-25%, customer retention, competitive positioning."
        ),
        name="analysis_agent"
    )
    logger.info("✓ Analysis agent initialized successfully with sync PyMongo")
except Exception as e:
    error_msg = str(e).lower()
    if "api_key" in error_msg or "openai" in error_msg:
        logger.warning("⚠️ Analysis agent could not be initialized: OPENAI_API_KEY not configured")
        analysis_agent = None
    else:
        logger.error(f"Failed to initialize analysis agent: {e}")
        raise
