/**
 * QueueColumn Component
 * 
 * Displays a single queue column (P0, P1, or P2) with all its orders.
 * Handles empty states, loading states, and scrolling for large queues.
 * 
 * Features:
 * - Color-coded header based on queue type
 * - Shows queue metadata (name, description, sorting method)
 * - Displays order count
 * - Renders list of OrderCard components
 * - Empty state when no orders in queue
 */

import React from "react";
import { QueueColumnProps, QUEUE_METADATA } from "@/types/queue";
import OrderCard from "./OrderCard";

/**
 * QueueColumn Component
 * 
 * Step-by-step explanation:
 * 1. Receives queue type, orders array, count, and loading state as props
 * 2. Gets queue metadata (colors, labels) from QUEUE_METADATA
 * 3. Renders a column with header containing queue info
 * 4. Displays loading skeleton when fetching data
 * 5. Shows empty state if no orders in queue
 * 6. Renders OrderCard for each order in the queue
 */
export default function QueueColumn({
  queueType,
  orders,
  count,
  isLoading = false,
}: QueueColumnProps) {
  // Step 1: Get queue metadata for styling and labels
  const metadata = QUEUE_METADATA[queueType];
  
  return (
    <div className="flex flex-col h-full">
      {/* Queue Header - Shows queue name, emoji, and order count */}
      <div
        className={`
          ${metadata.color.bg}
          border-2
          ${metadata.color.border}
          rounded-t-lg
          p-4
          sticky
          top-0
          z-10
        `}
      >
        {/* Queue Title Row */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{metadata.emoji}</span>
            <h3 className={`text-lg font-bold ${metadata.color.text}`}>
              {metadata.label}
            </h3>
          </div>
          {/* Order Count Badge */}
          <span
            className={`
              ${metadata.color.badge}
              px-3
              py-1
              rounded-full
              text-sm
              font-bold
            `}
          >
            {count} {count === 1 ? "order" : "orders"}
          </span>
        </div>
        
        {/* Queue Description */}
        <p className="text-xs text-gray-600 mb-1">
          {metadata.description}
        </p>
        
        {/* Sort Method */}
        <p className="text-xs text-gray-500 italic">
          {metadata.sortMethod}
        </p>
      </div>
      
      {/* Queue Content - Scrollable area with orders */}
      <div
        className={`
          ${metadata.color.bg}
          border-x-2
          border-b-2
          ${metadata.color.border}
          rounded-b-lg
          p-4
          flex-1
          overflow-y-auto
          min-h-[400px]
          max-h-[600px]
        `}
      >
        {/* Loading State - Show skeleton cards while fetching */}
        {isLoading && orders.length === 0 && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="bg-white border border-gray-200 rounded-lg p-4 animate-pulse"
              >
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
              </div>
            ))}
          </div>
        )}
        
        {/* Empty State - Show when queue has no orders */}
        {!isLoading && orders.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center py-12">
            <div className="text-6xl mb-4 opacity-50">{metadata.emoji}</div>
            <p className="text-gray-500 font-semibold mb-1">
              No orders in {metadata.label}
            </p>
            <p className="text-gray-400 text-sm">
              Orders will appear here as they arrive
            </p>
          </div>
        )}
        
        {/* Orders List - Render all orders in this queue */}
        {orders.length > 0 && (
          <div>
            {orders.map((order, index) => (
              <OrderCard
                key={`${order.order_id}-${index}`}
                order={order}
                queueType={queueType}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

