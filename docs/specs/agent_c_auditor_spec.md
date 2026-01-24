# Agent C: The Auditor - Technical Specification

**Version**: 1.0
**Created**: 2026-01-23
**Status**: Draft

---

## 1. Overview

### 1.1 Purpose

Agent C is the **compliance auditor** that validates promotion calendars against business constraints. It acts as a strict gatekeeper, ensuring all proposed calendars meet budget, spacing, frequency, and blackout requirements before approval.

### 1.2 Role in Multi-Agent System

- **Input**: Draft promotion calendar from Agent B (Strategist)
- **Output**: Audit report with APPROVED/REJECTED status + detailed violation feedback
- **Rejection Loop**: If rejected, Agent B receives feedback and regenerates calendar
- **Success Criteria**: Zero violations = APPROVED status

### 1.3 Key Characteristics

- **Deterministic**: Same calendar always produces same result
- **Strict**: ANY violation = REJECTED status
- **Detailed Feedback**: Each violation gets actionable guidance for Agent B
- **LLM-Powered**: Uses Claude to read constraints, analyze calendar, generate feedback

---

## 2. Responsibilities

### 2.1 Core Functions

1. **Load and validate constraint definitions**
2. **Parse promotion calendar JSON**
3. **Execute 5 constraint validation checks**:
   - Budget compliance (total spend ≤ budget limit)
   - Gap rules (min weeks between promos per PPG)
   - Frequency limits (max promos per PPG per year)
   - Blackout weeks (no promos in specified weeks)
   - Financial sanity (no negative margins)
4. **Generate detailed violation reports**
5. **Save audit results to JSON**

### 2.2 Out of Scope

- ❌ Calendar generation (Agent B's job)
- ❌ Optimization (Agent B's job)
- ❌ Forecasting/causal parameters (Agent A's job)
- ❌ Relaxing constraints (always enforce as-is)

---

## 3. Inputs

### 3.1 Draft Calendar (from Agent B)

**Format**: JSON
**File**: `outputs/draft_calendar_iteration_N.json`

**Schema**:
```json
{
  "metadata": {
    "objective": "Maximize Unit Volume" | "Maximize Profit",
    "budget_limit": 1000000,
    "iteration": 1,
    "total_projected_spend": 950000,
    "projected_outcome": "1.2M incremental units"
  },
  "calendar_events": [
    {
      "week": 12,
      "ppg": "Brand 5_Promo.Group 6",
      "retailer": "Retailer 0",
      "discount_depth": 0.30,
      "display_tier": "gold",
      "feature": false,
      "projected_lift": "3.8x baseline",
      "projected_cost": 45000,
      "reasoning": "High elasticity PPG during peak seasonality week"
    }
  ]
}
```

**Required Fields per Event**:
- `week` (1-52)
- `ppg` (string, must match data)
- `retailer` (string, must match data)
- `discount_depth` (0.0-1.0, e.g., 0.30 = 30% off)
- `display_tier` ("platinum" | "gold" | "silver" | "bronze" | null)
- `feature` (boolean)
- `projected_cost` (dollars)

### 3.2 Constraint Definitions

**Format**: Hardcoded in DataLoader (see `Constraints.json` is malformed)

**Constraints**:
```python
constraints = {
    "budget_limit": 1000000,  # From user input (main.py --budget)
    "gap_rule_weeks": 4,       # Min weeks between promos for same PPG
    "max_promos_per_ppg_per_year": 12,  # Max frequency
    "blackout_weeks": [52],    # No promos in week 52 (holiday shutdown)
    "min_margin_pct": 0.0      # No negative margins allowed
}
```

### 3.3 Financial Data (for margin checks)

**Source**: `case-data/Finance.xlsx`
**Columns**: List Price, Unit Cost

---

## 4. Outputs

### 4.1 Audit Report

**Format**: JSON
**File**: `outputs/audit_report_iteration_N.json`

**Schema**:
```json
{
  "status": "APPROVED" | "REJECTED",
  "iteration": 1,
  "calendar_id": "draft_calendar_iteration_1.json",
  "total_violations": 3,
  "validation_timestamp": "2026-01-23T10:30:00",
  "violations": [
    {
      "type": "Gap Rule Violation",
      "severity": "high",
      "details": "PPG 'Brand 5_Promo.Group 6' has promos in weeks 12 and 14 (2-week gap, requires 4-week minimum)",
      "affected_events": [
        {"week": 12, "ppg": "Brand 5_Promo.Group 6", "retailer": "Retailer 0"},
        {"week": 14, "ppg": "Brand 5_Promo.Group 6", "retailer": "Retailer 0"}
      ],
      "recommendation": "Move week 14 event to week 16 or later to meet 4-week gap requirement"
    },
    {
      "type": "Budget Violation",
      "severity": "critical",
      "details": "Total spend $1,050,000 exceeds budget limit $1,000,000 by $50,000",
      "affected_events": "all",
      "recommendation": "Remove lowest-ROI promotions or reduce discount depths to stay within budget"
    }
  ],
  "summary_feedback": "Calendar rejected due to 3 violations. Primary issues: Budget overspend by $50K and gap rule violations for 2 PPGs. Fix budget first (highest priority), then adjust spacing.",
  "validation_details": {
    "budget_check": {"passed": false, "total_spend": 1050000, "budget_limit": 1000000},
    "gap_rule_check": {"passed": false, "violations_count": 2},
    "frequency_check": {"passed": true, "violations_count": 0},
    "blackout_check": {"passed": true, "violations_count": 0},
    "margin_check": {"passed": true, "violations_count": 0}
  }
}
```

**Status Logic**:
- `APPROVED`: total_violations = 0
- `REJECTED`: total_violations > 0

---

## 5. Tool Definitions

Agent C has **6 tools** for validation:

### 5.1 load_calendar

**Purpose**: Load and parse draft calendar JSON
**Input**: `{"file_path": "outputs/draft_calendar_iteration_1.json"}`
**Output**:
```json
{
  "status": "loaded",
  "num_events": 45,
  "weeks_covered": [2, 5, 8, 12, ...],
  "ppgs_involved": ["Brand 5_Promo.Group 6", ...],
  "total_projected_spend": 950000
}
```

### 5.2 validate_budget

**Purpose**: Check total spend ≤ budget limit
**Input**: `{"budget_limit": 1000000}`
**Output**:
```json
{
  "passed": false,
  "total_spend": 1050000,
  "budget_limit": 1000000,
  "overspend": 50000,
  "overspend_pct": 5.0,
  "violation": {
    "type": "Budget Violation",
    "severity": "critical",
    "details": "Total spend $1,050,000 exceeds budget limit $1,000,000 by $50,000"
  }
}
```

### 5.3 validate_gap_rules

**Purpose**: Check min weeks between promos per PPG
**Input**: `{"min_gap_weeks": 4}`
**Output**:
```json
{
  "passed": false,
  "violations_count": 2,
  "violations": [
    {
      "ppg": "Brand 5_Promo.Group 6",
      "retailer": "Retailer 0",
      "week_pairs": [[12, 14], [14, 17]],
      "actual_gaps": [2, 3],
      "required_gap": 4,
      "recommendation": "Move week 14 promo to week 16+ and week 17 to week 18+"
    }
  ]
}
```

### 5.4 validate_frequency

**Purpose**: Check max promos per PPG per year
**Input**: `{"max_promos_per_ppg": 12}`
**Output**:
```json
{
  "passed": true,
  "violations_count": 0,
  "ppg_promo_counts": {
    "Brand 5_Promo.Group 6": 8,
    "Brand 4_Promo.Group 0": 12
  }
}
```

### 5.5 validate_blackout_weeks

**Purpose**: Check no promos in blackout weeks
**Input**: `{"blackout_weeks": [52]}`
**Output**:
```json
{
  "passed": false,
  "violations_count": 1,
  "violations": [
    {
      "week": 52,
      "events": [
        {"ppg": "Brand 1_Promo.Group 20", "retailer": "Retailer 0"}
      ],
      "recommendation": "Move week 52 events to week 51 or remove"
    }
  ]
}
```

### 5.6 save_audit_report

**Purpose**: Save final audit results
**Input**: `{"report": {...}, "file_path": "outputs/audit_report_iteration_1.json"}`
**Output**:
```json
{
  "status": "saved",
  "file_path": "outputs/audit_report_iteration_1.json"
}
```

---

## 6. System Prompt Design

### 6.1 Core Behavior

```
You are Agent C, the compliance auditor for trade promotion calendars.

Your role: STRICT enforcement of business constraints. You are NOT flexible.

Workflow:
1. Load draft calendar from Agent B
2. Run ALL 5 validation checks (budget, gap rules, frequency, blackout, margins)
3. If ANY check fails: status = REJECTED
4. If ALL checks pass: status = APPROVED
5. Provide detailed, actionable feedback for each violation

Constraint Definitions (ENFORCE EXACTLY):
- Budget: Total spend ≤ ${budget_limit}
- Gap Rule: Min {gap_weeks} weeks between promos for same PPG-Retailer
- Frequency: Max {max_promos} promos per PPG across all retailers per year
- Blackout Weeks: NO promos in weeks {blackout_list}
- Margins: NO promotions with negative margins

Feedback Quality:
- Be SPECIFIC: "Week 12 and 14 for PPG X violate 4-week gap" (not "gap violations found")
- Be ACTIONABLE: "Move week 14 to week 16+" (not "fix the gaps")
- Prioritize by severity: Budget violations are CRITICAL, gap violations are HIGH

Remember: You are the gatekeeper. Agent B needs clear feedback to fix issues.
```

### 6.2 Multi-Turn Conversation Pattern

**Turn 1**: Load calendar
**Turn 2**: Validate budget
**Turn 3**: Validate gap rules
**Turn 4**: Validate frequency
**Turn 5**: Validate blackout weeks
**Turn 6**: Generate summary feedback
**Turn 7**: Save audit report

Expected iterations: **7-10**

---

## 7. Success Criteria

### 7.1 Functional Requirements

- ✅ Detects ALL constraint violations (100% recall)
- ✅ Zero false positives (100% precision)
- ✅ Provides actionable feedback for Agent B
- ✅ Saves audit report to JSON
- ✅ Completes within 10 iterations

### 7.2 Quality Metrics

**Determinism**:
- Same calendar → same audit result (100% reproducibility)

**Feedback Quality**:
- Each violation has specific details (which PPGs, which weeks)
- Each violation has actionable recommendation
- Violations prioritized by severity

**Performance**:
- Execution time: < 30 seconds per audit
- Iteration count: 7-10 iterations

---

## 8. Test Plan

### 8.1 Unit Tests

**Test 1: Budget Violation**
```json
Input: Calendar with $1,050,000 spend, budget limit $1,000,000
Expected: REJECTED, 1 budget violation, overspend = $50,000
```

**Test 2: Gap Rule Violation**
```json
Input: PPG "Brand 5_Promo.Group 6" has promos in weeks 12, 14, 17
Expected: REJECTED, 2 gap violations (12→14: 2 weeks, 14→17: 3 weeks)
```

**Test 3: Frequency Violation**
```json
Input: PPG "Brand 4_Promo.Group 0" has 15 promos
Expected: REJECTED, 1 frequency violation (15 > 12 max)
```

**Test 4: Blackout Week Violation**
```json
Input: Event in week 52 (blackout)
Expected: REJECTED, 1 blackout violation
```

**Test 5: Clean Calendar**
```json
Input: Calendar with no violations
Expected: APPROVED, 0 violations
```

### 8.2 Integration Tests

**Test 6: Rejection Loop**
- Agent B generates calendar with violations
- Agent C rejects with feedback
- Agent B adjusts calendar
- Agent C approves on iteration 2

**Test 7: Multi-Violation Calendar**
- Calendar with budget + gap + blackout violations
- Agent C detects all 3 types
- Feedback prioritizes budget as critical

---

## 9. Implementation Notes

### 9.1 Gap Rule Calculation

For each PPG-Retailer combination:
1. Sort promos by week
2. Calculate gaps: `gap[i] = week[i+1] - week[i]`
3. If any gap < min_gap_weeks: VIOLATION

**Example**:
```
PPG "Brand 5_Promo.Group 6", Retailer 0:
Weeks: [12, 14, 18]
Gaps: [14-12=2, 18-14=4]
Min gap: 4 weeks
Result: Violation (gap 2 < 4)
```

### 9.2 Budget Calculation

```python
total_spend = sum([
    event['projected_cost']
    for event in calendar_events
])

if total_spend > budget_limit:
    violation = {
        "overspend": total_spend - budget_limit,
        "overspend_pct": (total_spend - budget_limit) / budget_limit * 100
    }
```

### 9.3 Frequency Calculation

```python
from collections import defaultdict

promo_counts = defaultdict(int)
for event in calendar_events:
    promo_counts[event['ppg']] += 1

violations = {
    ppg: count
    for ppg, count in promo_counts.items()
    if count > max_promos_per_ppg
}
```

---

## 10. Dependencies

### 10.1 Data Files

- Draft calendar: `outputs/draft_calendar_iteration_N.json`
- Finance data: `case-data/Finance.xlsx` (for margin checks)

### 10.2 Python Packages

- `anthropic` - Claude API client
- `pandas` - Data manipulation
- `json` - Calendar parsing
- `loguru` - Logging

### 10.3 Configuration

- Constraints hardcoded in `src/utils/data_loader.py`
- Budget limit from command-line argument (`--budget`)

---

## 11. Research Sources

1. **Constraint satisfaction problems (CSP)**
   - Standard validation patterns
   - Backtracking and feedback generation

2. **Retail promotion planning**
   - Industry gap rules (typically 2-6 weeks)
   - Frequency limits (10-15 promos per SKU per year)

3. **Business rule engines**
   - Violation severity classification
   - Actionable feedback generation

---

## 12. Open Questions

1. **Margin check implementation**: Do we calculate margin per event or just check for negatives?
2. **Gap rule granularity**: Is gap rule per PPG-Retailer or just PPG (aggregated across retailers)?
3. **Frequency limit scope**: Max promos per PPG across all retailers, or per PPG-Retailer?

**Current Assumptions**:
- Gap rule: Per PPG-Retailer (more strict)
- Frequency: Per PPG across all retailers (aggregated)
- Margin: Just check for negative margins (boolean pass/fail)

---

**End of Specification**
