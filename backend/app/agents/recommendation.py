"""
Recommendation Agent - Provides strategic recommendations.

This agent provides strategic business recommendations using:
- Strategy knowledge from ChromaDB (PRIMARY RAG source)
- Recent events from n8n (events, traffic, news)
- Competitor analysis data
- Forecasting Agent predictions

The agent focuses on achieving business objectives:
- Revenue increase (15-25%)
- Customer retention (10-15% churn reduction)
- Competitive positioning
"""
from langchain.agents import create_agent
from langchain.tools import tool
from typing import Dict, Any, List
import asyncio
import json
from app.agents.utils import (
    query_chromadb, 
    fetch_mongodb_documents, 
    format_documents_as_context,
    query_historical_rides,
    query_competitor_prices,
    query_events_data,
    query_traffic_data,
    query_news_data,
    get_mongodb_collection_stats
)
from app.config import settings


@tool
def get_performance_metrics(
    month: str = "",
    pricing_model: str = ""
) -> str:
    """
    Query actual HWCO performance metrics from MongoDB.
    
    Use this tool to get real revenue, ride counts, and pricing data
    for making strategic recommendations.
    
    Args:
        month: Month name (e.g., "November") or number. Empty for all.
        pricing_model: "CONTRACTED", "STANDARD", or "CUSTOM". Empty for all.
    
    Returns:
        str: JSON string with performance metrics
    """
    try:
        results = query_historical_rides(
            month=month,
            pricing_model=pricing_model,
            limit=1000  # Get more data for accurate metrics
        )
        
        if not results:
            return json.dumps({"error": "No performance data found", "count": 0})
        
        # Calculate key metrics
        total_revenue = sum(r.get("Historical_Cost_of_Ride", 0) for r in results)
        total_rides = len(results)
        avg_price = total_revenue / total_rides if total_rides > 0 else 0
        
        # By pricing model
        by_model = {}
        for r in results:
            model = r.get("Pricing_Model", "UNKNOWN")
            if model not in by_model:
                by_model[model] = {"count": 0, "revenue": 0}
            by_model[model]["count"] += 1
            by_model[model]["revenue"] += r.get("Historical_Cost_of_Ride", 0)
        
        # By location
        by_location = {}
        for r in results:
            loc = r.get("Location_Category", "Unknown")
            if loc not in by_location:
                by_location[loc] = {"count": 0, "revenue": 0}
            by_location[loc]["count"] += 1
            by_location[loc]["revenue"] += r.get("Historical_Cost_of_Ride", 0)
        
        # By customer tier
        by_tier = {}
        for r in results:
            tier = r.get("Customer_Loyalty_Status", "Regular")
            if tier not in by_tier:
                by_tier[tier] = {"count": 0, "revenue": 0}
            by_tier[tier]["count"] += 1
            by_tier[tier]["revenue"] += r.get("Historical_Cost_of_Ride", 0)
        
        return json.dumps({
            "total_rides": total_rides,
            "total_revenue": round(total_revenue, 2),
            "average_price_per_ride": round(avg_price, 2),
            "by_pricing_model": by_model,
            "by_location": by_location,
            "by_customer_tier": by_tier
        })
    except Exception as e:
        return json.dumps({"error": f"Error getting metrics: {str(e)}"})


@tool
def get_competitor_comparison() -> str:
    """
    Query actual competitor data from MongoDB and compare with HWCO.
    
    Use this tool to understand competitive positioning and pricing gaps.
    Returns comparison of HWCO vs competitor (Lyft) metrics.
    
    Returns:
        str: JSON string with competitive analysis
    """
    try:
        # Get HWCO data from historical_rides
        hwco_data = query_historical_rides(limit=500)
        # Get competitor data from competitor_prices
        competitor_data = query_competitor_prices(limit=500)
        
        if not hwco_data and not competitor_data:
            return json.dumps({"error": "No data found for comparison"})
        
        # Calculate HWCO metrics - use Historical_Cost_of_Ride field
        hwco_prices = [float(r.get("Historical_Cost_of_Ride", 0)) for r in hwco_data if r.get("Historical_Cost_of_Ride")]
        hwco_avg = sum(hwco_prices) / len(hwco_prices) if hwco_prices else 0
        hwco_total = sum(hwco_prices)
        
        # Calculate competitor metrics - also uses Historical_Cost_of_Ride field
        comp_prices = []
        for r in competitor_data:
            price = r.get("Historical_Cost_of_Ride") or r.get("price", 0)
            if price:
                comp_prices.append(float(price))
        
        comp_avg = sum(comp_prices) / len(comp_prices) if comp_prices else 0
        comp_total = sum(comp_prices)
        
        # Calculate gap
        price_gap = ((hwco_avg - comp_avg) / comp_avg * 100) if comp_avg > 0 else 0
        
        # By location comparison
        hwco_by_loc = {}
        for r in hwco_data:
            loc = r.get("Location_Category", "Unknown")
            price = float(r.get("Historical_Cost_of_Ride", 0))
            if loc not in hwco_by_loc:
                hwco_by_loc[loc] = {"count": 0, "total": 0}
            hwco_by_loc[loc]["count"] += 1
            hwco_by_loc[loc]["total"] += price
        
        comp_by_loc = {}
        for r in competitor_data:
            loc = r.get("Location_Category", "Unknown")
            price = float(r.get("Historical_Cost_of_Ride") or r.get("price", 0))
            if loc not in comp_by_loc:
                comp_by_loc[loc] = {"count": 0, "total": 0}
            comp_by_loc[loc]["count"] += 1
            comp_by_loc[loc]["total"] += price
        
        # Calculate averages by location
        location_comparison = {}
        for loc in set(list(hwco_by_loc.keys()) + list(comp_by_loc.keys())):
            hwco_loc_avg = hwco_by_loc.get(loc, {}).get("total", 0) / hwco_by_loc.get(loc, {}).get("count", 1) if hwco_by_loc.get(loc, {}).get("count", 0) > 0 else 0
            comp_loc_avg = comp_by_loc.get(loc, {}).get("total", 0) / comp_by_loc.get(loc, {}).get("count", 1) if comp_by_loc.get(loc, {}).get("count", 0) > 0 else 0
            gap = ((hwco_loc_avg - comp_loc_avg) / comp_loc_avg * 100) if comp_loc_avg > 0 else 0
            location_comparison[loc] = {
                "hwco_avg": round(hwco_loc_avg, 2),
                "competitor_avg": round(comp_loc_avg, 2),
                "gap_percent": round(gap, 2)
            }
        
        return json.dumps({
            "hwco": {
                "ride_count": len(hwco_data),
                "total_revenue": round(hwco_total, 2),
                "average_price": round(hwco_avg, 2)
            },
            "competitor": {
                "ride_count": len(competitor_data),
                "total_revenue": round(comp_total, 2),
                "average_price": round(comp_avg, 2)
            },
            "comparison": {
                "overall_price_gap_percent": round(price_gap, 2),
                "hwco_is_higher": price_gap > 0,
                "recommendation": "HWCO is priced higher than competitors" if price_gap > 0 else "HWCO is priced lower than competitors"
            },
            "by_location": location_comparison
        })
    except Exception as e:
        return json.dumps({"error": f"Error comparing: {str(e)}"})


@tool
def get_market_context() -> str:
    """
    Query actual market context from MongoDB (events, traffic, news).
    
    Use this tool to understand current market conditions for recommendations.
    Combines events, traffic, and news data for comprehensive context.
    
    Returns:
        str: JSON string with market context
    """
    try:
        # Get events
        events = query_events_data(limit=10)
        # Get traffic
        traffic = query_traffic_data(limit=10)
        # Get news
        news = query_news_data(limit=5)
        
        # Format events
        formatted_events = []
        for e in events:
            formatted_events.append({
                "name": e.get("name") or e.get("title", "Unknown"),
                "date": str(e.get("event_date") or e.get("date", "Unknown")),
                "venue": e.get("venue", "Unknown"),
                "type": e.get("event_type", "Unknown")
            })
        
        # Format traffic summary
        traffic_summary = []
        for t in traffic:
            traffic_summary.append({
                "location": t.get("location", "Unknown"),
                "congestion": t.get("congestion_level") or t.get("traffic_level", "Unknown")
            })
        
        # Format news
        formatted_news = []
        for n in news:
            formatted_news.append({
                "title": n.get("title", "No title"),
                "date": str(n.get("published_at", "Unknown"))
            })
        
        return json.dumps({
            "events_count": len(formatted_events),
            "upcoming_events": formatted_events[:5],
            "traffic_count": len(traffic_summary),
            "traffic_conditions": traffic_summary[:5],
            "news_count": len(formatted_news),
            "recent_news": formatted_news,
            "data_availability": get_mongodb_collection_stats()
        })
    except Exception as e:
        return json.dumps({"error": f"Error getting market context: {str(e)}"})


@tool
def simulate_pricing_rule_impact(pricing_rules: str, segment_forecasts: str) -> str:
    """
    Simulate the impact of pricing rules on multi-dimensional segment forecasts.
    
    This tool calculates the projected revenue, demand, and business objective impact
    when pricing rules are applied to forecasted segments.
    
    For each rule and each affected segment, it calculates:
    - Price change (multiplier effect)
    - Demand elasticity (how demand changes with price)
    - Revenue impact (baseline vs projected)
    - Which business objectives are affected
    
    Args:
        pricing_rules: JSON string with pricing rules (from generate_and_rank_pricing_rules)
        segment_forecasts: JSON string with multi-dimensional forecasts (from generate_multidimensional_forecast)
    
    Returns:
        str: JSON string with rule impact simulation results
    """
    try:
        import pymongo
        from app.config import settings
        
        # Parse inputs
        try:
            rules = json.loads(pricing_rules) if isinstance(pricing_rules, str) else pricing_rules
            forecasts = json.loads(segment_forecasts) if isinstance(segment_forecasts, str) else segment_forecasts
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON input for rules or forecasts"})
        
        # Extract rules and forecasts from structure
        rules_list = rules.get("top_rules", []) if isinstance(rules, dict) else rules
        forecast_list = forecasts.get("segmented_forecasts", []) if isinstance(forecasts, dict) else forecasts
        
        if not rules_list or not forecast_list:
            return json.dumps({"error": "No rules or forecasts provided", "rule_impacts": []})
        
        # Define demand elasticity by segment characteristics
        # Elasticity = % change in demand / % change in price (typically negative)
        def get_demand_elasticity(segment_dims):
            """Calculate demand elasticity based on segment characteristics."""
            loyalty = segment_dims.get("loyalty_tier", "Regular")
            demand_profile = segment_dims.get("demand_profile", "MEDIUM")
            vehicle = segment_dims.get("vehicle_type", "Economy")
            
            # Base elasticity
            elasticity = -0.5  # Default: 1% price increase = 0.5% demand decrease
            
            # Gold customers are less price-sensitive
            if loyalty == "Gold":
                elasticity = -0.3
            elif loyalty == "Silver":
                elasticity = -0.4
            
            # High demand segments are less elastic
            if demand_profile == "HIGH":
                elasticity *= 0.7  # Less elastic
            elif demand_profile == "LOW":
                elasticity *= 1.3  # More elastic
            
            # Premium vehicles have less elastic demand
            if vehicle == "Premium":
                elasticity *= 0.8
            
            return elasticity
        
        # Simulate impact for each rule
        rule_impacts = []
        
        for rule in rules_list:
            rule_id = rule.get("rule_id", "UNKNOWN")
            rule_name = rule.get("name", "Unknown Rule")
            rule_category = rule.get("category", "other")
            rule_condition = rule.get("condition", {})
            
            # Determine multiplier from rule (simplified - exact match only)
            multiplier = 1.0
            if "action" in rule:
                action = rule["action"]
                if "multiplier" in action:
                    multiplier = action["multiplier"]
                elif "max_multiplier" in action:
                    multiplier = action["max_multiplier"]  # For surge caps
            # No fuzzy matching - use exact values from rule
            
            affected_segments = []
            total_baseline_revenue = 0
            total_projected_revenue = 0
            total_baseline_rides = 0
            total_projected_rides = 0
            
            # Check each segment to see if rule applies
            for segment in forecast_list:
                dimensions = segment.get("dimensions", {})
                baseline = segment.get("baseline_metrics", {})
                forecast_30d = segment.get("forecast_30d", {})
                
                # Simplified rule matching: exact match only (no fuzzy logic)
                def rule_applies_to_segment(rule_condition, dimensions):
                    """
                    Simple exact matching only. No fuzzy logic, no fallbacks.
                    Returns True if all rule conditions match segment dimensions exactly.
                    """
                    # Global rule (no conditions) applies to all segments
                    if not rule_condition:
                        return True
                    
                    # Check each condition field - exact match required
                    for field, value in rule_condition.items():
                        # Map condition field to dimension field (standardized names)
                        dim_field = field  # Exact match (standardized names)
                        
                        # Special handling for nested conditions
                        if field == "min_rides":
                            continue  # Skip min_rides check (not a dimension filter)
                        
                        if dimensions.get(dim_field) != value:
                            return False  # Doesn't match, rule doesn't apply
                    
                    return True  # All conditions matched
                
                applies = rule_applies_to_segment(rule_condition, dimensions)
                
                if not applies:
                    continue
                
                # Calculate impact for this segment
                baseline_price = baseline.get("avg_price", 0)
                baseline_rides = forecast_30d.get("predicted_rides", 0)
                baseline_revenue = forecast_30d.get("predicted_revenue", 0)
                
                if baseline_price == 0 or baseline_rides == 0:
                    continue
                
                # Apply price multiplier
                new_price = baseline_price * multiplier
                price_change_pct = ((new_price - baseline_price) / baseline_price) * 100
                
                # Calculate demand change using elasticity
                elasticity = get_demand_elasticity(dimensions)
                demand_change_pct = elasticity * price_change_pct
                
                # Calculate new demand and revenue
                new_rides = baseline_rides * (1 + demand_change_pct / 100)
                new_revenue = new_rides * new_price
                
                revenue_change = new_revenue - baseline_revenue
                revenue_change_pct = (revenue_change / baseline_revenue * 100) if baseline_revenue > 0 else 0
                
                # Track affected segment
                affected_segments.append({
                    "dimensions": dimensions,
                    "baseline": {
                        "price": round(baseline_price, 2),
                        "rides": round(baseline_rides, 2),
                        "revenue": round(baseline_revenue, 2)
                    },
                    "projected": {
                        "price": round(new_price, 2),
                        "rides": round(new_rides, 2),
                        "revenue": round(new_revenue, 2)
                    },
                    "changes": {
                        "price_change_pct": round(price_change_pct, 2),
                        "demand_change_pct": round(demand_change_pct, 2),
                        "revenue_change_pct": round(revenue_change_pct, 2),
                        "revenue_change_amount": round(revenue_change, 2)
                    },
                    "elasticity": round(elasticity, 2)
                })
                
                total_baseline_revenue += baseline_revenue
                total_projected_revenue += new_revenue
                total_baseline_rides += baseline_rides
                total_projected_rides += new_rides
            
            if not affected_segments:
                continue
            
            # Calculate total impact
            total_revenue_change = total_projected_revenue - total_baseline_revenue
            total_revenue_change_pct = (total_revenue_change / total_baseline_revenue * 100) if total_baseline_revenue > 0 else 0
            total_demand_change_pct = ((total_projected_rides - total_baseline_rides) / total_baseline_rides * 100) if total_baseline_rides > 0 else 0
            
            # Determine which business objectives are affected
            affects_objectives = []
            
            if total_revenue_change_pct >= 5:
                affects_objectives.append("MAXIMIZE_REVENUE")
            if total_revenue_change_pct >= 15:
                affects_objectives.append("STAY_COMPETITIVE")
            if multiplier < 1.0 or (multiplier >= 1.0 and multiplier <= 1.25 and "Gold" in str(rule_condition)):
                affects_objectives.append("CUSTOMER_RETENTION")
            if total_revenue_change_pct > 0 and total_demand_change_pct > -10:
                affects_objectives.append("MAXIMIZE_PROFIT_MARGINS")
            
            rule_impacts.append({
                "rule_id": rule_id,
                "rule_name": rule_name,
                "rule_category": rule_category,
                "multiplier": multiplier,
                "segments_affected_count": len(affected_segments),
                "affected_segments": affected_segments[:10],  # Limit to first 10 for response size
                "total_impact": {
                    "baseline_revenue": round(total_baseline_revenue, 2),
                    "projected_revenue": round(total_projected_revenue, 2),
                    "revenue_increase_amount": round(total_revenue_change, 2),
                    "revenue_increase_pct": round(total_revenue_change_pct, 2),
                    "demand_change_pct": round(total_demand_change_pct, 2),
                    "baseline_rides": round(total_baseline_rides, 2),
                    "projected_rides": round(total_projected_rides, 2)
                },
                "affects_objectives": affects_objectives
            })
        
        # Sort by revenue impact
        rule_impacts.sort(key=lambda x: x["total_impact"]["revenue_increase_pct"], reverse=True)
        
        result = {
            "simulation_summary": {
                "total_rules_simulated": len(rules_list),
                "rules_with_impact": len(rule_impacts),
                "total_segments_analyzed": len(forecast_list)
            },
            "rule_impacts": rule_impacts[:20],  # Return top 20 rules by impact
            "note": "Only showing top 20 rules by revenue impact and first 10 affected segments per rule"
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Error simulating rule impact: {str(e)}", "rule_impacts": []})


@tool
def generate_strategic_recommendations(forecasts: str, rules: str) -> str:
    """
    Generate top 3 strategic recommendations by simulating all pricing rules
    and finding minimum rule sets that achieve all 4 business objectives.
    
    This tool combines:
    1. Rule impact simulation across all segments
    2. Rule set optimization (find top 3 combinations)
    3. Strategic recommendation generation with explanations
    
    Args:
        forecasts: Multi-dimensional forecasts (162 segments) from generate_multidimensional_forecast
        rules: Ranked pricing rules from generate_and_rank_pricing_rules
    
    Returns:
        str: JSON with top 3 strategic recommendations
    """
    try:
        import itertools
        
        # Parse inputs
        try:
            forecasts_data = json.loads(forecasts) if isinstance(forecasts, str) else forecasts
            rules_data = json.loads(rules) if isinstance(rules, str) else rules
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON input for forecasts or rules"})
        
        # Extract data - handle different possible structures
        if isinstance(forecasts_data, dict):
            # Try multiple possible keys
            forecast_list = forecasts_data.get("segmented_forecasts", [])
            if not forecast_list:
                forecast_list = forecasts_data.get("forecasts", [])
            if not forecast_list and "data" in forecasts_data:
                forecast_list = forecasts_data["data"].get("segmented_forecasts", [])
        else:
            forecast_list = forecasts_data if isinstance(forecasts_data, list) else []
        
        if isinstance(rules_data, dict):
            rules_list = rules_data.get("top_rules", [])
            if not rules_list:
                rules_list = rules_data.get("rules", [])
            if not rules_list and "data" in rules_data:
                rules_list = rules_data["data"].get("top_rules", [])
        else:
            rules_list = rules_data if isinstance(rules_data, list) else []
        
        if not rules_list:
            return json.dumps({"error": "No rules provided", "recommendations": []})
        if not forecast_list:
            # If no forecasts, still generate recommendations from rules only
            forecast_list = []
        
        # Step 1: Simulate each rule's impact
        rule_impacts = []
        
        # Use simplified rule matching (exact match only)
        def rule_applies_to_segment(rule_condition, dimensions):
            if not rule_condition:
                return True
            for field, value in rule_condition.items():
                if field == "min_rides":
                    continue
                if dimensions.get(field) != value:
                    return False
            return True
        
        def get_demand_elasticity(segment_dims):
            """Calculate demand elasticity based on segment characteristics (KEEP AS-IS)."""
            loyalty = segment_dims.get("loyalty_tier", "Regular")
            demand_profile = segment_dims.get("demand_profile", "MEDIUM")
            vehicle = segment_dims.get("vehicle_type", "Economy")
            
            elasticity = -0.5
            if loyalty == "Gold":
                elasticity = -0.3
            elif loyalty == "Silver":
                elasticity = -0.4
            
            if demand_profile == "HIGH":
                elasticity *= 0.7
            elif demand_profile == "LOW":
                elasticity *= 1.3
            
            if vehicle == "Premium":
                elasticity *= 0.8
            
            return elasticity
        
        # Simulate each rule
        for rule in rules_list:
            rule_id = rule.get("rule_id", "UNKNOWN")
            rule_condition = rule.get("condition", {})
            action = rule.get("action", {})
            multiplier = action.get("multiplier", action.get("max_multiplier", 1.0))
            
            total_impact = {
                "baseline_revenue": 0,
                "projected_revenue": 0,
                "segments_affected": 0
            }
            
            # If we have forecasts, simulate impact on segments
            if forecast_list:
                for segment in forecast_list:
                    dimensions = segment.get("dimensions", {})
                    if not rule_applies_to_segment(rule_condition, dimensions):
                        continue
                    
                    baseline = segment.get("baseline_metrics", {})
                    forecast_30d = segment.get("forecast_30d", {})
                    
                    baseline_price = baseline.get("avg_price", 0)
                    baseline_rides = forecast_30d.get("predicted_rides", 0)
                    baseline_revenue = forecast_30d.get("predicted_revenue", 0)
                    
                    if baseline_price == 0 or baseline_rides == 0:
                        continue
                    
                    new_price = baseline_price * multiplier
                    price_change_pct = ((new_price - baseline_price) / baseline_price) * 100
                    elasticity = get_demand_elasticity(dimensions)
                    demand_change_pct = elasticity * price_change_pct
                    new_rides = baseline_rides * (1 + demand_change_pct / 100)
                    new_revenue = new_rides * new_price
                    
                    total_impact["baseline_revenue"] += baseline_revenue
                    total_impact["projected_revenue"] += new_revenue
                    total_impact["segments_affected"] += 1
            else:
                # No forecasts available - estimate impact from rule's estimated_impact
                estimated_impact = rule.get("estimated_impact", 10.0)
                total_impact["baseline_revenue"] = 100000  # Placeholder
                total_impact["projected_revenue"] = 100000 * (1 + estimated_impact / 100)
                total_impact["segments_affected"] = 1  # Assume affects at least 1 segment
            
            if total_impact["segments_affected"] > 0:
                revenue_change_pct = ((total_impact["projected_revenue"] - total_impact["baseline_revenue"]) / total_impact["baseline_revenue"] * 100) if total_impact["baseline_revenue"] > 0 else 0
                
                # Determine objectives affected
                affects_objectives = []
                if revenue_change_pct >= 5:
                    affects_objectives.append("MAXIMIZE_REVENUE")
                if revenue_change_pct >= 15:
                    affects_objectives.append("STAY_COMPETITIVE")
                if multiplier < 1.0 or (multiplier >= 1.0 and multiplier <= 1.25):
                    affects_objectives.append("CUSTOMER_RETENTION")
                if revenue_change_pct > 0:
                    affects_objectives.append("MAXIMIZE_PROFIT_MARGINS")
                
                rule_impacts.append({
                    "rule_id": rule_id,
                    "rule_name": rule.get("name", "Unknown"),
                    "multiplier": multiplier,
                    "revenue_impact_pct": revenue_change_pct,
                    "affects_objectives": affects_objectives,
                    "segments_affected": total_impact["segments_affected"]
                })
        
        # Step 2: Find top 3 rule combinations
        # If no rule impacts, create fallback recommendations from rules directly
        if not rule_impacts:
            # Fallback: Use top rules directly as recommendations
            top_3 = []
            for idx, rule in enumerate(rules_list[:3], 1):
                top_3.append({
                    "rules": [rule.get("rule_id", f"RULE_{idx}")],
                    "rule_names": [rule.get("name", "Unknown Rule")],
                    "rule_count": 1,
                    "objectives_achieved": 2,  # Conservative estimate
                    "revenue_impact_pct": rule.get("estimated_impact", 10.0),
                    "affects_objectives": ["MAXIMIZE_REVENUE", "STAY_COMPETITIVE"],
                    "score": 2000 + rule.get("estimated_impact", 10.0)
                })
        else:
            # Test combinations of 1-5 rules
            all_combinations = []
            for size in range(1, min(6, len(rule_impacts) + 1)):
                for combo in itertools.combinations(rule_impacts, size):
                    # Calculate combined impact
                    combined_revenue_pct = sum(r["revenue_impact_pct"] for r in combo)
                    all_objectives = set()
                    for r in combo:
                        all_objectives.update(r["affects_objectives"])
                    
                    objectives_met = len([obj for obj in all_objectives if obj in ["MAXIMIZE_REVENUE", "MAXIMIZE_PROFIT_MARGINS", "STAY_COMPETITIVE", "CUSTOMER_RETENTION"]])
                    
                    # Score: objectives_met * 1000 - rule_count * 10 + revenue_impact
                    score = objectives_met * 1000 - len(combo) * 10 + combined_revenue_pct
                    
                    all_combinations.append({
                        "rules": [r["rule_id"] for r in combo],
                        "rule_names": [r["rule_name"] for r in combo],
                        "rule_count": len(combo),
                        "objectives_achieved": objectives_met,
                        "revenue_impact_pct": round(combined_revenue_pct, 2),
                        "affects_objectives": list(all_objectives),
                        "score": score
                    })
            
            # Sort by score and get top 3
            all_combinations.sort(key=lambda x: x["score"], reverse=True)
            top_3 = all_combinations[:3]
            
            # If we have fewer than 3, pad with single-rule recommendations
            if len(top_3) < 3:
                used_rule_ids = set()
                for combo in top_3:
                    used_rule_ids.update(combo["rules"])
                
                for rule_impact in rule_impacts:
                    if len(top_3) >= 3:
                        break
                    if rule_impact["rule_id"] not in used_rule_ids:
                        top_3.append({
                            "rules": [rule_impact["rule_id"]],
                            "rule_names": [rule_impact["rule_name"]],
                            "rule_count": 1,
                            "objectives_achieved": len(rule_impact["affects_objectives"]),
                            "revenue_impact_pct": rule_impact["revenue_impact_pct"],
                            "affects_objectives": rule_impact["affects_objectives"],
                            "score": len(rule_impact["affects_objectives"]) * 1000 + rule_impact["revenue_impact_pct"]
                        })
                        used_rule_ids.add(rule_impact["rule_id"])
        
        # Step 3: Generate recommendations
        recommendations = []
        for idx, combo in enumerate(top_3, 1):
            recommendations.append({
                "rank": idx,
                "name": f"Strategic Recommendation #{idx}",
                "rules": combo["rules"],
                "rule_names": combo["rule_names"],
                "rule_count": combo["rule_count"],
                "objectives_achieved": combo["objectives_achieved"],
                "revenue_impact": f"+{combo['revenue_impact_pct']:.1f}%",
                "affects_objectives": combo["affects_objectives"],
                "implementation_priority": "HIGH" if combo["objectives_achieved"] == 4 else "MEDIUM",
                "explanation": f"Implement {combo['rule_count']} pricing rules to achieve {combo['objectives_achieved']}/4 business objectives with {combo['revenue_impact_pct']:.1f}% revenue impact."
            })
        
        result = {
            "summary": {
                "total_rules_analyzed": len(rules_list),
                "total_combinations_tested": len(all_combinations) if 'all_combinations' in locals() else 0,
                "top_recommendations": len(recommendations)
            },
            "recommendations": recommendations
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Error generating strategic recommendations: {str(e)}", "recommendations": []})


@tool
def query_strategy_knowledge(query: str, n_results: int = 10) -> str:
    """
    Query strategy knowledge and business rules (PRIMARY RAG source).
    
    This is the PRIMARY source for strategic recommendations.
    This tool searches ChromaDB for pricing strategies, business rules,
    and strategic knowledge that guides decision-making.
    
    Args:
        query: Text description to search for (e.g., "revenue optimization strategy")
        n_results: Number of similar strategies to retrieve (default: 10, more for comprehensive context)
    
    Returns:
        str: Formatted context string with strategic knowledge
    """
    try:
        # Query ChromaDB for strategy knowledge (PRIMARY RAG source)
        results = query_chromadb("strategy_knowledge_vectors", query, n_results)
        
        if not results:
            return "No strategic knowledge found."
        
        # Extract MongoDB IDs
        mongodb_ids = [r["mongodb_id"] for r in results]
        
        # Fetch full documents from MongoDB
        # Note: Strategy knowledge might be in various collections
        # For now, we'll return the document descriptions from ChromaDB
        context_parts = []
        for result in results:
            doc = result.get("document", "")
            metadata = result.get("metadata", {})
            if doc:
                context_parts.append(doc)
            elif metadata:
                # Use metadata if document not available
                context_parts.append(str(metadata))
        
        return " ".join(context_parts) if context_parts else "No strategy details found."
    except Exception as e:
        return f"Error querying strategy knowledge: {str(e)}"


@tool
def query_recent_events(query: str, n_results: int = 5) -> str:
    """
    Query recent events from n8n ingested data.
    
    This tool searches for recent events, traffic patterns, and news
    that might inform strategic recommendations. Use this to understand
    current market conditions and external factors.
    
    Args:
        query: Text description to search for (e.g., "recent events downtown")
        n_results: Number of similar events to retrieve (default: 5)
    
    Returns:
        str: Formatted context string with recent events
    """
    try:
        # Query ChromaDB for recent events/news
        results = query_chromadb("news_events_vectors", query, n_results)
        
        if not results:
            return "No recent events found."
        
        # Extract MongoDB IDs
        mongodb_ids = [r["mongodb_id"] for r in results]
        
        # Fetch full documents from MongoDB
        loop = asyncio.get_event_loop()
        documents = []
        
        for collection_name in ["events_data", "traffic_data", "news_articles"]:
            docs = loop.run_until_complete(
                fetch_mongodb_documents(mongodb_ids, collection_name)
            )
            documents.extend(docs)
        
        # Format as context string
        return format_documents_as_context(documents)
    except Exception as e:
        return f"Error querying recent events: {str(e)}"


@tool
def query_competitor_analysis(query: str, n_results: int = 5) -> str:
    """
    Query competitor analysis data.
    
    This tool searches for competitor pricing and market positioning data
    to inform strategic recommendations. Use this to understand competitive
    landscape and make recommendations that maintain competitive advantage.
    
    Args:
        query: Text description to search for (e.g., "competitor pricing downtown")
        n_results: Number of similar records to retrieve (default: 5)
    
    Returns:
        str: Formatted context string with competitor analysis data
    """
    try:
        # Query ChromaDB for competitor data
        results = query_chromadb("competitor_analysis_vectors", query, n_results)
        
        if not results:
            return "No competitor data found."
        
        # Extract MongoDB IDs
        mongodb_ids = [r["mongodb_id"] for r in results]
        
        # Fetch full documents from MongoDB
        loop = asyncio.get_event_loop()
        documents = loop.run_until_complete(
            fetch_mongodb_documents(mongodb_ids, "competitor_prices")
        )
        
        # Format as context string
        return format_documents_as_context(documents)
    except Exception as e:
        return f"Error querying competitor analysis: {str(e)}"


@tool
def generate_strategic_recommendation(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate strategic recommendation using OpenAI GPT-4.
    
    This tool takes context from strategy knowledge, events, competitor data, and forecast,
    then uses OpenAI GPT-4 to generate strategic recommendations focused on
    achieving business objectives (revenue increase 15-25%, customer retention).
    
    Args:
        context: Dictionary with:
            - strategy_knowledge: str (from query_strategy_knowledge)
            - recent_events: str (from query_recent_events)
            - competitor_data: str (from query_competitor_analysis)
            - forecast_data: dict (optional, from Forecasting Agent)
            - mongodb_ids: List[str] (optional, data source IDs)
    
    Returns:
        dict: Strategic recommendation with:
            - recommendation: str (the recommendation from OpenAI GPT-4)
            - reasoning: str (why this recommendation from OpenAI GPT-4)
            - expected_impact: dict (revenue_increase, confidence)
            - data_sources: List[str] (mongodb_ids used)
    """
    try:
        from openai import OpenAI
        
        strategy = context.get("strategy_knowledge", "")
        events = context.get("recent_events", "")
        competitor = context.get("competitor_data", "")
        forecast_data = context.get("forecast_data", {})
        mongodb_ids = context.get("mongodb_ids", [])
        
        if not settings.OPENAI_API_KEY:
            # Fallback to basic recommendation if API key not available
            recommendation = "Based on strategic analysis: "
            if strategy and strategy != "No strategic knowledge found.":
                recommendation += f"Strategy context: {strategy[:200]}... "
            if events and events != "No recent events found.":
                recommendation += f"Recent events: {events[:200]}... "
            if competitor and competitor != "No competitor data found.":
                recommendation += f"Competitor insights: {competitor[:200]}... "
            
            return {
                "recommendation": recommendation,
                "reasoning": "Combined analysis of strategy knowledge, recent events, and competitor data.",
                "expected_impact": {
                    "revenue_increase": "15-25%",
                    "confidence": "High"
                },
                "data_sources": mongodb_ids
            }
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Format forecast data for prompt
        forecast_text = ""
        if forecast_data and isinstance(forecast_data, dict):
            forecast_text = f"""
            Forecast Data:
            - Pricing Model: {forecast_data.get('pricing_model', 'N/A')}
            - Period: {forecast_data.get('periods', 0)} days
            - Average Demand: {sum(p.get('predicted_demand', 0) for p in forecast_data.get('forecast', [])) / len(forecast_data.get('forecast', [1])) if forecast_data.get('forecast') else 0:.2f} rides/day
            - Events Detected: {', '.join(forecast_data.get('context', {}).get('events_detected', []))}
            - Traffic Patterns: {', '.join(forecast_data.get('context', {}).get('traffic_patterns', []))}
            """
        
        prompt = f"""
        Generate a strategic business recommendation for a rideshare company to achieve FOUR business objectives.
        
        BUSINESS OBJECTIVES (ALL MUST BE ADDRESSED):
        1. **Maximize Revenue:** Increase 15-25% through intelligent pricing
        2. **Maximize Profit Margins:** Optimize without losing customers  
        3. **Stay Competitive:** Real-time competitor analysis and positioning
        4. **Customer Retention:** Reduce churn 10-15%
        
        Strategy Knowledge (from pricing_strategies MongoDB collection):
        {strategy[:1000] if strategy and strategy != "No strategic knowledge found." else "No strategy knowledge available"}
        
        Recent Events (from n8n ingested data):
        {events[:500] if events and events != "No recent events found." else "No recent events available"}
        
        Competitor Analysis:
        {competitor[:500] if competitor and competitor != "No competitor data found." else "No competitor data available"}
        
        {forecast_text if forecast_text else ""}
        
        Generate a strategic recommendation in JSON format with:
        1. recommendations_by_objective: Object with 4 keys (revenue, profit_margin, competitive, retention), 
           each containing:
           - actions: Array of specific action items
           - expected_impact: String describing impact
           - priority: "high", "medium", or "low"
        
        2. integrated_strategy: A 2-3 sentence summary explaining how all recommendations work together
        
        3. reasoning: Why these recommendations make sense based on the data (2-3 sentences)
        
        4. expected_impact: Object with:
           - revenue_increase: Percentage range (e.g., "18-23%")
           - profit_margin_improvement: Percentage (e.g., "5-7%")
           - churn_reduction: Percentage (e.g., "12%")
           - competitive_positioning: String (e.g., "move from 5% behind to competitive parity")
           - confidence: "High", "Medium", or "Low"
        
        5. implementation_phases: Array of phases with:
           - phase_name: String (e.g., "Week 1", "Month 1")
           - actions: Array of actions
           - expected_timeline: String
        
        REQUIREMENTS:
        - Every recommendation must map to at least one of the 4 business objectives
        - Include specific numbers and percentages wherever possible
        - Reference actual data from strategy knowledge and competitor analysis
        - Ensure recommendations are actionable and measurable
        
        Example structure:
        {{
          "recommendations_by_objective": {{
            "revenue": {{
              "actions": ["Apply 1.12x multiplier to urban routes (Gap: +14.9%)", "Implement evening rush surge 1.25x"],
              "expected_impact": "+18% revenue from pricing optimization",
              "priority": "high"
            }},
            "profit_margin": {{
              "actions": ["Reduce CUSTOM pricing (7.2% → 2%)", "Optimize operational efficiency"],
              "expected_impact": "+6% margin improvement",
              "priority": "high"
            }},
            "competitive": {{
              "actions": ["Match competitor pricing in rural areas", "Exceed urban competitor pricing by 5%"],
              "expected_impact": "Close 5% market share gap",
              "priority": "high"
            }},
            "retention": {{
              "actions": ["Cap surge at 1.25x for Gold customers", "Launch Silver→Gold upgrade path"],
              "expected_impact": "-12% churn rate",
              "priority": "high"
            }}
          }},
          "integrated_strategy": "Focus on urban premium pricing and loyalty protection to maximize revenue while retaining customers, using competitor data to stay competitive.",
          "reasoning": "Analysis shows HWCO is underpriced in urban areas by 14.9% vs competitors, presenting immediate revenue opportunity. Gold customer protection prevents churn during pricing adjustments.",
          "expected_impact": {{
            "revenue_increase": "18-23%",
            "profit_margin_improvement": "5-7%", 
            "churn_reduction": "12%",
            "competitive_positioning": "close 5% gap and achieve parity",
            "confidence": "High"
          }},
          "implementation_phases": [
            {{
              "phase_name": "Week 1 - Quick Wins",
              "actions": ["Urban price multiplier 1.12x", "Gold customer surge cap"],
              "expected_timeline": "7 days"
            }}
          ]
        }}
        
        Return ONLY valid JSON, no additional text.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}  # Structured output
        )
        
        recommendation_json = json.loads(response.choices[0].message.content)
        
        return {
            "recommendations_by_objective": recommendation_json.get("recommendations_by_objective", {
                "revenue": {"actions": [], "expected_impact": "Unknown", "priority": "medium"},
                "profit_margin": {"actions": [], "expected_impact": "Unknown", "priority": "medium"},
                "competitive": {"actions": [], "expected_impact": "Unknown", "priority": "medium"},
                "retention": {"actions": [], "expected_impact": "Unknown", "priority": "medium"}
            }),
            "integrated_strategy": recommendation_json.get("integrated_strategy", "No integrated strategy provided"),
            "reasoning": recommendation_json.get("reasoning", "No reasoning provided"),
            "expected_impact": recommendation_json.get("expected_impact", {
                "revenue_increase": "15-25%",
                "profit_margin_improvement": "0%",
                "churn_reduction": "0%",
                "competitive_positioning": "Unknown",
                "confidence": "Medium"
            }),
            "implementation_phases": recommendation_json.get("implementation_phases", []),
            "data_sources": mongodb_ids
        }
        
    except Exception as e:
        # Fallback to basic recommendation on error
        strategy = context.get("strategy_knowledge", "")
        events = context.get("recent_events", "")
        competitor = context.get("competitor_data", "")
        mongodb_ids = context.get("mongodb_ids", [])
        
        recommendation = "Based on strategic analysis: "
        if strategy and strategy != "No strategic knowledge found.":
            recommendation += f"Strategy context: {strategy[:200]}... "
        if events and events != "No recent events found.":
            recommendation += f"Recent events: {events[:200]}... "
        if competitor and competitor != "No competitor data found.":
            recommendation += f"Competitor insights: {competitor[:200]}... "
        
        return {
            "recommendations_by_objective": {
                "revenue": {
                    "actions": ["Analyze pricing opportunities"],
                    "expected_impact": "15-25% increase target",
                    "priority": "high"
                },
                "profit_margin": {
                    "actions": ["Optimize operational efficiency"],
                    "expected_impact": "Margin improvement",
                    "priority": "medium"
                },
                "competitive": {
                    "actions": ["Monitor competitor pricing"],
                    "expected_impact": "Maintain competitive position",
                    "priority": "medium"
                },
                "retention": {
                    "actions": ["Protect customer loyalty tiers"],
                    "expected_impact": "10-15% churn reduction",
                    "priority": "high"
                }
            },
            "integrated_strategy": recommendation,
            "reasoning": f"Combined analysis of available data. Error generating detailed recommendation: {str(e)[:100]}",
            "expected_impact": {
                "revenue_increase": "15-25%",
                "profit_margin_improvement": "0%",
                "churn_reduction": "10%",
                "competitive_positioning": "Maintain position",
                "confidence": "Low"
            },
            "implementation_phases": [],
            "data_sources": mongodb_ids
        }


# Create the recommendation agent
# Handle missing API key gracefully (for testing environments)
try:
    recommendation_agent = create_agent(
        model="openai:gpt-4o-mini",
        tools=[
            # MongoDB direct query tools (for ACTUAL data) - USE THESE FIRST!
            get_performance_metrics,
            get_competitor_comparison,
            get_market_context,
            # ChromaDB RAG tools (for strategic context only)
            query_strategy_knowledge,
            query_recent_events,
            # Rule simulation and optimization (NEW)
            simulate_pricing_rule_impact,
            generate_strategic_recommendations,  # Combined tool (NEW)
            # Legacy recommendation generation (for backward compatibility)
            generate_strategic_recommendation
        ],
        system_prompt=(
            "You are a strategic recommendation specialist. "
            "Your role is to provide strategic business recommendations that help "
            "achieve business objectives: revenue increase (15-25%), customer retention, "
            "and competitive positioning. "
            "\n\n"
            "CRITICAL TOOL SELECTION - USE MONGODB TOOLS FIRST: "
            "- ALWAYS use get_performance_metrics for HWCO revenue/ride data "
            "- ALWAYS use get_competitor_comparison for HWCO vs competitor pricing "
            "- ALWAYS use get_market_context for events, traffic, news "
            "- Only use query_strategy_knowledge for business rules/strategies (ChromaDB) "
            "- DO NOT use ChromaDB for actual data - use MongoDB tools! "
            "\n\n"
            "For 'competitor comparison' or 'HWCO vs competitor' questions: "
            "→ ALWAYS call get_competitor_comparison FIRST (returns actual MongoDB data) "
            "\n\n"
            "For 'performance' or 'revenue' questions: "
            "→ ALWAYS call get_performance_metrics FIRST "
            "\n\n"
            "Key workflow: "
            "1. Call get_competitor_comparison for HWCO vs competitor data "
            "2. Call get_performance_metrics for HWCO metrics "
            "3. Call get_market_context for events/traffic/news "
            "4. Optionally call query_strategy_knowledge for business rules "
            "5. Generate recommendations with SPECIFIC NUMBERS from the data "
            "\n\n"
            "NEVER give generic responses without first calling the MongoDB tools!"
        ),
        name="recommendation_agent"
    )
except Exception as e:
    # If API key is missing, set to None (for testing environments)
    if "api_key" in str(e).lower() or "openai" in str(e).lower():
        recommendation_agent = None
    else:
        # Re-raise if it's not an API key issue
        raise


