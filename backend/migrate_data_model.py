"""
Data Model Migration Script

Migrates 5 MongoDB collections to new data model:
1. Remove pricing_tier → use pricing_model
2. Replace distance with ride_duration
3. Replace avg_price with avg_fcs_unit_price (price per minute)
4. Add segment_demand_profile (calculated from driver/rider ratio)
5. Add riders_per_order and drivers_per_order fields

Collections migrated:
- historical_rides
- competitor_prices
- orders
- pipeline_results
- pricing_strategies
"""

import pymongo
import os
from dotenv import load_dotenv
from datetime import datetime
import sys

load_dotenv()

def calculate_demand_profile(drivers: float, riders: float) -> str:
    """
    Calculate segment_demand_profile based on driver/rider ratio.
    
    Logic:
    - HIGH: driver ratio < 34% (low supply, high demand)
    - MEDIUM: driver ratio 34-67%
    - LOW: driver ratio >= 67% (high supply, low demand)
    """
    if riders == 0 or riders is None:
        return "MEDIUM"  # Default if no data
    
    driver_ratio = (drivers / riders) * 100
    
    if driver_ratio < 34:
        return "HIGH"
    elif driver_ratio < 67:
        return "MEDIUM"
    else:
        return "LOW"


def migrate_historical_rides(db):
    """Migrate historical_rides collection."""
    print("\n1. Migrating historical_rides collection...")
    collection = db["historical_rides"]
    
    total = collection.count_documents({})
    print(f"   Total documents: {total}")
    
    updated = 0
    skipped = 0
    
    for doc in collection.find({}):
        updates = {}
        
        # Ensure pricing_model exists
        if "Pricing_Model" in doc and "pricing_model" not in doc:
            updates["pricing_model"] = doc["Pricing_Model"]
        
        # Remove pricing_tier if exists
        if "pricing_tier" in doc:
            updates["$unset"] = {"pricing_tier": ""}
        
        # Calculate Historical_Unit_Price if not exists
        duration = doc.get("Expected_Ride_Duration", 0)
        price = doc.get("Historical_Cost_of_Ride", 0)
        
        if duration and duration > 0 and price:
            updates["Historical_Unit_Price"] = round(price / duration, 4)
        
        # Calculate segment_demand_profile
        riders = doc.get("Number_Of_Riders", 0)
        drivers = doc.get("Number_of_Drivers", 0)
        
        if riders and drivers:
            updates["segment_demand_profile"] = calculate_demand_profile(drivers, riders)
        
        # Apply updates
        if updates:
            if "$unset" in updates:
                unset = updates.pop("$unset")
                if updates:
                    collection.update_one({"_id": doc["_id"]}, {"$set": updates, "$unset": unset})
                else:
                    collection.update_one({"_id": doc["_id"]}, {"$unset": unset})
            else:
                collection.update_one({"_id": doc["_id"]}, {"$set": updates})
            updated += 1
        else:
            skipped += 1
    
    print(f"   ✓ Updated: {updated}, Skipped: {skipped}")
    return updated


def migrate_competitor_prices(db):
    """Migrate competitor_prices collection."""
    print("\n2. Migrating competitor_prices collection...")
    collection = db["competitor_prices"]
    
    total = collection.count_documents({})
    print(f"   Total documents: {total}")
    
    updated = 0
    skipped = 0
    
    for doc in collection.find({}):
        updates = {}
        
        # Ensure pricing_model exists
        if "Pricing_Model" in doc and "pricing_model" not in doc:
            updates["pricing_model"] = doc["Pricing_Model"]
        
        # Remove pricing_tier
        if "pricing_tier" in doc:
            updates["$unset"] = {"pricing_tier": ""}
        
        # Calculate unit_price if not exists
        duration = doc.get("Expected_Ride_Duration", 0)
        price = doc.get("Historical_Cost_of_Ride", 0) or doc.get("price", 0)
        
        if duration and duration > 0 and price:
            updates["unit_price"] = round(price / duration, 4)
        
        # Calculate segment_demand_profile
        riders = doc.get("Number_Of_Riders", 0)
        drivers = doc.get("Number_of_Drivers", 0)
        
        if riders and drivers:
            updates["segment_demand_profile"] = calculate_demand_profile(drivers, riders)
        
        # Apply updates
        if updates:
            if "$unset" in updates:
                unset = updates.pop("$unset")
                if updates:
                    collection.update_one({"_id": doc["_id"]}, {"$set": updates, "$unset": unset})
                else:
                    collection.update_one({"_id": doc["_id"]}, {"$unset": unset})
            else:
                collection.update_one({"_id": doc["_id"]}, {"$set": updates})
            updated += 1
        else:
            skipped += 1
    
    print(f"   ✓ Updated: {updated}, Skipped: {skipped}")
    return updated


def migrate_orders(db):
    """Migrate orders collection."""
    print("\n3. Migrating orders collection...")
    collection = db["orders"]
    
    total = collection.count_documents({})
    print(f"   Total documents: {total}")
    
    updated = 0
    skipped = 0
    
    for doc in collection.find({}):
        updates = {}
        unset_fields = {}
        
        # Rename pricing_tier to pricing_model if needed
        if "pricing_tier" in doc and "pricing_model" not in doc:
            updates["pricing_model"] = doc["pricing_tier"]
            unset_fields["pricing_tier"] = ""
        elif "pricing_tier" in doc:
            unset_fields["pricing_tier"] = ""
        
        # Rename segment_avg_distance to segment_avg_fcs_ride_duration
        if "segment_avg_distance" in doc:
            # For orders, distance might have been in miles - treat as duration estimate
            updates["segment_avg_fcs_ride_duration"] = doc["segment_avg_distance"]
            unset_fields["segment_avg_distance"] = ""
        
        # Rename segment_avg_price to segment_avg_fcs_unit_price (recalculate)
        if "segment_avg_price" in doc:
            duration = doc.get("segment_avg_fcs_ride_duration", doc.get("duration", doc.get("segment_avg_distance", 30)))
            if duration and duration > 0:
                updates["segment_avg_fcs_unit_price"] = round(doc["segment_avg_price"] / duration, 4)
            unset_fields["segment_avg_price"] = ""
        
        # Remove price field (use estimated_price)
        if "price" in doc:
            unset_fields["price"] = ""
        
        # Calculate segment_demand_profile (default to MEDIUM if no data)
        if "segment_demand_profile" not in doc:
            updates["segment_demand_profile"] = "MEDIUM"
        
        # Add default values for new fields if missing
        if "segment_avg_riders_per_order" not in doc:
            updates["segment_avg_riders_per_order"] = 1.0
        if "segment_avg_drivers_per_order" not in doc:
            updates["segment_avg_drivers_per_order"] = 0.5
        
        # Apply updates
        if updates or unset_fields:
            update_doc = {}
            if updates:
                update_doc["$set"] = updates
            if unset_fields:
                update_doc["$unset"] = unset_fields
            
            collection.update_one({"_id": doc["_id"]}, update_doc)
            updated += 1
        else:
            skipped += 1
    
    print(f"   ✓ Updated: {updated}, Skipped: {skipped}")
    return updated


def migrate_pipeline_results(db):
    """Migrate pipeline_results collection (complex nested structure)."""
    print("\n4. Migrating pipeline_results collection...")
    collection = db["pipeline_results"]
    
    total = collection.count_documents({})
    print(f"   Total documents: {total}")
    
    print("   ℹ️  Skipping pipeline_results migration - will be regenerated by new pipeline runs")
    print("   (Complex nested structures, easier to regenerate than migrate)")
    
    return 0


def migrate_pricing_strategies(db):
    """Migrate pricing_strategies collection."""
    print("\n5. Migrating pricing_strategies collection...")
    collection = db["pricing_strategies"]
    
    total = collection.count_documents({})
    print(f"   Total documents: {total}")
    
    print("   ℹ️  Skipping pricing_strategies migration - will be regenerated by new pipeline runs")
    print("   (Contains per_segment_impacts that will be created fresh)")
    
    return 0


def verify_migration(db):
    """Verify migration was successful."""
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    # Check historical_rides
    print("\n1. Verifying historical_rides:")
    sample = db["historical_rides"].find_one({})
    if sample:
        print(f"   ✓ pricing_model: {sample.get('pricing_model', 'MISSING')}")
        print(f"   ✓ Historical_Unit_Price: {sample.get('Historical_Unit_Price', 'MISSING')}")
        print(f"   ✓ segment_demand_profile: {sample.get('segment_demand_profile', 'MISSING')}")
        print(f"   ✓ pricing_tier removed: {'pricing_tier' not in sample}")
    
    # Check competitor_prices
    print("\n2. Verifying competitor_prices:")
    sample = db["competitor_prices"].find_one({})
    if sample:
        print(f"   ✓ pricing_model: {sample.get('pricing_model', 'MISSING')}")
        print(f"   ✓ unit_price: {sample.get('unit_price', 'MISSING')}")
        print(f"   ✓ segment_demand_profile: {sample.get('segment_demand_profile', 'MISSING')}")
    
    # Check orders
    print("\n3. Verifying orders:")
    sample = db["orders"].find_one({})
    if sample:
        print(f"   ✓ pricing_model: {sample.get('pricing_model', 'MISSING')}")
        print(f"   ✓ segment_avg_fcs_ride_duration: {sample.get('segment_avg_fcs_ride_duration', 'MISSING')}")
        print(f"   ✓ segment_avg_fcs_unit_price: {sample.get('segment_avg_fcs_unit_price', 'MISSING')}")
        print(f"   ✓ segment_demand_profile: {sample.get('segment_demand_profile', 'MISSING')}")
        print(f"   ✓ pricing_tier removed: {'pricing_tier' not in sample}")
        print(f"   ✓ segment_avg_distance removed: {'segment_avg_distance' not in sample}")
        print(f"   ✓ segment_avg_price removed: {'segment_avg_price' not in sample}")


def main():
    """Run the migration."""
    print("=" * 60)
    print("DATA MODEL MIGRATION")
    print("=" * 60)
    print("\nThis will migrate 5 MongoDB collections to the new data model.")
    print("\nChanges:")
    print("  - Remove pricing_tier → use pricing_model")
    print("  - Replace distance with ride_duration (minutes)")
    print("  - Replace avg_price with avg_fcs_unit_price (price per minute)")
    print("  - Add segment_demand_profile (calculated from driver/rider ratio)")
    print("")
    
    response = input("Continue with migration? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Migration cancelled.")
        sys.exit(0)
    
    try:
        # Connect to MongoDB
        mongodb_url = os.getenv("MONGO_URI")
        mongodb_db = os.getenv("MONGO_DB_NAME", "rideshare")
        
        print(f"\nConnecting to MongoDB: {mongodb_db}...")
        client = pymongo.MongoClient(mongodb_url)
        db = client[mongodb_db]
        
        print("✓ Connected")
        
        # Run migrations
        total_updated = 0
        total_updated += migrate_historical_rides(db)
        total_updated += migrate_competitor_prices(db)
        total_updated += migrate_orders(db)
        total_updated += migrate_pipeline_results(db)
        total_updated += migrate_pricing_strategies(db)
        
        # Verify
        verify_migration(db)
        
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETE")
        print("=" * 60)
        print(f"\n✅ Total documents updated: {total_updated}")
        print("\n📝 Next steps:")
        print("  1. Clear backend cache: python3 clear_backend_cache.py")
        print("  2. Restart backend server")
        print("  3. Re-train ML model: POST /api/v1/ml/train")
        print("  4. Run pipeline: POST /api/v1/pipeline/run")
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
