# Backend Architecture Summary

## 1. Backend Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLIENT APPLICATIONS                             │
│                     (Frontend, Swagger UI, API Clients)                  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI APPLICATION                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         API ROUTERS                              │   │
│  │  /orders  /upload  /ml  /analytics  /chatbot  /pipeline        │   │
│  │                    /agents/test                                  │   │
│  └──────────────────┬────────────────────────────┬─────────────────┘   │
└────────────────────┬┴────────────────────────────┴┬────────────────────┘
                     │                              │
          ┌──────────▼──────────┐      ┌───────────▼────────────┐
          │   PRICING ENGINE    │      │  PROPHET ML MODEL      │
          │  (Dynamic Pricing)  │      │   (Forecasting)        │
          └─────────────────────┘      └────────────────────────┘
                     │
                     │
┌────────────────────▼─────────────────────────────────────────────────────┐
│                          AI AGENT SYSTEM                                  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              ORCHESTRATOR AGENT (Chatbot Router)                 │   │
│  │         Routes queries to specialist agents                       │   │
│  └──────┬──────────┬───────────┬──────────┬────────────────────────┘   │
│         │          │           │          │                             │
│  ┌──────▼─────┐ ┌──▼─────┐ ┌──▼─────┐ ┌──▼──────────┐                 │
│  │ ANALYSIS   │ │ PRICING│ │FORECAST│ │RECOMMENDATION│                 │
│  │   AGENT    │ │ AGENT  │ │ AGENT  │ │    AGENT     │                 │
│  └──────┬─────┘ └──┬─────┘ └──┬─────┘ └──────┬───────┘                 │
│         │          │           │              │                         │
│         └──────────┴───────────┴──────────────┘                         │
│                            │                                             │
│  ┌────────────────────────▼────────────────────────────────────────┐   │
│  │                  SHARED UTILITIES & HELPERS                      │   │
│  │  - MongoDB Query Tools    - Pricing Helpers                      │   │
│  │  - ChromaDB Query Tools   - Forecasting Helpers                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└───────────────────────┬───────────────────────────┬──────────────────────┘
                        │                           │
          ┌─────────────▼──────────┐   ┌───────────▼────────────┐
          │   MONGODB DATABASE     │   │  CHROMADB VECTORSTORE  │
          │  (Persistent Storage)  │   │   (RAG Embeddings)     │
          └────────────────────────┘   └────────────────────────┘
                        │                           ▲
                        │                           │
          ┌─────────────▼──────────────────────────┘
          │  DATA INGESTION AGENT                  │
          │  (Monitors MongoDB, Creates Embeddings)│
          └────────────────────────────────────────┘
```

## 2. MongoDB and ChromaDB Collections

### MongoDB Collections (8):

| Collection | Description |
|-----------|-------------|
| `historical_rides` | HWCO historical ride data (completed orders, pricing, segments) |
| `competitor_prices` | Lyft competitor pricing data for market analysis |
| `events_data` | Eventbrite events from n8n workflow (concerts, sports, conferences) |
| `traffic_data` | Google Maps traffic patterns from n8n workflow |
| `news_articles` | NewsAPI articles from n8n workflow (local news, market trends) |
| `customers` | Customer profiles and loyalty tiers |
| `ride_orders` | Active ride orders with priority queue (P0/P1/P2) |
| `pricing_strategies` | Business objectives, pricing rules, ML metadata, pipeline results |

### ChromaDB Collections (5):

| Collection | Description |
|-----------|-------------|
| `ride_scenarios_vectors` | Embeddings from historical_rides and ride_orders |
| `news_events_vectors` | Embeddings from events_data and news_articles |
| `customer_behavior_vectors` | Embeddings from customers collection |
| `strategy_knowledge_vectors` | Embeddings from pricing_strategies |
| `competitor_analysis_vectors` | Embeddings from competitor_prices |

## 3. Backend Agents

### Data Ingestion Agent
**Inputs:** MongoDB change streams (all 8 collections)  
**Functionality:** Monitors MongoDB for changes, generates text descriptions, creates OpenAI embeddings (text-embedding-3-small, 1536d), stores in ChromaDB with metadata  
**Outputs:** 5 ChromaDB collections with embeddings for RAG queries

### Orchestrator Agent (Chatbot Router)
**Inputs:** User query (string), conversation context (thread_id)  
**Functionality:** Routes queries to specialist agents using GPT-4o-mini and 4 routing tools, maintains conversation memory with InMemorySaver  
**Outputs:** Specialist agent response routed back to user

### Analysis Agent
**Inputs:** Query about revenue, KPIs, business intelligence, historical data  
**Functionality:** Queries MongoDB (historical_rides, competitor_prices, events, traffic, news), performs data analysis, generates pricing rules, calculates what-if impact on forecasts  
**Outputs:** JSON with analysis results, pricing rules, KPI projections, natural language explanations

### Pricing Agent
**Inputs:** Order data (location, distance, duration, vehicle type, loyalty tier, pricing model)  
**Functionality:** Uses PricingEngine to calculate dynamic prices with detailed breakdowns (base fare, distance rate, time rate, surge multiplier, loyalty discount, rule multipliers), queries pricing strategies from MongoDB  
**Outputs:** JSON with final_price, breakdown components, pricing explanation

### Forecasting Agent
**Inputs:** Forecast periods (30/60/90 days), segment filters (optional)  
**Functionality:** Generates multi-dimensional forecasts across 5 dimensions (162 segments), uses PricingEngine for price forecasts and forecasting_helpers for demand projections, supports future Prophet ML integration  
**Outputs:** JSON with segmented forecasts (baseline metrics, predicted rides, predicted revenue for 30/60/90 days), aggregated totals, forecast methodology

### Recommendation Agent
**Inputs:** Forecasts (from Forecasting Agent), pricing rules (from Analysis Agent)  
**Functionality:** Simulates pricing rules using PricingEngine, ranks rule combinations by business objective impact (revenue, profit margin, competitiveness, churn reduction), generates top 3 strategic recommendations  
**Outputs:** JSON with top 3 recommendations (rules, estimated impact, confidence score, rationale)

## 4. Data Ingestion Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    1. DATA UPLOAD & INGESTION                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
         ┌──────▼─────────┐      ┌───────▼────────┐
         │  CSV UPLOAD    │      │  n8n WORKFLOWS │
         │  /api/v1/upload│      │  (Background)  │
         │  - Historical  │      │  - Eventbrite  │
         │  - Competitor  │      │  - Google Maps │
         └──────┬─────────┘      │  - NewsAPI     │
                │                └───────┬────────┘
                │                        │
                └────────────┬───────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│                    2. MONGODB STORAGE                                 │
│  historical_rides, competitor_prices, events_data,                    │
│  traffic_data, news_articles                                          │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             │ Change Streams Monitor
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│              3. DATA INGESTION AGENT (Background Process)             │
│  - Detects MongoDB changes                                            │
│  - Generates text descriptions                                        │
│  - Creates OpenAI embeddings (1536d)                                  │
│  - Stores in 5 ChromaDB collections                                   │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│              4. PIPELINE ORCHESTRATOR (Auto/Manual Trigger)           │
│  Triggers when: Change threshold reached OR manual request            │
└──────────────────┬────────────────────┬──────────────────────────────┘
                   │                    │
         ┌─────────▼─────────┐ ┌────────▼──────────┐
         │ FORECASTING AGENT │ │  ANALYSIS AGENT   │
         │ (30/60/90 day     │ │ (Pricing rules,   │
         │  predictions)     │ │  external data)   │
         └─────────┬─────────┘ └────────┬──────────┘
                   │                    │
                   └──────────┬─────────┘
                              │
                   ┌──────────▼──────────┐
                   │ RECOMMENDATION AGENT│
                   │ (Top 3 strategic    │
                   │  recommendations)   │
                   └──────────┬──────────┘
                              │
                   ┌──────────▼──────────┐
                   │ WHAT-IF ANALYSIS    │
                   │ (Impact on KPIs:    │
                   │  revenue, margin,   │
                   │  churn, 30/60/90d)  │
                   └──────────┬──────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────────────┐
│         5. RESULTS STORAGE (MongoDB: pricing_strategies)              │
│  - forecasts (segmented + aggregated)                                 │
│  - pricing_rules (generated by Analysis Agent)                        │
│  - recommendations (top 3 with rule combinations)                     │
│  - whatif_analysis (30/60/90 day KPI projections)                     │
└───────────────────────────────────────────────────────────────────────┘
```

## 5. Chatbot Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                   1. USER QUERY (via /chatbot/chat)                  │
│              WebSocket or HTTP POST with message                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│              2. ORCHESTRATOR AGENT (Chatbot Router)                   │
│  - Receives user message + thread_id                                  │
│  - Uses GPT-4o-mini to analyze query intent                           │
│  - Selects appropriate routing tool                                   │
└──────┬───────────┬─────────────┬──────────────┬───────────────────────┘
       │           │             │              │
┌──────▼──────┐ ┌──▼─────┐ ┌────▼─────┐ ┌──────▼──────────┐
│  ANALYSIS   │ │ PRICING│ │FORECASTING│ │ RECOMMENDATION │
│   AGENT     │ │ AGENT  │ │  AGENT    │ │     AGENT      │
└──────┬──────┘ └──┬─────┘ └────┬──────┘ └──────┬─────────┘
       │           │             │               │
       │     3. SPECIALIST AGENT PROCESSING      │
       │     - Queries MongoDB (direct access)   │
       │     - Queries ChromaDB (RAG embeddings) │
       │     - Uses PricingEngine (if needed)    │
       │     - Generates analysis/recommendations│
       │                                          │
       └──────────────┬───────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────────────────────┐
│           4. ORCHESTRATOR RECEIVES SPECIALIST RESPONSE             │
│  - Formats response                                                │
│  - Updates conversation memory (thread_id)                         │
└────────────────────────────┬───────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│               5. RESPONSE RETURNED TO USER                            │
│  WebSocket message or HTTP response with formatted answer             │
└───────────────────────────────────────────────────────────────────────┘
```
