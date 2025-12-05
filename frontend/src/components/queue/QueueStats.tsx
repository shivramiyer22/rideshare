/**
 * QueueStats Component
 * 
 * Displays statistics and controls for the priority queue visualization.
 * Shows total order counts, last update time, and refresh button.
 * 
 * Features:
 * - Total orders across all queues
 * - Breakdown by queue (P0, P1, P2)
 * - Last updated timestamp
 * - Manual refresh button
 * - Loading indicator
 */

import React from "react";
import { QueueStatsProps, QUEUE_METADATA, Priority } from "@/types/queue";
import { RefreshCw } from "lucide-react";

/**
 * Format date as human-readable string
 */
function formatDateTime(date: Date | null): string {
  if (!date) return "Never";
  
  try {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }).format(date);
  } catch (error) {
    return "Unknown";
  }
}

/**
 * QueueStats Component
 * 
 * Step-by-step explanation:
 * 1. Receives queue status, last updated time, loading state, and refresh callback
 * 2. Calculates total orders across all queues
 * 3. Displays statistics bar with counts and controls
 * 4. Provides manual refresh button that calls onRefresh callback
 */
export default function QueueStats({
  status,
  lastUpdated,
  isLoading,
  onRefresh,
}: QueueStatsProps) {
  // Step 1: Calculate total orders across all queues
  const totalOrders = (status.P0 || 0) + (status.P1 || 0) + (status.P2 || 0);
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4 mb-6">
      {/* Title Row */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-800">
          Priority Queue Visualization
        </h2>
        
        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className={`
            flex
            items-center
            gap-2
            px-4
            py-2
            rounded-lg
            font-semibold
            text-sm
            transition-all
            ${
              isLoading
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : "bg-blue-500 text-white hover:bg-blue-600 active:scale-95"
            }
          `}
          aria-label="Refresh queue data"
        >
          <RefreshCw
            size={16}
            className={isLoading ? "animate-spin" : ""}
          />
          {isLoading ? "Refreshing..." : "Refresh Now"}
        </button>
      </div>
      
      {/* Statistics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Orders */}
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-lg p-4">
          <p className="text-xs text-purple-600 font-semibold mb-1">
            TOTAL ORDERS
          </p>
          <p className="text-3xl font-bold text-purple-900">{totalOrders}</p>
        </div>
        
        {/* P0 Count */}
        <div
          className={`
            ${QUEUE_METADATA[Priority.P0].color.bg}
            border
            ${QUEUE_METADATA[Priority.P0].color.border}
            rounded-lg
            p-4
          `}
        >
          <p className="text-xs text-red-600 font-semibold mb-1 flex items-center gap-1">
            <span>{QUEUE_METADATA[Priority.P0].emoji}</span>
            P0 - CONTRACTED
          </p>
          <p className="text-3xl font-bold text-red-900">{status.P0 || 0}</p>
        </div>
        
        {/* P1 Count */}
        <div
          className={`
            ${QUEUE_METADATA[Priority.P1].color.bg}
            border
            ${QUEUE_METADATA[Priority.P1].color.border}
            rounded-lg
            p-4
          `}
        >
          <p className="text-xs text-amber-600 font-semibold mb-1 flex items-center gap-1">
            <span>{QUEUE_METADATA[Priority.P1].emoji}</span>
            P1 - STANDARD
          </p>
          <p className="text-3xl font-bold text-amber-900">{status.P1 || 0}</p>
        </div>
        
        {/* P2 Count */}
        <div
          className={`
            ${QUEUE_METADATA[Priority.P2].color.bg}
            border
            ${QUEUE_METADATA[Priority.P2].color.border}
            rounded-lg
            p-4
          `}
        >
          <p className="text-xs text-green-600 font-semibold mb-1 flex items-center gap-1">
            <span>{QUEUE_METADATA[Priority.P2].emoji}</span>
            P2 - CUSTOM
          </p>
          <p className="text-3xl font-bold text-green-900">{status.P2 || 0}</p>
        </div>
      </div>
      
      {/* Last Updated Timestamp */}
      <div className="mt-4 text-center">
        <p className="text-xs text-gray-500">
          Last Updated:{" "}
          <span className="font-semibold text-gray-700">
            {formatDateTime(lastUpdated)}
          </span>
        </p>
      </div>
    </div>
  );
}

