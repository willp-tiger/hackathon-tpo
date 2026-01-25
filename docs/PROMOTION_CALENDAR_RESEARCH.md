# Promotion Calendar Generation Research

**Date**: 2026-01-24
**Purpose**: Research findings for Agent B (Strategist) specification
**Focus**: Multi-objective optimization, constraint satisfaction, iterative refinement

---

## Research Summary

This document synthesizes industry best practices and academic research on promotion calendar generation, multi-objective optimization, and constraint-based scheduling for Agent B implementation.

---

## 1. Multi-Objective Optimization in Trade Promotion

### Volume vs. Profit Trade-offs

**Source**: SoftServe, CPG Vision, River Logic (2024-2025)

Modern trade promotion optimization explicitly addresses competing objectives:

- **Volume Maximization**: "Which combination of events will have the greatest impact on volume?"
- **Profit Maximization**: "How do we maximize profit received for trade investment spent?"
- **Revenue Targets**: Ability to specify minimum targets as 'soft' constraints while optimizing for profit

**Key Insight**: Instead of evaluating a single promotion plan, modern TPO systems generate multiple scenarios, calculate projected performance, and rank them from strongest to weakest.

### Pareto Optimization

**Source**: Wikipedia - Multi-objective Optimization

Multi-objective optimization (Pareto optimization) deals with mathematical optimization problems involving more than one objective function, applied in economics and logistics where optimal decisions involve trade-offs between conflicting objectives.

**Implication for Agent B**:
- Cannot optimize for both volume AND profit simultaneously
- Must use user-specified objective to guide calendar generation
- Alternative: Generate Pareto-optimal frontier (advanced feature)

---

## 2. Constraint Satisfaction in Promotion Scheduling

### Types of Constraints

**Source**: Cognira, ClearDemand, ICAPS Conference

Retail promotion optimization includes several constraint types:

1. **Self Business Rules**: Constraints on individual promotion attributes
   - Budget limits (hard constraint)
   - Maximum discount depths per retailer
   - Blackout periods

2. **Cross-Item Business Rules**: Constraints across multiple promotions
   - Minimum gap between promotions (same PPG-Retailer)
   - Maximum frequency per PPG per year
   - Category conflict avoidance

3. **Inter-Item Ordinal Constraints**: Price relationships
   - Smaller sizes have lower prices than larger sizes
   - National brands more expensive than private labels

**Relevance to Agent B**: Must respect all constraint types defined in Constraints.json and validated by Agent C.

### Constraint Satisfaction Problem (CSP) Approaches

**Source**: UC Berkeley AI Course, ICAPS Planning School

CSP algorithms exploit problem structure for efficient solutions:

1. **Backtracking**: Systematic search with backtracking on constraint violations
2. **Forward Checking**: Check constraints before assigning values
3. **Constraint Propagation**: Reduce search space by inferring additional constraints
4. **Min-Conflicts**: Local search heuristic for many-variable problems

**Performance**: CSPs exhibit high complexity, requiring combination of heuristics and combinatorial search methods to solve in reasonable time.

---

## 3. Heuristic vs. Optimization Approaches

### Trade-offs

**Source**: ICRON, Management Science

**Exact Optimization**:
- ✅ Delivers optimal solution
- ❌ Computationally expensive
- ❌ Poor scalability to large instances
- **Use case**: Small/medium-size instances

**Heuristic Algorithms**:
- ✅ Fast and feasible short-term solutions
- ✅ Good scalability
- ❌ Unable to guarantee optimal solution (in vast majority of cases)
- **Use case**: Large instances, time-critical scenarios

### Hybrid Approaches

**Source**: Management Science, Springer Nature

**Constraint Programming + Greedy (CPIGA)**:
- Hybridizes Iterated Greedy Algorithm with CP model
- **Performance**: < 5% deviation from optimal solution
- **Advantage**: Balances speed and solution quality

**Matheuristic Algorithms**:
- Combine exact solution methods and heuristic procedures
- Use mathematical programming tools to explore solution space
- **Advantage**: Non-trivial optimization with practical runtime

**Recommendation for Agent B**: Greedy heuristic with constraint checking (fast, good enough for demo)

---

## 4. Promotion Vehicle Scheduling

### Problem Formulation

**Source**: Management Science - Cohen et al. (2017)

Scheduling promotion vehicles (displays, features, price discounts) to time periods as a **nonlinear bipartite matching problem** with capacity constraints.

**Key Findings**:
- Rigorous optimization approach increases retailer profit by **2% to 9%**
- Eight heuristics can approximate optimal solutions
- **Tabu search** and **branch-and-price** routines preferred for large instances

**Relevance**: Agent B allocates promotion tactics (discount + display tier + feature) to weeks, subject to constraints.

---

## 5. Iterative Refinement with Feedback

### Self-Refine: Iterative Refinement with Self-Feedback

**Source**: arXiv:2303.17651 (Madaan et al., 2023)

**Key Innovation**: LLM generates output, provides feedback, refines iteratively in a FEEDBACK → REFINE loop.

**Performance**:
- Outperforms direct generation from GPT-3.5/GPT-4 by **5% to 40%**
- Quality improves with number of iterations (e.g., Code Optimization: 22.0 → 28.8 after 3 iterations)
- No supervised training data, additional training, or RL required

**Critical Success Factor**: **Actionable feedback**
- ✅ Good: "Avoid repeated calculations in the for loop" (specific, actionable)
- ❌ Bad: "This code is inefficient" (generic, not actionable)

**Direct Application to Agent B → Agent C Loop**:
1. Agent B generates promotion calendar
2. Agent C validates constraints, provides **specific violation feedback**
3. Agent B refines calendar based on feedback
4. Repeat until APPROVED or max iterations

**Expected Improvement**: 5-40% better calendar quality through iterative refinement

### Constraint Violation Logging

**Source**: arXiv HeuriGym (Cornell, 2025)

After each iteration, log:
- LLM-generated solution
- Execution trace
- Verification result (APPROVED/REJECTED)
- Evaluation score (budget utilization, projected lift, etc.)
- Diagnostic messages from verifier

**Purpose**: Enables LLM to learn from past attempts and incrementally improve output.

**Implementation for Agent B**: Agent C audit report appended to Agent B conversation history.

---

## 6. Industry Benchmarks & Success Metrics

### Expected Performance

**Source**: Cognira, Tredence, IDC MarketScape (2024-2025)

**Modern TPO Systems**:
- Prescriptive recommendations accounting for cannibalization and halo effects
- Business constraints and objectives integrated
- AI-driven approaches for real-time market conditions

**Success Metrics**:
1. **Constraint Compliance**: 100% adherence to business rules (hard requirement)
2. **Budget Utilization**: 80-95% of allocated budget (underutilization = missed opportunity)
3. **Convergence Speed**: 3-5 iterations typical for constraint satisfaction
4. **Projected ROI**: 2-9% profit improvement vs. baseline planning

### Calendar Quality Indicators

**Good Calendar Characteristics**:
- ✅ Promotions scheduled during high-seasonality weeks
- ✅ High-elasticity PPGs receive deeper discounts
- ✅ Display tiers allocated based on ROI (Platinum/Gold for high-value promos)
- ✅ Even distribution across 52 weeks (avoid clustering)
- ✅ Retailer-specific constraints respected
- ✅ Explainable reasoning for each promotion decision

**Poor Calendar Indicators**:
- ❌ Promotions during blackout weeks
- ❌ Budget significantly under/over-utilized
- ❌ Repeated constraint violations (> 5 iterations)
- ❌ Unrealistic discount depths (> max allowed)
- ❌ Lack of reasoning/explanation

---

## 7. Recommended Approach for Agent B

### Algorithm Selection: **Greedy Heuristic with Iterative Refinement**

**Rationale**:
1. **Fast**: Can generate 52-week calendar in single LLM call
2. **Good Enough**: Heuristics achieve < 5% from optimal
3. **Explainable**: Each decision has clear reasoning
4. **Iterative**: Self-Refine pattern shows 5-40% improvement
5. **Constraint-Aware**: Agent C provides actionable feedback

### High-Level Algorithm

```
1. INITIALIZE (Iteration 0)
   - Load causal parameters from Agent A
   - Load constraints from Constraints.json
   - Parse user objective (volume or profit)
   - Set budget limit

2. GENERATE CALENDAR (Greedy Selection)
   For each PPG-Retailer combination:
     a. Rank weeks by seasonality (high → low)
     b. Select top N weeks (respecting frequency limit)
     c. For volume objective: prioritize high-elasticity PPGs
     d. For profit objective: prioritize high-margin PPGs
     e. Choose discount depth based on lift factors
     f. Allocate display tier based on ROI
     g. Add feature if incremental lift > cost
     h. Assign reasoning for each decision

3. VALIDATE (Agent C Call)
   - Send calendar to Agent C
   - Receive audit report (APPROVED/REJECTED + violations)

4. REFINE (If REJECTED)
   - Parse violation feedback
   - Adjust calendar:
     * Gap violations: Shift promotions to later weeks
     * Frequency violations: Remove lowest-ROI promotions
     * Budget violations: Reduce discount depths or remove displays
     * Blackout violations: Move to nearest non-blackout week
   - Document adjustments in reasoning

5. REPEAT Steps 3-4 until:
   - APPROVED by Agent C, OR
   - Max iterations reached (10), OR
   - No further improvements possible

6. OUTPUT
   - Final calendar JSON
   - Projected financial impact
   - Execution log with reasoning trace
```

### Tool Definitions (5 Tools)

1. **load_causal_parameters** - Load Agent A outputs
2. **generate_initial_calendar** - Greedy calendar generation
3. **adjust_calendar_for_violations** - Refine based on Agent C feedback
4. **calculate_projected_impact** - Estimate volume/profit/spend
5. **save_promotion_calendar** - Save final calendar as JSON

### System Prompt Philosophy

```
You are Agent B, the Strategist. Your goal is to generate a 52-week
promotion calendar that maximizes {objective} while respecting all constraints.

Approach:
1. Prioritize high-seasonality weeks for promotions
2. For volume: Focus on high-elasticity PPGs with deep discounts
3. For profit: Balance margin preservation with lift generation
4. Allocate premium display tiers (Platinum/Gold) to high-ROI promos
5. Explain EVERY decision with clear reasoning

When Agent C rejects your calendar:
- Read violations carefully
- Make SPECIFIC adjustments to address each violation
- Document what you changed and why
- Don't make cosmetic changes - fix root causes

Iterate until APPROVED or max attempts (10) reached.
```

---

## 8. Success Criteria for Agent B

### Must Have (MVP Requirements)

1. **Constraint Compliance**: Agent C approves calendar (APPROVED status)
2. **Budget Utilization**: 70-100% of allocated budget used
3. **Convergence**: Achieves APPROVED within 10 iterations
4. **Reasoning**: Every promotion has documented rationale
5. **Execution Log**: Full conversation trace showing iterations

### Nice to Have (Enhancements)

1. **Optimal Budget Use**: 85-95% utilization
2. **Fast Convergence**: < 5 iterations to APPROVED
3. **Seasonality Exploitation**: 80%+ of promos in top 50% seasonality weeks
4. **Display Optimization**: Platinum/Gold for top 20% high-value promos
5. **Multi-Scenario**: Generate 3 alternative calendars for comparison

### Performance Targets

| Metric | Target | Source |
|--------|--------|--------|
| Constraint Compliance | 100% | Hard requirement (Agent C) |
| Budget Utilization | 80-95% | Industry standard |
| Convergence Iterations | 3-5 | Self-Refine research |
| Projected ROI Improvement | 2-9% | Management Science (Cohen) |
| Calendar Generation Time | < 5 min | Practical usability |
| Reasoning Coverage | 100% | Explainability requirement |

---

## 9. Key Research Sources

### Academic Papers

1. **Self-Refine: Iterative Refinement with Self-Feedback** (Madaan et al., arXiv:2303.17651, 2023)
   - 5-40% improvement through feedback loops
   - Actionable feedback critical

2. **Scheduling Promotion Vehicles to Boost Profits** (Management Science, Cohen et al., 2017)
   - 2-9% profit improvement from optimization
   - Tabu search effective for large instances

3. **Constraint Programming + Greedy (CPIGA)** (ScienceDirect, 2023)
   - < 5% deviation from optimal
   - Hybrid approach balances speed and quality

4. **CSP Algorithms** (UC Berkeley AIMA, ICAPS)
   - Constraint propagation, min-conflicts heuristic
   - High complexity requires heuristics

### Industry Reports

5. **Cognira - Complete Guide to Retail Promotion Management** (2025)
   - Constraint types, cannibalization effects
   - Strategic planning and optimization

6. **Tredence - Trade Promotion Optimization Will Redefine Retail Success** (2025)
   - AI-driven recommendations
   - Real-time market conditions

7. **River Logic - Optimizing Trade Promotion Planning Process**
   - Volume/revenue targets as soft constraints
   - Scenario planning approach

8. **ICRON - Optimization vs. Heuristics**
   - Trade-offs between exact and heuristic methods
   - When to use each approach

### Additional Resources

9. **HeuriGym** (Cornell, arXiv:2506.07972, 2025)
   - Constraint violation logging
   - Learning from iterative attempts

10. **ClearDemand - Promotion Optimization Software**
    - Prescriptive recommendations
    - Business constraints integration

---

## 10. Implementation Recommendations

### Phase 4A: Agent B Specification (2 hours)

1. Create `docs/specs/agent_b_strategist_spec.md`
2. Define 5 tool schemas
3. Write system prompt (250-300 lines)
4. Specify success criteria with numbers
5. Document greedy algorithm logic

### Phase 4B: Agent B Implementation (3 hours)

1. Create `src/agents/strategist.py` (~700 lines)
2. Implement 5 tool functions
3. Multi-turn conversation loop
4. Integration with Agent A (load causal params)
5. Integration with Agent C (validation calls)

### Phase 4C: Testing (2 hours)

1. Create test fixtures (mock Agent A outputs)
2. Test volume objective calendar generation
3. Test profit objective calendar generation
4. Test rejection loop (simulate Agent C violations)
5. Verify convergence within 10 iterations

### Total Estimated Effort: 7 hours

---

**Next Steps**: Create Agent B specification document using these research findings.
