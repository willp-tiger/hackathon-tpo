# Dashboard Generator Specification

## Purpose

Generate an interactive HTML dashboard that visualizes the optimization journey and results in a user-friendly format. This dashboard serves as the primary interface for understanding:
- Agent decision-making process
- Rejection loop iterations
- Final calendar and financial outcomes
- Data quality and validation

## User Requirements

**From Session 13**: "Create user-friendly frontend" for journey visualization
**Target Audience**: Hackathon judges, stakeholders, non-technical users
**Access Pattern**: Open `outputs/journey_dashboard.html` in any browser

## Input Sources

1. **Journey Log**: `outputs/OPTIMIZATION_JOURNEY.txt`
   - Phase information (STEP 1-7)
   - Event timestamps and types ([>] INFO, [+] SUCCESS, [!] WARNING, [X] ERROR)
   - Agent reasoning and decisions
   - Iteration details (PPG selection, violations, feedback)

2. **Execution Summary**: `outputs/EXECUTION_SUMMARY.txt`
   - Configuration and timing
   - Agent metrics (MAPE, elasticity, etc.)
   - Financial impact
   - Key insights

3. **Promotion Calendar**: `outputs/promotion_calendar.json`
   - Calendar events with PPG, week, discount, display
   - Reasoning for each promotion

4. **Causal Parameters**: `outputs/causal_parameters.json`
   - Baseline velocity
   - Elasticity model
   - Seasonality factors
   - Display lifts

## Dashboard Sections

### 1. Header Section
- Project title: "TPO AI Agents - Optimization Dashboard"
- Configuration summary (objective, budget, timestamp)
- Total execution time
- Navigation menu (quick jump to sections)

### 2. Executive Summary
- Key metrics in card format:
  - Total projected spend
  - Budget utilization %
  - Rejection loop iterations
  - Final calendar event count
  - MAPE accuracy
- Status indicators (APPROVED/REJECTED)

### 3. Journey Timeline (Interactive)
- Vertical timeline visualization
- Expandable sections for each phase (STEP 1-7)
- Event cards with:
  - Timestamp and elapsed time
  - Event type icon (visual indicators)
  - Event description
  - Detailed data (collapsible)
- Filter by event type (INFO/SUCCESS/WARNING/ERROR)

### 4. Agent A (Analyst) Summary
- Baseline method used
- MAPE accuracy (visual gauge)
- Key parameters table:
  - Baseline velocity
  - Price elasticity
  - Discount lift factors
  - Display lift multiplier
  - Seasonality coverage
- Data validation metrics

### 5. Rejection Loop Visualization
- Iteration-by-iteration breakdown
- For each iteration:
  - Agent B calendar composition (PPG list, event count, spend)
  - Agent C validation result (violations, feedback)
  - Visual diff (what changed between iterations)
- Convergence chart (violations over iterations)

### 6. Agent B (Strategist) Summary
- Final calendar statistics
- PPG distribution chart
- Week distribution chart
- Discount depth distribution
- Sample events table (top 10)

### 7. Agent C (Auditor) Summary
- Constraint validation results
- Pass/fail by constraint type
- Final violations (if any)
- Compliance percentage

### 8. Financial Impact
- Side-by-side comparison:
  - Base scenario (no promotions)
  - Optimized scenario (with promotions)
- Metrics:
  - Total volume
  - Total revenue
  - Total spend
  - ROI
- Visual bar chart

### 9. Promotion Calendar (Interactive Table)
- Sortable/filterable table
- Columns: Week, PPG, Retailer, Discount %, Display, Reasoning
- Calendar heatmap view (weeks × PPG grid)
- Color-coded by discount depth

### 10. Data Quality Report
- Data validation summary
- Schema compliance
- Missing data handling
- Data quality score

## Technical Requirements

### Implementation

**File**: `src/utils/dashboard_generator.py`

**Key Functions**:
```python
def generate_dashboard(
    journey_log_path: str,
    execution_summary_path: str,
    calendar_path: str,
    causal_params_path: str,
    output_path: str = "outputs/journey_dashboard.html"
) -> None:
    """Generate HTML dashboard from journey artifacts."""
    pass

def parse_journey_log(log_path: str) -> dict:
    """Parse journey log into structured data."""
    pass

def parse_execution_summary(summary_path: str) -> dict:
    """Parse execution summary into structured data."""
    pass

def create_timeline_html(journey_data: dict) -> str:
    """Generate HTML for interactive timeline."""
    pass

def create_calendar_table_html(calendar_events: list) -> str:
    """Generate HTML for sortable calendar table."""
    pass

def create_rejection_loop_html(iterations: list) -> str:
    """Generate HTML for rejection loop visualization."""
    pass
```

### Frontend Technologies

**Styling**: Embedded CSS (no external dependencies)
- Modern card-based layout
- Responsive design (mobile-friendly)
- Color scheme:
  - Primary: #1E40AF (blue)
  - Success: #059669 (green)
  - Warning: #D97706 (orange)
  - Error: #DC2626 (red)
  - Background: #F9FAFB (light gray)

**JavaScript**: Embedded JS (no external libraries)
- Timeline expand/collapse
- Table sorting/filtering
- Chart rendering (simple bar/line charts using SVG)
- Smooth scrolling navigation

**Charts**: SVG-based (no Chart.js dependency)
- Violations over iterations (line chart)
- PPG distribution (bar chart)
- Week distribution (bar chart)
- Discount depth distribution (histogram)
- Calendar heatmap (grid with color-coded cells)

### File Structure

Single-file HTML with embedded CSS and JavaScript:
```html
<!DOCTYPE html>
<html>
<head>
    <title>TPO AI Agents - Dashboard</title>
    <style>/* Embedded CSS */</style>
</head>
<body>
    <!-- Dashboard sections -->
    <script>/* Embedded JavaScript */</script>
</body>
</html>
```

## Success Criteria

1. **Completeness**: All 10 sections present with real data
2. **Interactivity**: Timeline expandable, table sortable, charts interactive
3. **Visual Quality**: Professional appearance, clear typography, intuitive layout
4. **Performance**: Loads instantly (<1s), smooth interactions
5. **Accessibility**: Works in Chrome, Firefox, Edge (no IE11 requirement)
6. **Self-Contained**: Zero external dependencies (can open offline)

## Testing Plan

1. **Test with Session 13 outputs**:
   - Load existing journey log
   - Verify all sections render correctly
   - Check interactive features (expand/collapse, sort/filter)

2. **Test with multiple scenarios**:
   - Volume optimization
   - Profit optimization
   - Low budget (many iterations)
   - High budget (few iterations)

3. **Visual regression**:
   - Verify layout on different screen sizes (desktop, tablet, mobile)
   - Check color contrast for readability

4. **Edge cases**:
   - Empty journey log
   - Missing files (graceful degradation)
   - Very large calendars (100+ events)

## Expected Output

**File**: `outputs/journey_dashboard.html`
**Size**: ~200-300 KB (includes embedded data as JSON)
**Load Time**: <1 second
**Browser Support**: Chrome 90+, Firefox 88+, Edge 90+

## Example Usage

```python
from src.utils.dashboard_generator import generate_dashboard

generate_dashboard(
    journey_log_path="outputs/OPTIMIZATION_JOURNEY.txt",
    execution_summary_path="outputs/EXECUTION_SUMMARY.txt",
    calendar_path="outputs/promotion_calendar.json",
    causal_params_path="outputs/causal_parameters.json",
    output_path="outputs/journey_dashboard.html"
)
print("Dashboard generated: outputs/journey_dashboard.html")
```

## Integration Points

**Orchestrator Integration**: Add dashboard generation as final step (Step 8)

```python
# In orchestrator.py after report generation
from src.utils.dashboard_generator import generate_dashboard

self.journey.log_step_start(8, "DASHBOARD GENERATION")
generate_dashboard(
    journey_log_path="outputs/OPTIMIZATION_JOURNEY.txt",
    execution_summary_path="outputs/EXECUTION_SUMMARY.txt",
    calendar_path="outputs/promotion_calendar.json",
    causal_params_path="outputs/causal_parameters.json"
)
self.journey.log_event("Dashboard saved: outputs/journey_dashboard.html", "SUCCESS")
```

## Design Mockup (ASCII)

```
+----------------------------------------------------------+
| TPO AI Agents - Optimization Dashboard          [Nav]    |
+----------------------------------------------------------+
| Executive Summary                                         |
| +-------------+ +-------------+ +-------------+          |
| | Total Spend | | Budget Used | | Iterations  |          |
| | $950,000    | | 95%         | | 3           |          |
| +-------------+ +-------------+ +-------------+          |
+----------------------------------------------------------+
| Journey Timeline                                 [Filter]|
| > STEP 1: DATA LOADING             [00:00:01]    [+]     |
| > STEP 2: AGENT A (ANALYST)        [00:02:15]    [+]     |
| v STEP 3: REJECTION LOOP           [00:05:30]    [-]     |
|   | Iteration 1                                           |
|   | - Calendar: 30 events, $950K                          |
|   | - Violations: 10 (GAP_RULE, BUDGET)                   |
|   | Iteration 2                                           |
|   | - Calendar: 28 events, $900K                          |
|   | - Violations: 2 (GAP_RULE)                            |
+----------------------------------------------------------+
| Promotion Calendar                          [Sort] [Filter]
| +--------+--------+----------+----------+----------+      |
| | Week   | PPG    | Retailer | Discount | Display  |      |
| +--------+--------+----------+----------+----------+      |
| | 12     | Brand1 | 0        | 30%      | Yes      |      |
| | 15     | Brand4 | 1        | 20%      | No       |      |
+----------------------------------------------------------+
| Financial Impact                                          |
| Base:      Volume: 100K | Revenue: $1.5M                  |
| Optimized: Volume: 150K | Revenue: $2.2M | ROI: 1.8x      |
| [==================== Chart ====================]        |
+----------------------------------------------------------+
```

## References

- Journey tracking spec: `docs/specs/journey_tracking_spec.md`
- Execution report spec: `docs/specs/execution_report_spec.md`
- Agent outputs: `outputs/*.json`, `outputs/*.txt`

---

**Created**: 2026-01-25
**Status**: Ready for implementation
**Estimated Effort**: 2-3 hours
