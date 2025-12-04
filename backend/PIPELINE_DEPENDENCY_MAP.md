"""
RIDESHARE DYNAMIC PRICING - COMPLETE PIPELINE DEPENDENCY MAP
=============================================================

This document maps all code dependencies for the entire agent pipeline process.

PIPELINE FLOW:
--------------
1. Data Ingestion (MongoDB Change Streams) → ChangeTracker records changes
2. Hourly Check (background_tasks.py) → Detects if changes exist
3. Pipeline Orchestrator → Coordinates all agents
4. Phase 1: Forecasting Agent (parallel with Analysis)
5. Phase 2: Analysis Agent (parallel with Forecasting)
6. Phase 3: Recommendation Agent (uses forecasts + rules)
7. Phase 4: What-If Analysis (tests top 3 recommendations)
8. Phase 5: Report Generation
9. Results stored in MongoDB pipeline_results collection


COMPONENT DEPENDENCY TREE:
===========================

┌─────────────────────────────────────────────────────────────────────────┐
│ 1. DATA INGESTION & CHANGE DETECTION                                    │
└─────────────────────────────────────────────────────────────────────────┘

app/agents/data_ingestion.py
├── ChangeTracker (class)
│   ├── record_change() - Records MongoDB changes
│   ├── has_pending_changes() - Check if pipeline should run
│   └── get_and_clear_changes() - Get summary and reset
├── monitor_change_streams() - Watches MongoDB for new data
└── ingest_and_embed_document() - Creates ChromaDB embeddings

Dependencies:
- pymongo (MongoDB change streams)
- chromadb (vector embeddings)
- app/database.py (MongoDB connection)
- app/config.py (settings)


┌─────────────────────────────────────────────────────────────────────────┐
│ 2. BACKGROUND SCHEDULER (Hourly Pipeline Trigger)                       │
└─────────────────────────────────────────────────────────────────────────┘

app/background_tasks.py
├── check_and_run_pipeline()
│   ├── Checks ChangeTracker.has_pending_changes()
│   ├── Calls run_agent_pipeline() if changes detected
│   └── Clears ChangeTracker after completion
├── check_and_retrain_ml_model() - Auto ML retraining
└── compute_analytics_kpis() - Dashboard pre-computation

Dependencies:
- apscheduler (AsyncIOScheduler)
- app/agents/data_ingestion.py (change_tracker)
- app/pipeline_orchestrator.py (run_agent_pipeline)
- app/forecasting_ml.py (RideshareForecastModel)


┌─────────────────────────────────────────────────────────────────────────┐
│ 3. PIPELINE ORCHESTRATOR (Main Coordinator)                             │
└─────────────────────────────────────────────────────────────────────────┘

app/pipeline_orchestrator.py
├── run_agent_pipeline()
│   ├── _run_forecasting_phase() - Parallel execution
│   ├── _run_analysis_phase() - Parallel execution
│   ├── _run_recommendation_phase() - Sequential (needs forecasts + rules)
│   ├── _run_whatif_phase() - Sequential (needs recommendations)
│   └── _save_pipeline_results() - Store to MongoDB
└── Context passing between phases:
    ├── forecasting → recommendation (forecast data)
    ├── analysis → recommendation (pricing rules)
    └── recommendation → whatif (top 3 recommendations)

Dependencies:
- app/agents/forecasting.py (ForecastingAgentExecutor)
- app/agents/analysis.py (AnalysisAgentExecutor)
- app/agents/recommendation.py (RecommendationAgentExecutor)
- app/agents/what_if.py (WhatIfAgentExecutor)
- app/database.py (pipeline_results collection)


┌─────────────────────────────────────────────────────────────────────────┐
│ 4. FORECASTING AGENT (Phase 1 - Parallel)                               │
└─────────────────────────────────────────────────────────────────────────┘

app/agents/forecasting.py
├── ForecastingAgentExecutor (LangGraph agent)
│   └── run() - Invokes forecast_demand tool
└── forecast_demand() - Tool
    ├── Fetches historical_rides from MongoDB
    ├── Segments data by 5 dimensions:
    │   - location_category (Urban/Suburban/Rural)
    │   - loyalty_tier (Gold/Silver/Regular)
    │   - vehicle_type (Economy/Premium)
    │   - pricing_model (STANDARD/SURGE/CONTRACTED/CUSTOM)
    │   - demand_profile (HIGH/MEDIUM/LOW)
    ├── Calculates segment_demand_profile:
    │   - ratio = avg_drivers / avg_riders
    │   - HIGH if ratio > 0.9
    │   - LOW if ratio < 0.7
    │   - MEDIUM otherwise
    ├── Calls RideshareForecastModel for each segment
    ├── Generates 30/60/90-day forecasts for:
    │   - predicted_rides
    │   - predicted_unit_price ($/min)
    │   - predicted_duration (minutes)
    │   - predicted_revenue
    └── Returns 162 segment forecasts + aggregated forecasts

Dependencies:
- app/forecasting_ml.py (RideshareForecastModel)
- app/agents/segment_analysis.py (calculate_segment_metrics)
- app/database.py (historical_rides, competitor_prices)
- app/models/schemas.py (ForecastPrediction)


┌─────────────────────────────────────────────────────────────────────────┐
│ 5. ML FORECASTING MODEL (Core ML Logic)                                 │
└─────────────────────────────────────────────────────────────────────────┘

app/forecasting_ml.py
├── RideshareForecastModel
│   ├── train() - Train Prophet with historical data
│   │   ├── 20 categorical regressors:
│   │   │   - Location_Category, Customer_Loyalty_Status, Vehicle_Type
│   │   │   - Pricing_Model, Hour, DayOfWeek, Month, IsWeekend
│   │   │   - IsRushHour, IsHoliday, Weather_Conditions, Traffic_Level
│   │   │   - Event_Type, Competitor_Pricing_Strategy, Driver_Availability_Level
│   │   │   - Route_Popularity, Payment_Method, Booking_Channel
│   │   │   - Service_Class, Demand_Profile
│   │   └── 4 numeric regressors:
│   │       - num_riders, num_drivers, ride_duration, unit_price
│   └── forecast() - Generate predictions for future dates
└── Model saved to: backend/models/prophet_forecast_model.pkl

Dependencies:
- prophet (Facebook Prophet ML library)
- pandas, numpy
- pickle (model serialization)


┌─────────────────────────────────────────────────────────────────────────┐
│ 6. ANALYSIS AGENT (Phase 2 - Parallel with Forecasting)                 │
└─────────────────────────────────────────────────────────────────────────┘

app/agents/analysis.py
├── AnalysisAgentExecutor (LangGraph agent)
│   └── run() - Invokes generate_and_rank_pricing_rules tool
└── generate_and_rank_pricing_rules() - Tool
    ├── Fetches data from MongoDB:
    │   - historical_rides
    │   - competitor_prices
    │   - events_data (n8n populated)
    │   - rideshare_news (n8n populated)
    │   - traffic_data
    ├── Calculates segment_demand_profile (same logic as forecasting)
    ├── Generates 9 categories of pricing rules:
    │   1. location_based (Urban/Suburban/Rural adjustments)
    │   2. loyalty_based (Gold/Silver retention incentives)
    │   3. demand_based (HIGH/MEDIUM/LOW surge/discounts)
    │   4. vehicle_based (Premium vs Economy pricing)
    │   5. event_based (High-impact events, festivals, sports) ← External data
    │   6. news_based (Competition, regulation changes) ← External data
    │   7. surge_based (Traffic congestion) ← External data
    │   8. time_based (Peak hours, weekends)
    │   9. pricing_based (Competitive positioning)
    ├── Ranks rules by:
    │   - estimated_impact (revenue % increase)
    │   - confidence (high/medium/low)
    │   - ride_count (number of rides affected)
    └── Returns top 20 rules with conditions & actions

Dependencies:
- app/database.py (MongoDB collections)
- app/models/schemas.py (PricingRule)


┌─────────────────────────────────────────────────────────────────────────┐
│ 7. RECOMMENDATION AGENT (Phase 3 - Sequential)                          │
└─────────────────────────────────────────────────────────────────────────┘

app/agents/recommendation.py
├── RecommendationAgentExecutor (LangGraph agent)
│   └── run() - Invokes generate_strategic_recommendations tool
└── generate_strategic_recommendations() - Tool
    ├── Input: forecasts (from Phase 1) + rules (from Phase 2)
    ├── Simulates rule impacts on each segment:
    │   - Checks if rule conditions match segment dimensions
    │   - Applies rule multiplier if match found
    │   - Calculates new_unit_price, new_revenue
    │   - Uses demand elasticity for ride count impact
    ├── Tests rule combinations (1-5 rules per combo)
    ├── Scores combinations by:
    │   - objectives_met * 1000
    │   - revenue_impact %
    │   - rule_count penalty
    ├── Selects top 3 recommendations
    ├── Generates per_segment_impacts for each recommendation:
    │   - For EACH of 162 segments:
    │     - baseline (ML forecast): unit_price, duration, rides, revenue
    │     - with_recommendation: new values after rules applied
    │     - applied_rules: list of rules that matched
    │     - If NO rules apply → keeps ML forecast unchanged ✅
    └── Returns:
        - 3 recommendations (rule combinations)
        - per_segment_impacts (162 segments × 3 recommendations = 486 records)

Dependencies:
- app/agents/pricing_helpers.py (rule matching, elasticity)
- app/models/schemas.py (SegmentScenario)


┌─────────────────────────────────────────────────────────────────────────┐
│ 8. WHAT-IF ANALYSIS AGENT (Phase 4 - Sequential)                        │
└─────────────────────────────────────────────────────────────────────────┘

app/agents/what_if.py
├── WhatIfAgentExecutor (LangGraph agent)
│   └── run() - Invokes analyze_recommendation_impact tool
└── analyze_recommendation_impact() - Tool
    ├── Input: Top 3 recommendations from Phase 3
    ├── For each recommendation:
    │   ├── Simulates market response
    │   ├── Calculates competitor reactions
    │   ├── Estimates demand elasticity impact
    │   ├── Projects 30/60/90-day outcomes
    │   └── Identifies risks and opportunities
    └── Returns impact analysis for all 3 recommendations

Dependencies:
- app/agents/recommendation.py (recommendation data)
- app/database.py (historical_rides, competitor_prices)


┌─────────────────────────────────────────────────────────────────────────┐
│ 9. REPORT GENERATOR (Phase 5 - Final Output)                            │
└─────────────────────────────────────────────────────────────────────────┘

app/utils/report_generator.py
├── generate_segment_pricing_report()
│   ├── Input: Latest pipeline_results from MongoDB
│   ├── For EACH of 162 segments:
│   │   ├── Fetches historical baseline (HWCO):
│   │   │   - Calculates avg unit_price = Historical_Cost_of_Ride / Expected_Ride_Duration
│   │   │   - Calculates revenue = rides × duration × unit_price
│   │   ├── Fetches competitor baseline (Lyft):
│   │   │   - Similar calculations
│   │   ├── Fetches per_segment_impacts from recommendation phase
│   │   │   - recommendation_1, recommendation_2, recommendation_3
│   │   └── Creates 5 scenarios per segment:
│   │       1. hwco_continue_current (baseline ML forecast)
│   │       2. lyft_competitor (competitor pricing)
│   │       3. recommendation_1 (top recommendation)
│   │       4. recommendation_2 (second recommendation)
│   │       5. recommendation_3 (third recommendation)
│   ├── Each scenario includes:
│   │   - rides_30d
│   │   - unit_price ($/min)
│   │   - duration_minutes
│   │   - revenue_30d
│   │   - explanation (detailed description)
│   └── Exports to CSV: backend/reports/FINAL_REPORT.csv
└── get_report_summary()
    └── Returns high-level stats (total segments, recommendations)

Dependencies:
- app/database.py (pipeline_results, historical_rides, competitor_prices)
- csv module


┌─────────────────────────────────────────────────────────────────────────┐
│ 10. SUPPORTING MODULES                                                   │
└─────────────────────────────────────────────────────────────────────────┘

app/pricing_engine.py
├── PricingEngine
│   └── calculate_price() - Dynamic price calculation
│       ├── Base price = duration × base_rate_per_minute
│       ├── Applies surge/loyalty multipliers
│       └── Returns final price + breakdown

app/agents/segment_analysis.py
├── calculate_segment_metrics() - Historical baseline computation
│   ├── Aggregates rides by segment
│   ├── Calculates averages: unit_price, duration, riders, drivers
│   └── Determines segment_demand_profile

app/models/schemas.py
├── Pydantic schemas for data validation:
│   ├── HistoricalBaseline
│   ├── ForecastPrediction
│   ├── PricingRule
│   ├── SegmentScenario
│   ├── OrderCreate / OrderResponse
│   └── PipelineResult

app/database.py
├── get_database() - MongoDB connection
└── Collections used:
    ├── historical_rides (7,750 documents)
    ├── competitor_prices
    ├── orders
    ├── pipeline_results (pipeline run history)
    ├── pricing_strategies (ChromaDB source)
    ├── events_data (n8n populated)
    ├── rideshare_news (n8n populated)
    ├── traffic_data
    └── analytics_cache


┌─────────────────────────────────────────────────────────────────────────┐
│ 11. EXTERNAL DEPENDENCIES                                                │
└─────────────────────────────────────────────────────────────────────────┘

ChromaDB:
├── Location: backend/chroma_db/
├── Purpose: Vector embeddings for RAG (chatbot)
└── Populated by: data_ingestion.py

MongoDB:
├── Connection: settings.mongodb_url
├── Database: rideshare_pricing
└── 9 collections (listed above)

Redis:
├── Purpose: Caching, rate limiting
└── Connection: settings.redis_url

n8n Workflows:
├── Populates: events_data collection
├── Populates: rideshare_news collection
└── External system (not part of backend)


DATA FLOW SUMMARY:
==================

1. n8n → MongoDB (events_data, rideshare_news)
2. ChangeTracker → Records all MongoDB changes
3. Hourly scheduler → Checks for changes
4. Pipeline triggered → run_agent_pipeline()
5. Forecasting (parallel) → 162 segment forecasts → MongoDB
6. Analysis (parallel) → 11 pricing rules → MongoDB
7. Recommendation → Top 3 combos + 486 per-segment impacts → MongoDB
8. What-If → Impact analysis for 3 recommendations → MongoDB
9. Report → CSV with all 162 segments × 5 scenarios → File system
10. API endpoints → Serve data to frontend


CRITICAL DATA MODEL FIELDS:
============================

Segment Dimensions (5 fields):
- location_category: Urban / Suburban / Rural
- loyalty_tier: Gold / Silver / Regular
- vehicle_type: Economy / Premium
- pricing_model: STANDARD / SURGE / CONTRACTED / CUSTOM
- demand_profile: HIGH / MEDIUM / LOW

Total Segments: 3 × 3 × 2 × 3 × 3 = 162 segments

New Duration-Based Pricing:
- segment_avg_fcs_unit_price: $/minute
- segment_avg_fcs_ride_duration: minutes
- estimated_price = unit_price × duration
- revenue = rides × unit_price × duration

Removed Fields (deprecated):
- pricing_tier (replaced by pricing_model)
- segment_avg_distance (replaced by segment_avg_fcs_ride_duration)
- segment_avg_price (replaced by segment_avg_fcs_unit_price)


TESTING STRATEGY:
=================

Unit Tests:
- Schema validation (Pydantic)
- Segment key generation
- Demand profile calculation
- Duration-based pricing logic
- Rule matching logic

Integration Tests:
- Full pipeline execution
- Data flow between phases
- 162 segments in forecasts
- 11 rules generated
- 486 per-segment impacts
- Report generation with 5 scenarios per segment

API Tests:
- All 38 endpoints
- Request/response validation
- Error handling
- Performance (< 5s per request)


DEPLOYMENT CHECKLIST:
=====================

□ MongoDB connected with 7,750+ historical rides
□ Redis running
□ ChromaDB initialized with embeddings
□ Prophet ML model trained (backend/models/prophet_forecast_model.pkl)
□ Background scheduler running (3 jobs)
□ Change stream monitoring active
□ All 38 API endpoints functional
□ Pipeline runs automatically every hour if changes detected
□ Reports generated with all 162 segments
□ Frontend can fetch segment analysis report


VERSION: 1.0.0
LAST UPDATED: 2025-12-04
REFACTORING STATUS: ✅ COMPLETE
"""