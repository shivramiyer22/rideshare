/**
 * PriorityQueueViz Component
 * 
 * Main component for the Priority Queue Visualization.
 * Displays all three priority queues (P0, P1, P2) side by side with real-time updates.
 * 
 * Features:
 * - Auto-refresh every 5 seconds (configurable)
 * - Manual refresh button
 * - Displays statistics for all queues
 * - Responsive layout (3 columns on desktop, stacked on mobile)
 * - Loading states and error handling
 * 
 * Architecture:
 * - Uses QueueStats component for statistics bar
 * - Uses QueueColumn components for each queue (P0, P1, P2)
 * - Fetches data from /api/orders/queue/priority endpoint
 * - Implements polling with useEffect and setInterval
 */

"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  PriorityQueueVizProps,
  QueueData,
  Priority,
  QUEUE_POLL_INTERVAL,
} from "@/types/queue";
import QueueStats from "./QueueStats";
import QueueColumn from "./QueueColumn";
import { fetchPriorityQueue } from "@/lib/api";

/**
 * PriorityQueueViz Component
 * 
 * Step-by-step explanation:
 * 1. Initialize state for queue data, loading, error, and last updated time
 * 2. Create fetch function that calls API and updates state
 * 3. Set up auto-refresh polling using useEffect and setInterval
 * 4. Provide manual refresh button through QueueStats
 * 5. Render statistics bar and three queue columns
 * 6. Clean up interval on unmount to prevent memory leaks
 */
export default function PriorityQueueViz({
  autoRefresh = true,
  refreshInterval = QUEUE_POLL_INTERVAL,
  maxOrdersPerQueue = 50,
}: PriorityQueueVizProps) {
  // ============================================================================
  // STATE MANAGEMENT
  // ============================================================================
  
  // Step 1: Initialize state
  const [queueData, setQueueData] = useState<QueueData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  
  // Use ref to track if component is mounted (prevents state updates after unmount)
  const isMountedRef = useRef<boolean>(true);
  
  // ============================================================================
  // DATA FETCHING
  // ============================================================================
  
  /**
   * Step 2: Fetch queue data from API
   * This function is wrapped in useCallback to prevent unnecessary re-creation
   */
  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Call API client function
      const data = await fetchPriorityQueue();
      
      // Only update state if component is still mounted
      if (isMountedRef.current) {
        setQueueData(data);
        setLastUpdated(new Date());
        setIsLoading(false);
      }
    } catch (err) {
      console.error("Error fetching priority queue:", err);
      
      if (isMountedRef.current) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to fetch priority queue data"
        );
        setIsLoading(false);
      }
    }
  }, []);
  
  /**
   * Manual refresh handler for the refresh button
   */
  const handleManualRefresh = useCallback(() => {
    fetchData();
  }, [fetchData]);
  
  // ============================================================================
  // LIFECYCLE & POLLING
  // ============================================================================
  
  /**
   * Step 3: Set up polling effect
   * - Fetch data immediately on mount
   * - Set up interval for auto-refresh if enabled
   * - Clean up interval on unmount
   */
  useEffect(() => {
    // Mark component as mounted
    isMountedRef.current = true;
    
    // Initial fetch
    fetchData();
    
    // Set up auto-refresh interval if enabled
    let intervalId: NodeJS.Timeout | null = null;
    
    if (autoRefresh && refreshInterval > 0) {
      intervalId = setInterval(() => {
        fetchData();
      }, refreshInterval);
    }
    
    // Cleanup function - runs when component unmounts
    return () => {
      isMountedRef.current = false;
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [autoRefresh, refreshInterval, fetchData]);
  
  // ============================================================================
  // RENDER HELPERS
  // ============================================================================
  
  /**
   * Limit orders per queue to prevent performance issues
   */
  const limitOrders = (orders: any[], limit: number) => {
    return orders.slice(0, limit);
  };
  
  // ============================================================================
  // RENDER
  // ============================================================================
  
  return (
    <div className="w-full">
      {/* Error State - Show error message if fetch failed */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded-lg">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700 font-semibold">
                Error loading priority queue data
              </p>
              <p className="text-xs text-red-600 mt-1">{error}</p>
            </div>
            <div className="ml-auto">
              <button
                onClick={handleManualRefresh}
                className="text-sm text-red-700 hover:text-red-800 font-semibold underline"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Statistics Bar */}
      <QueueStats
        status={
          queueData?.status || {
            P0: 0,
            P1: 0,
            P2: 0,
          }
        }
        lastUpdated={lastUpdated}
        isLoading={isLoading}
        onRefresh={handleManualRefresh}
      />
      
      {/* Queue Columns Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* P0 Queue Column - CONTRACTED (FIFO) */}
        <QueueColumn
          queueType={Priority.P0}
          orders={
            queueData?.P0 ? limitOrders(queueData.P0, maxOrdersPerQueue) : []
          }
          count={queueData?.status.P0 || 0}
          isLoading={isLoading}
        />
        
        {/* P1 Queue Column - STANDARD (Revenue Score DESC) */}
        <QueueColumn
          queueType={Priority.P1}
          orders={
            queueData?.P1 ? limitOrders(queueData.P1, maxOrdersPerQueue) : []
          }
          count={queueData?.status.P1 || 0}
          isLoading={isLoading}
        />
        
        {/* P2 Queue Column - CUSTOM (Revenue Score DESC) */}
        <QueueColumn
          queueType={Priority.P2}
          orders={
            queueData?.P2 ? limitOrders(queueData.P2, maxOrdersPerQueue) : []
          }
          count={queueData?.status.P2 || 0}
          isLoading={isLoading}
        />
      </div>
      
      {/* Auto-refresh indicator */}
      {autoRefresh && (
        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500">
            Auto-refreshing every {refreshInterval / 1000} seconds
          </p>
        </div>
      )}
    </div>
  );
}

