'use client';

import React, { useState, useRef } from 'react';
import { Upload, Database, TrendingUp, Calendar, FileText, Users } from 'lucide-react';
import { Button } from '@/components/ui/Button';

type UploadType = 'historical' | 'competitor' | 'event' | 'traffic' | 'loyalty';

export function UploadTab() {
  const [activeTab, setActiveTab] = useState<UploadType>('historical');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadTabs = [
    { id: 'historical' as UploadType, label: 'Historical Data', icon: Database },
    { id: 'competitor' as UploadType, label: 'Competitor Data', icon: TrendingUp },
    { id: 'event' as UploadType, label: 'Event Data', icon: Calendar },
    { id: 'traffic' as UploadType, label: 'Traffic Signals', icon: FileText },
    { id: 'loyalty' as UploadType, label: 'Loyalty Data', icon: Users },
  ];

  const uploadConfig = {
    historical: {
      title: 'Historical Data Requirements',
      requirements: [
        'Minimum 300 rows required for Prophet ML training',
        'Required columns: Order_Date, Historical_Cost_of_Ride, Pricing_Model, Expected_Ride_Duration',
        'Optional columns: Customer_Id, Number_Of_Riders, Number_of_Drivers, Location_Category, Customer_Loyalty_Status, Number_of_Past_Rides, Average_Ratings, Time_of_Ride, Vehicle_Type',
        'Accepted formats: CSV, JSON',
        'Derived fields (Supply_by_Demand, Demand_Profile, Historical_Unit_Price) are calculated automatically',
      ],
      formats: 'CSV or JSON files only',
      afterUpload: [
        'Data is validated and stored in MongoDB',
        'Derived fields (Historical_Unit_Price, Supply_by_Demand, Demand_Profile) are calculated automatically',
        'Use this ML training endpoint to start Prophet ML models on this data',
      ],
    },
    competitor: {
      title: 'Competitor Data Requirements',
      requirements: [
        'Required columns: Competitor_Name, Pricing_Strategy, Base_Price',
        'Optional columns: Surge_Multiplier, Discount_Offers, Market_Share',
        'Accepted formats: CSV, XLSX, XLS',
        'Data should be current (within last 30 days)',
      ],
      formats: 'CSV, XLSX, or XLS files',
      afterUpload: [
        'Data is validated and stored securely',
        'Competitor analysis is updated automatically',
        'Price comparison charts are refreshed',
      ],
    },
    event: {
      title: 'Event Data Requirements',
      requirements: [
        'Required columns: Event_Name, Event_Date, Event_Location, Expected_Attendance',
        'Optional columns: Event_Type, Start_Time, End_Time',
        'Accepted formats: CSV, JSON',
        'Events should be future-dated for forecasting',
      ],
      formats: 'CSV or JSON files only',
      afterUpload: [
        'Events are integrated into demand forecasting',
        'Surge pricing recommendations are generated',
        'Calendar view is updated with events',
      ],
    },
    traffic: {
      title: 'Traffic Signal Requirements',
      requirements: [
        'Required columns: Timestamp, Location, Traffic_Level, Congestion_Score',
        'Optional columns: Weather_Condition, Road_Closures, Incidents',
        'Accepted formats: CSV, JSON',
        'Real-time or historical traffic data accepted',
      ],
      formats: 'CSV or JSON files only',
      afterUpload: [
        'Traffic patterns are analyzed',
        'Location-based multipliers are updated',
        'Surge zones are recalculated',
      ],
    },
    loyalty: {
      title: 'Loyalty Data Requirements',
      requirements: [
        'Required columns: Customer_Id, Loyalty_Status, Total_Rides, Total_Spend',
        'Optional columns: Join_Date, Last_Ride_Date, Average_Rating, Preferred_Vehicle',
        'Accepted formats: CSV, JSON',
        'Customer segmentation (Gold, Silver, Regular)',
      ],
      formats: 'CSV or JSON files only',
      afterUpload: [
        'Customer profiles are updated',
        'Loyalty discounts are recalculated',
        'Segmentation analysis is refreshed',
      ],
    },
  };

  const config = uploadConfig[activeTab];

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      console.log('Uploading:', selectedFile.name);
      // Upload logic will be connected to backend
    }
  };

  return (
    <div className="min-h-full bg-background dark:bg-[#1a1f2e] text-foreground dark:text-white p-6 rounded-lg">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">File Upload</h1>
        <p className="text-sm text-muted-foreground dark:text-gray-400">
          Upload Historical ride data for Prophet ML training or competitor pricing data.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-border dark:border-gray-700">
        {uploadTabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                setSelectedFile(null);
              }}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                activeTab === tab.id
                  ? 'border-[#5B7C99] text-foreground dark:text-white'
                  : 'border-transparent text-muted-foreground dark:text-gray-400 hover:text-foreground dark:hover:text-white'
              }`}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Requirements Section */}
      <div className="mb-6 p-4 bg-card dark:bg-[#232937] rounded-lg border border-border dark:border-transparent">
        <h3 className="text-lg font-semibold mb-3">{config.title}</h3>
        <ul className="space-y-2 text-sm text-foreground dark:text-gray-300">
          {config.requirements.map((req, index) => (
            <li key={index} className="flex items-start gap-2">
              <span className="text-[#5B7C99] dark:text-blue-400 mt-1">•</span>
              <span>{req}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Upload Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
          isDragging
            ? 'border-[#5B7C99] bg-[#5B7C99]/10'
            : 'border-border dark:border-gray-600 bg-card dark:bg-[#232937]'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={activeTab === 'competitor' ? '.csv,.xlsx,.xls' : '.csv,.json'}
          onChange={handleFileSelect}
          className="hidden"
        />
        
        <Upload size={48} className="mx-auto mb-4 text-muted-foreground dark:text-gray-400" />
        
        {selectedFile ? (
          <div className="mb-4">
            <p className="text-lg font-medium text-foreground dark:text-white mb-1">{selectedFile.name}</p>
            <p className="text-sm text-muted-foreground dark:text-gray-400">
              {(selectedFile.size / 1024).toFixed(2)} KB
            </p>
          </div>
        ) : (
          <p className="text-muted-foreground dark:text-gray-400 mb-4">Drag and drop your file here, or</p>
        )}
        
        <Button
          onClick={() => fileInputRef.current?.click()}
          className="text-white px-6 py-2 border-none"
          style={{
            background: 'linear-gradient(135deg, #3E4C59 0%, #6B8AA8 100%)',
            boxShadow: '4px 4px 8px rgba(0, 0, 0, 0.15), -2px -2px 6px rgba(255, 255, 255, 0.1)',
          }}
        >
          Browse Files
        </Button>
        
        <p className="text-xs text-muted-foreground dark:text-gray-500 mt-3">{config.formats}</p>
      </div>

      {/* Upload Button */}
      <Button
        onClick={handleUpload}
        disabled={!selectedFile}
        className="w-full mt-6 text-white py-3 text-base font-medium disabled:opacity-50 disabled:cursor-not-allowed border-none"
        style={{
          background: selectedFile ? 'linear-gradient(135deg, #3E4C59 0%, #6B8AA8 100%)' : '#9CA3AF',
          boxShadow: selectedFile ? '4px 4px 8px rgba(0, 0, 0, 0.15), -2px -2px 6px rgba(255, 255, 255, 0.1)' : 'none',
        }}
      >
        <Upload size={20} className="mr-2" />
        Upload {uploadTabs.find(t => t.id === activeTab)?.label}
      </Button>

      {/* What Happens After Upload */}
      <div className="mt-6 p-4 bg-card dark:bg-[#232937] rounded-lg border border-border dark:border-transparent">
        <h3 className="text-lg font-semibold mb-3">What happens after upload?</h3>
        <ul className="space-y-2 text-sm text-foreground dark:text-gray-300">
          {config.afterUpload.map((item, index) => (
            <li key={index} className="flex items-start gap-2">
              <span className="text-[#70AD47] dark:text-green-400 mt-1">•</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

