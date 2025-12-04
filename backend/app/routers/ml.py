"""
Prophet ML Training and Forecasting Endpoints

This module provides endpoints for:
1. Training Prophet ML models on historical data
2. Generating forecasts for 30, 60, and 90 days

Prophet ML is the ONLY forecasting method (NO moving averages).
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Literal
from app.forecasting_ml import RideshareForecastModel
from app.database import get_database
import pandas as pd
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["ml"])

# Global model instance
forecast_model = RideshareForecastModel()


@router.post("/train")
async def train_prophet_models() -> Dict[str, Any]:
    """
    Train Prophet ML model with 24 regressors on historical data from MongoDB.
    
    This endpoint:
    1. Reads historical_rides + competitor_prices from MongoDB (300+ combined rows required)
    2. Trains a single Prophet model with multi-dimensional forecasting
    3. Uses 24 regressors (20 categorical + 4 numeric) for accurate predictions
    4. Saves model to models/ directory
    5. Returns training metrics
    
    The 24 Regressors:
    
    **20 Categorical Regressors:**
    - Location_Category (Urban/Suburban/Rural)
    - Customer_Loyalty_Status (Gold/Silver/Regular)
    - Vehicle_Type (Economy/Premium)
    - Pricing_Model (STANDARD/SURGE/CONTRACTED/CUSTOM)
    - Hour (0-23)
    - DayOfWeek (0-6)
    - Month (1-12)
    - IsWeekend (0/1)
    - IsRushHour (0/1)
    - IsHoliday (0/1)
    - Weather_Conditions (Clear/Rain/Snow/etc)
    - Traffic_Level (Low/Medium/High)
    - Event_Type (None/Sports/Concert/etc)
    - Competitor_Pricing_Strategy
    - Driver_Availability_Level (Low/Medium/High)
    - Route_Popularity (Low/Medium/High)
    - Payment_Method (Card/Cash/Digital)
    - Booking_Channel (App/Web/Phone)
    - Service_Class (Standard/Premium)
    - Demand_Profile (HIGH/MEDIUM/LOW)
    
    **4 Numeric Regressors:**
    - num_riders (Number_Of_Riders)
    - num_drivers (Number_of_Drivers)
    - ride_duration (Expected_Ride_Duration in minutes)
    - unit_price (Historical_Unit_Price in $/minute)
    
    The model learns:
    - Weekly/daily patterns (seasonality)
    - Hourly rush patterns
    - Weather and traffic impacts
    - Pricing model effects on demand
    - Loyalty tier behavior differences
    - Location-specific trends
    - Vehicle type demand patterns
    
    Returns:
        Dictionary with:
            - success: bool
            - mape: Mean Absolute Percentage Error
            - confidence: 0.80 (80% confidence intervals)
            - model_path: Path to saved model
            - training_rows: Number of rows used for training
            - data_sources: Breakdown of HWCO vs competitor data
            - error: Error message if training failed
    """
    try:
        # Get database connection
        database = get_database()
        if database is None:
            raise HTTPException(
                status_code=500,
                detail="Database connection not available"
            )
        
        # ================================================================
        # Load BOTH HWCO historical data AND competitor data for training
        # This improves forecast accuracy by learning market-wide patterns
        # ================================================================
        
        # Load HWCO historical data
        hwco_collection = database["historical_rides"]
        hwco_cursor = hwco_collection.find({})
        hwco_records = await hwco_cursor.to_list(length=None)
        hwco_count = len(hwco_records)
        logger.info(f"Loaded {hwco_count} HWCO historical records")
        
        # Add source identifier to HWCO records
        for record in hwco_records:
            record["Rideshare_Company"] = "HWCO"
        
        # Load competitor data
        competitor_collection = database["competitor_prices"]
        competitor_cursor = competitor_collection.find({})
        competitor_records = await competitor_cursor.to_list(length=None)
        competitor_count = len(competitor_records)
        logger.info(f"Loaded {competitor_count} competitor records")
        
        # Add source identifier to competitor records
        for record in competitor_records:
            record["Rideshare_Company"] = "COMPETITOR"
        
        # Combine both datasets
        records = hwco_records + competitor_records
        total_count = len(records)
        logger.info(f"Combined training data: {total_count} records (HWCO: {hwco_count}, Competitor: {competitor_count})")
        
        if total_count < 300:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient combined data: {total_count} rows. Minimum 300 total rows required (HWCO: {hwco_count}, Competitor: {competitor_count})."
            )
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Ensure required columns exist (support both old and new field names)
        has_date = 'Order_Date' in df.columns or 'completed_at' in df.columns or 'ds' in df.columns
        has_price = 'Historical_Cost_of_Ride' in df.columns or 'actual_price' in df.columns or 'y' in df.columns
        
        if not has_date:
            raise HTTPException(
                status_code=400,
                detail="Missing required column: 'Order_Date', 'completed_at', or 'ds' (datetime)"
            )
        
        if not has_price:
            raise HTTPException(
                status_code=400,
                detail="Missing required column: 'Historical_Cost_of_Ride', 'actual_price', or 'y' (numeric)"
            )
        
        # Calculate pricing_model breakdown (optional enhancement)
        # Support both new and old field names
        pricing_model_breakdown = {}
        pricing_col = None
        if 'Pricing_Model' in df.columns:
            pricing_col = 'Pricing_Model'
        elif 'pricing_model' in df.columns:
            pricing_col = 'pricing_model'
        
        if pricing_col:
            pricing_model_counts = df[pricing_col].value_counts().to_dict()
            pricing_model_breakdown = {
                "CONTRACTED": pricing_model_counts.get("CONTRACTED", 0),
                "STANDARD": pricing_model_counts.get("STANDARD", 0),
                "CUSTOM": pricing_model_counts.get("CUSTOM", 0)
            }
        
        # Train the model synchronously
        # Training takes ~15-30 seconds for 2000 rows, which is acceptable
        # Using run_in_executor caused CancelledError issues
        logger.info("Starting model training (synchronous)...")
        result = forecast_model.train(df)
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Training failed")
            )
        
        logger.info("Training successful, preparing response...")
        
        # Update training metadata in MongoDB
        try:
            metadata_collection = database["ml_training_metadata"]
            await metadata_collection.update_one(
                {"type": "last_training"},
                {
                    "$set": {
                        "timestamp": datetime.utcnow(),
                        "training_rows": result.get("training_rows", 0),
                        "hwco_rows": hwco_count,
                        "competitor_rows": competitor_count,
                        "mape": result.get("mape", 0.0),
                        "data_sources": ["historical_rides", "competitor_prices"]
                    }
                },
                upsert=True
            )
            logger.info("MongoDB metadata updated successfully")
        except Exception as e:
            logger.warning(f"Failed to update training metadata: {e}")
        
        # Build response with data source breakdown
        response = {
            "success": True,
            "mape": result.get("mape", 0.0),
            "confidence": result.get("confidence", 0.80),
            "model_path": result.get("model_path", ""),
            "training_rows": result.get("training_rows", 0),
            "data_sources": {
                "hwco_rows": hwco_count,
                "competitor_rows": competitor_count,
                "total_rows": total_count,
                "collections": ["historical_rides", "competitor_prices"]
            },
            "message": f"Model trained successfully on {result.get('training_rows', 0)} combined rows (HWCO: {hwco_count}, Competitor: {competitor_count})"
        }
        
        # Add pricing_model breakdown if we have the data
        if pricing_model_breakdown:
            response["pricing_model_breakdown"] = pricing_model_breakdown
        
        logger.info(f"Returning training response: success={response.get('success')}, rows={response.get('training_rows')}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error training model: {str(e)}"
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


