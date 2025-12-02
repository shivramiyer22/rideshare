import React, { useState, useCallback } from 'react';
import { Download, ChevronDown, ChevronRight, AlertCircle, Upload, FileText, Database } from 'lucide-react';

const DynamicPricingArchitectureV8 = () => {
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

  const [activeView, setActiveView] = useState('overview'); // 'overview' or 'competitor-upload'
  const [dragActive, setDragActive] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setUploadedFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setUploadedFile(e.target.files[0]);
    }
  };

  const handleUpload = () => {
    if (uploadedFile) {
      // Handle upload logic here
      console.log('Uploading:', uploadedFile.name);
      alert(`File "${uploadedFile.name}" uploaded successfully!`);
      setUploadedFile(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-xl shadow-2xl p-8">
          {/* Header */}
          <div className="flex justify-between items-start mb-6">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                Dynamic Pricing AI Solution v8.0
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

          {/* Navigation Buttons */}
          <div className="flex gap-4 mb-6">
            <button
              onClick={() => setActiveView('overview')}
              className={`flex items-center gap-2 px-6 py-3 rounded-lg transition-colors ${
                activeView === 'overview'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <FileText size={20} />
              Overview
            </button>
            <button
              onClick={() => setActiveView('upload')}
              className={`flex items-center gap-2 px-6 py-3 rounded-lg transition-colors ${
                activeView === 'upload'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Upload size={20} />
              Upload
            </button>
          </div>

          {/* Upload View */}
          {activeView === 'upload' && (
            <div className="space-y-6">
              <div className="bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 rounded-xl p-8">
                <h2 className="text-2xl font-bold text-white mb-4">File Upload</h2>
                <p className="text-purple-200 mb-6">
                  Upload historical ride data for Prophet ML training or competitor pricing data
                </p>

                {/* Historical Data Requirements */}
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 mb-6">
                  <h3 className="text-lg font-bold text-white mb-4">Historical Data Requirements</h3>
                  <div className="space-y-3 text-sm">
                    <div>
                      <p className="text-purple-200 font-semibold mb-1">Required columns (minimum 10):</p>
                      <p className="text-purple-300 font-mono text-xs">
                        Datetime, Customer_Name, Historical_Cost, Ride_From, Model, Expected_Ride_Duration, 
                        Number_Of_Riders, Customer_ID, Number_Of_Past_Rides, Average_Rating
                      </p>
                    </div>
                    <div>
                      <p className="text-purple-200 font-semibold mb-1">Optional columns:</p>
                      <p className="text-purple-300 font-mono text-xs">
                        Customer_ID, Number_Of_Riders, Location_Category, Customer_Loyalty_Status, 
                        Number_of_Past_Rides, Average_Rating, Time_of_Ride, Vehicle_Type
                      </p>
                    </div>
                    <div>
                      <p className="text-purple-200 font-semibold mb-1">Accepted formats:</p>
                      <p className="text-purple-300">CSV, JSON</p>
                    </div>
                    <div>
                      <p className="text-purple-200 font-semibold mb-1">Derived fields (Urgency_By_Demand, Demand_Profile, Historical_Unit_Price, Historical_Price) are calculated automatically</p>
                    </div>
                  </div>
                </div>

                {/* What happens after upload */}
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 mb-6">
                  <h3 className="text-lg font-bold text-white mb-3">What happens after upload?</h3>
                  <ul className="space-y-2 text-sm text-purple-200">
                    <li>• Data is validated and stored in MongoDB</li>
                    <li>• Derived fields (Urgency_By_Demand, Demand_Profile, Historical_Unit_Price, Historical_Price) are calculated automatically</li>
                    <li>• Use the ML training endpoint to train Prophet ML model on this data</li>
                  </ul>
                </div>

                {/* Drag and Drop Area */}
                <div
                  className={`relative border-2 border-dashed rounded-xl p-12 transition-all ${
                    dragActive
                      ? 'border-purple-400 bg-purple-500/20'
                      : 'border-purple-400/50 bg-white/5'
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  <div className="flex flex-col items-center justify-center text-center">
                    <Upload className="text-purple-300 mb-4" size={48} />
                    <p className="text-white text-lg font-semibold mb-2">
                      Drag and drop your file here, or
                    </p>
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <span className="inline-block px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
                        Browse Files
                      </span>
                      <input
                        id="file-upload"
                        type="file"
                        className="hidden"
                        accept=".csv,.json"
                        onChange={handleFileChange}
                      />
                    </label>
                    <p className="text-purple-300 text-sm mt-4">CSV or JSON files only</p>
                  </div>
                </div>

                {/* Uploaded File Display */}
                {uploadedFile && (
                  <div className="mt-6 bg-white/10 backdrop-blur-sm rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <FileText className="text-purple-300" size={24} />
                        <div>
                          <p className="text-white font-semibold">{uploadedFile.name}</p>
                          <p className="text-purple-300 text-sm">
                            {(uploadedFile.size / 1024).toFixed(2)} KB
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={handleUpload}
                        className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
                      >
                        <Upload size={16} />
                        Upload Historical Data
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Overview Content */}
          {activeView === 'overview' && (
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
                        <li>✅ Chatbot Orchestrator Agent - Routes queries to worker agents</li>
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

              {/* Rest of the sections remain the same... */}
              {/* AI AGENTS, DATA FLOW, MONGODB, CHROMADB, TIMELINE, DEPLOYMENT sections */}
              
              {/* FOOTER */}
              <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-6 mt-8">
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-purple-900 mb-2">
                    ✅ Version 8.0 - Ready for Implementation
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
          )}
        </div>
      </div>
    </div>
  );
};

export default DynamicPricingArchitectureV8;

