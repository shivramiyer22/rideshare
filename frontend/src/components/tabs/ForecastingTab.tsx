'use client';

import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import {
  LineChart,
  Line,
  Area,
  AreaChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { mlAPI } from '@/lib/api';
import { formatNumber, formatDate } from '@/lib/utils';

// Mock forecast data
const generate30DayForecast = () => {
  const data = [];
  const startDate = new Date();
  for (let i = 0; i < 30; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    data.push({
      date: date.toISOString().split('T')[0],
      predicted: 145 + Math.random() * 50 + Math.sin(i / 7) * 30,
      lower: 120 + Math.random() * 30,
      upper: 170 + Math.random() * 40,
      trend: 145 + i * 0.5,
    });
  }
  return data;
};

const generate60DayForecast = () => {
  const data = [];
  const startDate = new Date();
  for (let i = 0; i < 60; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    data.push({
      date: date.toISOString().split('T')[0],
      predicted: 145 + Math.random() * 60 + Math.sin(i / 7) * 35,
      lower: 115 + Math.random() * 35,
      upper: 175 + Math.random() * 45,
      trend: 145 + i * 0.6,
    });
  }
  return data;
};

const generate90DayForecast = () => {
  const data = [];
  const startDate = new Date();
  for (let i = 0; i < 90; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    data.push({
      date: date.toISOString().split('T')[0],
      predicted: 145 + Math.random() * 70 + Math.sin(i / 7) * 40,
      lower: 110 + Math.random() * 40,
      upper: 180 + Math.random() * 50,
      trend: 145 + i * 0.7,
    });
  }
  return data;
};

export function ForecastingTab() {
  const [pricingModel, setPricingModel] = useState('STANDARD');
  const [forecastHorizon, setForecastHorizon] = useState<'30d' | '60d' | '90d'>('30d');
  const [loading, setLoading] = useState(false);
  const [forecastData, setForecastData] = useState({
    '30d': generate30DayForecast(),
    '60d': generate60DayForecast(),
    '90d': generate90DayForecast(),
  });

  const currentData = forecastData[forecastHorizon];
  const trendDirection = currentData[currentData.length - 1].trend > currentData[0].trend ? 'up' : 'down';
  const avgPredicted = currentData.reduce((sum, d) => sum + d.predicted, 0) / currentData.length;

  const handleRefresh = async () => {
    setLoading(true);
    try {
      // const response = await mlAPI.forecast(forecastHorizon, pricingModel);
      // setForecastData(prev => ({ ...prev, [forecastHorizon]: response.data.forecast }));
      
      // For now, regenerate mock data
      setForecastData({
        '30d': generate30DayForecast(),
        '60d': generate60DayForecast(),
        '90d': generate90DayForecast(),
      });
    } catch (error) {
      console.error('Forecast refresh failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-[200px]">
              <label className="text-sm font-medium mb-2 block">
                Pricing Model
              </label>
              <Select
                value={pricingModel}
                onChange={(e) => setPricingModel(e.target.value)}
              >
                <option value="CONTRACTED">Contracted</option>
                <option value="STANDARD">Standard</option>
                <option value="CUSTOM">Custom</option>
              </Select>
            </div>

            <div className="flex-1 min-w-[200px]">
              <label className="text-sm font-medium mb-2 block">Method</label>
              <Badge variant="success" className="text-sm">
                Prophet ML
              </Badge>
            </div>

            <div className="pt-6">
              <Button 
                onClick={handleRefresh} 
                disabled={loading} 
                variant="outline"
                className="border-none text-white hover:opacity-90"
                style={{
                  background: 'linear-gradient(135deg, #3E4C59 0%, #6B8AA8 100%)',
                  boxShadow: '4px 4px 8px rgba(0, 0, 0, 0.15), -2px -2px 6px rgba(255, 255, 255, 0.1)',
                }}
              >
                <RefreshCw size={16} className="mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Forecast Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Avg. Predicted Demand
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(Math.round(avgPredicted))}</div>
            <p className="text-xs text-muted-foreground mt-1">rides/day</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Trend
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {trendDirection === 'up' ? (
                <TrendingUp size={24} className="text-green-500" />
              ) : (
                <TrendingDown size={24} className="text-red-500" />
              )}
              <span className="text-2xl font-bold">
                {trendDirection === 'up' ? 'Increasing' : 'Decreasing'}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Confidence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">92%</div>
            <p className="text-xs text-muted-foreground mt-1">80% intervals</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              MAPE
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">8.4%</div>
            <p className="text-xs text-muted-foreground mt-1">accuracy</p>
          </CardContent>
        </Card>
      </div>

      {/* Forecast Chart */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Demand Forecast - Prophet ML</CardTitle>
            <Tabs value={forecastHorizon} onValueChange={(v) => setForecastHorizon(v as any)}>
              <TabsList>
                <TabsTrigger value="30d">30 Days</TabsTrigger>
                <TabsTrigger value="60d">60 Days</TabsTrigger>
                <TabsTrigger value="90d">90 Days</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={currentData}>
              <defs>
                <linearGradient id="confidenceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.1} />
                  <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis
                dataKey="date"
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickFormatter={(value) => {
                  const date = new Date(value);
                  return `${date.getMonth() + 1}/${date.getDate()}`;
                }}
              />
              <YAxis
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickFormatter={(value) => formatNumber(value)}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
                labelFormatter={(value) => formatDate(value)}
                formatter={(value: any) => formatNumber(Math.round(value))}
              />
              <Legend />
              
              {/* Confidence Interval */}
              <Area
                type="monotone"
                dataKey="upper"
                stroke="none"
                fill="url(#confidenceGradient)"
                fillOpacity={0.3}
                name="Upper Bound"
              />
              <Area
                type="monotone"
                dataKey="lower"
                stroke="none"
                fill="url(#confidenceGradient)"
                fillOpacity={0.3}
                name="Lower Bound"
              />
              
              {/* Predicted Line */}
              <Line
                type="monotone"
                dataKey="predicted"
                stroke="hsl(var(--primary))"
                strokeWidth={3}
                dot={false}
                name="Predicted Demand"
              />
              
              {/* Trend Line */}
              <Line
                type="monotone"
                dataKey="trend"
                stroke="hsl(var(--accent-foreground))"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                name="Trend"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Seasonality & Components */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Weekly Seasonality</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart
                data={[
                  { day: 'Mon', effect: 0.95 },
                  { day: 'Tue', effect: 0.92 },
                  { day: 'Wed', effect: 0.90 },
                  { day: 'Thu', effect: 1.05 },
                  { day: 'Fri', effect: 1.25 },
                  { day: 'Sat', effect: 1.35 },
                  { day: 'Sun', effect: 1.20 },
                ]}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="day" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="effect"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  dot={{ fill: 'hsl(var(--primary))' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Daily Seasonality</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart
                data={[
                  { hour: '6AM', effect: 0.85 },
                  { hour: '9AM', effect: 1.30 },
                  { hour: '12PM', effect: 1.10 },
                  { hour: '3PM', effect: 0.95 },
                  { hour: '6PM', effect: 1.40 },
                  { hour: '9PM', effect: 1.15 },
                  { hour: '12AM', effect: 0.80 },
                ]}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="hour" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="effect"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  dot={{ fill: 'hsl(var(--primary))' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* AI Explanation */}
      <Card>
        <CardHeader>
          <CardTitle>Forecast Explanation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div 
              className="p-4 rounded-lg"
              style={{
                background: 'linear-gradient(135deg, #3E4C59 0%, #6B8AA8 100%)',
                boxShadow: '4px 4px 8px rgba(0, 0, 0, 0.15), -2px -2px 6px rgba(255, 255, 255, 0.1)',
              }}
            >
              <h4 className="font-medium mb-2 text-white">Prophet ML Analysis</h4>
              <p className="text-sm text-white/90">
                The forecast predicts an {trendDirection === 'up' ? 'upward' : 'downward'} trend over the next {forecastHorizon.replace('d', ' days')}.
                Weekly seasonality shows peak demand on Fridays and Saturdays. Daily patterns indicate
                morning (9 AM) and evening (6 PM) rush hours as high-demand periods.
              </p>
            </div>

            <div 
              className="p-4 rounded-lg"
              style={{
                background: 'linear-gradient(135deg, #3E4C59 0%, #6B8AA8 100%)',
                boxShadow: '4px 4px 8px rgba(0, 0, 0, 0.15), -2px -2px 6px rgba(255, 255, 255, 0.1)',
              }}
            >
              <h4 className="font-medium mb-2 text-white">
                External Factors Detected
              </h4>
              <ul className="text-sm text-white/90 space-y-1">
                <li>• Concert at Stadium (Friday, 7 PM) - Expected +45% demand</li>
                <li>• Heavy traffic downtown - Surge pricing recommended</li>
                <li>• Weather forecast: Clear skies - Normal demand</li>
              </ul>
            </div>

            <div 
              className="p-4 rounded-lg"
              style={{
                background: 'linear-gradient(135deg, #3E4C59 0%, #6B8AA8 100%)',
                boxShadow: '4px 4px 8px rgba(0, 0, 0, 0.15), -2px -2px 6px rgba(255, 255, 255, 0.1)',
              }}
            >
              <h4 className="font-medium mb-2 text-white">
                Recommendations
              </h4>
              <ul className="text-sm text-white/90 space-y-1">
                <li>• Increase driver availability on Friday evening</li>
                <li>• Apply 1.7x surge multiplier during concert hours</li>
                <li>• Expected revenue increase: +$8,400</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

