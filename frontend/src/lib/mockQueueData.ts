/**
 * Mock Queue Data for Testing Priority Queue Visualization
 * 
 * This file provides sample data to test the queue visualization
 * WITHOUT needing backend or MongoDB connection.
 * 
 * Usage: Import this instead of calling the real API
 */

import { QueueData, Order, Priority } from '@/types/queue';

/**
 * Generate mock orders for testing
 */
export const mockOrders: Order[] = [
  // P0 Orders (CONTRACTED - Red)
  {
    order_id: 'ORD-A1B2C3',
    pricing_model: 'CONTRACTED' as any,
    revenue_score: 100,
    created_at: new Date(Date.now() - 2 * 60 * 1000).toISOString(), // 2 minutes ago
    order_data: {
      user_id: 'John Doe',
      pickup_location: { address: '123 Main Street, Downtown' },
      dropoff_location: { address: '456 Oak Avenue, Uptown' },
      price: 52.00,
      status: 'PENDING',
    },
  },
  {
    order_id: 'ORD-D4E5F6',
    pricing_model: 'CONTRACTED' as any,
    revenue_score: 100,
    created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 minutes ago
    order_data: {
      user_id: 'Sarah Johnson',
      pickup_location: { address: '789 Pine Road, Westside' },
      dropoff_location: { address: '321 Elm Street, Eastside' },
      price: 48.50,
      status: 'PENDING',
    },
  },
  {
    order_id: 'ORD-G7H8I9',
    pricing_model: 'CONTRACTED' as any,
    revenue_score: 100,
    created_at: new Date(Date.now() - 8 * 60 * 1000).toISOString(), // 8 minutes ago
    order_data: {
      user_id: 'Mike Williams',
      pickup_location: { address: '555 Broadway, Theater District' },
      dropoff_location: { address: '777 Park Avenue, Central Park' },
      price: 65.00,
      status: 'PENDING',
    },
  },
  
  // P1 Orders (STANDARD - Amber) - Sorted by revenue_score DESC
  {
    order_id: 'ORD-J1K2L3',
    pricing_model: 'STANDARD' as any,
    revenue_score: 145.8,
    created_at: new Date(Date.now() - 1 * 60 * 1000).toISOString(), // 1 minute ago
    order_data: {
      user_id: 'Emily Chen',
      pickup_location: { address: 'Airport Terminal 1' },
      dropoff_location: { address: 'Downtown Hotel District' },
      price: 89.50,
      status: 'PENDING',
    },
  },
  {
    order_id: 'ORD-M4N5O6',
    pricing_model: 'STANDARD' as any,
    revenue_score: 132.4,
    created_at: new Date(Date.now() - 3 * 60 * 1000).toISOString(), // 3 minutes ago
    order_data: {
      user_id: 'David Martinez',
      pickup_location: { address: 'Business District, 5th Ave' },
      dropoff_location: { address: 'Residential Area, Maple Street' },
      price: 72.30,
      status: 'PENDING',
    },
  },
  {
    order_id: 'ORD-P7Q8R9',
    pricing_model: 'STANDARD' as any,
    revenue_score: 128.9,
    created_at: new Date(Date.now() - 4 * 60 * 1000).toISOString(), // 4 minutes ago
    order_data: {
      user_id: 'Jessica Brown',
      pickup_location: { address: 'Shopping Mall, West Side' },
      dropoff_location: { address: 'University Campus' },
      price: 68.75,
      status: 'PENDING',
    },
  },
  {
    order_id: 'ORD-S1T2U3',
    pricing_model: 'STANDARD' as any,
    revenue_score: 115.6,
    created_at: new Date(Date.now() - 6 * 60 * 1000).toISOString(), // 6 minutes ago
    order_data: {
      user_id: 'Robert Taylor',
      pickup_location: { address: 'Train Station' },
      dropoff_location: { address: 'Suburban Area' },
      price: 58.20,
      status: 'PENDING',
    },
  },
  {
    order_id: 'ORD-V4W5X6',
    pricing_model: 'STANDARD' as any,
    revenue_score: 108.3,
    created_at: new Date(Date.now() - 7 * 60 * 1000).toISOString(), // 7 minutes ago
    order_data: {
      user_id: 'Amanda Wilson',
      pickup_location: { address: 'Concert Hall' },
      dropoff_location: { address: 'Restaurant District' },
      price: 54.90,
      status: 'PENDING',
    },
  },
  
  // P2 Orders (CUSTOM - Green) - Sorted by revenue_score DESC
  {
    order_id: 'ORD-Y7Z8A9',
    pricing_model: 'CUSTOM' as any,
    revenue_score: 95.7,
    created_at: new Date(Date.now() - 2 * 60 * 1000).toISOString(), // 2 minutes ago
    order_data: {
      user_id: 'Chris Anderson',
      pickup_location: { address: 'Corporate Office Park' },
      dropoff_location: { address: 'Hotel & Conference Center' },
      price: 45.80,
      status: 'PENDING',
    },
  },
  {
    order_id: 'ORD-B1C2D3',
    pricing_model: 'CUSTOM' as any,
    revenue_score: 88.4,
    created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 minutes ago
    order_data: {
      user_id: 'Lisa Garcia',
      pickup_location: { address: 'Medical Center' },
      dropoff_location: { address: 'Pharmacy, Main St' },
      price: 38.90,
      status: 'PENDING',
    },
  },
  {
    order_id: 'ORD-E4F5G6',
    pricing_model: 'CUSTOM' as any,
    revenue_score: 76.2,
    created_at: new Date(Date.now() - 9 * 60 * 1000).toISOString(), // 9 minutes ago
    order_data: {
      user_id: 'Kevin Lee',
      pickup_location: { address: 'Library' },
      dropoff_location: { address: 'Coffee Shop District' },
      price: 32.50,
      status: 'PENDING',
    },
  },
];

/**
 * Organize mock orders by priority queue
 */
export const mockQueueData: QueueData = {
  P0: mockOrders.filter(o => o.pricing_model === 'CONTRACTED'),
  P1: mockOrders
    .filter(o => o.pricing_model === 'STANDARD')
    .sort((a, b) => b.revenue_score - a.revenue_score), // Sorted DESC
  P2: mockOrders
    .filter(o => o.pricing_model === 'CUSTOM')
    .sort((a, b) => b.revenue_score - a.revenue_score), // Sorted DESC
  status: {
    P0: mockOrders.filter(o => o.pricing_model === 'CONTRACTED').length,
    P1: mockOrders.filter(o => o.pricing_model === 'STANDARD').length,
    P2: mockOrders.filter(o => o.pricing_model === 'CUSTOM').length,
  },
};

/**
 * Mock API function that returns mock data
 * (Simulates the real fetchPriorityQueue function)
 */
export async function fetchMockPriorityQueue(): Promise<QueueData> {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 500));
  
  return mockQueueData;
}

/**
 * Generate random order for testing dynamic updates
 */
export function generateRandomOrder(): Order {
  const types = ['CONTRACTED', 'STANDARD', 'CUSTOM'] as const;
  const type = types[Math.floor(Math.random() * types.length)];
  
  const names = [
    'Alex Thompson', 'Maria Rodriguez', 'James Kim', 'Sophie Turner',
    'Daniel Park', 'Olivia Davis', 'Ryan Murphy', 'Emma Watson',
  ];
  
  const locations = [
    'Downtown Plaza', 'Airport Terminal', 'Shopping Center', 'Business District',
    'Residential Area', 'University Campus', 'Medical Center', 'Park Avenue',
  ];
  
  const randomName = names[Math.floor(Math.random() * names.length)];
  const randomPickup = locations[Math.floor(Math.random() * locations.length)];
  const randomDropoff = locations[Math.floor(Math.random() * locations.length)];
  
  const baseRevenue = type === 'CONTRACTED' ? 100 : 
                     type === 'STANDARD' ? 80 + Math.random() * 70 :
                     50 + Math.random() * 50;
  
  const basePrice = type === 'CONTRACTED' ? 50 + Math.random() * 20 :
                   type === 'STANDARD' ? 60 + Math.random() * 40 :
                   30 + Math.random() * 30;
  
  return {
    order_id: `ORD-${Math.random().toString(36).substr(2, 6).toUpperCase()}`,
    pricing_model: type as any,
    revenue_score: Math.round(baseRevenue * 10) / 10,
    created_at: new Date().toISOString(),
    order_data: {
      user_id: randomName,
      pickup_location: { address: randomPickup },
      dropoff_location: { address: randomDropoff },
      price: Math.round(basePrice * 100) / 100,
      status: 'PENDING',
    },
  };
}

/**
 * Empty queue data (for testing empty states)
 */
export const emptyQueueData: QueueData = {
  P0: [],
  P1: [],
  P2: [],
  status: {
    P0: 0,
    P1: 0,
    P2: 0,
  },
};

