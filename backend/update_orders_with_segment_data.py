"""
Update existing orders with latest segment-specific data from pipeline results.

This script:
1. Fetches the latest pipeline results with per_segment_impacts
2. Extracts segment-specific avg unit price and ride duration
3. Updates all orders with their segment's latest values
"""

import sys
sys.path.insert(0, "/Users/manasaiyer/Desktop/SKI - ASU/Vibe-Coding/hackathon/rideshare/backend")

from pymongo import MongoClient
from app.config import settings
from datetime import datetime

def calculate_demand_profile(riders, drivers):
    """Calculate demand profile from riders and drivers."""
    if riders == 0 or riders is None:
        return "MEDIUM"
    driver_ratio = (drivers / riders) * 100
    if driver_ratio < 34:
        return "HIGH"
    elif driver_ratio < 67:
        return "MEDIUM"
    else:
        return "LOW"

def get_segment_key(order):
    """Generate segment key from order data."""
    location = order.get("location_category", "Unknown")
    loyalty = order.get("customer_loyalty_status", "Unknown")
    vehicle = order.get("vehicle_type", "Unknown")
    pricing = order.get("pricing_model", "Unknown")
    
    # Calculate demand profile from order
    riders = order.get("segment_avg_riders_per_order", 0)
    drivers = order.get("segment_avg_drivers_per_order", 0)
    demand = calculate_demand_profile(riders, drivers)
    
    return f"{location}_{loyalty}_{vehicle}_{pricing}_{demand}"

def main():
    print("=" * 70)
    print("UPDATING ORDERS WITH LATEST SEGMENT DATA")
    print("=" * 70)
    
    # Connect to MongoDB
    client = MongoClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]
    
    orders_collection = db["orders"]
    pipeline_collection = db["pipeline_results"]
    
    # Get latest pipeline results
    print("\n1. Fetching latest pipeline results...")
    latest_pipeline = pipeline_collection.find_one(
        sort=[("completed_at", -1)]
    )
    
    if not latest_pipeline:
        print("❌ No pipeline results found")
        return
    
    print(f"   ✅ Found pipeline run: {latest_pipeline.get('run_id')}")
    print(f"   Completed at: {latest_pipeline.get('completed_at')}")
    
    # Extract per_segment_impacts
    per_segment_impacts = latest_pipeline.get("per_segment_impacts", {})
    
    if not per_segment_impacts:
        # Try nested location
        phases = latest_pipeline.get("phases", {})
        recommendation = phases.get("recommendation", {})
        data = recommendation.get("data", {})
        per_segment_impacts = data.get("per_segment_impacts", {})
    
    if not per_segment_impacts:
        print("❌ No per_segment_impacts found in pipeline results")
        return
    
    # Build segment lookup dictionary
    segment_lookup = {}
    total_impacts = 0
    
    for location, location_data in per_segment_impacts.items():
        if isinstance(location_data, list):
            for impact in location_data:
                segment_key = impact.get("segment_key")
                if segment_key:
                    segment_lookup[segment_key] = {
                        "unit_price": impact.get("baseline_unit_price", 0),
                        "duration": impact.get("baseline_duration", 0)
                    }
                    total_impacts += 1
    
    print(f"   ✅ Built segment lookup with {total_impacts} segments")
    
    # Get all orders
    print("\n2. Fetching all orders...")
    orders = list(orders_collection.find({}))
    print(f"   ✅ Found {len(orders)} orders")
    
    # Update each order
    print("\n3. Updating orders with segment data...")
    updated_count = 0
    not_found_count = 0
    
    for order in orders:
        order_id = order.get("order_id")
        segment_key = get_segment_key(order)
        
        if segment_key in segment_lookup:
            segment_data = segment_lookup[segment_key]
            
            # Update order with segment-specific values
            update_result = orders_collection.update_one(
                {"order_id": order_id},
                {"$set": {
                    "segment_avg_fcs_unit_price": segment_data["unit_price"],
                    "segment_avg_fcs_ride_duration": segment_data["duration"],
                    "segment_data_updated_at": datetime.utcnow()
                }}
            )
            
            if update_result.modified_count > 0:
                updated_count += 1
                print(f"   ✅ Updated order {order_id}: {segment_key}")
                print(f"      Unit Price: ${segment_data['unit_price']:.2f}/min")
                print(f"      Duration: {segment_data['duration']:.1f} min")
        else:
            not_found_count += 1
            print(f"   ⚠️  Segment not found for order {order_id}: {segment_key}")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total orders: {len(orders)}")
    print(f"Successfully updated: {updated_count}")
    print(f"Segment not found: {not_found_count}")
    
    if updated_count > 0:
        print(f"\n✅ SUCCESS! Updated {updated_count} orders with latest segment data")
    else:
        print(f"\n⚠️  No orders were updated")
    
    # Verify a sample order
    if updated_count > 0:
        print("\n4. Verification - Sample updated order:")
        sample = orders_collection.find_one({"segment_data_updated_at": {"$exists": True}})
        if sample:
            print(f"   Order ID: {sample.get('order_id')}")
            print(f"   Segment: {get_segment_key(sample)}")
            print(f"   Unit Price: ${sample.get('segment_avg_fcs_unit_price', 0):.2f}/min")
            print(f"   Duration: {sample.get('segment_avg_fcs_ride_duration', 0):.1f} min")
            print(f"   Updated At: {sample.get('segment_data_updated_at')}")
    
    client.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
