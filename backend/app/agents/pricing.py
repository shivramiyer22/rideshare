"""
Pricing Agent - Handles pricing calculations and recommendations.

This agent calculates prices and explains pricing decisions using:
- PricingEngine for actual calculations
- Similar past scenarios from ChromaDB for context
- Business rules and strategies from ChromaDB

The agent provides:
- Price calculations with detailed breakdowns
- Natural language explanations of pricing decisions
- Recommendations based on similar past scenarios
"""
from langchain.agents import create_agent
from langchain.tools import tool
from typing import Dict, Any
import asyncio
import json
from app.agents.utils import query_chromadb, fetch_mongodb_documents, format_documents_as_context
from app.pricing_engine import PricingEngine
from app.config import settings


# Initialize PricingEngine instance
pricing_engine = PricingEngine()


def generate_price_explanation(price_result: Dict[str, Any], similar_scenarios: str = "") -> str:
    """
    Generate natural language explanation of price calculation using OpenAI GPT-4.
    
    Args:
        price_result: Price calculation result from PricingEngine
        similar_scenarios: Context string with similar past scenarios
    
    Returns:
        str: Natural language explanation of the price
    """
    try:
        from openai import OpenAI
        
        if not settings.OPENAI_API_KEY:
            # Fallback to basic explanation if API key not available
            return (
                f"The final price is ${price_result.get('final_price', 0):.2f}. "
                f"Pricing model: {price_result.get('pricing_model', 'UNKNOWN')}. "
                f"Revenue score: {price_result.get('revenue_score', 0):.2f}."
            )
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Build breakdown description
        breakdown = price_result.get("breakdown", {})
        breakdown_text = ""
        if breakdown:
            breakdown_text = "\n".join([
                f"- {key}: {value}" for key, value in breakdown.items()
            ])
        
        prompt = f"""
        Explain this ride pricing calculation in natural language for a customer.
        
        Price Calculation Result:
        - Final Price: ${price_result.get('final_price', 0):.2f}
        - Pricing Model: {price_result.get('pricing_model', 'UNKNOWN')}
        - Revenue Score: {price_result.get('revenue_score', 0):.2f}
        
        Price Breakdown:
        {breakdown_text if breakdown_text else "No breakdown available"}
        
        Similar Past Scenarios:
        {similar_scenarios[:500] if similar_scenarios else "No similar scenarios found"}
        
        Provide a clear, customer-friendly explanation that:
        1. Explains why the price is what it is
        2. Describes how multipliers affected the price (if applicable)
        3. Compares to similar past scenarios (if available)
        4. Explains the business rationale
        5. Is concise but informative (2-3 sentences)
        
        Write in a professional but friendly tone.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        # Fallback to basic explanation on error
        return (
            f"The final price is ${price_result.get('final_price', 0):.2f}. "
            f"Pricing model: {price_result.get('pricing_model', 'UNKNOWN')}. "
            f"Error generating detailed explanation: {str(e)[:100]}"
        )


@tool
def query_similar_pricing_scenarios(query: str, n_results: int = 5) -> str:
    """
    Query similar past pricing scenarios for context.
    
    This tool searches ChromaDB for similar past rides with pricing information.
    Use this to understand how prices were calculated in similar situations
    and to explain pricing decisions to users.
    
    Args:
        query: Text description to search for (e.g., "urban evening rush premium Gold")
        n_results: Number of similar scenarios to retrieve (default: 5)
    
    Returns:
        str: Formatted context string with similar pricing scenarios
    """
    try:
        # Query ChromaDB for similar ride scenarios
        results = query_chromadb("ride_scenarios_vectors", query, n_results)
        
        if not results:
            return "No similar pricing scenarios found."
        
        # Extract MongoDB IDs
        mongodb_ids = [r["mongodb_id"] for r in results]
        
        # Fetch full documents from MongoDB
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
        return f"Error querying pricing scenarios: {str(e)}"


@tool
def query_pricing_strategies(query: str, n_results: int = 5) -> str:
    """
    Query pricing strategies and business rules.
    
    This tool searches ChromaDB for pricing strategies and business rules.
    Use this to understand pricing policies and make informed recommendations.
    
    Args:
        query: Text description to search for (e.g., "surge pricing strategy")
        n_results: Number of similar strategies to retrieve (default: 5)
    
    Returns:
        str: Formatted context string with pricing strategies
    """
    try:
        # Query ChromaDB for strategy knowledge
        results = query_chromadb("strategy_knowledge_vectors", query, n_results)
        
        if not results:
            return "No pricing strategies found."
        
        # Extract MongoDB IDs
        mongodb_ids = [r["mongodb_id"] for r in results]
        
        # Fetch full documents from MongoDB
        # Note: Strategy knowledge might be in various collections
        # For now, we'll return the metadata/descriptions from ChromaDB
        context_parts = []
        for result in results:
            context_parts.append(result.get("document", ""))
        
        return " ".join(context_parts) if context_parts else "No strategy details found."
    except Exception as e:
        return f"Error querying pricing strategies: {str(e)}"


@tool
def calculate_price_with_explanation(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate price using PricingEngine and return with natural language explanation.
    
    This tool uses the PricingEngine to calculate the actual price,
    then uses OpenAI GPT-4 to generate a natural language explanation.
    
    Args:
        order_data: Order data dictionary with:
            - pricing_model: "CONTRACTED", "STANDARD", or "CUSTOM"
            - distance: Distance in miles
            - duration: Duration in minutes
            - time_of_day: "morning_rush", "evening_rush", "night", "regular"
            - location_type: "urban_high_demand", "urban_regular", "suburban"
            - vehicle_type: "premium" or "economy"
            - supply_demand_ratio: float (drivers/riders)
            - customer: {"loyalty_tier": "Gold", "Silver", or "Regular"}
            - fixed_price: float (only for CONTRACTED)
    
    Returns:
        dict: Price calculation result with:
            - final_price: float
            - breakdown: dict with multipliers
            - explanation: string (natural language from OpenAI GPT-4)
            - pricing_model: string
            - revenue_score: float
    """
    try:
        # Use PricingEngine to calculate price
        result = pricing_engine.calculate_price(order_data)
        
        # Query similar scenarios for context
        similar_scenarios = ""
        try:
            # Build query from order data
            query_parts = []
            if order_data.get("location_type"):
                query_parts.append(order_data["location_type"].replace("_", " "))
            if order_data.get("time_of_day"):
                query_parts.append(order_data["time_of_day"].replace("_", " "))
            if order_data.get("vehicle_type"):
                query_parts.append(order_data["vehicle_type"])
            if order_data.get("customer", {}).get("loyalty_tier"):
                query_parts.append(order_data["customer"]["loyalty_tier"])
            
            if query_parts:
                query = " ".join(query_parts)
                similar_scenarios = query_similar_pricing_scenarios(query, n_results=3)
        except Exception as e:
            # If query fails, continue without similar scenarios
            similar_scenarios = ""
        
        # Generate natural language explanation using OpenAI GPT-4
        explanation = generate_price_explanation(result, similar_scenarios)
        
        # Return exact format as specified
        return {
            "final_price": result.get("final_price", 0.0),
            "breakdown": result.get("breakdown", {}),
            "explanation": explanation,
            "pricing_model": result.get("pricing_model", "UNKNOWN"),
            "revenue_score": result.get("revenue_score", 0.0)
        }
    except Exception as e:
        return {
            "error": f"Error calculating price: {str(e)}",
            "final_price": 0.0,
            "breakdown": {},
            "explanation": f"Error calculating price: {str(e)}",
            "pricing_model": order_data.get("pricing_model", "UNKNOWN"),
            "revenue_score": 0.0
        }


# Create the pricing agent
# Handle missing API key gracefully (for testing environments)
try:
    pricing_agent = create_agent(
        model="openai:gpt-4o-mini",
        tools=[
            query_similar_pricing_scenarios,
            query_pricing_strategies,
            calculate_price_with_explanation
        ],
        system_prompt=(
            "You are a pricing specialist. "
            "Your role is to calculate optimal prices, explain pricing decisions, "
            "and recommend pricing strategies. "
            "\n\n"
            "Key responsibilities: "
            "- Calculate prices using PricingEngine for accurate results "
            "- Explain price breakdowns in natural language using OpenAI GPT-4 "
            "- Reference similar past scenarios to justify pricing decisions "
            "- Use business rules and strategies to guide recommendations "
            "\n\n"
            "When calculating prices: "
            "- Use calculate_price_with_explanation tool for actual calculations "
            "  (this tool automatically generates natural language explanations using OpenAI GPT-4) "
            "- Query similar_pricing_scenarios to find comparable past rides "
            "- Query pricing_strategies to understand business rules "
            "- The calculate_price_with_explanation tool returns: "
            "  final_price, breakdown, explanation (natural language), pricing_model, revenue_score "
            "\n\n"
            "Always provide clear, customer-friendly explanations that reference similar past scenarios "
            "and explain the business rationale behind pricing decisions."
        ),
        name="pricing_agent"
    )
except Exception as e:
    # If API key is missing, set to None (for testing environments)
    if "api_key" in str(e).lower() or "openai" in str(e).lower():
        pricing_agent = None
    else:
        # Re-raise if it's not an API key issue
        raise


