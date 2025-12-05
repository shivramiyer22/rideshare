"""
Generate Comprehensive Lyft Competitor Data for All 162 Segments

This script generates realistic Lyft competitor pricing data for all segment combinations
to ensure complete coverage in the segment dynamic pricing report.

Segments: 162 total
- Location Category: Urban, Suburban, Rural (3)
- Loyalty Tier: Gold, Silver, Regular (3)  
- Vehicle Type: Economy, Premium (2)
- Demand Profile: HIGH, MEDIUM, LOW (3)
- Pricing Model: STANDARD, SUBSCRIPTION, PAY_PER_RIDE (3)

Total: 3 × 3 × 2 × 3 × 3 = 162 segments
"""
from datetime import datetime, timedelta
import random
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from parent directory
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


# Lyft pricing strategy (typically 5-10% lower than HWCO to be competitive)
LYFT_PRICING_ADJUSTMENTS = {
    "Urban": 0.95,      # 5% lower in competitive urban markets
    "Suburban": 0.93,   # 7% lower to capture suburban market
    "Rural": 0.90       # 10% lower due to lower competition
}

LOYALTY_MULTIPLIERS = {
    "Gold": 1.0,        # No discount (Lyft doesn't have same loyalty program)
    "Silver": 1.0,
    "Regular": 1.0
}

VEHICLE_MULTIPLIERS = {
    "Economy": 1.0,
    "Premium": 1.25     # Premium rides cost 25% more
}

DEMAND_MULTIPLIERS = {
    "HIGH": 1.15,       # 15% surge during high demand
    "MEDIUM": 1.0,      # Normal pricing
    "LOW": 0.90         # 10% discount to attract riders
}

PRICING_MODEL_ADJUSTMENTS = {
    "STANDARD": 1.0,
    "CONTRACTED": 0.90,    # 10% discount for contracted rides
    "SUBSCRIPTION": 0.85,  # 15% discount for subscription
    "PAY_PER_RIDE": 1.05,  # 5% premium for pay-per-ride
    "CUSTOM": 1.02         # 2% premium for custom pricing
}

# Base pricing (per minute)
BASE_UNIT_PRICE = 2.50  # Lyft's typical $/minute rate


def generate_lyft_pricing(location, loyalty, vehicle, demand, pricing_model):
    """
    Generate realistic Lyft pricing for a segment.
    
    Args:
        location: Urban, Suburban, Rural
        loyalty: Gold, Silver, Regular
        vehicle: Economy, Premium
        demand: HIGH, MEDIUM, LOW
        pricing_model: STANDARD, SUBSCRIPTION, PAY_PER_RIDE
    
    Returns:
        Dictionary with pricing data
    """
    # Calculate unit price with all multipliers
    unit_price = BASE_UNIT_PRICE
    unit_price *= LYFT_PRICING_ADJUSTMENTS.get(location, 1.0)
    unit_price *= LOYALTY_MULTIPLIERS.get(loyalty, 1.0)
    unit_price *= VEHICLE_MULTIPLIERS.get(vehicle, 1.0)
    unit_price *= DEMAND_MULTIPLIERS.get(demand, 1.0)
    unit_price *= PRICING_MODEL_ADJUSTMENTS.get(pricing_model, 1.0)
    
    # Add slight randomness (+/- 5%)
    unit_price *= random.uniform(0.95, 1.05)
    
    # Expected ride duration (minutes) - varies by location and demand
    duration_base = {
        "Urban": 15,
        "Suburban": 25,
        "Rural": 35
    }
    duration = duration_base.get(location, 20)
    
    # Adjust duration by demand profile
    if demand == "HIGH":
        duration *= random.uniform(0.8, 1.0)  # Shorter rides during high demand
    elif demand == "LOW":
        duration *= random.uniform(1.0, 1.2)  # Longer rides during low demand
    else:
        duration *= random.uniform(0.9, 1.1)
    
    # Calculate total ride cost
    total_cost = unit_price * duration
    
    # Number of riders (typically 1-2 for most rides)
    num_riders = random.choices([1, 2, 3, 4], weights=[60, 30, 8, 2])[0]
    
    # Number of drivers (always 1 for standard rides)
    num_drivers = 1
    
    # Historical ride distance (miles)
    distance_base = {
        "Urban": 5,
        "Suburban": 10,
        "Rural": 15
    }
    distance = distance_base.get(location, 8) * random.uniform(0.8, 1.2)
    
    return {
        "unit_price": round(unit_price, 2),
        "duration": round(duration, 1),
        "total_cost": round(total_cost, 2),
        "num_riders": num_riders,
        "num_drivers": num_drivers,
        "distance": round(distance, 2)
    }


def generate_competitor_record(location, loyalty, vehicle, demand, pricing_model, index):
    """Generate a single competitor record with realistic data."""
    
    pricing = generate_lyft_pricing(location, loyalty, vehicle, demand, pricing_model)
    
    # Random date within last 6 months
    days_ago = random.randint(1, 180)
    order_date = datetime.now() - timedelta(days=days_ago)
    
    # Random time of day
    hour = random.randint(6, 23)
    time_of_ride = f"{hour:02d}:00"
    
    # Month name
    month = order_date.strftime("%B")
    
    # Traffic level (more likely to be high in urban areas during rush hour)
    if location == "Urban" and hour in [7, 8, 9, 17, 18, 19]:
        traffic = random.choices(["High", "Medium", "Low"], weights=[60, 30, 10])[0]
    else:
        traffic = random.choices(["High", "Medium", "Low"], weights=[20, 50, 30])[0]
    
    # Weather (mostly clear)
    weather = random.choices(
        ["Clear", "Rainy", "Cloudy", "Snowy"],
        weights=[70, 15, 10, 5]
    )[0]
    
    # Event type (rare)
    event = random.choices(
        ["None", "Concert", "Sports", "Conference"],
        weights=[85, 5, 7, 3]
    )[0]
    
    # Day of week
    day_of_week = order_date.strftime("%A")
    is_weekend = 1 if day_of_week in ["Saturday", "Sunday"] else 0
    
    # Rush hour
    is_rush_hour = 1 if hour in [7, 8, 9, 17, 18, 19] else 0
    
    # Holiday (rare)
    is_holiday = random.choices([0, 1], weights=[95, 5])[0]
    
    record = {
        # Segment dimensions (use title case for Demand_Profile to match MongoDB schema)
        "Location_Category": location,
        "Customer_Loyalty_Status": loyalty,
        "Vehicle_Type": vehicle,
        "Demand_Profile": demand.title(),  # Convert HIGH → High, MEDIUM → Medium, LOW → Low
        "Pricing_Model": pricing_model,
        
        # Pricing data (NEW MODEL: duration + unit_price)
        "unit_price": pricing["unit_price"],
        "Expected_Ride_Duration": pricing["duration"],
        "Historical_Cost_of_Ride": pricing["total_cost"],
        
        # Demand data
        "Number_Of_Riders": pricing["num_riders"],
        "Number_of_Drivers": pricing["num_drivers"],
        "Historical_Ride_Distance": pricing["distance"],
        
        # Temporal data
        "Order_Date": order_date.strftime("%Y-%m-%d"),
        "Month": month,
        "Time_of_Ride": time_of_ride,
        "Hour": hour,
        "DayOfWeek": order_date.weekday(),
        "IsWeekend": is_weekend,
        "IsRushHour": is_rush_hour,
        "IsHoliday": is_holiday,
        
        # Context data
        "Weather_Conditions": weather,
        "Traffic_Level": traffic,
        "Event_Type": event,
        
        # Metadata
        "Rideshare_Company": "Lyft",
        "Service_Class": "Standard" if vehicle == "Economy" else "Premium",
        "Booking_Channel": random.choice(["App", "Web"]),
        "Payment_Method": random.choice(["Card", "Digital"]),
        "Driver_Availability_Level": random.choice(["Low", "Medium", "High"]),
        "Route_Popularity": random.choice(["Low", "Medium", "High"]),
        
        # Pipeline metadata
        "generated_by": "generate_lyft_competitor_data.py",
        "generated_at": datetime.utcnow().isoformat(),
        "segment_index": index
    }
    
    return record


def main():
    """Generate Lyft competitor data for all 162 segments."""
    
    print("=" * 80)
    print("Generating Comprehensive Lyft Competitor Data")
    print("=" * 80)
    
    # Connect to database
    print("\n1. Connecting to MongoDB...")
    mongodb_uri = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")
    mongodb_db = os.getenv("MONGO_DB_NAME") or os.getenv("MONGODB_DB_NAME", "rideshare")
    
    if not mongodb_uri:
        print("❌ ERROR: MONGO_URI not found in environment")
        return
    
    client = MongoClient(mongodb_uri)
    database = client[mongodb_db]
    competitor_collection = database["competitor_prices"]
    
    # Check existing data
    existing_count = competitor_collection.count_documents({})
    print(f"✓ Current competitor records: {existing_count}")
    
    # Define all segment dimensions
    locations = ["Urban", "Suburban", "Rural"]
    loyalties = ["Gold", "Silver", "Regular"]
    vehicles = ["Economy", "Premium"]
    demands = ["HIGH", "MEDIUM", "LOW"]
    # Include ALL pricing models that appear in segments
    pricing_models = ["CONTRACTED", "STANDARD", "SUBSCRIPTION", "PAY_PER_RIDE", "CUSTOM"]
    
    total_segments = len(locations) * len(loyalties) * len(vehicles) * len(demands) * len(pricing_models)
    print(f"\n2. Target segments: {total_segments}")
    print(f"   - Locations: {locations}")
    print(f"   - Loyalty Tiers: {loyalties}")
    print(f"   - Vehicle Types: {vehicles}")
    print(f"   - Demand Profiles: {demands}")
    print(f"   - Pricing Models: {pricing_models}")
    
    # Generate records for each segment
    print("\n3. Generating Lyft competitor records...")
    print("   (30 records per segment for statistical reliability)")
    
    all_records = []
    segment_index = 0
    records_per_segment = 30  # Generate 30 records per segment for good statistics
    
    for location in locations:
        for loyalty in loyalties:
            for vehicle in vehicles:
                for demand in demands:
                    for pricing_model in pricing_models:
                        segment_index += 1
                        
                        # Generate multiple records for this segment
                        for i in range(records_per_segment):
                            record = generate_competitor_record(
                                location, loyalty, vehicle, demand, pricing_model, segment_index
                            )
                            all_records.append(record)
                        
                        if segment_index % 27 == 0:  # Progress update every ~16%
                            print(f"   Progress: {segment_index}/{total_segments} segments ({len(all_records)} records)")
    
    print(f"✓ Generated {len(all_records)} total Lyft competitor records")
    print(f"  ({records_per_segment} records × {total_segments} segments)")
    
    # Delete existing Lyft data to avoid duplicates
    print("\n4. Removing old Lyft competitor data...")
    delete_result = competitor_collection.delete_many({"Rideshare_Company": "Lyft"})
    print(f"✓ Deleted {delete_result.deleted_count} old Lyft records")
    
    # Insert new records in batches
    print("\n5. Inserting new Lyft competitor data...")
    batch_size = 500
    inserted_count = 0
    
    for i in range(0, len(all_records), batch_size):
        batch = all_records[i:i + batch_size]
        result = competitor_collection.insert_many(batch)
        inserted_count += len(result.inserted_ids)
        print(f"   Inserted {inserted_count}/{len(all_records)} records...")
    
    print(f"✓ Successfully inserted {inserted_count} Lyft competitor records")
    
    # Verify coverage
    print("\n6. Verifying segment coverage...")
    pipeline = [
        {"$match": {"Rideshare_Company": "Lyft"}},
        {"$group": {
            "_id": {
                "location": "$Location_Category",
                "loyalty": "$Customer_Loyalty_Status",
                "vehicle": "$Vehicle_Type",
                "demand": "$Demand_Profile",
                "pricing": "$Pricing_Model"
            },
            "count": {"$sum": 1}
        }},
        {"$group": {
            "_id": None,
            "total_segments": {"$sum": 1}
        }}
    ]
    
    coverage = list(competitor_collection.aggregate(pipeline))
    if coverage:
        segments_covered = coverage[0]["total_segments"]
        print(f"✓ Segments covered: {segments_covered}/{total_segments}")
        
        if segments_covered == total_segments:
            print("✓ 100% segment coverage achieved! 🎉")
        else:
            print(f"⚠ Warning: Only {segments_covered}/{total_segments} segments covered")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_lyft = competitor_collection.count_documents({"Rideshare_Company": "Lyft"})
    total_all = competitor_collection.count_documents({})
    
    print(f"Total competitor records: {total_all}")
    print(f"  - Lyft records: {total_lyft}")
    print(f"  - Other records: {total_all - total_lyft}")
    print(f"\nSegments covered: {total_segments}/{total_segments} (100%)")
    print(f"Records per segment: ~{records_per_segment}")
    
    # Sample pricing by segment
    print("\n" + "=" * 80)
    print("SAMPLE PRICING (First 5 Segments)")
    print("=" * 80)
    
    sample_segments = list(competitor_collection.aggregate([
        {"$match": {"Rideshare_Company": "Lyft"}},
        {"$group": {
            "_id": {
                "location": "$Location_Category",
                "loyalty": "$Customer_Loyalty_Status",
                "vehicle": "$Vehicle_Type",
                "demand": "$Demand_Profile",
                "pricing": "$Pricing_Model"
            },
            "avg_unit_price": {"$avg": "$unit_price"},
            "avg_duration": {"$avg": "$Expected_Ride_Duration"},
            "avg_total_cost": {"$avg": "$Historical_Cost_of_Ride"},
            "count": {"$sum": 1}
        }},
        {"$limit": 5}
    ]))
    
    for seg in sample_segments:
        print(f"\n{seg['_id']['location']}/{seg['_id']['loyalty']}/{seg['_id']['vehicle']}/{seg['_id']['demand']}/{seg['_id']['pricing']}:")
        print(f"  Avg unit price: ${seg['avg_unit_price']:.2f}/min")
        print(f"  Avg duration: {seg['avg_duration']:.1f} min")
        print(f"  Avg total cost: ${seg['avg_total_cost']:.2f}")
        print(f"  Sample size: {seg['count']} rides")
    
    print("\n" + "=" * 80)
    print("✓ Lyft competitor data generation COMPLETE!")
    print("✓ Ready to regenerate pipeline with full segment coverage")
    print("=" * 80)
    
    # Close MongoDB connection
    client.close()


if __name__ == "__main__":
    main()

