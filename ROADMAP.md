# TPO Development Roadmap

This document provides a detailed task breakdown for implementing the Trade Promotion Optimization multi-agent system.

## Phase 1: Data Exploration & Validation ✅ COMPLETE

**Objective**: Understand the data structure, quality, and relationships before implementing agents.

**Completed**: 2026-01-23

### Tasks

1. **Load and Examine All Data Files**
   - [x] Load `Sales.xlsx` - understand schema, date ranges, SKUs (use 'Sales' sheet)
   - [x] Load `PromotionData.xlsx` - understand promotion types, costs, mechanics
   - [x] Load `Finance.xlsx` - understand unit economics, margins, pricing
   - [x] Load `Promo_config.csv` - understand display fees and configuration
   - [x] Load `Constraints.json` - understand validation rules

2. **Data Quality Assessment**
   - [x] Check for missing values (4.9% in Sub.Segment, 99% errors in Finance Avg Price)
   - [x] Validate date ranges and continuity (complete 7-day intervals, 112 weeks)
   - [x] Verify SKU consistency across files (57 products across all files)
   - [x] Identify outliers or anomalies (6 negative sales, 43.4% zero sales)
   - [x] Document data quirks or issues (documented in DATA_SCHEMA.md)

3. **Schema Documentation**
   - [x] Document column names and types for each file
   - [x] Identify primary keys and foreign keys
   - [x] Map relationships between files (SKU links, date links)
   - [x] Create data dictionary (docs/DATA_SCHEMA.md)

4. **Exploratory Data Analysis**
   - [x] Calculate summary statistics (11,704 records, 29.1% promo rate)
   - [x] Analyze promotion frequency and patterns (845 promo events)
   - [x] Examine price points and discount levels (5-100%, median 37%)
   - [x] Identify data patterns (Vol.Sales in tonnes, zero sales patterns)

5. **Data Validation Scripts**
   - [x] Create validation script `scripts/validate_data.py`
   - [x] Add data quality checks (nulls, duplicates, consistency, relationships)
   - [x] Update `data_loader.py` with correct sheet handling and validation
   - [x] Document expected data formats

**Deliverables**:
- ✅ Data schema documentation: `docs/DATA_SCHEMA.md`
- ✅ Updated `data_loader.py` with validation (Sales sheet, Constraints hardcoded)
- ✅ Validation script: `scripts/validate_data.py` (0 critical issues, 4 warnings)
- ✅ Summary of findings in CLAUDE.md

**Key Findings**:
- Vol.Sales is in tonnes (metric tons): `Unit.Sales × Packsize_grams ÷ 1,000,000`
- 43.4% zero sales records require careful baseline modeling
- Constraints differ by retailer (Retailer 0 stricter: 4-week gaps vs 2-week)
- Finance.xlsx Avg Price column has errors - use List Price instead
- Time series complete with 7-day intervals, no gaps

**Actual Effort**: 1.5 hours

---

## Phase 2: Agent A Implementation (The Analyst) ⏭️ NEXT

**Objective**: Implement causal inference engine for baseline and elasticity calculation.

**Conversation Focus**: "Implement Agent A (Analyst) with baseline decomposition and elasticity modeling"

**Skill to Use**: `/causal-inference`

**Prerequisites**: Phase 1 complete - data validated and documented

### Tasks

1. **Baseline Decomposition**
   - [ ] Implement time series decomposition method
   - [ ] Extract trend component
   - [ ] Extract seasonal component (weekly patterns)
   - [ ] Calculate baseline velocity (average non-promoted sales)
   - [ ] Validate baseline accuracy on holdout data

2. **Price Elasticity Calculation**
   - [ ] Implement regression-based elasticity model
   - [ ] Calculate base price elasticity coefficient
   - [ ] Calculate discount lift factors for 15%, 20%, 30% depths
   - [ ] Validate elasticity estimates

3. **Display Mechanics Impact**
   - [ ] Measure incremental lift from displays
   - [ ] Calculate display lift multiplier
   - [ ] Validate display impact across SKUs

4. **Seasonality Patterns**
   - [ ] Extract week-of-year seasonality factors
   - [ ] Calculate seasonal indices (52 weeks)
   - [ ] Validate seasonality patterns

5. **Validation & Testing**
   - [ ] Split data into train/test (holdout last 12 weeks)
   - [ ] Calculate MAPE on holdout period
   - [ ] Target: MAPE < 15% for baseline forecast
   - [ ] Create validation report

6. **Output Generation**
   - [ ] Generate `causal_parameters.json` with correct structure
   - [ ] Include all required fields (baseline, elasticity, display, seasonality)
   - [ ] Add validation metrics to output

**Deliverables**:
- Fully implemented `src/agents/analyst.py`
- Unit tests for all methods
- `causal_parameters.json` output
- Validation report showing MAPE < 15%

**Estimated Effort**: 3-4 hours

---

## Phase 3: Agent C Implementation (The Auditor)

**Objective**: Implement strict compliance validator (do before Agent B for testing).

**Conversation Focus**: "Implement Agent C (Auditor) with constraint validation"

**Skill to Use**: `/constraint-validation`

### Tasks

1. **Budget Validation**
   - [ ] Implement TPR cost calculation (variable spend)
   - [ ] Implement display cost calculation (fixed spend)
   - [ ] Calculate total annual spend
   - [ ] Compare against budget limit
   - [ ] Generate budget violation reports

2. **Gap Rule Validation**
   - [ ] Implement minimum gap checking (default: 4 weeks)
   - [ ] Group promotions by SKU
   - [ ] Check spacing between consecutive promotions
   - [ ] Generate gap violation reports

3. **Frequency Limit Validation**
   - [ ] Count promotions per SKU per year
   - [ ] Check against maximum limit (default: 10)
   - [ ] Generate frequency violation reports

4. **Slotting Constraint Validation**
   - [ ] Check retailer slot availability per week
   - [ ] Validate promotions per week limits
   - [ ] Generate slotting violation reports

5. **Financial Feasibility Validation**
   - [ ] Check for negative margins
   - [ ] Validate minimum ROI thresholds (if applicable)
   - [ ] Generate financial violation reports

6. **Audit Report Generation**
   - [ ] Implement comprehensive audit report structure
   - [ ] Generate actionable feedback based on violations
   - [ ] Classify violations by severity
   - [ ] Return APPROVED or REJECTED status

7. **Testing**
   - [ ] Create test calendars with known violations
   - [ ] Test budget violations
   - [ ] Test gap rule violations
   - [ ] Test frequency violations
   - [ ] Verify feedback quality

**Deliverables**:
- Fully implemented `src/agents/auditor.py`
- Unit tests for all validation methods
- Test suite with violation scenarios
- Sample audit reports

**Estimated Effort**: 2-3 hours

---

## Phase 4: Agent B Implementation (The Strategist)

**Objective**: Implement calendar optimizer with feedback loop.

**Conversation Focus**: "Implement Agent B (Strategist) with volume/profit optimization"

**Skill to Use**: `/promotion-optimization`

### Tasks

1. **Volume Optimization Logic**
   - [ ] Implement greedy calendar generation
   - [ ] Prioritize high-elasticity SKUs
   - [ ] Select optimal discount depths for volume
   - [ ] Add displays where beneficial
   - [ ] Schedule in high-seasonality weeks

2. **Profit Optimization Logic**
   - [ ] Implement margin-aware optimization
   - [ ] Balance discount depth with margin retention
   - [ ] Calculate incremental margin per promotion
   - [ ] Optimize for net profit

3. **Budget Management**
   - [ ] Calculate projected spend for each promotion
   - [ ] Track cumulative spend during generation
   - [ ] Stay within budget constraint

4. **Reasoning Generation**
   - [ ] Create reasoning templates
   - [ ] Generate explanation for each promotion decision
   - [ ] Include seasonality, elasticity, and objective rationale
   - [ ] Make reasoning human-readable

5. **Feedback Processing**
   - [ ] Parse auditor feedback
   - [ ] Identify violation types
   - [ ] Implement adjustment strategies:
     - [ ] Reduce frequency for budget violations
     - [ ] Increase gaps for gap violations
     - [ ] Remove low-ROI events for frequency violations
   - [ ] Track iteration count

6. **Iteration Logic**
   - [ ] Implement regeneration with feedback
   - [ ] Make material adjustments (not cosmetic)
   - [ ] Document adjustments made
   - [ ] Prevent infinite loops (max iterations)

7. **Testing**
   - [ ] Test volume optimization mode
   - [ ] Test profit optimization mode
   - [ ] Test feedback processing
   - [ ] Test iteration convergence
   - [ ] Verify reasoning quality

**Deliverables**:
- Fully implemented `src/agents/strategist.py`
- Unit tests for optimization logic
- Test suite for both objectives
- Sample calendars with reasoning

**Estimated Effort**: 4-5 hours

---

## Phase 5: Orchestration & Integration

**Objective**: Connect all agents with rejection loop and generate execution logs.

**Conversation Focus**: "Integrate agents and implement rejection loop orchestration"

### Tasks

1. **Orchestrator Implementation**
   - [ ] Wire Agent A → causal parameters
   - [ ] Wire Agent B → calendar generation
   - [ ] Wire Agent C → validation
   - [ ] Implement rejection loop (B ↔ C)
   - [ ] Add iteration limit (default: 10)

2. **Execution Logging**
   - [ ] Log all agent interactions
   - [ ] Capture proposal/rejection cycles
   - [ ] Document reasoning at each step
   - [ ] Generate `agent_execution_log.txt`

3. **End-to-End Testing**
   - [ ] Test full workflow with Volume objective
   - [ ] Test full workflow with Profit objective
   - [ ] Verify rejection loop occurs (critical for judging!)
   - [ ] Test iteration until approval
   - [ ] Verify all outputs generated

4. **Edge Case Handling**
   - [ ] Handle max iterations reached
   - [ ] Handle data loading errors
   - [ ] Handle invalid causal parameters
   - [ ] Handle unsatisfiable constraints

**Deliverables**:
- Fully implemented `src/orchestrator.py`
- Integration tests
- Sample execution logs showing rejection loop
- Error handling documentation

**Estimated Effort**: 2-3 hours

---

## Phase 6: Deliverables Generation

**Objective**: Generate and validate all required hackathon outputs.

**Conversation Focus**: "Generate and validate final deliverables for submission"

### Tasks

1. **Generate Optimized Calendar**
   - [ ] Run full workflow with Volume objective
   - [ ] Generate `outputs/optimized_calendar.csv`
   - [ ] Verify CSV format and columns
   - [ ] Validate reasoning field populated
   - [ ] Check week numbers (1-52)

2. **Generate Financial Impact Report**
   - [ ] Calculate base plan metrics
   - [ ] Calculate optimized plan metrics
   - [ ] Compute deltas (volume, revenue, margin, spend)
   - [ ] Generate `outputs/financial_impact_report.json`
   - [ ] Validate JSON structure

3. **Generate Baseline Validation Report**
   - [ ] Run baseline validation on holdout data
   - [ ] Calculate MAPE, RMSE, MAE
   - [ ] Generate `outputs/baseline_validation.csv`
   - [ ] Verify MAPE < 15%

4. **Generate Execution Log**
   - [ ] Capture full agent conversation
   - [ ] Show proposal → rejection → adjustment cycle
   - [ ] Include all reasoning
   - [ ] Generate `outputs/agent_execution_log.txt`
   - [ ] Verify rejection loop is visible

5. **Validation**
   - [ ] Run validation hooks on all outputs
   - [ ] Check format compliance
   - [ ] Verify all required fields present
   - [ ] Test with Profit objective as well

**Deliverables**:
- `outputs/optimized_calendar.csv`
- `outputs/financial_impact_report.json`
- `outputs/baseline_validation.csv`
- `outputs/agent_execution_log.txt`
- All validated and submission-ready

**Estimated Effort**: 1-2 hours

---

## Phase 7: Testing & Quality Assurance

**Objective**: Comprehensive testing to meet judging criteria.

**Conversation Focus**: "Test system against judging criteria and fix issues"

### Tasks

1. **Architecture & Agentic Design Tests** (40% of score)
   - [ ] Verify rejection loop visible in logs
   - [ ] Confirm Agent A doesn't optimize
   - [ ] Confirm Agent B doesn't validate
   - [ ] Confirm Agent C doesn't analyze
   - [ ] Test objective switching (Volume ↔ Profit)
   - [ ] Verify architecture remains stable

2. **Technical Implementation Tests** (40% of score)
   - [ ] Verify budget calculations are exact
   - [ ] Confirm zero constraint violations in final output
   - [ ] Validate MAPE < 15% on baseline forecast
   - [ ] Test edge cases
   - [ ] Run full test suite

3. **User Experience Tests** (20% of score)
   - [ ] Review reasoning quality
   - [ ] Check Before/After clarity in reports
   - [ ] Verify reports are business-user friendly
   - [ ] Test CLI usability

4. **Bug Fixes & Refinement**
   - [ ] Fix any failing tests
   - [ ] Address validation issues
   - [ ] Improve reasoning clarity
   - [ ] Optimize performance if needed

**Deliverables**:
- Complete test suite passing
- All quality checks green
- No violations in final outputs
- Clear, explainable results

**Estimated Effort**: 2-3 hours

---

## Phase 8: Demo Preparation

**Objective**: Create 2-3 minute demo video and presentation materials.

**Conversation Focus**: "Prepare demo video and presentation"

### Tasks

1. **Demo Script**
   - [ ] Write demo narrative (2-3 minutes)
   - [ ] Highlight rejection loop
   - [ ] Explain strategy chosen
   - [ ] Show final outputs

2. **Demo Recording**
   - [ ] Record code running
   - [ ] Capture auditor catching violation
   - [ ] Show strategist fixing it
   - [ ] Display final approved calendar

3. **Presentation Materials** (Optional)
   - [ ] Architecture diagram
   - [ ] Key results summary
   - [ ] Unique features/innovations

4. **Submission Package**
   - [ ] All code in repository
   - [ ] All outputs in `outputs/` folder
   - [ ] Demo video file
   - [ ] README with instructions

**Deliverables**:
- 2-3 minute demo video
- Submission-ready code repository
- All required artifacts

**Estimated Effort**: 1-2 hours

---

## Summary Timeline

| Phase | Focus | Estimated Hours | Status |
|-------|-------|----------------|--------|
| 1. Data Exploration | Understand data | 1-2 | ⏭️ NEXT |
| 2. Agent A | Analyst implementation | 3-4 | Pending |
| 3. Agent C | Auditor implementation | 2-3 | Pending |
| 4. Agent B | Strategist implementation | 4-5 | Pending |
| 5. Integration | Orchestration & rejection loop | 2-3 | Pending |
| 6. Deliverables | Generate outputs | 1-2 | Pending |
| 7. Testing | Quality assurance | 2-3 | Pending |
| 8. Demo | Video & presentation | 1-2 | Pending |
| **TOTAL** | | **16-24 hours** | |

## Critical Success Factors

1. **The Rejection Loop**: System MUST show rejection/iteration cycles (not first-try success)
2. **Separation of Concerns**: Each agent stays strictly within its role
3. **Baseline Accuracy**: MAPE < 15% on holdout data
4. **Zero Violations**: Final calendar must be fully compliant
5. **Clear Reasoning**: Every decision must have human-readable explanation

## Development Principles

- **Single-Purpose Conversations**: One phase per conversation
- **Test-Driven**: Write tests before/during implementation
- **Documentation**: Keep CLAUDE.md updated with progress
- **Validation**: Use hooks to catch issues early
- **Skills**: Leverage `/causal-inference`, `/promotion-optimization`, `/constraint-validation`

---

**Last Updated**: 2026-01-23
**Current Phase**: Phase 1 - Data Exploration ✅ COMPLETE
**Next Phase**: Phase 2 - Agent A Implementation ⏭️
