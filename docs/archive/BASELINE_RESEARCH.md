# Baseline Forecasting Research - TPO AI Agents

**Date**: 2026-01-23
**Purpose**: Research to address high MAPE (185-265%) in Agent A's baseline forecasting

---

## Problem Statement

Agent A's current baseline forecasting approaches show extremely high MAPE values:
- Regression approach: 185-265% MAPE
- SKU averages: 220-265% MAPE
- Global average: 185-224% MAPE

**Target**: Industry best practice is 10-15% MAPE for promotional forecasting with ML/AI methods

---

## Root Cause Analysis

### Critical Bug Identified

**Location**: `_tool_validate_baseline_forecast()` (lines 394-439 in analyst.py)

```python
# CURRENT (INCORRECT):
predicted = np.full(len(actual), baseline_avg)  # Uses single average for ALL predictions
```

**Problem**: Validation uses one global average to predict ALL future sales, completely ignoring:
- ❌ Week-to-week seasonality variations
- ❌ SKU-specific patterns
- ❌ Retailer differences
- ❌ Time trends

**Analogy**: Like predicting weather will always be 72°F regardless of season, location, or time of day.

### Secondary Issues

1. **Overly Simple Baseline Approaches**
   - Global average: One number for entire dataset
   - SKU averages: One number per SKU (ignores seasonality)
   - Regression: Trains on features but only returns mean prediction

2. **Poor Feature Engineering**
   - R² = 0.0172 (explains only 1.7% of variance)
   - Week-of-year dummies ignore SKU-specific seasonality
   - No interaction terms (SKU × Week, Retailer × SKU)
   - No handling of promotional carryover effects

3. **Missing Counterfactual Framework**
   - Not properly estimating "what would have sold WITHOUT promotion"
   - Confounding between price, displays, and seasonality

---

## Industry Research Findings

### MAPE Benchmarks (Source: Web search - RELEX Solutions, E2Open)

| Method | Promotional MAPE | Notes |
|--------|-----------------|-------|
| Traditional statistical methods | 30-40% | Industry baseline |
| AI/ML methods (best practice) | 10-15% | Modern retail systems |
| **Agent A (current)** | **185-265%** | **Needs significant improvement** |

**Acceptable thresholds by category**:
- Stable FMCG products: <15% MAPE
- Volatile/seasonal retail: <30% MAPE
- Fashion/short lifecycle: <40% MAPE

### Best Practices from Literature

#### 1. Separate Baseline from Promotional Lift
**Source**: Databricks Blog, Causal AI research

> "Modern systems create transparent forecasts that separate baseline demand, promotional impacts, and event-driven changes"

**Key insight**: Model baseline and lift SEPARATELY, not together.

#### 2. Counterfactual Estimation
**Source**: "Causal Inference for Price Optimization", Medium/TowardsDataScience

> "The core problem is that we don't have data on counterfactual outcome (baseline without promotion). We have to build a causal demand model to simulate counterfactual baseline."

**Recommended methods**:
- **Difference-in-Differences (DiD)**: Compare treated vs control groups over time
- **Matching methods**: Find similar non-promoted periods for comparison
- **Fixed effects models**: Control for SKU and time-specific factors

#### 3. STL Decomposition for Retail
**Source**: "Forecasting: Principles and Practice" (Hyndman), statsmodels docs

**STL = Seasonal-Trend-Loess decomposition**

**Advantages**:
- Seasonal component can change over time (not static)
- Robust to outliers
- Transparent and explainable
- Works well for SKU-level forecasting

**Best for**: Data with clear seasonal patterns that evolve

#### 4. Multiple Validation Metrics
**Source**: RELEX Solutions, MAPE best practices

**Don't rely only on MAPE**:
- **Bias**: Detects systematic over/under-forecasting
- **RMSE**: Penalizes large errors more than MAPE
- **MAE**: More robust to outliers than MAPE
- **Tracking signal**: Detects when forecast goes off-track

---

## Recommended Implementation

### Priority 1: Fix Validation Logic (CRITICAL)

**Change validation to use proper counterfactual estimation:**

```python
# IMPROVED APPROACH:
# For each test observation, predict using its SPECIFIC SKU + Week-of-Year
# Not a single global average

def _tool_validate_baseline_forecast_improved(approach_name, holdout_weeks):
    # Get test data
    test_non_promo = test_df[test_df['TPR'] == 0]

    # For SKU-Week approach: lookup baseline[sku][week]
    # For regression approach: predict using actual features (SKU, week, trend)
    # For STL approach: use (trend + seasonal) components per SKU

    predictions = []
    for idx, row in test_non_promo.iterrows():
        sku = row['APN']
        week = row['week_of_year']

        # Get prediction for THIS SPECIFIC SKU-WEEK combination
        pred = get_baseline_for_sku_week(approach_name, sku, week)
        predictions.append(pred)

    mape = calculate_mape(actual, np.array(predictions))
```

### Priority 2: Implement SKU-Week Fixed Effects

**Method**: Historical average for each (SKU, Week-of-Year) combination

**Why**:
- Captures SKU-specific seasonality naturally
- Simple, interpretable, robust
- Research shows "historical averages under matching conditions" often outperform complex models

**Implementation**:
```python
def _tool_calculate_baseline_sku_week_fixed_effects():
    non_promo = sales_data[sales_data['TPR'] == 0]

    # Create lookup table: baseline[sku][week_of_year] = avg_sales
    baseline_lookup = (
        non_promo.groupby(['APN', 'week_of_year'])['Unit.Sales']
        .mean()
        .to_dict()
    )

    # For SKU-weeks with no non-promo history, fallback to SKU average
    sku_averages = non_promo.groupby('APN')['Unit.Sales'].mean()

    return baseline_lookup, sku_averages
```

### Priority 3: Implement STL Decomposition

**Method**: Decompose each SKU's time series into Trend + Seasonal + Residual

**Why**:
- Handles evolving seasonality (not static like regression dummies)
- Robust to promotional outliers
- Baseline = Trend + Seasonal (exclude residual)

**Implementation**:
```python
from statsmodels.tsa.seasonal import STL

def _tool_calculate_baseline_stl_decomposition(seasonal_period=52):
    baseline_predictions = {}

    for sku in sales_data['APN'].unique():
        sku_data = sales_data[sales_data['APN'] == sku].sort_values('Date')

        # STL decomposition (requires evenly spaced data)
        stl = STL(sku_data['Unit.Sales'], seasonal=seasonal_period)
        result = stl.fit()

        # Baseline = Trend + Seasonal (exclude residual/noise)
        baseline = result.trend + result.seasonal

        baseline_predictions[sku] = baseline

    return baseline_predictions
```

### Priority 4: Add Multiple Validation Metrics

**Enhance validation to return comprehensive metrics:**

```python
def _enhanced_validation(actual, predicted):
    mape = calculate_mape(actual, predicted)
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    bias = np.mean(predicted - actual) / np.mean(actual)  # % bias

    return {
        "mape": mape,
        "mae": mae,
        "rmse": rmse,
        "bias_pct": bias * 100,
        "interpretation": {
            "mape": "Average % error (lower is better, target <15%)",
            "bias_pct": "Systematic over(+) or under(-) forecasting",
            "rmse": "Penalizes large errors more than MAE"
        }
    }
```

---

## Expected Impact

| Approach | Expected MAPE | Confidence | Effort |
|----------|---------------|------------|--------|
| **Fix validation bug** | 30-80% | High | Low (1 function fix) |
| **SKU-Week fixed effects** | 20-50% | High | Low (simple groupby) |
| **STL decomposition** | 15-40% | Medium | Medium (needs statsmodels) |
| **Quantile regression** | 25-60% | Medium | Low (use median instead of mean) |
| **Mixed effects model** | 15-35% | Medium | High (complex implementation) |

**Recommendation**: Start with fixing validation + SKU-Week approach (highest ROI, lowest risk)

---

## Implementation Plan

1. ✅ **Research completed** (this document)
2. ⏭️ **Fix validation logic** - Update `_tool_validate_baseline_forecast()`
3. ⏭️ **Implement SKU-Week fixed effects** - New tool
4. ⏭️ **Implement STL decomposition** - New tool (optional but recommended)
5. ⏭️ **Add multi-metric validation** - Enhance validation tool
6. ⏭️ **Update system prompt** - Guide Claude to try new approaches
7. ⏭️ **Test with real data** - Re-run Agent A with improved tools
8. ⏭️ **Document results** - Update CLAUDE.md with findings

---

## References

1. **RELEX Solutions** - "Measuring forecast accuracy: The complete guide" (2024)
2. **Hyndman & Athanasopoulos** - "Forecasting: Principles and Practice" (STL decomposition)
3. **Databricks Blog** - "Optimizing Promotional Offers using Causal Machine Learning"
4. **TowardsDataScience** - "Causal Inference in the Wild: Elasticity Pricing"
5. **E2Open** - "2018 Forecasting and Inventory Benchmark Study"
6. **ResearchGate** - "Retailer promotion planning: Improving forecast accuracy and interpretability"
7. **SpringerLink** - "Retail Promotion Forecasting: A Comparison of Modern Approaches"
8. **BMC Medical Research Methodology** - "Causal inference based on counterfactuals"

---

**Author**: Claude (Agent collaboration session)
**Next Steps**: Implement fixes in [src/agents/analyst.py](../src/agents/analyst.py)
