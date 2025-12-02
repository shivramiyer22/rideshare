"""
Analysis Agent - Performs data analysis and insights generation.

This agent analyzes business data to provide insights about:
- Revenue, profit, and KPIs
- Customer segments and behavior
- Ride patterns and trends
- n8n ingested data (events, traffic, news)

The agent uses RAG (Retrieval-Augmented Generation):
1. Query ChromaDB for similar past scenarios
2. Fetch full documents from MongoDB
3. Analyze the data using OpenAI GPT-4
4. Generate actionable insights
"""
from langchain.agents import create_agent
from langchain.tools import tool
from typing import Dict, Any, List
import asyncio
import json
from datetime import datetime, timedelta
from app.agents.utils import query_chromadb, fetch_mongodb_documents, format_documents_as_context
from app.database import get_database


def run_async_query(coro):
    """Helper to run async MongoDB queries in sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, we can't use run_until_complete
            # Return empty result as fallback
            return []
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(coro)


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
            return "No similar ride scenarios found."
        
        # Extract MongoDB IDs
        mongodb_ids = [r["mongodb_id"] for r in results]
        
        # Fetch full documents from MongoDB
        # Run async function in sync context
        loop = asyncio.get_event_loop()
        documents = loop.run_until_complete(
            fetch_mongodb_documents(mongodb_ids, "ride_orders")
        )
        
        # If no documents in ride_orders, try historical_rides
        if not documents:
            documents = loop.run_until_complete(
                fetch_mongodb_documents(mongodb_ids, "historical_rides")
            )
        
        # Format as context string
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
        mongodb_ids = [r["mongodb_id"] for r in results]
        
        # Fetch full documents from MongoDB
        loop = asyncio.get_event_loop()
        documents = loop.run_until_complete(
            fetch_mongodb_documents(mongodb_ids, "customers")
        )
        
        # Format as context string
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
        mongodb_ids = [r["mongodb_id"] for r in results]
        
        # Fetch full documents from MongoDB
        loop = asyncio.get_event_loop()
        documents = loop.run_until_complete(
            fetch_mongodb_documents(mongodb_ids, "competitor_prices")
        )
        
        # Format as context string
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
        database = get_database()
        if not database:
            return json.dumps({"error": "Database connection not available"})
        
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
        
        # Query current period
        collection = database["ride_orders"]
        
        # Get orders in current period (handle async in sync context)
        async def get_current_orders():
            return await collection.find({
                "created_at": {"$gte": start_date, "$lte": end_date}
            }).to_list(length=None)
        
        async def get_prev_orders():
            return await collection.find({
                "created_at": {"$gte": prev_start_date, "$lt": start_date}
            }).to_list(length=None)
        
        current_orders = run_async_query(get_current_orders())
        prev_orders = run_async_query(get_prev_orders())
        
        # Calculate total revenue
        total_revenue = sum(
            order.get("final_price", order.get("price", 0)) 
            for order in current_orders
        )
        
        # Calculate average revenue per ride
        ride_count = len(current_orders)
        avg_revenue_per_ride = total_revenue / ride_count if ride_count > 0 else 0
        
        prev_revenue = sum(
            order.get("final_price", order.get("price", 0)) 
            for order in prev_orders
        )
        
        # Calculate revenue growth
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
        database = get_database()
        if not database:
            return json.dumps({"error": "Database connection not available"})
        
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
        
        collection = database["ride_orders"]
        
        # Get orders in period (handle async in sync context)
        async def get_orders():
            return await collection.find({
                "created_at": {"$gte": start_date, "$lte": end_date}
            }).to_list(length=None)
        
        orders = run_async_query(get_orders())
        
        total_revenue = sum(
            order.get("final_price", order.get("price", 0)) 
            for order in orders
        )
        
        # Estimate costs (if cost data not available, use 60% of revenue as estimate)
        # In production, this would come from actual cost data
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
        database = get_database()
        if not database:
            return json.dumps({"error": "Database connection not available"})
        
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
        
        collection = database["ride_orders"]
        
        # Get orders in period (handle async in sync context)
        async def get_orders():
            return await collection.find({
                "created_at": {"$gte": start_date, "$lte": end_date}
            }).to_list(length=None)
        
        orders = run_async_query(get_orders())
        
        # Count by pricing model
        contracted_count = sum(1 for o in orders if o.get("pricing_model") == "CONTRACTED")
        standard_count = sum(1 for o in orders if o.get("pricing_model") == "STANDARD")
        custom_count = sum(1 for o in orders if o.get("pricing_model") == "CUSTOM")
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
        database = get_database()
        if not database:
            return json.dumps({"error": "Database connection not available"})
        
        collection = database["ride_orders"]
        
        # Get all orders (or recent orders) - handle async in sync context
        async def get_all_orders():
            return await collection.find({}).to_list(length=1000)  # Limit for performance
        
        orders = run_async_query(get_all_orders())
        
        # Count by loyalty tier
        gold_count = 0
        silver_count = 0
        regular_count = 0
        gold_revenue = 0.0
        silver_revenue = 0.0
        regular_revenue = 0.0
        
        for order in orders:
            customer = order.get("customer", {})
            loyalty_tier = customer.get("loyalty_tier", "Regular")
            price = order.get("final_price", order.get("price", 0))
            
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
    # This will use OpenAI GPT-4 to analyze the event data
    # For now, return basic analysis (will be enhanced with OpenAI)
    if not event_data or event_data == "No similar events or news found.":
        return "No event data available for analysis."
    
    # Basic analysis (will be enhanced with OpenAI GPT-4)
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
    
    # Basic analysis (will be enhanced with OpenAI GPT-4)
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
    
    # Basic analysis (will be enhanced with OpenAI GPT-4)
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
        from app.config import settings
        
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
            response_format={"type": "json_object"}  # Structured output
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
        # ChromaDB querying tools
        query_ride_scenarios,
        query_news_events,
        query_customer_behavior,
        query_competitor_data,
        # KPI calculation tools
        calculate_revenue_kpis,
        calculate_profit_metrics,
        calculate_rides_count,
        analyze_customer_segments,
        # n8n data analysis tools
        analyze_event_impact_on_demand,
        analyze_traffic_patterns,
        analyze_industry_trends,
        # Structured insights generation
        generate_structured_insights
    ],
    system_prompt=(
        "You are a data analysis specialist. "
        "Your role is to analyze data, identify patterns, and generate actionable insights for the analytics dashboard. "
        "\n\n"
        "Key responsibilities: "
        "- Calculate KPIs: revenue, profit, rides count, customer segments "
        "- Analyze n8n ingested data: events_data (event impact on demand), traffic_data (surge pricing opportunities), news_articles (industry trends) "
        "- Query ChromaDB for similar past scenarios using RAG "
        "- Fetch full documents from MongoDB for complete analysis "
        "- Generate structured insights using OpenAI GPT-4 "
        "- Provide dashboard-ready responses with data and explanations "
        "\n\n"
        "Workflow: "
        "1. Use KPI calculation tools (calculate_revenue_kpis, calculate_profit_metrics, etc.) to get metrics "
        "2. Query ChromaDB for context (query_ride_scenarios, query_news_events, etc.) "
        "3. Analyze n8n data (analyze_event_impact_on_demand, analyze_traffic_patterns, analyze_industry_trends) "
        "4. Generate structured insights (generate_structured_insights) combining KPIs and context "
        "\n\n"
        "Always provide clear, data-driven recommendations that help achieve business objectives "
        "(revenue increase 15-25%, customer retention, competitive positioning)."
        ),
        name="analysis_agent"
    )
except Exception as e:
    # If API key is missing, set to None (for testing environments)
    if "api_key" in str(e).lower() or "openai" in str(e).lower():
        analysis_agent = None
    else:
        # Re-raise if it's not an API key issue
        raise


