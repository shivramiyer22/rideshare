# Dynamic Pricing Solutions - Frontend

AI-Powered Dynamic Pricing Intelligence Platform

## Features

- **6 AI Agents** - Data Ingestion, Orchestrator, Analysis, Pricing, Forecasting, Recommendation
- **Prophet ML Forecasting** - 30/60/90-day demand predictions with HWCO-specific forecasts
- **Order Management** - Create orders with real-time pricing estimates and success confirmations
- **Real-time Market Signals** - Events, traffic, weather, news integration
- **Competitor Analysis** - Price comparison and competitive intelligence
- **Elasticity Insights** - Demand curve analysis and price optimization
- **Dynamic Pricing Engine** - CONTRACTED/STANDARD/CUSTOM pricing models with priority queuing
- **Dark/Light Mode** - Accessible theme switching
- **Real-time AI Chat** - Streaming responses with markdown formatting and page context awareness
- **Order Tracking** - Query recent orders via natural language chatbot

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Charts:** Recharts
- **State Management:** React Hooks
- **API Client:** Axios
- **WebSocket:** Socket.IO Client

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local with your API URLs

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
# Build the application
npm run build

# Start production server
npm start
```

### Deploy with PM2

```bash
# Build first
npm run build

# Start with PM2
pm2 start npm --name "dynamic-pricing-frontend" -- start

# Save PM2 configuration
pm2 save

# Set up PM2 to start on boot
pm2 startup
```

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx              # Main dashboard page
│   │   ├── layout.tsx            # Root layout
│   │   └── globals.css           # Global styles
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx       # Navigation sidebar
│   │   │   ├── Header.tsx        # Top header with theme toggle
│   │   │   ├── AIPanel.tsx       # Right-side AI assistant panel
│   │   │   └── UploadDrawers.tsx # Bottom upload drawers
│   │   ├── tabs/
│   │   │   ├── OverviewTab.tsx   # Overview dashboard
│   │   │   ├── PricingTab.tsx    # Pricing engine
│   │   │   ├── ForecastingTab.tsx # Prophet ML forecasts
│   │   │   ├── MarketSignalsTab.tsx # Market signals
│   │   │   ├── ElasticityTab.tsx # Elasticity insights
│   │   │   └── CompetitorTab.tsx # Competitor analysis
│   │   └── ui/
│   │       ├── Card.tsx          # Card component
│   │       ├── Button.tsx        # Button component
│   │       ├── Badge.tsx         # Badge component
│   │       ├── Input.tsx         # Input component
│   │       ├── Select.tsx        # Select component
│   │       ├── Tabs.tsx          # Tabs component
│   │       └── Drawer.tsx        # Drawer component
│   ├── hooks/
│   │   ├── useTheme.ts           # Theme management hook
│   │   └── useChatbot.ts         # Chatbot WebSocket hook
│   └── lib/
│       ├── api.ts                # API client
│       └── utils.ts              # Utility functions
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.mjs
└── README.md
```

## Dashboard Tabs

### 1. Overview
- KPI cards (Revenue, Margin, Rides, Customers)
- Revenue & rides trend chart
- Customer distribution pie chart
- Top 5 routes table
- Active surge zones

### 2. Create Order
- Customer information form (name, loyalty status)
- Route planning (origin, destination, location category)
- Segment selection (pricing model, vehicle type)
- Real-time price estimation with HWCO forecasts
- Dynamic pricing breakdown showing unit price and duration
- Success confirmation modal with Order ID and estimated price
- Form validation and error handling
- Priority queue integration (P0/P1/P2)

### 3. Pricing Engine
- Interactive pricing calculator
- Real-time price breakdown
- AI-powered price explanations
- Pricing model comparison (CONTRACTED/STANDARD/CUSTOM)
- Accept/Reject/Simulate actions

### 4. Forecasting
- Prophet ML demand forecasts (30/60/90 days)
- Confidence intervals (80%)
- Trend analysis
- Weekly & daily seasonality charts
- External factors integration (events, traffic, news via n8n)
- AI-generated forecast explanations
- **NOTE:** Currently using mock data - Backend integration plan ready (see `supplemental/FORECAST_TAB_BACKEND_INTEGRATION_PLAN.md`)

### 5. Market Signals
- Live event tracking (concerts, sports, etc.)
- Real-time traffic conditions
- Weather monitoring
- Industry news feed
- Signal impact scoring
- AI recommendations

### 6. Elasticity Insights
- Elasticity by customer segment
- Elasticity heatmap (time × zone)
- Demand curve visualization
- Price optimization analysis
- Sensitivity scenarios
- Optimal pricing strategy

### 7. Competitor Analysis
- Market share overview
- Price comparison charts
- Route-by-route analysis
- Competitor promotions tracking
- Undercut warnings
- AI-powered competitive recommendations
- **100% Lyft Coverage:** All 162 segments have Lyft competitor baseline data

## AI Assistant Panel

The right-side AI panel features:
- **6 Active AI Agents** with status indicators
- **Real-time Chat Interface** with streaming responses
- **Agent Routing**: Orchestrator routes queries to appropriate agents
- **Order Queries**: Ask "What is my order number?" or "Show latest orders"
- **Page Context Awareness**: Agents know which page you're viewing
- **Markdown Support**: Rich formatting with headers, lists, code blocks
- **Conversation History**: Persistent chat history per session
- **Welcome Message**: Helpful introduction with feature list
- **WebSocket Connection** status indicator
- **Responsive Width**: Horizontally resizable panel with localStorage persistence
- **Clear Chat**: One-click history clearing (no confirmation dialog)

## AI Assistant Panel

The right-side AI panel features:
- **6 Active AI Agents** with status indicators
- **Real-time Chat Interface** with streaming responses
- **Agent Routing**: Orchestrator routes queries to appropriate agents
- **Order Queries**: Ask "What is my order number?" or "Show latest orders"
- **Page Context Awareness**: Agents know which page you're viewing
- **Markdown Support**: Rich formatting with headers, lists, code blocks
- **Conversation History**: Persistent chat history per session
- **Welcome Message**: Helpful introduction with feature list
- **WebSocket Connection** status indicator
- **Responsive Width**: Horizontally resizable panel with localStorage persistence
- **Clear Chat**: One-click history clearing (no confirmation dialog)

## Chatbot Features

### Natural Language Queries
The AI chatbot can answer:
- **Order Queries**: "What is my order number?", "Show latest orders"
- **Business Objectives**: "What are our business objectives?", "Show progress"
- **Revenue Analysis**: "How does November revenue compare?", "HWCO vs Lyft"
- **Forecasts**: "What is the demand forecast for next month?"
- **Pricing**: "Calculate price for Urban Gold Premium ride"
- **Recommendations**: "What are the top strategic recommendations?"

### Response Format
- **Consistent Formatting**: Headers (`##`), bullet points (`•`), bold numbers
- **Concise Answers**: Under 150 words with key metrics highlighted
- **Data-Driven**: Always includes actual numbers from database
- **Context-Aware**: Tailors responses based on current page

### Chat History
- **Chronological Order**: Oldest at top, newest at bottom
- **Persistent Storage**: MongoDB-backed history per user/thread
- **Clear Function**: Instant clearing with fresh start
- **Welcome Message**: Helpful introduction for new conversations

## Upload Functionality

Bottom drawer system for uploading:
- Historical rides data (CSV/JSON) for Prophet ML training
- Competitor pricing data (CSV/Excel)
- Event data
- Traffic/demand signals
- Customer loyalty data

## Theme Support

- **Dark Mode** (default) - Optimized for extended use
- **Light Mode** - Accessible alternative
- Persistent theme selection (localStorage)
- Smooth transitions

## Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Note: API endpoints must include trailing slashes for POST requests
# Correct: /api/v1/orders/
# Incorrect: /api/v1/orders
```

## API Integration

All tabs connect to the FastAPI backend:
- `/api/orders/*` - Order management
- `/api/queue/*` - Priority queue
- `/api/upload/*` - File uploads
- `/api/ml/*` - Prophet ML training & forecasting
- `/api/analytics/*` - Analytics & KPIs
- `/api/market/*` - Market signals
- `/api/competitor/*` - Competitor data
- `/api/elasticity/*` - Elasticity analysis
- `/api/pricing/*` - Pricing calculations
- `/ws/chatbot` - WebSocket chatbot

## Development

```bash
# Run development server with hot reload
npm run dev

# Lint code
npm run lint

# Type check
npx tsc --noEmit
```

## License

Proprietary - Dynamic Pricing Solutions

## Support

For issues or questions, contact the development team.

---

## 🆕 Recent Updates (December 5, 2025)

### Forecast Tab Integration (READY)
- **Backend Integration Plan:** Complete documentation with 7 phases
- **API Endpoints Documented:** `/forecast/{horizon}`, `/model-info`, `/seasonality`, `/external-factors`
- **Frontend Changes Needed:** 10 components identified for backend connection
- **Testing Strategy:** Comprehensive validation checklist
- **Mock Data Removal:** Prepared for live data migration
- **Estimated Effort:** 6 hours for complete integration

### Visualization Exports (NEW)
- **Pipeline Flow:** Interactive HTML diagram for PowerPoint export
- **Solution Architecture:** Single-slide architecture diagram
- **Browser Ready:** Direct viewing in any modern browser
- **Export Ready:** Copy to PowerPoint or export to PDF
- **Business Format:** Simplified, concise bullet points for executives

### Order Creation Enhancements
- **Success Modal**: Professional confirmation dialog with Order ID and price
- **No Confirmation Dialog**: Direct modal display without extra click
- **Form Reset**: Automatic reset after successful order creation
- **HWCO Forecasts**: Real-time pricing using forward-looking HWCO data (85% confidence)
- **API Fix**: Corrected endpoint to use trailing slash `/api/v1/orders/`
- **Payload Transformation**: Fixed form field mapping to backend API schema

### Chatbot Improvements
- **Order Queries**: Natural language order lookup ("my order number", "latest order")
- **Markdown Rendering**: Full markdown support with syntax highlighting
- **Page Context**: Agents aware of current page (Overview, Pricing, etc.)
- **Chat History Fix**: Correct chronological order (oldest→newest)
- **Clear Chat**: Simplified one-click clearing without confirmation
- **Welcome Message**: Comprehensive introduction with feature list
- **Response Formatting**: Consistent headers, bullet points, bold metrics
- **Streaming Support**: Token-by-token streaming for faster responses

### UI/UX Enhancements
- **AI Panel Width**: Horizontally resizable (280-800px) with localStorage persistence
- **Welcome Screen**: Helpful introduction for new users with feature list
- **Loading States**: Better feedback during API calls
- **Error Handling**: Improved 422 validation error messages with readable format
- **Responsive Design**: Better mobile/tablet support
- **Order Success Modal**: Beautiful confirmation with order details and OK button

### Bug Fixes
- **Chat History Order**: Fixed reverse order display
- **Reference Error**: Fixed `loadChatHistory` initialization issue
- **API Redirect**: Fixed 307 redirect by adding trailing slash
- **Form Validation**: Enhanced client-side validation
- **Chat Polling**: Removed unnecessary history refresh polling

