# Order Form Dynamic Pricing Update - Build Plan

**Date:** December 5, 2025  
**Task:** Remove Calculate Price button & Traffic Level field, Add Dynamic Pricing Estimation  
**Status:** ✅ Completed

---

## Overview

Updated the Order Creation Form to show real-time dynamic pricing estimates as the user fills in the form fields. The pricing information is fetched automatically from MongoDB-backed segment analysis and displayed without requiring a manual "Calculate Price" button click.

---

## Changes Made

### 1. Frontend API Client (`frontend/src/lib/api.ts`)

**Added:**
- New `estimate` method to `ordersAPI` that calls `/api/v1/orders/estimate`

**Updated:**
- Corrected API paths to use `/api/v1` prefix to match backend routing
  - `create`: `/api/v1/orders`
  - `getQueue`: `/api/v1/orders/queue/priority`
  - `estimate`: `/api/v1/orders/estimate` (new)

### 2. Order Creation Form (`frontend/src/components/OrderCreationForm.tsx`)

**Removed:**
- ❌ "Calculate Price" button (not needed - pricing updates automatically)
- ❌ "Traffic Level" field (removed as requested)

**Added:**
1. **Location Category Field**
   - Dropdown with options: Urban, Suburban, Rural
   - Required for segment-based pricing
   - Placed in Route Information section

2. **Estimated Dynamic Pricing Section**
   - Beautiful gradient card with real-time pricing data
   - Three key metrics displayed:
     - **Demand Level**: HIGH/MEDIUM/LOW (color-coded: red/yellow/green)
     - **Avg Ride Duration**: In minutes (from historical segment data)
     - **Unit Price**: Price per minute (from historical segment data)
   - Large estimated total price display
   - Loading spinner during API calls
   - Error handling with user-friendly messages

3. **Auto-fetch Logic (useEffect Hook)**
   - Automatically fetches price estimates when user changes:
     - Location Category
     - Loyalty Status
     - Vehicle Type
     - Pricing Model
   - No manual button click needed
   - Debounced to prevent excessive API calls

**Updated:**
- Form data interface to include `locationCategory` field
- Added `PriceEstimate` interface for type safety
- Reset form function to include new location category field

---

## How It Works

### User Experience Flow:

1. **User opens form** → Default values loaded (Urban, Regular, Economy, STANDARD)
2. **Initial estimate fetched** → Shows default segment pricing
3. **User selects "Premium" vehicle** → Estimate automatically updates
4. **User changes to "Gold" loyalty** → Estimate automatically updates
5. **User changes location to "Suburban"** → Estimate automatically updates
6. **User submits form** → Order created with estimated pricing

### Technical Flow:

```
User Input Change
    ↓
useEffect Triggered
    ↓
POST /api/v1/orders/estimate
    ↓
Backend: segment_analysis.calculate_segment_estimate()
    ↓
Query MongoDB historical_rides collection
    ↓
Calculate segment averages:
    - segment_avg_fcs_unit_price
    - segment_avg_fcs_ride_duration
    - segment_demand_profile (HIGH/MEDIUM/LOW)
    ↓
Return estimate to frontend
    ↓
Update UI with new pricing data
```

---

## Data Displayed

### Demand Level
- **Source:** `historical_baseline.segment_demand_profile`
- **Values:** HIGH, MEDIUM, LOW
- **Calculation:** Based on driver-to-rider ratio in segment
- **Display:** Color-coded badge with emoji indicator

### Ride Duration
- **Source:** `historical_baseline.segment_avg_fcs_ride_duration`
- **Units:** Minutes
- **Calculation:** Average of all historical rides in segment
- **Display:** Numeric value with "min" suffix

### Unit Price
- **Source:** `historical_baseline.segment_avg_fcs_unit_price`
- **Units:** Dollars per minute
- **Calculation:** Average price per minute across segment
- **Display:** Dollar amount with 2 decimal places

### Estimated Total Price
- **Source:** `estimated_price` from backend
- **Calculation:** Unit price × duration × multipliers
- **Display:** Large dollar amount in green gradient card

---

## Backend Integration

The form uses the existing backend endpoint:

**Endpoint:** `POST /api/v1/orders/estimate`

**Request Schema (OrderEstimateRequest):**
```json
{
  "location_category": "Urban",
  "loyalty_tier": "Gold",
  "vehicle_type": "Premium",
  "pricing_model": "STANDARD"
}
```

**Response Schema (OrderEstimateResponse):**
```json
{
  "segment": {...},
  "historical_baseline": {
    "segment_avg_fcs_unit_price": 2.45,
    "segment_avg_fcs_ride_duration": 18.5,
    "segment_demand_profile": "MEDIUM",
    "sample_size": 150
  },
  "forecast_prediction": {...},
  "estimated_price": 45.33,
  "explanation": "...",
  "assumptions": [...]
}
```

---

## UI/UX Improvements

### Visual Design:
- **Gradient background** (blue-50 to indigo-50) for pricing section
- **Color-coded demand levels**:
  - 🔥 HIGH = Red (high demand, less drivers)
  - 📊 MEDIUM = Yellow (balanced)
  - ✅ LOW = Green (low demand, more drivers)
- **Card-based metric display** for easy scanning
- **Loading spinner** during API calls
- **Responsive grid layout** (3 columns on desktop, stacks on mobile)

### User Feedback:
- Loading state with spinner icon
- Error messages in red alert box
- Real-time updates with smooth transitions
- Contextual help text under each field
- Icon indicators for visual clarity

---

## Testing Checklist

- [x] Form loads with default values
- [x] Initial estimate fetched on mount
- [x] Estimate updates when location category changes
- [x] Estimate updates when loyalty status changes
- [x] Estimate updates when vehicle type changes
- [x] Estimate updates when pricing model changes
- [x] Loading spinner shows during fetch
- [x] Error handling for failed API calls
- [x] Responsive design on mobile devices
- [x] All TypeScript types are correct
- [x] No linter errors

---

## Code Quality

✅ **No linter errors**  
✅ **Full TypeScript type safety**  
✅ **Responsive design**  
✅ **Error handling**  
✅ **Loading states**  
✅ **Clean, maintainable code**  
✅ **Follows existing code patterns**  

---

## Benefits

1. **Better UX:** Users see pricing instantly without clicking buttons
2. **Transparency:** Clear breakdown of demand, duration, and unit price
3. **Real-time:** Pricing updates as selections change
4. **Data-driven:** All metrics from MongoDB historical data
5. **Educational:** Users understand what affects pricing
6. **Reduced friction:** One less button to click before submission

---

## Future Enhancements (Optional)

1. Add route calculation (Origin → Destination) for exact distance/duration
2. Show forecast predictions alongside historical baseline
3. Add price trend indicator (↑ increasing, ↓ decreasing)
4. Display confidence score for estimates
5. Show similar past rides from segment
6. Add competitor pricing comparison

---

**Implementation Complete** ✅  
**Ready for User Testing** 🚀  
**Zero Linter Errors** ✨

