# Fix Plan: Recommendation System & Business Objectives

## Issues Identified

### 1. Recommendations Not Properly Stored
- **Current:** Recommendations array contains strings ["summary", "recommendations", "per_segment_impacts"]
- **Expected:** Array of 3 recommendation objects with multiple rules each
- **Root Cause:** Pipeline orchestrator is extracting wrong keys from result_data

### 2. Business Objectives Not Stored
- **Current:** Business objectives are only stored when uploaded via `/upload/pricing-strategies`
- **Expected:** Business objectives with targets should be auto-created and stored in `pricing_strategies` collection
- **Required Structure:**
```json
{
  "category": "business_objectives",
  "rule_id": "GOAL_MAXIMIZE_REVENUE",
  "objective": "Maximize Revenue",
  "target": "15-25% increase",
  "current_value": 0,
  "target_value": 0,
  "strategy": "Dynamic pricing optimization"
}
```

### 3. Insufficient Pricing Rules
- **Current:** Only 11 rules generated
- **Expected:** 15+ rules across multiple categories
- **Root Cause:** Analysis Agent's `generate_and_rank_pricing_rules` is limited

### 4. Single-Rule Recommendations
- **Current:** Each recommendation contains only 1 rule
- **Expected:** Recommendations should combine multiple rules (2-5 rules per recommendation)
- **Root Cause:** Combination logic in `generate_strategic_recommendations` tool

### 5. What-If Analysis Incomplete
- **Current:** What-if analysis doesn't assess individual rule impacts
- **Expected:**
  - Individual rule impact on forecast + revenue
  - Cumulative impact for all rules in a recommendation
  - Progress tracking for each business objective
  - Ranking of top 3 by objective achievement

## Fix Implementation

### Step 1: Fix Pipeline Orchestrator - Save Logic
**File:** `backend/app/pipeline_orchestrator.py`

**Issue:** Line 836-854 extracts wrong keys
```python
# WRONG: This extracts just the keys
recommendations = result_data.get("recommendations", [])
```

**Fix:** Extract from correct nested structure
```python
# Get the full result_data which has: summary, recommendations, per_segment_impacts
recommendations_list = result_data.get("recommendations", [])
```

### Step 2: Add Business Objectives to Pipeline
**File:** `backend/app/pipeline_orchestrator.py`

**Add function:**
```python
def _ensure_business_objectives_exist(db):
    """Ensure business objectives are stored in pricing_strategies collection."""
    objectives = [
        {
            "rule_id": "GOAL_MAXIMIZE_REVENUE",
            "name": "Business Objective: Maximize Revenue",
            "category": "business_objectives",
            "objective": "Maximize Revenue",
            "target": "15-25% increase",
            "target_min": 15.0,
            "target_max": 25.0,
            "strategy": "Dynamic pricing optimization, surge pricing, loyalty rewards",
            "description": "Increase total revenue by 15-25% through intelligent pricing"
        },
        {
            "rule_id": "GOAL_MAXIMIZE_PROFIT_MARGINS",
            "name": "Business Objective: Maximize Profit Margins",
            "category": "business_objectives",
            "objective": "Maximize Profit Margins",
            "target": "40%+ margin",
            "target_min": 40.0,
            "strategy": "Optimize operational efficiency, reduce low-margin rides",
            "description": "Improve profit margins to 40% or higher"
        },
        {
            "rule_id": "GOAL_STAY_COMPETITIVE",
            "name": "Business Objective: Stay Competitive",
            "category": "business_objectives",
            "objective": "Stay Competitive",
            "target": "Close 5% gap with Lyft",
            "target_value": 5.0,
            "strategy": "Competitive pricing analysis, market positioning",
            "description": "Match or exceed competitor pricing while maintaining profitability"
        },
        {
            "rule_id": "GOAL_CUSTOMER_RETENTION",
            "name": "Business Objective: Customer Retention",
            "category": "business_objectives",
            "objective": "Customer Retention",
            "target": "10-15% churn reduction",
            "target_min": 10.0,
            "target_max": 15.0,
            "strategy": "Loyalty programs, personalized pricing, quality service",
            "description": "Reduce customer churn by 10-15%"
        }
    ]
    
    for obj in objectives:
        db.pricing_strategies.update_one(
            {"rule_id": obj["rule_id"]},
            {"$set": obj},
            upsert=True
        )
```

### Step 3: Enhance Analysis Agent - Generate More Rules
**File:** `backend/app/agents/analysis.py`

**Current:** `generate_and_rank_pricing_rules` generates 11 rules
**Target:** Generate 20+ rules across 8 categories

**New categories to add:**
- Weather-based pricing (3 rules)
- Event-based surge (3 rules)
- Time-of-day optimization (4 rules)
- Vehicle type optimization (2 rules)

### Step 4: Fix Recommendation Agent - Multi-Rule Combinations
**File:** `backend/app/agents/recommendation.py`

**Current logic (lines 698-746):**
```python
# Test combinations of 1-5 rules
for size in range(1, min(6, len(rule_impacts) + 1)):
```

**Issue:** Algorithm correctly tries combinations but scoring favors single rules

**Fix:** Adjust scoring to prefer multi-rule combinations:
```python
# Current scoring
score = objectives_met * 1000 - len(combo) * 10 + combined_revenue_pct

# New scoring (prefer more rules that achieve same objectives)
score = objectives_met * 1000 + len(combo) * 5 + combined_revenue_pct
```

### Step 5: Enhance What-If Analysis
**File:** `backend/app/agents/analysis.py` - `calculate_whatif_impact_for_pipeline`

**Add:**
1. Individual rule impact assessment
2. Cumulative impact calculation
3. Business objective progress tracking
4. Ranking by objective achievement

**New structure:**
```python
{
    "recommendations_analysis": [
        {
            "recommendation_id": 1,
            "rules": ["RULE_1", "RULE_2", "RULE_3"],
            "individual_rule_impacts": [
                {
                    "rule_id": "RULE_1",
                    "revenue_impact": "+12.5%",
                    "rides_impact": "+8%",
                    "margin_impact": "+3%"
                },
                ...
            ],
            "cumulative_impact": {
                "total_revenue_impact": "+23.5%",
                "total_rides_impact": "+15%",
                "total_margin_impact": "+8%"
            },
            "business_objectives_progress": {
                "GOAL_MAXIMIZE_REVENUE": {
                    "target": "15-25%",
                    "achieved": "23.5%",
                    "progress": 94.0,  # % of target met
                    "status": "ON_TRACK"
                },
                ...
            },
            "rank": 1,
            "score": 3.8  # Weighted score across objectives
        },
        ...
    ],
    "top_3_ranked": [1, 2, 3]  # Recommendation IDs ranked by score
}
```

## Execution Order

1. ✅ Fix pipeline orchestrator save logic (Step 1)
2. ⏳ Add business objectives initialization (Step 2)
3. ⏳ Enhance analysis agent rule generation (Step 3)
4. ⏳ Fix recommendation scoring for multi-rule combos (Step 4)
5. ⏳ Enhance what-if analysis (Step 5)
6. ⏳ Test end-to-end pipeline
7. ⏳ Verify MongoDB storage

## Testing Checklist

- [ ] Business objectives stored in `pricing_strategies` with targets
- [ ] Analysis agent generates 15+ pricing rules
- [ ] Recommendations contain 2-5 rules each
- [ ] What-if analysis shows individual rule impacts
- [ ] What-if analysis shows cumulative impacts
- [ ] Business objectives progress tracked
- [ ] Top 3 recommendations ranked by objective achievement
- [ ] All data properly stored in MongoDB collections


