---
name: causal-inference
description: Statistical methods for causal inference, baseline decomposition, and elasticity modeling for TPO Agent A
---

# Causal Inference for Trade Promotion Analysis

This skill provides specialized knowledge for implementing Agent A (The Analyst) - the Causal Inference Engine.

## Core Concepts

### Baseline Decomposition

**Objective**: Separate historical sales into Baseline (what would have sold anyway) and Incremental (lift from promotions).

**Methods**:

1. **Time Series Decomposition**
   ```python
   from statsmodels.tsa.seasonal import seasonal_decompose

   # Decompose sales into trend, seasonal, and residual
   decomposition = seasonal_decompose(sales_data, model='multiplicative', period=52)
   baseline = decomposition.trend * decomposition.seasonal
   ```

2. **Control Group Method** (if available)
   - Compare promoted stores vs. non-promoted stores
   - Difference-in-differences estimation

3. **Regression-based Approach**
   ```python
   # Regress sales on promotion indicators
   # Baseline = predicted sales when promo variables = 0
   import statsmodels.formula.api as smf

   model = smf.ols('sales ~ promo_flag + discount_depth + display', data=df)
   results = model.fit()
   baseline = results.predict(df.assign(promo_flag=0, discount_depth=0, display=0))
   ```

### Price Elasticity Calculation

**Definition**: Measures responsiveness of demand to price changes.

**Formula**: `Elasticity = % Change in Quantity / % Change in Price`

**Implementation Pattern**:

```python
import numpy as np
from sklearn.linear_model import LinearRegression

# Log-log regression for elasticity
df['log_quantity'] = np.log(df['quantity'])
df['log_price'] = np.log(df['price'])

model = LinearRegression()
model.fit(df[['log_price']], df['log_quantity'])

base_price_elasticity = model.coef_[0]  # Coefficient is the elasticity
```

**Discount Depth Lift Factors**:

For different discount levels (15%, 20%, 30%), calculate:
```python
for depth in [0.15, 0.20, 0.30]:
    promo_sales = df[df['discount_depth'] == depth]['quantity'].mean()
    baseline_sales = df[df['discount_depth'] == 0]['quantity'].mean()
    lift_factor = promo_sales / baseline_sales
```

### Display Mechanics Impact

**Objective**: Quantify the incremental lift from in-store displays.

**Approach**:
```python
# Compare promotions with and without display
with_display = df[(df['promo'] == 1) & (df['display'] == 1)]['quantity'].mean()
without_display = df[(df['promo'] == 1) & (df['display'] == 0)]['quantity'].mean()

display_lift_multiplier = with_display / without_display
```

### Seasonality Patterns

**Weekly Seasonality Factors**:

```python
# Calculate week-of-year seasonality index
weekly_avg = df.groupby('week_of_year')['sales'].mean()
overall_avg = df['sales'].mean()
seasonality_factors = (weekly_avg / overall_avg).to_dict()
```

## Validation Best Practices

### Holdout Validation

Always validate baseline forecast on recent data:

```python
# Split data: train on weeks 1-40, test on weeks 41-52
train_data = df[df['week'] <= 40]
test_data = df[df['week'] > 40]

# Fit model on training data
# Predict on test data
# Calculate MAPE
mape = np.mean(np.abs((actual - predicted) / actual))
```

**Target**: MAPE < 15% for good baseline quality

### Diagnostic Checks

1. **Residual Analysis**: Check for autocorrelation
2. **Stability Tests**: Ensure parameters don't shift over time
3. **Cross-validation**: Validate across different SKUs/time periods

## Output Format for Agent A

```json
{
  "baseline_velocity_avg": 150.0,
  "elasticity_model": {
    "base_price_elasticity": -2.1,
    "discount_lift_factors": {
      "depth_15_pct": 1.8,
      "depth_20_pct": 2.5,
      "depth_30_pct": 3.8
    }
  },
  "display_lift_multiplier": 1.4,
  "seasonality_factors": {
    "1": 0.95,
    "2": 0.98,
    ...
    "52": 1.15
  },
  "validation_metrics": {
    "mape": 0.12,
    "rmse": 22.5,
    "mae": 18.3
  }
}
```

## Common Pitfalls

1. **Overfitting**: Don't use too many parameters relative to data
2. **Ignoring Seasonality**: Always account for weekly/monthly patterns
3. **Selection Bias**: Promotions may target already-popular items
4. **Confounding Variables**: Competitor actions, weather, holidays

## References

- Time Series Analysis: statsmodels library
- Causal Inference: "Mostly Harmless Econometrics" by Angrist & Pischke
- Promotion Lift Measurement: IRI Academic Data Set documentation
