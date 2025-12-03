/**
 * QueueTab Component
 * 
 * Tab page for the Priority Queue Visualization.
 * Integrates the PriorityQueueViz component into the main application tabs.
 * 
 * Features:
 * - Page header with title and description
 * - Full priority queue visualization with P0, P1, P2 queues
 * - Information cards explaining each queue type
 * - Real-time updates every 5 seconds
 */

'use client';

import React from 'react';
// import PriorityQueueViz from '@/components/queue/PriorityQueueViz'; // Real version (needs backend)
import PriorityQueueVizMock from '@/components/queue/PriorityQueueVizMock'; // Demo version (works without backend)

export function QueueTab() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">
          Priority Queue Visualization
        </h1>
        <p className="text-muted-foreground mt-1">
          Real-time view of all orders in P0 (CONTRACTED), P1 (STANDARD), and P2 (CUSTOM) priority queues
        </p>
      </div>

      {/* Priority Queue Visualization - DEMO MODE */}
      <PriorityQueueVizMock
        autoRefresh={true}
        refreshInterval={5000}
        maxOrdersPerQueue={50}
      />

      {/* Information Cards - Explain Queue Types */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold text-foreground mb-4">
          Queue Priority System
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* P0 - CONTRACTED */}
          <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-red-500 text-white rounded-lg">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-red-900 dark:text-red-100">
                  🔴 P0 Queue - CONTRACTED
                </h3>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                  Highest priority. Fixed pricing agreements. Processed FIFO (First In, First Out) order.
                </p>
              </div>
            </div>
          </div>

          {/* P1 - STANDARD */}
          <div className="p-4 rounded-lg bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-amber-500 text-white rounded-lg">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-amber-900 dark:text-amber-100">
                  🟡 P1 Queue - STANDARD
                </h3>
                <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
                  High priority. Dynamic pricing with multipliers. Sorted by revenue score (highest first).
                </p>
              </div>
            </div>
          </div>

          {/* P2 - CUSTOM */}
          <div className="p-4 rounded-lg bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-green-500 text-white rounded-lg">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-green-900 dark:text-green-100">
                  🟢 P2 Queue - CUSTOM
                </h3>
                <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                  Normal priority. Negotiated pricing for special cases. Sorted by revenue score (highest first).
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Technical Details */}
      <div className="mt-6 p-4 rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
        <h3 className="font-semibold text-foreground mb-2">
          Technical Details
        </h3>
        <ul className="text-sm text-muted-foreground space-y-1">
          <li>• <strong>Backend:</strong> Redis-based priority queue system with P0 (LIST), P1 (SORTED SET), P2 (SORTED SET)</li>
          <li>• <strong>Updates:</strong> Real-time polling every 5 seconds from <code className="px-1 py-0.5 bg-gray-200 dark:bg-gray-800 rounded text-xs">/api/orders/queue/priority</code></li>
          <li>• <strong>P0 Sorting:</strong> FIFO (First In, First Out) - oldest order processed first</li>
          <li>• <strong>P1/P2 Sorting:</strong> Revenue Score Descending - highest revenue orders processed first</li>
          <li>• <strong>Revenue Score:</strong> Calculated based on pricing tier, customer loyalty, and order characteristics</li>
        </ul>
      </div>
    </div>
  );
}

export default QueueTab;

