"""
Real-time Iteration Tracker for Multi-Agent Rejection Loop

Logs each iteration of the Agent B <-> Agent C feedback loop in real-time,
allowing users to monitor the optimization process as it progresses.
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import json


class IterationTracker:
    """
    Tracks and logs each iteration of the rejection loop in real-time.

    Creates an iteration journal that documents:
    - Iteration number
    - Timestamp
    - Agent B's calendar proposal (event count, spend)
    - Agent C's validation result (status, violations)
    - Feedback provided
    - Duration
    """

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.journal_path = self.output_dir / "ITERATION_JOURNAL.txt"
        self.iterations: List[Dict[str, Any]] = []
        self.workflow_start = None

        # Initialize journal file
        self._initialize_journal()

    def _initialize_journal(self):
        """Initialize the iteration journal file."""
        with open(self.journal_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("REJECTION LOOP - ITERATION JOURNAL\n")
            f.write("=" * 80 + "\n")
            f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            f.write("This journal tracks the Agent B <-> Agent C feedback loop in real-time.\n")
            f.write("Each iteration shows:\n")
            f.write("  - Strategist's calendar proposal\n")
            f.write("  - Auditor's validation result\n")
            f.write("  - Violations detected (if any)\n")
            f.write("  - Feedback for next iteration\n\n")
            f.write("=" * 80 + "\n\n")

    def start_workflow(self):
        """Mark the start of the optimization workflow."""
        self.workflow_start = datetime.now()

    def log_iteration(
        self,
        iteration_num: int,
        calendar: Dict[str, Any],
        audit_result: Dict[str, Any],
        duration_seconds: float = None
    ):
        """
        Log a single iteration in real-time.

        Args:
            iteration_num: Iteration number (1-based)
            calendar: Calendar proposal from Agent B
            audit_result: Validation result from Agent C
            duration_seconds: Time taken for this iteration
        """
        iteration_start = datetime.now()

        # Extract key metrics
        event_count = len(calendar.get("calendar_events", []))
        total_spend = calendar.get("total_spend", 0)
        status = audit_result.get("status", "UNKNOWN")
        violations = audit_result.get("violations", [])
        feedback = audit_result.get("feedback", "")

        # Create iteration record
        iteration_record = {
            "iteration": iteration_num,
            "timestamp": iteration_start.isoformat(),
            "calendar": {
                "event_count": event_count,
                "total_spend": total_spend
            },
            "audit": {
                "status": status,
                "violation_count": len(violations),
                "violations": violations
            },
            "feedback": feedback,
            "duration_seconds": duration_seconds
        }

        self.iterations.append(iteration_record)

        # Write to journal immediately (real-time)
        self._write_iteration_to_journal(iteration_record)

        # Also save JSON version for programmatic access
        self._save_json_log()

    def _write_iteration_to_journal(self, record: Dict[str, Any]):
        """Write iteration details to the text journal file."""
        with open(self.journal_path, 'a', encoding='utf-8') as f:
            f.write(f"ITERATION {record['iteration']}\n")
            f.write("-" * 80 + "\n")
            f.write(f"Timestamp: {record['timestamp']}\n\n")

            # Agent B proposal
            f.write("STRATEGIST (Agent B) PROPOSAL:\n")
            f.write(f"  Events Generated:  {record['calendar']['event_count']}\n")
            f.write(f"  Total Spend:       ${record['calendar']['total_spend']:,.2f}\n")
            f.write("\n")

            # Agent C validation
            f.write("AUDITOR (Agent C) VALIDATION:\n")
            f.write(f"  Status:            {record['audit']['status']}\n")
            f.write(f"  Violations Found:  {record['audit']['violation_count']}\n")

            if record['audit']['violations']:
                f.write("\n  VIOLATIONS:\n")
                for i, violation in enumerate(record['audit']['violations'], 1):
                    v_type = violation.get('type', 'UNKNOWN')
                    f.write(f"    {i}. {v_type}\n")

                    # Format violation details based on type
                    if v_type == 'GAP_VIOLATION':
                        f.write(f"       PPG: {violation.get('ppg', 'N/A')}\n")
                        f.write(f"       Retailer: {violation.get('retailer', 'N/A')}\n")
                        f.write(f"       Weeks: {violation.get('week1', 'N/A')} - {violation.get('week2', 'N/A')}\n")
                        f.write(f"       Gap: {violation.get('gap', 'N/A')} (Required: {violation.get('min_required', 'N/A')})\n")
                    elif v_type == 'BUDGET_VIOLATION':
                        f.write(f"       Total Spend: ${violation.get('total_spend', 0):,.2f}\n")
                        f.write(f"       Budget Limit: ${violation.get('budget_limit', 0):,.2f}\n")
                    elif v_type == 'FREQUENCY_VIOLATION':
                        f.write(f"       PPG: {violation.get('ppg', 'N/A')}\n")
                        f.write(f"       Count: {violation.get('count', 0)} (Max: {violation.get('max_allowed', 0)})\n")
                    elif v_type == 'BLACKOUT_VIOLATION':
                        f.write(f"       Week: {violation.get('week', 'N/A')}\n")
                    f.write("\n")

            # Feedback
            if record['audit']['status'] == 'REJECTED':
                f.write("\n  FEEDBACK TO STRATEGIST:\n")
                # Wrap feedback text at 76 characters
                feedback_lines = record['feedback'].split('\n')
                for line in feedback_lines:
                    if len(line) <= 76:
                        f.write(f"    {line}\n")
                    else:
                        # Simple word wrap
                        words = line.split()
                        current_line = "    "
                        for word in words:
                            if len(current_line) + len(word) + 1 <= 80:
                                current_line += word + " "
                            else:
                                f.write(current_line.rstrip() + "\n")
                                current_line = "    " + word + " "
                        if current_line.strip():
                            f.write(current_line.rstrip() + "\n")

            # Duration
            if record['duration_seconds']:
                f.write(f"\n  Duration: {record['duration_seconds']:.1f} seconds\n")

            f.write("\n" + "=" * 80 + "\n\n")

    def _save_json_log(self):
        """Save iteration log as JSON for programmatic access."""
        json_path = self.output_dir / "iteration_log.json"
        with open(json_path, 'w') as f:
            json.dump({
                "workflow_start": self.workflow_start.isoformat() if self.workflow_start else None,
                "iterations": self.iterations
            }, f, indent=2)

    def finalize(self, final_status: str, total_iterations: int):
        """
        Finalize the journal with summary statistics.

        Args:
            final_status: Final calendar status (APPROVED/REJECTED)
            total_iterations: Total number of iterations
        """
        workflow_end = datetime.now()
        total_duration = (workflow_end - self.workflow_start).total_seconds() if self.workflow_start else 0

        # Count violations by type across all iterations
        violation_summary = {}
        for iteration in self.iterations:
            for violation in iteration['audit']['violations']:
                v_type = violation.get('type', 'UNKNOWN')
                violation_summary[v_type] = violation_summary.get(v_type, 0) + 1

        with open(self.journal_path, 'a', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("REJECTION LOOP SUMMARY\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Final Status:       {final_status}\n")
            f.write(f"Total Iterations:   {total_iterations}\n")
            f.write(f"Total Duration:     {total_duration:.1f} seconds ({total_duration/60:.2f} minutes)\n")

            if violation_summary:
                f.write(f"\nViolations Encountered:\n")
                for v_type, count in sorted(violation_summary.items()):
                    f.write(f"  - {v_type}: {count}\n")

            if final_status == "APPROVED":
                convergence_iter = total_iterations
                f.write(f"\nConvergence: Approved at iteration {convergence_iter}\n")
            else:
                f.write(f"\nConvergence: Max iterations reached without approval\n")

            f.write("\n" + "=" * 80 + "\n")
            f.write(f"Completed: {workflow_end.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n")

    def get_summary(self) -> str:
        """Get a quick text summary of the rejection loop."""
        if not self.iterations:
            return "No iterations logged yet."

        total_violations = sum(len(it['audit']['violations']) for it in self.iterations)
        approved_count = sum(1 for it in self.iterations if it['audit']['status'] == 'APPROVED')
        rejected_count = len(self.iterations) - approved_count

        summary = f"""
Rejection Loop Summary:
  Total Iterations:  {len(self.iterations)}
  Approved:          {approved_count}
  Rejected:          {rejected_count}
  Total Violations:  {total_violations}

  Journal saved to: {self.journal_path}
"""
        return summary
