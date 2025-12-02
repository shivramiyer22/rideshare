"""
Routes and endpoints related to analytics.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app.database import get_database
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


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


