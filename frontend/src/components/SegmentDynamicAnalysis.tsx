import React, { useState, useMemo, useEffect } from 'react';
import { Search, TrendingUp, TrendingDown, DollarSign, Users, Target, Filter, Download, BarChart3, ChevronUp, ChevronDown } from 'lucide-react';

// ============================================================================
// API CONFIGURATION
// ============================================================================
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const API_ENDPOINTS = {
  segments: `${API_BASE}/api/v1/reports/segment-dynamic-pricing-analysis`,
  businessObjectives: `${API_BASE}/api/v1/analytics/pricing-strategies?filter_by=business_objectives`,
  recommendations: `${API_BASE}/api/v1/analytics/pricing-strategies?filter_by=pipeline_results&include_pipeline_data=true`,
};

// ============================================================================
// MODULE-LEVEL CACHE (persists across component mounts/unmounts)
// ============================================================================
let cachedData: {
  segments: any[];
  businessObjectives: any[];
  recommendations: any[];
  timestamp: number;
} | null = null;

const CACHE_DURATION = 1000 * 60 * 60; // 1 hour - cache expires after 1 hour

// ============================================================================
// Type definitions
// ============================================================================
interface SegmentData {
  segment: {
    location_category: string;
    loyalty_tier: string;
    vehicle_type: string;
    demand_profile: string;
    pricing_model: string;
  };
  hwco_continue_current: {
    rides_30d: number;
    unit_price: number;
    duration_minutes: number;
    revenue_30d: number;
    explanation: string;
  };
  lyft_continue_current: {
    rides_30d: number;
    unit_price: number;
    duration_minutes: number;
    revenue_30d: number;
    explanation: string;
  };
  recommendation_1: {
    rides_30d: number;
    unit_price: number;
    duration_minutes: number;
    revenue_30d: number;
    explanation: string;
  };
  recommendation_2: {
    rides_30d: number;
    unit_price: number;
    duration_minutes: number;
    revenue_30d: number;
    explanation: string;
  };
  recommendation_3: {
    rides_30d: number;
    unit_price: number;
    duration_minutes: number;
    revenue_30d: number;
    explanation: string;
  };
}

interface Segment {
  location_category: string;
  loyalty_tier: string;
  vehicle_type: string;
  demand_profile: string;
  pricing_model: string;
  hwco_rides_30d: number;
  hwco_unit_price: number;
  hwco_duration_minutes: number;
  hwco_revenue_30d: number;
  hwco_explanation: string;
  lyft_rides_30d: number;
  lyft_unit_price: number;
  lyft_duration_minutes: number;
  lyft_revenue_30d: number;
  lyft_explanation: string;
  rec1_rides_30d: number;
  rec1_unit_price: number;
  rec1_duration_minutes: number;
  rec1_revenue_30d: number;
  rec1_explanation: string;
  rec2_rides_30d: number;
  rec2_unit_price: number;
  rec2_duration_minutes: number;
  rec2_revenue_30d: number;
  rec2_explanation: string;
  rec3_rides_30d: number;
  rec3_unit_price: number;
  rec3_duration_minutes: number;
  rec3_revenue_30d: number;
  rec3_explanation: string;
}

interface BusinessObjective {
  name: string;
  target: string;
  metric: string;
  priority: string;
}

interface Filters {
  location: string;
  loyalty: string;
  vehicle: string;
  demand: string;
  pricing: string;
}

type ScenarioType = 'hwco' | 'lyft' | 'rec1' | 'rec2' | 'rec3';

const SegmentDynamicAnalysis: React.FC = () => {
  const [segments, setSegments] = useState<Segment[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<ScenarioType>('hwco');
  const [filters, setFilters] = useState<Filters>({
    location: 'all',
    loyalty: 'all',
    vehicle: 'all',
    demand: 'all',
    pricing: 'all'
  });
  const [searchTerm, setSearchTerm] = useState('');

  const [businessObjectives, setBusinessObjectives] = useState<BusinessObjective[]>([]);
  const [recommendations, setRecommendations] = useState<Array<{id: string; name: string; impact: string}>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataLoaded, setDataLoaded] = useState(false); // Track if data has been loaded

  // Pagination state for table
  const [displayLimit] = useState(25); // Show 25 rows at a time
  const [currentPage, setCurrentPage] = useState(0); // Current page index

  // Transform API segment data to flat structure
  const transformSegmentData = (apiSegment: SegmentData): Segment => {
    return {
      location_category: apiSegment.segment.location_category,
      loyalty_tier: apiSegment.segment.loyalty_tier,
      vehicle_type: apiSegment.segment.vehicle_type,
      demand_profile: apiSegment.segment.demand_profile,
      pricing_model: apiSegment.segment.pricing_model,
      hwco_rides_30d: apiSegment.hwco_continue_current.rides_30d,
      hwco_unit_price: apiSegment.hwco_continue_current.unit_price,
      hwco_duration_minutes: apiSegment.hwco_continue_current.duration_minutes,
      hwco_revenue_30d: apiSegment.hwco_continue_current.revenue_30d,
      hwco_explanation: apiSegment.hwco_continue_current.explanation,
      lyft_rides_30d: apiSegment.lyft_continue_current.rides_30d,
      lyft_unit_price: apiSegment.lyft_continue_current.unit_price,
      lyft_duration_minutes: apiSegment.lyft_continue_current.duration_minutes,
      lyft_revenue_30d: apiSegment.lyft_continue_current.revenue_30d,
      lyft_explanation: apiSegment.lyft_continue_current.explanation,
      rec1_rides_30d: apiSegment.recommendation_1.rides_30d,
      rec1_unit_price: apiSegment.recommendation_1.unit_price,
      rec1_duration_minutes: apiSegment.recommendation_1.duration_minutes,
      rec1_revenue_30d: apiSegment.recommendation_1.revenue_30d,
      rec1_explanation: apiSegment.recommendation_1.explanation,
      rec2_rides_30d: apiSegment.recommendation_2.rides_30d,
      rec2_unit_price: apiSegment.recommendation_2.unit_price,
      rec2_duration_minutes: apiSegment.recommendation_2.duration_minutes,
      rec2_revenue_30d: apiSegment.recommendation_2.revenue_30d,
      rec2_explanation: apiSegment.recommendation_2.explanation,
      rec3_rides_30d: apiSegment.recommendation_3.rides_30d,
      rec3_unit_price: apiSegment.recommendation_3.unit_price,
      rec3_duration_minutes: apiSegment.recommendation_3.duration_minutes,
      rec3_revenue_30d: apiSegment.recommendation_3.revenue_30d,
      rec3_explanation: apiSegment.recommendation_3.explanation,
    };
  };

  // Load data from API endpoints (with persistent caching across component mounts)
  useEffect(() => {
    const loadData = async () => {
      try {
        // Check if we have valid cached data
        if (cachedData && (Date.now() - cachedData.timestamp < CACHE_DURATION)) {
          console.log('📦 Using cached segment data - no API calls needed');
          setSegments(cachedData.segments);
          setBusinessObjectives(cachedData.businessObjectives);
          setRecommendations(cachedData.recommendations);
          setDataLoaded(true);
          setLoading(false);
          return;
        }

        console.log('🔄 Fetching fresh segment data from API...');
        setLoading(true);
        
        // Fetch segments data
        const segmentsRes = await fetch(API_ENDPOINTS.segments);
        if (!segmentsRes.ok) throw new Error('Failed to fetch segments');
        const segmentsData = await segmentsRes.json();
        
        // Transform nested structure to flat structure
        const rawSegments = segmentsData.segments || [];
        const transformedSegments = rawSegments.map((seg: SegmentData) => transformSegmentData(seg));

        // Fetch business objectives
        const objectivesRes = await fetch(API_ENDPOINTS.businessObjectives);
        if (!objectivesRes.ok) throw new Error('Failed to fetch objectives');
        const objectivesData = await objectivesRes.json();
        const objectives = objectivesData.strategies || objectivesData;

        // Fetch recommendations
        const recsRes = await fetch(API_ENDPOINTS.recommendations);
        if (!recsRes.ok) throw new Error('Failed to fetch recommendations');
        const recsData = await recsRes.json();
        
        // Parse recommendations from pipeline data
        let parsedRecommendations: Array<{id: string; name: string; impact: string}> = [];
        if (recsData.strategies && Array.isArray(recsData.strategies)) {
          const pipelineResult = recsData.strategies.find((s: any) => s.type === 'pipeline_result');
          if (pipelineResult && pipelineResult.recommendations) {
            const top3 = pipelineResult.recommendations.recommendations || [];
            parsedRecommendations = top3.slice(0, 3).map((rec: any, idx: number) => ({
              id: `rec${idx + 1}`,
              name: rec.name || `Recommendation ${idx + 1}`,
              impact: rec.estimated_impact ? `+${rec.estimated_impact.toFixed(1)}% revenue` : 'Impact analysis pending'
            }));
          } else {
            // Fallback if no pipeline results yet
            parsedRecommendations = [
              { id: 'rec1', name: 'Run pipeline to generate', impact: 'No data' },
              { id: 'rec2', name: 'Run pipeline to generate', impact: 'No data' },
              { id: 'rec3', name: 'Run pipeline to generate', impact: 'No data' }
            ];
          }
        }

        // Update state
        setSegments(transformedSegments);
        setBusinessObjectives(objectives);
        setRecommendations(parsedRecommendations);

        // Cache the data at module level (persists across component unmounts)
        cachedData = {
          segments: transformedSegments,
          businessObjectives: objectives,
          recommendations: parsedRecommendations,
          timestamp: Date.now()
        };

        console.log('✅ Segment data cached successfully - will persist for entire session');
        setDataLoaded(true);
        setLoading(false);
      } catch (err) {
        console.error('Error loading data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
        setLoading(false);
      }
    };

    loadData();
  }, []); // Empty dependency array - only run once on mount

  // Filter segments based on current filters
  const filteredSegments = useMemo(() => {
    return segments.filter(segment => {
      const matchesLocation = filters.location === 'all' || segment.location_category === filters.location;
      const matchesLoyalty = filters.loyalty === 'all' || segment.loyalty_tier === filters.loyalty;
      const matchesVehicle = filters.vehicle === 'all' || segment.vehicle_type === filters.vehicle;
      const matchesDemand = filters.demand === 'all' || segment.demand_profile === filters.demand;
      const matchesPricing = filters.pricing === 'all' || segment.pricing_model === filters.pricing;
      
      const matchesSearch = searchTerm === '' || 
        Object.values(segment).some(val => 
          String(val).toLowerCase().includes(searchTerm.toLowerCase())
        );

      return matchesLocation && matchesLoyalty && matchesVehicle && matchesDemand && matchesPricing && matchesSearch;
    });
  }, [segments, filters, searchTerm]);

  // Calculate pagination
  const totalPages = Math.ceil(filteredSegments.length / displayLimit);
  const startIdx = currentPage * displayLimit;
  const endIdx = Math.min(startIdx + displayLimit, filteredSegments.length);
  
  // Display current page of segments
  const displayedSegments = useMemo(() => {
    return filteredSegments.slice(startIdx, endIdx);
  }, [filteredSegments, startIdx, endIdx]);

  // Reset to page 0 when filters change
  useEffect(() => {
    setCurrentPage(0);
  }, [filteredSegments.length]);

  // Pagination handlers
  const handlePageUp = () => {
    setCurrentPage(prev => Math.max(0, prev - 1));
  };

  const handlePageDown = () => {
    setCurrentPage(prev => Math.min(totalPages - 1, prev + 1));
  };

  // Calculate aggregate metrics for ALL scenarios at once (memoized for performance)
  const scenarioMetricsCache = useMemo(() => {
    const scenarios: ScenarioType[] = ['hwco', 'lyft', 'rec1', 'rec2', 'rec3'];
    const cache: Record<ScenarioType, { totalRevenue: number; totalRides: number; avgUnitPrice: number; avgDuration: number }> = {} as any;
    
    scenarios.forEach(scenario => {
      const totalRevenue = filteredSegments.reduce((sum, seg) => sum + seg[`${scenario}_revenue_30d`], 0);
      const totalRides = filteredSegments.reduce((sum, seg) => sum + seg[`${scenario}_rides_30d`], 0);
      const avgUnitPrice = filteredSegments.reduce((sum, seg) => sum + seg[`${scenario}_unit_price`], 0) / (filteredSegments.length || 1);
      const avgDuration = filteredSegments.reduce((sum, seg) => sum + seg[`${scenario}_duration_minutes`], 0) / (filteredSegments.length || 1);
      
      cache[scenario] = { totalRevenue, totalRides, avgUnitPrice, avgDuration };
    });
    
    return cache;
  }, [filteredSegments]);

  // Fast metrics lookup from cache
  const calculateMetrics = (scenario: ScenarioType) => {
    return scenarioMetricsCache[scenario];
  };

  // Calculate objective performance
  const calculateObjectivePerformance = (scenario: ScenarioType) => {
    const hwcoMetrics = calculateMetrics('hwco');
    const scenarioMetrics = calculateMetrics(scenario);
    const lyftMetrics = calculateMetrics('lyft');

    const revenueGrowth = ((scenarioMetrics.totalRevenue - hwcoMetrics.totalRevenue) / hwcoMetrics.totalRevenue) * 100;
    const profitMargin = ((scenarioMetrics.avgUnitPrice - 2.5) / scenarioMetrics.avgUnitPrice) * 100; // Assuming $2.5 cost
    const lyftGap = lyftMetrics.totalRevenue > 0 
      ? ((lyftMetrics.totalRevenue - scenarioMetrics.totalRevenue) / lyftMetrics.totalRevenue) * 100
      : 0;
    const retentionImprovement = scenario === 'rec2' ? 12 : (scenario === 'rec1' ? 5 : 8);

    return {
      revenue: { value: revenueGrowth, target: 20, achieved: revenueGrowth >= 15 },
      margin: { value: profitMargin, target: 40, achieved: profitMargin >= 40 },
      competitive: { value: lyftGap, target: 5, achieved: lyftGap <= 5 },
      retention: { value: retentionImprovement, target: 12.5, achieved: retentionImprovement >= 10 }
    };
  };

  const currentMetrics = calculateMetrics(selectedScenario);
  const hwcoMetrics = calculateMetrics('hwco');
  const objectivePerformance = calculateObjectivePerformance(selectedScenario);

  // Export filtered data
  const handleExport = () => {
    const csv = [
      Object.keys(filteredSegments[0] || {}).join(','),
      ...filteredSegments.map(seg => Object.values(seg).join(','))
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `segment-analysis-${selectedScenario}-${new Date().toISOString()}.csv`;
    a.click();
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center max-w-md">
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-6">
            <h2 className="text-xl font-bold text-destructive mb-2">Error Loading Data</h2>
            <p className="text-destructive/80 mb-4">{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="px-4 py-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <header className="bg-card border-b border-border px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Segment Dynamic Pricing Analysis</h1>
            <p className="text-sm text-muted-foreground mt-1">HWCO Rideshare - Revenue Optimization Dashboard</p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleExport}
              className="flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition"
            >
              <Download className="w-4 h-4 mr-2" />
              Export Data
            </button>
          </div>
        </div>
      </header>

      {/* Business Objectives Overview */}
      <div className="bg-card border-b border-border px-6 py-4">
        <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center">
          <Target className="w-5 h-5 mr-2 text-primary" />
          Business Objectives Performance
        </h2>
          <div className="grid grid-cols-4 gap-4">
            {businessObjectives.map((obj, idx) => {
              const perfKey = ['revenue', 'margin', 'competitive', 'retention'][idx] as keyof typeof objectivePerformance;
              const perf = objectivePerformance[perfKey];
              
              return (
                <div key={obj.name} className="bg-gradient-to-br from-accent to-accent/50 rounded-lg p-4 border border-border">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <p className="text-xs font-medium text-muted-foreground uppercase">{obj.name}</p>
                      <p className="text-xs text-muted-foreground mt-1">{obj.target}</p>
                    </div>
                    <span className={`px-2 py-1 text-xs font-semibold rounded ${
                      obj.priority === 'HIGH' ? 'bg-destructive/10 text-destructive' : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {obj.priority}
                    </span>
                  </div>
                  <div className="mt-3">
                    <div className="flex items-baseline">
                      <span className={`text-2xl font-bold ${perf.achieved ? 'text-green-600' : 'text-orange-600'}`}>
                        {perf.value.toFixed(1)}%
                      </span>
                      {perf.achieved ? (
                        <TrendingUp className="w-5 h-5 ml-2 text-green-600" />
                      ) : (
                        <TrendingDown className="w-5 h-5 ml-2 text-orange-600" />
                      )}
                    </div>
                    <div className="mt-2 bg-muted rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full transition-all ${perf.achieved ? 'bg-green-500' : 'bg-orange-500'}`}
                        style={{ width: `${Math.min(100, (perf.value / perf.target) * 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      {/* Scenario Comparison & Top Recommendations */}
      <div className="bg-card border-b border-border px-6 py-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-foreground flex items-center">
            <BarChart3 className="w-5 h-5 mr-2 text-primary" />
            Scenario Comparison
          </h2>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-muted-foreground">Top 3 Recommendations:</span>
            {recommendations.map(rec => (
              <span key={rec.id} className="px-3 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                {rec.name} → {rec.impact}
              </span>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-5 gap-3">
          {['hwco', 'lyft', 'rec1', 'rec2', 'rec3'].map((scenario) => {
            const metrics = calculateMetrics(scenario as ScenarioType);
            const revenueVsHwco = scenario === 'hwco' ? 0 : 
              ((metrics.totalRevenue - hwcoMetrics.totalRevenue) / hwcoMetrics.totalRevenue) * 100;
            const isSelected = selectedScenario === scenario;
            
            return (
              <button
                key={scenario}
                onClick={() => setSelectedScenario(scenario as ScenarioType)}
                className={`p-4 rounded-lg border-2 transition-all text-left ${
                  isSelected 
                    ? 'border-primary bg-accent shadow-md' 
                    : 'border-border bg-card hover:border-primary/50'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold text-foreground uppercase">
                      {scenario === 'hwco' ? 'HWCO Current' : 
                       scenario === 'lyft' ? 'Lyft Current' : 
                       scenario.replace('rec', 'Rec #')}
                    </span>
                    {revenueVsHwco !== 0 && (
                      <span className={`text-xs font-bold ${revenueVsHwco > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {revenueVsHwco > 0 ? '+' : ''}{revenueVsHwco.toFixed(1)}%
                      </span>
                    )}
                  </div>
                <div className="space-y-1">
                  <div>
                    <p className="text-xs text-muted-foreground">Revenue (30d)</p>
                    <p className="text-lg font-bold text-foreground">${(metrics.totalRevenue / 1000).toFixed(1)}K</p>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <p className="text-muted-foreground">Rides</p>
                      <p className="font-semibold text-foreground">{metrics.totalRides.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Avg Price</p>
                      <p className="font-semibold text-foreground">${metrics.avgUnitPrice.toFixed(2)}</p>
                    </div>
                  </div>
                </div>
                </button>
              );
            })}
          </div>
        </div>

      {/* Filters */}
      <div className="bg-card border-b border-border px-6 py-4">
        <div className="flex items-center space-x-4">
          <Filter className="w-5 h-5 text-muted-foreground" />
          <div className="flex-1 grid grid-cols-6 gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search segments..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-border bg-background rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
            
            <select
              value={filters.location}
              onChange={(e) => setFilters({...filters, location: e.target.value})}
              className="px-3 py-2 border border-border bg-background text-foreground rounded-lg text-sm focus:ring-2 focus:ring-primary"
            >
                <option value="all">All Locations</option>
                <option value="Urban">Urban</option>
                <option value="Suburban">Suburban</option>
                <option value="Rural">Rural</option>
              </select>

            <select
              value={filters.loyalty}
              onChange={(e) => setFilters({...filters, loyalty: e.target.value})}
              className="px-3 py-2 border border-border bg-background text-foreground rounded-lg text-sm focus:ring-2 focus:ring-primary"
            >
                <option value="all">All Loyalty</option>
                <option value="Gold">Gold</option>
                <option value="Silver">Silver</option>
                <option value="Regular">Regular</option>
              </select>

            <select
              value={filters.vehicle}
              onChange={(e) => setFilters({...filters, vehicle: e.target.value})}
              className="px-3 py-2 border border-border bg-background text-foreground rounded-lg text-sm focus:ring-2 focus:ring-primary"
            >
                <option value="all">All Vehicles</option>
                <option value="Premium">Premium</option>
                <option value="Economy">Economy</option>
              </select>

            <select
              value={filters.demand}
              onChange={(e) => setFilters({...filters, demand: e.target.value})}
              className="px-3 py-2 border border-border bg-background text-foreground rounded-lg text-sm focus:ring-2 focus:ring-primary"
            >
                <option value="all">All Demand</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>

            <select
              value={filters.pricing}
              onChange={(e) => setFilters({...filters, pricing: e.target.value})}
              className="px-3 py-2 border border-border bg-background text-foreground rounded-lg text-sm focus:ring-2 focus:ring-primary"
            >
                <option value="all">All Pricing</option>
                <option value="CONTRACTED">Contracted</option>
                <option value="STANDARD">Standard</option>
                <option value="CUSTOM">Custom</option>
              </select>
            </div>
          <button
            onClick={() => setFilters({location: 'all', loyalty: 'all', vehicle: 'all', demand: 'all', pricing: 'all'})}
            className="px-4 py-2 bg-muted text-foreground rounded-lg hover:bg-muted/80 text-sm font-medium"
          >
            Clear Filters
          </button>
        </div>
        <p className="text-sm text-muted-foreground mt-2">
          Showing <span className="font-semibold text-foreground">{filteredSegments.length}</span> of {segments.length} segments
        </p>
      </div>

      {/* Segments Table */}
      <div className="flex-1 flex flex-col overflow-hidden px-6 py-4">
        <div className="bg-card rounded-lg shadow-sm border border-border flex flex-col h-full">
          {/* Table header with count and pagination controls */}
          <div className="px-4 py-3 border-b border-border flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground">
                Showing <span className="font-semibold text-foreground">{startIdx + 1}-{endIdx}</span> of <span className="font-semibold text-foreground">{filteredSegments.length}</span> segments
                {filteredSegments.length < segments.length && (
                  <span className="ml-2 text-primary">(Filtered from {segments.length} total)</span>
                )}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Page {currentPage + 1} of {totalPages || 1}
              </p>
            </div>
            
            {/* Pagination Controls */}
            <div className="flex items-center gap-2">
              <button
                onClick={handlePageUp}
                disabled={currentPage === 0}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition"
                title="Previous 25 rows"
              >
                <ChevronUp size={14} />
                Page Up
              </button>
              <button
                onClick={handlePageDown}
                disabled={currentPage >= totalPages - 1}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition"
                title="Next 25 rows"
              >
                <ChevronDown size={14} />
                Page Down
              </button>
            </div>
          </div>
          
          {/* Scrollable table container with fixed height */}
          <div className="flex-1 overflow-y-auto overflow-x-auto" style={{ maxHeight: 'calc(100vh - 520px)' }}>
            <table className="w-full">
              <thead className="bg-muted border-b border-border sticky top-0 z-10">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-foreground uppercase">Segment</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-foreground uppercase">Rides</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-foreground uppercase">Unit Price</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-foreground uppercase">Duration</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-foreground uppercase">Revenue (30d)</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-foreground uppercase">vs HWCO</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                  {displayedSegments.map((segment, idx) => {
                    const rides = segment[`${selectedScenario}_rides_30d`];
                    const price = segment[`${selectedScenario}_unit_price`];
                    const duration = segment[`${selectedScenario}_duration_minutes`];
                    const revenue = segment[`${selectedScenario}_revenue_30d`];
                    const hwcoRevenue = segment.hwco_revenue_30d;
                    const revenueDiff = selectedScenario === 'hwco' ? 0 : 
                      ((revenue - hwcoRevenue) / hwcoRevenue) * 100;

                  return (
                    <tr key={startIdx + idx} className="hover:bg-accent transition">
                      <td className="px-4 py-3">
                        <div className="flex flex-col">
                          <span className="text-sm font-medium text-foreground">
                            {segment.location_category} / {segment.loyalty_tier}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {segment.vehicle_type} • {segment.demand_profile} • {segment.pricing_model}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right text-sm text-foreground">{rides.toFixed(0)}</td>
                      <td className="px-4 py-3 text-right text-sm font-medium text-foreground">${price.toFixed(2)}</td>
                      <td className="px-4 py-3 text-right text-sm text-muted-foreground">{duration.toFixed(1)} min</td>
                      <td className="px-4 py-3 text-right text-sm font-semibold text-foreground">
                        ${revenue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                      </td>
                        <td className="px-4 py-3 text-right">
                          {revenueDiff !== 0 && (
                            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-semibold ${
                              revenueDiff > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                            }`}>
                              {revenueDiff > 0 ? '+' : ''}{revenueDiff.toFixed(1)}%
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SegmentDynamicAnalysis;

