# Backend Architecture Summary

**Last Updated:** December 2, 2025  
**Version:** 2.0 (with Segment Dynamic Pricing Analytics)

---

## 1. Backend Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         CLIENT APPLICATIONS                                   │
│              (Frontend, Swagger UI, API Clients, Chatbot Interface)           │
└─────────────────────────────────┬────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          FASTAPI APPLICATION                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         API ROUTERS (10)                               │  │
│  │  /orders  /upload  /ml  /analytics  /chatbot  /pipeline               │  │
│  │  /agents/test  /reports  /users                                        │  │
│  └──────────────┬────────────────────────────┬──────────────────────────┘  │
└─────────────────┴┬───────────────────────────┴┬─────────────────────────────┘
                   │                            │
       ┌───────────▼──────────┐      ┌─────────▼──────────┐
       │  PRICING ENGINE      │      │ PROPHET ML MODEL   │
       │ (Dynamic Pricing)    │      │  (Forecasting)     │
       │ - Base fare          │      │ - Demand trends    │
       │ - Distance/time      │      │ - Seasonality      │
       │ - Surge multiplier   │      │ - Prophet model    │
       │ - Loyalty discount   │      └────────────────────┘
       │ - Rule multipliers   │
       └──────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────────────────────────┐
│                         AI AGENT SYSTEM (6 AGENTS)                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │           ORCHESTRATOR AGENT (Chatbot Router + Memory)               │   │
│  │   Routes queries to specialist agents using GPT-4o-mini               │   │
│  │   Maintains conversation memory (InMemorySaver + thread_id)           │   │
│  └────┬─────────┬──────────┬──────────┬──────────────────────────────┘   │
│       │         │          │          │                                    │
│  ┌────▼───┐ ┌──▼────┐ ┌───▼────┐ ┌───▼──────┐ ┌───────────────────┐     │
│  │ANALYSIS│ │PRICING│ │FORECAST│ │RECOMMEND-│ │  DATA INGESTION   │     │
│  │ AGENT  │ │ AGENT │ │ AGENT  │ │  ATION   │ │      AGENT        │     │
│  │        │ │       │ │        │ │  AGENT   │ │   (Background)    │     │
│  └────┬───┘ └───┬───┘ └───┬────┘ └───┬──────┘ └─────────┬─────────┘     │
│       │         │         │          │                     │               │
│       │    SPECIALIST AGENT PROCESSING                     │               │
│       │    - Query MongoDB (direct)                        │               │
│       │    - Query ChromaDB (RAG)                          │               │
│       │    - PricingEngine integration                     │               │
│       │    - Generate recommendations                      │               │
│       │                                                     │               │
│  ┌────┴─────────┴─────────┴──────────┴─────────────────────┴───────────┐  │
│  │              SHARED UTILITIES & HELPER MODULES                        │  │
│  │  - pricing_helpers.py     - forecasting_helpers.py                    │  │
│  │  - segment_analysis.py    - report_generator.py                       │  │
│  │  - utils.py (ChromaDB/MongoDB tools)                                  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└───────────────────────┬──────────────────────────┬────────────────────────┘
                        │                          │
          ┌─────────────▼─────────┐   ┌───────────▼─────────────┐
          │  MONGODB DATABASE     │   │  CHROMADB VECTORSTORE   │
          │ (Persistent Storage)  │   │   (RAG Embeddings)      │
          │  - 9 Collections      │   │   - 5 Collections       │
          └───────────┬───────────┘   └───────────▲─────────────┘
                      │                           │
                      └────── Change Streams ─────┘
                              (Monitored by Data Ingestion Agent)
```

---

## 2. MongoDB Collections (9)

### Core Data Collections

| Collection | Description | Used By |
|-----------|-------------|---------|
| `historical_rides` | HWCO historical ride data (completed orders, pricing, segments) | Analysis Agent, Forecasting Agent, Report Generator |
| `competitor_prices` | Lyft competitor pricing data for market analysis | Analysis Agent, Recommendation Agent, Report Generator |
| `ride_orders` | Active ride orders with priority queue (P0/P1/P2), estimated pricing | Orders API, Priority Queue, Pricing Agent |
| `customers` | Customer profiles, loyalty tiers, preferences | Analysis Agent, Pricing Agent |

### External Data Collections (n8n Workflows)

| Collection | Description | Used By |
|-----------|-------------|---------|
| `events_data` | Eventbrite events (concerts, sports, conferences) | Forecasting Agent, Analysis Agent |
| `traffic_data` | Google Maps traffic patterns and congestion | Forecasting Agent, Analysis Agent |
| `news_articles` | NewsAPI articles (local news, market trends) | Analysis Agent, Recommendation Agent |

### Pipeline & Strategy Collections

| Collection | Description | Used By |
|-----------|-------------|---------|
| `pricing_strategies` | Business objectives, pricing rules, ML metadata, **per_segment_impacts**, pipeline results | All Agents, Report Generator, Pipeline Orchestrator |
| `pipeline_results` | Complete pipeline execution records with timestamps | Pipeline API, Report Generator |

**NEW in v2.0:** `pricing_strategies` now stores **per_segment_impacts** for all 162 segments × 3 recommendations = 486 detailed records per pipeline run.

---

## 3. ChromaDB Collections (5)

Created automatically by Data Ingestion Agent with OpenAI embeddings:

| Collection | Source | Embedding Model | Used By |
|-----------|--------|-----------------|---------|
| `ride_scenarios_vectors` | historical_rides, ride_orders | text-embedding-3-small (1536d) | Pricing Agent, Analysis Agent |
| `news_events_vectors` | events_data, news_articles | text-embedding-3-small (1536d) | Forecasting Agent, Recommendation Agent, Analysis Agent |
| `customer_behavior_vectors` | customers | text-embedding-3-small (1536d) | Analysis Agent, Recommendation Agent |
| `strategy_knowledge_vectors` | pricing_strategies | text-embedding-3-small (1536d) | Recommendation Agent (primary), Pricing Agent |
| `competitor_analysis_vectors` | competitor_prices | text-embedding-3-small (1536d) | Recommendation Agent, Analysis Agent |

**Metadata:** Every embedding includes `mongodb_id` for document retrieval in RAG pattern.

---

## 4. Backend Agents (6)

### 1. Data Ingestion Agent
**File:** `app/agents/data_ingestion.py`  
**Type:** Background process (runs independently)  
**Purpose:** Monitors MongoDB changes and creates ChromaDB embeddings for RAG

**Inputs:** 
- MongoDB change streams (all 9 collections)

**Processing:**
1. Detects document changes via MongoDB change streams
2. Generates text descriptions for each document
3. Creates OpenAI embeddings (text-embedding-3-small, 1536d)
4. Stores in ChromaDB with metadata (mongodb_id, collection, timestamp)

**Outputs:** 
- 5 ChromaDB collections with embeddings
- Enables RAG queries for other agents

**Run:** `python app/agents/data_ingestion.py`

---

### 2. Orchestrator Agent (Chatbot Router)
**File:** `app/agents/orchestrator.py`  
**Model:** GPT-4o-mini  
**Purpose:** Routes user queries to specialist agents with conversation memory

**Inputs:** 
- User query (string)
- Thread ID for conversation continuity

**Tools (4 routing tools):**
1. `route_to_analysis_agent` - For KPIs, revenue, historical data, **segment reports**
2. `route_to_pricing_agent` - For price calculations, estimates, segment pricing
3. `route_to_forecasting_agent` - For demand predictions, ML forecasts
4. `route_to_recommendation_agent` - For strategic advice, business objectives

**Processing:**
1. Analyzes user query intent using GPT-4o-mini
2. Selects appropriate specialist agent
3. Routes query with context
4. Receives specialist response
5. Updates conversation memory (thread_id)

**Outputs:** 
- Formatted response from specialist agent
- Maintained conversation context

**Memory:** Uses `InMemorySaver()` checkpointer for conversation history

---

### 3. Analysis Agent
**File:** `app/agents/analysis.py`  
**Model:** GPT-4o-mini  
**Purpose:** Business intelligence, KPIs, data analysis, **segment report queries**

**Inputs:** 
- Queries about revenue, KPIs, historical data, segments, competitors

**Tools (15+ tools including):**
- `calculate_revenue_kpis` - MongoDB query for revenue metrics
- `get_monthly_price_statistics` - Monthly price averages from MongoDB
- `compare_with_competitors` - HWCO vs Lyft comparison
- `analyze_event_impact_on_demand` - Events data analysis
- `analyze_traffic_patterns` - Traffic data analysis
- `generate_and_rank_pricing_rules` - Rule generation from current data patterns
- `calculate_whatif_impact_for_pipeline` - What-if analysis with PricingEngine
- `get_competitor_segment_baseline` - **NEW:** Lyft pricing per segment
- `query_segment_dynamic_pricing_report` - **NEW:** Segment report chatbot tool
- ChromaDB RAG tools for semantic search

**Processing:**
1. Queries MongoDB directly for actual data
2. Uses ChromaDB for semantic/contextual searches
3. Generates pricing rules from data patterns
4. Performs what-if analysis using PricingEngine
5. **NEW:** Queries and filters segment dynamic pricing reports

**Outputs:** 
- JSON with analysis results
- Pricing rules with impact estimates
- KPI projections
- **NEW:** Filtered segment pricing reports
- Natural language explanations

**Database Access:** Synchronous PyMongo (reliable for LangChain tools)

---

### 4. Pricing Agent
**File:** `app/agents/pricing.py`  
**Model:** GPT-4o-mini  
**Purpose:** Dynamic price calculation and segment-based estimates

**Inputs:** 
- Order data (location, distance, duration, vehicle, loyalty, pricing_model)
- Segment dimensions for estimation queries

**Tools (4 tools):**
1. `calculate_ride_price` - Uses PricingEngine for dynamic pricing
2. `estimate_ride_price` - **NEW:** Segment-based price estimation
3. `query_pricing_scenarios` - ChromaDB RAG for similar scenarios
4. `query_pricing_strategies` - ChromaDB RAG for pricing rules

**Processing:**
1. Uses `PricingEngine` to calculate prices with detailed breakdowns
2. **NEW:** Uses `segment_analysis.py` for segment-based estimates
3. Applies surge multipliers, loyalty discounts, rule multipliers
4. Queries historical pricing scenarios via ChromaDB
5. Retrieves pricing strategies from MongoDB

**Outputs:** 
- JSON with `final_price`
- Detailed breakdown (base, distance, time, surge, loyalty, rules)
- Pricing explanation
- **NEW:** Segment-based estimates with historical/forecast baselines

---

### 5. Forecasting Agent
**File:** `app/agents/forecasting.py`  
**Model:** GPT-4o-mini  
**Purpose:** Multi-dimensional demand and price forecasting

**Inputs:** 
- Forecast periods (30/60/90 days)
- Segment filters (optional)
- External data context (events, traffic, news)

**Tools (4 tools):**
1. `generate_multidimensional_forecast` - **162 segments** (5 dimensions)
2. `query_events_forecast` - ChromaDB RAG for event impacts
3. `explain_forecast_methodology` - Generates explanations
4. `check_ml_model_readiness` - Verifies Prophet ML model

**Processing:**
1. Generates forecasts across 5 dimensions = **162 segments**:
   - Location Category (Urban, Suburban, Rural) = 3
   - Loyalty Tier (Gold, Silver, Regular) = 3
   - Vehicle Type (Economy, Premium) = 2
   - Demand Profile (HIGH, MEDIUM, LOW) = 3
   - Pricing Model (STANDARD, SUBSCRIPTION, PAY_PER_RIDE) = 3
2. Uses `forecasting_helpers.py` for Prophet ML extensibility
3. Uses `PricingEngine` (via `pricing_helpers.py`) for price forecasts
4. Incorporates external data (events, traffic, news) via ChromaDB
5. Calculates baseline metrics and predicted rides/revenue

**Outputs:** 
- JSON with segmented forecasts (162 segments)
- Each segment: baseline metrics, forecast_30d/60d/90d
- Aggregated totals across all segments
- Forecast methodology explanation

**Helpers:** `app/agents/forecasting_helpers.py` for Prophet ML integration

---

### 6. Recommendation Agent
**File:** `app/agents/recommendation.py`  
**Model:** GPT-4o-mini  
**Purpose:** Strategic recommendations and rule impact simulation

**Inputs:** 
- Forecasts (from Forecasting Agent)
- Pricing rules (from Analysis Agent)
- Business objectives (revenue, profit, competitiveness, retention)

**Tools (5 tools):**
1. `generate_strategic_recommendations` - **NEW:** Returns per_segment_impacts
2. `query_strategy_knowledge` - ChromaDB RAG for business rules
3. `query_recent_events` - ChromaDB RAG for market conditions
4. `query_competitor_analysis` - ChromaDB RAG for competitive data
5. `get_competitor_comparison` - HWCO vs Lyft comparison

**Processing:**
1. Simulates pricing rules across all 162 segments using `PricingEngine`
2. Calculates demand impact using segment-specific elasticity
3. Ranks rule combinations by business objective achievement
4. **NEW:** Generates per_segment_impacts for top 3 recommendations
5. Returns minimum rule sets that achieve all 4 objectives

**Outputs:** 
- JSON with top 3 strategic recommendations
- Each recommendation: rules, objectives achieved, revenue impact
- **NEW:** `per_segment_impacts` = 162 segments × 3 recommendations = 486 records
- Rule combination rationale

**Business Objectives:**
1. Maximize Revenue (15-25% increase)
2. Maximize Profit Margins
3. Stay Competitive
4. Customer Retention (10-15% churn reduction)

---

## 5. Segment Dynamic Pricing Report (NEW in v2.0)

### Overview
Comprehensive per-segment analytics for all **162 segments** with **5 pricing scenarios** per segment.

### Components

**Report Generator:**  
- File: `app/utils/report_generator.py`
- Function: `generate_segment_dynamic_pricing_report()`
- Function: `convert_report_to_csv()`

**API Router:**  
- File: `app/routers/reports.py`
- Endpoints: 3 endpoints for JSON/CSV/summary

**Schemas:**  
- File: `app/models/schemas.py`
- 6 new schemas: SegmentIdentifier, SegmentScenario, SegmentDynamicPricingRow, ReportMetadata, SegmentDynamicPricingReport, SegmentDynamicPricingReportRequest

### Data Structure

**Per Segment (162 segments):**
```
{
  "segment": {
    "location_category": "Urban",
    "loyalty_tier": "Gold",
    "vehicle_type": "Premium",
    "demand_profile": "HIGH",
    "pricing_model": "STANDARD"
  },
  "hwco_continue_current": {
    "rides_30d": 100,
    "unit_price": 50.0,
    "revenue_30d": 5000.0,
    "explanation": "HWCO historical average..."
  },
  "lyft_continue_current": { ... },
  "recommendation_1": { ... },
  "recommendation_2": { ... },
  "recommendation_3": { ... }
}
```

### API Endpoints

1. **GET /api/v1/reports/segment-dynamic-pricing-analysis?format=json**
   - Returns: Complete 162-segment report in JSON
   - Use: Programmatic access, frontend dashboards

2. **GET /api/v1/reports/segment-dynamic-pricing-analysis?format=csv**
   - Returns: CSV file download (25 columns)
   - Use: Offline analysis, Excel integration

3. **GET /api/v1/reports/segment-dynamic-pricing-analysis/summary**
   - Returns: Aggregate statistics and revenue uplift %
   - Use: Dashboard quick view

### Chatbot Integration

**Tool:** `query_segment_dynamic_pricing_report` (Analysis Agent)

**Example Queries:**
- "Show me segment pricing report for Urban Gold Premium"
- "What are forecasted prices for all segments?"
- "Compare HWCO vs Lyft for Suburban segments"

**Functionality:**
- Natural language filtering by segment dimensions
- Returns JSON with filtered segment data
- Integrated with Analysis Agent routing

### Storage

**Per-segment impacts stored in TWO MongoDB collections:**

1. **pipeline_results** (complete record):
   ```json
   {
     "run_id": "...",
     "results": {
       "recommendations": {
         "per_segment_impacts": {
           "recommendation_1": [...162 segments...],
           "recommendation_2": [...162 segments...],
           "recommendation_3": [...162 segments...]
         }
       }
     }
   }
   ```

2. **pricing_strategies** (fast retrieval):
   ```json
   {
     "pipeline_run_id": "...",
     "per_segment_impacts": {
       "recommendation_1": [...162 segments...],
       "recommendation_2": [...162 segments...],
       "recommendation_3": [...162 segments...]
     },
     "metadata": {
       "total_segments": 486,
       "recommendation_count": 3
     }
   }
   ```

### Testing
- **Test File:** `tests/test_segment_dynamic_pricing_report.py`
- **Tests:** 7 tests covering report generation, CSV conversion, API endpoints, chatbot tools
- **Status:** ✅ 100% pass rate
- **Documentation:** `tests/README_TESTING_SEGMENT_DYNAMIC_PRICING_REPORT.md`
- **Results:** `tests/TEST_RESULTS_SEGMENT_DYNAMIC_PRICING.md`

---

## 6. Data Ingestion Pipeline Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      1. DATA UPLOAD & INGESTION                           │
└─────────────────────────────┬────────────────────────────────────────────┘
                              │
                 ┌────────────┴───────────┐
                 │                        │
          ┌──────▼─────────┐     ┌───────▼────────┐
          │  CSV UPLOAD    │     │  n8n WORKFLOWS │
          │  /upload/*     │     │  (Background)  │
          │  - Historical  │     │  - Eventbrite  │
          │  - Competitor  │     │  - Google Maps │
          └──────┬─────────┘     │  - NewsAPI     │
                 │               └───────┬────────┘
                 └────────────┬──────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────────┐
│                      2. MONGODB STORAGE (9 collections)                 │
│  historical_rides, competitor_prices, events_data, traffic_data,        │
│  news_articles, customers, ride_orders, pricing_strategies,             │
│  pipeline_results                                                        │
└─────────────────────────────┬──────────────────────────────────────────┘
                              │
                              │ Change Streams Monitor
                              │
┌─────────────────────────────▼──────────────────────────────────────────┐
│            3. DATA INGESTION AGENT (Background Process)                 │
│  - Detects MongoDB changes via change streams                           │
│  - Generates text descriptions for each document                        │
│  - Creates OpenAI embeddings (text-embedding-3-small, 1536d)            │
│  - Stores in 5 ChromaDB collections with metadata                       │
└─────────────────────────────┬──────────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────────┐
│           4. PIPELINE ORCHESTRATOR (Auto/Manual Trigger)                │
│  Triggers: Threshold reached (configurable) OR manual API request       │
└────────────┬─────────────────────────────┬───────────────────────────┘
             │                             │
    ┌────────▼─────────┐         ┌────────▼─────────┐
    │ FORECASTING      │         │  ANALYSIS        │
    │   AGENT          │         │    AGENT         │
    │ (Phase 1)        │         │  (Phase 1)       │
    │ - 162 segments   │         │ - Generate rules │
    │ - 30/60/90d      │         │ - Analyze data   │
    │ - PricingEngine  │         │ - External data  │
    └────────┬─────────┘         └────────┬─────────┘
             │                             │
             └──────────┬──────────────────┘
                        │
             ┌──────────▼──────────┐
             │ RECOMMENDATION       │
             │     AGENT            │
             │   (Phase 2)          │
             │ - Simulate rules     │
             │ - Rank combinations  │
             │ - Top 3 strategies   │
             │ - per_segment_impacts│ ◄── NEW: 486 records
             └──────────┬───────────┘
                        │
             ┌──────────▼──────────┐
             │  WHAT-IF ANALYSIS   │
             │   (Phase 3)         │
             │ - KPI projections   │
             │ - Revenue impact    │
             │ - Risk assessment   │
             └──────────┬───────────┘
                        │
┌───────────────────────▼────────────────────────────────────────────────┐
│      5. RESULTS STORAGE (MongoDB: pricing_strategies + pipeline_results)│
│                                                                          │
│  pipeline_results:                                                       │
│  - Complete pipeline execution record                                    │
│  - Timestamps, phases, errors                                            │
│  - forecasts (segmented + aggregated)                                    │
│  - pricing_rules                                                         │
│  - recommendations with per_segment_impacts (NEW)                        │
│  - whatif_analysis                                                       │
│                                                                          │
│  pricing_strategies:                                                     │
│  - per_segment_impacts for fast retrieval (NEW)                         │
│  - 162 segments × 3 recommendations = 486 records                        │
│  - Indexed by pipeline_run_id                                            │
└──────────────────────────────────────────────────────────────────────────┘
```

**NEW in v2.0:** Pipeline now stores detailed per-segment impacts for all 3 recommendations in both collections.

---

## 7. Chatbot Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                1. USER QUERY (via /chatbot/chat)                      │
│         WebSocket or HTTP POST with message + thread_id               │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────────────┐
│           2. ORCHESTRATOR AGENT (Chatbot Router + Memory)             │
│  - Receives user message + thread_id                                  │
│  - Retrieves conversation history from InMemorySaver                  │
│  - Uses GPT-4o-mini to analyze query intent                           │
│  - Selects appropriate routing tool                                   │
└───────┬────────────┬────────────┬───────────┬────────────────────────┘
        │            │            │           │
   ┌────▼─────┐ ┌───▼────┐ ┌─────▼────┐ ┌────▼──────────┐
   │ ANALYSIS │ │ PRICING│ │FORECASTING│ │RECOMMENDATION │
   │  AGENT   │ │ AGENT  │ │  AGENT    │ │    AGENT      │
   └────┬─────┘ └───┬────┘ └─────┬─────┘ └────┬──────────┘
        │           │            │            │
        │     3. SPECIALIST AGENT PROCESSING │
        │     - Queries MongoDB (direct)     │
        │     - Queries ChromaDB (RAG)       │
        │     - Uses PricingEngine           │
        │     - Uses segment_analysis        │ ◄── NEW
        │     - Queries segment reports      │ ◄── NEW
        │     - Generates recommendations    │
        │                                    │
        └────────────┬───────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────────────┐
│        4. ORCHESTRATOR RECEIVES SPECIALIST RESPONSE                   │
│  - Formats response for user                                          │
│  - Updates conversation memory (thread_id)                            │
│  - Saves to InMemorySaver checkpointer                                │
└────────────────────────────┬──────────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────────────┐
│              5. RESPONSE RETURNED TO USER                              │
│  WebSocket message or HTTP response with formatted answer              │
│  Conversation context maintained for follow-up queries                 │
└────────────────────────────────────────────────────────────────────────┘
```

**NEW in v2.0:** Chatbot can query segment dynamic pricing reports via natural language.

---

## 8. Key Technologies

### Core Framework
- **FastAPI** - Modern Python web framework with async support
- **Python 3.12** - Latest Python with improved performance

### Databases
- **MongoDB** - Document database (9 collections)
  - Motor (async) for FastAPI endpoints
  - PyMongo (sync) for LangChain agent tools
- **ChromaDB** - Vector database (5 collections)
  - Persistent local storage
  - OpenAI embeddings (1536 dimensions)
- **Redis** (optional) - Priority queue system

### AI/ML
- **LangChain v1.0** - Agent framework
- **LangGraph v1.0** - Agent orchestration
- **OpenAI GPT-4o-mini** - LLM for agents
- **OpenAI text-embedding-3-small** - Embeddings (1536d)
- **Prophet ML** - Time series forecasting

### Testing
- **pytest** - Test framework
- **pytest-asyncio** - Async test support
- **unittest.mock** - Mocking for unit tests
- **Total:** 146+ tests, 100% pass rate

---

## 9. API Endpoints Summary

### Orders & Pricing
- `POST /api/v1/orders` - Create order with estimated pricing
- `POST /api/v1/orders/estimate` - Get price estimate without order creation
- `GET /api/v1/orders` - List orders
- `GET /api/v1/orders/{order_id}` - Get order details

### Uploads & Data Ingestion
- `POST /api/v1/upload/historical-data` - Upload HWCO historical data
- `POST /api/v1/upload/competitor-data` - Upload Lyft competitor data
- `POST /api/v1/upload/sync-strategies-to-chromadb` - Manual ChromaDB sync

### Machine Learning
- `POST /api/v1/ml/train` - Train Prophet ML model
- `GET /api/v1/ml/forecast` - Generate forecasts (30/60/90 days)
- `GET /api/v1/ml/model-info` - Model metadata and accuracy metrics

### Analytics
- `GET /api/v1/analytics/revenue` - Revenue KPIs
- `GET /api/v1/analytics/segment-analysis` - Segment performance

### Pipeline Orchestration
- `POST /api/v1/pipeline/trigger` - Manually trigger pipeline
- `GET /api/v1/pipeline/status` - Get pipeline status
- `GET /api/v1/pipeline/history` - Get pipeline run history

### Reports (NEW)
- `GET /api/v1/reports/segment-dynamic-pricing-analysis?format=json` - Full report (JSON)
- `GET /api/v1/reports/segment-dynamic-pricing-analysis?format=csv` - Full report (CSV download)
- `GET /api/v1/reports/segment-dynamic-pricing-analysis/summary` - Aggregate summary

### Chatbot
- `POST /api/v1/chatbot/chat` - Send message to chatbot
- WebSocket support for real-time messaging

### Agent Testing (Swagger UI)
- `POST /api/v1/agents/test/analysis` - Test Analysis Agent
- `POST /api/v1/agents/test/pricing` - Test Pricing Agent
- `POST /api/v1/agents/test/forecasting` - Test Forecasting Agent
- `POST /api/v1/agents/test/recommendation` - Test Recommendation Agent

---

## 10. File Structure Summary

```
backend/
├── app/
│   ├── main.py                     # FastAPI app initialization
│   ├── config.py                   # Configuration (reads .env)
│   ├── database.py                 # MongoDB connection (Motor)
│   ├── redis_client.py             # Redis connection
│   ├── pricing_engine.py           # Dynamic pricing calculations
│   ├── forecasting_ml.py           # Prophet ML forecasting
│   ├── priority_queue.py           # Priority queue system
│   ├── pipeline_orchestrator.py    # Pipeline automation
│   │
│   ├── agents/                     # 6 AI Agents
│   │   ├── data_ingestion.py      # Background: MongoDB → ChromaDB
│   │   ├── orchestrator.py        # Chatbot router with memory
│   │   ├── analysis.py            # Business intelligence + segment reports
│   │   ├── pricing.py             # Dynamic pricing + estimates
│   │   ├── forecasting.py         # Multi-dimensional forecasting
│   │   ├── recommendation.py      # Strategic recommendations
│   │   ├── utils.py               # Shared utilities (ChromaDB, MongoDB)
│   │   ├── pricing_helpers.py     # PricingEngine integration
│   │   ├── forecasting_helpers.py # Prophet ML helpers
│   │   └── segment_analysis.py    # Segment estimation logic
│   │
│   ├── routers/                    # 10 API Routers
│   │   ├── orders.py              # Order management
│   │   ├── upload.py              # File uploads
│   │   ├── ml.py                  # ML endpoints
│   │   ├── analytics.py           # Analytics
│   │   ├── chatbot.py             # Chatbot
│   │   ├── pipeline.py            # Pipeline control
│   │   ├── agent_tests.py         # Agent testing
│   │   ├── reports.py             # Segment reports (NEW)
│   │   └── users.py               # User management
│   │
│   ├── utils/                      # Utility modules
│   │   └── report_generator.py    # Segment report generation (NEW)
│   │
│   └── models/
│       └── schemas.py              # Pydantic schemas (includes report schemas)
│
├── tests/                          # 146+ tests, 100% pass rate
│   ├── test_segment_dynamic_pricing_report.py  # NEW: 7/7 tests
│   ├── README_TESTING_SEGMENT_DYNAMIC_PRICING_REPORT.md
│   ├── TEST_RESULTS_SEGMENT_DYNAMIC_PRICING.md
│   └── ... (other test files)
│
├── models/
│   └── rideshare_forecast.pkl     # Trained Prophet ML model
│
├── chroma_db/                      # ChromaDB persistent storage
│
├── requirements.txt                # Python dependencies
└── README.md                       # Complete documentation
```

---

## 11. Recent Updates (v2.0)

### Segment Dynamic Pricing Analytics (December 2025)

**NEW Features:**
1. ✅ Per-segment impact tracking (162 segments × 3 recommendations = 486 records)
2. ✅ Report Generator module with JSON/CSV export
3. ✅ Reports API router with 3 endpoints
4. ✅ Chatbot tool for natural language segment queries
5. ✅ Dual storage in pipeline_results and pricing_strategies
6. ✅ Competitor baseline tool (Lyft pricing per segment)
7. ✅ 6 new Pydantic schemas for report data structures
8. ✅ Comprehensive testing (7 tests, 100% pass rate)

**Files Added:**
- `app/utils/report_generator.py`
- `app/routers/reports.py`
- `tests/test_segment_dynamic_pricing_report.py`
- `tests/README_TESTING_SEGMENT_DYNAMIC_PRICING_REPORT.md`
- `tests/TEST_RESULTS_SEGMENT_DYNAMIC_PRICING.md`

**Files Modified:**
- `app/agents/recommendation.py` - Returns per_segment_impacts
- `app/agents/analysis.py` - Added 2 new tools
- `app/agents/orchestrator.py` - Updated routing prompts
- `app/pipeline_orchestrator.py` - Enhanced storage logic
- `app/models/schemas.py` - Added 6 report schemas
- `app/main.py` - Registered reports router

**Impact:**
- Frontend can now display interactive segment pricing dashboards
- Chatbot can answer segment-specific pricing questions
- CSV export enables offline analysis in Excel
- Historical tracking of segment-level performance
- Detailed comparison of HWCO vs Lyft vs Recommendations

---

**End of Architecture Summary**
