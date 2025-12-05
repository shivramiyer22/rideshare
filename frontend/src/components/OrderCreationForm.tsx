'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { Label } from '@/components/ui/Label';
import { ordersAPI } from '@/lib/api';

// Types
type LoyaltyStatus = 'Gold' | 'Silver' | 'Regular';
type PricingModel = 'CONTRACTED' | 'STANDARD' | 'SURGE' | 'CUSTOM';
type VehicleType = 'Economy' | 'Premium';

interface OrderFormData {
  // Customer Information
  customerName: string;
  loyaltyStatus: LoyaltyStatus;
  
  // Route Information
  origin: string;
  destination: string;
  locationCategory: 'Urban' | 'Suburban' | 'Rural';
  
  // Pricing Model
  pricingModel: PricingModel;
  
  // Vehicle Information
  vehicleType: VehicleType;
}

interface PriceEstimate {
  demandLevel: string;
  rideDuration: number;
  unitPrice: number;
  estimatedPrice: number;
  isLoading: boolean;
  error: string | null;
}

interface FormErrors {
  [key: string]: string;
}

// Toast Component (Simple inline notification)
const Toast = ({ message, type, onClose }: { message: string; type: 'success' | 'error'; onClose: () => void }) => {
  React.useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div
      className={`fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg animate-slide-in-right ${
        type === 'success' 
          ? 'bg-green-500 text-white' 
          : 'bg-red-500 text-white'
      }`}
    >
      <div className="flex items-center gap-2">
        {type === 'success' ? (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        )}
        <span className="font-medium">{message}</span>
      </div>
    </div>
  );
};

export function OrderCreationForm() {
  // Form state
  const [formData, setFormData] = useState<OrderFormData>({
    customerName: '',
    loyaltyStatus: '' as any,
    origin: '',
    destination: '',
    locationCategory: '' as any,
    pricingModel: '' as any,
    vehicleType: '' as any,
  });

  // UI state
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  
  // Price estimation state
  const [estimate, setEstimate] = useState<PriceEstimate>({
    demandLevel: 'MEDIUM',
    rideDuration: 0,
    unitPrice: 0,
    estimatedPrice: 0,
    isLoading: false,
    error: null,
  });

  // Fetch price estimate whenever relevant fields change
  useEffect(() => {
    const fetchEstimate = async () => {
      // Only fetch if we have ALL required fields selected
      if (!formData.locationCategory || !formData.loyaltyStatus || !formData.vehicleType || !formData.pricingModel) {
        // Reset to zero if any field is not selected
        setEstimate({
          demandLevel: 'MEDIUM',
          rideDuration: 0,
          unitPrice: 0,
          estimatedPrice: 0,
          isLoading: false,
          error: null,
        });
        return;
      }

      setEstimate(prev => ({ ...prev, isLoading: true, error: null }));

      try {
        const response = await ordersAPI.estimate({
          location_category: formData.locationCategory,
          loyalty_tier: formData.loyaltyStatus,
          vehicle_type: formData.vehicleType,
          pricing_model: formData.pricingModel,
        });

        const data = response.data;
        
        // Extract data from response
        setEstimate({
          demandLevel: data.historical_baseline.segment_demand_profile || 'MEDIUM',
          rideDuration: data.historical_baseline.segment_avg_fcs_ride_duration || 0,
          unitPrice: data.historical_baseline.segment_avg_fcs_unit_price || 0,
          estimatedPrice: data.estimated_price || 0,
          isLoading: false,
          error: null,
        });
      } catch (error: any) {
        console.error('Error fetching estimate:', error);
        setEstimate(prev => ({
          ...prev,
          isLoading: false,
          error: 'Unable to fetch estimate',
        }));
      }
    };

    fetchEstimate();
  }, [formData.locationCategory, formData.loyaltyStatus, formData.vehicleType, formData.pricingModel]);

  // Validation function
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Customer Name validation
    if (!formData.customerName.trim()) {
      newErrors.customerName = 'Customer name is required';
    } else if (formData.customerName.trim().length < 2) {
      newErrors.customerName = 'Customer name must be at least 2 characters';
    }

    // Origin validation
    if (!formData.origin.trim()) {
      newErrors.origin = 'Origin location is required';
    } else if (formData.origin.trim().length < 3) {
      newErrors.origin = 'Origin must be at least 3 characters';
    }

    // Destination validation
    if (!formData.destination.trim()) {
      newErrors.destination = 'Destination location is required';
    } else if (formData.destination.trim().length < 3) {
      newErrors.destination = 'Destination must be at least 3 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle input changes
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    
    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate form
    if (!validateForm()) {
      setToast({
        message: 'Please fix the errors in the form',
        type: 'error',
      });
      return;
    }

    setIsSubmitting(true);

    try {
      // Call API to create order
      const response = await ordersAPI.create(formData);

      // Show success toast
      setToast({
        message: 'Order created successfully! Added to priority queue.',
        type: 'success',
      });

      // Reset form
      resetForm();
    } catch (error: any) {
      console.error('Error creating order:', error);
      
      // Show error toast
      setToast({
        message: error.response?.data?.detail || 'Failed to create order. Please try again.',
        type: 'error',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Reset form to initial state
  const resetForm = () => {
    setFormData({
      customerName: '',
      loyaltyStatus: '' as any,
      origin: '',
      destination: '',
      locationCategory: '' as any,
      pricingModel: '' as any,
      vehicleType: '' as any,
    });
    setErrors({});
    setEstimate({
      demandLevel: 'MEDIUM',
      rideDuration: 0,
      unitPrice: 0,
      estimatedPrice: 0,
      isLoading: false,
      error: null,
    });
  };

  return (
    <>
      <Card className="max-w-3xl mx-auto">
        <CardHeader>
          <CardTitle>Create New Ride Order</CardTitle>
          <CardDescription>
            Fill out the form below to create a new ride order. The order will be added to the priority queue based on the pricing model.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Customer Information Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-foreground border-b pb-2">
                Customer Information
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Customer Name */}
                <div className="space-y-2">
                  <Label htmlFor="customerName">
                    Customer Name <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="customerName"
                    name="customerName"
                    type="text"
                    placeholder="Enter customer name"
                    value={formData.customerName}
                    onChange={handleChange}
                    className={errors.customerName ? 'border-red-500' : ''}
                  />
                  {errors.customerName && (
                    <p className="text-sm text-red-500">{errors.customerName}</p>
                  )}
                </div>

                {/* Loyalty Status */}
                <div className="space-y-2">
                  <Label htmlFor="loyaltyStatus">
                    Loyalty Status
                  </Label>
                  <Select
                    id="loyaltyStatus"
                    name="loyaltyStatus"
                    value={formData.loyaltyStatus}
                    onChange={handleChange}
                  >
                    <option value="">-- Select Loyalty Status --</option>
                    <option value="Regular">Regular</option>
                    <option value="Silver">Silver</option>
                    <option value="Gold">Gold</option>
                  </Select>
                </div>
              </div>
            </div>

            {/* Route Information Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-foreground border-b pb-2">
                Route Information
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Origin */}
                <div className="space-y-2">
                  <Label htmlFor="origin">
                    Origin <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="origin"
                    name="origin"
                    type="text"
                    placeholder="e.g., Downtown LA"
                    value={formData.origin}
                    onChange={handleChange}
                    className={errors.origin ? 'border-red-500' : ''}
                  />
                  {errors.origin && (
                    <p className="text-sm text-red-500">{errors.origin}</p>
                  )}
                </div>

                {/* Destination */}
                <div className="space-y-2">
                  <Label htmlFor="destination">
                    Destination <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="destination"
                    name="destination"
                    type="text"
                    placeholder="e.g., LAX Airport"
                    value={formData.destination}
                    onChange={handleChange}
                    className={errors.destination ? 'border-red-500' : ''}
                  />
                  {errors.destination && (
                    <p className="text-sm text-red-500">{errors.destination}</p>
                  )}
                </div>
              </div>
              
              {/* Location Category */}
              <div className="space-y-2">
                <Label htmlFor="locationCategory">
                  Location Category
                </Label>
                  <Select
                    id="locationCategory"
                    name="locationCategory"
                    value={formData.locationCategory}
                    onChange={handleChange}
                  >
                    <option value="">-- Select Location Category --</option>
                    <option value="Urban">Urban</option>
                    <option value="Suburban">Suburban</option>
                    <option value="Rural">Rural</option>
                  </Select>
                <p className="text-xs text-muted-foreground">
                  Select the area type for accurate pricing
                </p>
              </div>
            </div>

            {/* Pricing & Vehicle Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-foreground border-b pb-2">
                Pricing & Vehicle
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Pricing Model */}
                <div className="space-y-2">
                  <Label htmlFor="pricingModel">
                    Pricing Model
                  </Label>
                  <Select
                    id="pricingModel"
                    name="pricingModel"
                    value={formData.pricingModel}
                    onChange={handleChange}
                  >
                    <option value="">-- Select Pricing Model --</option>
                    <option value="STANDARD">Standard</option>
                    <option value="SURGE">Surge</option>
                    <option value="CONTRACTED">Contracted</option>
                    <option value="CUSTOM">Custom</option>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    {formData.pricingModel === 'CONTRACTED' && 'Fixed price, highest priority'}
                    {formData.pricingModel === 'STANDARD' && 'Dynamic pricing with multipliers'}
                    {formData.pricingModel === 'SURGE' && 'Peak demand pricing'}
                    {formData.pricingModel === 'CUSTOM' && 'Custom negotiated rates'}
                  </p>
                </div>

                {/* Vehicle Type */}
                <div className="space-y-2">
                  <Label htmlFor="vehicleType">
                    Vehicle Type
                  </Label>
                  <Select
                    id="vehicleType"
                    name="vehicleType"
                    value={formData.vehicleType}
                    onChange={handleChange}
                  >
                    <option value="">-- Select Vehicle Type --</option>
                    <option value="Economy">Economy</option>
                    <option value="Premium">Premium</option>
                  </Select>
                </div>
              </div>
            </div>

            {/* Estimated Dynamic Pricing Section */}
            <div className={`space-y-4 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 p-6 rounded-lg border-2 border-blue-200 dark:border-blue-800 transition-all duration-300 ${estimate.isLoading ? 'opacity-70 scale-[0.99]' : 'opacity-100 scale-100'}`}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100">
                    Estimated Dynamic Pricing
                  </h3>
                  {estimate.isLoading && (
                    <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                  )}
                </div>
                {(formData.locationCategory || formData.loyaltyStatus || formData.vehicleType || formData.pricingModel) ? (
                  <div className="text-xs px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 font-mono">
                    {formData.locationCategory || '—'} • {formData.loyaltyStatus || '—'} • {formData.vehicleType || '—'} • {formData.pricingModel || '—'}
                  </div>
                ) : (
                  <div className="text-xs px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400">
                    No segment selected
                  </div>
                )}
              </div>

              {estimate.error && (
                <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 p-3 rounded">
                  {estimate.error}
                </div>
              )}

              {(!formData.locationCategory || !formData.loyaltyStatus || !formData.vehicleType || !formData.pricingModel) && (
                <div className="text-center py-8">
                  <svg className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  <p className="text-gray-500 dark:text-gray-400 text-lg font-medium">
                    Select all required fields to see pricing estimate
                  </p>
                  <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
                    Choose loyalty status, location, pricing model, and vehicle type
                  </p>
                </div>
              )}

              {formData.locationCategory && formData.loyaltyStatus && formData.vehicleType && formData.pricingModel && (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Demand Level */}
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                    <Label className="text-xs font-medium text-gray-600 dark:text-gray-400">
                      Demand Level
                    </Label>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span 
                      className={`text-2xl font-bold ${
                        estimate.demandLevel === 'HIGH' ? 'text-red-600' :
                        estimate.demandLevel === 'LOW' ? 'text-green-600' :
                        'text-yellow-600'
                      }`}
                    >
                      {estimate.isLoading ? '...' : estimate.demandLevel}
                    </span>
                    {!estimate.isLoading && (
                      <span className="text-xs text-gray-500">
                        {estimate.demandLevel === 'HIGH' && '🔥'}
                        {estimate.demandLevel === 'MEDIUM' && '📊'}
                        {estimate.demandLevel === 'LOW' && '✅'}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Based on driver availability
                  </p>
                </div>

                {/* Ride Duration */}
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <Label className="text-xs font-medium text-gray-600 dark:text-gray-400">
                      Avg Ride Duration
                    </Label>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-bold text-blue-600">
                      {estimate.isLoading ? '...' : estimate.rideDuration.toFixed(1)}
                    </span>
                    <span className="text-sm text-gray-500">min</span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Historical segment average
                  </p>
                </div>

                {/* Unit Price */}
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <Label className="text-xs font-medium text-gray-600 dark:text-gray-400">
                      Unit Price (per min)
                    </Label>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-bold text-green-600">
                      ${estimate.isLoading ? '...' : estimate.unitPrice.toFixed(2)}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Price per minute of ride
                  </p>
                </div>
                  </div>

                  {/* Estimated Total Price */}
                  {estimate.estimatedPrice > 0 && !estimate.isLoading && (
                    <div className="mt-4 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950/30 dark:to-emerald-950/30 p-4 rounded-lg border-2 border-green-300 dark:border-green-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Estimated Ride Price
                      </Label>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        Based on segment: {formData.locationCategory} • {formData.loyaltyStatus} • {formData.vehicleType}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-bold text-green-700 dark:text-green-400">
                        ${estimate.estimatedPrice.toFixed(2)}
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        {formData.pricingModel} pricing
                      </p>
                    </div>
                  </div>
                    </div>
                  )}

                  <p className="text-xs text-gray-500 dark:text-gray-400 italic text-center">
                    💡 Pricing updates automatically based on your selections
                  </p>
                </div>
              )}
            </div>

            {/* Form Actions */}
            <div className="flex gap-3 pt-4 border-t">
              <Button
                type="submit"
                disabled={isSubmitting}
                className="flex-1"
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Creating Order...
                  </>
                ) : (
                  'Create Order'
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={resetForm}
                disabled={isSubmitting}
              >
                Reset Form
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </>
  );
}

