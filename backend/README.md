# Rideshare Backend

Python FastAPI backend application with LangChain & LangGraph integration, using MongoDB for persistent database and ChromaDB for vector database. Features 6 AI agents, Prophet ML forecasting, and dynamic pricing engine.

## Project Structure

```
backend/
├── app/                    # Contains the main application files
│   ├── __init__.py        # Makes "app" a Python package
│   ├── main.py            # Initializes the FastAPI application
│   ├── config.py          # Configuration settings (reads from root .env)
│   ├── database.py        # MongoDB connection using motor
│   ├── redis_client.py    # Redis connection for priority queues
│   ├── dependencies.py   # Defines dependencies used by the routers
│   ├── forecasting_ml.py  # Prophet ML forecasting (single model for all pricing types)
│   ├── pricing_engine.py  # Dynamic pricing engine (CONTRACTED/STANDARD/CUSTOM)
│   ├── priority_queue.py  # Priority queue system (P0/P1/P2)
│   ├── agents/            # 6 AI Agents
│   │   ├── data_ingestion.py    # Monitors MongoDB, creates ChromaDB embeddings
│   │   ├── orchestrator.py      # Chatbot Orchestrator (routes queries)
│   │   ├── analysis.py          # Analysis Agent (business intelligence)
│   │   ├── pricing.py           # Pricing Agent (dynamic pricing)
│   │   ├── forecasting.py       # Forecasting Agent (Prophet ML + n8n data)
│   │   └── recommendation.py    # Recommendation Agent (strategic advice with RAG)
│   ├── routers/           # Contains router modules
│   │   ├── items.py       # Routes and endpoints related to items
│   │   ├── users.py       # Routes and endpoints related to users
│   │   ├── orders.py      # Order creation, management, and priority queue endpoints
│   │   ├── ml.py          # Prophet ML training and forecasting endpoints (enhanced with pricing_model breakdown)
│   │   ├── upload.py      # File upload endpoints (historical data, competitor data)
│   │   ├── analytics.py   # Analytics dashboard endpoints
│   │   └── chatbot.py     # WebSocket chatbot endpoint
│   ├── agents/            # 6 AI Agents + Shared Utilities
│   │   ├── utils.py       # Shared utilities (ChromaDB & MongoDB querying functions)
│   │   │                   # - setup_chromadb_client()
│   │   │                   # - query_chromadb() - Similarity search
│   │   │                   # - fetch_mongodb_documents() - Full document retrieval
│   │   │                   # - format_documents_as_context() - Context formatting
│   │   ├── data_ingestion.py    # Monitors MongoDB, creates ChromaDB embeddings
│   │   ├── orchestrator.py      # Chatbot Orchestrator (routes queries with 4 routing tools)
│   │   ├── analysis.py          # Analysis Agent (4 ChromaDB querying tools)
│   │   ├── pricing.py           # Pricing Agent (3 tools: scenarios, strategies, price calculation)
│   │   ├── forecasting.py       # Forecasting Agent (3 tools: events, forecast, explanation)
│   │   └── recommendation.py    # Recommendation Agent (4 tools: strategy, events, competitor, recommendation)
│   ├── crud/              # Contains CRUD operation modules
│   │   ├── item.py        # CRUD operations for items
│   │   └── user.py        # CRUD operations for users
│   ├── schemas/           # Contains Pydantic schema modules
│   │   ├── item.py        # Schemas for items
│   │   └── user.py        # Schemas for users
│   ├── models/            # Contains database model modules
│   │   ├── item.py        # Database models for items
│   │   ├── user.py        # Database models for users
│   │   └── schemas.py     # Shared schemas
│   ├── external_services/ # Modules for interacting with external services
│   │   ├── email.py       # Functions for sending emails
│   │   └── notification.py # Functions for sending notifications
│   └── utils/             # Utility modules
│       ├── authentication.py # Functions for authentication
│       └── validation.py      # Functions for validation
├── tests/                 # Contains test modules
│   ├── test_main.py       # Tests for the main application
│   ├── test_items.py      # Tests for the items module
│   ├── test_users.py      # Tests for the users module
│   ├── test_connections.py # Connection tests (MongoDB, Redis)
│   ├── test_data_ingestion.py # Data Ingestion Agent tests (4/4 passing)
│   ├── test_prophet_ml.py # Prophet ML tests (5/5 passing)
│   ├── validate_code.py   # Code structure validation
│   └── README_testing.md  # Testing documentation
├── models/                # Saved Prophet ML models
│   └── rideshare_forecast.pkl # Single model for all pricing types
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore file
└── README.md             # Project documentation
```

## Key Features

### 1. Data Ingestion Agent
- **Location:** `app/agents/data_ingestion.py`
- **Purpose:** Monitors MongoDB change streams and creates ChromaDB embeddings
- **Functionality:**
  - Monitors ALL MongoDB collections (ride_orders, events_data, traffic_data, news_articles, customers, historical_rides, competitor_prices)
  - Generates text descriptions for each document
  - Creates OpenAI embeddings (text-embedding-3-small, 1536 dimensions)
  - Stores in 5 ChromaDB collections with metadata (mongodb_id, collection, timestamp)
  - Runs as standalone process (not part of FastAPI)

**Run Data Ingestion Agent:**
```bash
python app/agents/data_ingestion.py
```

### 2. Prophet ML Forecasting
- **Location:** `app/forecasting_ml.py`
- **Purpose:** Demand forecasting using Prophet ML (ONLY forecasting method, NO moving averages)
- **Functionality:**
  - **Combined Training Data:** Uses BOTH HWCO historical data AND competitor (Lyft) data for better accuracy
  - Single model covering all pricing types (CONTRACTED, STANDARD, CUSTOM)
  - Uses multiple regressors to learn patterns:
    - `Pricing_Model`: CONTRACTED, STANDARD, CUSTOM
    - `Rideshare_Company`: HWCO, COMPETITOR (learns market-wide patterns)
    - `Customer_Loyalty_Status`: Gold, Silver, Regular
    - `Location_Category`: Urban, Suburban, Rural
    - `Vehicle_Type`: Premium, Economy
    - `Demand_Profile`: HIGH, MEDIUM, LOW
    - `Time_of_Ride`: Morning, Afternoon, Evening, Night
  - Requires minimum 300 total combined orders (HWCO + competitor)
  - Generates 30/60/90-day forecasts with 80% confidence intervals
  - Forecasts use HWCO-specific patterns while learning from market-wide data
  - Saves model to `models/rideshare_forecast.pkl`

**Why Combined Data Improves Accuracy:**
- More data points = better pattern recognition
- Market-wide patterns (weekly cycles, rush hours) are shared across companies
- Competitor data helps understand overall rideshare demand trends
- Model learns HWCO-specific patterns vs market average

**Usage:**
```python
from app.forecasting_ml import RideshareForecastModel

# Train model (all pricing types together)
model = RideshareForecastModel()
result = model.train(historical_df)  # DataFrame with completed_at, actual_price, pricing_model

# Generate forecast for specific pricing type
forecast = model.forecast("STANDARD", periods=30)  # 30, 60, or 90 days
```

### 3. 6 AI Agents Architecture

All agents use **LangChain v1.0+** with OpenAI GPT-4o-mini and direct MongoDB access for actual data:

**LangChain v1.0+ Compatibility:**
- All agents use `create_agent()` from `langchain.agents` (v1.0 API)
- Tools defined using `@tool` decorator from `langchain.tools`
- Conversation memory via `InMemorySaver` from `langgraph.checkpoint.memory`
- No deprecated v0.x patterns (LCEL, create_react_agent, etc.)
- Compatible with LangChain 1.0+, LangGraph 1.0+, and all related packages

**MongoDB Query Tools (Shared):**
All agents have access to dedicated MongoDB query tools in `app/agents/utils.py`:
- `query_historical_rides()` - Query HWCO ride data with filters (month, pricing_model, location)
- `query_competitor_prices()` - Query competitor (Lyft) pricing data
- `query_events_data()` - Query n8n Eventbrite events
- `query_traffic_data()` - Query n8n Google Maps traffic
- `query_news_data()` - Query n8n NewsAPI news
- `get_mongodb_collection_stats()` - Get data availability overview

---

#### 1. Data Ingestion Agent
**Location:** `app/agents/data_ingestion.py`

**Purpose:** Monitors MongoDB change streams and creates ChromaDB embeddings for semantic search

**Inputs:**
- MongoDB collections: ride_orders, events_data, traffic_data, news_articles, customers, historical_rides, competitor_prices

**Functionality:**
- Monitors ALL MongoDB collections via change streams
- Generates text descriptions for each document
- Creates OpenAI embeddings (text-embedding-3-small, 1536 dimensions)
- Stores in 5 ChromaDB collections with metadata (mongodb_id, collection, timestamp)
- Runs as standalone process (not part of FastAPI)

**Outputs:**
- 5 ChromaDB collections with embeddings:
  - `ride_scenarios_vectors`
  - `news_events_vectors`
  - `customer_behavior_vectors`
  - `strategy_knowledge_vectors`
  - `competitor_analysis_vectors`

**Run Command:**
```bash
python app/agents/data_ingestion.py
```

---

#### 2. Chatbot Orchestrator Agent
**Location:** `app/agents/orchestrator.py`

**Purpose:** Routes user queries to appropriate specialist agents using OpenAI function calling

**Inputs:**
- User message (string)
- Conversation context (thread_id)

**Tools:**
- `route_to_analysis_agent` - For revenue, analytics, KPIs, historical data
- `route_to_pricing_agent` - For price calculations, competitor pricing
- `route_to_forecasting_agent` - For demand forecasts, predictions
- `route_to_recommendation_agent` - For strategic recommendations, HWCO vs competitor

**Functionality:**
- Uses GPT-4o-mini for intelligent query routing
- Maintains conversation context via InMemorySaver
- Can call multiple agents sequentially for complex queries
- Synthesizes responses from multiple agents

**Outputs:**
- Routed query results from specialist agents
- Synthesized responses when multiple agents are involved
- Updated conversation context

---

#### 3. Analysis Agent
**Location:** `app/agents/analysis.py`

**Purpose:** Business intelligence, KPIs, analytics, and data analysis using actual MongoDB data

**Inputs:**
- Query parameters (month, pricing_model, location, time period)
- Context from other agents (optional)

**MongoDB Tools (Primary):**
- `calculate_revenue_kpis` - Total revenue, rides, pending orders
- `calculate_profit_metrics` - Profit margins, costs, profitability
- `calculate_rides_count` - Ride counts by pricing model
- `get_monthly_price_statistics` - Average prices by month with breakdowns
- `get_top_revenue_rides` - Top rides by revenue (filterable by month)
- `analyze_customer_segments` - Customer distribution by loyalty tier
- `analyze_location_performance` - Revenue/rides by location
- `analyze_time_patterns` - Revenue/rides by time of day
- `compare_with_competitors` - HWCO vs competitor pricing comparison
- `analyze_event_impact_on_demand` - Events affecting demand (queries MongoDB)
- `analyze_traffic_patterns` - Traffic conditions for surge pricing (queries MongoDB)
- `analyze_industry_trends` - News analysis (queries MongoDB)
- `get_n8n_data_summary` - Overview of n8n data availability

**ChromaDB RAG Tools (Secondary - for semantic search only):**
- `query_ride_scenarios` - Similar past ride scenarios
- `query_news_events` - Similar events/news
- `query_customer_behavior` - Customer patterns

**Functionality:**
- Queries MongoDB directly for actual data (PRIMARY method)
- Uses synchronous PyMongo for reliable database access from LangChain tools
- Generates natural language explanations using GPT-4o-mini
- Combines KPI data with n8n context (events, traffic, news)
- Returns structured insights with specific numbers

**Outputs:**
- JSON with KPI metrics, patterns, and insights
- Natural language explanations (GPT-4o-mini)
- Competitor comparisons with location breakdowns
- Event/traffic/news analysis with recommendations

---

#### 4. Pricing Agent
**Location:** `app/agents/pricing.py`

**Purpose:** Dynamic price calculation with explanations and historical pricing analysis

**Inputs:**
- Order data for new rides (pricing_model, distance, duration, location, time, customer tier)
- Historical pricing queries (month, location, pricing_model)

**MongoDB Tools:**
- `get_historical_pricing_data` - Actual historical ride prices with statistics
- `get_competitor_pricing_data` - Competitor pricing by location and model

**ChromaDB RAG Tools:**
- `query_similar_pricing_scenarios` - Similar past rides
- `query_pricing_strategies` - Business rules and strategies

**Calculation Tool:**
- `calculate_price_with_explanation` - Uses PricingEngine + GPT-4o-mini explanations

**Functionality:**
- Queries MongoDB for actual pricing data
- Calculates prices using PricingEngine (CONTRACTED/STANDARD/CUSTOM)
- Generates natural language explanations using GPT-4o-mini
- References similar past scenarios from ChromaDB
- Compares with competitor pricing

**Outputs:**
- `final_price` - Calculated price for new ride
- `breakdown` - Multipliers and adjustments
- `explanation` - Natural language explanation (GPT-4o-mini)
- `pricing_model` - CONTRACTED/STANDARD/CUSTOM
- `revenue_score` - Priority score
- Historical pricing statistics (when queried)
- Competitor pricing analysis (when queried)

---

#### 5. Forecasting Agent
**Location:** `app/agents/forecasting.py`

**Purpose:** Demand forecasting using Prophet ML with external context from n8n data

**Inputs:**
- Pricing model (CONTRACTED, STANDARD, CUSTOM)
- Forecast period (30, 60, or 90 days)
- Optional filters (event_type, location, topic)

**MongoDB Tools:**
- `get_historical_demand_data` - Past demand patterns from historical_rides
- `get_upcoming_events` - Events from n8n Eventbrite (queries MongoDB)
- `get_traffic_conditions` - Traffic data from n8n Google Maps (queries MongoDB)
- `get_industry_news` - News from n8n NewsAPI (queries MongoDB)

**ML & Explanation Tools:**
- `generate_prophet_forecast` - Prophet ML predictions
- `explain_forecast` - GPT-4o-mini explanations with context

**ChromaDB RAG Tools (Secondary):**
- `query_event_context` - Similar events (semantic search)

**Functionality:**
- Queries MongoDB for actual events, traffic, and news data
- Generates 30/60/90-day forecasts using Prophet ML
- Combines ML predictions with external context
- Generates natural language explanations using GPT-4o-mini
- Includes confidence intervals and trend analysis

**Outputs:**
- `forecast` - Array of predictions with dates, demand, confidence intervals
- `explanation` - Natural language explanation (GPT-4o-mini)
- `method` - "prophet_ml"
- `context` - Events detected, traffic patterns from MongoDB
- Historical demand analysis with breakdowns

---

#### 6. Recommendation Agent
**Location:** `app/agents/recommendation.py`

**Purpose:** Strategic business recommendations using actual data and RAG for context

**Inputs:**
- Performance period (month, pricing_model)
- Business objectives (revenue increase 15-25%, retention)

**MongoDB Tools (Primary):**
- `get_performance_metrics` - HWCO revenue, rides, pricing by location/tier
- `get_competitor_comparison` - HWCO vs competitor with location breakdowns
- `get_market_context` - Events, traffic, news from n8n (queries MongoDB)

**ChromaDB RAG Tools (Secondary):**
- `query_strategy_knowledge` - Business rules and strategies
- `query_recent_events` - Similar events (semantic search)

**Recommendation Tool:**
- `generate_strategic_recommendation` - GPT-4o-mini recommendations

**Functionality:**
- Queries MongoDB first for actual performance and competitor data
- Combines real data with strategic guidelines from ChromaDB
- Generates actionable recommendations using GPT-4o-mini
- Includes expected impact calculations
- Focuses on revenue goals (15-25% increase)

**Outputs:**
- `recommendation` - Strategic advice (GPT-4o-mini)
- `reasoning` - Why this recommendation
- `expected_impact` - Revenue increase %, confidence level
- `data_sources` - MongoDB IDs used
- Performance metrics with specific numbers
- Competitor comparison with location analysis
- Market context with events/traffic/news

---

**Agent Communication Flow:**
```
User Query → Orchestrator Agent
                │
                ├─→ Analysis Agent (MongoDB KPIs + n8n data)
                ├─→ Pricing Agent (MongoDB pricing + PricingEngine)
                ├─→ Forecasting Agent (Prophet ML + MongoDB n8n data)
                └─→ Recommendation Agent (MongoDB performance + ChromaDB strategy)
                        ↓
                GPT-4o-mini Synthesis → User Response
```

**Key Design Principles:**
1. **MongoDB First:** All agents query MongoDB for actual data, not just ChromaDB
2. **ChromaDB Secondary:** Used for semantic search and strategy context only
3. **GPT-4o-mini Explanations:** All agents generate natural language explanations
4. **Tool Naming:** Clear naming convention (MongoDB tools vs RAG tools)
5. **Structured Output:** JSON responses with explanations

---

### 4. Agent Pipeline (NEW)
**Location:** `app/pipeline_orchestrator.py`, `app/routers/pipeline.py`

**Purpose:** Automated agent pipeline triggered by MongoDB changes

**Architecture:**
```
MongoDB Collections → Change Tracker → Hourly Scheduler
                                             ↓
                                    Pipeline Orchestrator
                                             ↓
                              ┌──────────────┴──────────────┐
                              │ Check if ML Retrain Needed  │
                              │ (historical_rides or         │
                              │  competitor_prices changed?) │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────┴──────────────┐
                              ↓                             ↓
                    ┌─────────────────┐         ┌──────────────────┐
                    │ ML Retrain      │         │ Skip Retraining  │
                    │ (Prophet Model) │         │ (model up-to-date)│
                    └────────┬────────┘         └────────┬─────────┘
                             └──────────┬────────────────┘
                                        │
                                        ▼
                    ┌───────────────────────────────────┐
                    │     PHASE 1: PARALLEL EXECUTION   │
                    └───────────────────────────────────┘
                                        │
                         ┏━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━┓
                         ↓                              ↓
              ┌─────────────────────┐       ┌─────────────────────┐
              │ Forecasting Agent   │       │ Analysis Agent      │
              │ - Prophet ML (30d)  │       │ - Competitor Data   │
              │ - Events Context    │       │ - External Events   │
              │ - GPT-4o Explain    │       │ - Traffic Patterns  │
              └──────────┬──────────┘       │ - Pricing Rules     │
                         │                  │ - GPT-4o Insights   │
                         │                  └──────────┬──────────┘
                         └──────────┬─────────────────┘
                                    ↓
                    ┌───────────────────────────────────┐
                    │    PHASE 2: SEQUENTIAL EXECUTION  │
                    └───────────────────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Recommendation Agent│
                         │ - Strategy Context  │
                         │ - Forecast Data     │
                         │ - Analysis Insights │
                         │ - GPT-4o Recommend  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ What-If Analysis    │
                         │ - Impact Simulation │
                         │ - Revenue Projection│
                         │ - GPT-4o Summary    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Store Results →     │
                         │ MongoDB (pipeline_  │
                         │         results)    │
                         └─────────────────────┘
```

**Features:**
- **Change Tracker:** Thread-safe tracking of MongoDB collection changes
- **Automatic ML Retraining:** Prophet ML model retrained before forecasting if:
  - `historical_rides` collection has changed
  - `competitor_prices` collection has changed
  - New data exists since last training (checks timestamps)
- **Hourly Scheduler:** Runs pipeline only if changes detected (configurable in `background_tasks.py`)
- **Parallel Execution:** Forecasting + Analysis agents run concurrently for speed
- **Sequential Phases:** Recommendation → What-If run after parallel phase completes
- **Natural Language Explanations:** All agents generate GPT-4o-mini explanations
- **Chatbot Compatibility:** All chatbot queries continue to work independently
- **Result Storage:** Pipeline results stored in MongoDB `pipeline_results` collection

**API Endpoints:**
- `POST /api/v1/pipeline/trigger` - Manual pipeline trigger
  - Optional: `force=true` to run without checking for changes
- `GET /api/v1/pipeline/status` - Current pipeline status and change tracker
- `GET /api/v1/pipeline/history` - Pipeline run history from MongoDB
- `GET /api/v1/pipeline/changes` - Pending changes waiting for next run
- `POST /api/v1/pipeline/clear-changes` - Clear pending changes without running
- `GET /api/v1/pipeline/last-run` - Most recent pipeline execution results

**Pipeline-Specific Analysis Tools:**
- `analyze_competitor_data_for_pipeline()` - HWCO vs competitor comparison with GPT-4o explanation
- `analyze_external_data_for_pipeline()` - News, events, traffic synthesis with GPT-4o explanation
- `generate_pricing_rules_for_pipeline()` - Auto-generate pricing rules with GPT-4o explanation
- `calculate_whatif_impact_for_pipeline()` - KPI impact simulation mapped to 4 business objectives

**Business Objectives Integration:**
The Recommendation Agent explicitly addresses ALL 4 business objectives:
1. **Maximize Revenue:** 15-25% increase through intelligent pricing
   - Actions: Urban pricing optimization, surge pricing strategies
   - KPI: Revenue increase percentage
2. **Maximize Profit Margins:** Optimize without losing customers
   - Actions: Operational efficiency, pricing model optimization
   - KPI: Profit margin improvement percentage
3. **Stay Competitive:** Real-time competitor analysis
   - Actions: Competitive pricing adjustments, market positioning
   - KPI: Market gap closure percentage
4. **Customer Retention:** 10-15% churn reduction
   - Actions: Loyalty program enhancements, surge caps for Gold customers
   - KPI: Churn reduction percentage

**Recommendation Output Structure:**
```json
{
  "recommendations_by_objective": {
    "revenue": {
      "actions": ["Apply 1.12x multiplier to urban routes"],
      "expected_impact": "+18% revenue",
      "priority": "high"
    },
    "profit_margin": {...},
    "competitive": {...},
    "retention": {...}
  },
  "integrated_strategy": "Summary of how all recommendations work together",
  "expected_impact": {
    "revenue_increase": "18-23%",
    "profit_margin_improvement": "5-7%",
    "churn_reduction": "12%",
    "competitive_positioning": "close 5% gap",
    "confidence": "High"
  },
  "implementation_phases": [...]
}
```

**What-If Analysis Visualization Support:**
- **Endpoint:** `POST /api/v1/analytics/what-if-analysis`
- **Purpose:** Calculate projected impact across 30/60/90 day forecast periods
- **Returns:**
  - `baseline`: Current KPIs (revenue, rides, margins, churn)
  - `projections`: Day-by-day projections for 30d, 60d, 90d
  - `business_objectives_impact`: Impact breakdown for all 4 objectives
  - `visualization_data`: Chart-ready data (revenue_trend, objectives_summary, kpi_cards)
  - `confidence`: Overall confidence level

**Visualization Data Structure:**
```json
{
  "revenue_trend": {
    "labels": ["Day 1", "Day 5", "Day 10", ...],
    "baseline": [372502, 372502, ...],
    "projected_30d": [375048, 385229, ...],
    "projected_60d": [...],
    "projected_90d": [...]
  },
  "objectives_summary": {
    "labels": ["Revenue", "Profit Margin", "Competitive", "Retention"],
    "baseline": [0, 40, 0, 25],
    "projected": [20, 46, 5, 13],
    "targets": [20, 45, 5, 15],
    "target_met": [true, true, true, false]
  },
  "kpi_cards": [
    {"title": "Revenue Increase", "value": "20%", "target": "15-25%", "status": "success"},
    {"title": "Profit Margin", "value": "+6%", "target": "Optimize", "status": "success"},
    {"title": "Competitive Gap", "value": "5% closed", "target": "Parity", "status": "success"},
    {"title": "Churn Reduction", "value": "12%", "target": "10-15%", "status": "success"}
  ]
}
```

**Pipeline-Specific Analysis Tools:**
1. Check if `historical_rides` or `competitor_prices` collections changed
2. If changed → Retrain Prophet ML model with latest combined data (HWCO + competitor)
3. Generate 30/60/90-day forecasts for CONTRACTED, STANDARD, CUSTOM pricing
4. Generate GPT-4o-mini explanations for each forecast
5. Return forecasts with retraining status, explanations, and metadata

**Analysis Phase Details:**
1. Query competitor data from MongoDB (`competitor_prices` collection)
2. Query n8n data from MongoDB (events, traffic, news)
3. Analyze HWCO vs competitor pricing gaps
4. Generate pricing rules based on competitive positioning
5. Generate GPT-4o-mini insights combining all data sources

**Recommendation Phase Details:**
1. Receive forecast and analysis outputs from Phase 1
2. Query strategy knowledge from ChromaDB for business rules
3. Combine forecast + analysis + strategy context
4. Generate strategic recommendations using GPT-4o-mini
5. Focus on revenue objectives (15-25% increase)

**What-If Phase Details:**
1. Simulate impact of recommendations on KPIs
2. Calculate projected revenue, profit margin improvements
3. Assess if business objectives would be met
4. Generate GPT-4o-mini summary with risk/benefit analysis

---

### 5. ChromaDB Collections (5)
Created automatically by Data Ingestion Agent with OpenAI embeddings:
- **Configuration:** Uses OpenAI `text-embedding-3-small` (1536 dimensions) when `OPENAI_API_KEY` is available
- **Storage:** Local persistent storage at `CHROMADB_PATH` (default: `./chroma_db`)
- **Collections:**
  - `ride_scenarios_vectors` - Used by: Pricing Agent, Analysis Agent
  - `news_events_vectors` - Used by: Forecasting Agent, Recommendation Agent, Analysis Agent
  - `customer_behavior_vectors` - Used by: Analysis Agent, Recommendation Agent
  - `strategy_knowledge_vectors` - Used by: Recommendation Agent (primary), Pricing Agent
  - `competitor_analysis_vectors` - Used by: Recommendation Agent, Analysis Agent
- **Verification:** Run `python3 tests/test_chromadb_collections.py` to verify all collections exist and are accessible
- **Manual Sync:** Use `POST /api/v1/upload/sync-strategies-to-chromadb` to manually sync pricing strategies from MongoDB to ChromaDB

## Getting Started

### Prerequisites

- Python 3.11 or higher
- MongoDB (native installation or MongoDB Atlas)
- Redis (optional but recommended - automatically started by `start.sh` script)
- ChromaDB (installed via pip, uses persistent storage)
- OpenAI API Key (for embeddings and GPT-4)

**Note:** Redis is optional - the backend will start without it, but priority queue features will be unavailable. The `start.sh` script automatically starts Redis if available.

### Installation

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

**Key Dependencies:**
- `fastapi==0.104.1` - Web framework
- `motor==3.3.2` - Async MongoDB driver
- `chromadb>=0.4.22` - Vector database
- `openai>=1.0.0` - OpenAI API (embeddings + GPT-4)
- `prophet==1.1.5` - Prophet ML forecasting (ONLY forecasting method)
- `pandas==2.1.4` - Data manipulation
- `numpy>=1.24.0,<2.0.0` - Numerical operations
- `langchain>=1.0.0` - LangChain v1.0+ framework
- `langchain-core>=1.0.0` - LangChain core
- `langgraph>=1.0.0` - LangGraph for agent workflows
- `langchain-openai>=1.0.0` - LangChain OpenAI integration
- `langchain-community>=0.3.0` - LangChain community integrations
- `redis==5.0.1` - Redis client (async)
- `pydantic>=2.7.4,<3.0.0` - Data validation (required for LangChain 1.0+)
- `email-validator>=2.0.0` - Email validation for Pydantic
- `httpx>=0.27.0` - HTTP client (required by chromadb)

3. Set up environment variables:

Create a `.env` file in the **root directory** (not backend/) with your configuration:

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
# Or MongoDB Atlas:
# MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGO_DB_NAME=rideshare

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# ChromaDB Configuration
CHROMADB_PATH=./chroma_db

# OpenAI Configuration (REQUIRED for agents)
OPENAI_API_KEY=your-openai-api-key-here

# Optional: LangSmith Tracing
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_TRACING=false
LANGSMITH_PROJECT=rideshare

# API Configuration
SECRET_KEY=your-secret-key-here
```

**Important:** The backend reads from the root `.env` file (not `backend/.env`).

4. Run the application:

**Option 1: Using the start script (Recommended)**
```bash
./start.sh
```

The start script will:
- Clear Python caches
- Start Redis server automatically (if available)
- Stop any existing Data Ingestion Agent processes
- Install/update dependencies
- **Start Data Ingestion Agent in background** (logs: `backend/logs/data_ingestion.log`)
- Start the FastAPI server with auto-reload

**Option 2: Manual startup**
```bash
# Start Redis (if not already running)
../start-redis.sh

# Start Data Ingestion Agent in background
mkdir -p logs
nohup python app/agents/data_ingestion.py > logs/data_ingestion.log 2>&1 &

# Start FastAPI server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

**Note:** The backend gracefully handles Redis connection failures. If Redis is unavailable, the application will start but priority queue features will return appropriate error messages.

**Data Ingestion Agent:**
- Automatically started by `start.sh` script
- Runs in background and monitors MongoDB collections
- Creates ChromaDB embeddings for semantic search
- Logs available at: `backend/logs/data_ingestion.log`
- Check logs: `./scripts/check_data_ingestion_logs.sh -f`

## Running Tests

### Quick Validation (No Dependencies Required)
```bash
python3 tests/validate_code.py
```

### Full Test Suite (Requires Dependencies)
```bash
# Install dependencies first
pip install -r requirements.txt

# Run all tests
pytest

# Or run individual test suites:
python3 tests/test_connections.py        # MongoDB, Redis connections
python3 tests/test_data_ingestion.py     # Data Ingestion Agent (4/4 passing)
python3 tests/test_prophet_ml.py         # Prophet ML (5/5 passing)
```

### Test Coverage

**Latest Test Suites (100% pass rate):**
- ✓ Enhanced ML Endpoints (5 tests) - pricing_model breakdown, date formatting
- ✓ Agent Utilities (7 tests) - ChromaDB & MongoDB querying functions
- ✓ Enhanced AI Agents (7 tests) - All 5 agents with proper tool definitions
- ✓ Priority Queue Endpoint (3 tests) - Structure and data validation
- ✓ **Pricing Agent Enhanced (5 tests)** - OpenAI GPT-4 explanations, similar scenarios
- ✓ **Forecasting Agent Enhanced (5 tests)** - OpenAI GPT-4 explanations, n8n data analysis
- ✓ **Recommendation Agent Enhanced (6 tests)** - OpenAI GPT-4 recommendations, Forecasting Agent integration
- ✓ **WebSocket Endpoint (5 tests)** - Endpoint verification, conversation context
- ✓ **OpenAI Connection (4 tests)** - API key, embeddings, chat completions
- ✓ **ChromaDB Collections (5 tests)** - All collections exist, queryable, OpenAI embeddings
- ✓ **Analytics Revenue Endpoint (6 tests)** - Endpoint validation, response structure, date calculations
- ✓ **Analysis Agent API (10 tests)** - Sync PyMongo, KPI tools, pattern analysis, top revenue rides
- ✓ **Agent Pipeline (16 tests)** - Pipeline endpoints, chatbot compatibility, concurrent access
- ✓ **ML Combined Training (14 tests)** - HWCO + competitor data training, forecast endpoints

**Existing Test Suites:**
- ✓ Data Ingestion Agent Tests (4/4 passing)
- ✓ Prophet ML Tests (5/5 passing)
- ✓ Pricing Engine Tests (6/6 passing)
- ✓ File Upload Tests (8/8 passing)

**Run All Latest Updates Tests:**
```bash
# All 4 latest components (Pricing, Forecasting, Recommendation, WebSocket)
python3 tests/test_all_4_components.py

# OpenAI connection test
python3 tests/test_openai_connection.py

# ChromaDB collections verification
python3 tests/test_chromadb_collections.py

# Analysis Agent API tests (sync PyMongo verification)
python3 tests/test_analysis_agent_api.py
```

See `tests/README_testing.md` for detailed testing documentation.

## API Documentation

Once the server is running, you can access:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## Key Endpoints

### Orders & Priority Queue
- `POST /api/v1/orders` - Create new ride order (CONTRACTED/STANDARD/CUSTOM)
- `GET /api/v1/orders/queue/priority` - Get priority queue with all orders
  - Returns: `P0` (CONTRACTED orders, FIFO), `P1` (STANDARD orders, sorted by revenue_score DESC), `P2` (CUSTOM orders, sorted by revenue_score DESC)
  - Includes: `status` with counts for each queue
  - Each order includes: `order_id`, `pricing_model`, `revenue_score`, `order_data`, `created_at`
  - **Requires Redis:** Returns error if Redis is not available

### ML & Forecasting (Enhanced)
- `POST /api/v1/ml/train` - Train Prophet ML model on historical data
  - Returns: `success`, `mape`, `confidence`, `model_path`, `training_rows`, `pricing_model_breakdown` (optional)
  - Validates minimum 1000 total orders
- `GET /api/v1/ml/forecast/30d?pricing_model=STANDARD` - 30-day forecast
- `GET /api/v1/ml/forecast/60d?pricing_model=STANDARD` - 60-day forecast
- `GET /api/v1/ml/forecast/90d?pricing_model=STANDARD` - 90-day forecast
  - Returns: `forecast` array with `date` (ISO format), `predicted_demand`, `confidence_lower`, `confidence_upper`, `trend`
  - Includes: `model`, `pricing_model`, `periods`, `confidence` (0.80)

### File Uploads
- `POST /api/v1/upload/historical-data` - Upload CSV/JSON for Prophet ML training
  - Validates: minimum 300 orders, required columns (`Order_Date`, `Historical_Cost_of_Ride`, `Pricing_Model`, `Expected_Ride_Duration`)
  - Optional columns: `Customer_Id`, `Number_Of_Riders`, `Number_of_Drivers`, `Location_Category`, `Customer_Loyalty_Status`, `Number_of_Past_Rides`, `Average_Ratings`, `Time_of_Ride`, `Vehicle_Type`
  - Automatically calculates derived fields: `Historical_Unit_Price`, `Supply_By_Demand`, `Demand_Profile`
  - Stores in MongoDB `historical_rides` collection
  - Supports backward compatibility with old field names (`completed_at`, `actual_price`, `pricing_model`)
- `POST /api/v1/upload/competitor-data` - Upload competitor pricing data
  - Accepts: CSV or Excel files
  - Validates: required columns (`Rideshare_Company` or `competitor_name`, `Order_Date` or `timestamp`, `Historical_Cost_of_Ride` or `price`)
  - Stores in MongoDB `competitor_prices` collection
  - Supports backward compatibility with old field names

### Analytics
- `GET /api/v1/analytics/revenue?period=30d` - Analytics revenue data for dashboard
  - Returns: `total_revenue`, `total_rides`, `avg_revenue_per_ride`, `customer_distribution`, `revenue_chart_data`, `top_routes`
  - Period options: `7d`, `30d`, `60d`, `90d` (default: `30d`)
  - Queries MongoDB for revenue, rides, customer distribution, and top routes

- `POST /api/v1/analytics/what-if-analysis` - What-If Impact Analysis for recommendations (NEW)
  - **Purpose:** Calculate projected impact of recommendations on all 4 business objectives
  - **Input:** Recommendation structure with `recommendations_by_objective` (revenue, profit_margin, competitive, retention)
  - **Query Parameters:** `forecast_periods` (default: [30, 60, 90])
  - **Returns:**
    - `baseline`: Current metrics (revenue, rides, profit margin, churn rate)
    - `projections`: Day-by-day projections for 30d, 60d, 90d periods
    - `business_objectives_impact`: Impact breakdown per objective with target_met flags
    - `visualization_data`: Chart-ready data for frontend
      - `revenue_trend`: Line chart data (baseline vs projections)
      - `objectives_summary`: Bar chart data (4 objectives with targets)
      - `kpi_cards`: Card widgets data (value, target, status)
    - `confidence`: Overall confidence level (high/medium/low)
  - **Business Objectives Tracked:**
    1. Revenue: 15-25% increase target
    2. Profit Margin: Optimization target
    3. Competitive Position: Market parity target
    4. Customer Retention: 10-15% churn reduction target
  - **Example Usage:**
    ```bash
    curl -X POST 'http://localhost:8000/api/v1/analytics/what-if-analysis' \
      -H 'Content-Type: application/json' \
      -d '{
        "recommendations_by_objective": {
          "revenue": {"actions": ["Urban pricing 1.12x"], "expected_impact": "+18%", "priority": "high"},
          "profit_margin": {"actions": ["Reduce CUSTOM to 2%"], "expected_impact": "+6%", "priority": "high"},
          "competitive": {"actions": ["Match rural pricing"], "expected_impact": "Close 5% gap", "priority": "medium"},
          "retention": {"actions": ["Gold surge cap 1.25x"], "expected_impact": "-12% churn", "priority": "high"}
        },
        "expected_impact": {
          "revenue_increase": "20%",
          "profit_margin_improvement": "6%",
          "churn_reduction": "12%"
        }
      }'
    ```

### Chatbot (WebSocket & HTTP)
- `WebSocket /api/v1/chatbot/ws` - Real-time AI agent communication
  - **Implementation:** Full WebSocket endpoint with conversation context management
  - **Features:**
    - Real-time bidirectional communication
    - Conversation context using LangGraph `InMemorySaver` with `thread_id`
    - Routes queries through Chatbot Orchestrator Agent
    - Orchestrator intelligently routes to worker agents (Analysis, Pricing, Forecasting, Recommendation)
    - Returns agent responses via WebSocket
  - **Usage:** Connect via WebSocket client, send messages, receive agent responses
  - **Context:** Each conversation maintains context using unique `thread_id`
- `POST /api/v1/chatbot/chat` - HTTP endpoint for chatbot (for compatibility)
  - Accepts: `{"message": "user query", "context": {}}`
  - Returns: `{"response": "agent response", "context": {}}`

## Architecture Notes

### NO Docker
- All services run natively (MongoDB, Redis compiled from source)
- ChromaDB uses persistent storage (local directory)
- Data Ingestion Agent runs as standalone Python process
- Redis is automatically started by `start.sh` script (if `start-redis.sh` is available)

### Redis Integration
- **Automatic Startup:** The `start.sh` script automatically starts Redis before starting the backend
- **Graceful Degradation:** Backend starts successfully even if Redis is unavailable
- **Connection Handling:** Redis connection failures are handled gracefully with clear warning messages
- **Priority Queues:** P0 uses Redis LIST (FIFO), P1/P2 use Redis SORTED SETs (sorted by revenue_score DESC)
- **Manual Redis Control:** Use `../start-redis.sh` to start Redis manually, or `pkill -f 'redis-server.*:6379'` to stop it

### Prophet ML Only
- **NO moving averages** - Prophet ML is the ONLY forecasting method
- Single model covers all pricing types using regressors
- 20-40% better accuracy than moving averages
- Understands weekly patterns, daily cycles, trends

### Data Flow & RAG Pattern
1. n8n workflows write data → MongoDB (events_data, traffic_data, news_articles)
2. Data Ingestion Agent monitors MongoDB change streams
3. Agent creates embeddings → ChromaDB (5 collections) with mongodb_id metadata
4. Other agents query ChromaDB for similar scenarios (fast similarity search)
5. Agents extract mongodb_ids from ChromaDB results
6. Agents fetch full documents from MongoDB using mongodb_ids (complete data)
7. Agents format documents as context and use with OpenAI GPT-4 for analysis

**RAG Pattern (Retrieval-Augmented Generation):**
- **Retrieve:** Query ChromaDB for similar past scenarios
- **Augment:** Fetch full documents from MongoDB using mongodb_id
- **Generate:** Use context with OpenAI GPT-4 to generate insights/recommendations

### ChromaDB Embeddings
- **Model:** OpenAI text-embedding-3-small (1536 dimensions)
- **Metadata:** Every embedding includes mongodb_id (required for document retrieval)
- **Collections:** 5 collections for different use cases
- **Usage:** Other agents query for similar scenarios using similarity search

## Development Notes

### Running Data Ingestion Agent
The Data Ingestion Agent should run continuously as a background process:
```bash
# Direct execution
python app/agents/data_ingestion.py

# Or setup as systemd service (see deployment/systemd/)
```

### Training Prophet ML Models
1. Upload historical data via `POST /api/upload/historical-data`
2. Train model via `POST /api/ml/train`
3. Model saved to `models/rideshare_forecast.pkl`
4. Generate forecasts via forecast endpoints

### Testing
All test scripts are in `tests/` folder. Run tests to verify functionality:

**Latest Updates:**
- Enhanced ML Endpoints: 5/5 tests passing ✓
- Agent Utilities: 7/7 tests passing ✓
- Enhanced AI Agents: 7/7 tests passing ✓
- Priority Queue Endpoint: 3/3 tests passing ✓
- **Pricing Agent Enhanced: 5/5 tests passing ✓**
- **Forecasting Agent Enhanced: 5/5 tests passing ✓**
- **Recommendation Agent Enhanced: 6/6 tests passing ✓**
- **WebSocket Endpoint: 5/5 tests passing ✓**
- **OpenAI Connection: 4/4 tests passing ✓**
- **ChromaDB Collections: 5/5 tests passing ✓**
- **Analysis Agent API: 10/10 tests passing ✓** (NEW - sync PyMongo)

**Existing Tests:**
- Data Ingestion Agent: 4/4 tests passing ✓
- Prophet ML: 5/5 tests passing ✓
- Pricing Engine: 6/6 tests passing ✓
- File Upload: 8/8 tests passing ✓

**Analysis Agent (Sync PyMongo):**
- ✓ **Analysis Agent API: 10/10 tests passing ✓** (new)

**Agent Pipeline & ML Combined Training (NEW):**
- ✓ **Agent Pipeline: 16/16 tests passing ✓** (new)
- ✓ **ML Combined Training: 14/14 tests passing ✓** (new)

**Run Pipeline + ML Tests:**
```bash
python3 -m pytest tests/test_pipeline.py tests/test_ml_combined_training.py -v
```

**Total: 132+ tests, 100% pass rate**

## Troubleshooting

### Redis Connection Issues
- **Backend starts without Redis:** This is expected behavior. Priority queue endpoints will return errors.
- **To enable Redis:** Run `../start-redis.sh` or ensure Redis is running on `localhost:6379`
- **Check Redis status:** `ps aux | grep redis-server` or use `/tmp/redis-stable/src/redis-cli ping`
- **Redis auto-start:** The `start.sh` script automatically starts Redis if `start-redis.sh` is available in the project root
- **Connection errors:** Backend logs will show: `⚠️ Redis connection failed: ... Continuing without Redis`

### Data Ingestion Agent Not Creating Embeddings
- Check MongoDB connection (MONGO_URI in root .env)
- Verify OPENAI_API_KEY is set
- Check ChromaDB path is writable
- Review agent logs for errors

### Prophet ML Training Fails
- Ensure minimum 300 orders in historical data
- Verify data has `Order_Date` (or `completed_at`) datetime and `Historical_Cost_of_Ride` (or `actual_price`) numeric columns
- Check `Pricing_Model` (or `pricing_model`) column exists (CONTRACTED, STANDARD, or CUSTOM)
- Verify `Expected_Ride_Duration` is provided and is a positive numeric value

### ChromaDB Collections Not Found
- Data Ingestion Agent creates collections automatically with OpenAI embeddings
- Collections are created with `text-embedding-3-small` (1536 dimensions) when `OPENAI_API_KEY` is available
- Run `python3 tests/test_chromadb_collections.py` to verify all collections exist
- Run `python3 tests/fix_chromadb_collections.py` to recreate collections with correct embeddings if needed
- Check `CHROMADB_PATH` in config (default: `./chroma_db`)

### ChromaDB Embedding Dimension Mismatch
- **Issue:** Error "Collection expecting embedding with dimension of 1536, got 384"
- **Root Cause:** Collection was created with default embeddings (384 dim) instead of OpenAI (1536 dim)
- **Solution:** 
  1. Delete the `chromadb_data` directory
  2. Restart the backend server
  3. Run `POST /api/v1/upload/sync-strategies-to-chromadb` to repopulate
- **Prevention:** The `query_chromadb()` function now explicitly uses OpenAI embedding function

### OpenAI API Key Issues
- Verify `OPENAI_API_KEY` is set in root `.env` file
- Run `python3 tests/test_openai_connection.py` to test API connection
- All agents handle missing API key gracefully (will show warnings in tests)

### LangChain v1.0+ Compatibility
- All code uses LangChain v1.0+ APIs (`create_agent`, `@tool`, `InMemorySaver`)
- No deprecated patterns (LCEL, create_react_agent, etc.)
- Dependencies are compatible: `langchain>=1.0.0`, `langchain-core>=1.0.0`, `langgraph>=1.0.0`
- If you see import errors, ensure all LangChain packages are v1.0+

### Analysis Agent "Metrics Not Available" Fix
- **Issue:** Analysis Agent returned "metrics not available" when querying MongoDB
- **Root Cause:** LangChain `@tool` decorated functions run synchronously, but were using async Motor driver
- **Solution:** Refactored Analysis Agent to use **synchronous PyMongo** instead of async Motor
- **Tools Updated:** All KPI tools, pattern analysis tools, and top revenue rides query
- **Verification:** Run `python3 tests/test_analysis_agent_api.py` to verify (10/10 tests passing)

## License

[Your License Here]
