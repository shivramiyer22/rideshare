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
        "You are a chatbot orchestrator that routes user queries to specialist agents. "
        "Use OpenAI function calling to intelligently determine which agent(s) should handle each query. "
        "\n\n"
        "ROUTING RULES (ALWAYS route to an agent - NEVER answer without routing): "
        "\n"
        "Analysis Agent - for: "
        "  - Revenue, analytics, KPIs, data analysis "
        "  - Historical data queries (monthly statistics, averages, totals) "
        "  - Competitor comparison and competitive analysis "
        "  - Events, traffic, news data analysis "
        "  - Customer segments, location patterns "
        "  - Segment Dynamic Pricing Report queries (forecast pricing for all/specific segments) "
        "\n"
        "Pricing Agent - for: "
        "  - Price calculations for NEW rides "
        "  - Price ESTIMATIONS ('what would this cost?', 'price preview') "
        "  - Pricing explanations and breakdowns "
        "  - Competitor pricing analysis "
        "  - Historical pricing patterns "
        "  - Segment-based price estimates (Urban/Suburban/Rural, Gold/Silver/Regular, Premium/Economy) "
        "\n"
        "Forecasting Agent - for: "
        "  - Demand forecasts, predictions "
        "  - ML/Prophet forecasts "
        "  - Trend analysis "
        "\n"
        "Recommendation Agent - for: "
        "  - Strategic recommendations "
        "  - Business advice "
        "  - Competitive positioning "
        "  - HWCO vs competitor comparisons "
        "\n\n"
        "NEW: Price Estimation Queries "
        "- When user asks 'what would a ride cost?' or 'price preview' → Route to Pricing Agent "
        "- Examples: 'How much for Premium in Urban?', 'What's the price for Gold members?' "
        "- Pricing Agent will use segment analysis to provide comprehensive estimates "
        "- No order is created - this is just estimation/preview "
        "\n\n"
        "IMPORTANT: "
        "- For 'competitor' questions → Try BOTH Analysis Agent AND Pricing Agent "
        "- For 'HWCO vs competitor' → Route to Recommendation Agent (has get_competitor_comparison tool) "
        "- For historical/past data → Analysis Agent "
        "- For price estimates/preview → Pricing Agent "
        "- ALWAYS call at least one agent - never give a generic response without data "
        "\n\n"
        "Multi-Agent Coordination: "
        "- Some queries may need multiple agents "
        "- Call them sequentially and synthesize their responses "
        "- Combine responses into a coherent answer "
        "\n\n"
        "ALWAYS route to the appropriate agent(s). Do NOT give generic responses without calling tools."
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


