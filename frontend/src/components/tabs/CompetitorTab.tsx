'use client';

import React from 'react';
import { Users, AlertCircle, TrendingUp, TrendingDown } from 'lucide-react';
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
} from 'recharts';
import { formatCurrency } from '@/lib/utils';

const competitorPrices = [
  { route: 'Downtown → Airport', us: 28.50, uber: 32.00, lyft: 30.50, status: 'competitive' },
  { route: 'Airport → Downtown', us: 26.40, uber: 29.00, lyft: 27.50, status: 'competitive' },
  { route: 'Midtown → Stadium', us: 18.65, uber: 16.50, lyft: 17.00, status: 'undercut' },
  { route: 'University → Mall', us: 12.34, uber: 14.00, lyft: 13.50, status: 'winning' },
  { route: 'Beach → Downtown', us: 15.89, uber: 18.00, lyft: 17.50, status: 'winning' },
];

const priceComparison = [
  { time: 'Mon', us: 145, uber: 152, lyft: 148 },
  { time: 'Tue', us: 148, uber: 155, lyft: 151 },
  { time: 'Wed', us: 142, uber: 148, lyft: 145 },
  { time: 'Thu', us: 155, uber: 162, lyft: 158 },
  { time: 'Fri', us: 172, uber: 180, lyft: 176 },
  { time: 'Sat', us: 188, uber: 195, lyft: 192 },
  { time: 'Sun', us: 165, uber: 172, lyft: 168 },
];

const marketShare = [
  { competitor: 'Us', share: 28, rides: 1291, color: '#8b5cf6' },
  { competitor: 'Uber', share: 42, rides: 1935, color: '#3b82f6' },
  { competitor: 'Lyft', share: 30, rides: 1382, color: '#10b981' },
];

const competitorPromotions = [
  {
    competitor: 'Uber',
    promotion: '20% off first 3 rides',
    startDate: 'Dec 1',
    endDate: 'Dec 15',
    impact: 'High',
    status: 'active',
  },
  {
    competitor: 'Lyft',
    promotion: 'Free ride up to $15',
    startDate: 'Dec 5',
    endDate: 'Dec 10',
    impact: 'Medium',
    status: 'active',
  },
  {
    competitor: 'Uber',
    promotion: 'Premium rides -30%',
    startDate: 'Dec 10',
    endDate: 'Dec 20',
    impact: 'Low',
    status: 'upcoming',
  },
];

export function CompetitorTab() {
  return (
    <div className="space-y-6">
      {/* Market Share Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {marketShare.map((item) => (
          <Card key={item.competitor}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium">
                  {item.competitor}
                </CardTitle>
                <Users size={20} style={{ color: item.color }} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold mb-2">{item.share}%</div>
              <p className="text-sm text-muted-foreground">
                {item.rides.toLocaleString()} rides/week
              </p>
              <div className="mt-3 w-full bg-muted rounded-full h-2">
                <div
                  className="h-2 rounded-full"
                  style={{ width: `${item.share}%`, backgroundColor: item.color }}
                />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Price Comparison Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Average Price Comparison (Weekly)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={priceComparison}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis
                dataKey="time"
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
              />
              <YAxis
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickFormatter={(value) => `$${value}`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
                formatter={(value: any) => formatCurrency(value)}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="us"
                stroke="#8b5cf6"
                strokeWidth={3}
                name="Us"
                dot={{ fill: '#8b5cf6' }}
              />
              <Line
                type="monotone"
                dataKey="uber"
                stroke="#3b82f6"
                strokeWidth={2}
                name="Uber"
                dot={{ fill: '#3b82f6' }}
              />
              <Line
                type="monotone"
                dataKey="lyft"
                stroke="#10b981"
                strokeWidth={2}
                name="Lyft"
                dot={{ fill: '#10b981' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Route-by-Route Comparison */}
      <Card>
        <CardHeader>
          <CardTitle>Route-by-Route Price Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                    Route
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">
                    Us
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">
                    Uber
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">
                    Lyft
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-medium text-muted-foreground">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                {competitorPrices.map((route, index) => (
                  <tr key={index} className="border-b border-border last:border-0">
                    <td className="py-3 px-4 text-sm font-medium">
                      {route.route}
                    </td>
                    <td className="py-3 px-4 text-sm text-right font-bold text-primary">
                      {formatCurrency(route.us)}
                    </td>
                    <td className="py-3 px-4 text-sm text-right">
                      {formatCurrency(route.uber)}
                    </td>
                    <td className="py-3 px-4 text-sm text-right">
                      {formatCurrency(route.lyft)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <Badge
                        variant={
                          route.status === 'winning'
                            ? 'success'
                            : route.status === 'undercut'
                            ? 'destructive'
                            : 'secondary'
                        }
                      >
                        {route.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Competitor Promotions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Competitor Promotions</CardTitle>
            <Badge variant="warning">2 Active</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {competitorPromotions.map((promo, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-accent transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div
                    className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                      promo.status === 'active'
                        ? 'bg-red-500/10'
                        : 'bg-muted'
                    }`}
                  >
                    <AlertCircle
                      size={24}
                      className={
                        promo.status === 'active'
                          ? 'text-red-500'
                          : 'text-muted-foreground'
                      }
                    />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium">{promo.competitor}</h4>
                      <Badge
                        variant={promo.status === 'active' ? 'destructive' : 'secondary'}
                      >
                        {promo.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{promo.promotion}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {promo.startDate} - {promo.endDate}
                    </p>
                  </div>
                </div>
                <Badge
                  variant={
                    promo.impact === 'High'
                      ? 'destructive'
                      : promo.impact === 'Medium'
                      ? 'warning'
                      : 'secondary'
                  }
                >
                  {promo.impact} Impact
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Competitive Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Undercut Warnings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle size={20} className="text-red-500" />
                  <h4 className="font-medium">Midtown → Stadium</h4>
                </div>
                <p className="text-sm text-muted-foreground mb-2">
                  Uber is $2.15 cheaper. Losing 15% of potential customers.
                </p>
                <Badge variant="destructive">Action Required</Badge>
              </div>

              <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle size={20} className="text-yellow-500" />
                  <h4 className="font-medium">Airport → Downtown</h4>
                </div>
                <p className="text-sm text-muted-foreground mb-2">
                  Lyft is $1.10 cheaper. Monitor for changes.
                </p>
                <Badge variant="warning">Monitor</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>AI Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <h4 className="font-medium mb-2 text-blue-600 dark:text-blue-400">
                  Pricing Strategy
                </h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Reduce Midtown → Stadium price by $1.50 to match Uber</li>
                  <li>• Maintain premium pricing on winning routes</li>
                  <li>• Counter Uber's promotion with loyalty rewards</li>
                </ul>
              </div>

              <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                <h4 className="font-medium mb-2 text-green-600 dark:text-green-400">
                  Expected Impact
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Market Share</span>
                    <span className="font-medium text-green-500">+3.2%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Weekly Revenue</span>
                    <span className="font-medium text-green-500">+$4,800</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Customer Retention</span>
                    <span className="font-medium text-green-500">+8%</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

