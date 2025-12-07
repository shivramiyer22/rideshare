import React from 'react';

const SolutionArchitecture = () => {
  return (
    <div className="min-h-screen bg-white p-8">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-xl shadow-2xl p-8 border-2 border-gray-300">
          {/* Header */}
          <div className="text-center mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Dynamic Pricing Solution Architecture
            </h1>
            <p className="text-lg text-blue-600 font-semibold">
              MongoDB Atlas + FastAPI + Next.js + 6 AI Agents + Prophet ML
            </p>
          </div>

          {/* Main Architecture Diagram */}
          <div className="bg-slate-50 p-6 rounded-lg border-2 border-slate-300">
            <pre className="text-gray-800 text-xs font-mono whitespace-pre leading-relaxed">
{`┌──────────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                                     │
│                     Next.js 14 Frontend (Port 3000)                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Dashboard    │  Segment Analysis  │  Forecasts  │  Chatbot  │  Orders      │
│  • KPIs       │  • 162 Segments    │  • 30/60/90 │  • AI     │  • Priority  │
│  • Revenue    │  • HWCO vs Lyft    │  • Prophet  │  • WebSkt │  • Queue     │
│                                                                               │
└───────────────────────────────┬───────────────────────────────────────────────┘
                                │ REST API + WebSocket
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          APPLICATION LAYER                                    │
│                    FastAPI Backend (Python 3.12)                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌────────────────────┐  ┌────────────────────┐  ┌───────────────────┐     │
│  │   API Routers      │  │  Pricing Engine    │  │  Prophet ML       │     │
│  │   • /orders        │  │  • Dynamic rules   │  │  • Forecasting    │     │
│  │   • /analytics     │  │  • Surge logic     │  │  • 3 models       │     │
│  │   • /ml            │  │  • Loyalty tiers   │  │  • 30/60/90 days  │     │
│  │   • /pipeline      │  │  • Multipliers     │  │  • Training       │     │
│  │   • /chatbot       │  └────────────────────┘  └───────────────────┘     │
│  │   • /reports       │                                                      │
│  └────────────────────┘                                                      │
│                                                                               │
└───────────────────────────────┬───────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            AI AGENT LAYER                                     │
│                   LangChain + LangGraph + OpenAI GPT-4                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐         │
│  │              Orchestrator Agent (Chatbot Router)                │         │
│  │              • Routes queries to specialist agents              │         │
│  │              • Maintains conversation context                   │         │
│  └────────────────────────┬────────────────────────────────────────┘         │
│                           │                                                   │
│    ┌──────────────────────┼──────────────────────┐                           │
│    │          │           │           │          │                           │
│    ▼          ▼           ▼           ▼          ▼                           │
│  ┌─────┐  ┌────────┐  ┌────────┐  ┌──────────┐  ┌──────────────┐           │
│  │Data │  │Analysis│  │Pricing │  │Forecast  │  │Recommendation│           │
│  │Ingest│  │Agent   │  │Agent   │  │Agent     │  │Agent         │           │
│  │Agent │  │        │  │        │  │(Prophet) │  │(Strategic)   │           │
│  └──┬──┘  └───┬────┘  └───┬────┘  └────┬─────┘  └──────┬───────┘           │
│     │         │            │            │                │                   │
│     │         └────────────┴────────────┴────────────────┘                   │
│     │                              │                                          │
│     │ Embeddings                   │ RAG Queries                             │
│     ▼                              ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐            │
│  │         ChromaDB (Vector Store - Local Persistence)          │            │
│  │  • 5 collections with OpenAI embeddings (1536d)              │            │
│  │  • RAG for context-aware AI responses                        │            │
│  └──────────────────────────────────────────────────────────────┘            │
│                                                                               │
└───────────────────────────────┬───────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER                                         │
│                      MongoDB Atlas (Cloud Database)                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Core Data (3)         │  External Data (3)      │  ML & Analytics (3)       │
│  • ride_orders         │  • events_data          │  • pricing_strategies     │
│  • customers           │  • traffic_data         │  • pipeline_results       │
│  • historical_rides    │  • news_articles        │  • ml_training_metadata   │
│                        │                         │                           │
│  Total: 9 Collections  │  All indexed & optimized for fast queries           │
│                                                                               │
└───────────────────────────────┬───────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL DATA SOURCES                                  │
│                          (n8n Workflow Automation)                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  PredictHQ Events API    │    TomTom Traffic API    │    NewsHere News API   │
│  (Daily at 6 AM)         │    (Every 2 minutes)     │    (Every 15 minutes)  │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘`}
            </pre>
          </div>

          {/* Architecture Layers */}
          <div className="mt-6 grid grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="bg-blue-50 p-3 rounded-lg border-l-4 border-blue-600">
                <h4 className="font-bold text-blue-900 text-sm mb-1">Frontend Layer</h4>
                <ul className="text-xs text-gray-700 space-y-1">
                  <li>• Next.js 14 with TypeScript</li>
                  <li>• Real-time WebSocket chatbot</li>
                  <li>• Interactive dashboards & charts</li>
                  <li>• Segment analysis tables (162 segments)</li>
                </ul>
              </div>

              <div className="bg-purple-50 p-3 rounded-lg border-l-4 border-purple-600">
                <h4 className="font-bold text-purple-900 text-sm mb-1">Backend Layer</h4>
                <ul className="text-xs text-gray-700 space-y-1">
                  <li>• FastAPI with async endpoints</li>
                  <li>• Dynamic pricing engine</li>
                  <li>• Prophet ML integration</li>
                  <li>• Pipeline orchestrator</li>
                </ul>
              </div>

              <div className="bg-green-50 p-3 rounded-lg border-l-4 border-green-600">
                <h4 className="font-bold text-green-900 text-sm mb-1">AI Agent Layer</h4>
                <ul className="text-xs text-gray-700 space-y-1">
                  <li>• 6 specialized AI agents</li>
                  <li>• LangChain + LangGraph orchestration</li>
                  <li>• OpenAI GPT-4 powered</li>
                  <li>• RAG with ChromaDB vectors</li>
                </ul>
              </div>
            </div>

            <div className="space-y-3">
              <div className="bg-orange-50 p-3 rounded-lg border-l-4 border-orange-600">
                <h4 className="font-bold text-orange-900 text-sm mb-1">Data Layer</h4>
                <ul className="text-xs text-gray-700 space-y-1">
                  <li>• MongoDB Atlas (cloud)</li>
                  <li>• 9 collections, fully indexed</li>
                  <li>• Change streams for real-time</li>
                  <li>• ChromaDB for vector search</li>
                </ul>
              </div>

              <div className="bg-red-50 p-3 rounded-lg border-l-4 border-red-600">
                <h4 className="font-bold text-red-900 text-sm mb-1">External Data</h4>
                <ul className="text-xs text-gray-700 space-y-1">
                  <li>• PredictHQ: Event intelligence</li>
                  <li>• TomTom: Traffic data</li>
                  <li>• NewsHere: Market news</li>
                  <li>• n8n: Workflow automation</li>
                </ul>
              </div>

              <div className="bg-indigo-50 p-3 rounded-lg border-l-4 border-indigo-600">
                <h4 className="font-bold text-indigo-900 text-sm mb-1">ML/Analytics</h4>
                <ul className="text-xs text-gray-700 space-y-1">
                  <li>• Prophet ML forecasting</li>
                  <li>• Multi-dimensional analysis</li>
                  <li>• Segment dynamic pricing</li>
                  <li>• Competitive intelligence</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Key Capabilities */}
          <div className="mt-6 bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border border-gray-300">
            <h3 className="font-bold text-gray-900 mb-3 text-center">Core System Capabilities</h3>
            <div className="grid grid-cols-4 gap-3 text-xs">
              <div className="text-center">
                <div className="bg-blue-600 text-white rounded-lg p-2 mb-1 font-bold">Real-Time</div>
                <p className="text-gray-700">Live data ingestion & analysis</p>
              </div>
              <div className="text-center">
                <div className="bg-purple-600 text-white rounded-lg p-2 mb-1 font-bold">AI-Powered</div>
                <p className="text-gray-700">6 intelligent agents</p>
              </div>
              <div className="text-center">
                <div className="bg-green-600 text-white rounded-lg p-2 mb-1 font-bold">Forecasting</div>
                <p className="text-gray-700">30/60/90-day predictions</p>
              </div>
              <div className="text-center">
                <div className="bg-orange-600 text-white rounded-lg p-2 mb-1 font-bold">Strategic</div>
                <p className="text-gray-700">Automated recommendations</p>
              </div>
            </div>
          </div>

          {/* Technology Stack */}
          <div className="mt-6 bg-gray-50 p-4 rounded-lg border border-gray-300">
            <h3 className="font-bold text-gray-900 mb-2 text-center text-sm">Technology Stack</h3>
            <div className="flex flex-wrap justify-center gap-2 text-xs">
              <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full font-semibold">Next.js 14</span>
              <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full font-semibold">FastAPI</span>
              <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full font-semibold">Python 3.12</span>
              <span className="bg-orange-100 text-orange-800 px-3 py-1 rounded-full font-semibold">MongoDB Atlas</span>
              <span className="bg-red-100 text-red-800 px-3 py-1 rounded-full font-semibold">OpenAI GPT-4</span>
              <span className="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full font-semibold">Prophet ML</span>
              <span className="bg-pink-100 text-pink-800 px-3 py-1 rounded-full font-semibold">LangChain</span>
              <span className="bg-teal-100 text-teal-800 px-3 py-1 rounded-full font-semibold">ChromaDB</span>
              <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full font-semibold">n8n</span>
            </div>
          </div>

          {/* Footer Stats */}
          <div className="mt-6 grid grid-cols-5 gap-2 text-center">
            <div className="bg-white p-3 rounded shadow-md border border-gray-200">
              <p className="text-xl font-bold text-blue-600">9</p>
              <p className="text-xs text-gray-600">Collections</p>
            </div>
            <div className="bg-white p-3 rounded shadow-md border border-gray-200">
              <p className="text-xl font-bold text-purple-600">6</p>
              <p className="text-xs text-gray-600">AI Agents</p>
            </div>
            <div className="bg-white p-3 rounded shadow-md border border-gray-200">
              <p className="text-xl font-bold text-green-600">3</p>
              <p className="text-xs text-gray-600">APIs</p>
            </div>
            <div className="bg-white p-3 rounded shadow-md border border-gray-200">
              <p className="text-xl font-bold text-orange-600">162</p>
              <p className="text-xs text-gray-600">Segments</p>
            </div>
            <div className="bg-white p-3 rounded shadow-md border border-gray-200">
              <p className="text-xl font-bold text-red-600">100%</p>
              <p className="text-xs text-gray-600">Cloud Native</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SolutionArchitecture;


