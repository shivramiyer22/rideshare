'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { analyticsAPI, mlAPI } from '@/lib/api';

interface GlobalData {
  forecastData: any;
  segmentData: any;
  kpiData: any;
  lastUpdated: number;
  loading: boolean;
}

interface GlobalDataContextType {
  data: GlobalData;
  refreshData: () => Promise<void>;
  isRefreshing: boolean;
}

const GlobalDataContext = createContext<GlobalDataContextType | undefined>(undefined);

export function GlobalDataProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<GlobalData>({
    forecastData: null,
    segmentData: null,
    kpiData: null,
    lastUpdated: 0,
    loading: true,
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Load all data on initial mount
  const loadAllData = async () => {
    try {
      console.log('Loading all application data...');
      
      const [forecastRes, segmentRes, kpiRes] = await Promise.all([
        analyticsAPI.hwcoForecast('STANDARD', 30).catch(() => null),
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/reports/segment-dynamic-pricing-analysis`).then(r => r.json()).catch(() => null),
        analyticsAPI.kpis().catch(() => null),
      ]);

      setData({
        forecastData: forecastRes?.data || null,
        segmentData: segmentRes || null,
        kpiData: kpiRes?.data || null,
        lastUpdated: Date.now(),
        loading: false,
      });

      console.log('✓ All data loaded successfully');
    } catch (error) {
      console.error('Error loading global data:', error);
      setData(prev => ({ ...prev, loading: false }));
    }
  };

  // Check if data sources have been updated since last pull
  const checkForUpdates = async (): Promise<boolean> => {
    try {
      // Check pipeline last run timestamp
      const pipelineRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/pipeline/last-run`);
      const pipelineData = await pipelineRes.json();
      
      if (pipelineData.last_run) {
        const lastRunTime = new Date(pipelineData.last_run).getTime();
        // If pipeline ran after our last data pull, there's new data
        return lastRunTime > data.lastUpdated;
      }
      
      return false;
    } catch (error) {
      console.error('Error checking for updates:', error);
      return false; // If check fails, don't refresh
    }
  };

  // Refresh data only if backend has updates
  const refreshData = async () => {
    setIsRefreshing(true);
    try {
      console.log('Checking for data updates...');
      
      const hasUpdates = await checkForUpdates();
      
      if (hasUpdates) {
        console.log('✓ New data available, refreshing...');
        await loadAllData();
      } else {
        console.log('✓ Data is up-to-date, no refresh needed');
        // Just show loading state briefly
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Load data on mount
  useEffect(() => {
    loadAllData();
  }, []);

  return (
    <GlobalDataContext.Provider value={{ data, refreshData, isRefreshing }}>
      {children}
    </GlobalDataContext.Provider>
  );
}

export function useGlobalData() {
  const context = useContext(GlobalDataContext);
  if (!context) {
    throw new Error('useGlobalData must be used within GlobalDataProvider');
  }
  return context;
}

