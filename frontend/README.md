# Dynamic Pricing Solutions - Frontend

AI-Powered Dynamic Pricing Intelligence Platform

## Features

- **6 AI Agents** - Data Ingestion, Orchestrator, Analysis, Pricing, Forecasting, Recommendation
- **Prophet ML Forecasting** - 30/60/90-day demand predictions
- **Real-time Market Signals** - Events, traffic, weather, news integration
- **Competitor Analysis** - Price comparison and competitive intelligence
- **Elasticity Insights** - Demand curve analysis and price optimization
- **Dynamic Pricing Engine** - CONTRACTED/STANDARD/CUSTOM pricing models
- **Dark/Light Mode** - Accessible theme switching
- **Real-time AI Chat** - WebSocket-powered chatbot interface

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

### 2. Pricing Engine
- Interactive pricing calculator
- Real-time price breakdown
- AI-powered price explanations
- Pricing model comparison (CONTRACTED/STANDARD/CUSTOM)
- Accept/Reject/Simulate actions

### 3. Forecasting
- Prophet ML demand forecasts (30/60/90 days)
- Confidence intervals (80%)
- Trend analysis
- Weekly & daily seasonality charts
- External factors integration
- AI-generated forecast explanations

### 4. Market Signals
- Live event tracking (concerts, sports, etc.)
- Real-time traffic conditions
- Weather monitoring
- Industry news feed
- Signal impact scoring
- AI recommendations

### 5. Elasticity Insights
- Elasticity by customer segment
- Elasticity heatmap (time × zone)
- Demand curve visualization
- Price optimization analysis
- Sensitivity scenarios
- Optimal pricing strategy

### 6. Competitor Insights
- Market share overview
- Price comparison charts
- Route-by-route analysis
- Competitor promotions tracking
- Undercut warnings
- AI-powered competitive recommendations

## AI Assistant Panel

The right-side AI panel features:
- 6 active AI agents with status indicators
- Real-time chat interface
- Agent routing (Orchestrator routes queries to appropriate agents)
- Conversation history
- WebSocket connection status

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

