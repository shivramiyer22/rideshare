# Backend Testing Documentation

## Test Files

### test_ml_router_simple.py
Tests for ML Router endpoints (Prophet ML training and forecasting).

**Test Coverage:**
- ✅ Training endpoint validation (insufficient data check)
- ✅ Forecast endpoint parameter validation
- ✅ Forecast periods validation (30d, 60d, 90d)
- ✅ ML router imports
- ✅ Forecast model class existence

**Run Tests:**
```bash
cd backend
python3 -m pytest tests/test_ml_router_simple.py -v
```

**Test Results:**
- ✅ 5 tests passed
- ⚠️ 1 warning (Pydantic deprecation - non-critical)

## Test Status: ✅ 100% PASS RATE

All backend tests are passing successfully.

---

## Latest Updates Test Suite

### test_ml_endpoints_enhanced.py
Tests for enhanced ML endpoints with latest updates:
- ✅ Training endpoint with pricing_model breakdown
- ✅ Forecasting endpoints (30d, 60d, 90d) with proper date formatting
- ✅ Response format validation
- ✅ Invalid parameter handling

**Run Tests:**
```bash
cd backend
python3 tests/test_ml_endpoints_enhanced.py
```

**Test Results:** ✅ 5/5 tests passed

### test_agent_utils.py
Tests for agent utilities (ChromaDB & MongoDB functions):
- ✅ ChromaDB client setup
- ✅ ChromaDB querying (empty collections, metadata filters)
- ✅ MongoDB document fetching (empty lists, invalid IDs)
- ✅ Document formatting for context

**Run Tests:**
```bash
cd backend
python3 tests/test_agent_utils.py
```

**Prerequisites:**
- MongoDB connection (from .env)
- ChromaDB path configured

**Test Results:** ✅ 7/7 tests passed

### test_agents_enhanced.py
Tests for enhanced AI agents:
- ✅ All 5 agent modules can be imported
- ✅ Agent tools are properly defined
- ✅ Handles missing OPENAI_API_KEY gracefully (expected in test env)

**Run Tests:**
```bash
cd backend
python3 tests/test_agents_enhanced.py
```

**Note:** Agents require OPENAI_API_KEY for full instantiation, but tests verify module structure and tool definitions.

**Test Results:** ✅ 7/7 tests passed

### test_priority_queue_endpoint.py
Tests for priority queue endpoint:
- ✅ Queue endpoint exists and returns proper structure
- ✅ Order structure validation (P0, P1, P2)
- ✅ Queue status counts match order counts

**Run Tests:**
```bash
cd backend
python3 tests/test_priority_queue_endpoint.py
```

**Prerequisites:**
- Redis connection (for full endpoint testing)

**Test Results:** ✅ 3/3 tests passed

### test_all_latest_updates.py
Master test script that runs all latest update test suites:
- ✅ Enhanced ML Endpoints
- ✅ Agent Utilities
- ✅ Enhanced AI Agents
- ✅ Priority Queue Endpoint

**Run All Tests:**
```bash
cd backend
python3 tests/test_all_latest_updates.py
```

**Test Results:** ✅ 4/4 test suites passed (22 total tests, 100% pass rate)

---

## Complete Test Summary

### Test Coverage
- ✅ ML Endpoints: Training and forecasting with enhanced features
- ✅ Agent Utilities: ChromaDB and MongoDB integration
- ✅ AI Agents: All 5 agents with proper tools
- ✅ Priority Queue: Endpoint and data structure
- ✅ File Uploads: Historical and competitor data
- ✅ Pricing Engine: All pricing models and multipliers
- ✅ Prophet ML: Single model training and forecasting
- ✅ Data Ingestion: ChromaDB embedding creation

### Total Test Results
- **Total Test Suites:** 10+
- **Total Tests:** 85+
- **Pass Rate:** ✅ 100%

All tests handle missing dependencies gracefully (Redis, OpenAI API key) which is expected in test environments.

---

## Comprehensive Endpoint Tests

### test_all_endpoints.py
Comprehensive test suite for all API endpoints (35 tests total).

**Test Coverage:**

#### Analytics Endpoints (5 tests)
- ✅ `GET /analytics/dashboard` - Returns full dashboard with KPIs
- ✅ `GET /analytics/dashboard` with date parameters
- ✅ `GET /analytics/metrics` - Returns key business metrics
- ✅ `GET /analytics/revenue` - Returns revenue analytics
- ✅ `GET /analytics/revenue` with different periods (7d, 30d, 60d, 90d)

#### Users CRUD Endpoints (8 tests)
- ✅ `POST /users/` - Creates new user with USR-XXXXXXXX ID
- ✅ `GET /users/` - Lists all users
- ✅ `GET /users/` with loyalty_tier filter
- ✅ `GET /users/{user_id}` - Gets user by ID
- ✅ `GET /users/{user_id}` - Returns 404 for non-existent user
- ✅ `PUT /users/{user_id}` - Updates user
- ✅ `DELETE /users/{user_id}` - Soft deletes user
- ✅ `POST /users/` - Rejects duplicate email

#### Orders CRUD Endpoints (7 tests)
- ✅ `POST /orders/` - Creates order with ORD-XXXXXXXX ID
- ✅ `POST /orders/` with CONTRACTED pricing (auto P0 priority)
- ✅ `POST /orders/` with CUSTOM pricing (auto P2 priority)
- ✅ `GET /orders/` - Lists all orders
- ✅ `GET /orders/{order_id}` - Gets order by ID
- ✅ `GET /orders/{order_id}` - Returns 404 for non-existent order
- ✅ `GET /orders/queue/priority` - Returns priority queue status

#### Chatbot Endpoints (5 tests)
- ✅ `POST /chatbot/chat` - Sends and receives messages
- ✅ `POST /chatbot/chat` with thread_id for conversation continuity
- ✅ `GET /chatbot/history` - Returns chat history for user
- ✅ `GET /chatbot/history` with thread_id filter
- ✅ `GET /chatbot/history` - Requires user_id parameter

#### ML Training & Forecasting Endpoints (5 tests)
- ✅ `POST /ml/train` - Trains Prophet model
- ✅ `GET /ml/forecast/30d` - 30-day forecast
- ✅ `GET /ml/forecast/60d` - 60-day forecast
- ✅ `GET /ml/forecast/90d` - 90-day forecast
- ✅ Invalid pricing_model returns 400/422

#### Upload Endpoints (2 tests)
- ✅ `POST /upload/historical-data` - Requires file
- ✅ `POST /upload/competitor-data` - Requires file

#### Health Check (3 tests)
- ✅ `GET /` - Root endpoint
- ✅ `GET /docs` - OpenAPI documentation
- ✅ `GET /openapi.json` - OpenAPI schema

**Run Tests:**
```bash
cd backend
python3 -m pytest tests/test_all_endpoints.py -v
```

**Test Results:** ✅ 35/35 tests passed (100% pass rate)

**Last Run:** December 2, 2025

---

## Analysis Agent Tests

### test_analysis_agent_api.py
Tests the refactored Analysis Agent via HTTP API endpoints (avoids numpy import issues on macOS).

**Test Coverage (10 tests):**
- ✅ Chatbot top revenue rides query (routes to Analysis Agent)
- ✅ Chatbot revenue KPIs query
- ✅ Chatbot customer segments query
- ✅ Chatbot location performance query
- ✅ Chatbot time patterns query
- ✅ Analytics dashboard endpoint
- ✅ Analytics metrics endpoint
- ✅ Analytics revenue endpoint
- ✅ Chatbot routing to Analysis Agent verification
- ✅ Sync PyMongo integration (no async errors)

**Key Verification:**
- Analysis Agent uses **synchronous PyMongo** (not async Motor)
- No "metrics not available" errors
- No asyncio/event loop errors
- Proper routing from Orchestrator to Analysis Agent

**Run Tests:**
```bash
cd backend
python3 tests/test_analysis_agent_api.py
```

**Prerequisites:**
- Backend server running on localhost:8000
- MongoDB connection configured
- OpenAI API key for chatbot agent

**Test Results:** ✅ 10/10 tests passed (100% pass rate)

**Last Run:** December 2, 2025

---

---

## Agent Pipeline Tests

### test_pipeline.py
Tests for the Agent Pipeline Enhancement feature.

**Test Coverage (16 tests):**

#### Pipeline API Endpoints (8 tests)
- ✅ `GET /pipeline/status` - Returns pipeline status with change tracker
- ✅ `GET /pipeline/changes` - Returns pending MongoDB changes
- ✅ `GET /pipeline/history` - Returns pipeline run history
- ✅ `GET /pipeline/history?limit=5` - History with custom limit
- ✅ `GET /pipeline/last-run` - Returns last pipeline run details
- ✅ `POST /pipeline/trigger` without changes - Returns no_changes message
- ✅ `POST /pipeline/trigger` with force=true - Forces pipeline run
- ✅ `POST /pipeline/clear-changes` - Clears pending changes

#### Chatbot Compatibility (3 tests)
- ✅ Chatbot API still works after pipeline changes
- ✅ Analytics API still works after pipeline changes
- ✅ ML Forecast API still works after pipeline changes

#### Pipeline Integration (3 tests)
- ✅ Pipeline status structure validation
- ✅ Pipeline history structure validation
- ✅ Pipeline endpoints don't break health check

#### Concurrent Access (2 tests)
- ✅ Analytics works during pipeline status check
- ✅ Chatbot works during pipeline operations

**Key Features Tested:**
- ChangeTracker class for MongoDB change tracking
- Pipeline API endpoints (trigger, status, history)
- Chatbot compatibility guarantee
- No blocking of other operations during pipeline

**Run Tests:**
```bash
cd backend
python3 -m pytest tests/test_pipeline.py -v
```

**Prerequisites:**
- Backend server running on localhost:8000
- MongoDB connection configured

**Test Results:** ✅ 16/16 tests passed (100% pass rate)

**Last Run:** December 2, 2025

---

## ML Combined Training Tests

### test_ml_combined_training.py
Tests for ML Prophet model training with combined HWCO + competitor data.

**Test Coverage (14 tests):**

#### ML Train Endpoint (3 tests)
- ✅ Train endpoint exists and returns valid status
- ✅ Train response includes data_sources breakdown (hwco_rows, competitor_rows)
- ✅ Success message mentions combined data sources

#### ML Forecast Endpoint (3 tests)
- ✅ 30-day forecast for STANDARD pricing
- ✅ 60-day forecast for CONTRACTED pricing
- ✅ 90-day forecast for CUSTOM pricing

#### Pipeline Retraining (2 tests)
- ✅ Pipeline status endpoint available
- ✅ Pipeline can be triggered with force option

#### Data Standardization (2 tests)
- ✅ Analytics metrics include competitor data
- ✅ Health check still works after changes

#### ML Training Metadata (1 test)
- ✅ Training stores data source information

#### Regressor Integration (1 test)
- ✅ Forecast uses HWCO-specific patterns (company_HWCO regressor)

#### Error Handling (2 tests)
- ✅ Invalid pricing model handled (400/422)
- ✅ Missing pricing model handled (422)

**Key Features Tested:**
- Combined HWCO + competitor data loading
- Data standardization (`_standardize_record_for_training`)
- `Rideshare_Company` regressor (HWCO vs COMPETITOR)
- `company_HWCO` regressor set to 1 for HWCO-specific forecasts
- Data source breakdown in training response
- Training metadata with hwco_rows and competitor_rows

**Run Tests:**
```bash
cd backend
python3 -m pytest tests/test_ml_combined_training.py -v
```

**Prerequisites:**
- Backend server running on localhost:8000
- MongoDB connection with historical_rides and competitor_prices collections

**Test Results:** ✅ 14/14 tests passed (100% pass rate)

**Last Run:** December 2, 2025

---

## Total Test Summary

### All Test Suites
| Test Suite | Tests | Pass Rate |
|------------|-------|-----------|
| ML Router Simple | 5 | ✅ 100% |
| ML Endpoints Enhanced | 5 | ✅ 100% |
| Agent Utilities | 7 | ✅ 100% |
| Agents Enhanced | 7 | ✅ 100% |
| Priority Queue Endpoint | 3 | ✅ 100% |
| All Endpoints (Comprehensive) | 35 | ✅ 100% |
| **Analysis Agent API** | **10** | ✅ **100%** |
| Pricing Agent Enhanced | 5 | ✅ 100% |
| Forecasting Agent Enhanced | 5 | ✅ 100% |
| Recommendation Agent Enhanced | 6 | ✅ 100% |
| WebSocket Endpoint | 5 | ✅ 100% |
| OpenAI Connection | 4 | ✅ 100% |
| ChromaDB Collections | 5 | ✅ 100% |
| **Agent Pipeline** | **16** | ✅ **100%** |
| **ML Combined Training** | **14** | ✅ **100%** |

**Grand Total:** 132+ tests, 100% pass rate

### Combined Pipeline + ML Test Run
```bash
# Run both test suites together (30 tests)
python3 -m pytest tests/test_pipeline.py tests/test_ml_combined_training.py -v
```
**Result:** ✅ 30/30 tests passed
