/**
 * Type definitions for Priority Queue Visualization
 * 
 * This file contains TypeScript interfaces and types for the priority queue system.
 * The queue system has 3 priority levels:
 * - P0: CONTRACTED orders (highest priority, FIFO)
 * - P1: STANDARD orders (sorted by revenue_score DESC)
 * - P2: CUSTOM orders (sorted by revenue_score DESC)
 */

// ============================================================================
// ENUMS
// ============================================================================

/**
 * Priority levels for orders
 */
export enum Priority {
  P0 = "P0", // Critical - CONTRACTED orders (FIFO)
  P1 = "P1", // High - STANDARD orders (revenue sorted)
  P2 = "P2", // Normal - CUSTOM orders (revenue sorted)
}

/**
 * Pricing tiers that determine priority
 */
export enum PricingTier {
  CONTRACTED = "CONTRACTED", // → P0
  STANDARD = "STANDARD",     // → P1
  CUSTOM = "CUSTOM",         // → P2
}

/**
 * Order status
 */
export enum OrderStatus {
  PENDING = "PENDING",
  IN_PROGRESS = "IN_PROGRESS",
  COMPLETED = "COMPLETED",
  CANCELLED = "CANCELLED",
}

// ============================================================================
// INTERFACES
// ============================================================================

/**
 * Location information for pickup/dropoff
 */
export interface Location {
  address: string;
  city?: string;
  state?: string;
  zip?: string;
  latitude?: number;
  longitude?: number;
}

/**
 * Order data structure as returned by backend
 */
export interface Order {
  // Basic information
  order_id: string;
  user_id?: string;
  customer_name?: string;
  
  // Pricing and priority
  pricing_model: PricingTier;
  priority?: Priority;
  revenue_score: number;
  price?: number;
  
  // Location data
  pickup_location?: Location | string;
  dropoff_location?: Location | string;
  route?: string;
  
  // Status and timestamps
  status?: OrderStatus;
  created_at: string;
  updated_at?: string;
  processed_at?: string;
  
  // Additional order data
  order_data?: {
    pickup_location?: Location;
    dropoff_location?: Location;
    user_id?: string;
    status?: string;
    [key: string]: any;
  };
}

/**
 * Queue data structure as returned by API
 */
export interface QueueData {
  P0: Order[]; // CONTRACTED orders (FIFO)
  P1: Order[]; // STANDARD orders (revenue_score DESC)
  P2: Order[]; // CUSTOM orders (revenue_score DESC)
  status: {
    P0: number; // Count of P0 orders
    P1: number; // Count of P1 orders
    P2: number; // Count of P2 orders
  };
}

/**
 * Queue metadata for display
 */
export interface QueueMetadata {
  type: Priority;
  label: string;
  description: string;
  color: {
    bg: string;        // Background color (Tailwind class)
    border: string;    // Border color (Tailwind class)
    text: string;      // Text color (Tailwind class)
    badge: string;     // Badge color (Tailwind class)
    icon: string;      // Icon color (hex)
  };
  emoji: string;       // Visual indicator
  sortMethod: string;  // Display text for sorting method
}

// ============================================================================
// CONSTANTS
// ============================================================================

/**
 * Queue metadata configuration
 * Defines colors, labels, and display information for each queue type
 */
export const QUEUE_METADATA: Record<Priority, QueueMetadata> = {
  [Priority.P0]: {
    type: Priority.P0,
    label: "P0 Queue",
    description: "CONTRACTED - Highest Priority",
    color: {
      bg: "bg-red-50",
      border: "border-red-500",
      text: "text-red-900",
      badge: "bg-red-100 text-red-800",
      icon: "#dc2626",
    },
    emoji: "🔴",
    sortMethod: "FIFO (First In, First Out)",
  },
  [Priority.P1]: {
    type: Priority.P1,
    label: "P1 Queue",
    description: "STANDARD - High Priority",
    color: {
      bg: "bg-amber-50",
      border: "border-amber-500",
      text: "text-amber-900",
      badge: "bg-amber-100 text-amber-800",
      icon: "#f59e0b",
    },
    emoji: "🟡",
    sortMethod: "Revenue Score ↓ (Highest First)",
  },
  [Priority.P2]: {
    type: Priority.P2,
    label: "P2 Queue",
    description: "CUSTOM - Normal Priority",
    color: {
      bg: "bg-green-50",
      border: "border-green-500",
      text: "text-green-900",
      badge: "bg-green-100 text-green-800",
      icon: "#16a34a",
    },
    emoji: "🟢",
    sortMethod: "Revenue Score ↓ (Highest First)",
  },
};

/**
 * API endpoint for fetching queue data
 */
export const QUEUE_API_ENDPOINT = "/api/orders/queue/priority";

/**
 * Polling interval for real-time updates (milliseconds)
 */
export const QUEUE_POLL_INTERVAL = 5000; // 5 seconds

// ============================================================================
// TYPE GUARDS
// ============================================================================

/**
 * Check if a value is a valid Priority
 */
export function isPriority(value: any): value is Priority {
  return Object.values(Priority).includes(value);
}

/**
 * Check if a value is a valid PricingTier
 */
export function isPricingTier(value: any): value is PricingTier {
  return Object.values(PricingTier).includes(value);
}

// ============================================================================
// UTILITY TYPES
// ============================================================================

/**
 * Props for OrderCard component
 */
export interface OrderCardProps {
  order: Order;
  queueType: Priority;
}

/**
 * Props for QueueColumn component
 */
export interface QueueColumnProps {
  queueType: Priority;
  orders: Order[];
  count: number;
  isLoading?: boolean;
}

/**
 * Props for QueueStats component
 */
export interface QueueStatsProps {
  status: QueueData["status"];
  lastUpdated: Date | null;
  isLoading: boolean;
  onRefresh: () => void;
}

/**
 * Props for PriorityQueueViz component
 */
export interface PriorityQueueVizProps {
  autoRefresh?: boolean;        // Enable automatic polling (default: true)
  refreshInterval?: number;     // Polling interval in ms (default: 5000)
  maxOrdersPerQueue?: number;   // Max orders to display per queue (default: 50)
}

