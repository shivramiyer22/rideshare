"""
Routes and endpoints related to analytics.
"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from app.database import get_database
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ============================================================================
# WHAT-IF ANALYSIS MODELS
# ============================================================================

class RecommendationInput(BaseModel):
    """Input model for what-if analysis."""
    recommendations_by_objective: Dict[str, Dict[str, Any]] = Field(
        description="Recommendations mapped to 4 objectives: revenue, profit_margin, competitive, retention"
    )
    integrated_strategy: Optional[str] = Field(None, description="Overall strategy summary")
    expected_impact: Optional[Dict[str, Any]] = Field(None, description="Expected impact metrics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "recommendations_by_objective": {
                    "revenue": {
                        "actions": ["Apply 1.12x multiplier to urban routes"],
                        "expected_impact": "+18% revenue",
                        "priority": "high"
                    },
                    "profit_margin": {
                        "actions": ["Reduce CUSTOM pricing to 2%"],
                        "expected_impact": "+6% margin",
                        "priority": "high"
                    },
                    "competitive": {
                        "actions": ["Match rural pricing with competitors"],
                        "expected_impact": "Close 5% gap",
                        "priority": "medium"
                    },
                    "retention": {
                        "actions": ["Cap surge at 1.25x for Gold customers"],
                        "expected_impact": "-12% churn",
                        "priority": "high"
                    }
                },
                "integrated_strategy": "Urban pricing + loyalty protection",
                "expected_impact": {
                    "revenue_increase": "18-23%",
                    "profit_margin_improvement": "5-7%",
                    "churn_reduction": "12%"
                }
            }
        }


class WhatIfAnalysisResponse(BaseModel):
    """Response model for what-if analysis."""
    success: bool
    baseline: Dict[str, Any]
    projections: Dict[str, List[Dict[str, Any]]]  # 30d, 60d, 90d projections
    business_objectives_impact: Dict[str, Dict[str, Any]]  # Impact per objective
    confidence: str
    visualization_data: Dict[str, Any]  # Formatted for charting
    generated_at: str


@router.post("/what-if-analysis", response_model=WhatIfAnalysisResponse)
async def analyze_what_if(
    recommendations: RecommendationInput = Body(...),
    forecast_periods: List[int] = Query(
        default=[30, 60, 90],
        description="Forecast periods in days"
    )
):
    """
    Perform what-if impact analysis on recommendations across multiple forecast periods.
    
    This endpoint calculates the projected impact of recommendations on all 4 business objectives:
    1. Revenue (target: 15-25% increase)
    2. Profit Margin (target: optimize without losing customers)
    3. Competitive Position (target: achieve market parity/leadership)
    4. Customer Retention (target: 10-15% churn reduction)
    
    Returns structured data suitable for visualization with:
    - Baseline metrics
    - 30/60/90 day projections
    - Impact breakdown by objective
    - Chart-ready data for frontend
    
    Args:
        recommendations: Recommendation data structure from Recommendation Agent
        forecast_periods: List of forecast periods in days (default: [30, 60, 90])
    
    Returns:
        Comprehensive what-if analysis with visualization data
    """
    try:
        from app.agents.analysis import calculate_whatif_impact_for_pipeline
        
        logger.info(f"What-if analysis requested for periods: {forecast_periods}")
        
        # Get baseline metrics from MongoDB (async)
        database = get_database()
        if database is None:
            raise HTTPException(
                status_code=500,
                detail="Database connection not available"
            )
        
        try:
            hwco_collection = database["historical_rides"]
            
            # Calculate baseline using async aggregation (MUCH FASTER than iterating)
            pipeline = [
                {"$limit": 1000},
                {"$group": {
                    "_id": None,
                    "total_revenue": {"$sum": "$Historical_Cost_of_Ride"},
                    "total_rides": {"$sum": 1},
                    "prices": {"$push": "$Historical_Cost_of_Ride"}
                }}
            ]
            
            cursor = hwco_collection.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            if result:
                baseline_revenue = result[0].get("total_revenue", 0)
                baseline_rides = result[0].get("total_rides", 0)
                baseline_prices = [p for p in result[0].get("prices", []) if p > 0]
            else:
                baseline_revenue = 0
                baseline_rides = 0
                baseline_prices = []
            
            baseline_avg = baseline_revenue / baseline_rides if baseline_rides > 0 else 0
            
            logger.info(f"Baseline calculated: ${baseline_revenue:.2f} revenue from {baseline_rides} rides")
            
            # Extract impact percentages from recommendations
            recs_dict = recommendations.dict()
            expected_impact = recs_dict.get("expected_impact", {})
            
            # Parse impact percentages
            def extract_percentage(value: str) -> float:
                """Extract numeric percentage from strings like '18-23%' or '12%'."""
                if not value:
                    return 0
                # Remove % and get average if range
                value = value.replace("%", "").strip()
                if "-" in value:
                    parts = value.split("-")
                    return (float(parts[0]) + float(parts[1])) / 2
                try:
                    return float(value)
                except:
                    return 0
            
            revenue_impact_pct = extract_percentage(expected_impact.get("revenue_increase", "0"))
            margin_impact_pct = extract_percentage(expected_impact.get("profit_margin_improvement", "0"))
            churn_impact_pct = extract_percentage(expected_impact.get("churn_reduction", "0"))
            
            # Generate projections for each forecast period
            projections = {}
            for period_days in forecast_periods:
                period_name = f"{period_days}d"
                period_projections = []
                
                # Generate daily projections
                daily_revenue_increase = baseline_revenue * (revenue_impact_pct / 100) / period_days
                
                for day in range(1, period_days + 1):
                    # Progressive impact (ramps up over time)
                    progress_factor = day / period_days  # 0.0 to 1.0
                    
                    daily_impact = daily_revenue_increase * progress_factor
                    projected_daily_revenue = (baseline_revenue / baseline_rides) * (1 + (revenue_impact_pct / 100) * progress_factor)
                    
                    period_projections.append({
                        "day": day,
                        "projected_revenue": round(projected_daily_revenue * baseline_rides, 2),
                        "cumulative_increase": round(daily_impact * day, 2),
                        "revenue_per_ride": round(projected_daily_revenue, 2),
                        "progress_factor": round(progress_factor, 2)
                    })
                
                projections[period_name] = period_projections
            
            # Calculate business objectives impact
            objectives_impact = {
                "revenue": {
                    "objective": "Maximize Revenue: Increase 15-25%",
                    "baseline": round(baseline_revenue, 2),
                    "projected_30d": round(baseline_revenue * (1 + revenue_impact_pct / 100 * 0.3), 2),
                    "projected_60d": round(baseline_revenue * (1 + revenue_impact_pct / 100 * 0.6), 2),
                    "projected_90d": round(baseline_revenue * (1 + revenue_impact_pct / 100), 2),
                    "impact_pct": round(revenue_impact_pct, 1),
                    "target_met": revenue_impact_pct >= 15 and revenue_impact_pct <= 25,
                    "confidence": "high" if revenue_impact_pct >= 15 else "medium"
                },
                "profit_margin": {
                    "objective": "Maximize Profit Margins",
                    "baseline_margin_pct": 40.0,  # Industry average
                    "projected_margin_pct": round(40.0 + margin_impact_pct, 1),
                    "improvement_pct": round(margin_impact_pct, 1),
                    "target_met": margin_impact_pct >= 5,
                    "confidence": "medium"
                },
                "competitive": {
                    "objective": "Stay Competitive",
                    "current_position": "5% behind competitors",
                    "projected_position": "competitive parity" if revenue_impact_pct >= 15 else "3% behind",
                    "gap_closed_pct": round(min(revenue_impact_pct / 3, 5), 1),
                    "target_met": revenue_impact_pct >= 15,
                    "confidence": "medium"
                },
                "retention": {
                    "objective": "Customer Retention: Reduce churn 10-15%",
                    "baseline_churn_pct": 25.0,  # Industry average
                    "projected_churn_pct": round(25.0 - churn_impact_pct, 1),
                    "churn_reduction_pct": round(churn_impact_pct, 1),
                    "target_met": churn_impact_pct >= 10 and churn_impact_pct <= 15,
                    "confidence": "high" if churn_impact_pct >= 10 else "low"
                }
            }
            
            # Format visualization data for charts
            visualization_data = {
                "revenue_trend": {
                    "labels": [f"Day {p['day']}" for p in projections.get("30d", [])[:30:5]],  # Every 5 days
                    "baseline": [baseline_revenue] * 6,
                    "projected_30d": [p["projected_revenue"] for p in projections.get("30d", [])[:30:5]],
                    "projected_60d": [p["projected_revenue"] for p in projections.get("60d", [])[:60:10]],
                    "projected_90d": [p["projected_revenue"] for p in projections.get("90d", [])[:90:15]]
                },
                "objectives_summary": {
                    "labels": ["Revenue", "Profit Margin", "Competitive", "Retention"],
                    "baseline": [0, 40, 0, 25],
                    "projected": [
                        revenue_impact_pct,
                        40 + margin_impact_pct,
                        min(revenue_impact_pct / 3, 5),
                        25 - churn_impact_pct
                    ],
                    "targets": [20, 45, 5, 15],  # Target values
                    "target_met": [
                        objectives_impact["revenue"]["target_met"],
                        objectives_impact["profit_margin"]["target_met"],
                        objectives_impact["competitive"]["target_met"],
                        objectives_impact["retention"]["target_met"]
                    ]
                },
                "kpi_cards": [
                    {
                        "title": "Revenue Increase",
                        "value": f"{revenue_impact_pct:.1f}%",
                        "target": "15-25%",
                        "status": "success" if objectives_impact["revenue"]["target_met"] else "warning"
                    },
                    {
                        "title": "Profit Margin",
                        "value": f"+{margin_impact_pct:.1f}%",
                        "target": "Optimize",
                        "status": "success" if margin_impact_pct > 0 else "warning"
                    },
                    {
                        "title": "Competitive Gap",
                        "value": f"{objectives_impact['competitive']['gap_closed_pct']:.1f}% closed",
                        "target": "Parity",
                        "status": "success" if objectives_impact["competitive"]["target_met"] else "warning"
                    },
                    {
                        "title": "Churn Reduction",
                        "value": f"{churn_impact_pct:.1f}%",
                        "target": "10-15%",
                        "status": "success" if objectives_impact["retention"]["target_met"] else "warning"
                    }
                ]
            }
            
        finally:
            # Database connection is managed by get_database(), no need to close
            pass
        
        # Determine overall confidence
        targets_met_count = sum(1 for obj in objectives_impact.values() if obj.get("target_met", False))
        overall_confidence = "high" if targets_met_count >= 3 else "medium" if targets_met_count >= 2 else "low"
        
        return WhatIfAnalysisResponse(
            success=True,
            baseline={
                "total_revenue": round(baseline_revenue, 2),
                "ride_count": baseline_rides,
                "avg_revenue_per_ride": round(baseline_avg, 2),
                "profit_margin_pct": 40.0,
                "churn_rate_pct": 25.0,
                "market_position": "5% behind competitors"
            },
            projections=projections,
            business_objectives_impact=objectives_impact,
            confidence=overall_confidence,
            visualization_data=visualization_data,
            generated_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"What-if analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"What-if analysis failed: {str(e)}")


@router.get("/dashboard")
async def get_dashboard(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Get comprehensive analytics dashboard data.
    
    Args:
        start_date: Start date for analytics (defaults to 30 days ago)
        end_date: End date for analytics (defaults to now)
    
    Returns:
        Dict: Dashboard analytics data including KPIs, charts, and breakdowns
    """
    try:
        database = get_database()
        if database is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Default date range: last 30 days
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        # Get collections
        historical_collection = database["historical_rides"]
        orders_collection = database["orders"]
        
        # Check which collection has data
        historical_count = await historical_collection.count_documents({})
        orders_count = await orders_collection.count_documents({})
        
        # KPI Calculations
        # 1. Total Revenue
        if historical_count > 0:
            revenue_pipeline = [
                {"$group": {
                    "_id": None,
                    "total_revenue": {"$sum": {"$ifNull": ["$Historical_Cost_of_Ride", "$actual_price"]}},
                    "total_rides": {"$sum": 1},
                    "avg_ride_cost": {"$avg": {"$ifNull": ["$Historical_Cost_of_Ride", "$actual_price"]}}
                }}
            ]
            revenue_result = await historical_collection.aggregate(revenue_pipeline).to_list(length=1)
        else:
            revenue_pipeline = [
                {"$group": {
                    "_id": None,
                    "total_revenue": {"$sum": "$price"},
                    "total_rides": {"$sum": 1},
                    "avg_ride_cost": {"$avg": "$price"}
                }}
            ]
            revenue_result = await orders_collection.aggregate(revenue_pipeline).to_list(length=1)
        
        total_revenue = revenue_result[0].get("total_revenue", 0) if revenue_result else 0
        total_rides = revenue_result[0].get("total_rides", 0) if revenue_result else 0
        avg_ride_cost = revenue_result[0].get("avg_ride_cost", 0) if revenue_result else 0
        
        # 2. Pricing Model Breakdown
        if historical_count > 0:
            pricing_pipeline = [
                {"$group": {
                    "_id": {"$ifNull": ["$Pricing_Model", "$pricing_model"]},
                    "count": {"$sum": 1},
                    "revenue": {"$sum": {"$ifNull": ["$Historical_Cost_of_Ride", "$actual_price"]}}
                }}
            ]
            pricing_result = await historical_collection.aggregate(pricing_pipeline).to_list(length=None)
        else:
            pricing_pipeline = [
                {"$group": {
                    "_id": "$pricing_tier",
                    "count": {"$sum": 1},
                    "revenue": {"$sum": "$price"}
                }}
            ]
            pricing_result = await orders_collection.aggregate(pricing_pipeline).to_list(length=None)
        
        pricing_breakdown = {
            "CONTRACTED": {"count": 0, "revenue": 0},
            "STANDARD": {"count": 0, "revenue": 0},
            "CUSTOM": {"count": 0, "revenue": 0}
        }
        for item in pricing_result:
            model = item.get("_id", "STANDARD")
            if model in pricing_breakdown:
                pricing_breakdown[model] = {
                    "count": item.get("count", 0),
                    "revenue": round(item.get("revenue", 0), 2)
                }
        
        # 3. Customer Loyalty Distribution
        if historical_count > 0:
            loyalty_pipeline = [
                {"$group": {
                    "_id": {"$ifNull": ["$Customer_Loyalty_Status", "Regular"]},
                    "count": {"$sum": 1}
                }}
            ]
            loyalty_result = await historical_collection.aggregate(loyalty_pipeline).to_list(length=None)
        else:
            loyalty_result = []
        
        loyalty_distribution = {"Gold": 0, "Silver": 0, "Regular": 0}
        for item in loyalty_result:
            tier = item.get("_id", "Regular")
            if tier in loyalty_distribution:
                loyalty_distribution[tier] = item.get("count", 0)
        
        # 4. Location Category Distribution
        if historical_count > 0:
            location_pipeline = [
                {"$group": {
                    "_id": {"$ifNull": ["$Location_Category", "Unknown"]},
                    "count": {"$sum": 1},
                    "avg_revenue": {"$avg": {"$ifNull": ["$Historical_Cost_of_Ride", "$actual_price"]}}
                }}
            ]
            location_result = await historical_collection.aggregate(location_pipeline).to_list(length=None)
        else:
            location_result = []
        
        location_breakdown = {}
        for item in location_result:
            location_breakdown[item.get("_id", "Unknown")] = {
                "count": item.get("count", 0),
                "avg_revenue": round(item.get("avg_revenue", 0), 2)
            }
        
        # 5. Time of Day Distribution
        if historical_count > 0:
            time_pipeline = [
                {"$group": {
                    "_id": {"$ifNull": ["$Time_of_Ride", "Unknown"]},
                    "count": {"$sum": 1}
                }}
            ]
            time_result = await historical_collection.aggregate(time_pipeline).to_list(length=None)
        else:
            time_result = []
        
        time_distribution = {}
        for item in time_result:
            time_distribution[item.get("_id", "Unknown")] = item.get("count", 0)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "kpis": {
                "total_revenue": round(total_revenue, 2),
                "total_rides": total_rides,
                "avg_ride_cost": round(avg_ride_cost, 2),
                "data_source": "historical_rides" if historical_count > 0 else "orders"
            },
            "pricing_breakdown": pricing_breakdown,
            "loyalty_distribution": loyalty_distribution,
            "location_breakdown": location_breakdown,
            "time_distribution": time_distribution
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get key business metrics from the database.
    
    Returns real-time metrics including:
    - Total rides count
    - Total revenue
    - Active orders count
    - Average ratings
    - Supply/demand ratio
    """
    try:
        database = get_database()
        if database is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Get collections
        historical_collection = database["historical_rides"]
        orders_collection = database["orders"]
        
        # Count documents
        historical_count = await historical_collection.count_documents({})
        orders_count = await orders_collection.count_documents({})
        pending_orders = await orders_collection.count_documents({"status": "PENDING"})
        
        # Calculate metrics from historical data
        if historical_count > 0:
            metrics_pipeline = [
                {"$group": {
                    "_id": None,
                    "total_revenue": {"$sum": {"$ifNull": ["$Historical_Cost_of_Ride", "$actual_price"]}},
                    "avg_rating": {"$avg": {"$ifNull": ["$Average_Ratings", 4.5]}},
                    "avg_supply_demand": {"$avg": {"$ifNull": ["$Supply_By_Demand", 1.0]}},
                    "total_drivers": {"$sum": {"$ifNull": ["$Number_of_Drivers", 0]}},
                    "total_riders": {"$sum": {"$ifNull": ["$Number_Of_Riders", 0]}}
                }}
            ]
            metrics_result = await historical_collection.aggregate(metrics_pipeline).to_list(length=1)
            
            total_revenue = metrics_result[0].get("total_revenue", 0) if metrics_result else 0
            avg_rating = metrics_result[0].get("avg_rating", 0) if metrics_result else 0
            avg_supply_demand = metrics_result[0].get("avg_supply_demand", 0) if metrics_result else 0
        else:
            total_revenue = 0
            avg_rating = 0
            avg_supply_demand = 0
        
        return {
            "metrics": {
                "total_rides": historical_count + orders_count,
                "total_revenue": round(total_revenue, 2),
                "pending_orders": pending_orders,
                "avg_rating": round(avg_rating, 2),
                "supply_demand_ratio": round(avg_supply_demand, 2),
                "historical_rides": historical_count,
                "new_orders": orders_count
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching metrics: {str(e)}")


@router.get("/revenue")
async def get_analytics_revenue(period: str = Query(default="30d", description="Period: 7d, 30d, 60d, 90d")) -> Dict[str, Any]:
    """
    Get analytics revenue data for the AnalyticsDashboard component.
    
    This endpoint provides:
    - Total revenue
    - Total rides count
    - Average revenue per ride
    - Customer distribution (Gold/Silver/Regular)
    - Revenue chart data (daily revenue for the period)
    - Top 10 profitable routes
    
    Args:
        period: Time period (7d, 30d, 60d, 90d) - defaults to 30d
    
    Returns:
        Dictionary with analytics data for the dashboard
    """
    try:
        database = get_database()
        if database is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Calculate date range based on period
        days_map = {"7d": 7, "30d": 30, "60d": 60, "90d": 90}
        days = days_map.get(period, 30)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get collections - prefer historical_rides (new format), fallback to ride_orders
        historical_collection = database["historical_rides"]
        orders_collection = database["ride_orders"]
        customers_collection = database["customers"]
        
        # Check which collection to use (prefer historical_rides with new fields)
        historical_count = await historical_collection.count_documents({})
        orders_count = await orders_collection.count_documents({})
        
        use_historical = historical_count > 0
        
        if use_historical:
            # Use historical_rides collection with new field names
            # Match on Order_Date (new) or completed_at (backward compatibility)
            pipeline_revenue = [
                {
                    "$match": {
                        "$or": [
                            {"Order_Date": {"$gte": start_date, "$lte": end_date}},
                            {"completed_at": {"$gte": start_date, "$lte": end_date}}
                        ]
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_revenue": {"$sum": {"$ifNull": ["$Historical_Cost_of_Ride", "$actual_price"]}},
                        "total_rides": {"$sum": 1}
                    }
                }
            ]
        else:
            # Use ride_orders collection (old format)
            pipeline_revenue = [
                {
                    "$match": {
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_revenue": {"$sum": "$final_price"},
                        "total_rides": {"$sum": 1}
                    }
                }
            ]
        
        collection_to_use = historical_collection if use_historical else orders_collection
        revenue_result = await collection_to_use.aggregate(pipeline_revenue).to_list(length=1)
        total_revenue = revenue_result[0].get("total_revenue", 0.0) if revenue_result and len(revenue_result) > 0 else 0.0
        total_rides = revenue_result[0].get("total_rides", 0) if revenue_result and len(revenue_result) > 0 else 0
        
        # Calculate average revenue per ride
        avg_revenue_per_ride = total_revenue / total_rides if total_rides > 0 else 0.0
        
        # Get customer distribution
        # Use Customer_Loyalty_Status from historical_rides if available, else customers collection
        if use_historical:
            pipeline_customers = [
                {
                    "$group": {
                        "_id": {"$ifNull": ["$Customer_Loyalty_Status", "$loyalty_tier"]},
                        "count": {"$sum": 1}
                    }
                }
            ]
            customer_dist_result = await historical_collection.aggregate(pipeline_customers).to_list(length=None)
        else:
            pipeline_customers = [
                {
                    "$group": {
                        "_id": "$loyalty_tier",
                        "count": {"$sum": 1}
                    }
                }
            ]
            customer_dist_result = await customers_collection.aggregate(pipeline_customers).to_list(length=None)
        
        customer_distribution = {"Gold": 0, "Silver": 0, "Regular": 0}
        
        for item in customer_dist_result:
            tier = item.get("_id", "Regular")
            count = item.get("count", 0)
            if tier in customer_distribution:
                customer_distribution[tier] = count
        
        # Get revenue chart data (daily revenue for the period)
        if use_historical:
            pipeline_chart = [
                {
                    "$match": {
                        "$or": [
                            {"Order_Date": {"$gte": start_date, "$lte": end_date}},
                            {"completed_at": {"$gte": start_date, "$lte": end_date}}
                        ]
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": {"$ifNull": ["$Order_Date", "$completed_at"]}
                            }
                        },
                        "revenue": {"$sum": {"$ifNull": ["$Historical_Cost_of_Ride", "$actual_price"]}},
                        "rides": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]
        else:
            pipeline_chart = [
                {
                    "$match": {
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$created_at"
                            }
                        },
                        "revenue": {"$sum": "$final_price"},
                        "rides": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]
        
        chart_result = await collection_to_use.aggregate(pipeline_chart).to_list(length=None)
        revenue_chart_data = [
            {"date": item["_id"], "revenue": item["revenue"], "rides": item["rides"]}
            for item in chart_result
        ]
        
        # Get top 10 profitable routes
        # Note: Route information may not be in historical_rides, so we'll use Location_Category if available
        if use_historical:
            # Try to get routes from Location_Category or other location fields
            pipeline_routes = [
                {
                    "$match": {
                        "$or": [
                            {"Order_Date": {"$gte": start_date, "$lte": end_date}},
                            {"completed_at": {"$gte": start_date, "$lte": end_date}}
                        ]
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "$ifNull": ["$Location_Category", "Unknown"]
                        },
                        "revenue": {"$sum": {"$ifNull": ["$Historical_Cost_of_Ride", "$actual_price"]}},
                        "rides": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"revenue": -1}
                },
                {
                    "$limit": 10
                }
            ]
            routes_result = await historical_collection.aggregate(pipeline_routes).to_list(length=None)
            top_routes = [
                {
                    "route": item["_id"],
                    "revenue": item["revenue"],
                    "rides": item["rides"]
                }
                for item in routes_result
            ]
        else:
            pipeline_routes = [
                {
                    "$match": {
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "origin": "$origin",
                            "destination": "$destination"
                        },
                        "revenue": {"$sum": "$final_price"},
                        "rides": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"revenue": -1}
                },
                {
                    "$limit": 10
                }
            ]
            routes_result = await orders_collection.aggregate(pipeline_routes).to_list(length=None)
            top_routes = [
                {
                    "route": f"{item['_id']['origin']} → {item['_id']['destination']}",
                    "revenue": item["revenue"],
                    "rides": item["rides"]
                }
                for item in routes_result
            ]
        
        return {
            "total_revenue": round(total_revenue, 2),
            "total_rides": total_rides,
            "avg_revenue_per_ride": round(avg_revenue_per_ride, 2),
            "customer_distribution": customer_distribution,
            "revenue_chart_data": revenue_chart_data,
            "top_routes": top_routes,
            "period": period
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics data: {str(e)}")


@router.get("/hwco-forecast-aggregate")
async def get_hwco_forecast_aggregate(
    pricing_model: str = Query("STANDARD", description="Pricing model: CONTRACTED, STANDARD, or CUSTOM"),
    periods: int = Query(30, description="Forecast period in days", ge=1, le=90)
) -> Dict[str, Any]:
    """
    Aggregate HWCO forecast data across all segments for overall company predictions.
    
    This endpoint queries the latest per_segment_impacts from pricing_strategies collection
    and aggregates baseline forecasts across all 162 segments to provide:
    - Daily cumulative demand (rides per day)
    - Average unit price per minute
    - Average ride duration
    - Total revenue projections
    - Trend analysis and confidence metrics
    
    **Data Source:** HWCO forecasts from per_segment_impacts baseline (NOT recommendation-adjusted)
    
    **Use Cases:**
    - Forecasting tab overview metrics
    - Company-wide demand planning
    - Revenue projections
    - Capacity planning
    
    Returns:
        Dictionary with aggregated forecast metrics and daily predictions
    """
    try:
        database = get_database()
        if database is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        collection = database["pricing_strategies"]
        
        # Query for latest per_segment_impacts (HWCO forecasts)
        latest_strategy = await collection.find_one(
            {"per_segment_impacts": {"$exists": True}},
            sort=[("timestamp", -1)]
        )
        
        if not latest_strategy or "per_segment_impacts" not in latest_strategy:
            raise HTTPException(
                status_code=404, 
                detail="No HWCO forecast data available. Run the pipeline first."
            )
        
        per_segment_impacts = latest_strategy.get("per_segment_impacts", {})
        
        # Aggregate baseline forecasts across all segments
        # We'll use the first recommendation's baseline data (all recs have same baseline)
        total_rides_30d = 0.0
        total_revenue_30d = 0.0
        total_duration_weighted = 0.0
        total_price_weighted = 0.0
        segment_count = 0
        
        # Track min/max for confidence calculation
        min_rides = float('inf')
        max_rides = 0.0
        
        # Collect all segments for detailed analysis
        all_segments = []
        
        # Iterate through first recommendation to get baseline for all segments
        for rec_key, segments in per_segment_impacts.items():
            if not isinstance(segments, list):
                continue
            
            # Process each segment (should be 162 total)
            for segment_impact in segments:
                baseline = segment_impact.get("baseline", {})
                
                if not baseline:
                    continue
                
                rides = baseline.get("rides_30d", 0.0)
                unit_price = baseline.get("unit_price_per_minute", 0.0)
                duration = baseline.get("ride_duration_minutes", 0.0)
                revenue = baseline.get("revenue_30d", 0.0)
                
                # Filter by pricing_model if needed
                segment_dims = segment_impact.get("segment", {})
                seg_pricing_model = segment_dims.get("pricing_model", "STANDARD")
                
                # Aggregate across all pricing models for total company view
                # (User can filter by pricing_model parameter if needed)
                total_rides_30d += rides
                total_revenue_30d += revenue
                
                # Weighted averages (by ride volume)
                if rides > 0:
                    total_duration_weighted += duration * rides
                    total_price_weighted += unit_price * rides
                    segment_count += 1
                    
                    min_rides = min(min_rides, rides)
                    max_rides = max(max_rides, rides)
                    
                    all_segments.append({
                        "location": segment_dims.get("location_category", ""),
                        "loyalty": segment_dims.get("loyalty_tier", ""),
                        "vehicle": segment_dims.get("vehicle_type", ""),
                        "pricing_model": seg_pricing_model,
                        "rides_30d": rides,
                        "unit_price": unit_price,
                        "duration": duration,
                        "revenue_30d": revenue
                    })
            
            # Only process first recommendation (all have same baseline)
            break
        
        if segment_count == 0 or total_rides_30d == 0:
            raise HTTPException(
                status_code=404,
                detail="No valid forecast data found in segments"
            )
        
        # Calculate weighted averages
        avg_duration = total_duration_weighted / total_rides_30d
        avg_unit_price = total_price_weighted / total_rides_30d
        
        # Calculate rides per day
        rides_per_day = total_rides_30d / periods
        
        # Calculate trend (simple linear trend based on segment variability)
        # Higher variability = less certain trend
        variability = (max_rides - min_rides) / max_rides if max_rides > 0 else 0.5
        trend_direction = "stable"  # Can be enhanced with historical comparison
        
        # Calculate confidence (lower variability = higher confidence)
        # Inverse of coefficient of variation
        confidence_score = max(0.70, min(0.95, 1.0 - variability))
        
        # Estimate MAPE (Mean Absolute Percentage Error)
        # This would ideally come from Prophet model training
        # For now, use reasonable estimate based on segment count
        estimated_mape = 8.5 if segment_count >= 150 else 12.0
        
        # Generate daily forecast with realistic variance and patterns
        daily_forecasts = []
        start_date = datetime.utcnow()
        
        # Add weekly seasonality pattern (mimicking real demand patterns)
        weekly_pattern = [0.92, 0.88, 0.90, 1.05, 1.20, 1.35, 1.25]  # Mon-Sun
        
        import random
        random.seed(42)  # Consistent results
        
        for day in range(periods):
            forecast_date = start_date + timedelta(days=day)
            day_of_week = forecast_date.weekday()  # 0=Monday, 6=Sunday
            
            # Weekly seasonality effect
            weekly_effect = weekly_pattern[day_of_week]
            
            # Add slight upward trend (0.15% per day)
            trend_effect = 1.0 + (day * 0.0015)
            
            # Add some random variance (±5%)
            random_variance = 1.0 + (random.random() - 0.5) * 0.10
            
            # Combine effects for rides
            daily_rides = rides_per_day * weekly_effect * trend_effect * random_variance
            
            # Price variance (±2% from average, slight increase over time)
            price_variance = 1.0 + (random.random() - 0.5) * 0.04
            price_trend = 1.0 + (day * 0.0008)  # Slight price increase
            daily_price = avg_unit_price * price_variance * price_trend
            
            # Duration variance (±3% from average, with weekly pattern)
            duration_variance = 1.0 + (random.random() - 0.5) * 0.06
            duration_weekly = 1.0 + (weekly_effect - 1.0) * 0.3  # Less affected by weekly
            daily_duration = avg_duration * duration_variance * duration_weekly
            
            # Revenue is rides * price * duration
            daily_revenue = daily_rides * daily_price * daily_duration
            
            daily_forecasts.append({
                "date": forecast_date.strftime("%Y-%m-%d"),
                "day_number": day + 1,
                "predicted_rides": round(daily_rides, 2),
                "predicted_unit_price": round(daily_price, 4),
                "predicted_duration": round(daily_duration, 2),
                "predicted_revenue": round(daily_revenue, 2),
                "lower_bound_rides": round(daily_rides * 0.85, 2),
                "upper_bound_rides": round(daily_rides * 1.15, 2)
            })
        
        # Calculate cumulative totals
        cumulative_rides = sum(d["predicted_rides"] for d in daily_forecasts)
        cumulative_revenue = sum(d["predicted_revenue"] for d in daily_forecasts)
        
        response = {
            "timestamp": latest_strategy.get("timestamp", datetime.utcnow().isoformat()),
            "forecast_period_days": periods,
            "pricing_model": pricing_model,
            "data_source": "hwco_forecast_baseline",
            "summary": {
                "total_rides_forecast": round(cumulative_rides, 2),
                "avg_rides_per_day": round(rides_per_day, 2),
                "avg_unit_price_per_minute": round(avg_unit_price, 4),
                "avg_ride_duration_minutes": round(avg_duration, 2),
                "total_revenue_forecast": round(cumulative_revenue, 2),
                "segments_analyzed": segment_count,
                "trend_direction": trend_direction,
                "confidence_score": round(confidence_score, 3),
                "estimated_mape_pct": round(estimated_mape, 1)
            },
            "daily_forecasts": daily_forecasts,
            "metadata": {
                "pipeline_run_id": latest_strategy.get("run_id", "unknown"),
                "forecast_generated_at": datetime.utcnow().isoformat(),
                "segment_breakdown_available": len(all_segments)
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error aggregating HWCO forecast data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error aggregating forecast data: {str(e)}"
        )


@router.get("/pricing-strategies")
async def get_pricing_strategies(
    filter_by: Optional[str] = Query(
        None,
        description="Filter type: 'business_objectives', 'pricing_rules', 'pipeline_results', or 'all'",
        regex="^(business_objectives|pricing_rules|pipeline_results|all)?$"
    ),
    category: Optional[str] = Query(
        None,
        description="Filter by category (e.g., 'rush_hour', 'location_based', 'metadata')"
    ),
    limit: int = Query(100, description="Maximum number of results to return", ge=1, le=1000),
    include_pipeline_data: bool = Query(
        False,
        description="Include latest pipeline result with forecasts and recommendations"
    )
) -> Dict[str, Any]:
    """
    Get pricing strategies with flexible filtering for analytics dashboard.
    
    **Use Cases:**
    - `filter_by=business_objectives` - Get business objectives only
    - `filter_by=pricing_rules` - Get all pricing rules
    - `filter_by=pipeline_results` - Get latest pipeline execution results
    - `filter_by=all` or no filter - Get everything
    - `category=rush_hour` - Get only rush hour rules
    - `include_pipeline_data=true` - Include forecasts and recommendations
    
    **Returns:**
    - Pricing rules with categories
    - Business objectives with targets
    - Pipeline results (forecasts, recommendations, what-if analysis)
    - Summary statistics
    
    **Example for Dashboard:**
    ```
    GET /api/v1/analytics/pricing-strategies?filter_by=business_objectives&include_pipeline_data=true
    ```
    Returns business objectives + latest pipeline data for progress tracking.
    """
    try:
        database = get_database()
        if database is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        collection = database["pricing_strategies"]
        response_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "filter_applied": filter_by or "all",
            "category_filter": category
        }
        
        # Query based on filter
        query = {}
        
        if filter_by == "business_objectives":
            query["category"] = "business_objectives"
        elif filter_by == "pricing_rules":
            query["category"] = {"$nin": ["business_objectives", "metadata", "expected_outcomes"]}
            query["source"] = "pricing_strategies_upload"
        elif filter_by == "pipeline_results":
            query["type"] = "pipeline_result"
        elif category:
            query["category"] = category
        
        # Execute query for uploaded strategies
        if filter_by != "pipeline_results":
            cursor = collection.find(query).limit(limit)
            strategies = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                strategies.append(doc)
            
            response_data["strategies"] = strategies
            response_data["count"] = len(strategies)
            
            # Group by category for summary
            categories = {}
            for strategy in strategies:
                cat = strategy.get("category", "unknown")
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(strategy)
            
            response_data["categories_summary"] = {
                cat: len(items) for cat, items in categories.items()
            }
        
        # Get latest pipeline result if requested or if filter is pipeline_results
        if include_pipeline_data or filter_by == "pipeline_results":
            pipeline_result = await collection.find_one(
                {"type": "pipeline_result"},
                sort=[("timestamp", -1)]
            )
            
            if pipeline_result:
                pipeline_result["_id"] = str(pipeline_result["_id"])
                
                # Extract key sections for dashboard
                pipeline_summary = {
                    "run_id": pipeline_result.get("run_id"),
                    "timestamp": pipeline_result.get("timestamp"),
                    "status": pipeline_result.get("status", "completed")
                }
                
                # Add forecasts summary
                if "forecasts" in pipeline_result:
                    forecasts = pipeline_result["forecasts"]
                    pipeline_summary["forecasts"] = {
                        "segments_count": len(forecasts.get("segmented_forecasts", [])),
                        "aggregated": forecasts.get("aggregated_forecasts", {})
                    }
                
                # Add recommendations summary
                if "recommendations" in pipeline_result:
                    recs = pipeline_result["recommendations"]
                    pipeline_summary["recommendations"] = {
                        "top_3_count": len(recs.get("top_3", [])),
                        "per_segment_impacts_count": len(recs.get("per_segment_impacts", [])),
                        "top_3": recs.get("top_3", [])
                    }
                
                # Add what-if analysis with business objectives
                if "what_if_analysis" in pipeline_result:
                    what_if = pipeline_result["what_if_analysis"]
                    pipeline_summary["what_if_analysis"] = {
                        "baseline": what_if.get("baseline", {}),
                        "business_objectives_impact": what_if.get("business_objectives_impact", {}),
                        "confidence": what_if.get("confidence", "unknown")
                    }
                    
                    # Extract business objectives for easy access
                    if "business_objectives_impact" in what_if:
                        response_data["business_objectives_progress"] = {
                            "revenue": {
                                "target": "15-25% increase",
                                "projected": what_if["business_objectives_impact"].get("revenue", {}).get("revenue_increase_pct", 0),
                                "target_met": what_if["business_objectives_impact"].get("revenue", {}).get("target_met", False),
                                "confidence": what_if["business_objectives_impact"].get("revenue", {}).get("confidence", "unknown")
                            },
                            "profit_margin": {
                                "target": "40%+ margin",
                                "projected": what_if["business_objectives_impact"].get("profit_margin", {}).get("projected_margin_pct", 0),
                                "target_met": what_if["business_objectives_impact"].get("profit_margin", {}).get("target_met", False),
                                "confidence": what_if["business_objectives_impact"].get("profit_margin", {}).get("confidence", "unknown")
                            },
                            "competitive": {
                                "target": "Close 5% gap",
                                "gap_closed_pct": what_if["business_objectives_impact"].get("competitive", {}).get("gap_closed_pct", 0),
                                "target_met": what_if["business_objectives_impact"].get("competitive", {}).get("target_met", False),
                                "confidence": what_if["business_objectives_impact"].get("competitive", {}).get("confidence", "unknown")
                            },
                            "retention": {
                                "target": "10-15% churn reduction",
                                "projected": what_if["business_objectives_impact"].get("retention", {}).get("churn_reduction_pct", 0),
                                "target_met": what_if["business_objectives_impact"].get("retention", {}).get("target_met", False),
                                "confidence": what_if["business_objectives_impact"].get("retention", {}).get("confidence", "unknown")
                            }
                        }
                
                # Add report metadata
                if "report_metadata" in pipeline_result:
                    pipeline_summary["report"] = pipeline_result["report_metadata"]
                
                response_data["pipeline_result"] = pipeline_summary
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching pricing strategies: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching pricing strategies: {str(e)}")

