"""
Orchestrator for multi-agent TPO system

Coordinates the interaction between Analyst, Strategist, and Auditor agents
to generate an optimized promotion calendar through an iterative feedback loop.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger

from .agents import AnalystAgent, StrategistAgent, AuditorAgent
from .utils import DataLoader, validate_calendar_format
from .utils.report_generator import ExecutionReportGenerator, generate_quick_summary


class TPOOrchestrator:
    """
    Main orchestrator for the Trade Promotion Optimization system.

    Coordinates the three-agent workflow:
    1. Analyst generates causal parameters
    2. Strategist proposes calendar
    3. Auditor validates calendar
    4. Loop back to step 2 if rejected
    """

    def __init__(
        self,
        data_dir: str = "case-data",
        output_dir: str = "outputs",
        max_iterations: int = 10
    ):
        """
        Initialize the orchestrator.

        Args:
            data_dir: Directory containing input data
            output_dir: Directory for output files
            max_iterations: Maximum iterations for strategist-auditor loop
        """
        self.data_dir = data_dir
        self.output_dir = Path(output_dir)
        self.max_iterations = max_iterations

        # Create output directory
        self.output_dir.mkdir(exist_ok=True)

        # Initialize data loader
        self.data_loader = DataLoader(data_dir)

        # Agents (initialized later)
        self.analyst = None
        self.strategist = None
        self.auditor = None

        # Execution log
        self.execution_log = []

    def run(self, objective: str = "volume", budget: float = 1_000_000) -> Dict[str, Any]:
        """
        Execute the full TPO workflow.

        Args:
            objective: Optimization objective ("volume" or "profit")
            budget: Total annual budget

        Returns:
            Dictionary containing final calendar and all reports
        """
        logger.info("=" * 80)
        logger.info("Starting TPO Optimization Workflow")
        logger.info(f"Objective: {objective.upper()}")
        logger.info(f"Budget: ${budget:,.0f}")
        logger.info("=" * 80)

        # Track start time for execution summary
        self.start_time = datetime.now()

        self._log_event("workflow_start", {
            "objective": objective,
            "budget": budget
        })

        # Step 1: Load all data
        logger.info("\n[STEP 1] Loading data...")
        data = self._load_data()

        # Step 2: Run Analyst (Agent A)
        logger.info("\n[STEP 2] Running Analyst (Agent A)...")
        causal_parameters = self._run_analyst(data)

        # Step 3: Initialize Strategist and Auditor
        logger.info("\n[STEP 3] Initializing Strategist (Agent B) and Auditor (Agent C)...")
        self._initialize_strategist(causal_parameters, budget, data, objective)
        self._initialize_auditor(data)

        # Step 4: Iterative optimization loop
        logger.info("\n[STEP 4] Starting iterative optimization loop...")
        final_calendar, audit_report = self._optimization_loop()

        # Step 5: Generate final reports
        logger.info("\n[STEP 5] Generating final reports...")
        reports = self._generate_reports(final_calendar, audit_report, data)

        # Step 6: Save all outputs
        logger.info("\n[STEP 6] Saving outputs...")
        self._save_outputs(final_calendar, reports)

        # Step 7: Generate comprehensive execution summary
        logger.info("\n[STEP 7] Generating execution summary report...")
        end_time = datetime.now()
        self._generate_execution_summary(
            objective=objective,
            budget=budget,
            audit_report=audit_report,
            start_time=self.start_time,
            end_time=end_time
        )

        logger.info("\n" + "=" * 80)
        logger.info("TPO Optimization Complete!")
        logger.info(f"Final Status: {audit_report['status']}")
        logger.info(f"Total Iterations: {self.strategist.iteration if self.strategist else 0}")
        logger.info("=" * 80)

        return {
            "calendar": final_calendar,
            "reports": reports,
            "execution_log": self.execution_log
        }

    def _load_data(self) -> Dict[str, Any]:
        """Load all required data files."""
        self._log_event("data_loading_start", {})

        data = self.data_loader.load_all()

        self._log_event("data_loading_complete", {
            "sales_rows": len(data["sales"]),
            "promotion_rows": len(data["promotions"]),
            "financial_rows": len(data["financials"])
        })

        return data

    def _run_analyst(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Analyst agent."""
        self._log_event("analyst_start", {})

        # Check if causal parameters already exist
        causal_params_path = self.output_dir / "causal_parameters.json"
        if causal_params_path.exists():
            logger.info("Causal parameters already exist, loading from file...")
            with open(causal_params_path, 'r') as f:
                causal_parameters = json.load(f)
            logger.info("Loaded existing causal parameters")
        else:
            # Initialize Agent A with API key
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")

            self.analyst = AnalystAgent(api_key=api_key)

            # Agent A will load data and analyze via its tools
            causal_parameters = self.analyst.analyze()

        self._log_event("analyst_complete", {
            "baseline_avg": causal_parameters.get("baseline_velocity_avg", 0)
        })

        return causal_parameters

    def _initialize_strategist(
        self,
        causal_parameters: Dict[str, Any],
        budget: float,
        data: Dict[str, Any],
        objective: str
    ):
        """Initialize the Strategist agent."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.strategist = StrategistAgent(
            api_key=api_key,
            objective=objective,
            budget_limit=budget,
            max_iterations=self.max_iterations
        )

        self._log_event("strategist_initialized", {"objective": objective})

    def _initialize_auditor(self, data: Dict[str, Any]):
        """Initialize the Auditor agent."""
        # AuditorAgent gets API key from environment and uses data_dir
        self.auditor = AuditorAgent(
            data_dir=self.data_dir,
            output_dir=str(self.output_dir)
        )

        self._log_event("auditor_initialized", {})

    def _optimization_loop(self) -> tuple:
        """
        Execute the iterative optimization loop between Strategist and Auditor.

        Returns:
            Tuple of (final_calendar, audit_report)
        """
        feedback = None
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1

            logger.info(f"\n--- Iteration {iteration} ---")

            # Strategist generates calendar
            self._log_event("strategist_generation_start", {"iteration": iteration})
            calendar = self.strategist.generate_calendar(feedback)
            self._log_event("strategist_generation_complete", {
                "iteration": iteration,
                "events_count": len(calendar.get("calendar_events", [])),
                "total_spend": calendar.get("total_spend", 0)
            })

            # Validate calendar format (basic check)
            if not calendar.get("calendar_events"):
                logger.error("No calendar events generated by Strategist")
                raise ValueError("Invalid calendar - no events")

            # Auditor reviews calendar
            self._log_event("auditor_review_start", {"iteration": iteration})

            # Build constraints dict for auditor
            constraints = {
                "budget_limit": self.strategist.budget_limit if self.strategist else 1000000,
                "min_gap_weeks": 4,  # Default, can be retailer-specific
                "max_promos_per_ppg": 12,  # Default, can be retailer-specific
                "blackout_weeks": []  # From data if available
            }

            # Audit the calendar (Agent B saves to promotion_calendar.json)
            calendar_path = str(self.output_dir / "promotion_calendar.json")
            audit_report = self.auditor.audit(calendar_path, constraints)

            self._log_event("auditor_review_complete", {
                "iteration": iteration,
                "status": audit_report["status"],
                "violations_count": len(audit_report.get("violations", []))
            })

            # Log the exchange
            logger.info(f"Strategist proposed calendar with {len(calendar['calendar_events'])} events")
            logger.info(f"Total spend: ${calendar.get('total_spend', 0):,.0f}")
            logger.info(f"Auditor status: {audit_report['status']}")

            if audit_report["status"] == "APPROVED":
                logger.info("✓ Calendar APPROVED by Auditor")
                return calendar, audit_report

            # Calendar rejected - log violations and prepare feedback
            logger.warning(f"✗ Calendar REJECTED - {len(audit_report['violations'])} violations")
            for violation in audit_report["violations"]:
                # Format violation details based on type
                if violation['type'] == 'GAP_VIOLATION':
                    detail_str = f"PPG {violation['ppg']} at Retailer {violation['retailer']}: weeks {violation['week1']}-{violation['week2']} (gap: {violation['gap']}, required: {violation['min_required']})"
                elif violation['type'] == 'BUDGET_VIOLATION':
                    detail_str = f"Total spend ${violation.get('total_spend', 'N/A'):,.0f} exceeds budget ${violation.get('budget_limit', 'N/A'):,.0f}"
                elif violation['type'] == 'FREQUENCY_VIOLATION':
                    detail_str = f"PPG {violation['ppg']}: {violation.get('count', 0)} promotions exceeds limit {violation.get('max_allowed', 0)}"
                elif violation['type'] == 'BLACKOUT_VIOLATION':
                    detail_str = f"Promotion in blackout week {violation.get('week', 'N/A')}"
                else:
                    # Generic formatting for unknown violation types
                    detail_str = str(violation.get('details', violation))
                logger.warning(f"  - {violation['type']}: {detail_str}")

            logger.info(f"Auditor feedback: {audit_report['feedback']}")

            feedback = audit_report

        # Max iterations reached without approval
        logger.error(f"Max iterations ({self.max_iterations}) reached without approval")
        raise RuntimeError("Failed to generate approved calendar within iteration limit")

    def _generate_reports(
        self,
        calendar: Dict[str, Any],
        audit_report: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate all final reports."""
        reports = {
            "financial_impact": self._generate_financial_impact_report(calendar, data),
            "baseline_validation": self._generate_baseline_validation_report(data),
            "audit_summary": audit_report
        }

        return reports

    def _generate_financial_impact_report(
        self,
        calendar: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate financial impact comparison report."""
        # Simplified financial impact report
        # Full implementation would calculate actual volume/revenue projections
        total_spend = calendar.get("total_spend", 0)
        event_count = len(calendar.get("calendar_events", []))

        return {
            "objective": calendar.get("objective", "unknown"),
            "base_plan": {
                "total_volume": 0,
                "total_revenue": 0,
                "total_margin": 0,
                "total_spend": 0,
                "note": "Baseline calculations require full implementation"
            },
            "optimized_plan": {
                "total_volume": 0,
                "total_revenue": 0,
                "total_margin": 0,
                "total_spend": total_spend,
                "event_count": event_count
            },
            "delta": {
                "volume_lift_pct": 0,
                "revenue_lift_pct": 0,
                "margin_improvement": 0,
                "roi": 0,
                "note": "Projections require full implementation with causal model application"
            }
        }

    def _generate_baseline_validation_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate baseline forecast validation report."""
        # Load from Agent A's output if available
        causal_params_path = self.output_dir / "causal_parameters.json"
        if causal_params_path.exists():
            with open(causal_params_path, 'r') as f:
                params = json.load(f)
                return {
                    "baseline_method": params.get("baseline_method", "unknown"),
                    "mape": params.get("baseline_mape", 0),
                    "coverage_pct": params.get("baseline_coverage_pct", 0)
                }

        return {"baseline_method": "not_available", "mape": 0, "coverage_pct": 0}

    def _save_outputs(self, calendar: Dict[str, Any], reports: Dict[str, Any]):
        """Save all outputs to files."""
        # Save optimized calendar as CSV
        calendar_path = self.output_dir / "optimized_calendar.csv"
        self._save_calendar_csv(calendar, calendar_path)
        logger.info(f"Saved: {calendar_path}")

        # Save financial impact report as JSON
        financial_path = self.output_dir / "financial_impact_report.json"
        with open(financial_path, "w") as f:
            json.dump(reports["financial_impact"], f, indent=2)
        logger.info(f"Saved: {financial_path}")

        # Save baseline validation as CSV
        validation_path = self.output_dir / "baseline_validation.csv"
        import pandas as pd
        pd.DataFrame([reports["baseline_validation"]]).to_csv(validation_path, index=False)
        logger.info(f"Saved: {validation_path}")

        # Save execution log
        log_path = self.output_dir / "agent_execution_log.txt"
        self._save_execution_log(log_path)
        logger.info(f"Saved: {log_path}")

    def _save_calendar_csv(self, calendar: Dict[str, Any], path: Path):
        """Save calendar as CSV file."""
        import pandas as pd

        events = calendar.get("calendar_events", [])
        df = pd.DataFrame(events)

        df.to_csv(path, index=False)

    def _save_execution_log(self, path: Path):
        """Save execution log as text file."""
        with open(path, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("TPO AGENT EXECUTION LOG\n")
            f.write("=" * 80 + "\n\n")

            for entry in self.execution_log:
                f.write(f"[{entry['event']}] {entry.get('details', '')}\n")
                if "data" in entry:
                    f.write(json.dumps(entry["data"], indent=2) + "\n")
                f.write("\n")

    def _log_event(self, event: str, data: Any):
        """Log an event to the execution log."""
        self.execution_log.append({
            "event": event,
            "data": data
        })

    def _generate_execution_summary(
        self,
        objective: str,
        budget: float,
        audit_report: Dict[str, Any],
        start_time: datetime,
        end_time: datetime
    ):
        """Generate comprehensive execution summary report."""
        # Prepare optimization result for report generator
        optimization_result = {
            'status': audit_report.get('status', 'UNKNOWN'),
            'iterations': self.strategist.iteration if self.strategist else 0,
            'objective': objective,
            'violations_history': []  # Could be enhanced to track all iterations
        }

        # Add final violations if rejected
        if audit_report.get('status') == 'REJECTED':
            violations = audit_report.get('violations', [])
            if violations:
                optimization_result['violations_history'].append(violations)

        # Generate comprehensive report
        report_gen = ExecutionReportGenerator(output_dir=str(self.output_dir))
        report = report_gen.generate_comprehensive_report(
            objective=objective,
            budget=budget,
            optimization_result=optimization_result,
            start_time=start_time,
            end_time=end_time
        )

        logger.info(f"Saved: {report_gen.report_path}")

        # Also print quick summary to console
        quick_summary = generate_quick_summary(output_dir=str(self.output_dir))
        print("\n" + quick_summary)
