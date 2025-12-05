/**
 * PriorityQueueVizMock Component - DEMO VERSION
 * 
 * This is a demo version that uses MOCK DATA instead of the real API.
 * Perfect for testing the visualization without backend/MongoDB!
 * 
 * Features:
 * - Uses mock data from mockQueueData.ts
 * - Simulated auto-refresh
 * - Button to add random orders
 * - Everything works without backend!
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
import { 
  fetchMockPriorityQueue, 
  generateRandomOrder,
  mockQueueData 
} from "@/lib/mockQueueData";

/**
 * PriorityQueueVizMock - Demo version with mock data
 */
export default function PriorityQueueVizMock({
  autoRefresh = true,
  refreshInterval = QUEUE_POLL_INTERVAL,
  maxOrdersPerQueue = 50,
}: PriorityQueueVizProps) {
  // State management
  const [queueData, setQueueData] = useState<QueueData>(mockQueueData);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  
  const isMountedRef = useRef<boolean>(true);
  
  /**
   * Fetch mock data (simulates API call)
   */
  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Simulate API call with mock data
      const data = await fetchMockPriorityQueue();
      
      if (isMountedRef.current) {
        setQueueData(data);
        setLastUpdated(new Date());
        setIsLoading(false);
      }
    } catch (err) {
      console.error("Error fetching mock queue data:", err);
      
      if (isMountedRef.current) {
        setError("Failed to load queue data");
        setIsLoading(false);
      }
    }
  }, []);
  
  /**
   * Add a random order to the queue (for testing)
   */
  const addRandomOrder = useCallback(() => {
    const newOrder = generateRandomOrder();
    const pricingModel = newOrder.pricing_model;
    
    setQueueData(prev => {
      const newData = { ...prev };
      
      // Add to appropriate queue
      if (pricingModel === 'CONTRACTED') {
        newData.P0 = [...prev.P0, newOrder];
        newData.status.P0 = prev.status.P0 + 1;
      } else if (pricingModel === 'STANDARD') {
        newData.P1 = [...prev.P1, newOrder].sort(
          (a, b) => b.revenue_score - a.revenue_score
        );
        newData.status.P1 = prev.status.P1 + 1;
      } else if (pricingModel === 'CUSTOM') {
        newData.P2 = [...prev.P2, newOrder].sort(
          (a, b) => b.revenue_score - a.revenue_score
        );
        newData.status.P2 = prev.status.P2 + 1;
      }
      
      return newData;
    });
    
    setLastUpdated(new Date());
  }, []);
  
  /**
   * Manual refresh handler
   */
  const handleManualRefresh = useCallback(() => {
    fetchData();
  }, [fetchData]);
  
  /**
   * Setup polling effect
   */
  useEffect(() => {
    isMountedRef.current = true;
    
    // Initial load
    fetchData();
    
    // Setup auto-refresh
    let intervalId: NodeJS.Timeout | null = null;
    
    if (autoRefresh && refreshInterval > 0) {
      intervalId = setInterval(() => {
        // In demo mode, just update the timestamp
        // (Real mode would fetch new data)
        setLastUpdated(new Date());
      }, refreshInterval);
    }
    
    // Cleanup
    return () => {
      isMountedRef.current = false;
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [autoRefresh, refreshInterval, fetchData]);
  
  /**
   * Limit orders per queue
   */
  const limitOrders = (orders: any[], limit: number) => {
    return orders.slice(0, limit);
  };
  
  return (
    <div className="w-full">
      {/* Demo Mode Banner */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4 rounded-lg mb-6 shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold flex items-center gap-2">
              <span className="text-2xl">🎮</span>
              DEMO MODE - Using Mock Data
            </h3>
            <p className="text-sm mt-1 opacity-90">
              Testing the Priority Queue Visualization without backend! 
              Click "Add Random Order" to see it in action.
            </p>
          </div>
          <button
            onClick={addRandomOrder}
            className="px-6 py-3 bg-white text-purple-600 rounded-lg font-bold hover:bg-gray-100 active:scale-95 transition-all shadow-lg"
          >
            + Add Random Order
          </button>
        </div>
      </div>
      
      {/* Error State */}
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
                Error loading data
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
        status={queueData?.status || { P0: 0, P1: 0, P2: 0 }}
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
      
      {/* Demo Mode Footer */}
      <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg">
        <h4 className="font-semibold text-sm text-gray-800 dark:text-gray-200 mb-2">
          🎮 Demo Mode Features:
        </h4>
        <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
          <li>• <strong>Mock Data:</strong> Using pre-generated sample orders</li>
          <li>• <strong>Add Orders:</strong> Click "Add Random Order" button to add new orders</li>
          <li>• <strong>Auto-Sort:</strong> Orders automatically sort by priority and revenue score</li>
          <li>• <strong>No Backend:</strong> Everything works without API/MongoDB!</li>
          <li>• <strong>Switch to Real:</strong> Connect MongoDB to use real data (see TODO_NEXT_STEPS.md)</li>
        </ul>
      </div>
      
      {/* Auto-refresh indicator */}
      {autoRefresh && (
        <div className="mt-4 text-center">
          <p className="text-xs text-gray-500">
            ⏱️ Auto-updating timestamp every {refreshInterval / 1000} seconds
          </p>
        </div>
      )}
    </div>
  );
}

