# Journey Tracking System - Technical Specification

**Created**: 2025-01-25
**Purpose**: Real-time tracking and reporting of the complete multi-agent optimization journey
**User Need**: "I want a way to review the entire iteration journey as it goes on...the entire chain starting from when analyst agent begins"

---

## 1. Problem Statement

### Current State
- System generates outputs only at the end of execution
- No visibility into what's happening during long-running LLM agent operations
- Cannot monitor progress in real-time
- Difficult to debug or understand the optimization journey
- No comprehensive narrative of the complete workflow

### Target State
- **Real-time journey log** that updates as the system runs
- **Complete visibility** from data loading → Agent A → Agent B ↔ Agent C → Final reports
- **Human-readable narrative** suitable for presentations and demos
- **Live monitoring** capability (tail the file to watch progress)
- **Comprehensive final report** that includes the entire journey

---

## 2. User Requirements

From user feedback:

1. **"Review the entire iteration journey as it goes on"**
   - Need real-time updates during execution
   - File should be watchable (tail -f style)

2. **"Near real-time documentation"**
   - Events logged immediately as they happen
   - No batch writing at the end

3. **"Entire chain starting from when analyst agent begins"**
   - Not just rejection loop
   - Include ALL phases: data loading, Agent A, Agent B, Agent C, reports

4. **"Part of the report"**
   - Journey should be integrated into final execution summary
   - Provide both detailed journey log AND summary report

---

## 3. Design

### 3.1 Two-Tier Approach

**Tier 1: Live Journey Log** (`outputs/OPTIMIZATION_JOURNEY.txt`)
- Real-time, append-only log file
- Updates immediately as events occur
- Structured, timestamped entries
- Human-readable format
- Can be monitored with `tail -f`

**Tier 2: Final Execution Summary** (`outputs/EXECUTION_SUMMARY.txt`)
- Generated at end of workflow
- Includes condensed journey timeline
- Agent-by-agent summaries
- Key insights and talking points
- Presentation-ready

### 3.2 Journey Log Structure

```
================================================================================
TRADE PROMOTION OPTIMIZATION - COMPLETE JOURNEY LOG
================================================================================
Started: 2025-01-25 14:30:00
================================================================================

This log tracks the complete optimization journey in real-time.
You can monitor this file as the system runs to see live progress.

================================================================================

================================================================================
STEP 1: DATA LOADING
================================================================================

[>] [14:30:01 | +0.5s] Loading data files from case-data/
    sales_rows: 3676
    promo_rows: 845

[+] [14:30:02 | +1.2s] Data loaded successfully
    sales_rows: 3676
    promo_rows: 845

================================================================================
STEP 2: AGENT A (ANALYST)
================================================================================

[>] [14:30:02 | +1.5s] Analyst agent starting causal inference analysis...

[>] [14:30:05 | +4.2s] Iteration 1: Calling tool 'load_sales_preview'

[>] [14:30:08 | +7.8s] Iteration 2: Calling tool 'calculate_baseline_ppg_week_fixed_effects'

[+] [14:30:45 | +44.2s] Causal parameters generated (MAPE: 50.38%)
    baseline_method: PPG-Week Fixed Effects
    mape_percent: 50.38
    total_iterations: 11
    output_file: outputs/causal_parameters.json

================================================================================
STEP 3: REJECTION LOOP (AGENT B <-> AGENT C)
================================================================================

[>] [14:30:46 | +45.0s] Iteration 1: Generating calendar

[+] [14:31:15 | +74.5s] Iteration 1: Calendar generated - 30 events, $450,000 spend
    iteration: 1
    event_count: 30
    total_spend: 450000

[>] [14:31:15 | +74.8s] Iteration 1: Auditor validating calendar...

[!] [14:32:05 | +124.2s] Iteration 1: Calendar REJECTED - 2 violation(s) found
    iteration: 1
    status: REJECTED
    violation_count: 2
    violations: ["GAP_VIOLATION", "GAP_VIOLATION"]

[>] [14:32:06 | +125.0s] Iteration 2: Generating calendar (with feedback from Auditor)

[...]

[+] [14:35:30 | +330.0s] Rejection loop converged - Calendar approved after 3 iteration(s)
    final_status: APPROVED
    total_iterations: 3

================================================================================
STEP 4: GENERATING REPORTS
================================================================================

[>] [14:35:31 | +330.5s] Generating final deliverables and reports...

[+] [14:35:32 | +331.2s] Saved: optimized_calendar.csv
    filename: optimized_calendar.csv
    description: 52-week promotion schedule

[...]

================================================================================
OPTIMIZATION JOURNEY COMPLETE
================================================================================

Final Status:     APPROVED
Total Duration:   332.0 seconds (5.53 minutes)
Total Events:     42

Events by Phase:
  - STEP 1: DATA LOADING: 2 events
  - STEP 2: AGENT A (ANALYST): 13 events
  - STEP 3: REJECTION LOOP (AGENT B <-> AGENT C): 18 events
  - STEP 4: GENERATING REPORTS: 9 events

Completed: 2025-01-25 14:35:32
================================================================================
```

### 3.3 Event Icons

- `[>]` = INFO (action starting)
- `[+]` = SUCCESS (action completed successfully)
- `[!]` = WARNING (issue detected, e.g., rejection)
- `[X]` = ERROR (critical error)

---

## 4. Implementation Plan

### 4.1 JourneyTracker Class

**File**: `src/utils/journey_tracker.py`

**Key Methods**:

```python
class JourneyTracker:
    def __init__(self, output_dir: str = "outputs"):
        # Initialize journey log file
        pass

    def log_event(
        self,
        phase: str,
        event_type: str,
        description: str,
        details: Optional[Dict] = None,
        status: str = "INFO"
    ):
        # Log event immediately to file (real-time)
        pass

    # Convenience methods for common events
    def log_data_loading_start(self):
        pass

    def log_data_loading_complete(self, sales_rows: int, promo_rows: int):
        pass

    def log_agent_a_start(self):
        pass

    def log_agent_a_tool_call(self, tool_name: str, iteration: int):
        pass

    def log_agent_a_complete(self, mape: float, method: str, iterations: int):
        pass

    def log_agent_b_iteration_start(self, iteration: int, feedback: Optional[str] = None):
        pass

    def log_agent_b_calendar_generated(self, iteration: int, event_count: int, total_spend: float):
        pass

    def log_agent_c_validation_start(self, iteration: int):
        pass

    def log_agent_c_result(self, iteration: int, status: str, violations: list, feedback: Optional[str] = None):
        pass

    def log_rejection_loop_complete(self, final_status: str, total_iterations: int):
        pass

    def log_reports_generation(self):
        pass

    def log_report_saved(self, filename: str, description: str):
        pass

    def finalize(self, final_status: str):
        # Write final summary to journey log
        pass
```

### 4.2 Integration Points

**1. Orchestrator (`src/orchestrator.py`)**

```python
from .utils.journey_tracker import JourneyTracker

class TPOOrchestrator:
    def __init__(self, ...):
        self.journey = JourneyTracker(output_dir=self.output_dir)

    def run(self, ...):
        # Data loading
        self.journey.log_data_loading_start()
        data = self._load_data()
        self.journey.log_data_loading_complete(len(data['sales']), len(data['promotions']))

        # Agent A
        self.journey.log_agent_a_start()
        causal_parameters = self._run_analyst(data)
        # (Agent A logs tool calls internally)
        self.journey.log_agent_a_complete(mape, method, iterations)

        # Rejection loop
        for iteration in range(max_iterations):
            self.journey.log_agent_b_iteration_start(iteration + 1, feedback)
            calendar = strategist.generate_calendar(feedback)
            self.journey.log_agent_b_calendar_generated(iteration + 1, event_count, spend)

            self.journey.log_agent_c_validation_start(iteration + 1)
            audit = auditor.validate_calendar(calendar)
            self.journey.log_agent_c_result(iteration + 1, status, violations, feedback)

            if status == "APPROVED":
                break

        self.journey.log_rejection_loop_complete(final_status, total_iterations)

        # Reports
        self.journey.log_reports_generation()
        # ... save reports ...
        self.journey.log_report_saved("optimized_calendar.csv", "52-week promotion schedule")

        # Finalize
        self.journey.finalize(final_status)
```

**2. Agent A (`src/agents/analyst.py`)**

```python
class AnalystAgent:
    def analyze(self, ...):
        # Journey tracker passed from orchestrator
        for iteration in range(max_iterations):
            # Log tool call
            if self.journey:
                self.journey.log_agent_a_tool_call(tool_name, iteration)
```

**3. Execution Summary Report (`src/utils/report_generator.py`)**

```python
def _journey_summary_section(self) -> str:
    """Include condensed journey timeline in final report."""
    # Read journey log
    # Extract key milestones
    # Format as timeline
    return formatted_timeline
```

---

## 5. Output Files

After a complete run:

1. **`outputs/OPTIMIZATION_JOURNEY.txt`** (500-1000 lines)
   - Complete detailed journey
   - Real-time log
   - All events timestamped

2. **`outputs/optimization_journey.json`** (machine-readable)
   - Structured JSON for programmatic access
   - Same data as text log

3. **`outputs/EXECUTION_SUMMARY.txt`** (150-200 lines)
   - High-level summary
   - Includes journey timeline section
   - Presentation-ready

---

## 6. Success Criteria

### Functional Requirements

- [ ] Journey log created at workflow start
- [ ] Events logged immediately (not batched)
- [ ] All phases tracked (data → Agent A → B ↔ C → reports)
- [ ] Human-readable timestamps and descriptions
- [ ] File can be monitored in real-time (`tail -f`)
- [ ] Final summary includes journey overview

### Quality Requirements

- [ ] Events logged in < 10ms (negligible overhead)
- [ ] Log file encoding: UTF-8
- [ ] No crashes if file write fails (graceful degradation)
- [ ] Clear visual hierarchy (phase headers, icons)

### User Experience

- [ ] Non-technical user can understand journey from log
- [ ] Technical user can debug issues from log
- [ ] Presentation-ready (can copy-paste into slides)

---

## 7. Testing Strategy

### Manual Test Cases

**Test 1: Real-Time Monitoring**
```bash
# Terminal 1
python main.py --objective volume --budget 1000000

# Terminal 2 (simultaneously)
tail -f outputs/OPTIMIZATION_JOURNEY.txt
```
Expected: Events appear in Terminal 2 as they happen

**Test 2: Complete Journey**
```bash
python main.py --objective volume --budget 1000000
cat outputs/OPTIMIZATION_JOURNEY.txt | grep "STEP"
```
Expected: See all 4 phases (DATA LOADING, AGENT A, REJECTION LOOP, REPORTS)

**Test 3: Journey in Final Report**
```bash
python main.py --objective volume --budget 1000000
grep -A 20 "JOURNEY TIMELINE" outputs/EXECUTION_SUMMARY.txt
```
Expected: See condensed journey timeline in final report

---

## 8. Future Enhancements

### V2 Features
- Color coding (ANSI colors for terminal viewing)
- Progress bar integration
- Web dashboard (live view in browser)
- Journey replay (step through events interactively)

### V3 Features
- Journey diff (compare two runs)
- Performance profiling (time per phase)
- Anomaly detection (flag unusual patterns)

---

## 9. References

**User Requirements**: Session 12 user feedback
**Related Specs**:
- [execution_report_spec.md](execution_report_spec.md) - Final report structure
- Agent specs (A, B, C) - Integration points

---

**Specification Status**: ✅ COMPLETE - Ready for Implementation
**Next Step**: Integrate JourneyTracker into orchestrator and all agents
