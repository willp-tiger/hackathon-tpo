# Placeholder Code Audit & Remediation Plan

**Date**: 2026-01-25
**Status**: CRITICAL - Multiple placeholders causing data quality issues
**Priority**: HIGH - Must fix before demo/production

## Executive Summary

Agent B (Strategist) uses placeholder cost calculations (`$15K per event`) instead of real TPR costs from data. This causes:
- Agent B thinks spend is `$450K` (30 events × $15K)
- Agent C recalculates with real data and gets `$1.24M`
- Financial reports show `$0` for revenue/margin (not implemented)
- **Impossible to verify which results are real vs fake**

---

## Placeholder Locations & Solutions

### 🔴 CRITICAL: Agent B Cost Calculation

#### Location 1: `src/agents/strategist.py:357`

**Current Code** (WRONG):
```python
# Estimate cost (simplified)
promo_cost = 15000  # Placeholder
```

**Correct Solution**:
```python
# Calculate actual TPR cost using Agent A's baseline and pricing data
# Formula: TPR_cost = baseline_units × discount_depth × unit_price

# Get baseline velocity from causal parameters
baseline_velocity = self.causal_parameters.get("baseline_velocity_avg", 0)

# Get unit price from finance data (need to load this in __init__)
unit_price = self._get_unit_price(ppg)  # New helper method needed

# Calculate TPR cost
tpr_cost = baseline_velocity * discount_depth * unit_price

# Calculate display cost
display_cost = self._get_display_cost(display_tier)  # New helper method needed

# Total promo cost
promo_cost = tpr_cost + display_cost
```

**Required Helper Methods**:
```python
def _get_unit_price(self, ppg: str) -> float:
    """
    Get unit price for PPG from Finance.xlsx.

    Args:
        ppg: Product group identifier

    Returns:
        Unit price (List Price column)
    """
    # Load finance data (should be loaded in __init__)
    # Match PPG and return List Price
    # Return 10.0 as fallback only if PPG not found
    pass

def _get_display_cost(self, display_tier: str) -> float:
    """
    Get display cost from Promo_config.csv.

    Args:
        display_tier: Display tier (bronze, silver, gold, platinum)

    Returns:
        Display cost in dollars
    """
    # Load promo config (should be loaded in __init__)
    # Return cost for specified tier
    # Return 0.0 if tier is "none" or not found
    pass
```

**Data Sources**:
- `case-data/Finance.xlsx`: List Price column (per PPG)
- `case-data/Promo_config.csv`: Display fees by tier
- `outputs/causal_parameters.json`: baseline_velocity_avg

---

#### Location 2: `src/agents/strategist.py:432`

**Current Code** (WRONG):
```python
def _adjust_calendar_for_violations(...):
    # ...
    total_spend = len(calendar_events) * 15000  # Simplified cost calculation
```

**Correct Solution**:
```python
# Recalculate total spend using SAME logic as _generate_initial_calendar
total_spend = 0
for event in calendar_events:
    ppg = event["ppg"]
    discount_depth = event["discount_depth"]
    display_tier = event.get("display_tier", "none")

    baseline_velocity = self.causal_parameters.get("baseline_velocity_avg", 0)
    unit_price = self._get_unit_price(ppg)
    tpr_cost = baseline_velocity * discount_depth * unit_price
    display_cost = self._get_display_cost(display_tier)

    total_spend += tpr_cost + display_cost
```

---

#### Location 3: `src/agents/strategist.py:508`

**Current Code** (PARTIALLY WRONG):
```python
# Estimate cost (simplified: TPR cost)
total_cost += event.get("tpr_cost", 0) + event.get("display_cost", 0)
```

**Problem**: Events don't have `tpr_cost` or `display_cost` fields - they're not calculated during generation!

**Correct Solution**:
```python
# Calculate cost on-the-fly (SAME as above)
ppg = event.get("ppg")
discount_depth = event.get("discount_depth", 0)
display_tier = event.get("display_tier", "none")

baseline_velocity = self.causal_parameters.get("baseline_velocity_avg", 0)
unit_price = self._get_unit_price(ppg)
tpr_cost = baseline_velocity * discount_depth * unit_price
display_cost = self._get_display_cost(display_tier)

total_cost += tpr_cost + display_cost
```

---

### 🔴 CRITICAL: Agent B Data Loading

**Problem**: Agent B doesn't load Finance.xlsx or Promo_config.csv

**Location**: `src/agents/strategist.py:__init__()` (lines 32-65)

**Current Code**:
```python
def __init__(self, api_key, objective, budget_limit, max_iterations=10, output_dir="outputs"):
    # ... no data loading ...
    self.causal_parameters = None
```

**Correct Solution**:
```python
def __init__(self, api_key, objective, budget_limit, max_iterations=10, output_dir="outputs", data_dir="case-data"):
    # ... existing code ...

    # Load required data for cost calculations
    from src.utils import DataLoader
    loader = DataLoader(data_dir)

    # Load finance data (for unit prices)
    self.finance_data = loader.load_financials()

    # Load promo config (for display costs)
    self.promo_config = loader.load_promo_config()

    logger.info(f"Loaded finance data: {len(self.finance_data)} PPGs")
    logger.info(f"Loaded promo config: {len(self.promo_config)} tiers")
```

**Also update orchestrator** to pass `data_dir`:
```python
# src/orchestrator.py line 259
self.strategist = StrategistAgent(
    api_key=api_key,
    objective=objective,
    budget_limit=budget,
    max_iterations=self.max_iterations,
    output_dir=str(self.output_dir),
    data_dir=self.data_dir  # ADD THIS
)
```

---

### 🟡 MEDIUM: Agent A Hardcoded Fallback

**Location**: `src/agents/auditor.py:212-214`

**Current Code**:
```python
# Get baseline velocity (if available)
baseline_velocity = 3014.94  # Default fallback
if self.causal_parameters and "baseline_velocity_avg" in self.causal_parameters:
    baseline_velocity = self.causal_parameters["baseline_velocity_avg"]
```

**Issue**: Hardcoded fallback value. Should fail loudly if causal parameters missing.

**Correct Solution**:
```python
# Baseline velocity is REQUIRED
if not self.causal_parameters or "baseline_velocity_avg" not in self.causal_parameters:
    raise ValueError("Causal parameters missing - cannot calculate costs. Run Agent A first.")

baseline_velocity = self.causal_parameters["baseline_velocity_avg"]
```

---

**Location**: `src/agents/auditor.py:223-227`

**Current Code**:
```python
# Get unit price from finance data
unit_price = 10.0  # Default fallback
if self.finance_data is not None:
    ppg_finance = self.finance_data[self.finance_data["PPG"] == ppg]
    if not ppg_finance.empty:
        unit_price = ppg_finance.iloc[0]["List Price"]
```

**Issue**: Fallback value `$10.00` masks data quality issues.

**Correct Solution**:
```python
# Unit price is REQUIRED
if self.finance_data is None:
    raise ValueError("Finance data not loaded - cannot calculate TPR costs")

ppg_finance = self.finance_data[self.finance_data["PPG"] == ppg]
if ppg_finance.empty:
    raise ValueError(f"PPG '{ppg}' not found in Finance.xlsx - invalid calendar")

unit_price = ppg_finance.iloc[0]["List Price"]
```

---

### 🟡 MEDIUM: Financial Report Generator

**Location**: `src/orchestrator.py` (financial report generation)

**Problem**: Baseline and optimized plan calculations not implemented

**Current Output**:
```json
{
  "base_plan": {
    "total_volume": 0,
    "total_revenue": 0,
    "total_margin": 0,
    "total_spend": 0,
    "note": "Baseline calculations require full implementation"
  }
}
```

**Correct Solution**: Implement actual baseline calculations

```python
def _generate_financial_report(self, calendar, causal_params, data):
    """Generate financial impact report comparing baseline vs optimized."""

    # BASELINE PLAN: No promotions, just baseline sales
    baseline_volume = 0
    baseline_revenue = 0
    baseline_margin = 0

    for week in range(1, 53):
        week_baseline = causal_params["baseline_velocity_avg"]
        seasonality = causal_params["seasonality_factors"].get(str(week), 1.0)
        week_volume = week_baseline * seasonality

        # Get average unit price across PPGs
        avg_price = self.finance_data["List Price"].mean()

        week_revenue = week_volume * avg_price
        week_margin = week_revenue * 0.25  # Assume 25% margin

        baseline_volume += week_volume
        baseline_revenue += week_revenue
        baseline_margin += week_margin

    # OPTIMIZED PLAN: With promotions from calendar
    optimized_volume = baseline_volume  # Start with baseline
    optimized_revenue = baseline_revenue
    total_tpr_cost = 0

    for event in calendar["calendar_events"]:
        week = event["week"]
        discount_depth = event["discount_depth"]

        # Get lift from causal parameters
        lift = self._get_discount_lift(discount_depth, causal_params)

        # Calculate incremental volume
        week_baseline = causal_params["baseline_velocity_avg"]
        seasonality = causal_params["seasonality_factors"].get(str(week), 1.0)
        baseline_for_week = week_baseline * seasonality
        incremental_volume = baseline_for_week * (lift - 1.0)

        optimized_volume += incremental_volume

        # Revenue (reduced by discount)
        unit_price = self._get_unit_price(event["ppg"])
        promo_revenue = incremental_volume * unit_price * (1 - discount_depth)
        optimized_revenue += promo_revenue

        # TPR cost
        tpr_cost = baseline_for_week * discount_depth * unit_price
        total_tpr_cost += tpr_cost

    optimized_margin = optimized_revenue * 0.25 - total_tpr_cost

    return {
        "base_plan": {
            "total_volume": round(baseline_volume, 2),
            "total_revenue": round(baseline_revenue, 2),
            "total_margin": round(baseline_margin, 2),
            "total_spend": 0
        },
        "optimized_plan": {
            "total_volume": round(optimized_volume, 2),
            "total_revenue": round(optimized_revenue, 2),
            "total_margin": round(optimized_margin, 2),
            "total_spend": round(total_tpr_cost, 2),
            "event_count": len(calendar["calendar_events"])
        },
        "delta": {
            "volume_lift_pct": round((optimized_volume - baseline_volume) / baseline_volume * 100, 2),
            "revenue_lift_pct": round((optimized_revenue - baseline_revenue) / baseline_revenue * 100, 2),
            "margin_improvement": round(optimized_margin - baseline_margin, 2),
            "roi": round(incremental_volume / total_tpr_cost * 100, 2) if total_tpr_cost > 0 else 0
        }
    }
```

---

## Implementation Priority

### Phase 1: CRITICAL (Must fix for data integrity)

1. ✅ **Create helper methods** in StrategistAgent:
   - `_get_unit_price(ppg)`
   - `_get_display_cost(display_tier)`

2. ✅ **Load data** in StrategistAgent.__init__():
   - Finance.xlsx
   - Promo_config.csv

3. ✅ **Replace placeholder costs** in:
   - `_generate_initial_calendar()` line 357
   - `_adjust_calendar_for_violations()` line 432
   - `_calculate_projected_impact()` line 508

4. ✅ **Remove fallback values** in AuditorAgent:
   - Fail loudly if baseline_velocity missing
   - Fail loudly if unit_price missing

### Phase 2: HIGH (Complete financial reporting)

5. ⏭️ **Implement financial report generator**:
   - Baseline calculations (52-week projection without promos)
   - Optimized calculations (with promo lift)
   - Delta calculations (ROI, volume lift, etc.)

### Phase 3: POLISH (Code cleanup)

6. ⏭️ **Remove all placeholder comments**:
   - "This is simplified for demo"
   - "Placeholder"
   - "TODO"

7. ⏭️ **Add data validation**:
   - Verify PPG exists in Finance.xlsx
   - Verify display tier exists in Promo_config.csv
   - Verify week in range 1-52

---

## Testing Checklist

After implementing fixes, verify:

- [ ] Agent B's `total_spend` matches Agent C's `total_spend` (within 1%)
- [ ] Financial report shows non-zero baseline volume/revenue
- [ ] Financial report shows realistic ROI (not 0 or infinity)
- [ ] System fails gracefully if Finance.xlsx missing
- [ ] System fails gracefully if PPG not in Finance.xlsx
- [ ] Budget violations are caught correctly
- [ ] No placeholder comments remain in code

---

## Expected Impact

**Before**:
- Agent B: `$450K` spend (placeholder)
- Agent C: `$1.24M` spend (real data)
- Mismatch: **176% error**

**After**:
- Agent B: `$1.24M` spend (real data)
- Agent C: `$1.24M` spend (real data)
- Mismatch: **<1% error** (acceptable rounding)

---

**Prepared by**: Claude Code (Session 15)
**Reviewed by**: User
**Action Required**: Implement Phase 1 fixes before next demo
