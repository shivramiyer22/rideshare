# Priority Queue Visualization - Build Plan

**Created:** December 3, 2025  
**Scope:** Frontend-only component  
**Backend Impact:** Minimal (using existing endpoints)

---

## 🎯 Objective

Create a real-time Priority Queue Visualization component that displays P0, P1, and P2 queues with:
- Visual distinction between queue types (colors, icons)
- Real-time updates every 5 seconds
- Order details display (customer, route, price, revenue_score)
- Queue statistics (count per queue)
- Responsive design for mobile and desktop
- Smooth animations and transitions

---

## 📋 Requirements

### Functional Requirements
1. **Display 3 Queue Columns:**
   - **P0 (CONTRACTED):** Red theme, FIFO order, highest priority
   - **P1 (STANDARD):** Yellow/Amber theme, sorted by revenue_score DESC
   - **P2 (CUSTOM):** Green theme, sorted by revenue_score DESC

2. **Real-time Updates:**
   - Poll `GET /api/orders/queue/priority` every 5 seconds
   - Smooth transitions when orders are added/removed
   - Loading states during data fetch

3. **Order Information Display:**
   - Order ID
   - Customer name (from user_id)
   - Route (pickup → dropoff)
   - Price (if available)
   - Revenue score (for P1/P2)
   - Created timestamp

4. **Queue Statistics:**
   - Total count per queue
   - Visual indicators when queues are empty

### Non-Functional Requirements
1. **Performance:**
   - Minimal re-renders using React best practices
   - Efficient data fetching with caching
   - Smooth animations (60fps target)

2. **Accessibility:**
   - Proper ARIA labels
   - Keyboard navigation support
   - Screen reader friendly

3. **Responsive Design:**
   - Mobile: Stacked vertically
   - Tablet: 2 columns
   - Desktop: 3 columns side-by-side

---

## 🏗️ Architecture

### Component Structure
```
PriorityQueueViz.tsx (Main Component)
├── QueueColumn (Sub-component for each P0/P1/P2)
│   └── OrderCard (Individual order display)
└── QueueStats (Statistics bar)
```

### Data Flow
```
Backend API (/api/orders/queue/priority)
    ↓
API Client (lib/api.ts)
    ↓
React Component (PriorityQueueViz.tsx)
    ↓
UI Rendering (3 queue columns)
```

### State Management
- Local component state using `useState`
- Polling using `useEffect` with `setInterval`
- Optional: React Query for advanced caching (if already in project)

---

## 🎨 Design Specifications

### Color Scheme
| Queue | Theme Color | Background | Border | Text |
|-------|------------|------------|--------|------|
| **P0** | Red | `bg-red-50` | `border-red-500` | `text-red-900` |
| **P1** | Amber | `bg-amber-50` | `border-amber-500` | `text-amber-900` |
| **P2** | Green | `bg-green-50` | `border-green-500` | `text-green-900` |

### Layout
```
┌─────────────────────────────────────────────────────────┐
│              PRIORITY QUEUE VISUALIZATION               │
│  Last Updated: Dec 3, 2025 10:45:23 AM   [Refresh Now] │
├─────────────────────────────────────────────────────────┤
│   P0: 5 orders  │  P1: 12 orders  │  P2: 8 orders     │
├─────────────────┼─────────────────┼───────────────────┤
│  🔴 P0 Queue    │  🟡 P1 Queue    │  🟢 P2 Queue      │
│  CONTRACTED     │  STANDARD       │  CUSTOM           │
│  (FIFO)         │  (Revenue ↓)    │  (Revenue ↓)      │
│                 │                 │                   │
│ ┌─────────────┐ │ ┌─────────────┐ │ ┌─────────────┐ │
│ │ ORD-ABC123  │ │ │ ORD-DEF456  │ │ │ ORD-GHI789  │ │
│ │ John Doe    │ │ │ Jane Smith  │ │ │ Bob Jones   │ │
│ │ A → B       │ │ │ C → D       │ │ │ E → F       │ │
│ │ $52.00      │ │ │ $87.50      │ │ │ $45.00      │ │
│ │             │ │ │ Score: 125  │ │ │ Score: 68   │ │
│ │ 2m ago      │ │ │ 5m ago      │ │ │ 1m ago      │ │
│ └─────────────┘ │ └─────────────┘ │ └─────────────┘ │
│                 │                 │                   │
│ ┌─────────────┐ │ ┌─────────────┐ │ ┌─────────────┐ │
│ │ ORD-JKL012  │ │ │ ORD-MNO345  │ │ │ ORD-PQR678  │ │
│ │ ...         │ │ │ ...         │ │ │ ...         │ │
│ └─────────────┘ │ └─────────────┘ │ └─────────────┘ │
└─────────────────┴─────────────────┴───────────────────┘
```

---

## 🛠️ Implementation Plan

### Step 1: Create API Client Function
- **File:** `frontend/src/lib/api.ts`
- **Function:** `fetchPriorityQueue()`
- **Purpose:** Fetch queue data from backend

### Step 2: Create Order Card Component
- **File:** `frontend/src/components/queue/OrderCard.tsx`
- **Props:** `order, queueType`
- **Purpose:** Display individual order with proper styling

### Step 3: Create Queue Column Component
- **File:** `frontend/src/components/queue/QueueColumn.tsx`
- **Props:** `queueType, orders, count`
- **Purpose:** Display single queue column with all orders

### Step 4: Create Main Visualization Component
- **File:** `frontend/src/components/queue/PriorityQueueViz.tsx`
- **Purpose:** Main component orchestrating all sub-components

### Step 5: Create Queue Tab Component
- **File:** `frontend/src/components/tabs/QueueTab.tsx`
- **Purpose:** Tab wrapper that integrates with existing app structure

### Step 6: Integrate into Main Application
- **File:** `frontend/src/app/page.tsx`
- **Purpose:** Add queue visualization to dashboard tabs

---

## 📂 File Structure

```
frontend/src/
├── components/
│   ├── queue/                        # NEW FOLDER
│   │   ├── OrderCard.tsx            # Individual order display
│   │   ├── QueueColumn.tsx          # Single queue column
│   │   ├── QueueStats.tsx           # Statistics bar
│   │   └── PriorityQueueViz.tsx     # Main component
│   └── tabs/
│       └── QueueTab.tsx             # Tab integration (UPDATE)
├── lib/
│   └── api.ts                       # Add fetchPriorityQueue() function
└── types/
    └── queue.ts                     # NEW: Type definitions
```

---

## 🧪 Testing Plan

### Unit Tests
1. **OrderCard Component:**
   - Renders with valid order data
   - Displays correct colors for each queue type
   - Formats timestamps correctly
   - Handles missing data gracefully

2. **QueueColumn Component:**
   - Renders multiple orders
   - Handles empty queue state
   - Sorts orders correctly (P1/P2)
   - Maintains FIFO order (P0)

3. **PriorityQueueViz Component:**
   - Fetches data on mount
   - Polls every 5 seconds
   - Handles API errors gracefully
   - Shows loading state

### Integration Tests
1. **API Integration:**
   - Successfully fetches from `/api/orders/queue/priority`
   - Handles network errors
   - Parses response correctly

2. **Real-time Updates:**
   - Updates display when new orders arrive
   - Removes orders when they're processed
   - Maintains scroll position during updates

### Manual Testing Checklist
- [ ] All 3 queues display correctly
- [ ] Colors match design specifications
- [ ] Real-time polling works (every 5 seconds)
- [ ] Empty queue states display properly
- [ ] Order details are accurate
- [ ] Mobile responsive layout works
- [ ] Smooth animations on updates
- [ ] No console errors or warnings

---

## 📊 Success Criteria

1. **Visual Quality:**
   - ✅ Clear visual distinction between P0/P1/P2
   - ✅ Professional, modern design
   - ✅ Smooth animations and transitions

2. **Functionality:**
   - ✅ Real-time updates every 5 seconds
   - ✅ Accurate order information display
   - ✅ Proper sorting (FIFO for P0, revenue_score DESC for P1/P2)

3. **Performance:**
   - ✅ No memory leaks from polling
   - ✅ Smooth 60fps animations
   - ✅ Fast initial render (<100ms)

4. **User Experience:**
   - ✅ Easy to understand at a glance
   - ✅ Mobile-friendly responsive design
   - ✅ Accessible to screen readers

---

## 🚀 Deployment

### No Backend Changes Required
- Using existing endpoint: `GET /api/orders/queue/priority`
- No database schema changes
- No API modifications needed

### Frontend Only
1. Add new components to `frontend/src/components/queue/`
2. Update `lib/api.ts` with new fetch function
3. Integrate into existing tab structure
4. Test locally
5. Build and deploy frontend

---

## 📝 Notes

- **Minimal Backend Impact:** Uses existing endpoint, no backend changes needed
- **Reusable Components:** OrderCard and QueueColumn can be reused elsewhere
- **Extensible Design:** Easy to add filters, search, or export features later
- **Performance Optimized:** Uses React best practices to minimize re-renders

---

## ⏱️ Estimated Timeline

| Task | Time | Status |
|------|------|--------|
| Create type definitions | 15 min | Pending |
| Build OrderCard component | 30 min | Pending |
| Build QueueColumn component | 30 min | Pending |
| Build QueueStats component | 20 min | Pending |
| Build PriorityQueueViz component | 45 min | Pending |
| Add API client function | 15 min | Pending |
| Create/update QueueTab | 20 min | Pending |
| Integration & testing | 60 min | Pending |
| Documentation | 20 min | Pending |
| **TOTAL** | **~4 hours** | **Pending** |

---

**Ready for Implementation** ✅

This build plan provides a complete roadmap for implementing the Priority Queue Visualization with minimal backend impact.

