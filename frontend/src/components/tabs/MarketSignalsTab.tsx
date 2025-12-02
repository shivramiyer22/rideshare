'use client';

import React, { useState } from 'react';
import { Radio, Calendar, Cloud, Newspaper, AlertTriangle, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { formatDateTime } from '@/lib/utils';

const liveSignals = [
  {
    id: 1,
    type: 'event',
    title: 'Lakers Playoff Game',
    location: 'Staples Center',
    time: '7:00 PM',
    impact: 'high',
    demandIncrease: '+45%',
    icon: Calendar,
    color: 'text-red-500',
  },
  {
    id: 2,
    type: 'traffic',
    title: 'Heavy Traffic',
    location: 'Downtown to Airport',
    time: 'Now',
    impact: 'medium',
    demandIncrease: '+25%',
    icon: AlertTriangle,
    color: 'text-yellow-500',
  },
  {
    id: 3,
    type: 'weather',
    title: 'Clear Skies',
    location: 'Citywide',
    time: 'All Day',
    impact: 'low',
    demandIncrease: '+5%',
    icon: Cloud,
    color: 'text-blue-500',
  },
  {
    id: 4,
    type: 'news',
    title: 'Rideshare Strike Announced',
    location: 'Competitor',
    time: '2 hours ago',
    impact: 'high',
    demandIncrease: '+60%',
    icon: Newspaper,
    color: 'text-purple-500',
  },
];

const newsArticles = [
  {
    id: 1,
    title: 'Uber announces price increase in major cities',
    source: 'TechCrunch',
    time: '3 hours ago',
    sentiment: 'neutral',
    relevance: 'high',
  },
  {
    id: 2,
    title: 'Lyft drivers plan weekend strike',
    source: 'Reuters',
    time: '5 hours ago',
    sentiment: 'negative',
    relevance: 'high',
  },
  {
    id: 3,
    title: 'Gas prices drop 10% this week',
    source: 'Bloomberg',
    time: '1 day ago',
    sentiment: 'positive',
    relevance: 'medium',
  },
];

const upcomingEvents = [
  {
    id: 1,
    name: 'Lakers vs Warriors',
    venue: 'Staples Center',
    date: 'Friday, 7:00 PM',
    attendance: '20,000',
    predictedImpact: '+45%',
  },
  {
    id: 2,
    name: 'Tech Conference',
    venue: 'Convention Center',
    date: 'Saturday, 9:00 AM',
    attendance: '15,000',
    predictedImpact: '+35%',
  },
  {
    id: 3,
    name: 'Music Festival',
    venue: 'Beach Park',
    date: 'Sunday, 2:00 PM',
    attendance: '30,000',
    predictedImpact: '+55%',
  },
];

const trafficData = [
  {
    route: 'Downtown → Airport',
    status: 'Heavy',
    duration: '45 min',
    normal: '25 min',
    delay: '+20 min',
    color: 'bg-red-500',
  },
  {
    route: 'Midtown → Stadium',
    status: 'Moderate',
    duration: '18 min',
    normal: '15 min',
    delay: '+3 min',
    color: 'bg-yellow-500',
  },
  {
    route: 'Beach → Downtown',
    status: 'Light',
    duration: '22 min',
    normal: '20 min',
    delay: '+2 min',
    color: 'bg-green-500',
  },
];

export function MarketSignalsTab() {
  return (
    <div className="space-y-6">
      {/* Live Signals Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {liveSignals.map((signal) => {
          const Icon = signal.icon;
          return (
            <Card key={signal.id} className="hover:shadow-lg transition-shadow">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between mb-3">
                  <Icon size={24} className={signal.color} />
                  <Badge
                    variant={
                      signal.impact === 'high'
                        ? 'destructive'
                        : signal.impact === 'medium'
                        ? 'warning'
                        : 'secondary'
                    }
                  >
                    {signal.impact}
                  </Badge>
                </div>
                <h3 className="font-semibold mb-1">{signal.title}</h3>
                <p className="text-sm text-muted-foreground mb-2">
                  {signal.location}
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">{signal.time}</span>
                  <span className="text-sm font-medium text-green-500">
                    {signal.demandIncrease}
                  </span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Traffic Conditions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Real-Time Traffic Conditions</CardTitle>
            <Badge variant="success">Live</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {trafficData.map((traffic, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-4 bg-accent rounded-lg"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-3 rounded-full ${traffic.color}`} />
                  <div>
                    <p className="font-medium">{traffic.route}</p>
                    <p className="text-sm text-muted-foreground">
                      {traffic.status} congestion
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-medium">{traffic.duration}</p>
                  <p className="text-sm text-red-500">{traffic.delay}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Upcoming Events */}
      <Card>
        <CardHeader>
          <CardTitle>Upcoming Events</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {upcomingEvents.map((event) => (
              <div
                key={event.id}
                className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-accent transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Calendar size={24} className="text-primary" />
                  </div>
                  <div>
                    <h4 className="font-medium">{event.name}</h4>
                    <p className="text-sm text-muted-foreground">{event.venue}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {event.date} • {event.attendance} attendees
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <Badge variant="success">{event.predictedImpact}</Badge>
                  <p className="text-xs text-muted-foreground mt-1">demand</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* News & Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Industry News</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {newsArticles.map((article) => (
                <div
                  key={article.id}
                  className="p-4 border border-border rounded-lg hover:bg-accent transition-colors cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-medium text-sm flex-1">{article.title}</h4>
                    <Badge
                      variant={
                        article.sentiment === 'positive'
                          ? 'success'
                          : article.sentiment === 'negative'
                          ? 'destructive'
                          : 'secondary'
                      }
                      className="ml-2"
                    >
                      {article.sentiment}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{article.source}</span>
                    <span>{article.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Signal Impact Scoring</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Events</span>
                  <span className="text-sm font-bold text-red-500">High Impact</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div className="bg-red-500 h-2 rounded-full" style={{ width: '85%' }} />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Traffic</span>
                  <span className="text-sm font-bold text-yellow-500">Medium Impact</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div className="bg-yellow-500 h-2 rounded-full" style={{ width: '60%' }} />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Weather</span>
                  <span className="text-sm font-bold text-green-500">Low Impact</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div className="bg-green-500 h-2 rounded-full" style={{ width: '25%' }} />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">News</span>
                  <span className="text-sm font-bold text-red-500">High Impact</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div className="bg-red-500 h-2 rounded-full" style={{ width: '75%' }} />
                </div>
              </div>
            </div>

            <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <h4 className="font-medium mb-2 text-blue-600 dark:text-blue-400">
                AI Recommendation
              </h4>
              <p className="text-sm text-muted-foreground">
                Multiple high-impact signals detected. Recommend increasing surge
                pricing by 1.7x in affected zones. Expected revenue increase: +$12,400
                over the weekend.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

