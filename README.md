# HWCO - Dynamic Pricing AI Solution v7.0

**A comprehensive rideshare platform with AI-powered dynamic pricing, Prophet ML forecasting, and intelligent business analytics.**

[![Version](https://img.shields.io/badge/version-7.0-blue.svg)](https://github.com/your-repo/rideshare)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![NO DOCKER](https://img.shields.io/badge/NO-DOCKER-red.svg)](#)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Business Objectives](#business-objectives)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## 🎯 Overview

HWCO is an intelligent rideshare platform that leverages AI and machine learning to optimize pricing, forecast demand, and provide strategic business recommendations. The system uses **Prophet ML** for forecasting, **6 AI agents** for intelligent decision-making, and **n8n workflows** for real-time external data ingestion.

### Critical Requirements

- ✅ **NO DOCKER** - All services run natively (MongoDB, Redis, n8n via npm)
- ✅ **Prophet ML ONLY** - No moving averages or statistical forecasting methods
- ✅ **6 AI Agents** - All agents use OpenAI GPT-4 and embeddings
- ✅ **Native Deployment** - Managed with systemd and PM2

---

## 🎯 Business Objectives

### Primary Goals

1. **Maximize Revenue:** Increase 15-25% through intelligent pricing
2. **Maximize Profit Margins:** Optimize without losing customers
3. **Stay Competitive:** Real-time competitor analysis
4. **Customer Retention:** Reduce churn 10-15%
5. **Data-Driven Decisions:** AI-powered insights

### Success Metrics

- ✅ Prophet ML accuracy: ±8-12% (30-day forecast)
- ✅ API response time: <200ms (95th percentile)
- ✅ Chatbot response time: <3 seconds
- ✅ System uptime: 99.9%
- ✅ Revenue increase: 15-25%
- ✅ Customer churn reduction: 10-15%

---

## ✨ Key Features

### 🤖 6 AI Agents

1. **Data Ingestion Agent** - Monitors MongoDB change streams and creates ChromaDB embeddings
2. **Chatbot Orchestrator Agent** - Routes user queries to appropriate worker agents
3. **Analysis Agent** - Business intelligence, KPIs, and analytics
4. **Pricing Agent** - Dynamic pricing with OpenAI GPT-4 explanations
5. **Forecasting Agent** - Prophet ML predictions + n8n data analysis
6. **Recommendation Agent** - Strategic advice using RAG + n8n data

### 📊 Prophet ML Forecasting

- Single model for all pricing types (CONTRACTED, STANDARD, CUSTOM)
- Multiple regressors: `pricing_model`, `Customer_Loyalty_Status`, `Location_Category`, `Vehicle_Type`, `Demand_Profile`, `Time_of_Ride`
- 30/60/90-day forecast horizons
- Confidence intervals (80%)
- **NO moving averages** - Prophet ML is the ONLY forecasting method

### 💰 Dynamic Pricing Engine

- **CONTRACTED:** Fixed price (no multipliers)
- **STANDARD:** Dynamic pricing with multipliers (time, location, vehicle, surge)
- **CUSTOM:** Dynamic pricing with different base rates
- Revenue score calculation
- Loyalty tier discounts (Gold -15%, Silver -10%, Regular 0%)

### 📈 Priority Queue System

- **P0 (Red):** CONTRACTED orders (FIFO)
- **P1 (Yellow):** STANDARD orders (sorted by revenue_score DESC)
- **P2 (Green):** CUSTOM orders (sorted by revenue_score DESC)
- Redis-based implementation with sorted sets

### 🔄 n8n Workflows

- **Eventbrite Poller:** Daily event data ingestion
- **Google Maps Traffic:** Real-time traffic pattern analysis
- **NewsAPI Poller:** Industry news and trends

### 📱 Frontend Dashboard

- Order creation form
- Real-time priority queue visualization
- Prophet ML forecast dashboard (30d/60d/90d)
- Analytics dashboard with KPIs
- AI chatbot interface (WebSocket)
- File upload for historical and competitor data

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 14+)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Orders   │ │ Queue    │ │ Forecast │ │ Analytics│      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────┐ ┌──────────┐                               │
│  │ Chatbot  │ │ Upload    │                               │
│  └──────────┘ └──────────┘                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/WebSocket
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend (FastAPI)                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Pricing      │  │ Prophet ML   │  │ Priority     │     │
│  │ Engine       │  │ Forecasting  │  │ Queue        │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              6 AI Agents                            │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐          │    │
│  │  │ Data     │ │ Analysis │ │ Pricing  │          │    │
│  │  │ Ingestion│ │          │ │          │          │    │
│  │  └──────────┘ └──────────┘ └──────────┘          │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐          │    │
│  │  │Forecasting│ │Recommend│ │Orchestr. │          │    │
│  │  └──────────┘ └──────────┘ └──────────┘          │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   MongoDB     │ │    Redis     │ │   ChromaDB   │ │     n8n     │
│  (Persistent) │ │  (Priority   │ │  (Vector DB) │ │  (Workflows)│
│               │ │   Queues)    │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

### Data Flow

1. **Order Creation:** Frontend → FastAPI → Pricing Engine → Priority Queue (Redis)
2. **Historical Data Upload:** Frontend → FastAPI → MongoDB → Data Ingestion Agent → ChromaDB
3. **n8n Data Ingestion:** n8n Workflows → MongoDB → Data Ingestion Agent → ChromaDB
4. **AI Agent Queries:** Chatbot → Orchestrator → Worker Agents → ChromaDB (RAG) → MongoDB (full docs)
5. **Forecasting:** FastAPI → Prophet ML → Forecast Dashboard

---

## 🛠️ Technology Stack

### Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI 0.104+
- **Database:** MongoDB 7.0+ (native systemd)
- **Cache:** Redis 7.0+ (native systemd)
- **ML:** Prophet 1.1.5 (ONLY forecasting method)
- **AI:** OpenAI GPT-4 + OpenAI Embeddings (text-embedding-3-small)
- **Orchestration:** LangChain 1.0+, LangGraph 1.0+
- **Vector DB:** ChromaDB (native Python, persistent storage)
- **Background Tasks:** APScheduler 3.10.4+
- **Workflow:** n8n (native npm + PM2)

### Frontend
- **Framework:** Next.js 14+ (App Router)
- **Language:** TypeScript
- **UI:** Tailwind CSS, shadcn/ui
- **Charts:** Recharts
- **WebSocket:** Native WebSocket API
- **State Management:** React Hooks

### Deployment (NO DOCKER)
- **Backend:** systemd service
- **Frontend:** PM2
- **n8n:** PM2
- **MongoDB:** Native systemd
- **Redis:** Native systemd

---

## 📁 Project Structure

```
rideshare/
├── backend/                          # FastAPI backend
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── config.py                # Configuration (reads from root .env)
│   │   ├── database.py              # MongoDB connection
│   │   ├── redis_client.py          # Redis connection
│   │   ├── forecasting_ml.py        # Prophet ML (single model)
│   │   ├── pricing_engine.py        # Dynamic pricing engine
│   │   ├── priority_queue.py        # Priority queue system
│   │   ├── background_tasks.py      # Analytics pre-computation
│   │   ├── agents/                  # 6 AI Agents
│   │   │   ├── data_ingestion.py   # MongoDB → ChromaDB embeddings
│   │   │   ├── orchestrator.py     # Chatbot Orchestrator
│   │   │   ├── analysis.py         # Analysis Agent
│   │   │   ├── pricing.py          # Pricing Agent
│   │   │   ├── forecasting.py       # Forecasting Agent
│   │   │   ├── recommendation.py    # Recommendation Agent
│   │   │   └── utils.py            # Shared utilities
│   │   ├── routers/
│   │   │   ├── orders.py           # Order endpoints
│   │   │   ├── upload.py           # File upload endpoints
│   │   │   ├── ml.py               # Prophet ML endpoints
│   │   │   ├── analytics.py        # Analytics endpoints
│   │   │   └── chatbot.py          # WebSocket chatbot
│   │   └── models/                  # Prophet ML saved models
│   ├── scripts/                     # Utility scripts
│   │   ├── verify_*.py             # Verification scripts
│   │   ├── backfill_embeddings.py  # Backfill existing data
│   │   └── retrain_models.py       # Automated retraining
│   ├── tests/                       # Test suites
│   ├── logs/                        # Application logs
│   ├── chroma_db/                   # ChromaDB persistent storage
│   ├── requirements.txt            # Python dependencies
│   ├── start.sh                    # Backend startup script
│   └── README.md                   # Backend documentation
│
├── frontend/                         # Next.js frontend
│   ├── src/
│   │   ├── app/                    # Next.js App Router
│   │   │   ├── page.tsx           # Main dashboard
│   │   │   ├── layout.tsx         # Root layout
│   │   │   ├── orders/page.tsx    # Orders page
│   │   │   ├── queue/page.tsx     # Queue page
│   │   │   ├── analytics/page.tsx  # Analytics page
│   │   │   ├── forecast/page.tsx   # Forecast page
│   │   │   ├── chatbot/page.tsx    # Chatbot page
│   │   │   └── upload/page.tsx     # Upload page
│   │   ├── components/             # React components
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── HWCOLogo.tsx
│   │   │   ├── OrderCreationForm.tsx
│   │   │   ├── PriorityQueueViz.tsx
│   │   │   ├── ForecastDashboard.tsx
│   │   │   ├── AnalyticsDashboard.tsx
│   │   │   ├── ChatbotInterface.tsx
│   │   │   └── FileUpload.tsx
│   │   └── lib/
│   │       └── api.ts             # API client
│   ├── tests/                      # Frontend tests
│   ├── package.json
│   ├── start.sh                   # Frontend startup script
│   └── README.md                  # Frontend documentation
│
├── n8n-workflows/                   # n8n workflow JSONs
│   ├── eventbrite-poller.json
│   ├── google-maps-traffic.json
│   └── newsapi-poller.json
│
├── deployment/                      # Deployment configs (NO DOCKER)
│   ├── systemd/
│   │   ├── rideshare-backend.service
│   │   ├── mongod.service
│   │   └── redis-server.service
│   └── pm2/
│       └── ecosystem.config.js
│
├── supplemental/                    # Documentation and guides
│   └── CURSOR_IDE_INSTRUCTIONS.md
│
├── .env                             # Environment variables (root)
├── start-redis.sh                   # Redis startup script
├── restart-all.sh                   # Restart all services
└── README.md                        # This file
```

---

## 📋 Prerequisites

### Required Software

- **Python 3.11+** - Backend runtime
- **Node.js 18+** - Frontend runtime
- **MongoDB 7.0+** - Database (native installation)
- **Redis 7.0+** - Cache and priority queues (native installation)
- **npm/npx** - Package management
- **n8n** - Workflow automation (via npm)

### Required API Keys

- **OpenAI API Key** - For all AI agents (GPT-4 and embeddings)
- **MongoDB Connection String** - For database access
- **Optional:** Eventbrite API, Google Maps API, NewsAPI (for n8n workflows)

### System Requirements

- **OS:** Linux, macOS, or Windows (Linux recommended for production)
- **RAM:** Minimum 4GB (8GB+ recommended)
- **Disk:** Minimum 10GB free space
- **Network:** Internet connection for OpenAI API and external services

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd rideshare
```

### 2. Configure Environment Variables

Create/update `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=rideshare

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# ChromaDB Configuration
CHROMADB_PATH=./chroma_db

# Backend/Frontend Ports
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

### 3. Install Backend Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 5. Start Services

**Option 1: Use startup scripts (Recommended)**

```bash
# From project root
./restart-all.sh
```

**Option 2: Manual startup**

```bash
# Start Redis (if not running)
./start-redis.sh

# Start Backend (includes Data Ingestion Agent)
cd backend
./start.sh

# Start Frontend (in new terminal)
cd frontend
./start.sh
```

### 6. Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **n8n UI:** http://localhost:5678 (if configured)

---

## ⚙️ Configuration

### Environment Variables

All configuration is managed through the root `.env` file. Key variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for AI agents | ✅ Yes |
| `MONGO_URI` | MongoDB connection string | ✅ Yes |
| `MONGO_DB_NAME` | MongoDB database name | ✅ Yes |
| `REDIS_URL` | Redis connection URL | ⚠️ Optional |
| `CHROMADB_PATH` | ChromaDB storage path | ✅ Yes |
| `BACKEND_PORT` | FastAPI server port | Default: 8000 |
| `FRONTEND_PORT` | Next.js server port | Default: 3000 |

### MongoDB Collections

The application uses the following MongoDB collections:

- `ride_orders` - Active ride orders
- `historical_rides` - Historical data for Prophet ML training
- `competitor_prices` - Competitor pricing data
- `events_data` - Event data from n8n (Eventbrite)
- `traffic_data` - Traffic data from n8n (Google Maps)
- `news_articles` - News articles from n8n (NewsAPI)
- `customers` - Customer information
- `analytics_cache` - Pre-computed analytics KPIs

### ChromaDB Collections

The Data Ingestion Agent creates 5 ChromaDB collections:

- `ride_scenarios_vectors` - Ride order embeddings
- `news_events_vectors` - News and event embeddings
- `customer_behavior_vectors` - Customer behavior embeddings
- `strategy_knowledge_vectors` - Strategic knowledge embeddings
- `competitor_analysis_vectors` - Competitor data embeddings

---

## 🏃 Running the Application

### Backend

```bash
cd backend
./start.sh
```

This script:
- Clears Python caches
- Starts Redis server (if available)
- Stops existing Data Ingestion Agent processes
- Installs/updates dependencies
- **Starts Data Ingestion Agent in background** (logs: `backend/logs/data_ingestion.log`)
- Starts FastAPI server with auto-reload

### Frontend

```bash
cd frontend
./start.sh
```

This script:
- Clears Next.js caches
- Installs/updates dependencies
- Starts Next.js development server

### Data Ingestion Agent

The Data Ingestion Agent is **automatically started** by `backend/start.sh`. To run manually:

```bash
cd backend
python app/agents/data_ingestion.py
```

Or in background:
```bash
cd backend
nohup python app/agents/data_ingestion.py > logs/data_ingestion.log 2>&1 &
```

### Check Agent Status

```bash
# Check if running
ps aux | grep data_ingestion.py

# View logs
tail -f backend/logs/data_ingestion.log

# Or use helper script
./backend/scripts/check_data_ingestion_logs.sh -f
```

---

## 📚 API Documentation

### Core Endpoints

#### Orders
- `POST /api/v1/orders` - Create new ride order
- `GET /api/v1/orders/{order_id}` - Get order details
- `GET /api/v1/orders/queue/priority` - Get priority queue status

#### File Upload
- `POST /api/v1/upload/historical-data` - Upload historical ride data (CSV/JSON)
- `POST /api/v1/upload/competitor-data` - Upload competitor pricing data (CSV/Excel)

#### Prophet ML
- `POST /api/v1/ml/train` - Train Prophet ML model
- `GET /api/v1/ml/forecast/30d?pricing_model=STANDARD` - 30-day forecast
- `GET /api/v1/ml/forecast/60d?pricing_model=STANDARD` - 60-day forecast
- `GET /api/v1/ml/forecast/90d?pricing_model=STANDARD` - 90-day forecast

#### Analytics
- `GET /api/v1/analytics/dashboard` - Dashboard KPIs
- `GET /api/v1/analytics/metrics` - Detailed metrics
- `GET /api/v1/analytics/revenue?period=30d` - Revenue analytics

#### Chatbot
- `WebSocket /api/v1/chatbot/ws` - Real-time chatbot interface

### Interactive API Documentation

Visit http://localhost:8000/docs for Swagger UI with full API documentation.

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run specific test suite
python tests/test_e2e_integration.py
python tests/test_all_6_agents_e2e.py

# Run verification scripts
python scripts/verify_all_checks.py
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Verification Scripts

```bash
cd backend

# Run all verifications
python scripts/verify_all_checks.py

# Individual verifications
python scripts/verify_no_docker.py
python scripts/verify_prophet_ml.py
python scripts/verify_6_agents.py
python scripts/verify_n8n_workflows.py
python scripts/verify_integration.py
```

### Test Coverage

- ✅ Backend: 50+ tests, 100% pass rate
- ✅ Frontend: Component tests with Jest/React Testing Library
- ✅ Integration: End-to-end test scenarios
- ✅ Verification: Comprehensive verification scripts

See `backend/tests/README_testing.md` and `frontend/tests/README_testing.md` for detailed testing documentation.

---

## 🚀 Deployment

### Production Deployment (NO DOCKER)

#### Backend (systemd)

```bash
# Copy service file
sudo cp deployment/systemd/rideshare-backend.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable rideshare-backend
sudo systemctl start rideshare-backend

# Check status
sudo systemctl status rideshare-backend
```

#### Frontend (PM2)

```bash
# Build frontend
cd frontend
npm run build

# Start with PM2
cd ../deployment/pm2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

#### MongoDB & Redis (systemd)

```bash
# MongoDB
sudo systemctl enable mongod
sudo systemctl start mongod

# Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### Environment-Specific Configuration

For production, update paths in:
- `deployment/systemd/rideshare-backend.service` - Working directory, paths
- `deployment/pm2/ecosystem.config.js` - PROJECT_ROOT environment variable

---

## ✅ Verification

### Run All Verifications

```bash
cd backend
python scripts/verify_all_checks.py
```

### Verification Checklist

- ✅ **NO DOCKER:** No Docker files, native services only
- ✅ **Prophet ML:** No moving averages, Prophet ML only
- ✅ **6 AI Agents:** All agents implemented and working
- ✅ **n8n Workflows:** Workflows configured and data flowing
- ✅ **Integration:** All components integrate correctly

See `backend/VERIFICATION_RESULTS.md` for detailed verification results.

---

## 🔍 Troubleshooting

### Common Issues

#### Backend won't start
- Check MongoDB connection: `mongosh "your_connection_string"`
- Check Redis connection: `redis-cli ping`
- Verify `.env` file exists and has correct values
- Check logs: `backend/logs/data_ingestion.log`

#### Data Ingestion Agent not processing
- Verify agent is running: `ps aux | grep data_ingestion.py`
- Check logs: `tail -f backend/logs/data_ingestion.log`
- Verify MongoDB connection
- Verify OpenAI API key is set

#### Frontend build errors
- Clear caches: `rm -rf .next node_modules/.cache`
- Reinstall dependencies: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 18+)

#### Prophet ML training fails
- Verify minimum 300 rows in `historical_rides` collection
- Check data quality (no null values in required columns)
- Verify all required columns exist: `Order_Date`, `Historical_Cost_of_Ride`, `Pricing_Model`, `Expected_Ride_Duration`

### Getting Help

- Check logs in `backend/logs/` and `frontend/.next/`
- Review `backend/README.md` and `frontend/README.md`
- See `backend/DATA_INGESTION_LOGS.md` for Data Ingestion Agent help
- Review verification results: `backend/VERIFICATION_RESULTS.md`

---

## 📊 Key Components

### Pricing Engine

Handles three pricing models:
- **CONTRACTED:** Fixed price (no multipliers)
- **STANDARD:** Dynamic pricing with time, location, vehicle, surge multipliers
- **CUSTOM:** Dynamic pricing with different base rates

### Priority Queue

Redis-based priority queue system:
- **P0:** CONTRACTED orders (FIFO)
- **P1:** STANDARD orders (sorted by revenue_score DESC)
- **P2:** CUSTOM orders (sorted by revenue_score DESC)

### Prophet ML Forecasting

- Single model for all pricing types
- Multiple regressors for context-aware forecasting
- 30/60/90-day forecast horizons
- Confidence intervals (80%)

### 6 AI Agents

All agents use OpenAI GPT-4 and ChromaDB RAG:

1. **Data Ingestion:** MongoDB → ChromaDB embeddings
2. **Orchestrator:** Routes queries to worker agents
3. **Analysis:** Business intelligence and KPIs
4. **Pricing:** Dynamic pricing with explanations
5. **Forecasting:** Prophet ML + n8n data analysis
6. **Recommendation:** Strategic advice with RAG

---

## 🔐 Security Notes

- **API Keys:** Never commit `.env` file to version control
- **MongoDB:** Use secure connection strings in production
- **Redis:** Configure authentication for production
- **OpenAI API:** Monitor usage and set rate limits
- **CORS:** Configured for `localhost:3000` (update for production)

---

## 📝 License

[Add your license information here]

---

## 👥 Contributing

[Add contributing guidelines here]

---

## 📞 Support

For issues, questions, or contributions, please [add your contact/support information].

---

## 🎉 Acknowledgments

- **Prophet ML** by Meta/Facebook for time series forecasting
- **OpenAI** for GPT-4 and embeddings
- **LangChain & LangGraph** for AI agent orchestration
- **FastAPI** for the excellent Python web framework
- **Next.js** for the React framework

---

**Version:** 7.0  
**Last Updated:** December 1, 2025  
**Status:** ✅ Production Ready  
**NO DOCKER | Prophet ML | 6 AI Agents | n8n Analysis**

