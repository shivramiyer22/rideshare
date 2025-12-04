'use client';

import React, { useState } from 'react';
import { Sidebar, TabType } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { AIPanel } from '@/components/layout/AIPanel';
import { OverviewTab } from '@/components/tabs/OverviewTab';
import { PricingTab } from '@/components/tabs/PricingTab';
import { ForecastingTab } from '@/components/tabs/ForecastingTab';
import { MarketSignalsTab } from '@/components/tabs/MarketSignalsTab';
import { ElasticityTab } from '@/components/tabs/ElasticityTab';
import { UploadTab } from '@/components/tabs/UploadTab';

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab />;
      case 'pricing':
        return <PricingTab />;
      case 'forecasting':
        return <ForecastingTab />;
      case 'market':
        return <MarketSignalsTab />;
      case 'elasticity':
        return <ElasticityTab />;
      case 'upload':
        return <UploadTab />;
      default:
        return <OverviewTab />;
    }
  };

  return (
    <div className="h-screen flex overflow-hidden bg-background">
      {/* Sidebar */}
      <Sidebar 
        activeTab={activeTab} 
        onTabChange={setActiveTab}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header onMenuClick={() => setSidebarOpen(true)} />

        {/* Content with AI Panel */}
        <div className="flex-1 flex overflow-hidden gap-px bg-border">
          {/* Main Content */}
          <main className="flex-1 overflow-y-auto p-6">
            {renderTabContent()}
          </main>

          {/* AI Assistant Panel */}
          <AIPanel />
        </div>
      </div>
    </div>
  );
}

