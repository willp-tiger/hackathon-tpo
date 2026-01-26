# TPO Data Schema Documentation

**Generated**: 2026-01-23
**Updated**: 2026-01-23 (Session 4 - PPG Granularity Change)
**Validation Status**: ✅ Passed with warnings

This document describes the structure, relationships, and quality of all data files used in the TPO AI Agents system.

## Overview

The system uses **5+ data files** covering ~113 weeks (2018-08-05 to 2020-09-27) across **2 retailers** and **11 product groups (PPGs)**.

### ⚠️ CRITICAL: PPG-Retailer-Week Granularity

**UPDATED (Session 4)**: All forecasting, baseline calculations, and promotion calendars MUST use **PPG-level granularity**.

- **Primary data source**: `sales_v2.xlsx` (NOT Sales.xlsx!)
- Data structure: Each row = **PPG × Retailer × Week**
- **PPG** (Product Group) = Brand + Promo.Group combination (e.g., "Brand 5_Promo.Group 6")
- **DO NOT** use APN (individual SKU) level - that's the wrong granularity
- **DO NOT** aggregate across retailers
- Each PPG-Retailer combination has independent sales patterns
- Baselines must be calculated at **PPG-Retailer-Week** level
- Final promotion calendar must specify promotions per PPG + Retailer

**Granularity:**
- 11 unique PPGs
- 2 unique Retailers
- 113 unique Weeks
- 3,676 total rows in sales_v2.xlsx

### Data Files Summary

| File | Records | Key Fields | Purpose |
|------|---------|------------|---------|
| **sales_v2.xlsx** | **3,676** | **PPG, Retailer, Date, Unit.Sales, TPR** | **Primary sales data at PPG level** |
| ~~Sales.xlsx~~ | ~~11,704~~ | ~~APN~~ | ~~DEPRECATED - Wrong granularity (APN level)~~ |
| PromotionData.xlsx | 845 | Date, Promo.Group, Retailer, promo types | Historical promotion tactics |
| Finance.xlsx | 108 | Retailer, PPG, List Price, Margin | Unit economics per product |
| Promo_config.csv | 7 | Promo Type, fixed Spend | Display promotion costs |
| Constraints.json | 2 | Retailer rules | Operational constraints per retailer |

---

## 1. sales_v2.xlsx (Primary Sales Data)

**Purpose**: Primary dataset for causal inference and baseline forecasting. Contains weekly sales records at PPG (Product Group) level with promotion indicators.

**⚠️ CRITICAL**: This is the ONLY correct sales data file. Do NOT use Sales.xlsx (deprecated, wrong granularity).

### Schema

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| Date | datetime | Week ending date | Weekly granularity, 7-day intervals |
| Retailer | str | Retailer identifier | "Retailer 0" or "Retailer 1" |
| **PPG** | str | **Product Group identifier** | **11 unique product groups (Brand + Promo.Group)** |
| Promo.Group | str | Promotion group component | Part of PPG calculation |
| Category, Sub.Category | str | Product hierarchy | |
| Segment, Sub.Segment | str | Market segment | Some missing in Sub.Segment |
| Manufacturer, Brand, Sub.Brand | str | Brand hierarchy | Brand is part of PPG |
| Product.Type | str | Product type attribute | |
| Unit.Sales | float | Units sold | 592 zeros (16.1%), no negatives |
| Val.Sales | float | Sales value ($) | |
| Vol.Sales | float | Volume in **tonnes** (metric tons) | Formula: Unit.Sales × Packsize_grams ÷ 1,000,000 |
| Wtd.Selling.Dist | float | Weighted distribution | |
| Unit Price | float | Actual unit price | Note: no dot in column name |
| Price/kg | float | Price per kilogram | |
| ~~Calculated_Base_Price~~ | float | ~~Base price (no discount)~~ | **⚠️ UNRELIABLE - DO NOT USE** |
| **TPR** | float | **Temporary Price Reduction %** | **Merged from PromotionData.xlsx (promo_tpr × 100)** |
| **display_platinum** | int | Platinum display flag | Merged from PromotionData.xlsx |
| **display_gold** | int | Gold display flag | Merged from PromotionData.xlsx |
| **display_silver** | int | Silver display flag | Merged from PromotionData.xlsx |
| **display_bronze** | int | Bronze display flag | Merged from PromotionData.xlsx |
| **promo_feature** | int | Feature/ad flag | Merged from PromotionData.xlsx |

**Note**: Sheet name is 'Sales ' (with trailing space).

**⚠️ CRITICAL DATA QUALITY ISSUE**:
- `Calculated_Base_Price` column in sales_v2.xlsx is **unreliable and should not be used**
- TPR and promotion features are merged from PromotionData.xlsx during data loading

### Key Statistics

- **Date Range**: 2018-08-05 to 2020-09-27 (113 weeks)
- **Total Records**: 3,676
- **Retailers**: 2
- **Product Groups (PPGs)**: 11
- **PPG-Retailer Combinations**: 22 (11 × 2)
- **Promo Rate**: 26.0% of records have TPR > 0 (957 promotional periods)
- **Time Series**: Complete weekly data, 7-day intervals, no gaps

**Sample PPGs**:
- "Brand 5_Promo.Group 6"
- "Brand 4_Promo.Group 3"
- "Brand 1_Promo.Group 20"
- "Brand 5_Promo.Group 5"
- "Brand 5_Promo.Group 0"

### Data Quality Notes

**Good News:**
- No negative sales records (clean dataset)
- Only 592 records (16.1%) with zero sales (much lower than APN-level data)

**Discount Depth Analysis (TPR > 0):**
- Based on correct List Price from Finance.xlsx (not Calculated_Base_Price)
- Records with promotions: 957 (26.0% of data)
- TPR calculation is now accurate using Finance.xlsx List Price

### Comparison to Deprecated Sales.xlsx

| Metric | ❌ Sales.xlsx (Old) | ✅ sales_v2.xlsx (New) |
|--------|---------------------|------------------------|
| Granularity | APN (individual SKU) | PPG (Product Group) |
| Products | 57 APNs | 11 PPGs |
| Rows | 11,704 | 3,676 |
| Weeks | ~112 | 113 |
| Has PPG column | No (calculated) | Yes |
| Zero sales rate | 43.4% | 16.1% |
| Status | **DEPRECATED** | **ACTIVE** |

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
| PPG | str | Product-Promo Group identifier | Format: "Brand X_Promo.Group Y" |
| Retailer Margin | float | Retailer margin % | |
| Key | str | Unique key | |
| Avg Price | str | Average selling price | 107 records have "#ERROR!" |
| List Price | float | List price | Range: $0.00 to $4.32 |

### Key Statistics

- **Total Records**: 108
- **Unique PPGs**: Multiple (includes more granular breakdowns than sales_v2.xlsx)
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

**Note**: The JSON file has been fixed to proper JSON format and is now loaded directly by DataLoader.

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
sales_v2.xlsx
  ├─ Retailer ──┬──> PromotionData.xlsx (Retailer)
  │             └──> Finance.xlsx (Retailer)
  │
  ├─ Promo.Group ──> PromotionData.xlsx (Promo.Group)
  │
  └─ PPG ──> Finance.xlsx (PPG)
       Format: "Brand X_Promo.Group Y"
```

### Key Join Logic

1. **Sales ↔ Finance**:
   - Sales has `PPG` column (e.g., "Brand 5_Promo.Group 6")
   - Finance has `PPG` column (same format)
   - Join: Direct match on `PPG` and `Retailer`

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

1. **Load Sales data** using `data_loader.load_sales()` which loads sales_v2.xlsx and merges List Price from Finance.xlsx
2. **Work at PPG-Retailer-Week level**: Each baseline is PPG + Retailer + Week specific
3. **Handle zero sales**: 592 records (16.1%) with zero sales - treat as missing for baseline
4. **Use List Price for calculations**: List Price from Finance.xlsx is the correct base price (not Calculated_Base_Price)
5. **Split train/test**: Reserve last 12 weeks for validation (MAPE calculation)
6. **Promotion rate**: 26.0% of data has TPR > 0 (correct rate using List Price)

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
