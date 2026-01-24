# Agent B: The Strategist - Technical Specification

**Version**: 1.0
**Created**: 2026-01-23
**Status**: Draft

---

## 1. Overview

### 1.1 Purpose

Agent B is the **strategic optimizer** that generates 52-week promotion calendars to maximize either unit volume or profit, subject to budget constraints. It uses causal parameters from Agent A to make data-driven promotional decisions.

### 1.2 Role in Multi-Agent System

- **Input**: Causal parameters from Agent A + Objective + Budget from user
- **Output**: Draft promotion calendar JSON
- **Rejection Loop**: Receives feedback from Agent C, adjusts calendar, resubmits
- **Success Criteria**: Generate calendar approved by Agent C within 10 iterations

### 1.3 Key Characteristics

- **Strategic**: Makes high-level promotional decisions (which PPGs, when, what tactics)
- **Adaptive**: Learns from Agent C rejections and adjusts
- **Data-Driven**: Uses Agent A's causal parameters for ROI calculations
- **LLM-Powered**: Uses Claude for reasoning, not hardcoded optimization algorithms

---

## 2. Responsibilities

### 2.1 Core Functions

1. **Load causal parameters from Agent A**
2. **Generate initial 52-week promotion calendar**:
   - Select high-leverage PPGs (high elasticity for volume, high margin for profit)
   - Choose optimal discount depths using lift factors
   - Select display tiers based on ROI
   - Schedule in high-seasonality weeks
   - Stay within budget
3. **Receive audit feedback from Agent C**
4. **Adjust calendar to fix violations**:
   - Re-schedule to meet gap rules
   - Remove/reduce promos to meet budget
   - Avoid blackout weeks
5. **Iterate until approved (max 10 iterations)**
6. **Save final approved calendar**

### 2.2 Out of Scope

- ❌ Forecasting/causal analysis (Agent A's job)
- ❌ Constraint validation (Agent C's job)
- ❌ Relaxing business constraints (must meet Agent C's rules)

---

## 3. Inputs

### 3.1 Causal Parameters (from Agent A)

**Source**: `outputs/causal_parameters.json`

**Required Fields**:
```json
{
  "baseline_velocity_avg": 11815.46,
  "elasticity_model": {
    "base_price_elasticity": 6.91,
    "discount_lift_factors": {
      "0-15": 1.48,
      "15-25": 1.89,
      "25-35": 2.51,
      "35-45": 3.54,
      "45+": 6.46
    }
  },
  "tier_specific_display_lifts": {
    "platinum": 4.28,
    "gold": 4.35,
    "silver": 3.48,
    "bronze": 2.02
  },
  "feature_lift_multiplier": 0.81,
  "tactic_combination_effects": {
    "tpr_only": 17115,
    "tpr_plus_display": 68053,
    "tpr_plus_feature": 25898,
    "tpr_plus_both": 35202
  },
  "seasonality_factors": {
    "1": 0.92, "2": 0.93, ... "52": 0.51
  }
}
```

### 3.2 Optimization Objective

**Source**: Command-line argument `--objective`

**Options**:
- `"volume"`: Maximize total incremental unit volume
- `"profit"`: Maximize total incremental profit

### 3.3 Budget Constraint

**Source**: Command-line argument `--budget`

**Format**: Integer (dollars), e.g., `1000000` = $1M

### 3.4 Historical Sales Data (for PPG selection)

**Source**: `case-data/sales_v2.xlsx`

**Usage**:
- Identify PPGs with high baseline sales (volume target)
- Identify PPGs with high margins (profit target)
- Check PPG-Retailer combinations for coverage

### 3.5 Financial Data (for cost/profit calculations)

**Source**: `case-data/Finance.xlsx`

**Columns**:
- List Price (for TPR cost calculation)
- Unit Cost (for margin calculation)

### 3.6 Display Costs

**Source**: `case-data/Promo_config.csv`

**Format**:
```csv
Display Tier, Cost per Week
Platinum, 5000
Gold, 3000
Silver, 2000
Bronze, 1000
```

---

## 4. Outputs

### 4.1 Draft Promotion Calendar

**Format**: JSON
**File**: `outputs/draft_calendar_iteration_N.json`

**Schema**:
```json
{
  "metadata": {
    "objective": "Maximize Unit Volume",
    "budget_limit": 1000000,
    "iteration": 1,
    "total_projected_spend": 950000,
    "total_projected_lift": "1.2M incremental units",
    "generation_timestamp": "2026-01-23T10:30:00",
    "strategy_summary": "Focus on high-elasticity PPGs (Brand 5_Promo.Group 6, Brand 4_Promo.Group 0) with deep discounts (35-45%) + Gold displays in peak seasonality weeks (29, 37, 32)"
  },
  "calendar_events": [
    {
      "week": 29,
      "ppg": "Brand 5_Promo.Group 6",
      "retailer": "Retailer 0",
      "discount_depth": 0.40,
      "display_tier": "gold",
      "feature": false,
      "baseline_estimate": 15000,
      "projected_lift_factor": 15.3,
      "projected_incremental_units": 214500,
      "tpr_cost": 90000,
      "display_cost": 3000,
      "total_cost": 93000,
      "roi": 2.31,
      "reasoning": "Highest elasticity PPG (6.91) + peak seasonality week (1.73x) + Gold display (4.35x) + 35-45% discount (3.54x) = 15.3x baseline lift"
    }
  ]
}
```

**Required Fields per Event**:
- `week` (1-52)
- `ppg` (must exist in sales data)
- `retailer` ("Retailer 0" or "Retailer 1")
- `discount_depth` (0.0-1.0, e.g., 0.40 = 40% off)
- `display_tier` ("platinum" | "gold" | "silver" | "bronze" | null)
- `feature` (boolean)
- `projected_lift_factor` (multiplicative lift vs baseline)
- `total_cost` (TPR + display costs in dollars)
- `reasoning` (natural language explanation)

### 4.2 Final Approved Calendar

**Format**: JSON + CSV
**Files**:
- `outputs/optimized_calendar.json` (detailed with reasoning)
- `outputs/optimized_calendar.csv` (simplified for business users)

**CSV Schema**:
```csv
Week,PPG,Retailer,Discount %,Display Tier,Feature,Projected Lift,Cost
29,Brand 5_Promo.Group 6,Retailer 0,40%,Gold,No,15.3x,$93000
```

---

## 5. Tool Definitions

Agent B has **8 tools** for calendar generation:

### 5.1 load_causal_parameters

**Purpose**: Load Agent A's output
**Input**: `{}`
**Output**:
```json
{
  "status": "loaded",
  "baseline_velocity_avg": 11815.46,
  "num_discount_buckets": 5,
  "num_display_tiers": 4,
  "seasonality_weeks": 52
}
```

### 5.2 load_ppg_data

**Purpose**: Load PPG characteristics (baseline sales, margins)
**Input**: `{}`
**Output**:
```json
{
  "ppgs": [
    {
      "ppg": "Brand 5_Promo.Group 6",
      "retailers": ["Retailer 0", "Retailer 1"],
      "avg_baseline_sales": 15000,
      "avg_unit_price": 12.50,
      "avg_unit_cost": 8.00,
      "margin_pct": 36,
      "elasticity_rank": 1
    }
  ]
}
```

### 5.3 calculate_promo_lift

**Purpose**: Estimate lift for a specific promo configuration
**Input**:
```json
{
  "ppg": "Brand 5_Promo.Group 6",
  "week": 29,
  "discount_depth": 0.40,
  "display_tier": "gold",
  "feature": false
}
```
**Output**:
```json
{
  "baseline_estimate": 15000,
  "discount_lift": 3.54,
  "display_lift": 4.35,
  "seasonality_lift": 1.73,
  "combined_lift": 15.3,
  "projected_units": 214500,
  "incremental_units": 199500
}
```

### 5.4 calculate_promo_cost

**Purpose**: Calculate total cost (TPR + display)
**Input**:
```json
{
  "ppg": "Brand 5_Promo.Group 6",
  "discount_depth": 0.40,
  "display_tier": "gold",
  "projected_units": 214500,
  "unit_price": 12.50
}
```
**Output**:
```json
{
  "tpr_cost": 90000,
  "display_cost": 3000,
  "total_cost": 93000,
  "cost_per_incremental_unit": 0.47
}
```

### 5.5 calculate_promo_profit

**Purpose**: Calculate incremental profit (for profit objective)
**Input**:
```json
{
  "incremental_units": 199500,
  "unit_margin": 4.50,
  "tpr_cost": 90000,
  "display_cost": 3000
}
```
**Output**:
```json
{
  "gross_incremental_profit": 897750,
  "total_promo_cost": 93000,
  "net_incremental_profit": 804750,
  "roi": 8.65
}
```

### 5.6 get_audit_feedback

**Purpose**: Load Agent C's audit report
**Input**: `{"iteration": 1}`
**Output**:
```json
{
  "status": "REJECTED",
  "total_violations": 2,
  "violations": [
    {
      "type": "Gap Rule Violation",
      "details": "PPG 'Brand 5_Promo.Group 6' has promos in weeks 12 and 14",
      "recommendation": "Move week 14 to week 16+"
    }
  ],
  "summary_feedback": "Fix gap violations by rescheduling conflicting events"
}
```

### 5.7 save_draft_calendar

**Purpose**: Save calendar for Agent C audit
**Input**: `{"calendar": {...}, "iteration": 1}`
**Output**:
```json
{
  "status": "saved",
  "file_path": "outputs/draft_calendar_iteration_1.json",
  "num_events": 45
}
```

### 5.8 save_final_calendar

**Purpose**: Save approved calendar as final output
**Input**: `{"calendar": {...}}`
**Output**:
```json
{
  "status": "saved",
  "json_path": "outputs/optimized_calendar.json",
  "csv_path": "outputs/optimized_calendar.csv"
}
```

---

## 6. System Prompt Design

### 6.1 Core Behavior

```
You are Agent B, the strategic optimizer for trade promotion calendars.

Your goal: Generate a 52-week promotion calendar that maximizes {objective} within ${budget} budget.

Workflow:
1. Load causal parameters from Agent A
2. Load PPG data (sales, margins, elasticity)
3. Generate initial calendar:
   - Select high-leverage PPGs ({selection_criteria})
   - Choose optimal discount depths (use lift factors)
   - Select display tiers based on ROI
   - Schedule in high-seasonality weeks
   - Ensure total spend ≤ budget
4. Save draft calendar
5. Check if Agent C approved:
   - If APPROVED: Save final calendar and finish
   - If REJECTED: Read violations, adjust calendar, goto step 4
6. Max 10 iterations

{Objective-Specific Strategy}:

IF objective = "Maximize Unit Volume":
- Prioritize PPGs with HIGH ELASTICITY (top 20%)
- Use DEEP DISCOUNTS (35-45%+) for maximum lift
- Use HIGH-TIER DISPLAYS (Gold/Platinum) where ROI > 1
- Schedule in PEAK SEASONALITY weeks (top 10 weeks)
- Don't worry about margins (focus on units)

IF objective = "Maximize Profit":
- Prioritize PPGs with HIGH MARGINS (top 20%)
- Use MODERATE DISCOUNTS (15-25%) to preserve margin
- Use COST-EFFECTIVE DISPLAYS (Silver/Bronze)
- Schedule strategically to avoid over-promoting
- Calculate ROI = net_profit / promo_cost

Constraints (MUST MEET - Agent C will reject if violated):
- Budget: Total spend ≤ ${budget}
- Gap Rule: Min 4 weeks between promos for same PPG-Retailer
- Frequency: Max 12 promos per PPG per year
- Blackout Weeks: No promos in week 52
- Margins: No negative margins

Rejection Loop Strategy:
- Read violations CAREFULLY
- Make MATERIAL adjustments (not cosmetic)
- If budget violation: Remove lowest-ROI events OR reduce discount depths
- If gap violation: Re-schedule conflicting events (move to later weeks)
- If frequency violation: Remove excess events for that PPG
- Explain what you changed and why

Quality:
- Every event needs detailed reasoning
- Calculate lift/cost for every event
- Provide strategy summary in metadata
```

### 6.2 Multi-Turn Conversation Pattern

**Iteration 1** (Initial Calendar):
- Turn 1: Load causal parameters
- Turn 2: Load PPG data
- Turn 3-10: Generate calendar events (call calculate_promo_lift + calculate_promo_cost for each)
- Turn 11: Save draft calendar

**Iteration 2+** (Rejection Loop):
- Turn 1: Load audit feedback
- Turn 2-5: Adjust calendar (re-schedule, remove, modify events)
- Turn 6: Save draft calendar

Expected total turns: **20-50**

---

## 7. Success Criteria

### 7.1 Functional Requirements

- ✅ Generates valid calendar (all required fields)
- ✅ Meets all Agent C constraints within 10 iterations
- ✅ Maximizes objective (volume or profit)
- ✅ Uses Agent A's causal parameters correctly
- ✅ Provides reasoning for every decision

### 7.2 Quality Metrics

**Calendar Quality**:
- Coverage: 40-60 promotional events across 52 weeks
- PPG diversity: At least 5 different PPGs promoted
- Seasonality alignment: 60%+ of events in top 20 seasonality weeks

**Optimization Performance** (vs baseline):
- Volume objective: +30% incremental units minimum
- Profit objective: +20% incremental profit minimum

**Iteration Efficiency**:
- Approval rate: 80%+ approved by iteration 3
- Max iterations: ≤ 10

**Reasoning Quality**:
- Every event has specific reasoning
- Reasoning references causal parameters (e.g., "4.35x Gold display lift")
- Reasoning explains tradeoffs

---

## 8. Optimization Strategies

### 8.1 Volume Maximization Strategy

**PPG Selection**:
1. Rank PPGs by elasticity (base_price_elasticity * avg_discount_lift)
2. Select top 20% (2-3 PPGs)
3. Promote across both retailers

**Discount Depth Selection**:
- Prefer deep discounts (35-45% or 45%+)
- Use highest lift factors from Agent A

**Display Tier Selection**:
- Calculate ROI: (incremental_units * display_lift) / display_cost
- Use Gold/Platinum where ROI > 2
- Use Silver/Bronze where 1 < ROI < 2
- No display where ROI < 1

**Timing**:
- Schedule in top 10 seasonality weeks first
- Fill remaining slots with moderate seasonality weeks
- Respect 4-week gap rule

**Expected Outcome**:
- 50-60 events (aggressive promotion)
- 1.5-2.0M incremental units
- Budget: $900K-$1M (use full budget)

### 8.2 Profit Maximization Strategy

**PPG Selection**:
1. Rank PPGs by margin_pct * elasticity
2. Select top 20% (2-3 PPGs)
3. Focus on high-margin retailers

**Discount Depth Selection**:
- Prefer moderate discounts (15-25% or 25-35%)
- Balance lift vs margin erosion

**Display Tier Selection**:
- Calculate ROI: (incremental_profit - display_cost) / display_cost
- Use cost-effective tiers (Silver/Bronze)
- Avoid Platinum (too expensive)

**Timing**:
- Strategic scheduling (not just peak weeks)
- Spread events to maintain steady profit flow
- Respect 4-week gap rule

**Expected Outcome**:
- 40-50 events (moderate promotion)
- $300K-$500K incremental profit
- Budget: $700K-$900K (preserve margin)

---

## 9. Test Plan

### 9.1 Unit Tests

**Test 1: Volume Calendar Generation**
```
Input: objective="volume", budget=1000000
Expected: 50-60 events, deep discounts, Gold/Platinum displays, budget ~$950K
```

**Test 2: Profit Calendar Generation**
```
Input: objective="profit", budget=1000000
Expected: 40-50 events, moderate discounts, Silver/Bronze displays, budget ~$800K
```

**Test 3: Rejection Loop - Budget Violation**
```
Iteration 1: Generate calendar with $1.1M spend
Agent C: REJECTED (budget violation)
Iteration 2: Remove 5 lowest-ROI events → $980K spend
Agent C: APPROVED
```

**Test 4: Rejection Loop - Gap Violation**
```
Iteration 1: Generate calendar with weeks 12, 14 for same PPG
Agent C: REJECTED (2-week gap < 4-week min)
Iteration 2: Move week 14 → week 16
Agent C: APPROVED
```

### 9.2 Integration Tests

**Test 5: End-to-End Volume Optimization**
- Agent A generates causal parameters
- Agent B generates volume calendar
- Agent C approves within 3 iterations
- Final calendar: >1M incremental units

**Test 6: End-to-End Profit Optimization**
- Agent A generates causal parameters
- Agent B generates profit calendar
- Agent C approves within 3 iterations
- Final calendar: >$300K incremental profit

---

## 10. Implementation Notes

### 10.1 Lift Calculation

**Multiplicative Model**:
```python
combined_lift = (
    discount_lift_factors[discount_bucket] *
    tier_specific_display_lifts[display_tier] *
    seasonality_factors[week]
)

projected_units = baseline * combined_lift
incremental_units = projected_units - baseline
```

**Example**:
```
PPG: Brand 5_Promo.Group 6
Week: 29 (seasonality=1.73x)
Discount: 40% (bucket "35-45", lift=3.54x)
Display: Gold (lift=4.35x)
Baseline: 15,000 units

Combined lift = 3.54 * 4.35 * 1.73 = 26.6x
Projected units = 15,000 * 26.6 = 399,000 units
Incremental units = 399,000 - 15,000 = 384,000 units
```

### 10.2 Cost Calculation

**TPR Cost**:
```python
tpr_cost = projected_units * unit_price * discount_depth
```

**Display Cost**:
```python
display_costs = {
    "platinum": 5000,
    "gold": 3000,
    "silver": 2000,
    "bronze": 1000
}
display_cost = display_costs.get(display_tier, 0)
```

**Total Cost**:
```python
total_cost = tpr_cost + display_cost
```

### 10.3 ROI Calculation

**Volume ROI**:
```python
roi = incremental_units / total_cost
# Higher is better (units per dollar)
```

**Profit ROI**:
```python
gross_profit = incremental_units * unit_margin
net_profit = gross_profit - total_cost
roi = net_profit / total_cost
# ROI > 0 = profitable, ROI > 1 = very profitable
```

---

## 11. Dependencies

### 11.1 Data Files

- Causal parameters: `outputs/causal_parameters.json` (from Agent A)
- Sales data: `case-data/sales_v2.xlsx`
- Finance data: `case-data/Finance.xlsx`
- Display costs: `case-data/Promo_config.csv`

### 11.2 Python Packages

- `anthropic` - Claude API client
- `pandas` - Data manipulation
- `json` - Calendar parsing
- `loguru` - Logging

### 11.3 Inter-Agent Communication

- Agent A → Agent B: causal_parameters.json
- Agent B → Agent C: draft_calendar_iteration_N.json
- Agent C → Agent B: audit_report_iteration_N.json
- Agent B → User: optimized_calendar.json + optimized_calendar.csv

---

## 12. Open Questions

1. **Baseline estimation per event**: Use PPG-Week historical average or PPG-Retailer-Week?
2. **Feature flag usage**: Agent A shows feature_lift=0.81x (negative). Should Agent B ever use features?
3. **Multi-retailer strategy**: Promote same PPG across both retailers simultaneously or stagger?

**Current Assumptions**:
- Baseline: Use PPG-Retailer-Week if available, fallback to PPG-Week average
- Features: Don't use (negative lift)
- Multi-retailer: Promote both retailers separately (more events, higher total lift)

---

**End of Specification**
