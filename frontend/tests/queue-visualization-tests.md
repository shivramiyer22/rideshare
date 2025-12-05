# Priority Queue Visualization - Testing Guide

**Feature:** Priority Queue Visualization  
**Date:** December 3, 2025  
**Status:** Ready for Testing

---

## 🎯 Test Overview

This document provides comprehensive test cases for the Priority Queue Visualization feature.

### Components to Test
1. **OrderCard** - Individual order display
2. **QueueColumn** - Single queue column (P0/P1/P2)
3. **QueueStats** - Statistics bar with refresh button
4. **PriorityQueueViz** - Main visualization component
5. **QueueTab** - Tab integration

---

## ✅ Unit Test Cases

### OrderCard Component

#### Test 1: Renders with Valid Order Data
```
Given: A valid order object with all fields
When: OrderCard is rendered
Then: All order details should display correctly
  - Order ID is visible
  - Customer name is visible
  - Route is formatted as "Pickup → Dropoff"
  - Price is formatted as currency
  - Timestamp is shown as relative time (e.g., "2m ago")
```

#### Test 2: Color Coding by Queue Type
```
Given: Orders in different queues (P0, P1, P2)
When: OrderCard is rendered for each
Then: Border color should match queue type
  - P0: Red border
  - P1: Amber border
  - P2: Green border
```

#### Test 3: Revenue Score Display
```
Given: An order in P1 or P2 queue
When: OrderCard is rendered
Then: Revenue score should be visible
  - Score is formatted to 1 decimal place
  
Given: An order in P0 queue
When: OrderCard is rendered
Then: "FIFO" badge should show instead of revenue score
```

#### Test 4: Handles Missing Data
```
Given: Order with missing optional fields (price, customer name)
When: OrderCard is rendered
Then: Component should not crash
  - Missing price shows "—"
  - Missing customer shows "Unknown Customer"
  - Missing location shows "Unknown"
```

---

### QueueColumn Component

#### Test 5: Renders Multiple Orders
```
Given: A queue with 5 orders
When: QueueColumn is rendered
Then: All 5 OrderCard components should render
  - Orders appear in correct order
  - Each order is distinct
```

#### Test 6: Empty Queue State
```
Given: A queue with 0 orders
When: QueueColumn is rendered
Then: Empty state should display
  - Shows emoji indicator
  - Shows "No orders in [Queue]" message
  - Shows helpful text
```

#### Test 7: Loading State
```
Given: isLoading = true and orders = []
When: QueueColumn is rendered
Then: Loading skeleton should display
  - Shows 3 skeleton cards
  - Cards have animation
```

#### Test 8: Queue Header Information
```
Given: Any queue type (P0/P1/P2)
When: QueueColumn is rendered
Then: Header should show
  - Queue emoji
  - Queue label (e.g., "P0 Queue")
  - Order count badge
  - Queue description
  - Sort method explanation
```

---

### QueueStats Component

#### Test 9: Display Statistics
```
Given: Queue status with P0=5, P1=12, P2=8
When: QueueStats is rendered
Then: Should display
  - Total: 25 orders
  - P0: 5 orders (red theme)
  - P1: 12 orders (amber theme)
  - P2: 8 orders (green theme)
```

#### Test 10: Last Updated Timestamp
```
Given: lastUpdated = new Date("2025-12-03T10:45:00")
When: QueueStats is rendered
Then: "Last Updated" should show formatted date/time
  - Format: "Dec 3, 2025 10:45:00 AM"
```

#### Test 11: Refresh Button
```
Given: QueueStats component
When: User clicks "Refresh Now" button
Then: onRefresh callback should be called once
```

#### Test 12: Loading State for Refresh
```
Given: isLoading = true
When: QueueStats is rendered
Then: Refresh button should
  - Be disabled
  - Show "Refreshing..." text
  - Show spinning icon
```

---

### PriorityQueueViz Component

#### Test 13: Initial Data Fetch
```
Given: Component just mounted
When: Component renders
Then: Should fetch data from API
  - Calls fetchPriorityQueue()
  - Shows loading state initially
  - Updates with data when received
```

#### Test 14: Auto-refresh Polling
```
Given: autoRefresh=true, refreshInterval=5000
When: Component is mounted
Then: Should fetch data every 5 seconds
  - Sets up interval
  - Calls API repeatedly
  - Updates display with new data
```

#### Test 15: Manual Refresh
```
Given: Component is rendered with data
When: User clicks "Refresh Now" button
Then: Should immediately fetch new data
  - Shows loading state
  - Fetches from API
  - Updates display
```

#### Test 16: Error Handling
```
Given: API call fails
When: fetchPriorityQueue() throws error
Then: Should show error message
  - Red error box displays
  - Error message is shown
  - "Try Again" button is available
```

#### Test 17: Cleanup on Unmount
```
Given: Component with active polling interval
When: Component unmounts
Then: Should clean up
  - Clears interval
  - Sets isMountedRef to false
  - Prevents memory leaks
```

---

## 🔄 Integration Test Cases

### Test 18: End-to-End Order Display
```
Given: Backend has orders in all 3 queues
When: Page loads
Then: Should display all orders correctly
  - P0 orders in red column
  - P1 orders in amber column
  - P2 orders in green column
  - Correct counts in statistics
```

### Test 19: Real-time Order Addition
```
Given: Queue visualization is displayed
When: New order is created via API
And: Next auto-refresh occurs
Then: New order should appear in correct queue
  - Statistics update to reflect new count
  - Order appears in appropriate column
```

### Test 20: Order Processing Simulation
```
Given: 3 orders in P0 queue
When: Backend processes one order (removes from queue)
And: Next auto-refresh occurs
Then: Queue should update
  - P0 count decreases by 1
  - Processed order no longer displays
```

### Test 21: API Endpoint Integration
```
Given: Application is running
When: GET /api/orders/queue/priority is called
Then: Should return correct structure
  - P0: Array of orders
  - P1: Array of orders
  - P2: Array of orders
  - status: {P0: number, P1: number, P2: number}
```

---

## 📱 Responsive Design Test Cases

### Test 22: Desktop Layout (≥1024px)
```
Given: Screen width >= 1024px
When: Page is rendered
Then: Should show 3 columns side-by-side
  - P0, P1, P2 in a row
  - All columns equally sized
  - No horizontal scroll
```

### Test 23: Tablet Layout (768px - 1023px)
```
Given: Screen width between 768px and 1023px
When: Page is rendered
Then: Should show 2 columns per row
  - 2 queues on first row
  - 1 queue on second row
```

### Test 24: Mobile Layout (<768px)
```
Given: Screen width < 768px
When: Page is rendered
Then: Should show 1 column (stacked vertically)
  - P0 on top
  - P1 in middle
  - P2 on bottom
```

---

## 🎨 Visual/UI Test Cases

### Test 25: Color Consistency
```
Given: All three queue columns are displayed
When: Page is viewed
Then: Colors should match design spec
  - P0: Red (#dc2626)
  - P1: Amber (#f59e0b)
  - P2: Green (#16a34a)
```

### Test 26: Animations
```
Given: Orders are displayed
When: User hovers over an order card
Then: Card should
  - Scale slightly (1.01x)
  - Increase shadow
  - Transition smoothly (200ms)
```

### Test 27: Loading Skeletons
```
Given: Data is being fetched
When: Loading state is active
Then: Skeleton cards should
  - Show pulsing animation
  - Have gray placeholder bars
  - Match card layout
```

---

## 🔍 Performance Test Cases

### Test 28: Large Queue Performance
```
Given: Queue with 100+ orders
When: Component renders
Then: Should render smoothly
  - Initial render < 100ms
  - Scrolling is smooth (60fps)
  - No lag or freezing
```

### Test 29: Memory Leak Prevention
```
Given: Component with auto-refresh enabled
When: Component mounts, updates 10 times, then unmounts
Then: Should not leak memory
  - Intervals are cleaned up
  - State updates don't occur after unmount
  - Memory usage remains stable
```

### Test 30: Re-render Optimization
```
Given: Component receiving same data multiple times
When: Auto-refresh fetches identical data
Then: Should minimize re-renders
  - Only necessary components update
  - No full page re-render
```

---

## 🧪 Manual Testing Checklist

### Pre-Testing Setup
- [ ] Backend is running (`cd backend && ./start.sh`)
- [ ] Frontend is running (`cd frontend && npm run dev`)
- [ ] Redis is running (`redis-cli ping` returns PONG)
- [ ] Create test orders via OrderCreationForm

### Visual Tests
- [ ] All three queue columns display
- [ ] Colors match design (red, amber, green)
- [ ] Order cards are readable and well-formatted
- [ ] Statistics bar shows correct counts
- [ ] Empty states display when queues are empty
- [ ] Loading states appear during data fetch

### Functional Tests
- [ ] Page loads without errors
- [ ] Initial data fetches successfully
- [ ] Auto-refresh updates every 5 seconds
- [ ] Manual refresh button works
- [ ] Creating new order updates queue on next refresh
- [ ] Order details are accurate (ID, customer, route, price)
- [ ] Revenue scores display for P1/P2 orders
- [ ] FIFO badge displays for P0 orders

### Responsive Tests
- [ ] Desktop layout (3 columns)
- [ ] Tablet layout (2 columns)
- [ ] Mobile layout (1 column stacked)
- [ ] Scrolling works on all screen sizes
- [ ] Touch interactions work on mobile

### Error Handling Tests
- [ ] Stop backend → Error message displays
- [ ] Click "Try Again" → Retries fetch
- [ ] Network error → Graceful error display

### Performance Tests
- [ ] Smooth animations (hover, transitions)
- [ ] No console errors or warnings
- [ ] Fast initial load (<1 second)
- [ ] Smooth scrolling in large queues

---

## 🐛 Known Issues / Edge Cases

### Edge Case 1: Empty Order Data
```
Scenario: Order missing pickup_location or dropoff_location
Expected: Display "Unknown" instead of crashing
Status: ✅ Handled
```

### Edge Case 2: Invalid Timestamps
```
Scenario: created_at is malformed or missing
Expected: Display "Unknown" for relative time
Status: ✅ Handled
```

### Edge Case 3: Very Long Customer Names
```
Scenario: Customer name > 50 characters
Expected: Text wraps or truncates gracefully
Status: ⚠️ Monitor for overflow
```

### Edge Case 4: Negative Revenue Scores
```
Scenario: Revenue score is negative (shouldn't happen but...)
Expected: Display as-is with proper formatting
Status: ✅ Handled
```

---

## 📊 Test Results Template

| Test ID | Test Name | Status | Notes |
|---------|-----------|--------|-------|
| Test 1  | Renders with Valid Order Data | ⬜ | |
| Test 2  | Color Coding by Queue Type | ⬜ | |
| Test 3  | Revenue Score Display | ⬜ | |
| ... | ... | ... | ... |

**Status Key:**
- ✅ Pass
- ❌ Fail
- ⚠️ Partial/Warning
- ⬜ Not Tested

---

## 🚀 Testing Execution Steps

### Step 1: Run Backend
```bash
cd /Users/ishitasharma/Documents/GitHub/rideshare/rideshare/backend
./start.sh
```

### Step 2: Verify Redis
```bash
redis-cli ping
# Should return: PONG
```

### Step 3: Run Frontend
```bash
cd /Users/ishitasharma/Documents/GitHub/rideshare/rideshare/frontend
npm run dev
```

### Step 4: Create Test Orders
1. Navigate to "Orders" tab
2. Create 2-3 CONTRACTED orders
3. Create 3-4 STANDARD orders
4. Create 2-3 CUSTOM orders

### Step 5: Navigate to Queue Tab
1. Click "Queue" in sidebar/tabs
2. Verify all orders appear
3. Wait for auto-refresh (5 seconds)
4. Click manual refresh button

### Step 6: Test Edge Cases
1. Stop backend → Verify error handling
2. Create order with minimal data → Verify graceful handling
3. Test on mobile device → Verify responsive layout

---

## 📝 Test Report Template

```
Test Execution Report
Date: [DATE]
Tester: [NAME]
Environment: [Development/Staging/Production]

Total Tests: 30
Passed: __
Failed: __
Skipped: __

Critical Issues: __
Non-Critical Issues: __

Overall Status: [PASS/FAIL]

Notes:
- 
- 
- 
```

---

**Testing Complete! Report any issues to the development team.**

