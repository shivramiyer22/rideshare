'use client';

import React, { useEffect, useState } from 'react';
import {
  DollarSign,
  TrendingUp,
  Users,
  Car,
  ArrowUp,
  ArrowDown,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { analyticsAPI } from '@/lib/api';
import { formatCurrency, formatNumber, formatPercentage } from '@/lib/utils';

// Mock data (replace with API calls)
const revenueData = [
  { date: 'Mon', revenue: 12400, rides: 145 },
  { date: 'Tue', revenue: 13200, rides: 152 },
  { date: 'Wed', revenue: 11800, rides: 138 },
  { date: 'Thu', revenue: 14500, rides: 168 },
  { date: 'Fri', revenue: 18900, rides: 215 },
  { date: 'Sat', revenue: 22100, rides: 248 },
  { date: 'Sun', revenue: 19800, rides: 225 },
];

const customerDistribution = [
  { name: 'Gold', value: 28, color: '#3E4C59' },
  { name: 'Silver', value: 42, color: '#5B7C99' },
  { name: 'Bronze', value: 30, color: '#70AD47' },
];

const topRoutes = [
  { route: 'Downtown → Airport', rides: 342, revenue: 28450 },
  { route: 'Airport → Downtown', rides: 318, revenue: 26420 },
  { route: 'Midtown → Stadium', rides: 245, revenue: 18650 },
  { route: 'University → Mall', rides: 198, revenue: 12340 },
  { route: 'Beach → Downtown', rides: 176, revenue: 15890 },
];

interface KPICardProps {
  title: string;
  value: string;
  change: number;
  icon: React.ReactNode;
  trend?: 'up' | 'down';
}

function KPICard({ title, value, change, icon, trend = 'up' }: KPICardProps) {
  const isPositive = change >= 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div style={{ color: '#70AD47' }}>{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <div className="flex items-center gap-1 mt-1">
          {isPositive ? (
            <ArrowUp size={14} className="text-green-500" />
          ) : (
            <ArrowDown size={14} className="text-red-500" />
          )}
          <span
            className={`text-xs ${
              isPositive ? 'text-green-500' : 'text-red-500'
            }`}
          >
            {Math.abs(change)}%
          </span>
          <span className="text-xs text-muted-foreground">vs last week</span>
        </div>
      </CardContent>
    </Card>
  );
}

export function OverviewTab() {
  const [loading, setLoading] = useState(false);

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Revenue"
          value="$112.8K"
          change={15.3}
          icon={<DollarSign size={20} />}
        />
        <KPICard
          title="Avg. Margin"
          value="3.4%"
          change={0.8}
          icon={<TrendingUp size={20} />}
        />
        <KPICard
          title="Total Rides"
          value="1,291"
          change={12.5}
          icon={<Car size={20} />}
        />
        <KPICard
          title="Active Customers"
          value="847"
          change={8.2}
          icon={<Users size={20} />}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Trend */}
        <Card>
          <CardHeader>
            <CardTitle>Revenue & Rides Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="date"
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                />
                <YAxis
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  tickFormatter={(value) => `$${value / 1000}k`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                  formatter={(value: any, name: string) =>
                    name === 'revenue'
                      ? formatCurrency(value)
                      : formatNumber(value)
                  }
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="revenue"
                  stroke="#5B9BD5"
                  strokeWidth={2}
                  dot={{ fill: '#5B9BD5' }}
                />
                <Line
                  type="monotone"
                  dataKey="rides"
                  stroke="#70AD47"
                  strokeWidth={2}
                  dot={{ fill: '#70AD47' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Customer Distribution */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Customer Distribution</CardTitle>
              <select 
                className="text-sm text-white rounded px-3 py-1.5 border-none outline-none cursor-pointer [&>option]:bg-[#5B7C99] [&>option]:text-white [&>option:hover]:bg-[#4E6370]"
                style={{ background: 'linear-gradient(135deg, #3E4C59 0%, #6B8AA8 100%)' }}
              >
                <option>This Month</option>
                <option>Last Month</option>
                <option>Last 3 Months</option>
                <option>Last 6 Months</option>
                <option>This Year</option>
              </select>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-8">
              {/* Donut Chart */}
              <div className="flex-shrink-0">
                <ResponsiveContainer width={220} height={220}>
                  <PieChart>
                    <defs>
                      <linearGradient id="goldGradient" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stopColor="#2E3C49" />
                        <stop offset="50%" stopColor="#3E4C59" />
                        <stop offset="100%" stopColor="#4E5C69" />
                      </linearGradient>
                      <linearGradient id="silverGradient" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stopColor="#4B6C89" />
                        <stop offset="50%" stopColor="#5B7C99" />
                        <stop offset="100%" stopColor="#6B8CA9" />
                      </linearGradient>
                      <linearGradient id="bronzeGradient" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stopColor="#609D37" />
                        <stop offset="50%" stopColor="#70AD47" />
                        <stop offset="100%" stopColor="#80BD57" />
                      </linearGradient>
                    </defs>
                    <Pie
                      data={customerDistribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      fill="#8884d8"
                      dataKey="value"
                      label={false}
                    >
                      {customerDistribution.map((entry, index) => {
                        const gradientMap: { [key: string]: string } = {
                          'Gold': 'url(#goldGradient)',
                          'Silver': 'url(#silverGradient)',
                          'Bronze': 'url(#bronzeGradient)'
                        };
                        return (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={gradientMap[entry.name] || entry.color}
                            style={{ filter: 'drop-shadow(0px 2px 4px rgba(0,0,0,0.2))' }}
                          />
                        );
                      })}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#455A64',
                        border: 'none',
                        borderRadius: '8px',
                        color: 'white',
                        padding: '8px 12px',
                      }}
                      labelStyle={{
                        color: 'white',
                        fontWeight: 'bold',
                      }}
                      itemStyle={{
                        color: 'white',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Legend on the side */}
              <div className="flex-1 space-y-3">
                {customerDistribution.map((entry, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: entry.color }}
                      />
                      <span className="text-sm font-medium">{entry.name}</span>
                    </div>
                    <span className="text-sm font-semibold">{entry.value}%</span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Routes Table */}
      <Card>
        <CardHeader>
          <CardTitle>Top 5 Routes by Revenue</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto -mx-6 px-6 md:mx-0 md:px-0">
            <table className="w-full min-w-[600px]">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 text-sm font-medium text-primary">
                    Route
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-primary">
                    Rides
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-primary">
                    Revenue
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-primary">
                    Avg/Ride
                  </th>
                </tr>
              </thead>
              <tbody>
                {topRoutes.map((route, index) => (
                  <tr key={index} className="border-b border-border last:border-0">
                    <td className="py-3 px-4 text-sm font-medium">
                      {route.route}
                    </td>
                    <td className="py-3 px-4 text-sm text-right">
                      {formatNumber(route.rides)}
                    </td>
                    <td className="py-3 px-4 text-sm text-right font-medium" style={{ color: '#70AD47' }}>
                      {formatCurrency(route.revenue)}
                    </td>
                    <td className="py-3 px-4 text-sm text-right" style={{ color: '#8BC34A' }}>
                      {formatCurrency(route.revenue / route.rides)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Surge Zones Heatmap Preview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Active Surge Zones</CardTitle>
            <Badge variant="warning">3 Active</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Downtown</span>
                <Badge variant="destructive">2.0x</Badge>
              </div>
              <p className="text-xs text-muted-foreground">
                High demand • 45 active rides
              </p>
            </div>
            <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Airport</span>
                <Badge variant="warning">1.6x</Badge>
              </div>
              <p className="text-xs text-muted-foreground">
                Moderate demand • 28 active rides
              </p>
            </div>
            <div className="p-4 rounded-lg bg-orange-500/10 border border-orange-500/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Stadium</span>
                <Badge variant="warning">1.4x</Badge>
              </div>
              <p className="text-xs text-muted-foreground">
                Event surge • 32 active rides
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

