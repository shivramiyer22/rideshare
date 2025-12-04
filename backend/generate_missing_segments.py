"""
Generate synthetic historical rides for the 7 missing segment combinations.
All missing segments are: Premium vehicles with CUSTOM pricing
"""
import random
from datetime import datetime, timedelta
import pymongo
from app.config import settings

print("=" * 70)
print("GENERATING MISSING SEGMENT DATA")
print("=" * 70)

# The 7 missing combinations (all Premium + CUSTOM)
missing_combinations = [
    ("Urban", "Regular", "Premium", "CUSTOM"),
    ("Suburban", "Gold", "Premium", "CUSTOM"),
    ("Suburban", "Silver", "Premium", "CUSTOM"),
    ("Suburban", "Regular", "Premium", "CUSTOM"),
    ("Rural", "Gold", "Premium", "CUSTOM"),
    ("Rural", "Silver", "Premium", "CUSTOM"),
    ("Rural", "Regular", "Premium", "CUSTOM"),
]

# Connect to MongoDB
client = pymongo.MongoClient(settings.mongodb_url)
db = client[settings.mongodb_db_name]
collection = db["historical_rides"]

print(f"\n1. TARGET: Add 50 rides for each of 7 combinations = 350 new rides\n")

rides_to_add = []
ride_id_counter = 3000  # Start from 3000 to avoid conflicts

for location, loyalty, vehicle, pricing in missing_combinations:
    print(f"   Generating {location}/{loyalty}/{vehicle}/{pricing}...")
    
    # Generate 50 rides per combination
    for i in range(50):
        # Vary riders and drivers to create different demand profiles
        # Target: ~17 HIGH, ~17 MEDIUM, ~16 LOW per combination
        if i < 17:
            # HIGH demand: drivers < 34% of riders
            num_riders = random.randint(40, 60)
            num_drivers = random.randint(10, int(num_riders * 0.3))
        elif i < 34:
            # MEDIUM demand: drivers 34-66% of riders
            num_riders = random.randint(30, 50)
            num_drivers = random.randint(int(num_riders * 0.35), int(num_riders * 0.65))
        else:
            # LOW demand: drivers > 66% of riders
            num_riders = random.randint(20, 40)
            num_drivers = random.randint(int(num_riders * 0.7), num_riders - 5)
        
        # Calculate demand profile
        driver_ratio = (num_drivers / num_riders) * 100
        if driver_ratio < 34:
            demand_profile = "High"
        elif driver_ratio < 67:
            demand_profile = "Medium"
        else:
            demand_profile = "Low"
        
        # Generate ride duration (Premium vehicles typically longer rides)
        duration = random.uniform(20, 45)  # 20-45 minutes
        
        # Calculate unit price (Premium + CUSTOM = higher rates)
        base_unit_price = random.uniform(3.5, 5.0)  # $3.50-$5.00 per minute
        unit_price = round(base_unit_price, 2)
        
        # Calculate total ride cost
        total_cost = round(duration * unit_price, 2)
        
        # Generate random date in past 6 months
        days_ago = random.randint(1, 180)
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
            "Weather_Conditions": random.choice(["Clear", "Cloudy", "Rain"]),
            "Traffic_Conditions": random.choice(["Light", "Moderate", "Heavy"]),
        }
        
        rides_to_add.append(ride)
        ride_id_counter += 1

print(f"\n2. INSERTING {len(rides_to_add)} NEW RIDES INTO MONGODB...")

# Insert all rides
result = collection.insert_many(rides_to_add)
print(f"   ✅ Successfully inserted {len(result.inserted_ids)} rides")

# Verify insertion
print(f"\n3. VERIFICATION:")
total_rides = collection.count_documents({})
print(f"   Total historical rides now: {total_rides}")
print(f"   (Was 2000, now should be 2350)")

# Verify each combination
print(f"\n4. VERIFYING EACH COMBINATION:")
for location, loyalty, vehicle, pricing in missing_combinations:
    count = collection.count_documents({
        "Location_Category": location,
        "Customer_Loyalty_Status": loyalty,
        "Vehicle_Type": vehicle,
        "Pricing_Model": pricing
    })
    status = "✅" if count >= 50 else "❌"
    print(f"   {status} {location:10}/{loyalty:8}/{vehicle:8}/{pricing:10}: {count} rides")

print(f"\n5. DEMAND PROFILE DISTRIBUTION CHECK:")
for location, loyalty, vehicle, pricing in missing_combinations[:1]:  # Check first combo
    high = collection.count_documents({
        "Location_Category": location,
        "Customer_Loyalty_Status": loyalty,
        "Vehicle_Type": vehicle,
        "Pricing_Model": pricing,
        "Demand_Profile": "High"
    })
    med = collection.count_documents({
        "Location_Category": location,
        "Customer_Loyalty_Status": loyalty,
        "Vehicle_Type": vehicle,
        "Pricing_Model": pricing,
        "Demand_Profile": "Medium"
    })
    low = collection.count_documents({
        "Location_Category": location,
        "Customer_Loyalty_Status": loyalty,
        "Vehicle_Type": vehicle,
        "Pricing_Model": pricing,
        "Demand_Profile": "Low"
    })
    print(f"   {location}/{loyalty}/{vehicle}/{pricing}:")
    print(f"      HIGH: {high}, MEDIUM: {med}, LOW: {low}")

print(f"\n✅ DATA GENERATION COMPLETE!")
print(f"   Ready for Step 3: Rerun pipeline")

client.close()
