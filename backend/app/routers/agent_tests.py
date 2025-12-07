"""
Agent Test Endpoints - Test individual agents via Swagger Docs

This module provides test endpoints for each agent:
- Pricing Agent: Test price calculations
- Analysis Agent: Test data analysis queries
- Forecasting Agent: Test demand/price forecasts
- Recommendation Agent: Test strategic recommendations

All endpoints are accessible via Swagger docs for easy testing.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents/test", tags=["Agent Tests"])


# ============================================================================
# Pricing Agent Test Endpoints
# ============================================================================

class PricingTestRequest(BaseModel):
    """Request model for Pricing Agent test."""
    pricing_model: str = Field(..., description="Pricing model: CONTRACTED, STANDARD, or CUSTOM")
    distance: float = Field(..., description="Distance in miles", example=10.5)
    duration: float = Field(..., description="Duration in minutes", example=25.0)
    time_of_day: str = Field(default="regular", description="Time of day: morning_rush, evening_rush, night, regular")
    location_type: str = Field(default="urban_regular", description="Location type: urban_high_demand, urban_regular, suburban")
    vehicle_type: str = Field(default="economy", description="Vehicle type: premium or economy")
    supply_demand_ratio: float = Field(default=0.5, description="Supply/demand ratio (0.0 to 1.0+)")
    customer: Dict[str, str] = Field(default={"loyalty_tier": "Regular"}, description="Customer info with loyalty_tier")
    fixed_price: Optional[float] = Field(None, description="Fixed price (only for CONTRACTED)")
    query: Optional[str] = Field(None, description="Optional natural language query for Pricing Agent")


class PricingTestResponse(BaseModel):
    """Response model for Pricing Agent test."""
    success: bool
    agent_response: Optional[str] = None
    calculated_price: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/pricing", response_model=PricingTestResponse, summary="Test Pricing Agent")
async def test_pricing_agent(request: PricingTestRequest):
    """
    Test Pricing Agent with sample order data.
    
    This endpoint allows you to test the Pricing Agent by providing order details.
    The agent will calculate the price using PricingEngine and provide an explanation.
    
    **Example Request:**
    ```json
    {
      "pricing_model": "STANDARD",
      "distance": 10.5,
      "duration": 25.0,
      "time_of_day": "evening_rush",
      "location_type": "urban_high_demand",
      "vehicle_type": "premium",
      "supply_demand_ratio": 0.4,
      "customer": {"loyalty_tier": "Gold"}
    }
    ```
    """
    try:
        from app.agents.pricing import pricing_agent
        
        if pricing_agent is None:
            raise HTTPException(status_code=503, detail="Pricing Agent not initialized (missing API key)")
        
        # Build order data
        order_data = {
            "pricing_model": request.pricing_model,
            "distance": request.distance,
            "duration": request.duration,
            "time_of_day": request.time_of_day,
            "location_type": request.location_type,
            "vehicle_type": request.vehicle_type,
            "supply_demand_ratio": request.supply_demand_ratio,
            "customer": request.customer
        }
        
        if request.fixed_price is not None:
            order_data["fixed_price"] = request.fixed_price
        
        # If query provided, use agent's natural language interface
        if request.query:
            messages = [{"role": "user", "content": request.query}]
            result = pricing_agent.invoke({"messages": messages})
            agent_response = result.get("messages", [])[-1].content if result.get("messages") else None
        else:
            # Use calculate_price_with_explanation tool directly
            from app.agents.pricing import calculate_price_with_explanation
            calculated_price = calculate_price_with_explanation.invoke({"order_data": order_data})
            agent_response = calculated_price.get("explanation", "Price calculated successfully")
        
        return PricingTestResponse(
            success=True,
            agent_response=agent_response,
            calculated_price=calculated_price if not request.query else None
        )
        
    except Exception as e:
        logger.error(f"Error testing Pricing Agent: {e}")
        return PricingTestResponse(
            success=False,
            error=str(e)
        )


# ============================================================================
# Analysis Agent Test Endpoints
# ============================================================================

class AnalysisTestRequest(BaseModel):
    """Request model for Analysis Agent test."""
    query: str = Field(..., description="Analysis query (e.g., 'What is the average price in November?')")
    month: Optional[str] = Field(None, description="Optional month filter (e.g., 'November')")
    pricing_model: Optional[str] = Field(None, description="Optional pricing model filter")
    location_category: Optional[str] = Field(None, description="Optional location filter")


class AnalysisTestResponse(BaseModel):
    """Response model for Analysis Agent test."""
    success: bool
    agent_response: Optional[str] = None
    error: Optional[str] = None


@router.post("/analysis", response_model=AnalysisTestResponse, summary="Test Analysis Agent")
async def test_analysis_agent(request: AnalysisTestRequest):
    """
    Test Analysis Agent with sample queries.
    
    This endpoint allows you to test the Analysis Agent with various data analysis queries.
    
    **Example Queries:**
    - "What is the average price in November?"
    - "Compare our prices with competitors"
    - "What are the revenue KPIs for last month?"
    - "Analyze customer segments by loyalty tier"
    """
    try:
        from app.agents.analysis import analysis_agent
        
        if analysis_agent is None:
            raise HTTPException(status_code=503, detail="Analysis Agent not initialized (missing API key)")
        
        # Build query with optional filters
        query = request.query
        if request.month:
            query += f" for {request.month}"
        if request.pricing_model:
            query += f" with pricing model {request.pricing_model}"
        if request.location_category:
            query += f" in {request.location_category} locations"
        
        messages = [{"role": "user", "content": query}]
        result = analysis_agent.invoke({"messages": messages})
        
        agent_response = result.get("messages", [])[-1].content if result.get("messages") else None
        
        return AnalysisTestResponse(
            success=True,
            agent_response=agent_response
        )
        
    except Exception as e:
        logger.error(f"Error testing Analysis Agent: {e}")
        return AnalysisTestResponse(
            success=False,
            error=str(e)
        )


# ============================================================================
# Forecasting Agent Test Endpoints
# ============================================================================

class ForecastingTestRequest(BaseModel):
    """Request model for Forecasting Agent test."""
    forecast_type: str = Field(default="multidimensional", description="Forecast type: 'multidimensional' or 'prophet'")
    periods: int = Field(default=30, description="Forecast period in days: 30, 60, or 90")
    pricing_model: Optional[str] = Field(None, description="Pricing model (only for 'prophet' type): CONTRACTED, STANDARD, or CUSTOM")


class ForecastingTestResponse(BaseModel):
    """Response model for Forecasting Agent test."""
    success: bool
    forecast_result: Optional[Dict[str, Any]] = None
    agent_response: Optional[str] = None
    error: Optional[str] = None


@router.post("/forecasting", response_model=ForecastingTestResponse, summary="Test Forecasting Agent")
async def test_forecasting_agent(request: ForecastingTestRequest):
    """
    Test Forecasting Agent (multi-dimensional or Prophet ML).
    
    This endpoint allows you to test the Forecasting Agent with different forecast types.
    
    **Forecast Types:**
    - **multidimensional**: Generates forecasts for 162 segments (loyalty × vehicle × demand × pricing × location)
    - **prophet**: Generates Prophet ML forecast for a specific pricing model
    
    **Example Request (Multidimensional):**
    ```json
    {
      "forecast_type": "multidimensional",
      "periods": 30
    }
    ```
    
    **Example Request (Prophet):**
    ```json
    {
      "forecast_type": "prophet",
      "periods": 30,
      "pricing_model": "STANDARD"
    }
    ```
    """
    try:
        from app.agents.forecasting import forecasting_agent, generate_multidimensional_forecast, generate_prophet_forecast
        
        if forecasting_agent is None:
            raise HTTPException(status_code=503, detail="Forecasting Agent not initialized (missing API key)")
        
        if request.forecast_type == "multidimensional":
            # Use multi-dimensional forecast tool
            result = generate_multidimensional_forecast.invoke({"periods": request.periods})
            
            if isinstance(result, str):
                forecast_data = json.loads(result)
            else:
                forecast_data = result
            
            return ForecastingTestResponse(
                success=True,
                forecast_result=forecast_data,
                agent_response=f"Generated {forecast_data.get('summary', {}).get('forecasted_segments', 0)} segment forecasts"
            )
        
        elif request.forecast_type == "prophet":
            if not request.pricing_model:
                raise HTTPException(status_code=400, detail="pricing_model required for Prophet forecast type")
            
            # Use Prophet forecast tool
            result = generate_prophet_forecast.invoke({
                "pricing_model": request.pricing_model,
                "periods": request.periods
            })
            
            if isinstance(result, str):
                forecast_data = json.loads(result)
            else:
                forecast_data = result
            
            return ForecastingTestResponse(
                success=True,
                forecast_result=forecast_data,
                agent_response=f"Generated Prophet ML forecast for {request.pricing_model}"
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown forecast_type: {request.forecast_type}")
        
    except Exception as e:
        logger.error(f"Error testing Forecasting Agent: {e}")
        return ForecastingTestResponse(
            success=False,
            error=str(e)
        )


# ============================================================================
# Recommendation Agent Test Endpoints
# ============================================================================

class RecommendationTestRequest(BaseModel):
    """Request model for Recommendation Agent test."""
    query: Optional[str] = Field(None, description="Optional query for Recommendation Agent")
    include_forecasts: bool = Field(default=True, description="Auto-generate forecasts if true")
    include_rules: bool = Field(default=True, description="Auto-generate rules if true")


class RecommendationTestResponse(BaseModel):
    """Response model for Recommendation Agent test."""
    success: bool
    recommendations: Optional[Dict[str, Any]] = None
    agent_response: Optional[str] = None
    error: Optional[str] = None


@router.post("/recommendation", response_model=RecommendationTestResponse, summary="Test Recommendation Agent")
async def test_recommendation_agent(request: RecommendationTestRequest):
    """
    Test Recommendation Agent with strategic recommendations.
    
    This endpoint allows you to test the Recommendation Agent to generate strategic recommendations.
    It can optionally auto-generate forecasts and rules, or use existing ones.
    
    **Example Request:**
    ```json
    {
      "query": "What strategic recommendations do you have?",
      "include_forecasts": true,
      "include_rules": true
    }
    ```
    """
    try:
        from app.agents.recommendation import recommendation_agent, generate_strategic_recommendations
        from app.agents.forecasting import generate_multidimensional_forecast
        from app.agents.analysis import generate_and_rank_pricing_rules
        
        if recommendation_agent is None:
            raise HTTPException(status_code=503, detail="Recommendation Agent not initialized (missing API key)")
        
        # If query provided, use agent's natural language interface
        if request.query:
            messages = [{"role": "user", "content": request.query}]
            result = recommendation_agent.invoke({"messages": messages})
            agent_response = result.get("messages", [])[-1].content if result.get("messages") else None
            
            return RecommendationTestResponse(
                success=True,
                agent_response=agent_response
            )
        
        # Otherwise, generate strategic recommendations using the combined tool
        forecasts_result = None
        rules_result = None
        
        if request.include_forecasts:
            try:
                forecasts_result = generate_multidimensional_forecast.invoke({"periods": 30})
            except Exception as e:
                logger.warning(f"Could not generate forecasts: {e}")
        
        if request.include_rules:
            try:
                rules_result = generate_and_rank_pricing_rules.invoke({})
            except Exception as e:
                logger.warning(f"Could not generate rules: {e}")
                rules_result = None
        
        if not forecasts_result or not rules_result:
            return RecommendationTestResponse(
                success=False,
                error="Could not generate forecasts or rules. Try setting include_forecasts=true and include_rules=true, or provide a query instead."
            )
        
        # Generate strategic recommendations
        recommendations_result = generate_strategic_recommendations.invoke({
            "forecasts": forecasts_result if isinstance(forecasts_result, str) else json.dumps(forecasts_result),
            "rules": rules_result if isinstance(rules_result, str) else json.dumps(rules_result)
        })
        
        if isinstance(recommendations_result, str):
            recommendations_data = json.loads(recommendations_result)
        else:
            recommendations_data = recommendations_result
        
        return RecommendationTestResponse(
            success=True,
            recommendations=recommendations_data,
            agent_response=f"Generated {len(recommendations_data.get('recommendations', []))} strategic recommendations"
        )
        
    except Exception as e:
        logger.error(f"Error testing Recommendation Agent: {e}")
        return RecommendationTestResponse(
            success=False,
            error=str(e)
        )

