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
    Route query to Pricing Agent for price calculations and explanations.
    
    Use this for queries about:
    - Price calculations
    - Pricing explanations
    - Price breakdowns
    - Pricing strategies
    
    Args:
        query: User query about pricing
        context: Optional conversation context
    
    Returns:
        str: Pricing Agent response
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
        "Routing Intelligence: "
        "- Revenue, analytics, KPIs, data analysis → Analysis Agent "
        "- Price calculations, pricing explanations, price breakdowns → Pricing Agent "
        "- Forecasts, predictions, demand forecasting, Prophet ML → Forecasting Agent "
        "- Strategic recommendations, business advice, action plans → Recommendation Agent "
        "\n\n"
        "Multi-Agent Coordination: "
        "- Some queries may need multiple agents (e.g., 'What's our revenue forecast and pricing strategy?') "
        "- When multiple agents are needed, call them sequentially and synthesize their responses "
        "- Combine responses into a coherent, comprehensive answer for the user "
        "\n\n"
        "Context Management: "
        "- Maintain conversation context across messages (you have access to previous messages) "
        "- Pass relevant context to worker agents when routing "
        "- Ensure smooth user experience with natural, helpful responses "
        "\n\n"
        "Always route queries to the appropriate agent(s) and return their responses to the user."
        ),
        name="orchestrator_agent"
    )
except Exception as e:
    # If API key is missing, set to None (for testing environments)
    if "api_key" in str(e).lower() or "openai" in str(e).lower():
        orchestrator_agent = None
    else:
        # Re-raise if it's not an API key issue
        raise


