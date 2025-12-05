import React from 'react';

const PipelineProcessFlow = () => {
  return (
    <div className="min-h-screen bg-white p-8">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-xl shadow-2xl p-8 border-2 border-gray-300">
          {/* Header */}
          <div className="text-center mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              AI-Powered Dynamic Pricing Pipeline
            </h1>
            <p className="text-lg text-purple-600 font-semibold">
              End-to-End Data Flow: External APIs → AI Agents → Business Intelligence
            </p>
          </div>

          {/* Main Pipeline Diagram */}
          <div className="bg-slate-50 p-6 rounded-lg border-2 border-slate-300">
            <pre className="text-gray-800 text-xs font-mono whitespace-pre leading-relaxed">
{`┌────────────────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL DATA SOURCES (Real-Time)                          │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│    ┌──────────────┐      ┌──────────────┐      ┌──────────────┐                   │
│    │  PredictHQ   │      │   TomTom     │      │  NewsHere    │                   │
│    │Events API    │      │ Traffic API  │      │   News API   │                   │
│    │(Daily 6 AM)  │      │ (Every 2min) │      │(Every 15min) │                   │
│    └──────┬───────┘      └──────┬───────┘      └──────┬───────┘                   │
│           │                     │                      │                            │
│           └─────────────────────┴──────────────────────┘                            │
│                                 │                                                   │
└─────────────────────────────────┼───────────────────────────────────────────────────┘
                                  ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                            DATA INGESTION & STORAGE                                 │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  [n8n Workflows] → Transform & Load → [MongoDB Atlas]                              │
│                                                                                     │
│  • Events, traffic, news stored in collections                                     │
│  • Historical rides (CSV uploads) → Prophet ML training data                       │
│  • Competitor pricing → Competitive intelligence                                   │
│  • Real-time change streams trigger embeddings generation                          │
│                                                                                     │
└─────────────────────────────────┬───────────────────────────────────────────────────┘
                                  ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                       AI PROCESSING LAYER (6 Agents)                                │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Data Ingestion Agent → Creates embeddings → ChromaDB vectors                      │
│                              ↓                                                      │
│           ┌──────────────────┴──────────────────┐                                  │
│           │    Chatbot Orchestrator (Router)    │                                  │
│           └──────────────┬──────────────────────┘                                  │
│                          │                                                          │
│      ┌───────────────────┼───────────────────┐                                     │
│      ▼                   ▼                   ▼                                     │
│  ┌─────────┐      ┌──────────┐      ┌─────────────┐                               │
│  │Analysis │      │ Pricing  │      │ Forecasting │                               │
│  │ Agent   │      │  Agent   │      │   Agent     │                               │
│  │(KPIs)   │      │(Dynamic) │      │(Prophet ML) │                               │
│  └────┬────┘      └────┬─────┘      └──────┬──────┘                               │
│       │                │                    │                                      │
│       └────────────────┴────────────────────┘                                      │
│                        │                                                            │
│                        ▼                                                            │
│              ┌──────────────────┐                                                  │
│              │ Recommendation   │                                                  │
│              │     Agent        │                                                  │
│              │ (Strategic AI)   │                                                  │
│              └────────┬─────────┘                                                  │
│                       │                                                             │
└───────────────────────┼─────────────────────────────────────────────────────────────┘
                        ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                          BUSINESS INTELLIGENCE OUTPUT                               │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  📊 Forecasts: 30/60/90-day demand predictions (Prophet ML)                        │
│  💰 Pricing Rules: Optimized multipliers & surge strategies                        │
│  🎯 Recommendations: 3 strategic options to maximize revenue                        │
│  📈 KPIs: Revenue, profit margins, competitive positioning                          │
│  ⚡ Real-Time: Dynamic pricing based on current conditions                          │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘`}
            </pre>
          </div>

          {/* Key Points */}
          <div className="mt-6 grid grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-600">
              <h3 className="font-bold text-blue-900 mb-2 text-sm">Data Sources</h3>
              <ul className="text-xs text-gray-700 space-y-1">
                <li>• PredictHQ: Events data</li>
                <li>• TomTom: Traffic patterns</li>
                <li>• NewsHere: Market news</li>
                <li>• CSV uploads: Historical data</li>
              </ul>
            </div>

            <div className="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-600">
              <h3 className="font-bold text-purple-900 mb-2 text-sm">AI Processing</h3>
              <ul className="text-xs text-gray-700 space-y-1">
                <li>• 6 specialized AI agents</li>
                <li>• Prophet ML forecasting</li>
                <li>• RAG-powered insights</li>
                <li>• Real-time analysis</li>
              </ul>
            </div>

            <div className="bg-green-50 p-4 rounded-lg border-l-4 border-green-600">
              <h3 className="font-bold text-green-900 mb-2 text-sm">Business Value</h3>
              <ul className="text-xs text-gray-700 space-y-1">
                <li>• 15-25% revenue increase</li>
                <li>• Competitive positioning</li>
                <li>• Data-driven decisions</li>
                <li>• Automated optimization</li>
              </ul>
            </div>
          </div>

          {/* Pipeline Phases */}
          <div className="mt-6 bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border border-gray-300">
            <h3 className="font-bold text-gray-900 mb-3 text-center">Pipeline Execution Flow</h3>
            <div className="flex items-center justify-between text-xs">
              <div className="text-center flex-1">
                <div className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center mx-auto mb-1 font-bold">1</div>
                <p className="font-semibold text-gray-800">Ingest Data</p>
                <p className="text-gray-600 text-xs">APIs → MongoDB</p>
              </div>
              <div className="text-gray-400 text-2xl">→</div>
              <div className="text-center flex-1">
                <div className="bg-purple-600 text-white rounded-full w-8 h-8 flex items-center justify-center mx-auto mb-1 font-bold">2</div>
                <p className="font-semibold text-gray-800">Analyze & Forecast</p>
                <p className="text-gray-600 text-xs">AI Agents + ML</p>
              </div>
              <div className="text-gray-400 text-2xl">→</div>
              <div className="text-center flex-1">
                <div className="bg-green-600 text-white rounded-full w-8 h-8 flex items-center justify-center mx-auto mb-1 font-bold">3</div>
                <p className="font-semibold text-gray-800">Generate Rules</p>
                <p className="text-gray-600 text-xs">Pricing strategies</p>
              </div>
              <div className="text-gray-400 text-2xl">→</div>
              <div className="text-center flex-1">
                <div className="bg-orange-600 text-white rounded-full w-8 h-8 flex items-center justify-center mx-auto mb-1 font-bold">4</div>
                <p className="font-semibold text-gray-800">Recommend</p>
                <p className="text-gray-600 text-xs">Strategic options</p>
              </div>
            </div>
          </div>

          {/* Footer Stats */}
          <div className="mt-6 grid grid-cols-4 gap-3 text-center">
            <div className="bg-white p-3 rounded shadow-md border border-gray-200">
              <p className="text-2xl font-bold text-blue-600">162</p>
              <p className="text-xs text-gray-600">Segments Analyzed</p>
            </div>
            <div className="bg-white p-3 rounded shadow-md border border-gray-200">
              <p className="text-2xl font-bold text-purple-600">6</p>
              <p className="text-xs text-gray-600">AI Agents</p>
            </div>
            <div className="bg-white p-3 rounded shadow-md border border-gray-200">
              <p className="text-2xl font-bold text-green-600">3</p>
              <p className="text-xs text-gray-600">Time Horizons</p>
            </div>
            <div className="bg-white p-3 rounded shadow-md border border-gray-200">
              <p className="text-2xl font-bold text-orange-600">~12s</p>
              <p className="text-xs text-gray-600">Pipeline Runtime</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PipelineProcessFlow;

