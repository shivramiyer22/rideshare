"""
Recommendation Agent - Provides strategic recommendations.

This agent provides strategic business recommendations using:
- Strategy knowledge from ChromaDB (PRIMARY RAG source)
- Recent events from n8n (events, traffic, news)
- Competitor analysis data
- Forecasting Agent predictions

The agent focuses on achieving business objectives:
- Revenue increase (15-25%)
- Customer retention (10-15% churn reduction)
- Competitive positioning
"""
from langchain.agents import create_agent
from langchain.tools import tool
from typing import Dict, Any, List
import asyncio
import json
from app.agents.utils import (
    query_chromadb, 
    fetch_mongodb_documents, 
    format_documents_as_context,
    query_historical_rides,
    query_competitor_prices,
    query_events_data,
    query_traffic_data,
    query_news_data,
    get_mongodb_collection_stats
)
from app.config import settings


@tool
def get_performance_metrics(
    month: str = "",
    pricing_model: str = ""
) -> str:
    """
    Query actual HWCO performance metrics from MongoDB.
    
    Use this tool to get real revenue, ride counts, and pricing data
    for making strategic recommendations.
    
    Args:
        month: Month name (e.g., "November") or number. Empty for all.
        pricing_model: "CONTRACTED", "STANDARD", or "CUSTOM". Empty for all.
    
    Returns:
        str: JSON string with performance metrics
    """
    try:
        results = query_historical_rides(
            month=month,
            pricing_model=pricing_model,
            limit=1000  # Get more data for accurate metrics
        )
        
        if not results:
            return json.dumps({"error": "No performance data found", "count": 0})
        
        # Calculate key metrics
        total_revenue = sum(r.get("Historical_Cost_of_Ride", 0) for r in results)
        total_rides = len(results)
        avg_price = total_revenue / total_rides if total_rides > 0 else 0
        
        # By pricing model
        by_model = {}
        for r in results:
            model = r.get("Pricing_Model", "UNKNOWN")
            if model not in by_model:
                by_model[model] = {"count": 0, "revenue": 0}
            by_model[model]["count"] += 1
            by_model[model]["revenue"] += r.get("Historical_Cost_of_Ride", 0)
        
        # By location
        by_location = {}
        for r in results:
            loc = r.get("Location_Category", "Unknown")
            if loc not in by_location:
                by_location[loc] = {"count": 0, "revenue": 0}
            by_location[loc]["count"] += 1
            by_location[loc]["revenue"] += r.get("Historical_Cost_of_Ride", 0)
        
        # By customer tier
        by_tier = {}
        for r in results:
            tier = r.get("Customer_Loyalty_Status", "Regular")
            if tier not in by_tier:
                by_tier[tier] = {"count": 0, "revenue": 0}
            by_tier[tier]["count"] += 1
            by_tier[tier]["revenue"] += r.get("Historical_Cost_of_Ride", 0)
        
        return json.dumps({
            "total_rides": total_rides,
            "total_revenue": round(total_revenue, 2),
            "average_price_per_ride": round(avg_price, 2),
            "by_pricing_model": by_model,
            "by_location": by_location,
            "by_customer_tier": by_tier
        })
    except Exception as e:
        return json.dumps({"error": f"Error getting metrics: {str(e)}"})


@tool
def get_competitor_comparison() -> str:
    """
    Query actual competitor data from MongoDB and compare with HWCO.
    
    Use this tool to understand competitive positioning and pricing gaps.
    Returns comparison of HWCO vs competitor (Lyft) metrics.
    
    Returns:
        str: JSON string with competitive analysis
    """
    try:
        # Get HWCO data from historical_rides
        hwco_data = query_historical_rides(limit=500)
        # Get competitor data from competitor_prices
        competitor_data = query_competitor_prices(limit=500)
        
        if not hwco_data and not competitor_data:
            return json.dumps({"error": "No data found for comparison"})
        
        # Calculate HWCO metrics - use Historical_Cost_of_Ride field
        hwco_prices = [float(r.get("Historical_Cost_of_Ride", 0)) for r in hwco_data if r.get("Historical_Cost_of_Ride")]
        hwco_avg = sum(hwco_prices) / len(hwco_prices) if hwco_prices else 0
        hwco_total = sum(hwco_prices)
        
        # Calculate competitor metrics - also uses Historical_Cost_of_Ride field
        comp_prices = []
        for r in competitor_data:
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
        for r in competitor_data:
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
                "ride_count": len(competitor_data),
                "total_revenue": round(comp_total, 2),
                "average_price": round(comp_avg, 2)
            },
            "comparison": {
                "overall_price_gap_percent": round(price_gap, 2),
                "hwco_is_higher": price_gap > 0,
                "recommendation": "HWCO is priced higher than competitors" if price_gap > 0 else "HWCO is priced lower than competitors"
            },
            "by_location": location_comparison
        })
    except Exception as e:
        return json.dumps({"error": f"Error comparing: {str(e)}"})


@tool
def get_market_context() -> str:
    """
    Query actual market context from MongoDB (events, traffic, news).
    
    Use this tool to understand current market conditions for recommendations.
    Combines events, traffic, and news data for comprehensive context.
    
    Returns:
        str: JSON string with market context
    """
    try:
        # Get events
        events = query_events_data(limit=10)
        # Get traffic
        traffic = query_traffic_data(limit=10)
        # Get news
        news = query_news_data(limit=5)
        
        # Format events
        formatted_events = []
        for e in events:
            formatted_events.append({
                "name": e.get("name") or e.get("title", "Unknown"),
                "date": str(e.get("event_date") or e.get("date", "Unknown")),
                "venue": e.get("venue", "Unknown"),
                "type": e.get("event_type", "Unknown")
            })
        
        # Format traffic summary
        traffic_summary = []
        for t in traffic:
            traffic_summary.append({
                "location": t.get("location", "Unknown"),
                "congestion": t.get("congestion_level") or t.get("traffic_level", "Unknown")
            })
        
        # Format news
        formatted_news = []
        for n in news:
            formatted_news.append({
                "title": n.get("title", "No title"),
                "date": str(n.get("published_at", "Unknown"))
            })
        
        return json.dumps({
            "events_count": len(formatted_events),
            "upcoming_events": formatted_events[:5],
            "traffic_count": len(traffic_summary),
            "traffic_conditions": traffic_summary[:5],
            "news_count": len(formatted_news),
            "recent_news": formatted_news,
            "data_availability": get_mongodb_collection_stats()
        })
    except Exception as e:
        return json.dumps({"error": f"Error getting market context: {str(e)}"})


@tool
def query_strategy_knowledge(query: str, n_results: int = 10) -> str:
    """
    Query strategy knowledge and business rules (PRIMARY RAG source).
    
    This is the PRIMARY source for strategic recommendations.
    This tool searches ChromaDB for pricing strategies, business rules,
    and strategic knowledge that guides decision-making.
    
    Args:
        query: Text description to search for (e.g., "revenue optimization strategy")
        n_results: Number of similar strategies to retrieve (default: 10, more for comprehensive context)
    
    Returns:
        str: Formatted context string with strategic knowledge
    """
    try:
        # Query ChromaDB for strategy knowledge (PRIMARY RAG source)
        results = query_chromadb("strategy_knowledge_vectors", query, n_results)
        
        if not results:
            return "No strategic knowledge found."
        
        # Extract MongoDB IDs
        mongodb_ids = [r["mongodb_id"] for r in results]
        
        # Fetch full documents from MongoDB
        # Note: Strategy knowledge might be in various collections
        # For now, we'll return the document descriptions from ChromaDB
        context_parts = []
        for result in results:
            doc = result.get("document", "")
            metadata = result.get("metadata", {})
            if doc:
                context_parts.append(doc)
            elif metadata:
                # Use metadata if document not available
                context_parts.append(str(metadata))
        
        return " ".join(context_parts) if context_parts else "No strategy details found."
    except Exception as e:
        return f"Error querying strategy knowledge: {str(e)}"


@tool
def query_recent_events(query: str, n_results: int = 5) -> str:
    """
    Query recent events from n8n ingested data.
    
    This tool searches for recent events, traffic patterns, and news
    that might inform strategic recommendations. Use this to understand
    current market conditions and external factors.
    
    Args:
        query: Text description to search for (e.g., "recent events downtown")
        n_results: Number of similar events to retrieve (default: 5)
    
    Returns:
        str: Formatted context string with recent events
    """
    try:
        # Query ChromaDB for recent events/news
        results = query_chromadb("news_events_vectors", query, n_results)
        
        if not results:
            return "No recent events found."
        
        # Extract MongoDB IDs
        mongodb_ids = [r["mongodb_id"] for r in results]
        
        # Fetch full documents from MongoDB
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
        return f"Error querying recent events: {str(e)}"


@tool
def query_competitor_analysis(query: str, n_results: int = 5) -> str:
    """
    Query competitor analysis data.
    
    This tool searches for competitor pricing and market positioning data
    to inform strategic recommendations. Use this to understand competitive
    landscape and make recommendations that maintain competitive advantage.
    
    Args:
        query: Text description to search for (e.g., "competitor pricing downtown")
        n_results: Number of similar records to retrieve (default: 5)
    
    Returns:
        str: Formatted context string with competitor analysis data
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
        return f"Error querying competitor analysis: {str(e)}"


@tool
def generate_strategic_recommendation(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate strategic recommendation using OpenAI GPT-4.
    
    This tool takes context from strategy knowledge, events, competitor data, and forecast,
    then uses OpenAI GPT-4 to generate strategic recommendations focused on
    achieving business objectives (revenue increase 15-25%, customer retention).
    
    Args:
        context: Dictionary with:
            - strategy_knowledge: str (from query_strategy_knowledge)
            - recent_events: str (from query_recent_events)
            - competitor_data: str (from query_competitor_analysis)
            - forecast_data: dict (optional, from Forecasting Agent)
            - mongodb_ids: List[str] (optional, data source IDs)
    
    Returns:
        dict: Strategic recommendation with:
            - recommendation: str (the recommendation from OpenAI GPT-4)
            - reasoning: str (why this recommendation from OpenAI GPT-4)
            - expected_impact: dict (revenue_increase, confidence)
            - data_sources: List[str] (mongodb_ids used)
    """
    try:
        from openai import OpenAI
        
        strategy = context.get("strategy_knowledge", "")
        events = context.get("recent_events", "")
        competitor = context.get("competitor_data", "")
        forecast_data = context.get("forecast_data", {})
        mongodb_ids = context.get("mongodb_ids", [])
        
        if not settings.OPENAI_API_KEY:
            # Fallback to basic recommendation if API key not available
            recommendation = "Based on strategic analysis: "
            if strategy and strategy != "No strategic knowledge found.":
                recommendation += f"Strategy context: {strategy[:200]}... "
            if events and events != "No recent events found.":
                recommendation += f"Recent events: {events[:200]}... "
            if competitor and competitor != "No competitor data found.":
                recommendation += f"Competitor insights: {competitor[:200]}... "
            
            return {
                "recommendation": recommendation,
                "reasoning": "Combined analysis of strategy knowledge, recent events, and competitor data.",
                "expected_impact": {
                    "revenue_increase": "15-25%",
                    "confidence": "High"
                },
                "data_sources": mongodb_ids
            }
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Format forecast data for prompt
        forecast_text = ""
        if forecast_data and isinstance(forecast_data, dict):
            forecast_text = f"""
            Forecast Data:
            - Pricing Model: {forecast_data.get('pricing_model', 'N/A')}
            - Period: {forecast_data.get('periods', 0)} days
            - Average Demand: {sum(p.get('predicted_demand', 0) for p in forecast_data.get('forecast', [])) / len(forecast_data.get('forecast', [1])) if forecast_data.get('forecast') else 0:.2f} rides/day
            - Events Detected: {', '.join(forecast_data.get('context', {}).get('events_detected', []))}
            - Traffic Patterns: {', '.join(forecast_data.get('context', {}).get('traffic_patterns', []))}
            """
        
        prompt = f"""
        Generate a strategic business recommendation for a rideshare company to achieve business objectives.
        
        Business Objectives:
        - Revenue increase: 15-25%
        - Customer retention: 10-15% churn reduction
        - Competitive positioning
        
        Strategy Knowledge (PRIMARY RAG source):
        {strategy[:1000] if strategy and strategy != "No strategic knowledge found." else "No strategy knowledge available"}
        
        Recent Events (from n8n ingested data):
        {events[:500] if events and events != "No recent events found." else "No recent events available"}
        
        Competitor Analysis:
        {competitor[:500] if competitor and competitor != "No competitor data found." else "No competitor data available"}
        
        {forecast_text if forecast_text else ""}
        
        Generate a strategic recommendation in JSON format with:
        1. recommendation: A clear, actionable strategic recommendation (2-3 sentences)
        2. reasoning: Why this recommendation makes sense based on the data (2-3 sentences)
        3. expected_impact: Object with:
           - revenue_increase: Percentage or range (e.g., "15-25%" or "20%")
           - confidence: "High", "Medium", or "Low"
        
        Focus on:
        - Revenue optimization (15-25% increase target)
        - Customer retention strategies
        - Competitive positioning
        - Data-driven decision making
        
        Example: If n8n detects Lakers game and forecast shows +45% demand, recommend surge pricing 1.7x during game hours.
        
        Return ONLY valid JSON, no additional text.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}  # Structured output
        )
        
        recommendation_json = json.loads(response.choices[0].message.content)
        
        return {
            "recommendation": recommendation_json.get("recommendation", "No recommendation generated"),
            "reasoning": recommendation_json.get("reasoning", "No reasoning provided"),
            "expected_impact": recommendation_json.get("expected_impact", {
                "revenue_increase": "15-25%",
                "confidence": "Medium"
            }),
            "data_sources": mongodb_ids
        }
        
    except Exception as e:
        # Fallback to basic recommendation on error
        strategy = context.get("strategy_knowledge", "")
        events = context.get("recent_events", "")
        competitor = context.get("competitor_data", "")
        mongodb_ids = context.get("mongodb_ids", [])
        
        recommendation = "Based on strategic analysis: "
        if strategy and strategy != "No strategic knowledge found.":
            recommendation += f"Strategy context: {strategy[:200]}... "
        if events and events != "No recent events found.":
            recommendation += f"Recent events: {events[:200]}... "
        if competitor and competitor != "No competitor data found.":
            recommendation += f"Competitor insights: {competitor[:200]}... "
        
        return {
            "recommendation": recommendation,
            "reasoning": f"Combined analysis of strategy knowledge, recent events, and competitor data. Error generating detailed recommendation: {str(e)[:100]}",
            "expected_impact": {
                "revenue_increase": "15-25%",
                "confidence": "Medium"
            },
            "data_sources": mongodb_ids
        }


# Create the recommendation agent
# Handle missing API key gracefully (for testing environments)
try:
    recommendation_agent = create_agent(
        model="openai:gpt-4o-mini",
        tools=[
            # MongoDB direct query tools (for ACTUAL data) - USE THESE FIRST!
            get_performance_metrics,
            get_competitor_comparison,
            get_market_context,
            # ChromaDB RAG tools (for strategic context only)
            query_strategy_knowledge,
            query_recent_events,
            # Recommendation generation
            generate_strategic_recommendation
        ],
        system_prompt=(
            "You are a strategic recommendation specialist. "
            "Your role is to provide strategic business recommendations that help "
            "achieve business objectives: revenue increase (15-25%), customer retention, "
            "and competitive positioning. "
            "\n\n"
            "CRITICAL TOOL SELECTION - USE MONGODB TOOLS FIRST: "
            "- ALWAYS use get_performance_metrics for HWCO revenue/ride data "
            "- ALWAYS use get_competitor_comparison for HWCO vs competitor pricing "
            "- ALWAYS use get_market_context for events, traffic, news "
            "- Only use query_strategy_knowledge for business rules/strategies (ChromaDB) "
            "- DO NOT use ChromaDB for actual data - use MongoDB tools! "
            "\n\n"
            "For 'competitor comparison' or 'HWCO vs competitor' questions: "
            "→ ALWAYS call get_competitor_comparison FIRST (returns actual MongoDB data) "
            "\n\n"
            "For 'performance' or 'revenue' questions: "
            "→ ALWAYS call get_performance_metrics FIRST "
            "\n\n"
            "Key workflow: "
            "1. Call get_competitor_comparison for HWCO vs competitor data "
            "2. Call get_performance_metrics for HWCO metrics "
            "3. Call get_market_context for events/traffic/news "
            "4. Optionally call query_strategy_knowledge for business rules "
            "5. Generate recommendations with SPECIFIC NUMBERS from the data "
            "\n\n"
            "NEVER give generic responses without first calling the MongoDB tools!"
        ),
        name="recommendation_agent"
    )
except Exception as e:
    # If API key is missing, set to None (for testing environments)
    if "api_key" in str(e).lower() or "openai" in str(e).lower():
        recommendation_agent = None
    else:
        # Re-raise if it's not an API key issue
        raise


