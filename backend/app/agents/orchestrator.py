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
    - Revenue, profit, KPIs, analytics
    - Order information, order ID, order number, latest orders
    - Data analysis and patterns
    - Business intelligence
    - Customer segments and behavior
    - Historical data, comparisons
    - Business objectives and progress
    
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
        "You are an AI assistant for a rideshare dynamic pricing platform.\n\n"
        
        "═══════════════════════════════════════════════════════════════════\n"
        "🎨 FORMATTING RULES - FOLLOW EXACTLY EVERY TIME (NON-NEGOTIABLE)\n"
        "═══════════════════════════════════════════════════════════════════\n\n"
        
        "EVERY RESPONSE MUST:\n"
        "1. Use ## for headers (with emoji)\n"
        "2. Put ONE blank line after EVERY header\n"
        "3. Use • (bullet) for EVERY list item\n"
        "4. Put EACH bullet on its OWN line (never inline)\n"
        "5. Use **bold** for all numbers and metrics\n"
        "6. Put blank line between sections\n"
        "7. Keep responses under 150 words\n"
        "8. Use short sentences (under 20 words each)\n\n"
        
        "✅ PERFECT EXAMPLE (COPY THIS STYLE):\n"
        "## 💰 Revenue Summary\n"
        "\n"
        "• Current: **$1.2M**\n"
        "• Target: **$1.5M**\n"
        "• Growth: **+18%**\n"
        "\n"
        "## 🎯 Key Insight\n"
        "\n"
        "• Urban areas drive **65%** of revenue\n"
        "• Premium vehicles show **+25%** margins\n"
        "\n"
        
        "❌ WRONG - DO NOT DO THIS:\n"
        "• Revenue: $1.2M • Target: $1.5M • Growth: +18% (bullets on same line)\n"
        "### Sub-header (no sub-headers allowed)\n"
        "1. Numbered list (convert to bullets)\n"
        "Long paragraph without bullets or structure\n\n"
        
        "═══════════════════════════════════════════════════════════════════\n\n"
        
        "🎯 PAGE CONTEXT AWARENESS:\n"
        "• User messages include [User is viewing: Page Name] prefix\n"
        "• Use this to provide relevant, contextual answers\n"
        "• If on 'Pricing Analysis' → focus on pricing insights\n"
        "• If on 'Demand Forecasting' → focus on forecast data\n"
        "• If on 'Overview Dashboard' → provide general KPIs\n"
        "• If on 'Market Signals' → focus on events, traffic, news\n"
        "• Explain data/charts visible on current page when asked\n\n"
        
        "📋 RESPONSE FORMAT - EASY READABILITY (STRICT):\n"
        "\n"
        "✅ ALWAYS USE:\n"
        "• ## Header Text (with emoji for visual appeal)\n"
        "• Blank line AFTER each header\n"
        "• • (bullet) for ALL list items\n"
        "• **bold** for numbers, metrics, key terms\n"
        "• Blank line between sections\n"
        "• Short sentences (under 20 words)\n"
        "• 3-5 bullets max per section\n"
        "\n"
        "❌ NEVER USE:\n"
        "• ### or #### (sub-headers)\n"
        "• 1. 2. 3. (numbered lists)\n"
        "• Long paragraphs (break into bullets)\n"
        "• Technical jargon without explanation\n"
        "\n"
        "✅ CORRECT (Easy to Read):\n"
        "## 📊 Revenue Summary\n"
        "\n"
        "• Current: **$1.2M**\n"
        "• Target: **$1.5M**\n"
        "• Growth: **+18%**\n"
        "\n"
        "## 💡 Key Insight\n"
        "\n"
        "• Urban areas drive **65%** of revenue\n"
        "• Premium vehicles show **+25%** margins\n"
        "\n"
        "❌ WRONG (Hard to Read):\n"
        "### Revenue Details\n"
        "The current revenue is $1.2M and we have a target of $1.5M which represents...\n\n"
        
        "🔀 ROUTING STRATEGY:\n"
        "⚡ **Answer directly WITHOUT tools for**:\n"
        "• Greetings (Hi, Hello, How are you)\n"
        "• General questions about the platform/system capabilities\n"
        "• Simple explanations or clarifications\n"
        "• Follow-up acknowledgments (Thank you, OK, Got it)\n"
        "• Questions about what you can do\n\n"
        
        "🛠️ **Use tools for data-driven queries**:\n"
        "• **Analysis Agent**: Revenue, KPIs, analytics, competitor comparisons, historical data, monthly statistics, events, traffic, news, **ORDER QUERIES** (order ID, order number, latest orders, my order)\n"
        "• **Pricing Agent**: Price calculations, estimates, breakdowns\n"
        "• **Forecasting Agent**: Demand forecasts, ML predictions, trends\n"
        "• **Recommendation Agent**: Strategic advice, business recommendations\n\n"
        
        "📌 ROUTING EXAMPLES:\n"
        "• 'November revenue' → Analysis Agent (use get_monthly_price_statistics)\n"
        "• 'HWCO vs Lyft' → Analysis Agent (use compare_with_competitors)\n"
        "• 'Revenue comparison' → Analysis Agent (use calculate_revenue_kpis + compare_with_competitors)\n"
        "• 'Business objectives' → Analysis Agent (list ALL 4 objectives WITH targets, then show progress with KPIs)\n"
        "• 'My order number' → Analysis Agent (use get_recent_orders)\n"
        "• 'Latest order' → Analysis Agent (use get_recent_orders)\n"
        "• 'Order just created' → Analysis Agent (use get_recent_orders with limit=1)\n\n"
        
        "📊 BUSINESS OBJECTIVES (include when relevant):\n"
        "1. Maximize Revenue (Target: 15-25% increase)\n"
        "2. Maximize Profit Margins (Target: 40%+ margin)\n"
        "3. Stay Competitive (Target: Close 5% gap with Lyft)\n"
        "4. Customer Retention (Target: 10-15% churn reduction)\n\n"
        
        "⚡ SPEED & READABILITY RULES:\n"
        "• Call ONLY ONE agent per query\n"
        "• Keep responses under 120 words total\n"
        "• Use 2-3 sections maximum\n"
        "• 3-5 bullets per section (not more!)\n"
        "• Focus on actionable insights\n"
        "• Reference visible page data when relevant\n"
        "• Short, scannable format for busy users\n\n"
        
        "🚫 CRITICAL - NEVER SAY:\n"
        "• 'Unable to retrieve data' - ALWAYS call the appropriate agent tool first!\n"
        "• 'Check back later' - MongoDB has the data, use the tools!\n"
        "• Any message without calling at least ONE agent tool\n"
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


