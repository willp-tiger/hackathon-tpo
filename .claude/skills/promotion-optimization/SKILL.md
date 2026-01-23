---
name: promotion-optimization
description: Optimization strategies and constraint satisfaction techniques for TPO Agent B (Strategist)
---

# Promotion Calendar Optimization

This skill provides specialized knowledge for implementing Agent B (The Strategist) - the Promotion Calendar Optimizer.

## Optimization Objectives

### Volume Maximization

**Goal**: Generate the most unit volume within budget constraints.

**Strategy**:
- Prioritize high-elasticity SKUs (bigger lift per dollar spent)
- Use deeper discounts (30% vs 15%) for maximum lift
- Add displays where ROI is positive
- Schedule promotions during high-seasonality weeks

**Calculation**:
```python
projected_volume = baseline * lift_factor * display_multiplier * seasonality_factor

# For 30% discount with display in week 12:
lift_factor = 3.8  # From elasticity model
display_multiplier = 1.4  # From causal parameters
seasonality_factor = 1.05  # Week 12 seasonality

volume = 150 * 3.8 * 1.4 * 1.05 = 836 units
```

### Profit Maximization

**Goal**: Generate the most incremental margin within budget.

**Strategy**:
- Balance discount depth with margin retention
- Prefer moderate discounts (15-20%) over deep discounts
- Only add displays when incremental margin > display cost
- Focus on high-margin SKUs

**Calculation**:
```python
incremental_units = (promoted_sales - baseline_sales)
gross_margin = incremental_units * unit_margin
net_margin = gross_margin - promotion_cost

# Maximize net_margin across all promotions
```

## Constraint Satisfaction Techniques

### Budget Constraint

**Hard Constraint**: Total annual spend ≤ Budget limit

**Components**:
1. **Variable Spend (TPR)**: Trade rate * units sold
   ```python
   trade_rate = regular_price * discount_depth
   tpr_cost = trade_rate * promoted_units
   ```

2. **Fixed Spend (Display)**: Display fee per event
   ```python
   display_cost = display_fee if display_active else 0
   ```

3. **Total Spend**:
   ```python
   total_spend = sum(tpr_cost + display_cost for all promotions)
   ```

**Adjustment Strategy** when over budget:
1. Reduce promotion frequency (remove lowest-ROI events)
2. Reduce discount depths (30% → 20% → 15%)
3. Remove displays from marginal events
4. Shift promotions to lower-volume weeks

### Gap Rule Constraint

**Requirement**: Minimum N weeks between promotions for same SKU

**Implementation**:
```python
def check_gap_rule(events, min_gap=4):
    sku_weeks = {}
    for event in events:
        sku = event['sku']
        week = event['week']
        if sku in sku_weeks:
            last_week = sku_weeks[sku][-1]
            if week - last_week < min_gap:
                return False  # Violation
        sku_weeks.setdefault(sku, []).append(week)
    return True  # Compliant
```

**Adjustment Strategy** when violated:
1. Shift later promotions forward in time
2. Remove lower-value promotions
3. Spread promotions more evenly across the year

### Frequency Limit Constraint

**Requirement**: Maximum M promotions per SKU per year

**Implementation**:
```python
def check_frequency_limit(events, max_promotions=10):
    sku_counts = {}
    for event in events:
        sku = event['sku']
        sku_counts[sku] = sku_counts.get(sku, 0) + 1
        if sku_counts[sku] > max_promotions:
            return False  # Violation
    return True  # Compliant
```

**Adjustment Strategy** when violated:
1. Remove lowest-ROI promotions for over-promoted SKUs
2. Reallocate budget to under-promoted SKUs
3. Combine multiple small promotions into fewer larger ones

## Iterative Refinement Based on Auditor Feedback

### Feedback Loop Pattern

```python
def generate_with_feedback(auditor_feedback=None):
    if auditor_feedback is None:
        # Initial generation - be aggressive
        return optimize_for_objective()

    violations = auditor_feedback.get('violations', [])

    # Adjust based on violation types
    adjustments = []

    for violation in violations:
        if 'budget' in violation['type'].lower():
            adjustments.append('reduce_spend')
        elif 'gap' in violation['type'].lower():
            adjustments.append('increase_gaps')
        elif 'frequency' in violation['type'].lower():
            adjustments.append('reduce_frequency')

    return regenerate_with_adjustments(adjustments)
```

### Adjustment Priorities

When multiple constraints violated:
1. **Budget** (highest priority - hard stop)
2. **Gap rules** (affects feasibility)
3. **Frequency limits** (can reallocate)
4. **Financial feasibility** (margin checks)

## Calendar Generation Strategies

### Greedy Approach (Fast)

```python
# Sort opportunities by ROI
opportunities = []
for week in range(1, 53):
    for sku in skus:
        for depth in [0.15, 0.20, 0.30]:
            for display in [True, False]:
                roi = calculate_roi(week, sku, depth, display)
                opportunities.append({
                    'week': week, 'sku': sku,
                    'depth': depth, 'display': display, 'roi': roi
                })

# Sort by ROI descending
opportunities.sort(key=lambda x: x['roi'], reverse=True)

# Add promotions until budget exhausted or constraints violated
calendar = []
for opp in opportunities:
    if is_feasible(calendar + [opp]):
        calendar.append(opp)
```

### Optimization-Based Approach (Better Quality)

Use linear programming or constraint optimization:

```python
from pulp import *

# Decision variables: x[week, sku, depth, display] = 1 if selected
x = LpVariable.dicts("promo", ..., cat='Binary')

# Objective: maximize volume or profit
prob = LpProblem("PromoOptimization", LpMaximize)
prob += lpSum([volume[i] * x[i] for i in opportunities])

# Constraints
prob += lpSum([cost[i] * x[i] for i in opportunities]) <= budget  # Budget
# Add gap, frequency constraints...

prob.solve()
```

## Reasoning Generation

**Critical**: Every promotion must have clear reasoning.

**Template**:
```
"Selected {discount_depth}% discount {with_display} for {sku} in week {week} because:
- {seasonality_reasoning} (seasonality factor: {factor})
- {elasticity_reasoning} (expected lift: {lift}x baseline)
- {objective_reasoning} (projected {volume/margin}: {value})
- {strategic_reasoning} (e.g., Q1 market share push, holiday season)"
```

**Example**:
```
"Selected 30% discount with display for SKU_123 in week 12 because:
- Week 12 has high seasonality (1.15x average)
- 30% discount generates 3.8x lift with strong elasticity
- Maximizes unit volume for market share objective
- Q1 promotional window aligns with category trends"
```

## Common Pitfalls

1. **First-Try Approval**: The system MUST show rejection loops. Don't generate perfect calendars on first iteration.
2. **Crossing Boundaries**: Don't do data analysis (Agent A's job) or constraint checking (Agent C's job)
3. **Weak Reasoning**: Every decision needs clear "why" statements
4. **Ignoring Feedback**: Must materially adjust when rejected

## Output Format

```json
{
  "objective": "Maximize Unit Volume (Market Share)",
  "total_projected_spend": 950000,
  "budget_limit": 1000000,
  "iteration": 2,
  "calendar_events": [
    {
      "week": 12,
      "sku": "SKU_123",
      "discount_depth": 0.30,
      "display_active": true,
      "reasoning": "Selected 30% discount with display...",
      "projected_outcome": "Lift of 3.8x baseline, 836 units",
      "projected_units": 836,
      "projected_spend": 15000
    }
  ],
  "adjustments_made": "Reduced discount depth on 3 promotions from 30% to 20% to meet budget"
}
```
