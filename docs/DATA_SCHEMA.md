# TPO Data Schema Documentation

**Generated**: 2026-01-23
**Validation Status**: ✅ Passed with warnings

This document describes the structure, relationships, and quality of all data files used in the TPO AI Agents system.

## Overview

The system uses **5 data files** covering ~112 weeks (2018-08-05 to 2020-09-27) across **2 retailers** and **57 products**.

### Data Files Summary

| File | Records | Key Fields | Purpose |
|------|---------|------------|---------|
| Sales.xlsx | 11,704 | Date, Retailer, APN, Unit.Sales, TPR | Historical weekly sales (source of truth) |
| PromotionData.xlsx | 845 | Date, Promo.Group, Retailer, promo types | Historical promotion tactics |
| Finance.xlsx | 108 | Retailer, PPG, List Price, Margin | Unit economics per product |
| Promo_config.csv | 7 | Promo Type, fixed Spend | Display promotion costs |
| Constraints.json | 2 | Retailer rules | Operational constraints per retailer |

---

## 1. Sales.xlsx

**Purpose**: Primary dataset for causal inference and baseline forecasting. Contains weekly sales records with promotion indicators.

### Schema

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| Date | datetime | Week ending date | Weekly granularity, 7-day intervals |
| Retailer | str | Retailer identifier | "Retailer 0" or "Retailer 1" |
| APN | str | Product identifier | 57 unique products |
| Promo.Group | str | Promotion group | 10 groups for aggregation |
| Description | str | Product description | |
| Category, Sub.Category | str | Product hierarchy | |
| Segment, Sub.Segment | str | Market segment | ~5% missing in Sub.Segment |
| Manufacturer, Brand, Sub.Brand | str | Brand hierarchy | |
| Packsize, Product.Type | str | Product attributes | |
| Unit.Sales | float | Units sold | 6 negative values (returns?), 5,083 zeros (43.4%) |
| Val.Sales | float | Sales value ($) | |
| Vol.Sales | float | Volume in **tonnes** (metric tons) | Formula: Unit.Sales × Packsize_grams ÷ 1,000,000 |
| Wtd.Selling.Dist | float | Weighted distribution | |
| Unit.Price | float | Actual unit price | |
| Calculated_Base_Price | float | Base price (no discount) | Used for discount calculation |
| TPR | float | Temporary Price Reduction % | 0-100, >0 indicates promotion (29.1% of records) |

### Key Statistics

- **Date Range**: 2018-08-05 to 2020-09-27 (~112 weeks)
- **Total Records**: 11,704
- **Retailers**: 2
- **Products (APNs)**: 57
- **Promo Groups**: 10
- **Promo Rate**: 29.1% of records have TPR > 0
- **Time Series**: Complete weekly data, 7-day intervals, no gaps

### Data Quality Notes

**Warnings:**
- 6 records with negative sales (likely returns or adjustments)
- 5,083 records (43.4%) with zero sales (products not available or no purchases)

**Discount Depth Analysis (TPR > 0):**
- Min discount: 5.04%
- Max discount: 100.00%
- Median discount: 37.17%
- 567 records (16.6%) have discount > 50%

---

## 2. PromotionData.xlsx

**Purpose**: Historical promotion tactics applied. Used to understand what promotion types were used and their timing.

### Schema

| Column | Type | Description | Values |
|--------|------|-------------|--------|
| Date | datetime | Promotion week | |
| PPG | str | Product-Promo Group identifier | Format: "Brand X_Promo.Group Y" |
| Promo.Group | str | Promotion group | |
| Retailer | str | Retailer identifier | "Retailer 0" or "Retailer 1" |
| promo_tpr | float | TPR discount depth % | 0-100 |
| promo_feature | int | Feature promotion flag | 0/1 |
| display_platinum | int | Platinum display flag | 0/1 |
| display_gold | int | Gold display flag | 0/1 |
| display_silver | int | Silver display flag | 0/1 |
| display_bronze | int | Bronze display flag | 0/1 |

### Key Statistics

- **Date Range**: 2018-08-26 to 2020-09-27
- **Total Events**: 845
- **Promotion Type Usage**:
  - TPR: 259 events (avg depth: variable)
  - Feature: 141 events
  - Display Platinum: 86 events
  - Display Gold: 42 events
  - Display Silver: 58 events
  - Display Bronze: 128 events

---

## 3. Finance.xlsx

**Purpose**: Unit economics for each product. Used for profit calculations and margin analysis.

### Schema

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| Retailer | str | Retailer identifier | 1 null record |
| PPG | str | Product-Promo Group identifier | 57 unique (matches products in Sales) |
| Retailer Margin | float | Retailer margin % | |
| Key | str | Unique key | |
| Avg Price | str | Average selling price | 107 records have "#ERROR!" |
| List Price | float | List price | Range: $0.00 to $4.32 |

### Key Statistics

- **Total Records**: 108 (57 PPGs × ~2 retailers)
- **Unique PPGs**: 57 (matches APN count in Sales)
- **Unique Retailers**: 2

### Data Quality Notes

**Warnings:**
- 107 records (99%) have "#ERROR!" in Avg Price column
- Use List Price instead of Avg Price for financial calculations
- 1 record has null Retailer (needs investigation)

---

## 4. Promo_config.csv

**Purpose**: Fixed costs for display promotions. Used for budget calculations.

### Schema

| Promo Type | Fixed Spend (USD) |
|------------|------------------|
| promo_tpr | - (variable cost) |
| display_platinum (per week) | $500 |
| display_gold (per week) | $400 |
| display_silver (per week) | $350 |
| display_bronze (per week) | $300 |
| promo_feature | (not listed - assume no direct cost?) |

### Key Notes

- **TPR Cost**: Not a fixed cost - calculated based on discount depth and volume
- **Display Costs**: Weekly flat fees per display type
- **Feature Cost**: Not specified in config (may be included in TPR or negligible)

---

## 5. Constraints.json

**Purpose**: Operational constraints that Agent C (Auditor) must validate. These are hard rules that cannot be violated.

### Schema (Per Retailer)

**Note**: The JSON file has malformed structure with duplicate keys. Constraints are hardcoded in DataLoader.

#### Retailer 1 Constraints

```json
{
  "budget_enforcement_level": "Strict",
  "min_gap_weeks": 2,
  "max_promo_frequency": 12,
  "max_discount_depth": 0.25,
  "blackout_weeks": [47, 49, 51, 52],
  "max_display_slots_per_week": 3
}
```

#### Retailer 0 Constraints

```json
{
  "budget_enforcement_level": "Strict",
  "min_gap_weeks": 4,
  "max_promo_frequency": 8,
  "max_discount_depth": 0.40,
  "blackout_weeks": [44, 25, 51, 52],
  "max_display_slots_per_week": 3
}
```

### Constraint Definitions

| Constraint | Description | Retailer 0 | Retailer 1 |
|------------|-------------|------------|------------|
| budget_enforcement_level | Budget must be respected | Strict | Strict |
| min_gap_weeks | Minimum weeks between promotions for same product | 4 weeks | 2 weeks |
| max_promo_frequency | Maximum promotions per product per year (52 weeks) | 8 | 12 |
| max_discount_depth | Maximum allowed discount (0-1) | 40% | 25% |
| blackout_weeks | Weeks when no promotions allowed | [44,25,51,52] | [47,49,51,52] |
| max_display_slots_per_week | Max products on display simultaneously | 3 | 3 |

**Critical for Agent C**: These are HARD constraints. Any violation = rejection in the feedback loop.

---

## Data Relationships

### Linkage Keys

```
Sales.xlsx
  ├─ Retailer ──┬──> PromotionData.xlsx (Retailer)
  │             └──> Finance.xlsx (Retailer)
  │
  ├─ Promo.Group ──> PromotionData.xlsx (Promo.Group)
  │
  └─ [APN + Brand + Promo.Group] ──> Finance.xlsx (PPG)
       Format: "Brand X_Promo.Group Y_APN Z"
```

### Key Join Logic

1. **Sales ↔ Finance**:
   - Sales has `APN`, `Brand`, `Promo.Group`
   - Finance has `PPG` (combined format)
   - Join: Construct PPG from Sales columns or parse PPG to extract components

2. **Sales ↔ Promotions**:
   - Join on: `Retailer`, `Promo.Group`, `Date`
   - Note: Promotions data starts 3 weeks after Sales data

3. **Finance ↔ Promo Config**:
   - No direct join (promo config is lookup table)
   - Use promo type from calendar to lookup cost

### Time Alignment

- **Sales Data**: 2018-08-05 to 2020-09-27 (start of timeseries)
- **Promo Data**: 2018-08-26 to 2020-09-27 (starts 3 weeks later)
- **Implication**: First 3 weeks of sales have no promo history data

---

## Data Preprocessing Guidelines

### For Agent A (Analyst)

1. **Load Sales data** from 'Sales' sheet
2. **Handle zero/negative sales**: Consider filtering or treating as missing for baseline
3. **Create base price reference**: Use `Calculated_Base_Price` for elasticity
4. **Split train/test**: Reserve last 12 weeks for validation (MAPE calculation)
5. **Group by Promo.Group**: May improve statistical power for causal inference

### For Agent B (Strategist)

1. **Use Finance data** for profit calculations (List Price - Cost)
2. **Load Promo Config** for display costs
3. **Reference constraints** per retailer when generating calendar
4. **Consider zeros**: 43% zero sales = some products rarely sold

### For Agent C (Auditor)

1. **Load constraints** for target retailer
2. **Validate each constraint type** separately
3. **Check budget**: TPR cost (dynamic) + Display costs (fixed)
4. **Cross-check blackout weeks** against calendar

---

## Validation Results

**Validation Script**: `scripts/validate_data.py`
**Status**: ✅ PASSED WITH WARNINGS

**Summary**:
- ✅ No critical issues
- ⚠️ 4 warnings (non-blocking):
  - 6 negative sales records
  - 5,083 zero sales records (43.4%)
  - 107 Finance records with #ERROR! in Avg Price
  - 1 Finance record with null Retailer

**All datasets are ready for agent implementation.**

---

## Next Steps

1. ✅ Data exploration complete
2. ⏭️ **Next**: Implement Agent A (Analyst) using this schema
3. Agent A should:
   - Use Sales data for baseline decomposition
   - Calculate elasticity from TPR vs. Unit.Sales
   - Generate causal parameters for Agent B

---

**Document Version**: 1.0
**Last Updated**: 2026-01-23
**Validated By**: scripts/validate_data.py
