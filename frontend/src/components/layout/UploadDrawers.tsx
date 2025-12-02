'use client';

import React, { useState, useRef } from 'react';
import { Upload, FileText, X } from 'lucide-react';
import { Drawer } from '@/components/ui/Drawer';
import { Button } from '@/components/ui/Button';
import { uploadAPI } from '@/lib/api';

type DrawerType =
  | 'historical'
  | 'competitor'
  | 'event'
  | 'traffic'
  | 'loyalty'
  | null;

interface UploadDrawersProps {
  activeDrawer: DrawerType;
  onClose: () => void;
}

export function UploadDrawers({ activeDrawer, onClose }: UploadDrawersProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{
    type: 'success' | 'error' | null;
    message: string;
  }>({ type: null, message: '' });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const drawerConfig = {
    historical: {
      title: 'Upload Historical Rides Data',
      description: 'Upload CSV or JSON file with 1000+ historical orders for Prophet ML training',
      acceptedFormats: '.csv,.json',
      uploadFn: uploadAPI.historicalData,
    },
    competitor: {
      title: 'Upload Competitor Data',
      description: 'Upload CSV or Excel file with competitor pricing information',
      acceptedFormats: '.csv,.xlsx,.xls',
      uploadFn: uploadAPI.competitorData,
    },
    event: {
      title: 'Upload Event Data',
      description: 'Upload event files (concerts, sports, etc.)',
      acceptedFormats: '.csv,.json',
      uploadFn: uploadAPI.eventData,
    },
    traffic: {
      title: 'Upload Traffic/Demand Signals',
      description: 'Upload traffic patterns and demand signal data',
      acceptedFormats: '.csv,.json',
      uploadFn: uploadAPI.trafficData,
    },
    loyalty: {
      title: 'Upload Customer Loyalty Data',
      description: 'Upload customer loyalty and segmentation data',
      acceptedFormats: '.csv,.json',
      uploadFn: uploadAPI.loyaltyData,
    },
  };

  const config = activeDrawer ? drawerConfig[activeDrawer] : null;

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadStatus({ type: null, message: '' });
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !config) return;

    setUploading(true);
    setUploadStatus({ type: null, message: '' });

    try {
      const response = await config.uploadFn(selectedFile);
      setUploadStatus({
        type: 'success',
        message: `Successfully uploaded ${response.data.rows_count || 'file'}!`,
      });
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      
      // Close drawer after 2 seconds
      setTimeout(() => {
        onClose();
        setUploadStatus({ type: null, message: '' });
      }, 2000);
    } catch (error: any) {
      setUploadStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Upload failed. Please try again.',
      });
    } finally {
      setUploading(false);
    }
  };

  if (!activeDrawer || !config) return null;

  return (
    <Drawer
      isOpen={!!activeDrawer}
      onClose={onClose}
      title={config.title}
    >
      <div className="space-y-6">
        <p className="text-sm text-muted-foreground">{config.description}</p>

        {/* File Upload Area */}
        <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
          <input
            ref={fileInputRef}
            type="file"
            accept={config.acceptedFormats}
            onChange={handleFileSelect}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="cursor-pointer flex flex-col items-center gap-4"
          >
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
              <Upload size={32} className="text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium mb-1">
                Click to upload or drag and drop
              </p>
              <p className="text-xs text-muted-foreground">
                Accepted formats: {config.acceptedFormats}
              </p>
            </div>
          </label>
        </div>

        {/* Selected File */}
        {selectedFile && (
          <div className="flex items-center justify-between p-4 bg-accent rounded-lg">
            <div className="flex items-center gap-3">
              <FileText size={20} />
              <div>
                <p className="text-sm font-medium">{selectedFile.name}</p>
                <p className="text-xs text-muted-foreground">
                  {(selectedFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => {
                setSelectedFile(null);
                if (fileInputRef.current) fileInputRef.current.value = '';
              }}
            >
              <X size={16} />
            </Button>
          </div>
        )}

        {/* Upload Status */}
        {uploadStatus.type && (
          <div
            className={`p-4 rounded-lg ${
              uploadStatus.type === 'success'
                ? 'bg-green-500/10 text-green-500'
                : 'bg-red-500/10 text-red-500'
            }`}
          >
            <p className="text-sm">{uploadStatus.message}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <Button
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            className="flex-1"
          >
            {uploading ? 'Uploading...' : 'Upload'}
          </Button>
          <Button variant="outline" onClick={onClose} disabled={uploading}>
            Cancel
          </Button>
        </div>
      </div>
    </Drawer>
  );
}

// Upload Button Component
interface UploadButtonProps {
  onOpenDrawer: (drawer: DrawerType) => void;
}

export function UploadButtons({ onOpenDrawer }: UploadButtonProps) {
  const buttons = [
    { type: 'historical' as DrawerType, label: 'Historical Data', shortLabel: 'Historical' },
    { type: 'competitor' as DrawerType, label: 'Competitor Data', shortLabel: 'Competitor' },
    { type: 'event' as DrawerType, label: 'Event Data', shortLabel: 'Events' },
    { type: 'traffic' as DrawerType, label: 'Traffic Signals', shortLabel: 'Traffic' },
    { type: 'loyalty' as DrawerType, label: 'Loyalty Data', shortLabel: 'Loyalty' },
  ];

  return (
    <div className="fixed bottom-6 left-0 right-0 z-30 px-4 flex justify-center">
      <div 
        className="flex flex-wrap justify-center gap-2 rounded-lg p-3 max-w-4xl" 
        style={{ 
          background: 'linear-gradient(135deg, #3E4C59 0%, #6B8AA8 100%)', 
          marginRight: '80px',
          boxShadow: '8px 8px 16px rgba(0, 0, 0, 0.2), -4px -4px 12px rgba(255, 255, 255, 0.1)',
        }}
      >
        {buttons.map((button) => (
          <Button
            key={button.type}
            variant="outline"
            size="sm"
            onClick={() => onOpenDrawer(button.type)}
            className="gap-2 bg-white/10 border-white/30 text-white hover:bg-white/20 hover:border-white/50 transition-all"
            style={{
              boxShadow: '2px 2px 4px rgba(0, 0, 0, 0.2), -1px -1px 3px rgba(255, 255, 255, 0.1)',
            }}
          >
            <Upload size={14} />
            <span className="hidden sm:inline">{button.label}</span>
            <span className="sm:hidden">{button.shortLabel}</span>
          </Button>
        ))}
      </div>
    </div>
  );
}

