# Verification and Integration Testing Scripts

This directory contains verification and integration testing scripts based on CURSOR_IDE_INSTRUCTIONS.md lines 776-973.

## End-to-End Integration Tests

### `test_e2e_integration.py`
Comprehensive integration tests for all user flows (lines 820-846).

**Test Scenarios:**
1. **Order Creation → Priority Queue → Processing**
   - Creates CONTRACTED and STANDARD orders
   - Verifies priority queue structure (P0, P1, P2)
   - Checks FIFO for P0, sorted queues for P1/P2

2. **Historical Data Upload → Prophet ML Training → Forecasting**
   - Checks for historical data in MongoDB
   - Tests Prophet ML model initialization
   - Verifies forecast structure and endpoints

3. **Chatbot Conversations**
   - Tests routing to Analysis Agent
   - Tests routing to Pricing Agent
   - Tests routing to Forecasting Agent
   - Tests routing to Recommendation Agent

4. **Analytics Dashboard**
   - Checks analytics cache (pre-computed KPIs)
   - Verifies forecast endpoints
   - Verifies analytics endpoints
   - Confirms Prophet ML is the only forecasting method

**Run:**
```bash
cd backend
python tests/test_e2e_integration.py
```

## Verification Scripts

### `verify_all_checks.py` (Master Script)
Runs all verification checks. This is the main script to run for comprehensive verification.

**Run:**
```bash
cd backend
python scripts/verify_all_checks.py
```

### Individual Verification Scripts

#### `verify_no_docker.py`
Verifies NO DOCKER usage (lines 853-855).
- Checks `docker ps` command
- Searches for Docker files (docker-compose.yml, Dockerfile)
- Verifies native service management (systemd, PM2)

**Run:**
```bash
python scripts/verify_no_docker.py
```

#### `verify_prophet_ml.py`
Verifies Prophet ML is the ONLY forecasting method (lines 857-861).
- Searches for "moving_average" references (should not exist)
- Checks for Prophet model files (.pkl)
- Verifies Prophet imports
- Checks forecast endpoints

**Run:**
```bash
python scripts/verify_prophet_ml.py
```

#### `verify_6_agents.py`
Verifies all 6 AI agents are implemented (lines 863-869).
- Data Ingestion Agent
- Chatbot Orchestrator Agent
- Analysis Agent
- Pricing Agent
- Forecasting Agent
- Recommendation Agent

**Run:**
```bash
python scripts/verify_6_agents.py
```

#### `verify_n8n_workflows.py`
Verifies n8n workflows setup (lines 871-877).
- Checks n8n data collections in MongoDB
- Verifies n8n workflow JSON files exist
- Confirms Data Ingestion Agent processes n8n data

**Run:**
```bash
python scripts/verify_n8n_workflows.py
```

#### `verify_integration.py`
Verifies component integration (lines 879-885).
- Order → Queue integration
- Upload → Training integration
- Chatbot → Orchestrator → Agents integration
- Analytics Dashboard integration

**Run:**
```bash
python scripts/verify_integration.py
```

## PM2 Ecosystem Configuration

### `deployment/pm2/ecosystem.config.js`
Updated PM2 configuration for frontend and n8n (lines 777-817).

**Features:**
- Uses relative paths (works in development)
- Supports PROJECT_ROOT environment variable (for production)
- Includes log file configuration
- Configures both frontend and n8n apps

**Usage:**
```bash
# Development
cd deployment/pm2
pm2 start ecosystem.config.js

# Production (with PROJECT_ROOT)
PROJECT_ROOT=/opt/rideshare pm2 start ecosystem.config.js

# Save and enable startup
pm2 save
pm2 startup
```

## Quick Start

### Run All Verifications
```bash
cd backend
python scripts/verify_all_checks.py
```

### Run Integration Tests
```bash
cd backend
python tests/test_e2e_integration.py
```

### Run Both
```bash
cd backend
python scripts/verify_all_checks.py && python tests/test_e2e_integration.py
```

## Expected Results

### Verification Scripts
- ✅ All checks should pass if project is properly configured
- ⚠️ Some checks may show warnings if services aren't running (expected in test environments)

### Integration Tests
- ✅ All 4 test scenarios should pass
- ⚠️ Some tests may be skipped if services aren't available (MongoDB, Redis, OpenAI)

## Notes

- Verification scripts check code structure and file existence
- Integration tests require active services (MongoDB, Redis, OpenAI API)
- Some checks may fail if services aren't running (this is expected)
- All scripts handle missing dependencies gracefully

