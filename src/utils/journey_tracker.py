"""
Complete Journey Tracker for TPO Multi-Agent System

Tracks the entire optimization journey from start to finish in real-time:
- Agent A (Analyst): Data analysis and causal modeling
- Agent B (Strategist): Calendar generation iterations
- Agent C (Auditor): Validation checks
- Rejection loop: All feedback cycles

Creates a human-readable journey log that updates live as the system runs.
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import json


class JourneyTracker:
    """
    Tracks the complete multi-agent optimization journey in real-time.

    Logs every major step:
    - Data loading
    - Agent A analysis (baseline, elasticity, seasonality)
    - Agent B calendar generation (each iteration)
    - Agent C validation (each iteration)
    - Feedback loops
    - Final outcomes
    """

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.journey_path = self.output_dir / "OPTIMIZATION_JOURNEY.txt"
        self.json_path = self.output_dir / "optimization_journey.json"

        self.journey_start = None
        self.events = []

        # Initialize journey log
        self._initialize_journey()

    def _initialize_journey(self):
        """Initialize the journey log file."""
        self.journey_start = datetime.now()

        with open(self.journey_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("TRADE PROMOTION OPTIMIZATION - COMPLETE JOURNEY LOG\n")
            f.write("=" * 80 + "\n")
            f.write(f"Started: {self.journey_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            f.write("This log tracks the complete optimization journey in real-time.\n")
            f.write("You can monitor this file as the system runs to see live progress.\n\n")
            f.write("=" * 80 + "\n\n")

    def log_event(
        self,
        phase: str,
        event_type: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
        status: str = "INFO"
    ):
        """
        Log a single event in the journey.

        Args:
            phase: Phase name (e.g., "DATA_LOADING", "AGENT_A", "AGENT_B", "AGENT_C")
            event_type: Type of event (e.g., "START", "COMPLETE", "TOOL_CALL", "RESULT")
            description: Human-readable description
            details: Additional structured data
            status: Status level (INFO, SUCCESS, WARNING, ERROR)
        """
        timestamp = datetime.now()
        elapsed = (timestamp - self.journey_start).total_seconds()

        event = {
            "timestamp": timestamp.isoformat(),
            "elapsed_seconds": elapsed,
            "phase": phase,
            "event_type": event_type,
            "description": description,
            "details": details or {},
            "status": status
        }

        self.events.append(event)

        # Write to file immediately (real-time)
        self._write_event_to_log(event)

        # Update JSON log
        self._update_json_log()

    def _write_event_to_log(self, event: Dict[str, Any]):
        """Write event to the text log file."""
        with open(self.journey_path, 'a', encoding='utf-8') as f:
            timestamp_str = datetime.fromisoformat(event['timestamp']).strftime('%H:%M:%S')
            elapsed_str = f"{event['elapsed_seconds']:.1f}s"

            # Status indicator
            status_icon = {
                "INFO": "[>]",
                "SUCCESS": "[+]",
                "WARNING": "[!]",
                "ERROR": "[X]"
            }.get(event['status'], "[?]")

            # Phase header (if new phase)
            if self._is_new_phase(event['phase']):
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"{event['phase']}\n")
                f.write("=" * 80 + "\n\n")

            # Event line
            f.write(f"{status_icon} [{timestamp_str} | +{elapsed_str}] {event['description']}\n")

            # Details (if any) - format as ASCII table when possible
            if event['details']:
                details_text = self._format_details_as_table(event['details'])
                if details_text:
                    f.write(details_text)

            f.write("\n")

    def _format_details_as_table(self, details: Dict[str, Any]) -> str:
        """Format details as compact horizontal key-value pairs."""
        items = []

        for key, value in details.items():
            # Skip None or empty values
            if value is None:
                continue

            # Format value based on type
            if isinstance(value, (int, float)):
                if isinstance(value, float) and value > 1000:
                    value_str = f"{value:,.1f}"
                elif isinstance(value, float):
                    value_str = f"{value:.2f}"
                else:
                    value_str = f"{value:,}"
                items.append(f"{key}={value_str}")

            elif isinstance(value, dict):
                # Format nested dict as inline key=value pairs
                dict_items = []
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, (int, float)):
                        if isinstance(sub_value, float):
                            dict_items.append(f"{sub_key}={sub_value:.2f}")
                        else:
                            dict_items.append(f"{sub_key}={sub_value:,}")
                    else:
                        sub_str = str(sub_value)
                        if len(sub_str) < 20:
                            dict_items.append(f"{sub_key}={sub_str}")

                if dict_items:
                    # Put dict items on same line with parent key
                    items.append(f"{key}[{', '.join(dict_items[:4])}]")

            elif isinstance(value, list):
                if len(value) == 0:
                    continue
                elif len(value) <= 3:
                    list_str = ', '.join([str(v)[:15] for v in value])
                    items.append(f"{key}=[{list_str}]")
                else:
                    items.append(f"{key}=[{len(value)} items]")

            else:
                value_str = str(value)
                if len(value_str) < 30:
                    items.append(f"{key}={value_str}")

        if not items:
            return ''

        # Pack items horizontally (3 per line for compact display)
        output_lines = []
        for i in range(0, len(items), 3):
            batch = items[i:i+3]
            output_lines.append("    " + " | ".join(batch))

        return '\n'.join(output_lines) + '\n' if output_lines else ''

    def _is_new_phase(self, phase: str) -> bool:
        """Check if this is a new phase (for headers)."""
        if not self.events:
            return True
        return self.events[-1]['phase'] != phase if len(self.events) > 1 else True

    def _update_json_log(self):
        """Update the JSON log file."""
        with open(self.json_path, 'w') as f:
            json.dump({
                "journey_start": self.journey_start.isoformat(),
                "events": self.events
            }, f, indent=2)

    # Convenience methods for common events

    def log_data_loading_start(self):
        """Log start of data loading."""
        self.log_event(
            phase="STEP 1: DATA LOADING",
            event_type="START",
            description="Loading data files from case-data/",
            status="INFO"
        )

    def log_data_loading_complete(self, sales_rows: int, promo_rows: int):
        """Log completion of data loading."""
        self.log_event(
            phase="STEP 1: DATA LOADING",
            event_type="COMPLETE",
            description="Data loaded successfully",
            details={
                "sales_rows": sales_rows,
                "promo_rows": promo_rows
            },
            status="SUCCESS"
        )

    def log_agent_a_start(self):
        """Log start of Agent A analysis."""
        self.log_event(
            phase="STEP 2: AGENT A (ANALYST)",
            event_type="START",
            description="Analyst agent starting causal inference analysis...",
            status="INFO"
        )

    def log_agent_a_tool_call(self, tool_name: str, iteration: int):
        """Log Agent A tool call."""
        self.log_event(
            phase="STEP 2: AGENT A (ANALYST)",
            event_type="TOOL_CALL",
            description=f"Iteration {iteration}: Calling tool '{tool_name}'",
            details={"tool": tool_name, "iteration": iteration},
            status="INFO"
        )

    def log_agent_a_complete(self, mape: float, method: str, iterations: int):
        """Log completion of Agent A."""
        self.log_event(
            phase="STEP 2: AGENT A (ANALYST)",
            event_type="COMPLETE",
            description=f"Causal parameters generated (MAPE: {mape:.2f}%)",
            details={
                "baseline_method": method,
                "mape_percent": mape,
                "total_iterations": iterations,
                "output_file": "outputs/causal_parameters.json"
            },
            status="SUCCESS"
        )

    def log_agent_b_iteration_start(self, iteration: int, feedback: Optional[str] = None):
        """Log start of Agent B iteration."""
        desc = f"Iteration {iteration}: Generating calendar"
        if feedback:
            desc += " (with feedback from Auditor)"

        self.log_event(
            phase="STEP 3: REJECTION LOOP (AGENT B <-> AGENT C)",
            event_type="AGENT_B_START",
            description=desc,
            details={"iteration": iteration, "has_feedback": feedback is not None},
            status="INFO"
        )

    def log_agent_b_calendar_generated(self, iteration: int, event_count: int, total_spend: float):
        """Log Agent B calendar generation."""
        self.log_event(
            phase="STEP 3: REJECTION LOOP (AGENT B <-> AGENT C)",
            event_type="AGENT_B_RESULT",
            description=f"Iteration {iteration}: Calendar generated - {event_count} events, ${total_spend:,.0f} spend",
            details={
                "iteration": iteration,
                "event_count": event_count,
                "total_spend": total_spend
            },
            status="SUCCESS"
        )

    def log_agent_c_validation_start(self, iteration: int):
        """Log start of Agent C validation."""
        self.log_event(
            phase="STEP 3: REJECTION LOOP (AGENT B <-> AGENT C)",
            event_type="AGENT_C_START",
            description=f"Iteration {iteration}: Auditor validating calendar...",
            details={"iteration": iteration},
            status="INFO"
        )

    def log_agent_c_result(
        self,
        iteration: int,
        status: str,
        violations: list,
        feedback: Optional[str] = None
    ):
        """Log Agent C validation result."""
        if status == "APPROVED":
            desc = f"Iteration {iteration}: Calendar APPROVED - No violations found!"
            status_level = "SUCCESS"
        else:
            desc = f"Iteration {iteration}: Calendar REJECTED - {len(violations)} violation(s) found"
            status_level = "WARNING"

        details = {
            "iteration": iteration,
            "status": status,
            "violation_count": len(violations)
        }

        if violations:
            details["violations"] = [v.get('type', 'UNKNOWN') for v in violations]

        self.log_event(
            phase="STEP 3: REJECTION LOOP (AGENT B <-> AGENT C)",
            event_type="AGENT_C_RESULT",
            description=desc,
            details=details,
            status=status_level
        )

    def log_rejection_loop_complete(self, final_status: str, total_iterations: int):
        """Log completion of rejection loop."""
        if final_status == "APPROVED":
            desc = f"Rejection loop converged - Calendar approved after {total_iterations} iteration(s)"
            status = "SUCCESS"
        else:
            desc = f"Max iterations ({total_iterations}) reached - Returning best calendar"
            status = "WARNING"

        self.log_event(
            phase="STEP 3: REJECTION LOOP (AGENT B <-> AGENT C)",
            event_type="COMPLETE",
            description=desc,
            details={
                "final_status": final_status,
                "total_iterations": total_iterations
            },
            status=status
        )

    def log_reports_generation(self):
        """Log start of report generation."""
        self.log_event(
            phase="STEP 4: GENERATING REPORTS",
            event_type="START",
            description="Generating final deliverables and reports...",
            status="INFO"
        )

    def log_report_saved(self, filename: str, description: str):
        """Log individual report saved."""
        self.log_event(
            phase="STEP 4: GENERATING REPORTS",
            event_type="FILE_SAVED",
            description=f"Saved: {filename}",
            details={"filename": filename, "description": description},
            status="SUCCESS"
        )

    def finalize(self, final_status: str):
        """Finalize the journey log."""
        journey_end = datetime.now()
        total_duration = (journey_end - self.journey_start).total_seconds()

        with open(self.journey_path, 'a', encoding='utf-8') as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write("OPTIMIZATION JOURNEY COMPLETE\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Final Status:     {final_status}\n")
            f.write(f"Total Duration:   {total_duration:.1f} seconds ({total_duration/60:.2f} minutes)\n")
            f.write(f"Total Events:     {len(self.events)}\n")

            # Count events by phase
            phase_counts = {}
            for event in self.events:
                phase = event['phase']
                phase_counts[phase] = phase_counts.get(phase, 0) + 1

            f.write("\nEvents by Phase:\n")
            for phase, count in sorted(phase_counts.items()):
                f.write(f"  - {phase}: {count} events\n")

            f.write(f"\nCompleted: {journey_end.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n")

    def get_live_status(self) -> str:
        """Get current live status (for console output)."""
        if not self.events:
            return "Journey not started"

        last_event = self.events[-1]
        elapsed = last_event['elapsed_seconds']

        return f"[{elapsed:.0f}s] {last_event['phase']}: {last_event['description']}"
