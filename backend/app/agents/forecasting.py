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


# Initialize forecasting model instance
forecast_model = RideshareForecastModel()


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
            "You are a forecasting specialist. "
            "Your role is to predict future demand, analyze trends, "
            "and provide accurate forecasts using Prophet ML models and external data. "
            "\n\n"
            "IMPORTANT TOOL SELECTION: "
            "- For ACTUAL historical demand patterns: use get_historical_demand_data "
            "- For ACTUAL upcoming events: use get_upcoming_events "
            "- For ACTUAL traffic conditions: use get_traffic_conditions "
            "- For ACTUAL industry news: use get_industry_news "
            "- For RAG-based event search: use query_event_context "
            "- For ML forecasts: use generate_prophet_forecast "
            "- For explanations: use explain_forecast "
            "\n\n"
            "Key responsibilities: "
            "- Generate 30/60/90-day demand forecasts using Prophet ML "
            "- Query ACTUAL data from MongoDB (events, traffic, news) "
            "- Explain forecasts in natural language using OpenAI GPT-4 "
            "- Provide confidence intervals and trend analysis "
            "\n\n"
            "When generating forecasts: "
            "1. First query actual data: get_upcoming_events, get_traffic_conditions "
            "2. Use get_historical_demand_data to understand past patterns "
            "3. Use generate_prophet_forecast for ML predictions "
            "4. Use explain_forecast to provide natural language explanations "
            "5. Combine all data sources for comprehensive forecasts "
            "\n\n"
            "Return format should include: "
            "- forecast: List of forecast points with predicted_demand, confidence intervals "
            "- explanation: Natural language explanation from OpenAI GPT-4 "
            "- method: 'prophet_ml' "
            "- context: {events_detected, traffic_patterns} from actual MongoDB data "
            "\n\n"
            "Always include ACTUAL data from MongoDB in your analysis, not just RAG results."
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


