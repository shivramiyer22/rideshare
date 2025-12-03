'use client';

import React from 'react';
import { OrderCreationForm } from '@/components/OrderCreationForm';

export function OrdersTab() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">
          Order Management
        </h1>
        <p className="text-muted-foreground mt-1">
          Create new ride orders and manage them through the priority queue system
        </p>
      </div>

      {/* Order Creation Form */}
      <OrderCreationForm />

      {/* Information Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
        <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-blue-500 text-white rounded-lg">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-blue-900 dark:text-blue-100">
                CONTRACTED Orders (P0)
              </h3>
              <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                Fixed pricing, highest priority, processed FIFO
              </p>
            </div>
          </div>
        </div>

        <div className="p-4 rounded-lg bg-yellow-50 dark:bg-yellow-950 border border-yellow-200 dark:border-yellow-800">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-yellow-500 text-white rounded-lg">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-yellow-900 dark:text-yellow-100">
                STANDARD Orders (P1)
              </h3>
              <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                Dynamic pricing with multipliers, sorted by revenue score
              </p>
            </div>
          </div>
        </div>

        <div className="p-4 rounded-lg bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-green-500 text-white rounded-lg">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-green-900 dark:text-green-100">
                CUSTOM Orders (P2)
              </h3>
              <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                Negotiated rates, sorted by revenue score
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

