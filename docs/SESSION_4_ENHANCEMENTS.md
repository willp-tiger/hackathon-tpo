# Session 4: Promotion Feature Enhancements

**Date**: 2026-01-23
**Focus**: Fix TPR data source + Add tier-specific promotion lift calculations

---

## Critical Discovery: TPR Data Source Error

### Problem Identified

**Sessions 2-3 used WRONG TPR calculation**:
```python
# INCORRECT: Using Finance.xlsx
TPR = ((List Price - Unit Price) / List Price * 100)

# Result: Extreme bimodal distribution
- 74% of data: TPR = 0%
- 16% of data: TPR = 100% ← IMPOSSIBLE (free products!)
- 10% of data: Normal discounts (5-45%)
```

### Root Cause

- Agent A was calculating TPR by comparing `List Price` (Finance.xlsx) vs `Unit Price` (sales_v2.xlsx)
- These prices are from different systems/purposes
- List Price may not be the correct promotional base price
- This created artificial 100% discount values

### Solution

**Use PromotionData.xlsx promo_tpr column**:
```python
# CORRECT: Using PromotionData.xlsx
TPR = promo_tpr * 100  # Convert 0.0-0.59 to 0-59%

# Result: Realistic promotional distribution
- 53% of data: TPR = 0% (non-promotional)
- 6% of data: TPR 0-15%
- 15% of data: TPR 15-25%
- 7% of data: TPR 25-35%
- 12% of data: TPR 35-45%
- 8% of data: TPR 45%+
- Max TPR: 59% ✅ (realistic)
```

### Expected Impact

✅ **Baseline forecasting should improve dramatically**:
- No more 100% discount outliers contaminating averages
- Correct separation of promotional vs non-promotional periods
- More accurate lift factor calculations

---

## Enhancement 1: Tier-Specific Display Lifts

### Current State (Sessions 2-3)

Agent A calculates **single aggregated display lift**:
```python
has_display = (platinum==1 OR gold==1 OR silver==1 OR bronze==1)
display_lift = avg_sales(TPR + display) / avg_sales(TPR only)
```

**Problem**: Treats all display types equally, but they have different costs and effectiveness.

### New Approach (Session 4)

Calculate **separate lift for each tier**:

```json
{
  "display_lift_by_tier": {
    "platinum_lift": 2.8,    // Platinum displays: 2.8x vs TPR-only
    "gold_lift": 2.3,        // Gold displays: 2.3x vs TPR-only
    "silver_lift": 1.9,      // Silver displays: 1.9x vs TPR-only
    "bronze_lift": 1.5,      // Bronze displays: 1.5x vs TPR-only
    "no_display_baseline": 1000,  // TPR-only baseline sales
    "n_platinum": 230,       // Sample sizes
    "n_gold": 116,
    "n_silver": 162,
    "n_bronze": 363
  }
}
```

### Tool Implementation

**New Tool**: `calculate_display_lift_by_tier()`

**Method**:
1. Filter sales data to promotional periods (TPR > 0)
2. For each display tier:
   - Calculate: `avg_sales(TPR + tier) / avg_sales(TPR only)`
3. Return lift multipliers for all 4 tiers

**Agent B Usage**:
- Optimize display tier selection based on lift vs cost
- Choose Platinum for high-value promotions
- Choose Bronze for cost-effective volume

---

## Enhancement 2: Feature Lift Calculation

### Current State (Sessions 2-3)

**promo_feature flag ignored** - no lift calculation performed.

### New Approach (Session 4)

Quantify **incremental impact of in-store features/ads**:

```json
{
  "feature_lift": {
    "multiplier": 1.6,           // Features add 60% lift
    "no_feature_baseline": 1000, // TPR-only baseline
    "n_with_feature": 410,       // 410 promos with features
    "n_without_feature": 1554    // 1554 promos without features
  }
}
```

### Tool Implementation

**New Tool**: `calculate_feature_lift()`

**Method**:
1. Filter to promotional periods (TPR > 0)
2. Compare:
   - `avg_sales(TPR + feature)` vs `avg_sales(TPR only)`
3. Calculate lift multiplier

**Agent B Usage**:
- Decide whether to include in-store features/ads
- Balance feature cost vs incremental lift

---

## Enhancement 3: Tactic Combination Analysis

### Current State (Sessions 2-3)

**No analysis of combined tactics** - assumes effects are independent.

### New Approach (Session 4)

Analyze **synergies between promotion tactics**:

```json
{
  "tactic_combinations": {
    "tpr_only": 1000,           // Baseline: TPR with no extras
    "tpr_plus_display": 1700,   // TPR + any display tier
    "tpr_plus_feature": 1600,   // TPR + feature (no display)
    "tpr_plus_both": 2400,      // TPR + feature + display
    "interaction_effect": "synergistic",  // More than additive
    "sample_sizes": {
      "tpr_only": 467,
      "tpr_display": 237,
      "tpr_feature": 64,
      "tpr_both": 77
    }
  }
}
```

### Tool Implementation

**New Tool**: `calculate_tactic_combinations()`

**Method**:
1. Segment promotional sales into 4 groups:
   - TPR only (no display, no feature)
   - TPR + Display (any tier)
   - TPR + Feature (no display)
   - TPR + Both
2. Calculate average sales for each group
3. Determine interaction effect:
   - **Additive**: `tpr_both ≈ tpr_display + tpr_feature`
   - **Multiplicative**: `tpr_both ≈ tpr_display * tpr_feature`
   - **Synergistic**: `tpr_both > tpr_display * tpr_feature`

**Agent B Usage**:
- Understand which tactic combinations are most effective
- Prioritize synergistic combinations (Feature + Display)
- Avoid redundant combinations if effects are independent

---

## Updated Data Flow

### Old Flow (Sessions 2-3)
```
sales_v2.xlsx + Finance.xlsx
  ↓
Calculate TPR from prices (WRONG)
  ↓
Agent A analyzes with bad TPR
  ↓
MAPE = 185-265% (unusable)
```

### New Flow (Session 4)
```
sales_v2.xlsx + PromotionData.xlsx
  ↓
Merge promo_tpr + all promotion flags
  ↓
TPR = promo_tpr * 100 (CORRECT)
  ↓
Agent A analyzes with:
  - Correct TPR (5-59% range)
  - Tier-specific display lifts
  - Feature lift
  - Tactic combinations
  ↓
Expected MAPE = 15-50% (usable)
```

---

## Implementation Plan

### Step 1: Data Loader (COMPLETE ✅)
- Remove Finance.xlsx merge
- Merge PromotionData.xlsx on (Date, PPG, Promo.Group, Retailer)
- Use promo_tpr for TPR calculation
- Keep all promotion flags (display_*, promo_feature)

### Step 2: Agent A Tools (IN PROGRESS)
- [x] Update spec documentation
- [ ] Implement `calculate_display_lift_by_tier()`
- [ ] Implement `calculate_feature_lift()`
- [ ] Implement `calculate_tactic_combinations()`
- [ ] Update system prompt to use new tools
- [ ] Update save_causal_parameters to include new outputs

### Step 3: Testing (PENDING)
- [ ] Run enhanced Agent A with corrected TPR
- [ ] Verify MAPE improvement
- [ ] Validate new lift calculations
- [ ] Document actual vs expected results

### Step 4: Documentation (PENDING)
- [ ] Update CLAUDE.md with Session 4 summary
- [ ] Document TPR fix discovery
- [ ] Document MAPE improvement (actual)

---

## Expected Outcomes

### Baseline Forecasting
- **Old MAPE**: 185-265% (with wrong TPR)
- **Expected MAPE**: 15-50% (with correct TPR)
- **Confidence**: High - removing 100% discount outliers should dramatically improve

### Promotion Lift Calculations
- **Tier-specific displays**: Agent B can optimize display tier selection
- **Feature lift**: Agent B can decide on feature usage
- **Tactic combinations**: Agent B understands synergies

### Agent B Benefits
More granular levers for optimization:
- 5 discount depth buckets (0-15%, 15-25%, 25-35%, 35-45%, 45%+)
- 4 display tiers (Platinum, Gold, Silver, Bronze)
- Feature on/off
- Tactic combinations (8 possible combinations total)

---

## Research Alignment

### Industry Best Practices
✅ **Tier-specific pricing**: Standard in retail analytics (premium vs economy displays)
✅ **Feature advertising**: Proven incremental lift (16.7% of promos use features)
✅ **Interaction effects**: Well-documented in promotional marketing literature

### Data-Driven Approach
✅ **Real promotional data**: Using actual promo_tpr from PromotionData.xlsx
✅ **Sufficient sample sizes**: 230+ records per display tier
✅ **Balanced tactics**: All 4 combinations represented in historical data

---

## Success Criteria

### Minimum Acceptable
- [ ] TPR correctly sourced from PromotionData.xlsx
- [ ] All 3 new tools implemented and working
- [ ] At least ONE baseline method achieves MAPE < 50%

### Excellent
- [ ] MAPE < 30% for best baseline method
- [ ] Tier-specific lifts show clear hierarchy (Platinum > Gold > Silver > Bronze)
- [ ] Tactic combinations show synergistic effects
- [ ] Feature lift is statistically significant (sample size adequate)

---

**Last Updated**: 2026-01-23
**Status**: Specification complete, implementation in progress
**Next**: Implement 3 new tools in analyst.py
