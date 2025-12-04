"""
Generate comprehensive data to reach all 162 segments.
Strategy: Add 100+ rides per combination with strong demand profile signals.
"""
import random
from datetime import datetime, timedelta
import pymongo
from app.config import settings

print("=" * 70)
print("GENERATING COMPREHENSIVE DATA FOR ALL 162 SEGMENTS")
print("=" * 70)

client = pymongo.MongoClient(settings.mongodb_url)
db = client[settings.mongodb_db_name]
collection = db["historical_rides"]

# Get ALL 54 base combinations
locations = ["Urban", "Suburban", "Rural"]
loyalty_tiers = ["Gold", "Silver", "Regular"]
vehicle_types = ["Premium", "Economy"]
pricing_models = ["STANDARD", "CONTRACTED", "CUSTOM"]

print(f"\n1. STRATEGY:")
print(f"   • Add 100 rides per combination (50 per demand profile type)")
print(f"   • Ensure clear HIGH/MEDIUM/LOW demand signals")
print(f"   • Total to add: 54 combinations × 100 rides = 5,400 rides")

rides_to_add = []
ride_id_counter = 10000  # Start from 10000 to avoid conflicts

total_combinations = 0

for location in locations:
    for loyalty in loyalty_tiers:
        for vehicle in vehicle_types:
            for pricing in pricing_models:
                total_combinations += 1
                
                # Generate 100 rides per combination
                # 34 HIGH, 33 MEDIUM, 33 LOW to ensure all 3 demand profiles
                for i in range(100):
                    # Determine demand profile with clear signals
                    if i < 34:
                        # HIGH demand: drivers < 30% of riders (very clear signal)
                        num_riders = random.randint(50, 80)
                        num_drivers = random.randint(8, int(num_riders * 0.28))
                        demand_profile = "High"
                    elif i < 67:
                        # MEDIUM demand: drivers 40-60% of riders (clear middle)
                        num_riders = random.randint(40, 60)
                        num_drivers = random.randint(int(num_riders * 0.40), int(num_riders * 0.60))
                        demand_profile = "Medium"
                    else:
                        # LOW demand: drivers > 70% of riders (very clear signal)
                        num_riders = random.randint(30, 50)
                        num_drivers = random.randint(int(num_riders * 0.72), num_riders - 3)
                        demand_profile = "Low"
                    
                    # Verify demand profile calculation
                    driver_ratio = (num_drivers / num_riders) * 100
                    if driver_ratio < 34:
                        demand_profile = "High"
                    elif driver_ratio < 67:
                        demand_profile = "Medium"
                    else:
                        demand_profile = "Low"
                    
                    # Duration varies by vehicle and location
                    if vehicle == "Premium":
                        duration = random.uniform(25, 50)  # Premium = longer
                    else:
                        duration = random.uniform(15, 35)  # Economy = shorter
                    
                    # Unit price varies by vehicle and pricing model
                    if vehicle == "Premium" and pricing == "CUSTOM":
                        unit_price = random.uniform(4.0, 6.0)  # Highest
                    elif vehicle == "Premium":
                        unit_price = random.uniform(3.0, 4.5)
                    elif pricing == "CUSTOM":
                        unit_price = random.uniform(2.5, 4.0)
                    else:
                        unit_price = random.uniform(2.0, 3.5)  # Economy/Standard
                    
                    unit_price = round(unit_price, 2)
                    total_cost = round(duration * unit_price, 2)
                    
                    # Random date in past year
                    days_ago = random.randint(1, 365)
                    ride_date = datetime.now() - timedelta(days=days_ago)
                    
                    ride = {
                        "Ride_Id": ride_id_counter,
                        "Location_Category": location,
                        "Customer_Loyalty_Status": loyalty,
                        "Vehicle_Type": vehicle,
                        "Pricing_Model": pricing,
                        "Number_Of_Riders": num_riders,
                        "Number_of_Drivers": num_drivers,
                        "Demand_Profile": demand_profile,
                        "Expected_Ride_Duration": round(duration, 2),
                        "Historical_Cost_of_Ride": total_cost,
                        "Historical_Unit_Price": unit_price,
                        "segment_demand_profile": demand_profile,
                        "Date": ride_date.strftime("%Y-%m-%d"),
                        "Time": ride_date.strftime("%H:%M:%S"),
                        "Weather_Conditions": random.choice(["Clear", "Cloudy", "Rain", "Snow"]),
                        "Traffic_Conditions": random.choice(["Light", "Moderate", "Heavy"]),
                    }
                    
                    rides_to_add.append(ride)
                    ride_id_counter += 1

print(f"\n2. GENERATING DATA...")
print(f"   Total combinations: {total_combinations}")
print(f"   Rides per combination: 100")
print(f"   Total rides to add: {len(rides_to_add)}")

print(f"\n3. INSERTING INTO MONGODB...")
# Insert in batches for performance
batch_size = 1000
total_inserted = 0

for i in range(0, len(rides_to_add), batch_size):
    batch = rides_to_add[i:i + batch_size]
    result = collection.insert_many(batch)
    total_inserted += len(result.inserted_ids)
    print(f"   Inserted {total_inserted}/{len(rides_to_add)} rides...")

print(f"\n4. VERIFICATION:")
total_rides = collection.count_documents({})
print(f"   Total historical rides now: {total_rides}")
print(f"   (Was 2,350, added {len(rides_to_add)}, now should be {2350 + len(rides_to_add)})")

# Verify demand profile distribution for a sample combination
sample = collection.find({
    "Location_Category": "Urban",
    "Customer_Loyalty_Status": "Gold",
    "Vehicle_Type": "Premium",
    "Pricing_Model": "STANDARD"
})

high = medium = low = 0
for ride in sample:
    if ride.get("Demand_Profile") == "High":
        high += 1
    elif ride.get("Demand_Profile") == "Medium":
        medium += 1
    elif ride.get("Demand_Profile") == "Low":
        low += 1

print(f"\n5. SAMPLE DEMAND PROFILE DISTRIBUTION:")
print(f"   Urban/Gold/Premium/STANDARD:")
print(f"   HIGH: {high}, MEDIUM: {medium}, LOW: {low}")
print(f"   (Should be roughly 34/33/33 for new data)")

print(f"\n✅ COMPREHENSIVE DATA GENERATION COMPLETE!")
print(f"   All 54 combinations now have 100+ rides each")
print(f"   Each combination has strong signals for all 3 demand profiles")
print(f"   Ready to rerun pipeline for 162 segment coverage!")

client.close()
