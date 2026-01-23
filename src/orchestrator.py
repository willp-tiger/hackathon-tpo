"""
Orchestrator for multi-agent TPO system

Coordinates the interaction between Analyst, Strategist, and Auditor agents
to generate an optimized promotion calendar through an iterative feedback loop.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

from .agents import AnalystAgent, StrategistAgent, AuditorAgent
from .utils import DataLoader, validate_calendar_format, validate_audit_report


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

        logger.info("\n" + "=" * 80)
        logger.info("TPO Optimization Complete!")
        logger.info(f"Final Status: {audit_report['status']}")
        logger.info(f"Total Iterations: {self.strategist.get_iteration_count()}")
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

        self.analyst = AnalystAgent(
            sales_data=data["sales"],
            promo_data=data["promotions"]
        )

        causal_parameters = self.analyst.analyze()

        self._log_event("analyst_complete", {
            "causal_parameters": causal_parameters
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
        display_config = data["promo_config"].to_dict("records")

        self.strategist = StrategistAgent(
            causal_parameters=causal_parameters,
            budget_limit=budget,
            display_config=display_config,
            objective=objective
        )

        self._log_event("strategist_initialized", {"objective": objective})

    def _initialize_auditor(self, data: Dict[str, Any]):
        """Initialize the Auditor agent."""
        self.auditor = AuditorAgent(
            constraints=data["constraints"],
            financials=data["financials"].to_dict("records")
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
                "projected_spend": calendar.get("total_projected_spend", 0)
            })

            # Validate calendar format
            if not validate_calendar_format(calendar):
                logger.error("Invalid calendar format generated by Strategist")
                raise ValueError("Invalid calendar format")

            # Auditor reviews calendar
            self._log_event("auditor_review_start", {"iteration": iteration})
            audit_report = self.auditor.audit(calendar)
            self._log_event("auditor_review_complete", {
                "iteration": iteration,
                "status": audit_report["status"],
                "violations_count": len(audit_report.get("violations", []))
            })

            # Log the exchange
            logger.info(f"Strategist proposed calendar with {len(calendar['calendar_events'])} events")
            logger.info(f"Projected spend: ${calendar['total_projected_spend']:,.0f}")
            logger.info(f"Auditor status: {audit_report['status']}")

            if audit_report["status"] == "APPROVED":
                logger.info("✓ Calendar APPROVED by Auditor")
                return calendar, audit_report

            # Calendar rejected - log violations and prepare feedback
            logger.warning(f"✗ Calendar REJECTED - {len(audit_report['violations'])} violations")
            for violation in audit_report["violations"]:
                logger.warning(f"  - {violation['type']}: {violation['details']}")

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
        # TODO: Implement detailed financial comparison
        return {
            "base_plan": {
                "total_volume": 0,
                "total_revenue": 0,
                "total_margin": 0,
                "total_spend": 0
            },
            "optimized_plan": {
                "total_volume": 0,
                "total_revenue": 0,
                "total_margin": 0,
                "total_spend": calendar.get("total_projected_spend", 0)
            },
            "delta": {
                "volume_lift": 0,
                "revenue_lift": 0,
                "margin_improvement": 0,
                "roi": 0
            }
        }

    def _generate_baseline_validation_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate baseline forecast validation report."""
        if self.analyst:
            # TODO: Implement actual validation on holdout data
            validation_metrics = self.analyst.validate_baseline_forecast(data["sales"])
            return validation_metrics

        return {"mape": 0, "rmse": 0, "mae": 0}

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
