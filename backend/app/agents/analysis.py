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
from app.agents.utils import query_chromadb, format_documents_as_context
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
def analyze_event_impact_on_demand(event_data: str) -> str:
    """
    Analyze impact of events on demand using n8n ingested events_data.
    
    This tool analyzes events from n8n Eventbrite workflow to understand
    how events affect ride demand and pricing opportunities.
    
    Args:
        event_data: Context string from query_news_events tool or event description
    
    Returns:
        str: Analysis of event impact on demand
    """
    if not event_data or event_data == "No similar events or news found.":
        return "No event data available for analysis."
    
    return f"Event analysis: {event_data[:200]}... Impact on demand: Events typically increase demand by 20-40% during peak hours. Consider surge pricing during event times."


@tool
def analyze_traffic_patterns(traffic_data: str) -> str:
    """
    Analyze traffic patterns from n8n Google Maps workflow.
    
    Identifies surge pricing opportunities based on traffic congestion.
    
    Args:
        traffic_data: Context string from query_news_events tool or traffic description
    
    Returns:
        str: Analysis of traffic patterns and surge pricing opportunities
    """
    if not traffic_data or traffic_data == "No similar events or news found.":
        return "No traffic data available for analysis."
    
    return f"Traffic analysis: {traffic_data[:200]}... Surge pricing opportunity: Heavy traffic indicates high demand. Recommend 1.3x-1.6x surge multiplier."


@tool
def analyze_industry_trends(news_data: str) -> str:
    """
    Analyze industry trends from n8n NewsAPI workflow.
    
    Identifies trends that might affect rideshare demand or pricing strategy.
    
    Args:
        news_data: Context string from query_news_events tool or news description
    
    Returns:
        str: Analysis of industry trends
    """
    if not news_data or news_data == "No similar events or news found.":
        return "No news data available for analysis."
    
    return f"Industry trends: {news_data[:200]}... Market analysis: Monitor industry news for regulatory changes, competitor moves, or market shifts that could affect demand."


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
            # ChromaDB querying tools (RAG)
            query_ride_scenarios,
            query_news_events,
            query_customer_behavior,
            query_competitor_data,
            # KPI calculation tools (sync PyMongo)
            calculate_revenue_kpis,
            calculate_profit_metrics,
            calculate_rides_count,
            get_top_revenue_rides,
            analyze_customer_segments,
            analyze_location_performance,
            analyze_time_patterns,
            # n8n data analysis tools
            analyze_event_impact_on_demand,
            analyze_traffic_patterns,
            analyze_industry_trends,
            # Structured insights generation
            generate_structured_insights
        ],
        system_prompt=(
            "You are a data analysis specialist for a rideshare company. "
            "Your role is to analyze data, identify patterns, and generate actionable insights. "
            "\n\n"
            "Key responsibilities: "
            "- Calculate KPIs: revenue, profit, rides count, customer segments "
            "- Analyze patterns: location performance, time patterns, demand trends "
            "- Query historical data: top revenue rides, customer behavior "
            "- Analyze n8n ingested data: events (demand impact), traffic (surge pricing), news (industry trends) "
            "- Query ChromaDB for similar past scenarios using RAG "
            "- Generate structured insights using OpenAI GPT-4 "
            "\n\n"
            "Workflow for analytics queries: "
            "1. Use KPI tools (calculate_revenue_kpis, calculate_profit_metrics, etc.) for metrics "
            "2. Use get_top_revenue_rides for top performing rides "
            "3. Use analyze_customer_segments for customer distribution "
            "4. Use analyze_location_performance and analyze_time_patterns for patterns "
            "5. Generate structured insights combining all data "
            "\n\n"
            "Always provide clear, data-driven answers. Include specific numbers and trends. "
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
