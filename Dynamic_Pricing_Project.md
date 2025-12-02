# CURSOR IDE INSTRUCTIONS - Dynamic Pricing AI Solution v7.0
## Prophet ML + 6 AI Agents + n8n (NO DOCKER)

**Version:** 7.0  
**Timeline:** 4 days with 4 developers  
**Date:** November 29, 2025

---

## ⚠️ CRITICAL REQUIREMENTS

### ABSOLUTE RULES - NEVER VIOLATE

**1. NO DOCKER ANYWHERE**
- ❌ NO `docker-compose.yml`
- ❌ NO `Dockerfile`
- ❌ NO Docker containers
- ✅ ALL native installations (MongoDB, Redis, n8n via npm, Python, Node.js)
- ✅ Managed with systemd and PM2

**2. PROPHET ML ONLY (NO MOVING AVERAGES)**
- ✅ Prophet ML (Meta/Facebook) is the ONLY forecasting method
- ✅ Trained on 1000+ historical orders (CSV/JSON upload)
- ❌ NO moving averages anywhere in code
- ❌ NO statistical forecasting methods

**3. 6 AI AGENTS ARCHITECTURE**
- ✅ Data Ingestion Agent (MongoDB → ChromaDB embeddings)
- ✅ Chatbot Orchestrator Agent (routes queries)
- ✅ Analysis Agent (business intelligence, analyzes n8n data)
- ✅ Pricing Agent (dynamic pricing)
- ✅ Forecasting Agent (Prophet ML + n8n data analysis)
- ✅ Recommendation Agent (strategic advice with RAG + n8n data)

**4. ALL AGENTS USE OPENAI**
- ✅ OPENAI_API_KEY required for all agents
- ✅ OpenAI GPT-4 for reasoning
- ✅ OpenAI Embeddings for ChromaDB

---

## 🎯 BUSINESS OBJECTIVES

### Primary Goals
1. **Maximize Revenue:** Increase 15-25% through intelligent pricing
2. **Maximize Profit Margins:** Optimize without losing customers
3. **Stay Competitive:** Real-time competitor analysis
4. **Customer Retention:** Reduce churn 10-15%
5. **Data-Driven Decisions:** AI-powered insights

### Key Features
- 30/60/90-day Prophet ML forecasts
- Real-time n8n data analysis (events, traffic, news)
- AI agents continuously analyze external data for insights
- Strategic recommendations to achieve revenue goals

---

## 📁 PROJECT STRUCTURE

```
rideshare-dynamic-pricing/
├── backend/                          # FastAPI backend
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── config.py                # Configuration (NO Docker)
│   │   ├── database.py              # MongoDB connection
│   │   ├── redis_client.py          # Redis connection
│   │   ├── agents/                  # 6 AI Agents
│   │   │   ├── data_ingestion.py   # Data Ingestion Agent
│   │   │   ├── orchestrator.py     # Chatbot Orchestrator Agent
│   │   │   ├── analysis.py         # Analysis Agent
│   │   │   ├── pricing.py          # Pricing Agent
│   │   │   ├── forecasting.py      # Forecasting Agent
│   │   │   └── recommendation.py   # Recommendation Agent
│   │   ├── forecasting_ml.py        # Prophet ML (ONLY method)
│   │   ├── pricing_engine.py        # CONTRACTED/STANDARD/CUSTOM
│   │   ├── priority_queue.py        # P0/P1/P2 queue management
│   │   ├── routers/
│   │   │   ├── orders.py
│   │   │   ├── upload.py
│   │   │   ├── ml.py
│   │   │   ├── analytics.py
│   │   │   └── chatbot.py
│   │   └── models/
│   │       └── schemas.py
│   ├── models/                       # Prophet ML saved models
│   │   ├── contracted_forecast.pkl
│   │   ├── standard_forecast.pkl
│   │   └── custom_forecast.pkl
│   ├── requirements.txt
│   └── .env
├── frontend/                         # Next.js frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── OrderCreationForm.tsx
│   │   │   ├── PriorityQueueViz.tsx
│   │   │   ├── ChatbotInterface.tsx
│   │   │   ├── ForecastDashboard.tsx
│   │   │   ├── AnalyticsDashboard.tsx
│   │   │   └── FileUpload.tsx
│   │   └── lib/
│   │       └── api.ts
│   ├── package.json
│   └── next.config.js
├── n8n-workflows/                    # n8n workflow JSONs
│   ├── eventbrite-poller.json
│   ├── google-maps-traffic.json
│   └── newsapi-poller.json
└── deployment/                       # NO DOCKER deployment
    ├── systemd/
    │   ├── rideshare-backend.service
    │   ├── mongod.service (native)
    │   └── redis-server.service (native)
    └── pm2/
        └── ecosystem.config.js
```

---

## 🛠️ TECHNOLOGY STACK (NO DOCKER)

### Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI 0.104+
- **Database:** MongoDB 7.0+ (native systemd)
- **Cache:** Redis 7.0+ (native systemd)
- **ML:** Prophet 1.1.5 (ONLY forecasting method)
- **AI:** OpenAI GPT-4 + OpenAI Embeddings
- **Orchestration:** LangChain 0.1+, LangGraph
- **Vector DB:** ChromaDB (native Python)
- **Workflow:** n8n (native npm + PM2)

### Frontend
- **Framework:** Next.js 14+ (native Node.js + PM2)
- **Language:** TypeScript
- **UI:** Tailwind CSS, shadcn/ui
- **Charts:** Recharts
- **WebSocket:** Socket.IO client

### Deployment (NO DOCKER)
- **Backend:** systemd service
- **Frontend:** PM2
- **n8n:** PM2
- **MongoDB:** Native systemd
- **Redis:** Native systemd

---

## 📅 4-DAY IMPLEMENTATION GUIDE

### DAY 1: Foundation & Setup (8 hours)

#### CURSOR Prompts for Developer 1 (Backend Lead):

```
Create a FastAPI backend project with native MongoDB and Redis connections (NO Docker).

Requirements:
- FastAPI 0.104+ with uvicorn
- MongoDB native connection (mongodb://localhost:27017)
- Redis native connection (redis://localhost:6379)
- Environment variables in .env file
- NO Docker, NO containers

Create these files:
1. app/main.py - FastAPI app
2. app/config.py - Settings with environment variables
3. app/database.py - MongoDB connection using motor
4. app/redis_client.py - Redis connection
5. requirements.txt - Include fastapi, uvicorn, motor, redis, prophet, langchain, openai, chromadb
6. .env - MONGODB_URI, REDIS_URL, OPENAI_API_KEY

Then create priority queue system with Redis:
- P0 queue for CONTRACTED orders (FIFO)
- P1 queue for STANDARD orders (sorted by revenue_score desc)
- P2 queue for CUSTOM orders (sorted by revenue_score desc)

File: app/priority_queue.py
```

#### CURSOR Prompts for Developer 2 (Backend AI/ML):

```
Setup n8n WITHOUT Docker using npm.

Steps:
1. Install n8n globally: npm install -g n8n pm2
2. Start n8n with PM2: pm2 start n8n --name "n8n-workflows"
3. Access n8n UI at http://localhost:5678

Create 3 n8n workflows (export as JSON):
1. Eventbrite Event Poller (cron: 0 6 * * *)
   - HTTP Request to Eventbrite API
   - Transform data
   - MongoDB Insert to events_data collection
   
2. Google Maps Traffic Poller (cron: */2 * * * *)
   - HTTP Request to Google Maps Directions API
   - Transform traffic data
   - MongoDB Insert to traffic_data collection
   
3. NewsAPI Rideshare News Poller (cron: */15 * * * *)
   - HTTP Request to NewsAPI (query: rideshare OR uber OR lyft)
   - Transform articles
   - MongoDB Insert to news_articles collection

Save workflow JSONs to n8n-workflows/ directory.
```

```
Create Data Ingestion Agent that monitors MongoDB change streams and creates ChromaDB embeddings.

Requirements:
- Monitor ALL MongoDB collections for changes
- When n8n writes to events_data, traffic_data, news_articles
- Generate text descriptions for embedding
- Call OpenAI Embeddings API
- Store vectors in ChromaDB with mongodb_id metadata

File: app/agents/data_ingestion.py

Include:
- MongoDB change stream monitoring
- Text description generation function
- OpenAI Embeddings API call (openai.Embedding.create)
- ChromaDB client connection
- 5 ChromaDB collections: ride_scenarios_vectors, news_events_vectors, customer_behavior_vectors, strategy_knowledge_vectors, competitor_analysis_vectors
- Background task to run continuously

This agent should run as a separate process, not part of FastAPI.
```

```
Setup Prophet ML forecasting (ONLY forecasting method, NO moving averages).

File: app/forecasting_ml.py

Create RideshareForecastModel class:
- train(historical_data: pd.DataFrame, pricing_model: str) method
  * Train Prophet model on 1000+ historical orders
  * pricing_model: CONTRACTED, STANDARD, or CUSTOM
  * Configuration:
    - yearly_seasonality=False
    - weekly_seasonality=True
    - daily_seasonality=True
    - seasonality_mode='multiplicative'
    - interval_width=0.80
  * Save model to models/{pricing_model}_forecast.pkl
  * Return training metrics (MAPE, confidence)

- forecast(pricing_model: str, periods: int) method
  * Load model from models/{pricing_model}_forecast.pkl
  * Generate forecast for periods (30, 60, or 90 days)
  * Return: DataFrame with ds, yhat, yhat_lower, yhat_upper, trend

NO moving averages anywhere. Prophet ML is the ONLY forecasting method.
```

#### CURSOR Prompts for Developer 3 (Frontend Lead):

```
Create Next.js 14 project with TypeScript and Tailwind CSS (NO Docker).

Steps:
1. npx create-next-app@latest rideshare-frontend --typescript --tailwind --app
2. Install dependencies: npm install recharts lucide-react @tanstack/react-query

Project structure:
- src/app/page.tsx - Main dashboard
- src/app/layout.tsx - Root layout
- src/components/ - All components
- src/lib/api.ts - API client

Create layout with navigation:
- Header with logo
- Sidebar with menu items: Dashboard, Orders, Queue, Analytics, Forecast, Chatbot
- Responsive design (mobile-first)

File: src/app/layout.tsx
```

---

### DAY 2: Prophet ML + Core Features (8 hours)

#### CURSOR Prompts for Developer 1 (Backend Lead):

```
Implement pricing engine for CONTRACTED, STANDARD, CUSTOM pricing models.

File: app/pricing_engine.py

Create PricingEngine class:
- calculate_price(order_data: dict) method
  * Determine pricing_model (CONTRACTED/STANDARD/CUSTOM)
  * If CONTRACTED: return fixed_price (no multipliers)
  * If STANDARD or CUSTOM:
    - base_price = calculate_base_price(distance, duration)
    - Apply multipliers:
      * time_of_day: Morning rush 1.3x, Evening rush 1.4x, Night 1.2x
      * location: Urban high demand 1.3x, Urban regular 1.15x
      * vehicle: Premium 1.6x, Economy 1.0x
      * surge: Based on supply_demand_ratio (drivers/riders)
        - <0.3: 2.0x, 0.3-0.5: 1.6x, 0.5-0.7: 1.3x, >=0.9: 1.0x
    - loyalty_discount: Gold -15%, Silver -10%, Regular 0%
    - final_price = base_price * prod(multipliers) * (1 - loyalty_discount)
  * Calculate revenue_score = final_price * (1 + loyalty_multiplier)
  * Return: final_price, breakdown, revenue_score, pricing_model

Include detailed breakdown for all multipliers.
```

```
Create file upload endpoints for historical data (Prophet ML) and competitor data.

File: app/routers/upload.py

Endpoints:
1. POST /api/upload/historical-data
   - Accept CSV or JSON file (1000+ orders)
   - Required columns: completed_at, pricing_model, actual_price
   - Validate: minimum 300 orders per pricing_model
   - Store in MongoDB historical_rides collection
   - Return: {success: true, rows_count: int}

2. POST /api/upload/competitor-data
   - Accept CSV or Excel file
   - Required columns: competitor_name, route, price, timestamp
   - Store in MongoDB competitor_prices collection
   - Return: {success: true, rows_count: int}

Use pandas to read CSV/Excel files.
Include file validation and error handling.
```

#### CURSOR Prompts for Developer 2 (Backend AI/ML):

```
Create Prophet ML training endpoint.

File: app/routers/ml.py

Endpoint: POST /api/ml/train
- Read historical_rides from MongoDB (1000+ orders)
- Filter by pricing_model (CONTRACTED, STANDARD, CUSTOM)
- Prepare Prophet training data:
  * ds column: completed_at (datetime)
  * y column: actual_price (float)
- Train 3 Prophet models (one per pricing_model)
- Save models to models/ directory
- Return training metrics for each model

Include error handling for insufficient data (<1000 orders).
Train all 3 models in parallel if possible.
```

```
Create Prophet ML forecasting endpoints.

File: app/routers/ml.py

Endpoints:
1. GET /api/forecast/30d?pricing_model=STANDARD
2. GET /api/forecast/60d?pricing_model=CONTRACTED
3. GET /api/forecast/90d?pricing_model=CUSTOM

Logic:
- Load Prophet model for pricing_model
- Generate forecast for 30, 60, or 90 days
- Return: {
    forecast: [{date, predicted_demand, confidence_lower, confidence_upper, trend}],
    model: "prophet_ml",
    accuracy: training_metrics
  }

Include confidence intervals (80%) in response.
```

```
Setup LangChain for all 6 AI agents.

Install: langchain, langchain-openai, chromadb

Create agent templates in app/agents/:
1. orchestrator.py - Chatbot Orchestrator Agent
2. analysis.py - Analysis Agent  
3. pricing.py - Pricing Agent
4. forecasting.py - Forecasting Agent
5. recommendation.py - Recommendation Agent

Each agent should:
- Use OpenAI GPT-4 (OPENAI_API_KEY from env)
- Query ChromaDB for context
- Fetch full documents from MongoDB
- Return structured responses

Start with basic templates, we'll implement full logic on Day 3.
```

#### CURSOR Prompts for Developer 3 (Frontend Lead):

```
Create OrderCreationForm component for creating new ride orders.

File: src/components/OrderCreationForm.tsx

Form fields:
- Customer info (name, loyalty_status: Gold/Silver/Regular)
- Origin and destination (text inputs)
- Pricing model dropdown: CONTRACTED, STANDARD, CUSTOM
- Vehicle type: Economy, Premium
- Number of riders, number of drivers

On submit:
- POST /api/orders/create
- Show success/error toast
- Reset form

Use shadcn/ui Form components if possible.
Include form validation.
```

```
Create PriorityQueueViz component to visualize P0/P1/P2 queues.

File: src/components/PriorityQueueViz.tsx

Features:
- Fetch GET /api/queue/priority every 5 seconds
- Display 3 columns: P0 (red), P1 (yellow), P2 (green)
- P0: CONTRACTED orders (show in order, FIFO)
- P1: STANDARD orders (show revenue_score, sorted desc)
- P2: CUSTOM orders (show revenue_score, sorted desc)
- Show order details: customer, route, price
- Real-time updates (use setInterval or WebSocket)

Use Tailwind CSS for colors and layout.
```

---

### DAY 3: AI Agents + Advanced Features (8 hours)

#### CURSOR Prompts for Developer 2 (Backend AI/ML):

```
Implement Data Ingestion Agent fully (monitors MongoDB and creates embeddings).

File: app/agents/data_ingestion.py

Complete implementation:
1. MongoDB change stream monitoring for ALL collections
2. Text description generation:
   - For ride_orders: "Urban downtown Friday evening rain premium Gold customer"
   - For events_data: "Lakers playoff game Staples Center 20000 attendees Friday 7 PM"
   - For traffic_data: "Heavy traffic downtown to airport 45 min congestion"
   - For news_articles: Article title + summary
3. OpenAI Embeddings API call:
   - Model: text-embedding-3-small
   - Dimensions: 1536
4. ChromaDB storage:
   - Collection: Based on document type
   - Metadata: {mongodb_id, collection, ...other relevant fields}
5. Run as background process (not part of FastAPI)

This agent should run continuously and process changes in real-time.
```

```
Implement Chatbot Orchestrator Agent (routes queries to worker agents).

File: app/agents/orchestrator.py

Requirements:
- Receives user query via WebSocket
- Uses OpenAI function calling to determine intent
- Routes to appropriate agent:
  * "revenue forecast" → Forecasting Agent
  * "price explanation" → Pricing Agent
  * "analytics" → Analysis Agent
  * "recommendations" → Recommendation Agent
- Coordinates multi-agent workflows when needed
- Maintains conversation context
- Returns synthesized response

Function calling schema:
- route_to_analysis_agent
- route_to_pricing_agent
- route_to_recommendation_agent
- route_to_forecasting_agent

Use OpenAI GPT-4 with function calling.
```

```
Implement Analysis Agent (analyzes n8n ingested data for insights).

File: app/agents/analysis.py

Requirements:
- Query ChromaDB for relevant context
- Analyze newly ingested data from n8n workflows:
  * events_data: Event impact on demand
  * traffic_data: Traffic patterns and surge pricing
  * news_articles: Industry trends
- Calculate KPIs: revenue, profit, rides count, customer segments
- Fetch full documents from MongoDB
- Use OpenAI GPT-4 to generate insights
- Return structured response with data and explanation

This agent should produce analytics for the dashboard.
```

```
Implement Pricing Agent (calculates prices and explains decisions).

File: app/agents/pricing.py

Requirements:
- Query ChromaDB for similar past scenarios
- Use PricingEngine to calculate price
- Explain price breakdown in natural language via OpenAI GPT-4
- Return: {
    final_price: float,
    breakdown: {multipliers},
    explanation: string,
    pricing_model: string,
    revenue_score: float
  }

Example query: "Calculate price for Gold customer, urban LA, 6 PM, premium vehicle"
```

```
Implement Forecasting Agent (Prophet ML predictions + n8n data analysis).

File: app/agents/forecasting.py

Requirements:
- Load Prophet ML model for pricing_model
- Analyze n8n ingested data (events, traffic) for additional context
- Generate forecast using Prophet
- Use OpenAI GPT-4 to explain forecast in natural language
- Return: {
    forecast: {predicted_demand, confidence_intervals},
    explanation: string,
    method: "prophet_ml",
    context: {events_detected, traffic_patterns}
  }

This agent produces forecasts for the analytics dashboard (30/60/90-day).
```

```
Implement Recommendation Agent (strategic advice with RAG + n8n data).

File: app/agents/recommendation.py

Requirements:
- Continuously analyze newly ingested n8n data (events, traffic, news)
- Query ChromaDB strategy_knowledge_vectors (RAG)
- Combine Forecasting Agent predictions with current market data
- Use OpenAI GPT-4 to generate strategic recommendations
- Focus on achieving business objectives (revenue +15-25%)
- Return: {
    recommendation: string,
    reasoning: string,
    expected_impact: {revenue_increase, confidence},
    data_sources: [mongodb_ids]
  }

Example: n8n detects Lakers game → Forecast +45% demand → Recommend surge 1.7x
This agent produces recommendations for the analytics dashboard.
```

```
Create WebSocket endpoint for chatbot.

File: app/routers/chatbot.py

Endpoint: WebSocket /ws/chatbot

Logic:
1. Accept WebSocket connection
2. Receive user query
3. Call Chatbot Orchestrator Agent
4. Orchestrator routes to appropriate worker agent
5. Return agent response via WebSocket
6. Maintain conversation context

Use FastAPI WebSocket support.
Handle connect, disconnect, and message events.
```

#### CURSOR Prompts for Developer 3 (Frontend Lead):

```
Create ForecastDashboard component showing Prophet ML forecasts.

File: src/components/ForecastDashboard.tsx

Features:
- Tabs for 30d, 60d, 90d forecasts
- Dropdown to select pricing_model (CONTRACTED/STANDARD/CUSTOM)
- Fetch GET /api/forecast/{horizon}?pricing_model=X
- LineChart with:
  * X-axis: Date
  * Y-axis: Predicted demand
  * Shaded area for confidence intervals (yhat_lower to yhat_upper)
- Trend indicator: ↑ increasing, → stable, ↓ decreasing
- Display method: "Prophet ML" (never moving averages)

Use Recharts for charts.
Show loading state while fetching.
```

```
Create AnalyticsDashboard component (powered by Analysis Agent).

File: src/components/AnalyticsDashboard.tsx

Features:
- KPI cards: Total revenue, Total rides, Avg revenue/ride, Customer distribution
- Revenue chart (last 30 days) - LineChart
- Top 10 profitable routes - Table
- Customer loyalty distribution - PieChart (Gold/Silver/Regular)
- Date range selector

Fetch GET /api/analytics/revenue?period=30d
Use Recharts for charts.
```

```
Create ChatbotInterface component.

File: src/components/ChatbotInterface.tsx

Features:
- Chat window with message history
- User input box at bottom
- Send button
- WebSocket connection to /ws/chatbot
- Display user and assistant messages
- Typing indicator when waiting for response
- Message formatting (support markdown)

Use WebSocket API or socket.io-client.
Store messages in component state.
```

---

### DAY 4: Integration, Testing & Deployment (8 hours)

#### CURSOR Prompts for Developer 1 (Backend Lead):

```
Create systemd service for FastAPI backend (NO Docker).

File: deployment/systemd/rideshare-backend.service

[Unit]
Description=Rideshare Dynamic Pricing Backend
After=network.target mongodb.service redis-server.service

[Service]
Type=simple
User=rideshare
WorkingDirectory=/opt/rideshare/backend
Environment="PATH=/opt/rideshare/backend/venv/bin"
ExecStart=/opt/rideshare/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target

Installation steps:
1. sudo cp deployment/systemd/rideshare-backend.service /etc/systemd/system/
2. sudo systemctl daemon-reload
3. sudo systemctl enable rideshare-backend
4. sudo systemctl start rideshare-backend
```

```
Create analytics pre-computation background task.

File: app/background_tasks.py

Use APScheduler to run every 5 minutes:
1. Calculate KPIs:
   - Total revenue (last 7d, 30d)
   - Total rides
   - Average revenue per ride
   - Customer distribution (Gold/Silver/Regular)
   - Top 10 routes by revenue
2. Store in analytics_cache collection
3. Set expiry: 5 minutes

This allows dashboard to load pre-computed data quickly.
```

#### CURSOR Prompts for Developer 2 (Backend AI/ML):

```
Verify n8n deployment and test all 3 workflows.

Steps:
1. Check: pm2 status (should show n8n-workflows running)
2. Access n8n UI: http://localhost:5678
3. Verify workflows are active:
   - Eventbrite Event Poller (runs daily 6 AM)
   - Google Maps Traffic Poller (runs every 2 min)
   - NewsAPI Rideshare News Poller (runs every 15 min)
4. Manually trigger each workflow
5. Verify data appears in MongoDB:
   - events_data collection
   - traffic_data collection
   - news_articles collection
6. Check Data Ingestion Agent logs (should show embeddings created)
```

```
Test all 6 AI agents end-to-end.

Test scenarios:
1. Data Ingestion Agent:
   - Insert new event in MongoDB → Verify embedding in ChromaDB
   
2. Analysis Agent:
   - Query: "What's our revenue in the last 7 days?"
   - Verify response includes correct KPIs
   
3. Pricing Agent:
   - Query: "Calculate price for Gold customer, urban, evening rush, premium"
   - Verify response includes breakdown
   
4. Forecasting Agent:
   - Query: "Predict demand for next Friday evening"
   - Verify Prophet ML forecast returned
   
5. Recommendation Agent:
   - Insert Lakers game event via n8n
   - Query: "Should we increase prices during the Lakers game?"
   - Verify strategic recommendation
   
6. Chatbot Orchestrator:
   - Test routing to each agent
   - Test multi-agent workflow

Log all responses and verify correctness.
```

```
Setup automated Prophet ML model retraining.

Create cron job (Sunday 3 AM):
0 3 * * 0 /opt/rideshare/backend/venv/bin/python /opt/rideshare/backend/scripts/retrain_models.py

File: scripts/retrain_models.py
- Fetch latest 1000+ orders from MongoDB
- Retrain all 3 Prophet models (CONTRACTED, STANDARD, CUSTOM)
- Save new model versions
- Log training metrics
- Update prophet_models collection

This ensures models stay current with recent data.
```

#### CURSOR Prompts for Developer 3 (Frontend Lead):

```
Create PM2 ecosystem config for frontend (NO Docker).

File: deployment/pm2/ecosystem.config.js

module.exports = {
  apps: [
    {
      name: 'rideshare-frontend',
      script: 'npm',
      args: 'start',
      cwd: '/opt/rideshare/frontend',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      },
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false
    },
    {
      name: 'n8n-workflows',
      script: 'n8n',
      cwd: '/opt/rideshare',
      env: {
        N8N_PORT: 5678
      },
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false
    }
  ]
};

Deployment:
1. npm run build (in frontend directory)
2. pm2 start ecosystem.config.js
3. pm2 save
4. pm2 startup
```

```
Integrate all components and test end-to-end user flows.

Test scenarios:
1. Order Creation → Priority Queue → Processing
   - Create CONTRACTED order → Verify P0 queue
   - Create STANDARD order → Verify P1 queue with revenue_score
   - Process queue → Verify FIFO for P0, sorted for P1/P2

2. Historical Data Upload → Prophet ML Training → Forecasting
   - Upload CSV with 1000+ orders
   - Train models
   - View 30/60/90-day forecasts
   - Verify confidence intervals displayed

3. Chatbot Conversations
   - Ask about revenue → Analysis Agent response
   - Ask about pricing → Pricing Agent response
   - Ask about forecasts → Forecasting Agent response
   - Ask for recommendations → Recommendation Agent response

4. Analytics Dashboard
   - View KPIs (should be pre-computed)
   - View forecast charts (Prophet ML)
   - View recommendations (from Recommendation Agent)

Log any bugs and fix them.
```

---

## 🎯 VERIFICATION CHECKLIST

### NO DOCKER Verification
- [ ] Run `docker ps` → Should fail or show nothing
- [ ] All services running natively: `systemctl status mongod`, `systemctl status redis-server`, `pm2 status`
- [ ] No docker-compose.yml or Dockerfile in project

### Prophet ML Verification
- [ ] No moving average code anywhere (search codebase for "moving_average")
- [ ] Prophet models exist: `ls models/` shows 3 .pkl files
- [ ] Forecasting endpoints return Prophet predictions
- [ ] Dashboard shows "Prophet ML" as forecasting method

### 6 AI Agents Verification
- [ ] Data Ingestion Agent running (check logs)
- [ ] Chatbot Orchestrator routes queries correctly
- [ ] Analysis Agent produces analytics dashboard KPIs
- [ ] Pricing Agent calculates prices with explanations
- [ ] Forecasting Agent uses Prophet ML + n8n data
- [ ] Recommendation Agent provides strategic advice

### n8n Workflows Verification
- [ ] 3 workflows active in n8n UI
- [ ] Data flowing to MongoDB: events_data, traffic_data, news_articles
- [ ] Data Ingestion Agent creating embeddings for n8n data
- [ ] Analysis Agent analyzing n8n data
- [ ] Forecasting Agent using n8n data for context
- [ ] Recommendation Agent analyzing n8n data for recommendations

### Integration Verification
- [ ] Orders created → Priority queue → Processing works
- [ ] File uploads → Prophet ML training → Forecasting works
- [ ] Chatbot → Orchestrator → Worker agents → Response works
- [ ] Analytics dashboard displays pre-computed KPIs
- [ ] Forecast dashboard shows 30/60/90-day Prophet ML forecasts
- [ ] Recommendations panel shows AI-generated strategic advice

---

## 🚨 COMMON PITFALLS TO AVOID

### 1. Docker Usage
**NEVER:**
- Create `docker-compose.yml`
- Create `Dockerfile`
- Use Docker containers
- Reference Docker in deployment

**ALWAYS:**
- Use native installations (apt-get, npm, pip)
- Use systemd for backend services
- Use PM2 for Node.js services

### 2. Moving Averages
**NEVER:**
- Implement moving average forecasting
- Use statistical methods for forecasting
- Reference "moving average" in code

**ALWAYS:**
- Use Prophet ML exclusively
- Train models on historical data
- Return confidence intervals

### 3. Missing AI Agents
**NEVER:**
- Forget Data Ingestion Agent
- Skip Chatbot Orchestrator
- Implement only some agents

**ALWAYS:**
- Implement all 6 agents
- Ensure agents analyze n8n ingested data
- Test agent interactions end-to-end

### 4. n8n Data Not Used
**NEVER:**
- Ignore n8n ingested data
- Let data sit unused in MongoDB

**ALWAYS:**
- Data Ingestion Agent monitors n8n collections
- Analysis Agent analyzes n8n data for insights
- Forecasting Agent uses n8n data for context
- Recommendation Agent analyzes n8n data for strategy

---

## 📊 SUCCESS METRICS

### Technical
- ✅ Prophet ML accuracy: ±8-12% (30-day)
- ✅ API response time: <200ms (95th percentile)
- ✅ Chatbot response time: <3 seconds
- ✅ Data Ingestion Agent: <1 second per document
- ✅ n8n workflows: Data every 2-15 minutes
- ✅ System uptime: 99.9%
- ✅ NO Docker anywhere

### Business
- ✅ Revenue increase: 15-25%
- ✅ Customer churn reduction: 10-15%
- ✅ Competitive pricing maintained
- ✅ AI-powered recommendations
- ✅ 30/60/90-day forecasts accurate

---

## 🎯 FINAL REMINDERS

1. **NO DOCKER** - Every service runs natively
2. **Prophet ML ONLY** - No moving averages
3. **6 AI Agents** - All must be implemented
4. **n8n Data Analysis** - Agents must analyze external data
5. **Analytics Dashboard** - Show forecasts and recommendations
6. **OPENAI_API_KEY** - Required for all agents
7. **ChromaDB RAG** - Used by Recommendation Agent
8. **4 Days** - Stay on schedule

---

**Version:** 7.0  
**Status:** ✅ Ready for Implementation  
**NO DOCKER | Prophet ML | 6 AI Agents | n8n Analysis | 4 Days**

