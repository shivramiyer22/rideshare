"""
Analytics Pre-computation Background Task

This module pre-computes analytics KPIs every 5 minutes and stores them in MongoDB
for fast dashboard loading. Uses APScheduler for scheduled tasks.

The pre-computed data is stored in the analytics_cache collection with a 5-minute expiry.

Also includes automatic Prophet ML model retraining when new historical data is detected.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.database import get_database
from app.config import settings
from app.forecasting_ml import RideshareForecastModel
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def compute_analytics_kpis() -> Dict[str, Any]:
    """
    Compute analytics KPIs and store in analytics_cache collection.
    
    Calculates:
    - Total revenue (last 7d, 30d)
    - Total rides
    - Average revenue per ride
    - Customer distribution (Gold/Silver/Regular)
    - Top 10 routes by revenue
    
    Returns:
        Dict with computed KPIs
    """
    try:
        database = get_database()  # Synchronous function, don't await
        if database is None:
            logger.warning("Database not connected, skipping KPI computation")
            return {}
        rides_collection = database["historical_rides"]
        
        # Get date ranges
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)
        
        # Try to detect which collection format is being used
        # Check if historical_rides exists and has data
        count = await rides_collection.count_documents({})
        
        if count == 0:
            # Fallback to ride_orders if historical_rides is empty
            rides_collection = database["ride_orders"]
            count = await rides_collection.count_documents({})
        
        if count == 0:
            # No data available
            return {
                "total_revenue_7d": 0,
                "total_revenue_30d": 0,
                "total_rides_7d": 0,
                "total_rides_30d": 0,
                "avg_revenue_per_ride": 0,
                "customer_distribution": {"Gold": 0, "Silver": 0, "Regular": 0},
                "top_routes": []
            }
        
        # Determine field names based on collection
        sample_doc = await rides_collection.find_one({})
        has_new_format = sample_doc and "Order_Date" in sample_doc
        
        date_field = "Order_Date" if has_new_format else "created_at"
        price_field = "Historical_Cost_of_Ride" if has_new_format else "final_price"
        loyalty_field = "Customer_Loyalty_Status" if has_new_format else "loyalty_tier"
        location_field = "Location_Category" if has_new_format else "origin"
        
        # Total revenue and rides (7 days)
        pipeline_7d = [
            {
                "$match": {
                    date_field: {"$gte": seven_days_ago, "$lte": now}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": f"${price_field}"},
                    "total_rides": {"$sum": 1}
                }
            }
        ]
        
        result_7d = await rides_collection.aggregate(pipeline_7d).to_list(length=1)
        revenue_7d = result_7d[0]["total_revenue"] if result_7d else 0
        rides_7d = result_7d[0]["total_rides"] if result_7d else 0
        
        # Total revenue and rides (30 days)
        pipeline_30d = [
            {
                "$match": {
                    date_field: {"$gte": thirty_days_ago, "$lte": now}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": f"${price_field}"},
                    "total_rides": {"$sum": 1}
                }
            }
        ]
        
        result_30d = await rides_collection.aggregate(pipeline_30d).to_list(length=1)
        revenue_30d = result_30d[0]["total_revenue"] if result_30d else 0
        rides_30d = result_30d[0]["total_rides"] if result_30d else 0
        
        # Average revenue per ride (30 days)
        avg_revenue = revenue_30d / rides_30d if rides_30d > 0 else 0
        
        # Customer distribution
        pipeline_customers = [
            {
                "$group": {
                    "_id": f"${loyalty_field}",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        customer_results = await rides_collection.aggregate(pipeline_customers).to_list(length=100)
        customer_dist = {"Gold": 0, "Silver": 0, "Regular": 0}
        
        for result in customer_results:
            loyalty = result["_id"]
            count = result["count"]
            if loyalty in customer_dist:
                customer_dist[loyalty] = count
            elif loyalty and isinstance(loyalty, str):
                # Handle case variations
                loyalty_lower = loyalty.lower()
                if "gold" in loyalty_lower:
                    customer_dist["Gold"] += count
                elif "silver" in loyalty_lower:
                    customer_dist["Silver"] += count
                else:
                    customer_dist["Regular"] += count
        
        # Top 10 routes by revenue (30 days)
        pipeline_routes = [
            {
                "$match": {
                    date_field: {"$gte": thirty_days_ago, "$lte": now}
                }
            },
            {
                "$group": {
                    "_id": f"${location_field}",
                    "revenue": {"$sum": f"${price_field}"},
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
        
        top_routes = await rides_collection.aggregate(pipeline_routes).to_list(length=10)
        routes_list = [
            {
                "route": route["_id"] or "Unknown",
                "revenue": route["revenue"],
                "rides": route["rides"]
            }
            for route in top_routes
        ]
        
        # Compile results
        kpis = {
            "total_revenue_7d": float(revenue_7d),
            "total_revenue_30d": float(revenue_30d),
            "total_rides_7d": rides_7d,
            "total_rides_30d": rides_30d,
            "avg_revenue_per_ride": float(avg_revenue),
            "customer_distribution": customer_dist,
            "top_routes": routes_list,
            "computed_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=5)
        }
        
        # Store in analytics_cache collection
        cache_collection = database["analytics_cache"]
        await cache_collection.delete_many({})  # Clear old cache
        await cache_collection.insert_one(kpis)
        
        print(f"✓ Analytics KPIs computed and cached at {datetime.utcnow()}")
        return kpis
        
    except Exception as e:
        print(f"⚠️  Error computing analytics KPIs: {e}")
        return {
            "error": str(e),
            "computed_at": datetime.utcnow()
        }


async def check_and_retrain_ml_model():
    """
    Check if new historical data has been added and retrain Prophet ML model if needed.
    
    This function:
    1. Checks the last training timestamp stored in MongoDB
    2. Compares with the latest historical_rides document timestamp
    3. If new data is detected (and sufficient data exists), retrains the model
    4. Updates the training timestamp
    
    Runs every 30 minutes to check for new data.
    """
    try:
        database = get_database()
        if database is None:
            logger.warning("Database connection not available for ML retraining check")
            return
        
        historical_collection = database["historical_rides"]
        
        # Count total documents
        total_count = await historical_collection.count_documents({})
        
        if total_count < 300:
            logger.debug(f"Not enough data for ML training: {total_count} rows (minimum 300 required)")
            return
        
        # Get the last training timestamp from metadata collection
        metadata_collection = database.get_collection("ml_training_metadata")
        last_training = await metadata_collection.find_one({"type": "last_training"})
        
        # Get the latest document timestamp
        latest_doc = await historical_collection.find_one(
            {},
            sort=[("Order_Date", -1), ("created_at", -1), ("_id", -1)]
        )
        
        if not latest_doc:
            logger.debug("No historical data found")
            return
        
        # Determine latest timestamp
        latest_timestamp = None
        if "Order_Date" in latest_doc:
            latest_timestamp = latest_doc["Order_Date"]
        elif "created_at" in latest_doc:
            latest_timestamp = latest_doc["created_at"]
        elif "_id" in latest_doc:
            # Use ObjectId timestamp as fallback
            latest_timestamp = latest_doc["_id"].generation_time
        
        # Check if we need to retrain
        should_retrain = False
        
        if not last_training:
            # Never trained before, but we have data
            logger.info("No previous training found. Training model with existing data...")
            should_retrain = True
        else:
            last_training_time = last_training.get("timestamp")
            if latest_timestamp and last_training_time:
                # Compare timestamps
                if isinstance(latest_timestamp, datetime) and isinstance(last_training_time, datetime):
                    if latest_timestamp > last_training_time:
                        # New data detected
                        logger.info(f"New historical data detected. Last training: {last_training_time}, Latest data: {latest_timestamp}")
                        should_retrain = True
                elif isinstance(latest_timestamp, datetime):
                    # Latest is datetime, last_training might be ObjectId timestamp
                    should_retrain = True
        
        if should_retrain:
            logger.info(f"Retraining Prophet ML model with {total_count} rows...")
            
            # Fetch all historical data
            cursor = historical_collection.find({})
            records = await cursor.to_list(length=None)
            df = pd.DataFrame(records)
            
            # Train the model
            model = RideshareForecastModel()
            result = model.train(df)
            
            if result.get("success", False):
                # Update training timestamp
                await metadata_collection.update_one(
                    {"type": "last_training"},
                    {
                        "$set": {
                            "timestamp": datetime.utcnow(),
                            "training_rows": result.get("training_rows", 0),
                            "mape": result.get("mape", 0.0)
                        }
                    },
                    upsert=True
                )
                logger.info(f"✓ Prophet ML model retrained successfully. MAPE: {result.get('mape', 0.0):.2f}%")
            else:
                logger.error(f"Failed to retrain model: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        logger.error(f"Error checking/retraining ML model: {e}")


def start_background_tasks():
    """
    Start the background scheduler for analytics pre-computation and ML model retraining.
    
    - Analytics pre-computation: Runs every 5 minutes
    - ML model retraining check: Runs every 30 minutes
    """
    scheduler.add_job(
        compute_analytics_kpis,
        trigger=IntervalTrigger(minutes=5),
        id='analytics_precompute',
        name='Analytics Pre-computation',
        replace_existing=True
    )
    
    # Check for new historical data and retrain ML model if needed
    # AsyncIOScheduler can handle async functions directly
    scheduler.add_job(
        check_and_retrain_ml_model,
        trigger=IntervalTrigger(minutes=30),
        id='ml_retrain_check',
        name='ML Model Retraining Check',
        replace_existing=True
    )
    
    scheduler.start()
    print("✓ Background scheduler started:")
    print("  - Analytics pre-computation: Every 5 minutes")
    print("  - ML model retraining check: Every 30 minutes")


def stop_background_tasks():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        print("✓ Background analytics scheduler stopped")


# For standalone execution (testing)
if __name__ == "__main__":
    async def main():
        await compute_analytics_kpis()
    
    asyncio.run(main())

