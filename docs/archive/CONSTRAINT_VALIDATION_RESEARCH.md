# Constraint Validation Research - Agent C (Auditor)

**Research Date**: 2026-01-24
**Purpose**: Identify best practices for automated constraint validation in promotional calendar systems
**Target**: Design Agent C (The Auditor) for TPO system

---

## Executive Summary

Agent C must be a **strict, deterministic constraint validator** that checks promotional calendars against business rules. Research shows the optimal approach combines:
1. **Rules Engine Pattern** - Deterministic, externalized rule validation
2. **LLM-Powered Feedback Generation** - Natural language violation explanations
3. **Multi-Tier Severity System** - Critical (REJECT), Warning (flag but allow)
4. **Comprehensive Audit Trails** - Detailed violation logs for debugging

---

## 1. Constraint Satisfaction Problems (CSP) in Scheduling

### Overview
Constraint satisfaction is a proven technology for modeling and solving combinatorial optimization problems. Many scheduling and timetabling problems can be formulated as CSPs.

**Key Definition**: A feasible solution to a CSP is a complete assignment of variables satisfying ALL constraints. An optimal solution minimizes/maximizes an objective function while maintaining feasibility.

### Application to Promotion Scheduling
- **Variables**: PPG, Retailer, Week, Discount Depth, Display Tier, Feature
- **Constraints**: Budget limits, gap rules, frequency limits, blackout weeks
- **Validation**: Check if calendar is a feasible solution (all constraints satisfied)

**Source**: [ICAPS 2004 Tutorial - Constraint Satisfaction for Planning and Scheduling](https://ktiml.mff.cuni.cz/~bartak/ICAPS2004/)

---

## 2. Rules Engine Design Pattern

### Core Principles

**Separation of Concerns**: Business rules externalized from core application logic
- Rules can be updated without modifying codebase
- Clear documentation of business policies
- Independent testing of rule logic

**Deterministic Validation**: Rule engines work like checklists
- Preset criteria evaluated consistently
- No randomness or probabilistic decisions
- Repeatable results for same input

**Benefits**:
- **Maintainability**: Rules are easy to review and update
- **Transparency**: Clear separation between rules and application code
- **Auditability**: Explicit rule violations with traceable logic

### Validation System Design

**Traditional Approach** (Recommended for Agent C):
```
FOR EACH constraint IN constraint_set:
    result = evaluate_constraint(calendar)
    IF result == VIOLATED:
        violations.append({
            "type": constraint.name,
            "severity": constraint.severity,
            "details": constraint.explain_violation()
        })

IF violations.has_critical():
    STATUS = REJECTED
ELSE:
    STATUS = APPROVED
```

**Why NOT purely LLM-based validation**:
- LLMs can be non-deterministic (different results for same input)
- Financial/compliance decisions require 100% consistency
- Hard constraints (budget, gaps) need mathematical precision

**Why USE LLMs for Agent C**:
- Generate natural language explanations of violations
- Suggest remediation strategies
- Prioritize violations by business impact
- Provide contextual feedback to Agent B

**Sources**:
- [Rules Engine Design Pattern - Nected](https://www.nected.ai/blog/rules-engine-design-pattern)
- [Rules Design Pattern - Michael Whelan](https://www.michael-whelan.net/rules-design-pattern/)

---

## 3. Financial Compliance Automation

### Recent Academic Research (January 2025)

**Compliance-to-Code Framework**:
- "First large-scale dataset dedicated to financial regulatory compliance"
- Transforms compliance rules into "deterministic Python code mappings"
- Provides "detailed code reasoning and code explanations to facilitate automated auditing"

**Key Insight**: Modern compliance systems combine:
1. **Deterministic validation logic** (Python code enforcing rules)
2. **LLM-powered explanations** (natural language reasoning)
3. **Audit trails** (comprehensive documentation of decisions)

### Validation Best Practices

**Business Rule Enforcement**:
- Transform documented policies (e.g., "purchases over $10,000 require director approval") into executable validation logic
- System validates rule satisfaction, not just field completion
- Example: Check that approval EXISTS and AMOUNT < $10,000, not just that signature field is populated

**Benefits of Automated Validation**:
- "40% cost reductions" in compliance operations (financial services)
- Eliminates manual errors and inconsistencies
- Precise data validation with comprehensive audit trails

**Implementation Pattern**:
```python
# WRONG: Just check field exists
if calendar.get("budget_field"):
    return PASS

# CORRECT: Validate actual constraint
total_spend = calculate_total_spend(calendar)
if total_spend > budget_limit:
    return VIOLATED("Budget exceeded: ${total_spend} > ${budget_limit}")
```

**Sources**:
- [Compliance-to-Code (arXiv, Jan 2025)](https://arxiv.org/abs/2505.19804)
- [Neuro-Symbolic Compliance (arXiv, Jan 2025)](https://arxiv.org/html/2601.06181)

---

## 4. Retail Promotion Constraint Types

### Budget Constraints
**Definition**: Total promotion spend ≤ allocated budget
**Validation**: Sum all TPR costs + display fees across calendar
**Industry Practice**: "Budget constraints allow controlling promotion budgets by setting safety limits that automatically deactivate promotions if limits are reached"

### Gap Rules (Minimum Spacing)
**Definition**: Minimum weeks between promotions for same PPG-Retailer
**Typical Values**: 2-4 weeks in retail industry
**Validation**: For each PPG-Retailer, check week gaps between consecutive promos
**Example**: If PPG "Brand 1_Group 20" at Retailer A has promos in weeks [5, 8, 15], gaps are [3, 7]. If min gap = 4, week 8 VIOLATES (gap of 3 < 4).

### Frequency Limits (Maximum Promotions)
**Definition**: Maximum number of promotions per PPG per year
**Industry Practice**: Prevents promotion fatigue and margin erosion
**Validation**: Count promotions per PPG across all weeks
**Granularity**: Can be PPG-only or PPG-Retailer specific

### Blackout Periods
**Definition**: Weeks where promotions are prohibited
**Common Retail Blackouts**:
- Inventory/fiscal year-end periods
- Product launch windows (to measure organic demand)
- Major competitor promotion periods (avoid price wars)
**Validation**: Check no promotions scheduled in blackout week list

**Sources**:
- [Validation Rules Definition - Voucherify](https://www.voucherify.io/glossary/validation-rules)
- [Retail Blackout Periods - myshyft.com](https://www.myshyft.com/blog/blackout-period-management/)

---

## 5. Promotional Compliance in Practice

### Industry Approaches

**Compliance Monitoring**:
- "Half of retailers have clearly documented processes to ensure proper execution"
- Common methods: Centralized oversight (18%), guidelines (21%), dedicated staff (34%), technology tools (11%), verification/monitoring (16%)

**Audit Mechanisms**:
- Photo submissions or signed checklists for verification
- Secret shoppers for in-store validation
- Automated systems for pricing/promotion compliance

**Real-Time Validation**:
- "Near-real time data systems designed to quickly locate compliance issues"
- "Real-time item- and store-level insight into live promotions"

**Key Takeaway**: Modern systems favor **automated, real-time validation** over manual post-hoc audits.

**Sources**:
- [In-store Promotional Compliance - Colateral.io](https://colateral.io/en/blog/5-step-process-to-ensure-promotional-compliance/)
- [Promotion Compliance Solution - Datasembly](https://datasembly.com/promotion-compliance-solution/)

---

## 6. Validation Rule Implementation Patterns

### Multi-Tier Severity System

**Critical Violations** (Auto-reject):
- Budget exceeded
- Gap rule violations
- Blackout period violations
- Negative margins

**Warnings** (Flag but allow):
- Near budget limit (>90%)
- Uneven PPG distribution
- Low expected ROI

**Implementation**:
```python
class ConstraintViolation:
    type: str  # "Budget", "Gap Rule", "Frequency", "Blackout"
    severity: str  # "CRITICAL", "WARNING"
    details: str  # "Week 12 and 14 for PPG X violate 4-week gap"
    affected_items: list  # [{week: 12, ppg: "X"}, {week: 14, ppg: "X"}]

audit_result = {
    "status": "REJECTED" if has_critical_violations else "APPROVED",
    "violations": [...],
    "warnings": [...],
    "feedback": "Increase spacing between weeks 12 and 14..."
}
```

### Validation Order (Performance Optimization)

1. **Fast checks first** (budget calculation)
2. **PPG-level checks** (frequency limits)
3. **Pairwise checks** (gap rules - O(n²) complexity)
4. **Aggregate checks** (retailer balance, seasonality spread)

**Rationale**: Fail fast on critical violations before expensive computations.

---

## 7. Expected Performance Benchmarks

### Success Metrics

**Accuracy**:
- **100% precision** on constraint violations (no false positives)
- **100% recall** on violations (no false negatives)
- Deterministic (same input → same output, always)

**Performance**:
- Validate 52-week calendar in **< 1 second** (simple arithmetic operations)
- Handle 100+ promotion events efficiently

**Explainability**:
- Every violation includes:
  - Type of constraint violated
  - Specific weeks/PPGs affected
  - Quantitative details (e.g., "Budget exceeded by $50K")
  - Suggested remediation

**Iteration Support**:
- Provide actionable feedback to Agent B
- Track violations across rejection loop iterations
- Detect if Agent B is making progress

### Industry Standards

**Compliance Validation**:
- Financial services: 40% cost reduction with automation
- Retail: 50%+ of companies use documented compliance processes
- Validation rules applied automatically with comprehensive audit trails

---

## 8. Recommended Architecture for Agent C

### Hybrid LLM + Deterministic Approach

**Tools (Deterministic Validation)**:
1. `calculate_total_spend()` - Sum TPR + display costs
2. `check_gap_violations()` - Verify min spacing per PPG-Retailer
3. `check_frequency_violations()` - Count promos per PPG
4. `check_blackout_violations()` - Check weeks against blackout list
5. `check_financial_violations()` - Verify no negative margins
6. `save_audit_report()` - Save validation results as JSON

**LLM Role (Feedback Generation)**:
- Read tool results (violation details)
- Generate natural language explanation
- Suggest specific remediation actions
- Prioritize violations by business impact
- Maintain strict APPROVED/REJECTED status based on critical violations

**System Prompt Philosophy**:
```
You are Agent C, the compliance auditor. You are STRICT and DETERMINISTIC.

Your task: Validate promotional calendars against business constraints.

Constraints:
1. Budget: Total spend ≤ ${budget}
2. Gap Rule: Min ${min_gap} weeks between promos per PPG-Retailer
3. Frequency: Max ${max_promos} promos per PPG per year
4. Blackouts: No promos in weeks ${blackout_weeks}
5. Financial: No negative margins

Validation Process:
1. Call all validation tools systematically
2. Aggregate violations by severity (CRITICAL vs WARNING)
3. If ANY critical violation: Status = REJECTED
4. If ZERO critical violations: Status = APPROVED
5. Provide detailed, actionable feedback for each violation

Be precise. Be deterministic. Be helpful.
```

**Why This Approach**:
- ✅ Deterministic validation (financial compliance requirement)
- ✅ Natural language feedback (helps Agent B understand violations)
- ✅ Audit trail (tool calls + LLM reasoning visible in logs)
- ✅ Agentic behavior (LLM decides how to explain violations)

---

## 9. Key Findings Summary

| Aspect | Recommendation | Source |
|--------|---------------|---------|
| **Validation Logic** | Deterministic (Python tools), not LLM-based | Financial compliance research |
| **Feedback Generation** | LLM-powered natural language | Compliance-to-Code (2025) |
| **Constraint Types** | Budget, Gap, Frequency, Blackout, Financial | Retail promotion best practices |
| **Status Decision** | Binary (APPROVED/REJECTED) based on critical violations | Rules engine pattern |
| **Performance** | < 1 second validation time | Real-time compliance systems |
| **Explainability** | Detailed violation logs with remediation suggestions | Compliance audit standards |
| **Architecture** | Hybrid LLM + Tools (like Agent A) | Agent SDK best practices |

---

## 10. Research Sources

1. **Constraint Satisfaction**: ICAPS 2004 Tutorial - "Constraint Satisfaction for Planning and Scheduling"
2. **Rules Engine Pattern**: Nected, Michael Whelan, DevIQ (2024)
3. **Financial Compliance**: arXiv papers on Compliance-to-Code and Neuro-Symbolic Compliance (Jan 2025)
4. **Promotion Validation**: Voucherify, Microsoft Learn, Retail Pro documentation
5. **Retail Compliance**: Datasembly, Colateral.io, Assosia promotional compliance solutions
6. **Blackout Periods**: VacationTracker, myshyft.com, Shopify retail scheduling guides

---

## Next Steps

1. ✅ Research completed
2. ⏭️ Create Agent C specification (`docs/specs/agent_c_auditor_spec.md`)
3. ⏭️ Implement LLM-powered Auditor with 6 tools
4. ⏭️ Test with mock calendars (valid, budget violation, gap violation, frequency violation, blackout violation)
5. ⏭️ Validate 100% accuracy on constraint detection

**Expected Effort**: 2-3 hours for implementation + testing

---

**Document Version**: 1.0
**Last Updated**: 2026-01-24
