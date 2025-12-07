import React, { useState } from 'react';
import { Download, ChevronDown, ChevronRight, AlertCircle } from 'lucide-react';

const DynamicPricingArchitectureV7 = () => {
  const [expandedSections, setExpandedSections] = useState({
    critical: true,
    objectives: true,
    architecture: true,
    agents: true,
    dataFlow: true,
    mongodb: false,
    chromadb: false,
    timeline: false,
    deployment: false
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-xl shadow-2xl p-8">
          {/* Header */}
          <div className="flex justify-between items-start mb-6">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                Dynamic Pricing AI Solution v7.0
              </h1>
              <p className="text-lg text-purple-600 font-semibold">
                Prophet ML + 6 AI Agents + ChromaDB RAG + n8n Orchestration
              </p>
              <p className="text-sm text-red-600 font-bold mt-2">
                NO DOCKER | 4-Day Implementation | 4 Developers
              </p>
            </div>
            <button
              onClick={() => window.print()}
              className="flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <Download size={20} />
              Download
            </button>
          </div>

          <div className="space-y-6">
            {/* CRITICAL REQUIREMENTS */}
            <div className="border-2 border-red-500 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('critical')}
                className="w-full px-6 py-4 bg-red-50 hover:bg-red-100 flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <AlertCircle className="text-red-600" size={24} />
                  <h2 className="text-xl font-bold text-red-900">⚠️ CRITICAL REQUIREMENTS</h2>
                </div>
                {expandedSections.critical ? <ChevronDown size={24} /> : <ChevronRight size={24} />}
              </button>
              {expandedSections.critical && (
                <div className="px-6 py-4 bg-white space-y-4">
                  <div className="bg-red-50 border-l-4 border-red-600 p-4 rounded">
                    <h3 className="font-bold text-red-900 mb-2">NO DOCKER ANYWHERE</h3>
                    <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                      <li>❌ NO Docker containers</li>
                      <li>❌ NO docker-compose.yml</li>
                      <li>❌ NO Dockerfiles</li>
                      <li>✅ ALL native processes (MongoDB, Redis, n8n via npm, Python, Node.js)</li>
                      <li>✅ Managed with systemd and PM2</li>
                    </ul>
                  </div>

                  <div className="bg-orange-50 border-l-4 border-orange-600 p-4 rounded">
                    <h3 className="font-bold text-orange-900 mb-2">PROPHET ML FORECASTING ONLY</h3>
                    <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                      <li>✅ Prophet ML (Meta/Facebook) as ONLY forecasting method</li>
                      <li>✅ Trained on 1000+ historical orders (CSV/JSON upload)</li>
                      <li>✅ 20-40% better accuracy than moving averages</li>
                      <li>❌ NO moving averages anywhere</li>
                    </ul>
                  </div>

                  <div className="bg-purple-50 border-l-4 border-purple-600 p-4 rounded">
                    <h3 className="font-bold text-purple-900 mb-2">6 AI AGENTS ARCHITECTURE</h3>
                    <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                      <li>✅ Data Ingestion Agent - MongoDB → ChromaDB embeddings (monitors change streams)</li>
                      <li>✅ Chatbot Orchestrator Agent - Routes queries to worker agents</li>ok
                      <li>✅ Analysis Agent - Business intelligence (analyzes n8n ingested data)</li>
                      <li>✅ Pricing Agent - Dynamic price optimization</li>
                      <li>✅ Forecasting Agent - Prophet ML predictions (uses n8n data)</li>
                      <li>✅ Recommendation Agent - Strategic advice (LLM+RAG, analyzes n8n data)</li>
                    </ul>
                  </div>

                  <div className="bg-blue-50 border-l-4 border-blue-600 p-4 rounded">
                    <h3 className="font-bold text-blue-900 mb-2">ALL AGENTS USE OPENAI</h3>
                    <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                      <li>✅ All agents interact with OpenAI via OPENAI_API_KEY</li>
                      <li>✅ LangChain/LangGraph orchestration</li>
                      <li>✅ ChromaDB for RAG (Retrieval-Augmented Generation)</li>
                      <li>✅ OpenAI Embeddings API for Data Ingestion Agent</li>
                    </ul>
                  </div>
                </div>
              )}
            </div>

            {/* BUSINESS OBJECTIVES */}
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('objectives')}
                className="w-full px-6 py-4 bg-gray-50 hover:bg-gray-100 flex items-center justify-between"
              >
                <h2 className="text-xl font-bold text-gray-800">🎯 BUSINESS OBJECTIVES</h2>
                {expandedSections.objectives ? <ChevronDown size={24} /> : <ChevronRight size={24} />}
              </button>
              {expandedSections.objectives && (
                <div className="px-6 py-4 bg-white space-y-4">
                  <div className="bg-green-50 border-l-4 border-green-600 p-4 rounded">
                    <h3 className="font-bold text-green-900 mb-2">Primary Goals</h3>
                    <ol className="list-decimal list-inside space-y-1 text-gray-700 text-sm">
                      <li><strong>Maximize Revenue:</strong> Increase total revenue by 15-25% through intelligent pricing</li>
                      <li><strong>Maximize Profit Margins:</strong> Optimize prices without losing customers</li>
                      <li><strong>Stay Competitive:</strong> Real-time competitor analysis and response</li>
                      <li><strong>Improve Customer Retention:</strong> Loyalty-based pricing (reduce churn 10-15%)</li>
                      <li><strong>Data-Driven Decisions:</strong> AI-powered insights and recommendations</li>
                    </ol>
                  </div>

                  <div className="bg-blue-50 border-l-4 border-blue-600 p-4 rounded">
                    <h3 className="font-bold text-blue-900 mb-2">Competitive Strategy</h3>
                    <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                      <li>Monitor competitor pricing via user uploads (CSV/Excel)</li>
                      <li>AI agents continuously analyze n8n ingested data (events, traffic, news)</li>
                      <li>Automatic recommendations when competitors undercut prices</li>
                      <li>Dynamic surge pricing during high demand (detected by Forecasting Agent)</li>
                      <li>Loyalty rewards to retain high-value customers (Gold: 15%, Silver: 10%)</li>
                      <li>30/60/90-day Prophet ML forecasts for proactive pricing decisions</li>
                      <li>Recommendation Agent provides strategic advice to achieve revenue goals</li>
                    </ul>
                  </div>
                </div>
              )}
            </div>

            {/* SYSTEM ARCHITECTURE */}
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('architecture')}
                className="w-full px-6 py-4 bg-gray-50 hover:bg-gray-100 flex items-center justify-between"
              >
                <h2 className="text-xl font-bold text-gray-800">🏗️ COMPLETE SYSTEM ARCHITECTURE</h2>
                {expandedSections.architecture ? <ChevronDown size={24} /> : <ChevronRight size={24} />}
              </button>
              {expandedSections.architecture && (
                <div className="px-6 py-4 bg-white">
                  <div className="bg-slate-900 p-6 rounded-lg overflow-x-auto">
                    <pre className="text-green-400 text-xs font-mono whitespace-pre">
{`┌──────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL DATA SOURCES                                │
│                                                                              │
│    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                │
│    │ Eventbrite  │     │Google Maps  │     │   NewsAPI   │                │
│    │  (daily)    │     │Traffic (2min│     │  (15 min)   │                │
│    └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                │
│           │                   │                    │                        │
│           └─────────────────┬─┴────────────────────┘                        │
└───────────────────────────────┼──────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    N8N ORCHESTRATION LAYER (Native npm)                      │
│                                                                              │
│  3 Scheduled Workflows:                                                     │
│  • Event Poller (Daily 6 AM) → Eventbrite → MongoDB events_data            │
│  • Traffic Poller (Every 2 min) → Google Maps → MongoDB traffic_data       │
│  • News Poller (Every 15 min) → NewsAPI → MongoDB news_articles            │
│                                                                              │
│  All workflows: Fetch → Transform → Write to MongoDB                        │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                                ▼ (Writes via MongoDB driver)
┌──────────────────────────────────────────────────────────────────────────────┐
│                   MONGODB (Source of Truth - Native systemd)                 │
│                          ACID-Compliant Transactions                         │
│                                                                              │
│  CORE COLLECTIONS:                                                           │
│  • ride_orders (CONTRACTED/STANDARD/CUSTOM, revenue_score, P0/P1/P2)        │
│  • customers (loyalty: Gold/Silver/Regular)                                 │
│  • pricing_rules (multipliers, surge logic)                                 │
│                                                                              │
│  N8N POPULATED (External Data):                                              │
│  • events_data (Eventbrite concerts, sports)                                │
│  • traffic_data (Google Maps real-time)                                     │
│  • news_articles (NewsAPI rideshare news)                                   │
│    ↓ Monitored by Data Ingestion Agent                                      │
│    ↓ Analyzed by Analysis, Forecasting, Recommendation Agents               │
│                                                                              │
│  USER UPLOADS:                                                               │
│  • historical_rides (CSV/JSON, 1000+ orders for Prophet ML)                 │
│  • competitor_prices (CSV/Excel, competitive analysis)                      │
│                                                                              │
│  AI & ANALYTICS:                                                             │
│  • chat_history (chatbot conversations)                                     │
│  • prophet_models (model metadata, performance)                             │
│  • ml_predictions (Prophet forecasts with confidence intervals)             │
│  • analytics_cache (pre-computed KPIs, updated every 5 min)                 │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                                ▼ (Monitors via change streams)
┌──────────────────────────────────────────────────────────────────────────────┐
│                  DATA INGESTION AGENT (LangChain + OpenAI)                   │
│                                                                              │
│  Purpose: Monitor MongoDB and create ChromaDB embeddings                    │
│                                                                              │
│  • Monitors MongoDB change streams for ALL collections                      │
│  • Triggered when n8n writes new events, traffic, or news data              │
│  • Creates text descriptions suitable for embedding                         │
│  • Calls OpenAI Embeddings API (OPENAI_API_KEY)                             │
│  • Stores vectors in ChromaDB with mongodb_id references                    │
│  • Runs continuously as background process                                  │
│                                                                              │
│  Example Flow:                                                               │
│  n8n workflow → MongoDB events_data (Lakers game) →                          │
│  Change stream triggers Data Ingestion Agent →                               │
│  Generate embedding: "Lakers playoff game Staples Center 20k attendees" →   │
│  Store in ChromaDB news_events_vectors with mongodb_id                      │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                                ▼ (Writes embeddings)
┌──────────────────────────────────────────────────────────────────────────────┐
│                   CHROMADB VECTOR DATABASE (Native - Persistent)             │
│                                                                              │
│  5 Collections (all populated by Data Ingestion Agent):                     │
│                                                                              │
│  1. ride_scenarios_vectors                                                   │
│     • Past ride embeddings for pattern matching                             │
│     • Used by: Pricing Agent, Analysis Agent                                │
│                                                                              │
│  2. news_events_vectors                                                      │
│     • Embeddings of n8n ingested events and news                            │
│     • Used by: Forecasting Agent, Recommendation Agent, Analysis Agent      │
│                                                                              │
│  3. customer_behavior_vectors                                                │
│     • Customer segment behavioral patterns                                  │
│     • Used by: Analysis Agent, Recommendation Agent                         │
│                                                                              │
│  4. strategy_knowledge_vectors                                               │
│     • Pricing strategies and business rules (RAG source)                    │
│     • Used by: Recommendation Agent (primary), Pricing Agent                │
│                                                                              │
│  5. competitor_analysis_vectors                                              │
│     • Competitor pricing patterns from user uploads                         │
│     • Used by: Recommendation Agent, Analysis Agent                         │
│                                                                              │
│  Embedding: OpenAI text-embedding-3-small (1536 dimensions)                 │
│  Similarity: Cosine similarity                                               │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                                ▼ (Queried via similarity search)
┌──────────────────────────────────────────────────────────────────────────────┐
│              AI AGENT LAYER (LangGraph + OpenAI GPT-4) - 6 AGENTS            │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │            CHATBOT ORCHESTRATOR AGENT (OpenAI GPT-4)                │   │
│  │                                                                      │   │
│  │  • Receives all user queries via WebSocket                          │   │
│  │  • Analyzes intent using OpenAI function calling                    │   │
│  │  • Routes to appropriate worker agent                               │   │
│  │  • Coordinates multi-agent workflows                                │   │
│  │  • Synthesizes responses from multiple agents                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         │              │              │              │                       │
│         ▼              ▼              ▼              ▼                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │  ANALYSIS    │ │   PRICING    │ │RECOMMENDATION│ │ FORECASTING  │      │
│  │   AGENT      │ │   AGENT      │ │   AGENT      │ │    AGENT     │      │
│  │  (GPT-4)     │ │  (GPT-4)     │ │(GPT-4 + RAG) │ │(GPT-4+Prophet│      │
│  │              │ │              │ │              │ │    ML)       │      │
│  ├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤      │
│  │ Analyzes n8n │ │ Calculates   │ │ Strategic    │ │ Uses Prophet │      │
│  │ ingested data│ │ prices with  │ │ advice using │ │ ML + n8n data│      │
│  │ (events,     │ │ multipliers  │ │ RAG + n8n    │ │ for demand   │      │
│  │ traffic,news)│ │ Explains     │ │ ingested data│ │ forecasts    │      │
│  │ Produces KPIs│ │ breakdowns   │ │ Competitive  │ │ 30/60/90-day │      │
│  │ for dashboard│ │              │ │ intelligence │ │ predictions  │      │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘      │
│                                                                              │
│  All agents use OPENAI_API_KEY for GPT-4 interactions                       │
│  All agents query ChromaDB first (similarity search for context)            │
│  All agents fetch full documents from MongoDB (mongodb_id references)       │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                FASTAPI BACKEND (No Auth - Native Python + systemd)           │
│                    REST API + WebSocket + Prophet ML Engine                 │
│                                                                              │
│  Key Endpoints:                                                              │
│  • POST /api/orders/create (CONTRACTED/STANDARD/CUSTOM)                     │
│  • GET /api/queue/priority (P0/P1/P2 queues)                                │
│  • POST /api/upload/historical-data (CSV/JSON for Prophet ML)               │
│  • POST /api/ml/train (Train 3 Prophet models)                              │
│  • GET /api/forecast/30d, /60d, /90d (Prophet predictions)                  │
│  • GET /api/analytics/revenue (Pre-computed from n8n data)                  │
│  • WebSocket /ws/chatbot (Real-time AI agent communication)                 │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│              NEXT.JS FRONTEND (Open Access - Native Node.js + PM2)           │
│           Dashboard + Chatbot + File Upload + Analytics + Forecasts         │
│                                                                              │
│  • Order management (CONTRACTED/STANDARD/CUSTOM selection)                  │
│  • Priority queue visualization (P0/P1/P2 with revenue_score)               │
│  • AI Chatbot (WebSocket to 6 AI agents via Orchestrator)                   │
│  • Prophet ML forecasting dashboard (30/60/90-day charts)                   │
│  • Analytics dashboard (powered by Analysis Agent + n8n data)               │
│  • File uploads (historical data CSV/JSON, competitor data CSV/Excel)       │
│  • Recommendations panel (from Recommendation Agent)                        │
└──────────────────────────────────────────────────────────────────────────────┘`}
                    </pre>
                  </div>
                </div>
              )}
            </div>

            {/* AI AGENTS DETAILED */}
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('agents')}
                className="w-full px-6 py-4 bg-gray-50 hover:bg-gray-100 flex items-center justify-between"
              >
                <h2 className="text-xl font-bold text-gray-800">🤖 6 AI AGENTS - DETAILED SPECIFICATIONS</h2>
                {expandedSections.agents ? <ChevronDown size={24} /> : <ChevronRight size={24} />}
              </button>
              {expandedSections.agents && (
                <div className="px-6 py-4 bg-white space-y-6">
                  {/* Data Ingestion Agent */}
                  <div className="border-l-4 border-indigo-500 pl-4">
                    <h3 className="text-lg font-bold text-gray-800 mb-2">
                      1. Data Ingestion Agent (LangChain + OpenAI Embeddings)
                    </h3>
                    <div className="bg-indigo-50 p-4 rounded space-y-2">
                      <p className="text-sm font-semibold text-indigo-900">
                        Purpose: Monitor MongoDB and create ChromaDB vector embeddings
                      </p>
                      <div className="text-sm text-gray-700">
                        <p className="font-semibold mb-1">Responsibilities:</p>
                        <ul className="list-disc list-inside space-y-1 ml-2">
                          <li>Monitors MongoDB change streams for ALL collections</li>
                          <li>Triggered when n8n writes new events_data, traffic_data, news_articles</li>
                          <li>Creates natural language descriptions of documents</li>
                          <li>Calls OpenAI Embeddings API (text-embedding-3-small)</li>
                          <li>Stores vectors in ChromaDB with mongodb_id metadata</li>
                          <li>Runs continuously as background process</li>
                        </ul>
                      </div>
                      <div className="bg-white p-3 rounded border border-indigo-200">
                        <p className="text-xs font-mono text-gray-700">
                          <strong>Example Flow:</strong><br/>
                          n8n ingests Lakers game → MongoDB events_data →<br/>
                          Change stream detected → Data Ingestion Agent →<br/>
                          Generate text: "Lakers playoff game Staples Center 20000 attendees Friday 7 PM" →<br/>
                          OpenAI Embeddings API → ChromaDB news_events_vectors
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Chatbot Orchestrator */}
                  <div className="border-l-4 border-purple-500 pl-4">
                    <h3 className="text-lg font-bold text-gray-800 mb-2">
                      2. Chatbot Orchestrator Agent (OpenAI GPT-4)
                    </h3>
                    <div className="bg-purple-50 p-4 rounded space-y-2">
                      <p className="text-sm font-semibold text-purple-900">
                        Purpose: Route user queries to appropriate worker agents
                      </p>
                      <div className="text-sm text-gray-700">
                        <p className="font-semibold mb-1">Routing Examples:</p>
                        <ul className="list-disc list-inside space-y-1 ml-2">
                          <li>"What's our revenue forecast?" → <strong>Forecasting Agent</strong></li>
                          <li>"Why is this ride $52?" → <strong>Pricing Agent</strong></li>
                          <li>"How do we compare to competitors?" → <strong>Analysis Agent</strong></li>
                          <li>"Should we increase prices during concerts?" → <strong>Recommendation Agent</strong></li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* Analysis Agent */}
                  <div className="border-l-4 border-green-500 pl-4">
                    <h3 className="text-lg font-bold text-gray-800 mb-2">
                      3. Analysis Agent (OpenAI GPT-4)
                    </h3>
                    <div className="bg-green-50 p-4 rounded space-y-2">
                      <p className="text-sm font-semibold text-green-900">
                        Purpose: Business intelligence, KPIs, analytics from n8n ingested data
                      </p>
                      <div className="text-sm text-gray-700">
                        <p className="font-semibold mb-1">Key Responsibilities:</p>
                        <ul className="list-disc list-inside space-y-1 ml-2">
                          <li>Analyzes newly ingested data from n8n workflows (events, traffic, news)</li>
                          <li>Produces analytics dashboard KPIs (revenue, profit, rides count)</li>
                          <li>Customer segmentation analysis (Gold/Silver/Regular)</li>
                          <li>Historical trend analysis</li>
                          <li>Queries ChromaDB for similar past scenarios</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* Pricing Agent */}
                  <div className="border-l-4 border-blue-500 pl-4">
                    <h3 className="text-lg font-bold text-gray-800 mb-2">
                      4. Pricing Agent (OpenAI GPT-4)
                    </h3>
                    <div className="bg-blue-50 p-4 rounded space-y-2">
                      <p className="text-sm font-semibold text-blue-900">
                        Purpose: Calculate dynamic prices and explain decisions
                      </p>
                      <div className="text-sm text-gray-700">
                        <p className="font-semibold mb-1">Pricing Logic:</p>
                        <ul className="list-disc list-inside space-y-1 ml-2">
                          <li>CONTRACTED: Fixed price (P0 priority, FIFO)</li>
                          <li>STANDARD: Base + multipliers (P1 priority, revenue_score sorted)</li>
                          <li>CUSTOM: Negotiated rates (P2 priority, revenue_score sorted)</li>
                          <li>Multipliers: Time (1.3-1.4x), Location (1.15-1.3x), Vehicle (1.6x), Surge (1.0-2.0x)</li>
                          <li>Loyalty discounts: Gold (-15%), Silver (-10%)</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* Forecasting Agent */}
                  <div className="border-l-4 border-orange-500 pl-4">
                    <h3 className="text-lg font-bold text-gray-800 mb-2">
                      5. Forecasting Agent (OpenAI GPT-4 + Prophet ML)
                    </h3>
                    <div className="bg-orange-50 p-4 rounded space-y-2">
                      <p className="text-sm font-semibold text-orange-900">
                        Purpose: Demand and revenue forecasting using Prophet ML + n8n data analysis
                      </p>
                      <div className="text-sm text-gray-700">
                        <p className="font-semibold mb-1">Workflow:</p>
                        <ul className="list-disc list-inside space-y-1 ml-2">
                          <li>Loads trained Prophet ML models (3 models: CONTRACTED/STANDARD/CUSTOM)</li>
                          <li>Analyzes n8n ingested data (events, traffic) for context</li>
                          <li>Generates 30/60/90-day demand forecasts with 80% confidence intervals</li>
                          <li>Produces forecasts for analytics dashboard</li>
                          <li>OpenAI GPT-4 explains forecasts in natural language</li>
                          <li>Example: "We expect 145 rides Friday (128-162 range), +18% vs normal"</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* Recommendation Agent */}
                  <div className="border-l-4 border-red-500 pl-4">
                    <h3 className="text-lg font-bold text-gray-800 mb-2">
                      6. Recommendation Agent (OpenAI GPT-4 + RAG)
                    </h3>
                    <div className="bg-red-50 p-4 rounded space-y-2">
                      <p className="text-sm font-semibold text-red-900">
                        Purpose: Strategic recommendations using RAG + n8n data to achieve business objectives
                      </p>
                      <div className="text-sm text-gray-700">
                        <p className="font-semibold mb-1">Workflow:</p>
                        <ul className="list-disc list-inside space-y-1 ml-2">
                          <li>Continuously analyzes newly ingested n8n data (events, traffic, news)</li>
                          <li>Queries ChromaDB strategy_knowledge_vectors (RAG)</li>
                          <li>Combines Forecasting Agent predictions with current market data</li>
                          <li>Generates strategic recommendations to maximize revenue and profit</li>
                          <li>Competitive intelligence based on uploaded competitor data</li>
                          <li>Produces recommendations for analytics dashboard</li>
                        </ul>
                      </div>
                      <div className="bg-white p-3 rounded border border-red-200">
                        <p className="text-xs font-mono text-gray-700">
                          <strong>Example:</strong><br/>
                          n8n ingests: Lakers game Friday 7 PM + Heavy traffic detected →<br/>
                          Forecasting Agent: Predicts +45% demand →<br/>
                          Recommendation Agent: "Increase surge to 1.7x, expected +$8,400 revenue"
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* DATA FLOW */}
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('dataFlow')}
                className="w-full px-6 py-4 bg-gray-50 hover:bg-gray-100 flex items-center justify-between"
              >
                <h2 className="text-xl font-bold text-gray-800">🔄 COMPLETE DATA FLOW</h2>
                {expandedSections.dataFlow ? <ChevronDown size={24} /> : <ChevronRight size={24} />}
              </button>
              {expandedSections.dataFlow && (
                <div className="px-6 py-4 bg-white space-y-4">
                  <div className="bg-blue-50 border-l-4 border-blue-600 p-4 rounded">
                    <h3 className="font-bold text-blue-900 mb-2">System-Wide Data Flow:</h3>
                    <ol className="list-decimal list-inside space-y-1 text-sm text-gray-700">
                      <li>External APIs (Eventbrite, Google Maps, NewsAPI) polled by n8n workflows</li>
                      <li>n8n transforms and writes to MongoDB (events_data, traffic_data, news_articles)</li>
                      <li>Data Ingestion Agent monitors MongoDB change streams</li>
                      <li>Data Ingestion Agent generates embeddings → ChromaDB</li>
                      <li>User query → Frontend → FastAPI → Chatbot Orchestrator Agent</li>
                      <li>Orchestrator routes to worker agent (Analysis/Pricing/Forecasting/Recommendation)</li>
                      <li>Worker agent queries ChromaDB (similarity search for context)</li>
                      <li>Worker agent fetches full documents from MongoDB (mongodb_id)</li>
                      <li>Worker agent sends context to OpenAI GPT-4 (OPENAI_API_KEY)</li>
                      <li>Worker agent returns response to Orchestrator → Frontend → User</li>
                    </ol>
                  </div>

                  <div className="bg-green-50 border-l-4 border-green-600 p-4 rounded">
                    <h3 className="font-bold text-green-900 mb-2">Analytics Dashboard Flow:</h3>
                    <ol className="list-decimal list-inside space-y-1 text-sm text-gray-700">
                      <li>n8n workflows continuously ingest data every 2-15 minutes</li>
                      <li>Data Ingestion Agent creates embeddings for all new data</li>
                      <li>Analysis Agent monitors and analyzes new data for insights</li>
                      <li>Forecasting Agent generates 30/60/90-day forecasts using Prophet ML + n8n data</li>
                      <li>Recommendation Agent produces strategic recommendations</li>
                      <li>All insights cached in analytics_cache collection (updated every 5 min)</li>
                      <li>Frontend dashboard fetches pre-computed analytics</li>
                      <li>Real-time updates via WebSocket when new recommendations generated</li>
                    </ol>
                  </div>

                  <div className="bg-purple-50 border-l-4 border-purple-600 p-4 rounded">
                    <h3 className="font-bold text-purple-900 mb-2">Prophet ML Training & Forecasting Flow:</h3>
                    <ol className="list-decimal list-inside space-y-1 text-sm text-gray-700">
                      <li>User uploads historical_rides.csv (1000+ orders) via frontend</li>
                      <li>POST /api/upload/historical-data validates and stores in MongoDB</li>
                      <li>POST /api/ml/train triggers Prophet training for 3 models</li>
                      <li>Models saved: models/contracted_forecast.pkl, standard_forecast.pkl, custom_forecast.pkl</li>
                      <li>Forecasting Agent loads models for predictions</li>
                      <li>Forecasting Agent analyzes n8n data for additional context</li>
                      <li>Prophet generates forecasts with 80% confidence intervals</li>
                      <li>OpenAI GPT-4 explains forecasts in natural language</li>
                      <li>Forecasts displayed on analytics dashboard (30/60/90-day charts)</li>
                    </ol>
                  </div>
                </div>
              )}
            </div>

            {/* MONGODB COLLECTIONS */}
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('mongodb')}
                className="w-full px-6 py-4 bg-gray-50 hover:bg-gray-100 flex items-center justify-between"
              >
                <h2 className="text-xl font-bold text-gray-800">🗄️ MONGODB COLLECTIONS (High-Level)</h2>
                {expandedSections.mongodb ? <ChevronDown size={24} /> : <ChevronRight size={24} />}
              </button>
              {expandedSections.mongodb && (
                <div className="px-6 py-4 bg-white space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-blue-50 p-4 rounded">
                      <h4 className="font-bold text-blue-900 mb-2">Core Collections (3)</h4>
                      <ul className="text-sm text-gray-700 space-y-1">
                        <li>• ride_orders</li>
                        <li>• customers</li>
                        <li>• pricing_rules</li>
                      </ul>
                    </div>

                    <div className="bg-green-50 p-4 rounded">
                      <h4 className="font-bold text-green-900 mb-2">N8N Populated (3)</h4>
                      <ul className="text-sm text-gray-700 space-y-1">
                        <li>• events_data ⚡</li>
                        <li>• traffic_data ⚡</li>
                        <li>• news_articles ⚡</li>
                      </ul>
                      <p className="text-xs text-green-700 mt-2">⚡ Monitored by Data Ingestion Agent</p>
                    </div>

                    <div className="bg-purple-50 p-4 rounded">
                      <h4 className="font-bold text-purple-900 mb-2">User Uploads (2)</h4>
                      <ul className="text-sm text-gray-700 space-y-1">
                        <li>• historical_rides</li>
                        <li>• competitor_prices</li>
                      </ul>
                    </div>

                    <div className="bg-orange-50 p-4 rounded">
                      <h4 className="font-bold text-orange-900 mb-2">AI & Analytics (4)</h4>
                      <ul className="text-sm text-gray-700 space-y-1">
                        <li>• chat_history</li>
                        <li>• prophet_models</li>
                        <li>• ml_predictions</li>
                        <li>• analytics_cache</li>
                      </ul>
                    </div>
                  </div>

                  <div className="bg-yellow-50 border-l-4 border-yellow-600 p-4 rounded">
                    <p className="text-sm text-gray-700">
                      <strong>Total: 12 collections</strong> - All monitored by Data Ingestion Agent for embeddings.
                      Analysis, Forecasting, and Recommendation Agents continuously analyze n8n populated collections
                      to produce insights, forecasts, and recommendations for business objectives.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* CHROMADB COLLECTIONS */}
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('chromadb')}
                className="w-full px-6 py-4 bg-gray-50 hover:bg-gray-100 flex items-center justify-between"
              >
                <h2 className="text-xl font-bold text-gray-800">🔍 CHROMADB VECTOR COLLECTIONS</h2>
                {expandedSections.chromadb ? <ChevronDown size={24} /> : <ChevronRight size={24} />}
              </button>
              {expandedSections.chromadb && (
                <div className="px-6 py-4 bg-white space-y-4">
                  <div className="bg-indigo-50 border-l-4 border-indigo-600 p-4 rounded">
                    <p className="text-sm text-gray-700 mb-2">
                      <strong>Purpose:</strong> Provide context to AI agents via similarity search (RAG)
                    </p>
                    <p className="text-sm text-gray-700 mb-2">
                      <strong>Embeddings:</strong> OpenAI text-embedding-3-small (1536 dimensions)
                    </p>
                    <p className="text-sm text-gray-700">
                      <strong>Population:</strong> Data Ingestion Agent monitors MongoDB change streams
                    </p>
                  </div>

                  <div className="space-y-3">
                    <div className="bg-gray-50 p-3 rounded border-l-4 border-gray-400">
                      <h4 className="font-bold text-gray-800 text-sm">1. ride_scenarios_vectors</h4>
                      <p className="text-xs text-gray-600 mt-1">Past ride embeddings for pattern matching</p>
                      <p className="text-xs text-gray-600">Used by: Pricing Agent, Analysis Agent</p>
                    </div>

                    <div className="bg-green-50 p-3 rounded border-l-4 border-green-400">
                      <h4 className="font-bold text-green-800 text-sm">2. news_events_vectors ⚡</h4>
                      <p className="text-xs text-green-600 mt-1">Embeddings of n8n ingested events and news</p>
                      <p className="text-xs text-green-600">Used by: Forecasting Agent, Recommendation Agent, Analysis Agent</p>
                    </div>

                    <div className="bg-gray-50 p-3 rounded border-l-4 border-gray-400">
                      <h4 className="font-bold text-gray-800 text-sm">3. customer_behavior_vectors</h4>
                      <p className="text-xs text-gray-600 mt-1">Customer segment behavioral patterns</p>
                      <p className="text-xs text-gray-600">Used by: Analysis Agent, Recommendation Agent</p>
                    </div>

                    <div className="bg-purple-50 p-3 rounded border-l-4 border-purple-400">
                      <h4 className="font-bold text-purple-800 text-sm">4. strategy_knowledge_vectors (RAG)</h4>
                      <p className="text-xs text-purple-600 mt-1">Pricing strategies and business rules</p>
                      <p className="text-xs text-purple-600">Used by: Recommendation Agent (primary), Pricing Agent</p>
                    </div>

                    <div className="bg-gray-50 p-3 rounded border-l-4 border-gray-400">
                      <h4 className="font-bold text-gray-800 text-sm">5. competitor_analysis_vectors</h4>
                      <p className="text-xs text-gray-600 mt-1">Competitor pricing patterns from user uploads</p>
                      <p className="text-xs text-gray-600">Used by: Recommendation Agent, Analysis Agent</p>
                    </div>
                  </div>

                  <div className="bg-blue-50 border-l-4 border-blue-600 p-4 rounded">
                    <p className="text-sm text-gray-700">
                      <strong>⚡ Key:</strong> Collections populated from n8n workflows are actively used by
                      Analysis, Forecasting, and Recommendation Agents to produce real-time insights, forecasts,
                      and strategic recommendations for achieving business objectives.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* 4-DAY TIMELINE */}
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('timeline')}
                className="w-full px-6 py-4 bg-gray-50 hover:bg-gray-100 flex items-center justify-between"
              >
                <h2 className="text-xl font-bold text-gray-800">📅 4-DAY DEVELOPMENT TIMELINE</h2>
                {expandedSections.timeline ? <ChevronDown size={24} /> : <ChevronRight size={24} />}
              </button>
              {expandedSections.timeline && (
                <div className="px-6 py-4 bg-white space-y-4">
                  <div className="bg-gray-50 p-4 rounded">
                    <h3 className="font-bold text-gray-800 mb-2">Team: 4 Developers</h3>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div className="bg-blue-50 p-3 rounded">
                        <p className="font-semibold text-blue-900">Developer 1: Backend Lead</p>
                        <p className="text-xs text-gray-600">FastAPI, MongoDB, Redis, APIs</p>
                      </div>
                      <div className="bg-purple-50 p-3 rounded">
                        <p className="font-semibold text-purple-900">Developer 2: Backend AI/ML</p>
                        <p className="text-xs text-gray-600">Prophet, 6 Agents, n8n, ChromaDB</p>
                      </div>
                      <div className="bg-green-50 p-3 rounded">
                        <p className="font-semibold text-green-900">Developer 3: Frontend Lead</p>
                        <p className="text-xs text-gray-600">Next.js, Core UI, Dashboards</p>
                      </div>
                      <div className="bg-orange-50 p-3 rounded">
                        <p className="font-semibold text-orange-900">Developer 4: Frontend Features</p>
                        <p className="text-xs text-gray-600">Chatbot UI, Analytics, Testing</p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="bg-blue-50 border-l-4 border-blue-600 p-4 rounded">
                      <h4 className="font-bold text-blue-900 mb-2">DAY 1: Foundation & Setup</h4>
                      <ul className="text-sm text-gray-700 space-y-1 ml-4">
                        <li>• Backend: FastAPI + MongoDB + Redis + Priority Queue</li>
                        <li>• AI/ML: n8n setup (3 workflows) + Data Ingestion Agent + ChromaDB</li>
                        <li>• Frontend: Next.js project + Layout + Order UI skeleton</li>
                      </ul>
                    </div>

                    <div className="bg-green-50 border-l-4 border-green-600 p-4 rounded">
                      <h4 className="font-bold text-green-900 mb-2">DAY 2: Prophet ML + Core Features</h4>
                      <ul className="text-sm text-gray-700 space-y-1 ml-4">
                        <li>• Backend: Pricing engine + File uploads + Analytics pre-computation</li>
                        <li>• AI/ML: Prophet ML training + Forecasting endpoints + Embeddings pipeline</li>
                        <li>• Frontend: Order form + Priority queue viz + Historical data upload</li>
                      </ul>
                    </div>

                    <div className="bg-purple-50 border-l-4 border-purple-600 p-4 rounded">
                      <h4 className="font-bold text-purple-900 mb-2">DAY 3: AI Agents + Advanced Features</h4>
                      <ul className="text-sm text-gray-700 space-y-1 ml-4">
                        <li>• Backend: Analytics endpoints + WebSocket + Testing</li>
                        <li>• AI/ML: Implement ALL 6 AI agents + Test with n8n data + RAG workflow</li>
                        <li>• Frontend: Forecast dashboard + Analytics dashboard + Chatbot integration</li>
                      </ul>
                    </div>

                    <div className="bg-orange-50 border-l-4 border-orange-600 p-4 rounded">
                      <h4 className="font-bold text-orange-900 mb-2">DAY 4: Integration, Testing & Deployment</h4>
                      <ul className="text-sm text-gray-700 space-y-1 ml-4">
                        <li>• Backend: Native deployment (systemd) + Testing + Optimization</li>
                        <li>• AI/ML: n8n deployment (PM2) + Test all agents + Verify n8n data analysis</li>
                        <li>• Frontend: Deployment (PM2) + End-to-end testing + Polish</li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* DEPLOYMENT */}
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection('deployment')}
                className="w-full px-6 py-4 bg-gray-50 hover:bg-gray-100 flex items-center justify-between"
              >
                <h2 className="text-xl font-bold text-gray-800">🚀 DEPLOYMENT (NO DOCKER)</h2>
                {expandedSections.deployment ? <ChevronDown size={24} /> : <ChevronRight size={24} />}
              </button>
              {expandedSections.deployment && (
                <div className="px-6 py-4 bg-white space-y-4">
                  <div className="bg-red-50 border-l-4 border-red-600 p-4 rounded">
                    <h3 className="font-bold text-red-900 mb-2">ALL NATIVE INSTALLATIONS - NO DOCKER</h3>
                    <p className="text-sm text-gray-700">
                      Every service runs natively on the host OS. NO containers anywhere.
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-blue-50 p-4 rounded">
                      <h4 className="font-bold text-blue-900 mb-2 text-sm">MongoDB (systemd)</h4>
                      <pre className="text-xs bg-white p-2 rounded border border-blue-200 overflow-x-auto">
{`sudo apt-get install mongodb-org
sudo systemctl enable mongod
sudo systemctl start mongod`}
                      </pre>
                    </div>

                    <div className="bg-green-50 p-4 rounded">
                      <h4 className="font-bold text-green-900 mb-2 text-sm">Redis (systemd)</h4>
                      <pre className="text-xs bg-white p-2 rounded border border-green-200 overflow-x-auto">
{`sudo apt-get install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server`}
                      </pre>
                    </div>

                    <div className="bg-purple-50 p-4 rounded">
                      <h4 className="font-bold text-purple-900 mb-2 text-sm">n8n (PM2)</h4>
                      <pre className="text-xs bg-white p-2 rounded border border-purple-200 overflow-x-auto">
{`npm install -g n8n pm2
pm2 start n8n --name "n8n-workflows"
pm2 save
pm2 startup`}
                      </pre>
                    </div>

                    <div className="bg-orange-50 p-4 rounded">
                      <h4 className="font-bold text-orange-900 mb-2 text-sm">Backend (systemd)</h4>
                      <pre className="text-xs bg-white p-2 rounded border border-orange-200 overflow-x-auto">
{`[Unit]
Description=Rideshare Backend

[Service]
ExecStart=uvicorn app.main:app
Restart=always

[Install]
WantedBy=multi-user.target`}
                      </pre>
                    </div>

                    <div className="bg-teal-50 p-4 rounded">
                      <h4 className="font-bold text-teal-900 mb-2 text-sm">Frontend (PM2)</h4>
                      <pre className="text-xs bg-white p-2 rounded border border-teal-200 overflow-x-auto">
{`npm run build
pm2 start npm --name "frontend" -- start
pm2 save`}
                      </pre>
                    </div>

                    <div className="bg-indigo-50 p-4 rounded">
                      <h4 className="font-bold text-indigo-900 mb-2 text-sm">Verification</h4>
                      <pre className="text-xs bg-white p-2 rounded border border-indigo-200 overflow-x-auto">
{`systemctl status mongod
systemctl status redis-server
pm2 status
docker ps # Should fail!`}
                      </pre>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* FOOTER */}
            <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-6 mt-8">
              <div className="text-center">
                <h3 className="text-2xl font-bold text-purple-900 mb-2">
                  ✅ Version 7.0 - Ready for Implementation
                </h3>
                <p className="text-sm text-gray-700 mb-4">
                  6 AI Agents | Prophet ML | NO Docker | 30/60/90-Day Forecasts | n8n Data Analysis
                </p>
                <div className="grid grid-cols-4 gap-4 text-center">
                  <div className="bg-white p-3 rounded shadow">
                    <p className="text-2xl font-bold text-purple-600">6</p>
                    <p className="text-xs text-gray-600">AI Agents</p>
                  </div>
                  <div className="bg-white p-3 rounded shadow">
                    <p className="text-2xl font-bold text-green-600">100%</p>
                    <p className="text-xs text-gray-600">Native (NO Docker)</p>
                  </div>
                  <div className="bg-white p-3 rounded shadow">
                    <p className="text-2xl font-bold text-blue-600">4</p>
                    <p className="text-xs text-gray-600">Days to Deploy</p>
                  </div>
                  <div className="bg-white p-3 rounded shadow">
                    <p className="text-2xl font-bold text-orange-600">15-25%</p>
                    <p className="text-xs text-gray-600">Revenue Increase</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DynamicPricingArchitectureV7;
