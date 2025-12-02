# Dynamic Pricing AI Solution

**Prophet ML \+ 5 AI Agents \+ ChromaDB RAG \+ n8n Orchestration**

Version 7.0 | NO DOCKER | 4-Day Implementation

# **⚠️ CRITICAL REQUIREMENTS**

**NO DOCKER ANYWHERE**  
❌ NO Docker containers  
❌ NO docker-compose.yml  
❌ NO Dockerfiles  
✅ ALL native processes (MongoDB, Redis, n8n via npm, Python, Node.js)  
✅ Managed with systemd and PM2

**PROPHET ML FORECASTING ONLY**  
✅ Prophet ML (Meta/Facebook) as ONLY forecasting method  
✅ Trained on 1000+ historical orders (CSV/JSON upload)  
✅ 20-40% better accuracy than moving averages  
❌ NO moving averages anywhere

**6 AI AGENTS ARCHITECTURE**  
✅ Data Ingestion Agent \- MongoDB → ChromaDB embeddings (monitors change streams)  
✅ Chatbot Orchestrator Agent \- Routes queries to worker agents  
✅ Analysis Agent \- Business intelligence and analytics  
✅ Pricing Agent \- Dynamic price optimization  
✅ Forecasting Agent \- Demand prediction with Prophet ML  
✅ Recommendation Agent \- Strategic recommendations (LLM+RAG)

**ALL AGENTS USE OPENAI**  
✅ All agents interact with OpenAI via OPENAI\_API\_KEY  
✅ LangChain/LangGraph orchestration  
✅ ChromaDB for RAG (Retrieval-Augmented Generation)

# **🎯 BUSINESS OBJECTIVES**

* Primary Goals:

1\. Maximize Revenue \- Increase total revenue by 15-25% through intelligent pricing  
2\. Maximize Profit Margins \- Optimize prices without losing customers  
3\. Stay Competitive \- Real-time competitor analysis and response  
4\. Improve Customer Retention \- Loyalty-based pricing (reduce churn 10-15%)  
5\. Data-Driven Decisions \- AI-powered insights and recommendations

## **Competitive Strategy:**

• Monitor competitor pricing via user uploads (CSV/Excel)  
• AI agents analyze external data from n8n workflows (events, traffic, news)  
• Automatic recommendations when competitors undercut our prices  
• Dynamic surge pricing during high demand detected by Forecasting Agent  
• Loyalty rewards to retain high-value customers (Gold: 15%, Silver: 10%)  
• 30/60/90-day Prophet ML forecasts for proactive pricing decisions

# **📊 PRICING MODELS & RULES**

## **Three Pricing Tiers:**

1. 1\. CONTRACTED Pricing (Priority P0):

• Definition: Pre-negotiated fixed rates for corporate accounts  
• Priority: P0 (FIFO queue \- First In First Out)  
• Characteristics: Fixed prices, no surge, guaranteed availability  
• Use Case: Corporate accounts, partnerships, bulk bookings

2. 2\. STANDARD Pricing (Priority P1):

• Definition: Regular on-demand rides with dynamic pricing  
• Priority: P1 (Sorted by revenue\_score descending)  
• Characteristics: Base price \+ multipliers, surge pricing, loyalty discounts  
• Use Case: Most individual customers

3. 3\. CUSTOM Pricing (Priority P2):

• Definition: Special negotiated rates for unique situations  
• Priority: P2 (Sorted by revenue\_score descending)  
• Characteristics: Case-by-case pricing, promotional rates  
• Use Case: One-off deals, special events, promotions

## **Revenue Score Calculation:**

**revenue\_score \= predicted\_revenue \* (1 \+ customer\_loyalty\_multiplier)**

Loyalty Multipliers:  
• Gold: 0.20 (20% boost)  
• Silver: 0.10 (10% boost)  
• Regular: 0.00 (no boost)

## **Pricing Multipliers:**

**Time-of-Day:**  
• Morning Rush (7-9 AM): 1.3x  
• Afternoon (12-2 PM): 1.15x  
• Evening Rush (5-7 PM): 1.4x  
• Night (10 PM \- 6 AM): 1.2x

**Location:**  
• Urban High Demand: 1.3x  
• Urban Regular: 1.15x  
• Suburban: 1.0x

**Vehicle Type:**  
• Premium: 1.6x  
• Economy: 1.0x

**Demand Surge (supply/demand ratio):**  
• Critical (\<0.3): 2.0x  
• Very High (0.3-0.5): 1.6x  
• High (0.5-0.7): 1.3x  
• Normal (≥0.9): 1.0x

# **🤖 AI AGENTS ARCHITECTURE (6 AGENTS)**

## **1\. Data Ingestion Agent (LangChain \+ OpenAI)**

**Purpose:** Monitor MongoDB and create ChromaDB embeddings

**Responsibilities:**  
• Monitors MongoDB change streams for new/updated documents  
• Monitors ALL collections: ride\_orders, events\_data, traffic\_data, news\_articles, competitor\_prices, etc.  
• Creates text descriptions suitable for embedding  
• Generates embeddings using OpenAI Embeddings API (OPENAI\_API\_KEY)  
• Writes vectors to ChromaDB with mongodb\_id in metadata  
• Runs continuously as background process

**Example:**  
New event from n8n → MongoDB events\_data → Change stream detected →  
Generate embedding: "Lakers game at Staples Center, 20000 attendees, Friday 7 PM" →  
Store in ChromaDB news\_events\_vectors with mongodb\_id reference

## **2\. Chatbot Orchestrator Agent (OpenAI GPT-4)**

**Purpose:** Route user queries to appropriate worker agents

**Responsibilities:**  
• Receives all user queries via WebSocket  
• Analyzes intent using OpenAI function calling  
• Routes to: Analysis, Pricing, Forecasting, or Recommendation Agent  
• Coordinates multi-agent workflows when needed  
• Synthesizes responses from multiple agents  
• Maintains conversation context

**Query Examples:**  
• "What's our revenue forecast?" → Forecasting Agent  
• "Why is this ride $52?" → Pricing Agent  
• "Should we increase prices during concerts?" → Recommendation Agent

## **3\. Analysis Agent (OpenAI GPT-4)**

**Purpose:** Business intelligence, KPIs, analytics

**Responsibilities:**  
• Calculate and explain KPIs (revenue, profit, rides count)  
• Analyze newly ingested n8n data (events, traffic, news) for insights  
• Customer segmentation analysis  
• Produce analytics dashboards with data from n8n workflows  
• Historical trend analysis

## **4\. Pricing Agent (OpenAI GPT-4)**

**Purpose:** Calculate dynamic prices and explain decisions

**Responsibilities:**  
• Calculate prices for CONTRACTED/STANDARD/CUSTOM  
• Apply multipliers (time, location, vehicle, surge, loyalty)  
• Provide price breakdowns and explanations  
• Query ChromaDB for similar past scenarios

## **5\. Forecasting Agent (OpenAI GPT-4 \+ Prophet ML)**

**Purpose:** Demand and revenue forecasting using Prophet ML

**Responsibilities:**  
• Load trained Prophet ML models  
• Generate 30/60/90-day demand forecasts  
• Provide confidence intervals (80%)  
• Analyze n8n ingested data (events, traffic) to produce proactive forecasts  
• Explain forecasts in natural language via OpenAI GPT-4  
• Used by orchestrator and recommendation agent for strategic decisions

## **6\. Recommendation Agent (OpenAI GPT-4 \+ RAG)**

**Purpose:** Strategic pricing recommendations and competitive intelligence

**Responsibilities:**  
• Analyze newly ingested data from n8n workflows (events, traffic, news)  
• Query ChromaDB strategy\_knowledge\_vectors (RAG)  
• Combine forecasts from Forecasting Agent with current market data  
• Generate strategic recommendations to achieve business objectives  
• Provide expected impact and confidence scores  
• Competitive analysis based on uploaded competitor data

**Example:**  
n8n ingests: Lakers game Friday 7 PM →  
Forecasting Agent: Predicts \+45% demand →  
Recommendation Agent: "Increase surge to 1.7x, expected \+$8400 revenue"

# **🔄 DATA FLOW & AGENT ORCHESTRATION**

**Complete System Flow:**

1\. External APIs (Eventbrite, Google Maps, NewsAPI) → n8n workflows (scheduled)  
2\. n8n transforms and writes to MongoDB (events\_data, traffic\_data, news\_articles)  
3\. Data Ingestion Agent monitors MongoDB change streams  
4\. Data Ingestion Agent generates embeddings → ChromaDB  
5\. User query → Frontend → FastAPI → Chatbot Orchestrator Agent  
6\. Orchestrator routes to worker agent (Analysis/Pricing/Forecasting/Recommendation)  
7\. Worker agent queries ChromaDB (similarity search for context)  
8\. Worker agent fetches full documents from MongoDB (mongodb\_id)  
9\. Worker agent sends context to OpenAI GPT-4 (OPENAI\_API\_KEY)  
10\. Worker agent returns response to Orchestrator → Frontend → User

**Analytics Dashboard Flow:**

1\. n8n workflows continuously ingest external data every 2-15 minutes  
2\. Analysis Agent monitors new data via Data Ingestion Agent embeddings  
3\. Forecasting Agent generates 30/60/90-day forecasts using Prophet ML  
4\. Recommendation Agent analyzes forecasts \+ external data for recommendations  
5\. All insights cached in analytics\_cache collection  
6\. Frontend dashboard fetches pre-computed analytics  
7\. Real-time updates via WebSocket when new recommendations generated

# **📈 PROPHET ML FORECASTING**

**ONLY Forecasting Method \- NO Moving Averages**

**Model:** Meta/Facebook Prophet (prophet==1.1.5)  
**Training Data:** 1000+ historical orders (CSV/JSON upload from frontend)  
**Accuracy:** ±8-12% (30-day), ±10-14% (60-day), ±12-18% (90-day)  
**Improvement:** 20-40% better than moving averages

**Configuration:**  
• yearly\_seasonality: False (insufficient data)  
• weekly\_seasonality: True (Mon-Sun patterns)  
• daily\_seasonality: True (hour-of-day patterns)  
• seasonality\_mode: 'multiplicative'  
• interval\_width: 0.80 (80% confidence intervals)  
• changepoint\_prior\_scale: 0.05

**Three Models:**  
• models/contracted\_forecast.pkl (for CONTRACTED orders)  
• models/standard\_forecast.pkl (for STANDARD orders)  
• models/custom\_forecast.pkl (for CUSTOM orders)

**Training Workflow:**  
1\. User uploads historical\_rides.csv/json (1000+ orders) via frontend  
2\. POST /api/upload/historical-data validates and stores in MongoDB  
3\. POST /api/ml/train triggers training for all 3 pricing models  
4\. Training takes 30 seconds \- 2 minutes per model  
5\. Models saved to models/ directory  
6\. Forecasting Agent can now use models for predictions

**Forecasting Workflow:**  
1\. User asks: "Predict demand for next Friday"  
2\. Chatbot Orchestrator routes to Forecasting Agent  
3\. Forecasting Agent loads Prophet model (standard\_forecast.pkl)  
4\. Prophet generates prediction with 80% confidence intervals  
5\. OpenAI GPT-4 explains forecast in natural language  
6\. Response: "We expect 145 rides (128-162 range), \+18% vs normal Friday"

# **🗄️ MONGODB COLLECTIONS (High-Level)**

## **Core Collections:**

1\. ride\_orders \- All ride transactions (CONTRACTED/STANDARD/CUSTOM, revenue\_score)  
2\. customers \- Customer profiles, loyalty tiers (Gold/Silver/Regular)  
3\. pricing\_rules \- Dynamic pricing rules and multipliers

## **N8N Populated Collections (External Data):**

4\. events\_data \- Eventbrite events (concerts, sports) \- polled daily  
5\. traffic\_data \- Google Maps real-time traffic \- polled every 2 minutes  
6\. news\_articles \- NewsAPI rideshare news \- polled every 15 minutes  
   → All monitored by Data Ingestion Agent for embeddings  
   → Analysis Agent analyzes new data for insights  
   → Forecasting Agent uses for demand predictions  
   → Recommendation Agent uses for strategic advice

## **User Upload Collections:**

7\. historical\_rides \- CSV/JSON upload (1000+ orders for Prophet ML training)  
8\. competitor\_prices \- CSV/Excel upload (competitive analysis)

## **AI & Analytics Collections:**

9\. chat\_history \- Chatbot conversations and context  
10\. prophet\_models \- Prophet ML model metadata, performance metrics  
11\. ml\_predictions \- Prophet forecasts with confidence intervals  
12\. analytics\_cache \- Pre-computed KPIs for dashboard (updated every 5 min)

# **🔍 CHROMADB VECTOR COLLECTIONS**

**Purpose:** Provide context to AI agents via similarity search (RAG)  
**Embeddings:** OpenAI text-embedding-3-small (1536 dimensions)  
**Population:** Data Ingestion Agent monitors MongoDB change streams

* 1\. ride\_scenarios\_vectors

   Embeddings of past ride scenarios for similar pattern matching  
   Example: "Urban downtown Friday evening rain premium Gold customer"  
   Used by: Pricing Agent, Analysis Agent

* 2\. news\_events\_vectors

   Embeddings of news articles and events from n8n workflows  
   Example: "Lakers playoff game Staples Center 20000 attendees"  
   Used by: Forecasting Agent, Recommendation Agent, Analysis Agent

* 3\. customer\_behavior\_vectors

   Embeddings of customer segment behaviors and patterns  
   Used by: Analysis Agent, Recommendation Agent

* 4\. strategy\_knowledge\_vectors

   Embeddings of pricing strategies and business rules (RAG source)  
   Used by: Recommendation Agent (primary), Pricing Agent

* 5\. competitor\_analysis\_vectors

   Embeddings of competitor pricing patterns from user uploads  
   Used by: Recommendation Agent, Analysis Agent

# **📅 4-DAY DEVELOPMENT TIMELINE**

**Team: 4 Developers (2 Backend, 2 Frontend)**  
**Hours: 32 hours per developer \= 128 total hours**  
**Schedule: 8 hours per day, 4 days**

## **Developer Roles:**

• Developer 1: Backend Lead (FastAPI, MongoDB, Redis, Priority Queue, APIs)  
• Developer 2: Backend AI/ML (Prophet, 6 AI Agents, n8n, ChromaDB, RAG)  
• Developer 3: Frontend Lead (Next.js, Core UI, Dashboards, Deployment)  
• Developer 4: Frontend Features (Chatbot UI, Analytics, File Upload, Testing)

## **DAY 1: Foundation & Setup**

**Developer 1 (Backend Lead):**  
• Setup FastAPI project (NO Docker)  
• MongoDB connection (native)  
• Redis connection (native)  
• Core API endpoints (orders CRUD)  
• Priority queue (P0/P1/P2)

**Developer 2 (Backend AI/ML):**  
• Setup n8n (npm install \-g n8n pm2)  
• Create 3 n8n workflows (Eventbrite, Google Maps, NewsAPI)  
• Setup Data Ingestion Agent (MongoDB change streams monitoring)  
• Setup ChromaDB (native)  
• Prophet ML setup (prophet==1.1.5)

**Developer 3 (Frontend Lead):**  
• Next.js project setup (NO Docker)  
• Layout and navigation  
• Order management UI skeleton  
• API integration layer

**Developer 4 (Frontend Features):**  
• UI component library setup  
• File upload component skeleton  
• Chart components

## **DAY 2: Prophet ML \+ Core Features**

**Developer 1 (Backend Lead):**  
• Pricing engine (CONTRACTED/STANDARD/CUSTOM logic)  
• Multipliers calculation  
• File upload endpoints  
• Analytics pre-computation

**Developer 2 (Backend AI/ML):**  
• Prophet ML training endpoint (3 models)  
• Prophet ML forecasting endpoints (30/60/90-day)  
• Data Ingestion Agent \- Embedding pipeline  
• LangChain setup for all 6 agents

**Developer 3 (Frontend Lead):**  
• Order creation form (pricing model selection)  
• Priority queue visualization (P0/P1/P2)  
• Historical data upload UI  
• Dashboard layout with KPIs

**Developer 4 (Frontend Features):**  
• Competitor data upload UI  
• Chatbot UI skeleton  
• Forecast dashboard skeleton

## **DAY 3: AI Agents \+ Advanced Features**

**Developer 1 (Backend Lead):**  
• Analytics endpoints  
• WebSocket server for chatbot  
• Testing and bug fixes

**Developer 2 (Backend AI/ML):**  
• Implement ALL 6 AI agents:  
  1\. Data Ingestion Agent (MongoDB → ChromaDB)  
  2\. Chatbot Orchestrator Agent (routing)  
  3\. Analysis Agent (n8n data analysis)  
  4\. Pricing Agent (price calculation)  
  5\. Forecasting Agent (Prophet ML integration)  
  6\. Recommendation Agent (RAG \+ strategy)  
• Test all agents with n8n ingested data  
• Test ChromaDB queries and RAG workflow

**Developer 3 (Frontend Lead):**  
• Forecast dashboard (30/60/90-day Prophet ML charts)  
• Analytics dashboard (revenue, routes, segments)  
• Chatbot integration (WebSocket)  
• Responsive design

**Developer 4 (Frontend Features):**  
• Chatbot message UI  
• Recommendations panel  
• Real-time notifications

## **DAY 4: Integration, Testing & Deployment**

**Developer 1 (Backend Lead):**  
• Native deployment (systemd service)  
• MongoDB & Redis verification  
• End-to-end API testing  
• Performance optimization  
• API documentation

**Developer 2 (Backend AI/ML):**  
• n8n deployment (PM2)  
• Verify all 3 n8n workflows active  
• Test Data Ingestion Agent with real n8n data  
• Test all 6 AI agents end-to-end  
• Verify agents analyze n8n ingested data  
• Prophet ML model management and retraining  
• AI system documentation

**Developer 3 (Frontend Lead):**  
• Frontend deployment (PM2)  
• End-to-end UI testing  
• Bug fixes and polish  
• User documentation

**Developer 4 (Frontend Features):**  
• Integration testing  
• Performance optimization  
• Accessibility improvements  
• Final polish

# **🎯 SUCCESS METRICS**

## **Technical Metrics:**

✅ Prophet ML accuracy: ±8-12% error (30-day forecasts)  
✅ API response time: \<200ms (95th percentile)  
✅ Priority queue processing: \<100ms per order  
✅ Chatbot response time: \<3 seconds  
✅ Data Ingestion Agent: \<1 second per document  
✅ n8n workflows: 100% uptime, data every 2-15 minutes  
✅ AI agents analyze all newly ingested data  
✅ System uptime: 99.9%  
✅ NO Docker anywhere (100% native)

## **Business Metrics:**

✅ Revenue increase: 15-25%  
✅ Customer retention: Reduce churn by 10-15%  
✅ Competitive positioning: Match or beat competitor prices  
✅ Customer satisfaction: Transparent pricing explanations via chatbot  
✅ Operational efficiency: AI-powered automated recommendations  
✅ Forecasting accuracy: 30/60/90-day Prophet ML forecasts within ±12%

# **🚀 DEPLOYMENT (NO DOCKER)**

**ALL NATIVE INSTALLATIONS \- NO DOCKER**

**1\. MongoDB 7.0+ (systemd service):**  
   sudo apt-get install mongodb-org  
   sudo systemctl enable mongod  
   sudo systemctl start mongod

**2\. Redis 7.0+ (systemd service):**  
   sudo apt-get install redis-server  
   sudo systemctl enable redis-server  
   sudo systemctl start redis-server

**3\. n8n (PM2 managed):**  
   npm install \-g n8n pm2  
   pm2 start n8n \--name "n8n-workflows"  
   pm2 save  
   pm2 startup

**4\. FastAPI Backend (systemd service):**  
   Create: /etc/systemd/system/rideshare-backend.service  
   \[Service\]  
   ExecStart=/opt/rideshare/venv/bin/uvicorn app.main:app \--host 0.0.0.0 \--port 8000  
   sudo systemctl enable rideshare-backend  
   sudo systemctl start rideshare-backend

**5\. Next.js Frontend (PM2 managed):**  
   npm run build  
   pm2 start npm \--name "rideshare-frontend" \-- start  
   pm2 save

**6\. ChromaDB (native):**  
   pip install chromadb \--break-system-packages  
   Run as part of Data Ingestion Agent process

**Verification:**  
• systemctl status mongod (should be active)  
• systemctl status redis-server (should be active)  
• systemctl status rideshare-backend (should be active)  
• pm2 status (should show n8n-workflows and rideshare-frontend)  
• docker ps (should fail or show nothing \- NO DOCKER\!)  
