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
  - Single model covering all pricing types (CONTRACTED, STANDARD, CUSTOM)
  - Uses pricing_model as regressor to learn pricing-specific patterns
  - Requires minimum 300 total orders (across all pricing types)
  - Generates 30/60/90-day forecasts with 80% confidence intervals
  - Saves model to `models/rideshare_forecast.pkl`

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
All agents use **LangChain v1.0+** with OpenAI GPT-4 and ChromaDB RAG:

**LangChain v1.0+ Compatibility:**
- All agents use `create_agent()` from `langchain.agents` (v1.0 API)
- Tools defined using `@tool` decorator from `langchain.tools`
- Conversation memory via `InMemorySaver` from `langgraph.checkpoint.memory`
- No deprecated v0.x patterns (LCEL, create_react_agent, etc.)
- Compatible with LangChain 1.0+, LangGraph 1.0+, and all related packages

- **Data Ingestion Agent:** MongoDB → ChromaDB embeddings
  - Monitors all MongoDB collections via change streams
  - Creates embeddings using OpenAI text-embedding-3-small
  - Stores in 5 ChromaDB collections with mongodb_id metadata

- **Chatbot Orchestrator Agent:** Routes user queries to worker agents
  - Tools: `route_to_analysis_agent`, `route_to_pricing_agent`, `route_to_forecasting_agent`, `route_to_recommendation_agent`
  - Uses OpenAI function calling for intelligent routing

- **Analysis Agent:** Business intelligence, KPIs, analytics
  - Tools: `query_ride_scenarios`, `query_news_events`, `query_customer_behavior`, `query_competitor_data`
  - Analyzes n8n ingested data (events, traffic, news)
  - Generates insights using ChromaDB RAG + MongoDB documents

- **Pricing Agent:** Dynamic price calculation with OpenAI GPT-4 explanations
  - Tools: `query_similar_pricing_scenarios`, `query_pricing_strategies`, `calculate_price_with_explanation`
  - Uses PricingEngine for calculations
  - **Enhanced:** Generates natural language explanations using OpenAI GPT-4
  - Returns: `final_price`, `breakdown`, `explanation` (GPT-4), `pricing_model`, `revenue_score`
  - Explains pricing decisions by referencing similar past scenarios from ChromaDB

- **Forecasting Agent:** Prophet ML predictions + n8n data analysis with OpenAI GPT-4
  - Tools: `query_event_context`, `generate_prophet_forecast`, `explain_forecast`
  - Combines Prophet ML forecasts with n8n event context (events, traffic patterns)
  - **Enhanced:** Generates natural language explanations using OpenAI GPT-4
  - Returns: `forecast`, `explanation` (GPT-4), `method` ("prophet_ml"), `context` (events_detected, traffic_patterns)
  - Analyzes external factors (events, traffic) that might affect demand

- **Recommendation Agent:** Strategic advice using RAG + n8n data + Forecasting Agent predictions
  - Tools: `query_strategy_knowledge` (PRIMARY RAG source), `query_recent_events`, `query_competitor_analysis`, `generate_strategic_recommendation`
  - **Enhanced:** Generates strategic recommendations using OpenAI GPT-4
  - **Enhanced:** Integrates Forecasting Agent predictions for future demand insights
  - Focuses on revenue goals (15-25% increase)
  - Returns: `recommendation` (GPT-4), `reasoning`, `expected_impact`, `data_sources` (mongodb_ids)
  - Uses strategy_knowledge_vectors as primary RAG source

### 4. ChromaDB Collections (5)
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

**Existing Tests:**
- Data Ingestion Agent: 4/4 tests passing ✓
- Prophet ML: 5/5 tests passing ✓
- Pricing Engine: 6/6 tests passing ✓
- File Upload: 8/8 tests passing ✓

**Total: 70+ tests, 100% pass rate**

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

### OpenAI API Key Issues
- Verify `OPENAI_API_KEY` is set in root `.env` file
- Run `python3 tests/test_openai_connection.py` to test API connection
- All agents handle missing API key gracefully (will show warnings in tests)

### LangChain v1.0+ Compatibility
- All code uses LangChain v1.0+ APIs (`create_agent`, `@tool`, `InMemorySaver`)
- No deprecated patterns (LCEL, create_react_agent, etc.)
- Dependencies are compatible: `langchain>=1.0.0`, `langchain-core>=1.0.0`, `langgraph>=1.0.0`
- If you see import errors, ensure all LangChain packages are v1.0+

## License

[Your License Here]
