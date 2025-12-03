'use client';

import React, { useState } from 'react';
import { Calculator, Check, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { pricingAPI } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';

interface PricingResult {
  final_price: number;
  breakdown: {
    base_price: number;
    time_multiplier: number;
    location_multiplier: number;
    vehicle_multiplier: number;
    surge_multiplier: number;
    loyalty_discount: number;
  };
  revenue_score: number;
  pricing_model: string;
  explanation: string;
}

export function PricingTab() {
  const [formData, setFormData] = useState({
    customer_name: '',
    loyalty_status: 'Regular',
    origin: '',
    destination: '',
    pricing_model: 'STANDARD',
    vehicle_type: 'Economy',
    num_riders: 1,
    num_drivers: 10,
    time_of_day: 'Morning',
    location_type: 'Urban',
  });

  const [result, setResult] = useState<PricingResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleCalculate = async () => {
    setLoading(true);
    try {
      const response = await pricingAPI.calculate(formData);
      setResult(response.data);
    } catch (error) {
      console.error('Pricing calculation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const response = await pricingAPI.simulate(formData);
      setResult(response.data);
    } catch (error) {
      console.error('Pricing simulation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pricing Calculator */}
        <Card>
          <CardHeader>
            <CardTitle>Pricing Calculator</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Customer Info */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Customer Name
              </label>
              <Input
                placeholder="Enter customer name"
                value={formData.customer_name}
                onChange={(e) =>
                  setFormData({ ...formData, customer_name: e.target.value })
                }
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Loyalty Status
              </label>
              <Select
                value={formData.loyalty_status}
                onChange={(e) =>
                  setFormData({ ...formData, loyalty_status: e.target.value })
                }
              >
                <option value="Regular">Regular</option>
                <option value="Silver">Silver (-10%)</option>
                <option value="Gold">Gold (-15%)</option>
              </Select>
            </div>

            {/* Route Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Origin</label>
                <Input
                  placeholder="Origin"
                  value={formData.origin}
                  onChange={(e) =>
                    setFormData({ ...formData, origin: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Destination
                </label>
                <Input
                  placeholder="Destination"
                  value={formData.destination}
                  onChange={(e) =>
                    setFormData({ ...formData, destination: e.target.value })
                  }
                />
              </div>
            </div>

            {/* Pricing Model */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Pricing Model
              </label>
              <Select
                value={formData.pricing_model}
                onChange={(e) =>
                  setFormData({ ...formData, pricing_model: e.target.value })
                }
              >
                <option value="CONTRACTED">Contracted (Fixed Price)</option>
                <option value="STANDARD">Standard (Dynamic)</option>
                <option value="CUSTOM">Custom (Negotiated)</option>
              </Select>
            </div>

            {/* Vehicle Type */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Vehicle Type
              </label>
              <Select
                value={formData.vehicle_type}
                onChange={(e) =>
                  setFormData({ ...formData, vehicle_type: e.target.value })
                }
              >
                <option value="Economy">Economy (1.0x)</option>
                <option value="Premium">Premium (1.6x)</option>
              </Select>
            </div>

            {/* Time and Location */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Time of Day
                </label>
                <Select
                  value={formData.time_of_day}
                  onChange={(e) =>
                    setFormData({ ...formData, time_of_day: e.target.value })
                  }
                >
                  <option value="Morning">Morning Rush (1.3x)</option>
                  <option value="Evening">Evening Rush (1.4x)</option>
                  <option value="Night">Night (1.2x)</option>
                  <option value="Regular">Regular (1.0x)</option>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Location Type
                </label>
                <Select
                  value={formData.location_type}
                  onChange={(e) =>
                    setFormData({ ...formData, location_type: e.target.value })
                  }
                >
                  <option value="Urban High">Urban High Demand (1.3x)</option>
                  <option value="Urban">Urban Regular (1.15x)</option>
                  <option value="Suburban">Suburban (1.0x)</option>
                </Select>
              </div>
            </div>

            {/* Supply/Demand */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Active Riders
                </label>
                <Input
                  type="number"
                  value={formData.num_riders}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      num_riders: parseInt(e.target.value),
                    })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Available Drivers
                </label>
                <Input
                  type="number"
                  value={formData.num_drivers}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      num_drivers: parseInt(e.target.value),
                    })
                  }
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <Button
                onClick={handleCalculate}
                disabled={loading}
                className="flex-1"
              >
                <Calculator size={16} className="mr-2" />
                Calculate Price
              </Button>
              <Button
                variant="outline"
                onClick={handleSimulate}
                disabled={loading}
                className="flex-1"
              >
                Simulate
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Pricing Result */}
        <Card>
          <CardHeader>
            <CardTitle>Pricing Result</CardTitle>
          </CardHeader>
          <CardContent>
            {result ? (
              <div className="space-y-6">
                {/* Final Price */}
                <div className="text-center p-6 bg-primary/10 rounded-lg">
                  <p className="text-sm text-muted-foreground mb-2">
                    Final Price
                  </p>
                  <p className="text-4xl font-bold text-primary">
                    {formatCurrency(result.final_price)}
                  </p>
                  <div className="flex items-center justify-center gap-2 mt-2">
                    <Badge>{result.pricing_model}</Badge>
                    <Badge variant="secondary">
                      Score: {result.revenue_score.toFixed(2)}
                    </Badge>
                  </div>
                </div>

                {/* Breakdown */}
                <div>
                  <h3 className="text-sm font-medium mb-3">Price Breakdown</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Base Price</span>
                      <span className="font-medium">
                        {formatCurrency(result.breakdown.base_price)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">
                        Time Multiplier
                      </span>
                      <span className="font-medium">
                        {result.breakdown.time_multiplier}x
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">
                        Location Multiplier
                      </span>
                      <span className="font-medium">
                        {result.breakdown.location_multiplier}x
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">
                        Vehicle Multiplier
                      </span>
                      <span className="font-medium">
                        {result.breakdown.vehicle_multiplier}x
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">
                        Surge Multiplier
                      </span>
                      <span className="font-medium">
                        {result.breakdown.surge_multiplier}x
                      </span>
                    </div>
                    {result.breakdown.loyalty_discount > 0 && (
                      <div className="flex justify-between text-sm text-green-500">
                        <span>Loyalty Discount</span>
                        <span className="font-medium">
                          -{(result.breakdown.loyalty_discount * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* AI Explanation */}
                {result.explanation && (
                  <div className="p-4 bg-accent rounded-lg">
                    <h3 className="text-sm font-medium mb-2">AI Explanation</h3>
                    <p className="text-sm text-muted-foreground">
                      {result.explanation}
                    </p>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-3">
                  <Button className="flex-1">
                    <Check size={16} className="mr-2" />
                    Accept
                  </Button>
                  <Button variant="outline" className="flex-1">
                    <X size={16} className="mr-2" />
                    Reject
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <Calculator size={48} className="mx-auto mb-4 opacity-50" />
                <p>Calculate a price to see results</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Pricing Models Comparison */}
      <Card>
        <CardHeader>
          <CardTitle>Pricing Models Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 border border-border rounded-lg">
              <Badge className="mb-3">CONTRACTED</Badge>
              <h4 className="font-medium mb-2">Fixed Price</h4>
              <p className="text-sm text-muted-foreground mb-3">
                Pre-agreed fixed pricing for corporate clients. No multipliers
                applied.
              </p>
              <ul className="text-xs space-y-1 text-muted-foreground">
                <li>• P0 Priority (FIFO)</li>
                <li>• No surge pricing</li>
                <li>• Guaranteed rates</li>
              </ul>
            </div>

            <div className="p-4 border border-border rounded-lg">
              <Badge className="mb-3">STANDARD</Badge>
              <h4 className="font-medium mb-2">Dynamic Pricing</h4>
              <p className="text-sm text-muted-foreground mb-3">
                Real-time dynamic pricing with all multipliers and surge
                pricing.
              </p>
              <ul className="text-xs space-y-1 text-muted-foreground">
                <li>• P1 Priority (Revenue sorted)</li>
                <li>• All multipliers active</li>
                <li>• Loyalty discounts</li>
              </ul>
            </div>

            <div className="p-4 border border-border rounded-lg">
              <Badge className="mb-3">CUSTOM</Badge>
              <h4 className="font-medium mb-2">Negotiated Rates</h4>
              <p className="text-sm text-muted-foreground mb-3">
                Custom negotiated pricing for special customers or scenarios.
              </p>
              <ul className="text-xs space-y-1 text-muted-foreground">
                <li>• P2 Priority (Revenue sorted)</li>
                <li>• Flexible multipliers</li>
                <li>• Custom discounts</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

