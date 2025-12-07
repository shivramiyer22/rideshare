"""
Prophet ML Training and Forecasting Endpoints

This module provides endpoints for:
1. Training Prophet ML models on historical data (3 models: demand, duration, unit_price)
2. Generating forecasts for 30, 60, and 90 days

Prophet ML is the ONLY forecasting method (NO moving averages).
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Literal
from app.forecasting_ml_multi import MultiMetricForecastModel
from app.database import get_database
import pandas as pd
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["ml"])

# Global model instance
forecast_model = MultiMetricForecastModel()


@router.post("/train")
async def train_prophet_models() -> Dict[str, Any]:
    """
    Train 3 Prophet ML models on historical data from MongoDB.
    
    This endpoint:
    1. Reads historical_rides + competitor_prices from MongoDB (300+ combined rows required)
    2. Trains 3 separate Prophet models:
       - **Demand Model**: Forecasts ride counts per day
       - **Duration Model**: Forecasts average ride duration per day
       - **Unit Price Model**: Forecasts average $/minute per day
    3. Saves all 3 models to models/ directory
    4. Returns training metrics
    
    Each model learns weekly patterns and trends from historical data.
    
    Returns:
        Dictionary with:
            - success: bool
            - models_trained: list of metrics ['demand', 'duration', 'unit_price']
            - training_rows: dict with rows per model
            - message: Success/error message
    """
    try:
        # Get database connection
        database = get_database()
        if database is None:
            raise HTTPException(
                status_code=500,
                detail="Database connection not available"
            )
        
        # Load HWCO historical data
        hwco_collection = database["historical_rides"]
        hwco_cursor = hwco_collection.find({})
        hwco_records = await hwco_cursor.to_list(length=None)
        hwco_count = len(hwco_records)
        logger.info(f"Loaded {hwco_count} HWCO historical records")
        
        # Add source identifier
        for record in hwco_records:
            record["Rideshare_Company"] = "HWCO"
        
        # Load competitor data
        competitor_collection = database["competitor_prices"]
        competitor_cursor = competitor_collection.find({})
        competitor_records = await competitor_cursor.to_list(length=None)
        competitor_count = len(competitor_records)
        logger.info(f"Loaded {competitor_count} competitor records")
        
        for record in competitor_records:
            record["Rideshare_Company"] = "COMPETITOR"
        
        # Combine both datasets
        records = hwco_records + competitor_records
        total_count = len(records)
        logger.info(f"Combined training data: {total_count} records (HWCO: {hwco_count}, Competitor: {competitor_count})")
        
        if total_count < 300:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data: {total_count} rides. Minimum 300 rides required (HWCO: {hwco_count}, Competitor: {competitor_count})."
            )
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Train all 3 models
        logger.info("Starting multi-metric Prophet ML training...")
        result = forecast_model.train_all(df)
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Training failed")
            )
        
        logger.info("Training successful!")
        
        # Update training metadata in MongoDB
        try:
            metadata_collection = database["ml_training_metadata"]
            await metadata_collection.update_one(
                {"type": "last_training"},
                {
                    "$set": {
                        "timestamp": datetime.utcnow(),
                        "total_rides": total_count,
                        "hwco_rows": hwco_count,
                        "competitor_rows": competitor_count,
                        "models_trained": result.get("models_trained", []),
                        "data_sources": ["historical_rides", "competitor_prices"]
                    }
                },
                upsert=True
            )
            logger.info("MongoDB metadata updated successfully")
        except Exception as e:
            logger.warning(f"Failed to update training metadata: {e}")
        
        # Build response
        response = {
            "success": True,
            "models_trained": result.get("models_trained", []),
            "training_rows": result.get("training_rows", {}),
            "data_sources": {
                "hwco_rows": hwco_count,
                "competitor_rows": competitor_count,
                "total_rows": total_count
            },
            "message": result.get("message", "Training complete")
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error training models: {str(e)}"
        )


# Forecast endpoints (30d, 60d, 90d)
@router.get("/forecast/30d")
async def forecast_30d(
    pricing_model: str = Query(..., description="Pricing model: CONTRACTED, STANDARD, or CUSTOM")
) -> Dict[str, Any]:
    """
    Generate 30-day forecast using Prophet ML.
    
    Args:
        pricing_model: One of CONTRACTED, STANDARD, or CUSTOM
    
    Returns:
        Dictionary with forecast data and metadata
    """
    return await _generate_forecast(pricing_model, periods=30)


@router.get("/forecast/60d")
async def forecast_60d(
    pricing_model: str = Query(..., description="Pricing model: CONTRACTED, STANDARD, or CUSTOM")
) -> Dict[str, Any]:
    """
    Generate 60-day forecast using Prophet ML.
    
    Args:
        pricing_model: One of CONTRACTED, STANDARD, or CUSTOM
    
    Returns:
        Dictionary with forecast data and metadata
    """
    return await _generate_forecast(pricing_model, periods=60)


@router.get("/forecast/90d")
async def forecast_90d(
    pricing_model: str = Query(..., description="Pricing model: CONTRACTED, STANDARD, or CUSTOM")
) -> Dict[str, Any]:
    """
    Generate 90-day forecast using Prophet ML.
    
    Args:
        pricing_model: One of CONTRACTED, STANDARD, or CUSTOM
    
    Returns:
        Dictionary with forecast data and metadata
    """
    return await _generate_forecast(pricing_model, periods=90)


async def _generate_forecast(pricing_model: str, periods: int) -> Dict[str, Any]:
    """
    Internal function to generate forecast.
    
    This function will automatically train the model if it doesn't exist and sufficient data is available.
    
    Args:
        pricing_model: CONTRACTED, STANDARD, or CUSTOM
        periods: Number of days (30, 60, or 90)
    
    Returns:
        Dictionary with forecast results
    """
    try:
        # Validate pricing_model
        valid_models = ["CONTRACTED", "STANDARD", "CUSTOM"]
        if pricing_model.upper() not in valid_models:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid pricing_model: {pricing_model}. Must be one of {valid_models}"
            )
        
        pricing_model = pricing_model.upper()
        
        # Validate periods
        valid_periods = [30, 60, 90]
        if periods not in valid_periods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid periods: {periods}. Must be one of {valid_periods}"
            )
        
        # Check if model exists, if not, try to auto-train
        if not forecast_model._model_exists():
            logger.info("Model not found. Attempting to auto-train...")
            
            # Check if we have enough data to train
            database = get_database()
            if database is None:
                raise HTTPException(
                    status_code=500,
                    detail="Database connection not available. Cannot auto-train model."
                )
            
            collection = database["historical_rides"]
            record_count = await collection.count_documents({})
            
            if record_count < 300:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model not trained and insufficient data for auto-training. "
                           f"Found {record_count} rows, minimum 300 required. "
                           f"Please upload historical data or train manually using POST /api/v1/ml/train"
                )
            
            # Auto-train the model
            logger.info(f"Auto-training model with {record_count} rows...")
            cursor = collection.find({})
            records = await cursor.to_list(length=None)
            df = pd.DataFrame(records)
            
            # Train in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            train_result = await loop.run_in_executor(
                None,
                forecast_model.train,
                df
            )
            
            if not train_result.get("success", False):
                raise HTTPException(
                    status_code=500,
                    detail=f"Auto-training failed: {train_result.get('error', 'Unknown error')}. "
                           f"Please train manually using POST /api/v1/ml/train"
                )
            
            logger.info(f"✓ Model auto-trained successfully with {train_result.get('training_rows', 0)} rows")
        
        # Generate forecast (run in thread pool to avoid blocking)
        loop = asyncio.get_event_loop()
        forecast_df = await loop.run_in_executor(
            None,
            forecast_model.forecast,
            pricing_model,
            periods
        )
        
        if forecast_df is None:
            raise HTTPException(
                status_code=500,
                detail="Forecast generation failed. Model may be corrupted. Please retrain using POST /api/v1/ml/train"
            )
        
        # Convert DataFrame to list of dictionaries for JSON response
        # Ensure proper column mapping for response format
        forecast_list = []
        for _, row in forecast_df.iterrows():
            # Map Prophet columns to required response format
            forecast_item = {
                "date": row.get("ds", row.get("date", "")),
                "predicted_demand": float(row.get("yhat", row.get("predicted_demand", 0.0))),
                "confidence_lower": float(row.get("yhat_lower", row.get("confidence_lower", 0.0))),
                "confidence_upper": float(row.get("yhat_upper", row.get("confidence_upper", 0.0))),
                "trend": float(row.get("trend", row.get("trend", 0.0)))
            }
            
            # Format date as ISO string for JSON
            if hasattr(forecast_item["date"], "isoformat"):
                forecast_item["date"] = forecast_item["date"].isoformat()
            elif isinstance(forecast_item["date"], str):
                # Already a string, keep as is
                pass
            else:
                # Try to convert to string
                forecast_item["date"] = str(forecast_item["date"])
            
            forecast_list.append(forecast_item)
        
        return {
            "forecast": forecast_list,
            "model": "prophet_ml",
            "pricing_model": pricing_model,
            "periods": periods,
            "days": periods,  # Alias for periods
            "confidence": 0.80,
            "accuracy": "Training metrics available from /api/ml/train endpoint"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating forecast: {str(e)}"
        )


@router.get("/forecast-multi/{horizon}")
async def forecast_multi_metrics(
    horizon: Literal['30d', '60d', '90d']
) -> Dict[str, Any]:
    """
    Generate multi-metric forecasts using trained Prophet ML models.
    
    This endpoint forecasts ALL 3 metrics simultaneously:
    - Demand (ride counts per day)
    - Duration (average minutes per ride)
    - Unit Price (average $/minute)
    
    Args:
        horizon: Forecast period ('30d', '60d', or '90d')
    
    Returns:
        Dictionary with:
            - success: bool
            - horizon: forecast period
            - daily_forecasts: list of dicts with all 3 metrics per day
            - summary: aggregate statistics
    """
    try:
        # Parse periods
        periods = int(horizon[:-1])  # '30d' -> 30
        
        # Check if models exist
        model_files_exist = all(
            (forecast_model.models_dir / forecast_model.model_files[metric]).exists()
            for metric in ['demand', 'duration', 'unit_price']
        )
        
        if not model_files_exist:
            raise HTTPException(
                status_code=400,
                detail="Models not trained yet. Please train using POST /api/v1/ml/train"
            )
        
        # Load historical data to get regressor means for forecasting
        database = get_database()
        historical_df = None
        
        if database is not None:
            try:
                # Load recent historical data for regressor calculation
                hwco_collection = database["historical_rides"]
                hwco_cursor = hwco_collection.find({}).limit(1000)  # Use recent 1000 rides
                hwco_records = await hwco_cursor.to_list(length=1000)
                
                if hwco_records:
                    for record in hwco_records:
                        record["Rideshare_Company"] = "HWCO"
                    historical_df = pd.DataFrame(hwco_records)
                    logger.info(f"Loaded {len(historical_df)} historical records for regressor calculation")
            except Exception as e:
                logger.warning(f"Could not load historical data for regressors: {e}")
        
        # Generate forecasts for all 3 metrics with regressors
        logger.info(f"Generating {periods}-day forecast for all metrics with 24 regressors...")
        forecasts = forecast_model.forecast_all(periods=periods, historical_data=historical_df)
        
        if forecasts is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate forecasts"
            )
        
        # Combine forecasts into daily records
        daily_forecasts = []
        for day in range(periods):
            date_str = forecasts['demand'].iloc[day]['ds'].strftime('%Y-%m-%d')
            
            demand_val = forecasts['demand'].iloc[day]['yhat']
            duration_val = forecasts['duration'].iloc[day]['yhat']
            unit_price_val = forecasts['unit_price'].iloc[day]['yhat']
            
            # Calculate revenue = rides * duration * unit_price
            revenue_val = demand_val * duration_val * unit_price_val
            
            daily_forecasts.append({
                "date": date_str,
                "day_number": day + 1,
                "predicted_rides": round(max(0, demand_val), 2),
                "predicted_duration": round(max(0, duration_val), 2),
                "predicted_unit_price": round(max(0, unit_price_val), 4),
                "predicted_revenue": round(max(0, revenue_val), 2),
                "lower_bound_rides": round(max(0, forecasts['demand'].iloc[day]['yhat_lower']), 2),
                "upper_bound_rides": round(forecasts['demand'].iloc[day]['yhat_upper'], 2)
            })
        
        # Calculate summary statistics
        total_rides = sum(d['predicted_rides'] for d in daily_forecasts)
        avg_rides_per_day = total_rides / periods
        avg_duration = sum(d['predicted_duration'] for d in daily_forecasts) / periods
        avg_unit_price = sum(d['predicted_unit_price'] for d in daily_forecasts) / periods
        total_revenue = sum(d['predicted_revenue'] for d in daily_forecasts)
        
        # Calculate trend
        first_week_rides = sum(d['predicted_rides'] for d in daily_forecasts[:7]) / 7
        last_week_rides = sum(d['predicted_rides'] for d in daily_forecasts[-7:]) / 7
        trend_direction = "increasing" if last_week_rides > first_week_rides * 1.02 else ("decreasing" if last_week_rides < first_week_rides * 0.98 else "stable")
        
        summary = {
            "total_predicted_rides": round(total_rides, 2),
            "avg_rides_per_day": round(avg_rides_per_day, 2),
            "avg_duration_minutes": round(avg_duration, 2),
            "avg_unit_price_per_minute": round(avg_unit_price, 4),
            "total_predicted_revenue": round(total_revenue, 2),
            "trend": trend_direction,
            "confidence_score": 0.80,
            "forecast_period_days": periods
        }
        
        logger.info(f"✓ Generated {periods}-day forecast: {avg_rides_per_day:.1f} rides/day avg")
        
        return {
            "success": True,
            "horizon": horizon,
            "daily_forecasts": daily_forecasts,
            "summary": summary,
            "method": "Prophet ML"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating forecast: {str(e)}"
        )
