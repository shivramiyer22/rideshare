# 🎯 Dynamic Pricing Rules Summary

**Data Analysis:** HWCO Historical (1000 rides) vs Lyft Competitor (1001 rides)

## 📊 Key Findings

| Metric | HWCO | Lyft | Gap | Action |
|--------|------|------|-----|--------|
| **Total Revenue** | $372,503 | $385,170 | -3.4% | Must close gap |
| **Unit Price** | $3.89/min | $4.06/min | -4.3% | Increase prices |
| **Supply/Demand** | 43.8% | 65.8% | -22% | Critical shortage |
| **Gold Customers** | 31.3% | 45.4% | -14% | Improve loyalty |
| **CONTRACTED %** | 33.7% | 56.1% | -22% | Push contracts |

---

## 🔥 PHASE 1: Immediate Implementation (Revenue +15-20%)

### 1. Morning Rush Surge (6-10 AM)
```
HWCO: $378.06 → Lyft: $421.90 (Gap: +11.6%)
ACTION: Apply 1.10x - 1.25x surge
IMPACT: +10-12% revenue
```

### 2. Evening Rush Surge (5-9 PM)
```
HWCO: $364.25 → Lyft: $411.32 (Gap: +12.9%)
ACTION: Apply 1.12x - 1.30x surge
IMPACT: +12-15% revenue
```

### 3. High Demand Surge
```
Trigger: Supply/Demand < 60% AND Demand = HIGH
Formula: 1.0 + (1 - supply_ratio) × 1.5
Range: 1.3x - 2.0x
IMPACT: +30-50% during surge
```

### 4. Critical Supply Shortage
```
Trigger: Supply/Demand < 50%
ACTION: 1.75x surge + 1.5x driver bonus
IMPACT: +40-60% revenue, +30% driver availability
```

---

## 📍 PHASE 2: Location Optimization (Week 1)

### Urban Routes (+12-15% revenue)
```
HWCO: $363.67 → Lyft: $417.97 (Gap: +14.9%)
ACTION: Apply 1.12x multiplier (max 1.15x)
RATIONALE: Significant underpricing in urban areas
```

### Rural Routes (Competitive pricing)
```
HWCO: $379.94 → Lyft: $329.00 (Gap: -13.4%)
ACTION: Apply 0.90x multiplier (min 0.87x)
RATIONALE: Overpriced, losing customers to Lyft
```

### Suburban Routes (Maintain)
```
HWCO: $374.32 → Lyft: $373.06 (Gap: -0.3%)
ACTION: No change, already competitive
```

---

## 🏆 PHASE 2: Loyalty Program (Week 1)

### Gold Customer Protection
```
Problem: HWCO 31.3% Gold vs Lyft 45.4%
ACTION: Cap surge at 1.25x, 5% discount on STANDARD
IMPACT: -10-12% churn, +15% lifetime value
```

### Silver Upgrade Path
```
Trigger: Silver customer with 25+ rides
ACTION: 3% discount + "Free Gold upgrade at 50 rides"
IMPACT: +15-20% conversion to Gold
```

---

## 💰 PHASE 3: Pricing Model Shift (Week 2)

### Increase CONTRACTED (33.7% → 50%+)
```
Lyft: 56.1% CONTRACTED (predictable revenue)
ACTION: 5% discount vs STANDARD for contracts
IMPACT: +25% revenue predictability, +12% retention
```

### Reduce CUSTOM (7.2% → <2%)
```
Lyft: Only 1.1% CUSTOM
ACTION: Convert to STANDARD with volume discounts
IMPACT: +15% operational efficiency
```

### Optimize STANDARD (+10%)
```
HWCO: $365.44 → Lyft: $415.27 (Gap: +13.6%)
ACTION: Phase increase: +5% now, +5% in 30 days
IMPACT: +8-10% revenue
```

---

## 🚗 Vehicle & Events (Phases 3-4)

### Premium Vehicle Surge
```
Trigger: Premium + HIGH/MEDIUM demand
ACTION: 1.20x base, 1.35x during surge
IMPACT: +15-20% revenue (top 10% segment)
```

### Major Events (Sports, Concerts)
```
Trigger: Event with 5000+ attendees
Pre-event: 1.5x (starts 2 hours before)
During: 2.0x
Post-event: 1.75x (ends 1 hour after)
IMPACT: +40-60% during event windows
```

### Weather Events
```
Trigger: Rain, snow, extreme heat
ACTION: 1.25x surge + 20% driver incentive
IMPACT: +20-25% revenue
```

---

## 📈 Expected Outcomes

| Metric | Conservative | Target | Optimistic |
|--------|--------------|--------|------------|
| **Revenue Increase** | 15% | 20% | 25% |
| **Profit Margin** | +5% | +7% | +8% |
| **Customer Retention** | +10% | +12% | +15% |
| **Market Share** | +5% | +7% | +10% |
| **Gold Customers** | 35% | 40% | 45% |
| **Supply/Demand** | 55% | 60% | 65% |

---

## 🔄 Rule Application Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    INCOMING RIDE REQUEST                     │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌──────────┐    ┌──────────┐    ┌──────────┐
       │ Location │    │   Time   │    │  Demand  │
       │  Rules   │    │  Rules   │    │  Rules   │
       └────┬─────┘    └────┬─────┘    └────┬─────┘
            │               │               │
            └───────────────┼───────────────┘
                            ▼
                    ┌──────────────┐
                    │   Combine    │
                    │ Multipliers  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
       ┌──────────┐ ┌──────────┐ ┌──────────┐
       │ Loyalty  │ │ Vehicle  │ │Competitor│
       │  Caps    │ │ Premium  │ │  Check   │
       └────┬─────┘ └────┬─────┘ └────┬─────┘
            │            │            │
            └────────────┼────────────┘
                         ▼
                 ┌───────────────┐
                 │  FINAL PRICE  │
                 │   + Explain   │
                 └───────────────┘
```

---

## 📁 Files Generated

1. **`dynamic_pricing_rules.json`** - Machine-readable rules for Pricing Engine
2. **`PRICING_RULES_SUMMARY.md`** - Human-readable summary (this file)

---

## 🚀 Next Steps

1. **Load rules into MongoDB** `pricing_strategies` collection
2. **Update Data Ingestion** to route to `strategy_knowledge_vectors`
3. **Update Pricing Engine** to apply rules dynamically
4. **Test with chatbot**: "What's the recommended price for an Urban ride during evening rush?"

