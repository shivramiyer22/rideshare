/**
 * OrderCard Component
 * 
 * Displays a single order in the priority queue visualization.
 * Shows order details including ID, customer, route, price, and revenue score.
 * 
 * Design:
 * - Color-coded by queue type (P0=red, P1=amber, P2=green)
 * - Compact card layout with all essential information
 * - Responsive design for mobile and desktop
 */

import React from "react";
import { OrderCardProps, QUEUE_METADATA, Priority } from "@/types/queue";

/**
 * Format a timestamp as relative time (e.g., "2m ago", "5h ago")
 */
function formatRelativeTime(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  } catch (error) {
    return "Unknown";
  }
}

/**
 * Format currency
 */
function formatCurrency(amount: number | undefined): string {
  if (amount === undefined || amount === null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(amount);
}

/**
 * Extract location string from Location object or string
 */
function formatLocation(location: any): string {
  if (!location) return "Unknown";
  
  if (typeof location === "string") return location;
  
  if (location.address) return location.address;
  if (location.city && location.state) return `${location.city}, ${location.state}`;
  if (location.city) return location.city;
  
  return "Unknown";
}

/**
 * OrderCard Component
 * 
 * Step-by-step explanation:
 * 1. Receives order data and queue type as props
 * 2. Gets color theme from QUEUE_METADATA based on queue type
 * 3. Extracts pickup/dropoff locations from order data
 * 4. Formats timestamps, prices, and other display data
 * 5. Renders a card with border color matching queue type
 */
export default function OrderCard({ order, queueType }: OrderCardProps) {
  // Step 1: Get color configuration for this queue type
  const metadata = QUEUE_METADATA[queueType];
  
  // Step 2: Extract location data from order
  // The backend may provide location in order_data or directly on the order
  const pickupLocation = order.order_data?.pickup_location || order.pickup_location;
  const dropoffLocation = order.order_data?.dropoff_location || order.dropoff_location;
  
  // Step 3: Format pickup and dropoff for display
  const pickupText = formatLocation(pickupLocation);
  const dropoffText = formatLocation(dropoffLocation);
  const routeDisplay = order.route || `${pickupText} → ${dropoffText}`;
  
  // Step 4: Get customer name (from order_data or user_id)
  const customerName = order.customer_name || 
                       order.order_data?.user_id || 
                       order.user_id || 
                       "Unknown Customer";
  
  // Step 5: Format timestamp
  const timeAgo = formatRelativeTime(order.created_at);
  
  return (
    <div
      className={`
        ${metadata.color.bg} 
        border-l-4 
        ${metadata.color.border}
        rounded-lg 
        p-4 
        mb-3
        shadow-sm
        hover:shadow-md
        transition-all
        duration-200
        hover:scale-[1.01]
      `}
    >
      {/* Order ID and Time - Header Row */}
      <div className="flex justify-between items-start mb-2">
        <div className="flex-1">
          <p className={`text-sm font-mono font-bold ${metadata.color.text}`}>
            {order.order_id}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-500">{timeAgo}</p>
        </div>
      </div>
      
      {/* Customer Name */}
      <div className="mb-2">
        <p className="text-sm font-semibold text-gray-700">
          {customerName}
        </p>
      </div>
      
      {/* Route Display */}
      <div className="mb-3">
        <p className="text-xs text-gray-600 break-words">
          {routeDisplay}
        </p>
      </div>
      
      {/* Price and Revenue Score - Footer Row */}
      <div className="flex justify-between items-center pt-2 border-t border-gray-200">
        {/* Price */}
        <div>
          <p className="text-xs text-gray-500">Price</p>
          <p className="text-sm font-bold text-gray-800">
            {formatCurrency(order.price || order.order_data?.price)}
          </p>
        </div>
        
        {/* Revenue Score (only show for P1 and P2, not P0 which is FIFO) */}
        {queueType !== Priority.P0 && (
          <div className="text-right">
            <p className="text-xs text-gray-500">Revenue Score</p>
            <p className={`text-sm font-bold ${metadata.color.text}`}>
              {order.revenue_score?.toFixed(1) || "—"}
            </p>
          </div>
        )}
        
        {/* For P0, show "FIFO" badge instead of revenue score */}
        {queueType === Priority.P0 && (
          <div className="text-right">
            <span className={`text-xs px-2 py-1 rounded ${metadata.color.badge} font-semibold`}>
              FIFO
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

