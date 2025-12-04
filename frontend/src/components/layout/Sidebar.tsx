'use client';

import React from 'react';
import {
  LayoutDashboard,
  DollarSign,
  TrendingUp,
  Radio,
  Activity,
  Settings,
  X,
  Upload,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export type TabType =
  | 'overview'
  | 'pricing'
  | 'forecasting'
  | 'market'
  | 'elasticity'
  | 'upload';

interface SidebarProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  isOpen?: boolean;
  onClose?: () => void;
}

const menuItems = [
  { id: 'overview' as TabType, label: 'Overview', icon: LayoutDashboard },
  { id: 'pricing' as TabType, label: 'Order Pricing', icon: DollarSign },
  { id: 'forecasting' as TabType, label: 'Forecasting', icon: TrendingUp },
  { id: 'market' as TabType, label: 'Market Signals', icon: Radio },
  { id: 'elasticity' as TabType, label: 'Analysis', icon: Activity },
  { id: 'upload' as TabType, label: 'Data Upload', icon: Upload },
];

export function Sidebar({ activeTab, onTabChange, isOpen = true, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <aside className={cn(
        "w-64 bg-card border-r border-border flex flex-col",
        "fixed lg:static inset-y-0 left-0 z-50 transform transition-transform duration-300",
        "lg:translate-x-0",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
      {/* Logo */}
      <div className="p-6 border-b border-border flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-primary">
            Dynamic Pricing Solutions
          </h1>
          <p className="text-xs text-muted-foreground mt-1">Intelligence Platform</p>
        </div>
        {/* Close button - only visible on mobile */}
        <button
          onClick={onClose}
          className="lg:hidden p-2 hover:bg-accent rounded-md transition-colors"
        >
          <X size={20} />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => {
                onTabChange(item.id);
                // Close sidebar on mobile after selection
                if (onClose && window.innerWidth < 1024) {
                  onClose();
                }
              }}
              className={cn(
                'w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
              style={isActive ? { 
                background: 'linear-gradient(135deg, #3E4C59 0%, #6B8AA8 100%)',
              } : {}}
            >
              <Icon size={20} />
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* Settings */}
      <div className="p-4 border-t border-border">
        <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors">
          <Settings size={20} />
          Settings
        </button>
      </div>
    </aside>
    </>
  );
}

