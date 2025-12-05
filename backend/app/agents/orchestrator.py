"""
Chatbot Orchestrator Agent - Coordinates chatbot interactions and routing.

This agent acts as a traffic controller for the chatbot system.
When a user asks a question, the orchestrator determines which specialist agent
should handle it based on the query intent.

Routing examples:
- "What's our revenue?" → Analysis Agent
- "Calculate price for..." → Pricing Agent
- "Predict demand for..." → Forecasting Agent
- "What should we do about..." → Recommendation Agent

The orchestrator maintains conversation context using LangGraph checkpointer,
allowing it to remember previous messages in the conversation.
"""
from langchain.agents import create_agent
from langchain.tools import tool
from typing import Dict, Any
from langgraph.checkpoint.memory import InMemorySaver
import logging

# Setup logging
logger = logging.getLogger(__name__)


@tool
def route_to_analysis_agent(query: str, context: Dict[str, Any] = None) -> str:
    """
    Route query to Analysis Agent for data analysis and insights.
    
    Use this for queries about:
    - Revenue, profit, KPIs
    - Data analysis and patterns
    - Business intelligence
    - Customer segments and behavior
    
    Args:
        query: User query about analytics or data analysis
        context: Optional conversation context
    
    Returns:
        str: Analysis Agent response
    """
    try:
        from app.agents.analysis import analysis_agent
        
        # Prepare messages with context
        messages = [{"role": "user", "content": query}]
        if context:
            # Add context as system message if provided
            context_str = str(context) if not isinstance(context, str) else context
            messages.insert(0, {"role": "system", "content": f"Context: {context_str}"})
        
        # Invoke analysis agent
        result = analysis_agent.invoke({"messages": messages})
        
        # Extract response from agent
        if result.get("messages") and len(result["messages"]) > 0:
            return result["messages"][-1].content
        return "Analysis Agent processed the query but returned no response."
    except Exception as e:
        return f"Error routing to Analysis Agent: {str(e)}"


@tool
def route_to_pricing_agent(query: str, context: Dict[str, Any] = None) -> str:
    """
    Route query to Pricing Agent for price calculations, estimations, and explanations.
    
    Use this for queries about:
    - Price calculations and exact pricing
    - Price ESTIMATIONS ("what would this cost?", "price preview")
    - Pricing explanations and breakdowns
    - Pricing strategies and competitor comparisons
    - Historical pricing data
    
    NEW: Price Estimation Support
    - User asks "what would a ride cost?" → Uses estimate_ride_price tool
    - Provides segment-based estimates without creating orders
    - Combines historical baseline + forecast predictions
    
    Args:
        query: User query about pricing or price estimation
        context: Optional conversation context
    
    Returns:
        str: Pricing Agent response with calculations or estimates
    """
    try:
        from app.agents.pricing import pricing_agent
        
        # Prepare messages with context
        messages = [{"role": "user", "content": query}]
        if context:
            context_str = str(context) if not isinstance(context, str) else context
            messages.insert(0, {"role": "system", "content": f"Context: {context_str}"})
        
        # Invoke pricing agent
        result = pricing_agent.invoke({"messages": messages})
        
        # Extract response
        if result.get("messages") and len(result["messages"]) > 0:
            return result["messages"][-1].content
        return "Pricing Agent processed the query but returned no response."
    except Exception as e:
        return f"Error routing to Pricing Agent: {str(e)}"


@tool
def route_to_forecasting_agent(query: str, context: Dict[str, Any] = None) -> str:
    """
    Route query to Forecasting Agent for demand predictions.
    
    Use this for queries about:
    - Demand forecasts
    - Future predictions
    - Trend analysis
    - Prophet ML forecasts
    
    Args:
        query: User query about forecasting
        context: Optional conversation context
    
    Returns:
        str: Forecasting Agent response
    """
    try:
        from app.agents.forecasting import forecasting_agent
        
        # Prepare messages with context
        messages = [{"role": "user", "content": query}]
        if context:
            context_str = str(context) if not isinstance(context, str) else context
            messages.insert(0, {"role": "system", "content": f"Context: {context_str}"})
        
        # Invoke forecasting agent
        result = forecasting_agent.invoke({"messages": messages})
        
        # Extract response
        if result.get("messages") and len(result["messages"]) > 0:
            return result["messages"][-1].content
        return "Forecasting Agent processed the query but returned no response."
    except Exception as e:
        return f"Error routing to Forecasting Agent: {str(e)}"


@tool
def route_to_recommendation_agent(query: str, context: Dict[str, Any] = None) -> str:
    """
    Route query to Recommendation Agent for strategic advice.
    
    Use this for queries about:
    - Strategic recommendations
    - Business advice
    - Action plans
    - Optimization suggestions
    
    Args:
        query: User query about recommendations
        context: Optional conversation context
    
    Returns:
        str: Recommendation Agent response
    """
    try:
        from app.agents.recommendation import recommendation_agent
        
        # Prepare messages with context
        messages = [{"role": "user", "content": query}]
        if context:
            context_str = str(context) if not isinstance(context, str) else context
            messages.insert(0, {"role": "system", "content": f"Context: {context_str}"})
        
        # Invoke recommendation agent
        result = recommendation_agent.invoke({"messages": messages})
        
        # Extract response
        if result.get("messages") and len(result["messages"]) > 0:
            return result["messages"][-1].content
        return "Recommendation Agent processed the query but returned no response."
    except Exception as e:
        return f"Error routing to Recommendation Agent: {str(e)}"


# Create checkpointer for conversation context
# This allows the orchestrator to remember previous messages
orchestrator_checkpointer = InMemorySaver()

# Create the orchestrator agent with checkpointer for conversation memory
# Handle missing API key gracefully (for testing environments)
try:
    orchestrator_agent = create_agent(
        model="openai:gpt-4o-mini",
        tools=[
            route_to_analysis_agent,
            route_to_pricing_agent,
            route_to_forecasting_agent,
            route_to_recommendation_agent
        ],
        checkpointer=orchestrator_checkpointer,  # Enable conversation memory
        system_prompt=(
        "You are an AI assistant for a rideshare dynamic pricing platform. "
        "Route queries to specialist agents and present responses in a STRUCTURED, ORGANIZED format. "
        "\n\n"
        "📋 RESPONSE FORMAT REQUIREMENTS:\n"
        "1. Use clear section headers with emojis\n"
        "2. Present data in bullet points or numbered lists\n"
        "3. Keep responses concise - max 3-4 key points per section\n"
        "4. Use newlines to separate sections\n"
        "5. Highlight key metrics with **bold**\n"
        "\n"
        "Example Structure:\n"
        "## 📊 Key Findings\n"
        "• Point 1\n"
        "• Point 2\n"
        "\n"
        "## 💡 Insights\n"
        "• Key insight here\n"
        "\n\n"
        "🔀 ROUTING RULES (ALWAYS route - NEVER answer without calling a tool):\n"
        "\n"
        "📊 Analysis Agent:\n"
        "  • Revenue, KPIs, analytics\n"
        "  • Historical data, statistics\n"
        "  • Competitor comparisons\n"
        "  • Events, news analysis\n"
        "  • Segment reports\n"
        "\n"
        "💰 Pricing Agent:\n"
        "  • Price calculations\n"
        "  • Price estimations\n"
        "  • Pricing breakdowns\n"
        "  • Segment pricing\n"
        "\n"
        "📈 Forecasting Agent:\n"
        "  • Demand forecasts\n"
        "  • ML predictions\n"
        "  • Trend analysis\n"
        "\n"
        "💡 Recommendation Agent:\n"
        "  • Strategic advice\n"
        "  • Business recommendations\n"
        "  • HWCO vs competitor\n"
        "\n\n"
        "⚠️ CRITICAL RULES:\n"
        "• ALWAYS call at least one agent\n"
        "• Format agent responses with clear sections\n"
        "• Be concise - eliminate verbose explanations\n"
        "• Use bullet points, not paragraphs\n"
        "• Multi-agent queries: call sequentially, then synthesize\n"
        ),
        name="orchestrator_agent"
    )
    logger.info("✓ Orchestrator agent initialized successfully")
except Exception as e:
    # If API key is missing, set to None (for testing environments)
    error_msg = str(e).lower()
    if "api_key" in error_msg or "openai" in error_msg or "authentication" in error_msg:
        logger.warning(
            "⚠️  Orchestrator agent could not be initialized: OPENAI_API_KEY not configured or invalid. "
            "Chatbot endpoints will return 503 Service Unavailable."
        )
        orchestrator_agent = None
    else:
        # Re-raise if it's not an API key issue
        logger.error(f"Failed to initialize orchestrator agent: {e}")
        raise


