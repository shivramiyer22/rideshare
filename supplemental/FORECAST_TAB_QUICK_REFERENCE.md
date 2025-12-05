# Forecast Tab Integration - Quick Reference Card

## 📋 At a Glance

**Current State:** 100% Mock Data ❌  
**Target State:** 100% Backend Integration ✅  
**Total Tasks:** 7 Phases  
**Estimated Time:** 4 weeks  

---

## 🎯 Integration Points (10 Mock Components)

| # | Component | Status | Backend Endpoint | Priority |
|---|-----------|--------|------------------|----------|
| 1 | Forecast Chart Data | ❌ Mock | `GET /api/v1/ml/forecast/{horizon}` | ⭐⭐⭐ HIGH |
| 2 | Avg Demand Metric | ❌ Mock | Same as #1 | ⭐⭐⭐ HIGH |
| 3 | Trend Direction | ❌ Mock | Same as #1 | ⭐⭐⭐ HIGH |
| 4 | MAPE Metric | ❌ Mock | `GET /api/v1/ml/model-info` 🔧 NEW | ⭐⭐⭐ HIGH |
| 5 | Confidence Metric | ❌ Mock | Same as #4 | ⭐⭐⭐ HIGH |
| 6 | Weekly Seasonality | ❌ Mock | `GET /api/v1/ml/seasonality` 🔧 NEW | ⭐⭐ MEDIUM |
| 7 | Daily Seasonality | ❌ Mock | Same as #6 | ⭐⭐ MEDIUM |
| 8 | External Factors | ❌ Mock | `GET /api/v1/analytics/external-factors` 🔧 NEW | ⭐⭐ MEDIUM |
| 9 | Recommendations | ❌ Mock | `POST /api/v1/chatbot/chat` ✅ EXISTS | ⭐ LOW |
| 10 | Explanations | ❌ Mock | `POST /api/v1/chatbot/chat` ✅ EXISTS | ⭐ LOW |

**Legend:**  
✅ = Backend ready to use  
🔧 = Need to create new endpoint  
❌ = Currently mock data  

---

## 🚀 Quick Start (Phase 1 - Highest Impact)

### Step 1: Update API Client (5 minutes)

```typescript
// frontend/src/lib/api.ts

export const mlAPI = {
  train: () => api.post('/api/v1/ml/train'),
  
  // ✅ ALREADY EXISTS - Just fix the call
  forecast: (horizon: '30d' | '60d' | '90d', pricingModel: string) =>
    api.get(`/api/v1/ml/forecast/${horizon}`, { 
      params: { pricing_model: pricingModel } 
    }),
};
```

### Step 2: Update Forecast Tab Component (15 minutes)

```typescript
// frontend/src/components/tabs/ForecastingTab.tsx

// REMOVE these mock functions
// ❌ const generate30DayForecast = () => { ... }
// ❌ const generate60DayForecast = () => { ... }
// ❌ const generate90DayForecast = () => { ... }

// ADD this fetch function
const fetchForecastData = async () => {
  setLoading(true);
  try {
    const response = await mlAPI.forecast(forecastHorizon, pricingModel);
    
    // Transform backend response to match chart format
    const transformedData = response.data.forecast.map((item: any) => ({
      date: item.date,
      predicted: item.predicted_demand,
      lower: item.confidence_lower,
      upper: item.confidence_upper,
      trend: item.trend
    }));
    
    setForecastData(prev => ({
      ...prev,
      [forecastHorizon]: transformedData
    }));
  } catch (error) {
    console.error('Forecast fetch failed:', error);
    // Show error to user
  } finally {
    setLoading(false);
  }
};

// CALL on component mount and when controls change
useEffect(() => {
  fetchForecastData();
}, [forecastHorizon, pricingModel]);
```

### Step 3: Update Refresh Handler (2 minutes)

```typescript
const handleRefresh = async () => {
  // REPLACE mock regeneration with real API call
  await fetchForecastData();
};
```

**Result:** Forecast chart now shows real Prophet ML predictions! 🎉

---

## 🔧 New Backend Endpoints to Create

### 1. Model Info Endpoint (Phase 2)

```python
# backend/app/routers/ml.py

@router.get("/model-info")
async def get_model_info() -> Dict[str, Any]:
    """Get Prophet ML model metadata and training statistics."""
    database = get_database()
    metadata_collection = database["ml_training_metadata"]
    
    metadata = await metadata_collection.find_one(
        {"type": "last_training"},
        sort=[("timestamp", -1)]
    )
    
    if metadata:
        return {
            "model_exists": forecast_model._model_exists(),
            "mape": metadata.get("mape", 0.0),
            "confidence": 0.80,
            "training_rows": metadata.get("training_rows", 0)
        }
    else:
        return {"model_exists": False, "error": "Model not trained"}
```

**Frontend Usage:**
```typescript
const modelInfo = await mlAPI.getModelInfo();
setMape(modelInfo.mape);
setConfidence(modelInfo.confidence * 100); // Convert to percentage
```

---

### 2. Seasonality Endpoint (Phase 3)

```python
# backend/app/routers/ml.py

@router.get("/seasonality")
async def get_seasonality_patterns() -> Dict[str, Any]:
    """Get weekly and daily seasonality patterns from Prophet model."""
    if not forecast_model._model_exists():
        raise HTTPException(status_code=400, detail="Model not trained")
    
    # Generate sample forecast to extract patterns
    loop = asyncio.get_event_loop()
    forecast_df = await loop.run_in_executor(
        None, forecast_model.forecast, "STANDARD", 7
    )
    
    # Extract weekly patterns
    weekly_effects = []
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for i in range(7):
        row = forecast_df.iloc[i]
        effect = row['yhat'] / row['trend'] if row['trend'] != 0 else 1.0
        weekly_effects.append({"day": day_names[i], "effect": float(effect)})
    
    # Daily patterns (sample hours)
    daily_effects = [
        {"hour": "6AM", "effect": 0.85},
        {"hour": "9AM", "effect": 1.30},
        # ... more hours
    ]
    
    return {
        "weekly_seasonality": weekly_effects,
        "daily_seasonality": daily_effects
    }
```

**Frontend Usage:**
```typescript
const seasonality = await mlAPI.getSeasonality();
setWeeklyData(seasonality.weekly_seasonality);
setDailyData(seasonality.daily_seasonality);
```

---

### 3. External Factors Endpoint (Phase 4)

```python
# backend/app/routers/analytics.py

@router.get("/external-factors")
async def get_external_factors(days: int = Query(30)) -> Dict[str, Any]:
    """Get external factors affecting demand in next N days."""
    database = get_database()
    
    from datetime import datetime, timedelta
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=days)
    
    # Fetch events
    events = await database["events_data"].find({
        "event_date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
    }).limit(10).to_list(10)
    
    # Fetch traffic
    traffic = await database["traffic_data"].find({}).sort("timestamp", -1).limit(5).to_list(5)
    
    # Fetch news
    news = await database["news_articles"].find({}).sort("published_at", -1).limit(5).to_list(5)
    
    # Format responses
    formatted_events = [{
        "title": e.get("event_name", "Event"),
        "date": e.get("event_date", ""),
        "type": e.get("event_type", "Other"),
        "estimated_impact": f"+{int(impact_map.get(e.get('event_type'), 0.15) * 100)}% demand"
    } for e in events]
    
    return {
        "events": formatted_events,
        "traffic": traffic,  # Format as needed
        "news": news         # Format as needed
    }
```

**Frontend Usage:**
```typescript
const factors = await analyticsAPI.externalFactors(30);
setEvents(factors.events);
setTraffic(factors.traffic);
setNews(factors.news);
```

---

## 🤖 AI Integration (Phases 5-6)

### Recommendations (Phase 5)

```typescript
const response = await api.post('/api/v1/chatbot/chat', {
  message: `Based on the ${forecastHorizon} forecast for ${pricingModel} pricing, provide strategic recommendations to maximize revenue and retention. Include specific actions and expected revenue impact.`,
  thread_id: 'forecast_tab_recommendations'
});

setRecommendations(response.data.response);
```

### Explanations (Phase 6)

```typescript
const response = await api.post('/api/v1/chatbot/chat', {
  message: `Explain the ${forecastHorizon} forecast for ${pricingModel}. What are the key drivers? Why is the trend ${trendDirection}?`,
  thread_id: 'forecast_tab_explanation'
});

setExplanation(response.data.response);
```

---

## ✅ Testing Checklist

### Backend Tests
```bash
cd backend

# Test existing forecast endpoint
curl "http://localhost:8000/api/v1/ml/forecast/30d?pricing_model=STANDARD"

# Test new model-info endpoint (after creating)
curl "http://localhost:8000/api/v1/ml/model-info"

# Test new seasonality endpoint (after creating)
curl "http://localhost:8000/api/v1/ml/seasonality"

# Test new external-factors endpoint (after creating)
curl "http://localhost:8000/api/v1/analytics/external-factors?days=30"
```

### Frontend Tests (Manual)
- [ ] Open Forecast Tab - No console errors
- [ ] Chart displays real data (not random)
- [ ] Switch pricing model - Chart updates
- [ ] Switch horizon - Chart updates with correct days
- [ ] Click Refresh - Data refetches
- [ ] MAPE shows real value (not 8.4%)
- [ ] Confidence shows 80% (not 92%)

---

## 📊 Success Metrics

**After Phase 1-2 (Week 1):**
- ✅ Forecast chart = Real ML predictions
- ✅ MAPE = Real model accuracy
- ✅ Confidence = Real 80% intervals
- ✅ Zero console errors

**After Phase 3-4 (Week 2-3):**
- ✅ Seasonality = Data-driven patterns
- ✅ Events = Real Eventbrite data
- ✅ Traffic = Real Google Maps data
- ✅ News = Real NewsAPI articles

**After Phase 5-6 (Week 4):**
- ✅ Recommendations = AI-generated
- ✅ Explanations = AI-generated
- ✅ **100% backend integration**
- ✅ **ZERO mock data**

---

## 🆘 Common Issues & Fixes

### Issue: "Model not trained" error
**Fix:** Train model first
```bash
curl -X POST "http://localhost:8000/api/v1/ml/train"
```

### Issue: "Insufficient data" error
**Fix:** Upload historical data
```bash
# Upload HWCO data
curl -X POST "http://localhost:8000/api/v1/upload/historical-data" \
  -F "file=@historical_rides.csv"

# Upload competitor data
curl -X POST "http://localhost:8000/api/v1/upload/competitor-data" \
  -F "file=@competitor_prices.csv"
```

### Issue: Chart not updating
**Fix:** Check `useEffect` dependencies
```typescript
useEffect(() => {
  fetchForecastData();
}, [forecastHorizon, pricingModel]); // Make sure these are in deps array
```

### Issue: Data format mismatch
**Fix:** Transform backend response
```typescript
const transformedData = response.data.forecast.map(item => ({
  date: item.date,
  predicted: item.predicted_demand,  // Match backend field names
  lower: item.confidence_lower,
  upper: item.confidence_upper,
  trend: item.trend
}));
```

---

## 📚 Full Documentation

- **Detailed Plan:** `FORECAST_TAB_BACKEND_INTEGRATION_PLAN.md`
- **Visual Map:** `FORECAST_TAB_VISUAL_MAP.md`
- **Summary:** `FORECAST_TAB_INTEGRATION_SUMMARY.md`
- **Backend Docs:** `backend/BACKEND_ARCHITECTURE_SUMMARY.md`

---

## 🎯 Start Here

**Fastest Path to Success:**
1. ✅ Phase 1 (Core forecast) - 20 min implementation
2. ✅ Test with real backend - 10 min
3. ✅ Phase 2 (Model metrics) - 30 min (create endpoint + integrate)
4. ✅ Celebrate! 🎉 You've replaced 50% of mock data

**Total Time Phase 1-2:** ~1 hour for major improvement

---

**Questions? Check the full integration plan or ask the team!**

