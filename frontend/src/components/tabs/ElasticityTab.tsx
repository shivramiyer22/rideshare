'use client';

import React from 'react';
import { Activity, TrendingDown, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  ZAxis,
  AreaChart,
  Area,
} from 'recharts';

const elasticityBySegment = [
  { segment: 'Gold', elasticity: -0.3, label: 'Inelastic', color: '#3E4C59' },
  { segment: 'Silver', elasticity: -0.6, label: 'Moderate', color: '#5B7C99' },
  { segment: 'Regular', elasticity: -1.2, label: 'Elastic', color: '#70AD47' },
];

const elasticityHeatmap = [
  { time: '6AM', downtown: -0.4, midtown: -0.6, suburban: -0.9 },
  { time: '9AM', downtown: -0.3, midtown: -0.5, suburban: -0.8 },
  { time: '12PM', downtown: -0.5, midtown: -0.7, suburban: -1.0 },
  { time: '3PM', downtown: -0.6, midtown: -0.8, suburban: -1.1 },
  { time: '6PM', downtown: -0.2, midtown: -0.4, suburban: -0.7 },
  { time: '9PM', downtown: -0.4, midtown: -0.6, suburban: -0.9 },
];

const demandCurveData = [
  { price: 10, demand: 250 },
  { price: 15, demand: 220 },
  { price: 20, demand: 185 },
  { price: 25, demand: 155 },
  { price: 30, demand: 130 },
  { price: 35, demand: 110 },
  { price: 40, demand: 95 },
  { price: 45, demand: 80 },
  { price: 50, demand: 70 },
];

const priceOptimization = [
  { price: 20, revenue: 3700, profit: 1850 },
  { price: 25, revenue: 3875, profit: 1940 },
  { price: 30, revenue: 3900, profit: 1950 },
  { price: 35, revenue: 3850, profit: 1925 },
  { price: 40, revenue: 3800, profit: 1900 },
];

export function ElasticityTab() {
  return (
    <div className="space-y-6">
      {/* Elasticity by Segment */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {elasticityBySegment.map((item) => (
          <Card key={item.segment}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium">
                  {item.segment} Customers
                </CardTitle>
                <Activity size={20} style={{ color: item.color }} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold mb-2">{item.elasticity}</div>
              <Badge
                variant={
                  Math.abs(item.elasticity) < 0.5
                    ? 'success'
                    : Math.abs(item.elasticity) < 1.0
                    ? 'warning'
                    : 'destructive'
                }
              >
                {item.label}
              </Badge>
              <p className="text-xs text-muted-foreground mt-2">
                {Math.abs(item.elasticity) < 0.5
                  ? 'Low price sensitivity'
                  : Math.abs(item.elasticity) < 1.0
                  ? 'Moderate price sensitivity'
                  : 'High price sensitivity'}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Elasticity Heatmap */}
      <Card>
        <CardHeader>
          <CardTitle>Analysis by Time & Zone</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={elasticityHeatmap}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis
                dataKey="time"
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
              />
              <YAxis
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                domain={[-1.2, 0]}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="downtown"
                stroke="#8b5cf6"
                strokeWidth={2}
                name="Downtown"
              />
              <Line
                type="monotone"
                dataKey="midtown"
                stroke="#3b82f6"
                strokeWidth={2}
                name="Midtown"
              />
              <Line
                type="monotone"
                dataKey="suburban"
                stroke="#10b981"
                strokeWidth={2}
                name="Suburban"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Demand Curve & Price Optimization */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Demand Curve</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={demandCurveData}>
                <defs>
                  <linearGradient id="demandGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#5B7C99" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#5B7C99" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="price"
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  label={{ value: 'Price ($)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  label={{ value: 'Demand', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="demand"
                  stroke="#5B7C99"
                  strokeWidth={3}
                  fill="url(#demandGradient)"
                  dot={{ fill: '#5B7C99', r: 5 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Price Optimization</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={priceOptimization} barGap={8} margin={{ left: -20 }}>
                <defs>
                  <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3E4C59" />
                    <stop offset="100%" stopColor="#6B8AA8" />
                  </linearGradient>
                  <linearGradient id="profitGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#609D37" />
                    <stop offset="50%" stopColor="#70AD47" />
                    <stop offset="100%" stopColor="#80BD57" />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="price"
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  label={{ value: 'Price ($)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Legend 
                  wrapperStyle={{ paddingTop: '20px' }} 
                  iconType="square"
                  align="center"
                  verticalAlign="bottom"
                />
                <Bar dataKey="revenue" fill="url(#revenueGradient)" name="Revenue" />
                <Bar dataKey="profit" fill="url(#profitGradient)" name="Profit" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Sensitivity Analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Sensitivity Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp size={20} className="text-green-500" />
                  <h4 className="font-medium">Price Increase Scenario</h4>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">+10% Price</span>
                    <span className="font-medium">-6% Demand</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Revenue Impact</span>
                    <span className="font-medium text-green-500">+3.4%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Profit Impact</span>
                    <span className="font-medium text-green-500">+4.8%</span>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingDown size={20} className="text-red-500" />
                  <h4 className="font-medium">Price Decrease Scenario</h4>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">-10% Price</span>
                    <span className="font-medium">+8% Demand</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Revenue Impact</span>
                    <span className="font-medium text-red-500">-2.8%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Profit Impact</span>
                    <span className="font-medium text-red-500">-5.2%</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <h4 className="font-medium mb-2 text-blue-600 dark:text-blue-400">
                Optimal Pricing Strategy
              </h4>
              <p className="text-sm text-muted-foreground">
                Based on elasticity analysis, the optimal price point is <strong>$30</strong> which
                maximizes profit at <strong>$1,950</strong>. Gold customers show low price
                sensitivity (elasticity: -0.3), allowing for premium pricing during peak hours.
                Regular customers are highly price-sensitive (elasticity: -1.2), suggesting
                promotional pricing during off-peak times.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

