import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Orders API
export const ordersAPI = {
  create: (data: any) => api.post('/api/v1/orders/', data), // Added trailing slash to avoid 307 redirect
  getQueue: () => api.get('/api/v1/orders/queue/priority'),
  estimate: (data: any) => api.post('/api/v1/orders/estimate', data),
};

// Upload API
export const uploadAPI = {
  historicalData: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/upload/historical-data', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  competitorData: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/upload/competitor-data', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  eventData: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/upload/event-data', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  trafficData: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/upload/traffic-data', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  loyaltyData: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/upload/loyalty-data', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// ML API
export const mlAPI = {
  train: () => api.post('/api/ml/train'),
  forecast: (horizon: '30d' | '60d' | '90d', pricingModel: string) =>
    api.get(`/api/forecast/${horizon}`, { params: { pricing_model: pricingModel } }),
};

// Analytics API
export const analyticsAPI = {
  revenue: (period: string) => api.get('/api/analytics/revenue', { params: { period } }),
  kpis: () => api.get('/api/analytics/kpis'),
  topRoutes: () => api.get('/api/analytics/top-routes'),
  customerDistribution: () => api.get('/api/analytics/customer-distribution'),
};

// Market Signals API
export const marketAPI = {
  events: () => api.get('/api/market/events'),
  traffic: () => api.get('/api/market/traffic'),
  news: () => api.get('/api/market/news'),
  signals: () => api.get('/api/market/signals'),
};

// Competitor API
export const competitorAPI = {
  prices: () => api.get('/api/competitor/prices'),
  comparison: () => api.get('/api/competitor/comparison'),
};

// Elasticity API
export const elasticityAPI = {
  segments: () => api.get('/api/elasticity/segments'),
  heatmap: () => api.get('/api/elasticity/heatmap'),
};

// Pricing API
export const pricingAPI = {
  calculate: (data: any) => api.post('/api/pricing/calculate', data),
  simulate: (data: any) => api.post('/api/pricing/simulate', data),
};

