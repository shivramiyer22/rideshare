'use client';

import React from 'react';
import { OrderCreationForm } from '@/components/OrderCreationForm';

export function PricingTab() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">
          Create New Order
        </h1>
        <p className="text-muted-foreground mt-1">
          Create new ride orders with real-time dynamic pricing estimates from historical data
        </p>
      </div>

      {/* Order Creation Form with Dynamic Pricing */}
      <OrderCreationForm />
    </div>
  );
}

