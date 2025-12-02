#!/usr/bin/env python3
"""
Prophet ML Model Retraining Script

This script fetches the latest historical data from MongoDB and retrains the SINGLE Prophet ML model
that covers all pricing types (CONTRACTED, STANDARD, CUSTOM) together.

The model uses pricing_model as a regressor to learn pricing-type-specific patterns while sharing
common patterns (weekly cycles, daily cycles, trends) across all pricing types.

Designed to run as a cron job (Sunday 3 AM).

Usage:
    python scripts/retrain_models.py

Cron job (Sunday 3 AM):
    0 3 * * 0 /opt/rideshare/backend/venv/bin/python /opt/rideshare/backend/scripts/retrain_models.py
"""
import sys
import os
import asyncio
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import connect_to_mongo, close_mongo_connection, get_database
from app.forecasting_ml import RideshareForecastModel
import pandas as pd


async def retrain_all_models():
    """
    Fetch latest historical data and retrain the single Prophet ML model.
    
    The model trains on ALL pricing types (CONTRACTED, STANDARD, CUSTOM) together,
    using pricing_model as a regressor to learn pricing-type-specific patterns.
    
    This is a SINGLE model that covers all pricing types, not separate models.
    """
    print("=" * 60)
    print("Prophet ML Model Retraining")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        database = await get_database()
        rides_collection = database["historical_rides"]
        
        # Fetch latest historical data
        print("\n📊 Fetching historical data from MongoDB...")
        records = await rides_collection.find({}).to_list(length=None)
        
        if not records:
            print("⚠️  No historical data found. Skipping retraining.")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        print(f"✓ Loaded {len(df)} records")
        
        # Check minimum data requirement
        if len(df) < 300:
            print(f"⚠️  Insufficient data: {len(df)} rows. Minimum 300 rows required.")
            print("   Skipping retraining.")
            return
        
        # Initialize forecast model
        model = RideshareForecastModel()
        
        # Determine field names (support both new and old formats)
        has_new_format = "Order_Date" in df.columns
        
        if has_new_format:
            date_field = "Order_Date"
            price_field = "Historical_Cost_of_Ride"
            pricing_field = "Pricing_Model"
        else:
            date_field = "completed_at"
            price_field = "actual_price"
            pricing_field = "pricing_model"
        
        # Ensure date field is datetime
        df[date_field] = pd.to_datetime(df[date_field], errors='coerce')
        df = df.dropna(subset=[date_field, price_field])
        
        print(f"✓ After cleaning: {len(df)} records")
        
        # Check pricing model distribution
        if pricing_field in df.columns:
            pricing_dist = df[pricing_field].value_counts()
            print(f"\n📊 Pricing model distribution:")
            for pm, count in pricing_dist.items():
                print(f"   - {pm}: {count} records")
        else:
            print(f"\n⚠️  No '{pricing_field}' column found - model will train without pricing regressor")
        
        # Train SINGLE model on ALL data (all pricing types together)
        print(f"\n🔧 Training single Prophet model on all pricing types...")
        print(f"   → Model will learn patterns for CONTRACTED, STANDARD, and CUSTOM together")
        print(f"   → Using {pricing_field} as regressor to learn pricing-type-specific patterns")
        
        try:
            # Train the single model on all data
            result = model.train(df)
            
            if result.get("success"):
                print(f"\n   ✓ Model trained successfully")
                print(f"      - MAPE: {result.get('mape', 'N/A')}%")
                print(f"      - Model saved to: {result.get('model_path', 'N/A')}")
                print(f"      - Training rows: {result.get('training_rows', 'N/A')}")
                
                # Update prophet_models collection with training metadata
                models_collection = database["prophet_models"]
                metadata = {
                    "retrained_at": datetime.utcnow(),
                    "total_records": len(df),
                    "model": {
                        "success": True,
                        "mape": result.get("mape"),
                        "model_path": result.get("model_path"),
                        "training_rows": result.get("training_rows")
                    },
                    "pricing_distribution": pricing_dist.to_dict() if pricing_field in df.columns else {},
                    "status": "completed"
                }
                
                await models_collection.delete_many({})  # Clear old metadata
                await models_collection.insert_one(metadata)
                
                print(f"\n✓ Metadata saved to prophet_models collection")
            else:
                print(f"\n   ❌ Model training failed: {result.get('error', 'Unknown error')}")
                # Still save metadata with error
                models_collection = database["prophet_models"]
                metadata = {
                    "retrained_at": datetime.utcnow(),
                    "total_records": len(df),
                    "model": {
                        "success": False,
                        "error": result.get("error", "Unknown error")
                    },
                    "status": "failed"
                }
                await models_collection.delete_many({})
                await models_collection.insert_one(metadata)
                
        except Exception as e:
            print(f"\n   ❌ Error training model: {e}")
            import traceback
            traceback.print_exc()
            
            # Save error metadata
            models_collection = database["prophet_models"]
            metadata = {
                "retrained_at": datetime.utcnow(),
                "total_records": len(df),
                "model": {
                    "success": False,
                    "error": str(e)
                },
                "status": "failed"
            }
            await models_collection.delete_many({})
            await models_collection.insert_one(metadata)
        
        print("\n" + "=" * 60)
        print("Retraining Summary")
        print("=" * 60)
        print(f"✓ Single model trained on all pricing types")
        print(f"✓ Model covers: CONTRACTED, STANDARD, CUSTOM")
        print(f"✓ Uses pricing_model as regressor")
        print(f"Completed at: {datetime.now()}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during retraining: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(retrain_all_models())

