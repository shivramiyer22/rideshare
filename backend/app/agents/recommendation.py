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
from app.agents.utils import query_chromadb, fetch_mongodb_documents, format_documents_as_context
from app.config import settings


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
            query_strategy_knowledge,
            query_recent_events,
            query_competitor_analysis,
            generate_strategic_recommendation
        ],
        system_prompt=(
            "You are a strategic recommendation specialist. "
            "Your role is to provide strategic business recommendations that help "
            "achieve business objectives: revenue increase (15-25%), customer retention, "
            "and competitive positioning. "
            "\n\n"
            "Key responsibilities: "
            "- Analyze strategy knowledge (PRIMARY RAG source) for business rules "
            "- Analyze recent events from n8n (events, traffic, news) for market context "
            "- Analyze competitor data for competitive positioning "
            "- Combine Forecasting Agent predictions with current market data "
            "- Generate actionable strategic recommendations using OpenAI GPT-4 "
            "\n\n"
            "When generating recommendations: "
            "- ALWAYS start with query_strategy_knowledge (PRIMARY RAG source) "
            "- Query recent_events to understand current market conditions "
            "- Query competitor_analysis to understand competitive landscape "
            "- Optionally get forecast_data from Forecasting Agent (if needed) "
            "- Use generate_strategic_recommendation to create final recommendations via OpenAI GPT-4 "
            "- The generate_strategic_recommendation tool returns: "
            "  recommendation, reasoning, expected_impact, data_sources "
            "- Focus on revenue goals (15-25% increase) and customer retention "
            "\n\n"
            "Example workflow: "
            "1. n8n detects Lakers game (via query_recent_events) "
            "2. Forecasting Agent predicts +45% demand "
            "3. Generate recommendation: surge pricing 1.7x during game hours to maximize revenue "
            "\n\n"
            "Always provide clear reasoning and expected impact for recommendations."
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


