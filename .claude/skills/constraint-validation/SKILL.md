---
name: constraint-validation
description: Compliance checking and constraint validation techniques for TPO Agent C (Auditor)
---

# Constraint Validation and Compliance Checking

This skill provides specialized knowledge for implementing Agent C (The Auditor) - the Compliance & Finance Guardrail.

## Core Principles

### Deterministic Validation

Agent C must be **strict and deterministic**:
- No creativity or optimization suggestions
- Binary outcomes: APPROVED or REJECTED
- Clear, actionable feedback only
- Zero tolerance for violations

### Validation Categories

1. **Financial Constraints** (Budget compliance)
2. **Operational Constraints** (Gap rules, frequency limits)
3. **Retailer Constraints** (Slotting availability)
4. **Business Rules** (Margin thresholds, SKU eligibility)

## Budget Validation

### Total Spend Calculation

**Components**:

1. **TPR (Temporary Price Reduction) Cost**:
   ```python
   for event in calendar_events:
       regular_price = financials[event['sku']]['regular_price']
       discount_amount = regular_price * event['discount_depth']
       promoted_units = calculate_promoted_volume(event)
       tpr_cost = discount_amount * promoted_units
   ```

2. **Display Cost** (Fixed Fee):
   ```python
   display_cost = display_fee if event['display_active'] else 0
   ```

3. **Total Event Cost**:
   ```python
   event_total = tpr_cost + display_cost
   ```

4. **Annual Aggregate**:
   ```python
   total_annual_spend = sum(event_total for all events)
   ```

### Validation Rule

```python
if total_annual_spend > budget_limit:
    violation = {
        "type": "Total Budget Exceeded",
        "details": f"Total Annual Spend ${total_annual_spend:,.0f} exceeds Budget Limit ${budget_limit:,.0f} by ${excess:,.0f}.",
        "severity": "critical"
    }
```

### Feedback Generation

```python
if budget_exceeded:
    feedback = f"Reduce overall frequency or discount depth to bring Total Spend under ${budget_limit:,.0f}."
```

## Gap Rule Validation

### Rule Definition

**Constraint**: Minimum N weeks between promotions for the same SKU.

**Typical Values**: 4 weeks (from Constraints.json)

### Implementation

```python
def validate_gap_rules(events, min_gap_weeks=4):
    violations = []

    # Group events by SKU
    sku_events = {}
    for event in events:
        sku = event['sku']
        week = event['week']
        sku_events.setdefault(sku, []).append(week)

    # Check gaps for each SKU
    for sku, weeks in sku_events.items():
        sorted_weeks = sorted(weeks)

        for i in range(len(sorted_weeks) - 1):
            current_week = sorted_weeks[i]
            next_week = sorted_weeks[i + 1]
            gap = next_week - current_week

            if gap < min_gap_weeks:
                violations.append({
                    "type": "Gap Rule Violation",
                    "details": f"Week {current_week} and {next_week} for {sku} violate {min_gap_weeks}-week gap rule (actual gap: {gap} weeks).",
                    "severity": "high"
                })

    return violations
```

### Feedback Generation

```python
if gap_violations:
    feedback = "Increase spacing between promotions to meet minimum gap requirements."
```

## Frequency Limit Validation

### Rule Definition

**Constraint**: Maximum M promotions per SKU per year.

**Typical Values**: 10 promotions/year (from Constraints.json)

### Implementation

```python
def validate_frequency_limits(events, max_promotions_per_year=10):
    violations = []

    # Count promotions per SKU
    sku_counts = {}
    for event in events:
        sku = event['sku']
        sku_counts[sku] = sku_counts.get(sku, 0) + 1

    # Check frequency limits
    for sku, count in sku_counts.items():
        if count > max_promotions_per_year:
            violations.append({
                "type": "Frequency Limit Exceeded",
                "details": f"{sku} has {count} promotions, exceeding limit of {max_promotions_per_year}.",
                "severity": "high"
            })

    return violations
```

### Feedback Generation

```python
if frequency_violations:
    feedback = "Reduce the number of promotions per SKU to comply with frequency limits."
```

## Slotting Constraint Validation

### Rule Definition

**Constraint**: Retailer has limited promotional slots per week.

**Example**: Max 5 promotions per week across all SKUs.

### Implementation

```python
def validate_slotting_constraints(events, max_slots_per_week=5):
    violations = []

    # Count promotions per week
    week_counts = {}
    for event in events:
        week = event['week']
        week_counts[week] = week_counts.get(week, 0) + 1

    # Check slot availability
    for week, count in week_counts.items():
        if count > max_slots_per_week:
            violations.append({
                "type": "Slotting Constraint Violation",
                "details": f"Week {week} has {count} promotions, exceeding retailer slot limit of {max_slots_per_week}.",
                "severity": "medium"
            })

    return violations
```

## Financial Feasibility Validation

### Margin Threshold Check

**Rule**: Each promotion must maintain positive incremental margin.

```python
def validate_financial_feasibility(event, financials):
    sku = event['sku']
    unit_cost = financials[sku]['unit_cost']
    regular_price = financials[sku]['regular_price']
    discount_depth = event['discount_depth']

    promoted_price = regular_price * (1 - discount_depth)
    unit_margin = promoted_price - unit_cost

    if unit_margin <= 0:
        return {
            "type": "Negative Margin",
            "details": f"{sku} with {discount_depth*100}% discount results in negative margin (${unit_margin:.2f} per unit).",
            "severity": "critical"
        }

    return None  # No violation
```

### ROI Threshold Check (Optional)

**Rule**: Minimum ROI threshold for all promotions.

```python
def validate_roi_threshold(event, min_roi=1.0):
    incremental_revenue = event['incremental_revenue']
    promotion_cost = event['projected_spend']

    roi = incremental_revenue / promotion_cost if promotion_cost > 0 else float('inf')

    if roi < min_roi:
        return {
            "type": "Insufficient ROI",
            "details": f"Promotion ROI of {roi:.2f} below minimum threshold of {min_roi:.2f}.",
            "severity": "medium"
        }

    return None
```

## Audit Report Structure

### Complete Audit Report

```json
{
  "status": "REJECTED",
  "violations": [
    {
      "type": "Total Budget Exceeded",
      "details": "Total Annual Spend $1,150,000 exceeds Budget Limit $1,000,000 by $150,000.",
      "severity": "critical"
    },
    {
      "type": "Gap Rule Violation",
      "details": "Week 12 and 14 for SKU_123 violate 4-week gap rule (actual gap: 2 weeks).",
      "severity": "high"
    }
  ],
  "feedback": "Reduce overall frequency or discount depth to bring Total Spend under $1,000,000. Increase spacing between promotions to meet minimum gap requirements.",
  "total_violations": 2,
  "checks_performed": [
    "Budget Compliance",
    "Gap Rules",
    "Frequency Limits",
    "Slotting Constraints",
    "Financial Feasibility"
  ]
}
```

### Approved Report

```json
{
  "status": "APPROVED",
  "violations": [],
  "feedback": "All constraints satisfied. Calendar approved.",
  "total_violations": 0,
  "checks_performed": [
    "Budget Compliance",
    "Gap Rules",
    "Frequency Limits",
    "Slotting Constraints",
    "Financial Feasibility"
  ]
}
```

## Feedback Generation Strategy

### Combine Multiple Violations

```python
def generate_feedback(violations):
    if not violations:
        return "All constraints satisfied. Calendar approved."

    feedback_parts = []

    # Categorize violations
    budget_violations = [v for v in violations if 'budget' in v['type'].lower()]
    gap_violations = [v for v in violations if 'gap' in v['type'].lower()]
    frequency_violations = [v for v in violations if 'frequency' in v['type'].lower()]
    margin_violations = [v for v in violations if 'margin' in v['type'].lower()]

    # Priority order: Budget > Margin > Gap > Frequency
    if budget_violations:
        feedback_parts.append("Reduce overall frequency or discount depth to bring Total Spend under budget.")

    if margin_violations:
        feedback_parts.append("Remove or reduce discount depth on promotions with negative margins.")

    if gap_violations:
        feedback_parts.append("Increase spacing between promotions to meet minimum gap requirements.")

    if frequency_violations:
        feedback_parts.append("Reduce the number of promotions per SKU to comply with frequency limits.")

    return " ".join(feedback_parts)
```

## Validation Order

**Recommended sequence** for efficiency:

1. **Budget** - Fails fast if way over budget
2. **Margin Feasibility** - Prevent fundamentally unprofitable promotions
3. **Gap Rules** - Check temporal spacing
4. **Frequency Limits** - Check annual counts
5. **Slotting** - Check retailer capacity

## Common Pitfalls to Avoid

1. **Making Suggestions**: Don't tell Strategist HOW to fix, just WHAT is broken
2. **Partial Approval**: Status must be binary (APPROVED or REJECTED), never partial
3. **Crossing Boundaries**: Don't optimize or analyze, only validate
4. **Vague Feedback**: Be specific about which weeks/SKUs violate which rules
5. **Inconsistent Severity**: Use consistent severity levels (critical/high/medium/low)

## Edge Cases to Handle

1. **Multiple Violations Same SKU**: Report all, not just first
2. **Boundary Conditions**: Week 1 and Week 52 wrapping (if applicable)
3. **Missing Data**: Handle gracefully if financials incomplete
4. **Zero Promotions**: Approve empty calendars if requested
5. **Rounding Errors**: Use tolerance for floating-point comparisons (e.g., budget within $0.01)

## Integration with Orchestrator

The Auditor's role in the feedback loop:

```python
# Orchestrator calls Auditor after each Strategist proposal
audit_report = auditor.audit(draft_calendar)

if audit_report['status'] == 'REJECTED':
    # Pass feedback back to Strategist
    feedback = {
        'violations': audit_report['violations'],
        'feedback': audit_report['feedback']
    }
    # Strategist regenerates with this feedback
else:
    # APPROVED - exit loop
    final_calendar = draft_calendar
```

This creates the **rejection loop** that is critical for the hackathon judging criteria.
