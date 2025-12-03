'use client';

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { Label } from '@/components/ui/Label';
import { ordersAPI } from '@/lib/api';

// Types
type LoyaltyStatus = 'Gold' | 'Silver' | 'Regular';
type PricingModel = 'CONTRACTED' | 'STANDARD' | 'CUSTOM';
type VehicleType = 'Economy' | 'Premium';

interface OrderFormData {
  // Customer Information
  customerName: string;
  loyaltyStatus: LoyaltyStatus;
  
  // Route Information
  origin: string;
  destination: string;
  
  // Pricing Model
  pricingModel: PricingModel;
  
  // Vehicle Information
  vehicleType: VehicleType;
  
  // Capacity
  numberOfRiders: number;
  numberOfDrivers: number;
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
    loyaltyStatus: 'Regular',
    origin: '',
    destination: '',
    pricingModel: 'STANDARD',
    vehicleType: 'Economy',
    numberOfRiders: 1,
    numberOfDrivers: 1,
  });

  // UI state
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

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

    // Number of riders validation
    if (formData.numberOfRiders < 1) {
      newErrors.numberOfRiders = 'At least 1 rider is required';
    } else if (formData.numberOfRiders > 10) {
      newErrors.numberOfRiders = 'Maximum 10 riders allowed';
    }

    // Number of drivers validation
    if (formData.numberOfDrivers < 1) {
      newErrors.numberOfDrivers = 'At least 1 driver is required';
    } else if (formData.numberOfDrivers > 5) {
      newErrors.numberOfDrivers = 'Maximum 5 drivers allowed';
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
      [name]: name === 'numberOfRiders' || name === 'numberOfDrivers' 
        ? parseInt(value) || 0 
        : value,
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
      loyaltyStatus: 'Regular',
      origin: '',
      destination: '',
      pricingModel: 'STANDARD',
      vehicleType: 'Economy',
      numberOfRiders: 1,
      numberOfDrivers: 1,
    });
    setErrors({});
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
                    <option value="Regular">Regular (No Discount)</option>
                    <option value="Silver">Silver (10% Discount)</option>
                    <option value="Gold">Gold (15% Discount)</option>
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
                    <option value="CONTRACTED">CONTRACTED (P0 - Fixed Price, FIFO)</option>
                    <option value="STANDARD">STANDARD (P1 - Dynamic, Revenue Sorted)</option>
                    <option value="CUSTOM">CUSTOM (P2 - Negotiated, Revenue Sorted)</option>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    {formData.pricingModel === 'CONTRACTED' && 'Fixed price, highest priority (FIFO)'}
                    {formData.pricingModel === 'STANDARD' && 'Dynamic pricing with multipliers'}
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
                    <option value="Economy">Economy (1.0x)</option>
                    <option value="Premium">Premium (1.6x)</option>
                  </Select>
                </div>
              </div>
            </div>

            {/* Capacity Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-foreground border-b pb-2">
                Capacity
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Number of Riders */}
                <div className="space-y-2">
                  <Label htmlFor="numberOfRiders">
                    Number of Riders <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="numberOfRiders"
                    name="numberOfRiders"
                    type="number"
                    min="1"
                    max="10"
                    value={formData.numberOfRiders}
                    onChange={handleChange}
                    className={errors.numberOfRiders ? 'border-red-500' : ''}
                  />
                  {errors.numberOfRiders && (
                    <p className="text-sm text-red-500">{errors.numberOfRiders}</p>
                  )}
                </div>

                {/* Number of Drivers */}
                <div className="space-y-2">
                  <Label htmlFor="numberOfDrivers">
                    Number of Drivers <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="numberOfDrivers"
                    name="numberOfDrivers"
                    type="number"
                    min="1"
                    max="5"
                    value={formData.numberOfDrivers}
                    onChange={handleChange}
                    className={errors.numberOfDrivers ? 'border-red-500' : ''}
                  />
                  {errors.numberOfDrivers && (
                    <p className="text-sm text-red-500">{errors.numberOfDrivers}</p>
                  )}
                </div>
              </div>
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

