# Execution Report Generator - Technical Specification

**Created**: 2025-01-25
**Purpose**: Comprehensive execution summary reporting for TPO multi-agent system demos and presentations
**Phase**: Deliverables & Final Reports (Phase 6)

---

## 1. Problem Statement

### Current State
- System generates 4+ output files (CSV, JSON, TXT) scattered across outputs/
- No single source of truth for "what happened during this run"
- Difficult to quickly assess system performance for demos
- Execution logs are machine-readable but not presentation-friendly
- Cannot easily compare runs or show progression to stakeholders

### Target State
- Single comprehensive execution summary report (human-readable)
- Clear narrative of Agent A → B → C workflow
- Visual presentation of rejection loop iterations
- Key metrics and insights for demo/presentation
- Quick-glance status of all deliverables
- Suitable for both technical and non-technical audiences

---

## 2. Requirements

### Functional Requirements

**FR1: Comprehensive Summary Generation**
- Generate single master report consolidating all execution data
- Include timing (start/end/duration)
- Summarize each agent's contribution
- Show rejection loop progression
- Display final outcomes

**FR2: Multi-Audience Support**
- Executive summary section (high-level, 1-page)
- Technical details section (metrics, methods, accuracy)
- Deliverables checklist (file verification)
- Key insights section (presentation talking points)

**FR3: Real-Time File Validation**
- Check existence of all expected output files
- Parse and summarize content from existing outputs
- Flag missing deliverables clearly
- Show file sizes and timestamps

**FR4: Metrics & Performance Tracking**
- Agent A: MAPE, coverage, baseline method
- Agent B: Iterations, budget utilization, event count
- Agent C: Violations detected, final status
- Rejection loop: Total iterations, convergence status

**FR5: Formatting & Readability**
- Plain text format (Windows console compatible)
- Clear section headers with visual separators
- Tables for structured data
- Checkboxes for deliverables
- NO EMOJIS (Windows cp1252 encoding)

### Non-Functional Requirements

**NFR1: Performance**
- Report generation < 5 seconds
- No heavy computation (read existing files only)

**NFR2: Robustness**
- Handle missing files gracefully
- Work with partial outputs (e.g., if workflow crashed mid-run)
- Never fail silently (always generate something)

**NFR3: Maintainability**
- Modular design (one method per section)
- Easy to add new sections
- Clear separation of data extraction vs formatting

---

## 3. Research Findings

### Industry Best Practices (Data Science Executive Summaries)

**Source**: OpenStax "Principles of Data Science" + ProjectPro + Insight7

**Key Insights**:
1. **Structure**: Problem → Methodology → Findings → Recommendations
2. **Avoid Information Overload**: Focus on 3-5 key insights, not everything
3. **Visual Aids**: Use sparingly but effectively (tables for comparison)
4. **Actionable**: Every section should answer "so what?"
5. **Audience-Specific**: Tailor technical depth to viewer

**Application to TPO**:
- Problem: Trade promotion optimization with budget constraints
- Methodology: Multi-agent LLM system with rejection loop
- Findings: X events, Y budget utilization, Z% MAPE
- Recommendations: Key insights for presentation

### Multi-Agent System Logging (2025 Frameworks)

**Source**: CrewAI, Google ADK, LangGraph

**Key Insights**:
1. **Audit Trails**: Track which agent made which decision and why
2. **Step-by-Step Execution**: Show trajectory, not just final output
3. **Observability**: Real-time progress tracking + log visualization
4. **Reproducibility**: Store all config params, seeds, versions

**Application to TPO**:
- Agent-level summaries (A, B, C contributions)
- Rejection loop visualization (iteration-by-iteration)
- Configuration tracking (objective, budget, constraints)
- Decision transparency (reasoning from execution logs)

### Optimization Summary Reports (Microsoft Dynamics)

**Source**: Microsoft Dynamics 365 Field Service optimization reports

**Key Insights**:
1. **Key Metrics Front and Center**: Total bookings, resources, time allocation
2. **Business Impact**: Connect technical metrics to business outcomes
3. **Comparison**: Before vs after (baseline vs optimized)
4. **Resource Utilization**: Show % of budget/capacity used

**Application to TPO**:
- Budget utilization prominently displayed
- Baseline vs optimized comparison (financial impact)
- Calendar coverage (weeks utilized, PPGs promoted)
- Constraint compliance (violations fixed)

---

## 4. Design

### 4.1 Tool Interface

**Class**: `ExecutionReportGenerator`

**Primary Method**:
```python
def generate_comprehensive_report(
    objective: str,
    budget: float,
    optimization_result: Dict[str, Any],
    start_time: datetime,
    end_time: datetime
) -> str:
    """
    Generate comprehensive execution summary.

    Args:
        objective: "volume" or "profit"
        budget: Budget limit (float)
        optimization_result: Dict with keys:
            - status: "APPROVED" | "REJECTED"
            - iterations: int
            - violations_history: List[List[Dict]]
            - final_violations: List[Dict]
        start_time: Workflow start timestamp
        end_time: Workflow end timestamp

    Returns:
        Formatted report string (saved to outputs/EXECUTION_SUMMARY.txt)
    """
```

**Helper Method**:
```python
def generate_quick_summary(output_dir: str = "outputs") -> str:
    """
    Generate 1-page quick summary for immediate review.

    Returns:
        Quick summary string (10-15 lines)
    """
```

### 4.2 Report Structure

**Sections** (in order):

1. **Header** (5-10 lines)
   - Title banner
   - Generation timestamp
   - Configuration (objective, budget)
   - Execution time (start, end, duration)

2. **Agent A Summary** (15-20 lines)
   - Role description
   - Outputs generated
   - Baseline performance (MAPE, coverage, method)
   - Causal parameters count (discount depths, display tiers)
   - Key insights

3. **Agent B Summary** (15-20 lines)
   - Role description
   - Optimization process (iterations, tool calls)
   - Decision criteria
   - Agent reasoning highlights
   - Output file reference

4. **Agent C Summary** (15-20 lines)
   - Role description
   - Validation checks performed
   - Final status
   - Validation approach (hybrid LLM + rules)

5. **Rejection Loop Summary** (20-25 lines)
   - Process description (B ↔ C)
   - Iterations count
   - Outcome (converged vs max iterations)
   - Violations encountered (types, counts)
   - Agentic behavior demonstration

6. **Final Calendar Summary** (20-25 lines)
   - File reference
   - Calendar statistics (events, PPGs, retailers, weeks)
   - Promotion tactics (avg discount, display distribution)
   - Granularity confirmation

7. **Financial Impact Summary** (15-20 lines)
   - Budget utilization (spend, %, remaining)
   - Projected impact (baseline vs optimized)
   - Volume/profit lift

8. **Data Quality & Validation** (10-15 lines)
   - Baseline validation metrics
   - Data sources listed
   - Granularity confirmation

9. **Deliverables Checklist** (10-15 lines)
   - 6 expected files with checkboxes
   - [X] = exists, [ ] = missing
   - File descriptions

10. **Key Insights for Presentation** (25-30 lines)
    - 5 key talking points:
      1. LLM-powered architecture
      2. Multi-agent collaboration
      3. Iterative rejection loop
      4. Explainability & transparency
      5. PPG-Retailer-Week granularity

**Total Length**: ~150-200 lines (fits in 2-3 pages)

### 4.3 Data Extraction Strategy

**Files to Read**:
- `outputs/causal_parameters.json` → Agent A metrics
- `outputs/optimized_calendar.csv` → Calendar statistics
- `outputs/financial_impact_report.json` → Budget/impact metrics
- `outputs/baseline_validation.csv` → Validation metrics
- `outputs/agent_execution_log.txt` → (optional) reasoning excerpts

**Fallback Handling**:
- If file missing → "NO OUTPUT FOUND" or "MISSING"
- If file exists but malformed → "ERROR PARSING"
- If metrics missing → "N/A"

### 4.4 Integration with Orchestrator

**When to Generate**:
- At end of `Orchestrator.run()` method
- After all agents have completed (success or failure)
- Before returning final result to main.py

**Call Pattern**:
```python
# In orchestrator.py, at end of run()
from src.utils.report_generator import ExecutionReportGenerator

report_gen = ExecutionReportGenerator(output_dir=self.output_dir)
summary = report_gen.generate_comprehensive_report(
    objective=self.objective,
    budget=self.budget_limit,
    optimization_result=optimization_result,
    start_time=start_time,
    end_time=datetime.now()
)

# Print to console
print("\n" + summary)

# Also generate quick summary
quick = report_gen.generate_quick_summary()
logger.info(quick)
```

---

## 5. Success Criteria

### Quantitative Metrics

**Report Completeness**:
- [ ] All 10 sections present
- [ ] All expected metrics displayed (MAPE, iterations, budget %, etc.)
- [ ] All 6 deliverables checked

**Accuracy**:
- [ ] MAPE matches causal_parameters.json
- [ ] Event count matches optimized_calendar.csv
- [ ] Budget spend matches financial_impact_report.json
- [ ] Iterations match optimization_result

**Performance**:
- [ ] Generation time < 5 seconds
- [ ] Report file < 50 KB (text)

### Qualitative Metrics

**Readability**:
- [ ] Non-technical stakeholder can understand high-level flow
- [ ] Technical reviewer can verify accuracy
- [ ] Clear visual hierarchy (headers, spacing, alignment)

**Presentation-Readiness**:
- [ ] Key insights section has 5 concrete talking points
- [ ] Can copy-paste sections into PowerPoint
- [ ] Deliverables checklist shows demo-readiness

**Robustness**:
- [ ] Handles missing files without crashing
- [ ] Works with partial outputs
- [ ] Clear error messages

---

## 6. Testing Strategy

### Unit Tests

**Test 1: Complete Outputs**
- Pre-condition: All 5 output files exist
- Expected: All sections populated, all checkboxes [X]

**Test 2: Missing Outputs**
- Pre-condition: Only causal_parameters.json exists
- Expected: Report generates, other sections show "MISSING"

**Test 3: Malformed JSON**
- Pre-condition: financial_impact_report.json is invalid JSON
- Expected: Section shows "ERROR PARSING", report continues

**Test 4: Performance**
- Pre-condition: Complete outputs
- Expected: Report generation < 5 seconds

### Integration Tests

**Test 5: End-to-End**
- Run: `python main.py --objective volume --budget 1000000`
- Expected: EXECUTION_SUMMARY.txt generated at end
- Verify: Metrics match other output files

**Test 6: Interrupted Workflow**
- Simulate: Kill process after Agent B, before Agent C
- Expected: Report shows partial completion

### Manual Review

**Test 7: Presentation Simulation**
- Task: Use report as basis for 5-minute demo
- Success: Can explain workflow using only the report

---

## 7. Implementation Plan

### Phase 1: Core Report Generator (1 hour)
- [ ] Create `src/utils/report_generator.py`
- [ ] Implement `ExecutionReportGenerator` class
- [ ] Implement all 10 section methods
- [ ] Implement file reading with error handling

### Phase 2: Data Extraction (30 min)
- [ ] Implement JSON parsing (causal_parameters, financial_impact)
- [ ] Implement CSV parsing (calendar, validation)
- [ ] Implement fallback logic for missing files

### Phase 3: Integration (30 min)
- [ ] Update `src/orchestrator.py` to call report generator
- [ ] Update `main.py` to print quick summary
- [ ] Test with existing outputs

### Phase 4: Testing & Refinement (1 hour)
- [ ] Run all unit tests
- [ ] Run end-to-end test
- [ ] Manual review for readability
- [ ] Adjust formatting as needed

**Total Estimated Effort**: 3 hours

---

## 8. Future Enhancements (Post-Hackathon)

**V2 Features**:
- HTML report with charts (matplotlib/plotly)
- Comparison mode (multiple runs side-by-side)
- Export to PowerPoint (python-pptx)
- Interactive dashboard (Streamlit/Gradio)
- Email/Slack notification with summary

**V3 Features**:
- Real-time streaming report (updated during execution)
- Diff view (show what changed between iterations)
- Reasoning excerpts (pull key quotes from execution log)
- Visualization of rejection loop (flowchart)

---

## 9. Open Questions

1. **Execution Log Parsing**: Should we parse agent_execution_log.txt to extract reasoning quotes?
   - **Decision**: Not in V1 (adds complexity). V1 just references file.

2. **Report Format**: Plain text vs Markdown vs HTML?
   - **Decision**: Plain text for V1 (console-friendly, no dependencies). Future: add HTML export.

3. **Calendar Visualization**: Should we show week-by-week calendar grid?
   - **Decision**: Not in V1 (too large). Just summary statistics.

4. **Historical Tracking**: Should we save all reports with timestamps?
   - **Decision**: Yes. Name format: `EXECUTION_SUMMARY_<timestamp>.txt`, keep latest as `EXECUTION_SUMMARY.txt`.

---

## 10. References

**Industry Sources**:
1. OpenStax - "Principles of Data Science" (Executive Summaries)
2. ProjectPro - "How to Write a Data Science Project Report"
3. Google ADK Documentation - Multi-Agent Observability
4. CrewAI - Real-Time Tracing & Logging
5. Microsoft Dynamics 365 - Optimization Summary Reports

**Internal Sources**:
1. [CLAUDE.md](../CLAUDE.md) - Project requirements & architecture
2. [case-study-instructions.pptx](../case-study-instructions.pptx) - Judging criteria
3. [Agent A Spec](agent_a_analyst_spec.md) - Baseline validation metrics
4. [Agent B Spec](agent_b_strategist_spec.md) - Calendar generation
5. [Agent C Spec](agent_c_auditor_spec.md) - Constraint validation

---

**Specification Status**: ✅ COMPLETE - Ready for Implementation
**Next Step**: Implement `src/utils/report_generator.py` according to this spec
