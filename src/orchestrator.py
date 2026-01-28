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
from .utils.journey_tracker import JourneyTracker


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

        # Initialize journey tracker
        self.journey = JourneyTracker(output_dir=str(self.output_dir))

        # Agents (initialized later)
        self.analyst = None
        self.strategist = None
        self.auditor = None

        # Execution log
        self.execution_log = []

    def _log_agent_reasoning(self, reasoning_text: str):
        """
        Callback for agents to log their reasoning to the journey tracker.

        Args:
            reasoning_text: Reasoning from agent (prefixed with "Agent X: ...")
        """
        if self.journey:
            self.journey.log_agent_reasoning(reasoning_text)

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
        self.journey.log_report_saved(
            filename="EXECUTION_SUMMARY.txt",
            description="Comprehensive execution summary for presentation"
        )

        # Finalize journey log
        self.journey.finalize(final_status=audit_report['status'])

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
        self.journey.log_data_loading_start()

        data = self.data_loader.load_all()

        self._log_event("data_loading_complete", {
            "sales_rows": len(data["sales"]),
            "promotion_rows": len(data["promotions"]),
            "financial_rows": len(data["financials"])
        })
        self.journey.log_data_loading_complete(
            sales_rows=len(data["sales"]),
            promo_rows=len(data["promotions"])
        )

        return data

    def _run_analyst(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Analyst agent."""
        self._log_event("analyst_start", {})
        self.journey.log_agent_a_start()

        # Check if causal parameters already exist
        causal_params_path = self.output_dir / "causal_parameters.json"
        logger.info(f"{causal_params_path}")
        if causal_params_path.exists():
            logger.info("Causal parameters already exist, loading from file...")
            self.journey.log_event(
                phase="STEP 2: AGENT A (ANALYST)",
                event_type="CACHED",
                description="Loading existing causal parameters from cache",
                details={"file": "outputs/causal_parameters.json"},
                status="INFO"
            )
            with open(causal_params_path, 'r') as f:
                causal_parameters = json.load(f)
            logger.info("Loaded existing causal parameters")

            # Log completion with cached data
            self.journey.log_agent_a_complete(
                mape=causal_parameters.get("baseline_mape", 0),
                method=causal_parameters.get("baseline_method", "cached"),
                iterations=0
            )

            # Log cached parameters details
            self.journey.log_event(
                phase="STEP 2: AGENT A (ANALYST)",
                event_type="CACHED_PARAMETERS",
                description="Using cached causal parameters",
                details={
                    "baseline_velocity": causal_parameters.get("baseline_velocity_avg", 0),
                    "price_elasticity": causal_parameters.get("elasticity_model", {}).get("base_price_elasticity", 0),
                    "discount_buckets": list(causal_parameters.get("elasticity_model", {}).get("discount_lift_factors", {}).keys()),
                    "display_lift": causal_parameters.get("elasticity_model", {}).get("display_lift_multiplier", 0),
                    "seasonality_weeks": len(causal_parameters.get("seasonality_factors", {}))
                },
                status="INFO"
            )
        else:
            # Initialize Agent A (it gets API key from environment internally)
            self.analyst = AnalystAgent(
                data_dir=self.data_dir,
                output_dir=str(self.output_dir),
                journey_tracker=self.journey,
                reasoning_callback=self._log_agent_reasoning
            )

            # Agent A will load data and analyze via its tools
            causal_parameters = self.analyst.analyze()

            # Log completion with new analysis
            self.journey.log_agent_a_complete(
                mape=causal_parameters.get("baseline_mape", 0),
                method=causal_parameters.get("baseline_method", "unknown"),
                iterations=causal_parameters.get("total_iterations", 0)
            )

            # Log detailed Agent A results
            self.journey.log_event(
                phase="STEP 2: AGENT A (ANALYST)",
                event_type="ANALYSIS_RESULTS",
                description="Causal parameters generated successfully",
                details={
                    "baseline_velocity": causal_parameters.get("baseline_velocity_avg", 0),
                    "price_elasticity": causal_parameters.get("elasticity_model", {}).get("base_price_elasticity", 0),
                    "discount_lifts": causal_parameters.get("elasticity_model", {}).get("discount_lift_factors", {}),
                    "display_lift": causal_parameters.get("elasticity_model", {}).get("display_lift_multiplier", 0),
                    "seasonality_weeks": len(causal_parameters.get("seasonality_factors", {})),
                    "baseline_coverage": f"{causal_parameters.get('baseline_coverage_pct', 0):.1f}%"
                },
                status="SUCCESS"
            )

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
            max_iterations=self.max_iterations,
            output_dir=str(self.output_dir),
            data_dir=self.data_dir,
            reasoning_callback=self._log_agent_reasoning
        )

        self._log_event("strategist_initialized", {"objective": objective})

    def _initialize_auditor(self, data: Dict[str, Any]):
        """Initialize the Auditor agent."""
        # AuditorAgent gets API key from environment and uses data_dir
        self.auditor = AuditorAgent(
            data_dir=self.data_dir,
            output_dir=str(self.output_dir),
            reasoning_callback=self._log_agent_reasoning
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
            self.journey.log_agent_b_iteration_start(
                iteration=iteration,
                feedback=feedback.get('feedback') if feedback else None
            )

            calendar = self.strategist.generate_calendar(feedback)

            self._log_event("strategist_generation_complete", {
                "iteration": iteration,
                "events_count": len(calendar.get("calendar_events", [])),
                "total_spend": calendar.get("total_spend", 0)
            })
            # Log calendar generation with more details
            events = calendar.get("calendar_events", [])
            ppgs_used = set(e.get('ppg', 'unknown') for e in events)
            weeks_used = sorted(set(e.get('week', 0) for e in events))

            self.journey.log_agent_b_calendar_generated(
                iteration=iteration,
                event_count=len(events),
                total_spend=calendar.get("total_spend", 0)
            )

            # Log additional calendar details
            self.journey.log_event(
                phase="STEP 3: REJECTION LOOP (AGENT B <-> AGENT C)",
                event_type="CALENDAR_DETAILS",
                description=f"Iteration {iteration}: Calendar composition",
                details={
                    "ppgs": sorted(list(ppgs_used)),
                    "ppg_count": len(ppgs_used),
                    "weeks_range": f"{min(weeks_used)}-{max(weeks_used)}" if weeks_used else "none",
                    "sample_events": [
                        f"Week {e.get('week')}: {e.get('ppg')} at {e.get('retailer')} ({e.get('discount_depth', 0)*100:.0f}% off)"
                        for e in events[:3]  # First 3 events as sample
                    ]
                },
                status="INFO"
            )

            # Validate calendar format (basic check)
            if not calendar.get("calendar_events"):
                logger.error("No calendar events generated by Strategist")
                raise ValueError("Invalid calendar - no events")

            # Auditor reviews calendar
            self._log_event("auditor_review_start", {"iteration": iteration})
            self.journey.log_agent_c_validation_start(iteration=iteration)

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
            self.journey.log_agent_c_result(
                iteration=iteration,
                status=audit_report["status"],
                violations=audit_report.get("violations", []),
                feedback=audit_report.get("feedback")
            )

            # Log detailed violations if rejected
            if audit_report["status"] == "REJECTED" and audit_report.get("violations"):
                violation_details = []
                for v in audit_report["violations"][:5]:  # First 5 violations
                    vtype = v.get('type', v.get('category', 'UNKNOWN'))
                    if 'gap' in vtype.lower():
                        violation_details.append(
                            f"{vtype}: {v.get('description', 'PPG at weeks with insufficient gap')}"
                        )
                    elif 'frequency' in vtype.lower():
                        violation_details.append(
                            f"{vtype}: {v.get('description', 'Too many promotions')}"
                        )
                    else:
                        violation_details.append(
                            f"{vtype}: {v.get('description', str(v))}"
                        )

                self.journey.log_event(
                    phase="STEP 3: REJECTION LOOP (AGENT B <-> AGENT C)",
                    event_type="VIOLATION_DETAILS",
                    description=f"Iteration {iteration}: Top violations found",
                    details={
                        "violations": violation_details,
                        "total_violations": len(audit_report.get("violations", [])),
                        "feedback_summary": audit_report.get("feedback", "")[:200] + "..." if len(audit_report.get("feedback", "")) > 200 else audit_report.get("feedback", "")
                    },
                    status="WARNING"
                )

            # Log the exchange
            logger.info(f"Strategist proposed calendar with {len(calendar['calendar_events'])} events")
            logger.info(f"Total spend: ${calendar.get('total_spend', 0):,.0f}")
            logger.info(f"Auditor status: {audit_report['status']}")

            if audit_report["status"] == "APPROVED":
                logger.info("✓ Calendar APPROVED by Auditor")
                self.journey.log_rejection_loop_complete(
                    final_status="APPROVED",
                    total_iterations=iteration
                )
                return calendar, audit_report

            # Calendar rejected - log violations and prepare feedback
            logger.warning(f"✗ Calendar REJECTED - {len(audit_report['violations'])} violations")
            for violation in audit_report["violations"]:
                # Format violation details based on type or category
                vtype = violation.get('type', violation.get('category', 'UNKNOWN'))

                # Use 'details' field first, fallback to type-specific formatting
                if 'details' in violation:
                    detail_str = violation['details']
                elif 'gap' in vtype.lower() or vtype == 'GAP_VIOLATION':
                    detail_str = f"PPG {violation.get('ppg', 'N/A')} at Retailer {violation.get('retailer', 'N/A')}: weeks {violation.get('week1', 'N/A')}-{violation.get('week2', 'N/A')} (gap: {violation.get('gap', 'N/A')}, required: {violation.get('min_required', 'N/A')})"
                elif 'budget' in vtype.lower() or vtype == 'BUDGET_VIOLATION':
                    # Use 'overage' field if available
                    overage = violation.get('overage', 'N/A')
                    detail_str = f"Budget exceeded by ${overage:,.0f}" if isinstance(overage, (int, float)) else "Budget exceeded"
                elif 'frequency' in vtype.lower() or vtype == 'FREQUENCY_VIOLATION':
                    detail_str = f"PPG {violation.get('ppg', 'N/A')}: {violation.get('count', 0)} promotions exceeds limit {violation.get('max_allowed', 0)}"
                elif 'blackout' in vtype.lower() or vtype == 'BLACKOUT_VIOLATION':
                    detail_str = f"Promotion in blackout week {violation.get('week', 'N/A')}"
                else:
                    # Generic formatting for unknown violation types
                    detail_str = violation.get('description', str(violation))
                logger.warning(f"  - {vtype}: {detail_str}")

            logger.info(f"Auditor feedback: {audit_report['feedback']}")

            feedback = audit_report

        # Max iterations reached without approval - return last calendar anyway
        logger.warning(f"Max iterations ({self.max_iterations}) reached without approval")
        logger.warning(f"Returning last calendar (status: {audit_report.get('status', 'UNKNOWN')})")
        self.journey.log_rejection_loop_complete(
            final_status=audit_report.get('status', 'MAX_ITERATIONS'),
            total_iterations=self.max_iterations
        )
        return calendar, audit_report

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
        self.journey.log_reports_generation()

        # Save optimized calendar as CSV
        calendar_path = self.output_dir / "optimized_calendar.csv"
        self._save_calendar_csv(calendar, calendar_path)
        logger.info(f"Saved: {calendar_path}")
        self.journey.log_report_saved(
            filename="optimized_calendar.csv",
            description="52-week promotion calendar (CSV format)"
        )

        # Save financial impact report as JSON
        financial_path = self.output_dir / "financial_impact_report.json"
        with open(financial_path, "w") as f:
            json.dump(reports["financial_impact"], f, indent=2)
        logger.info(f"Saved: {financial_path}")
        self.journey.log_report_saved(
            filename="financial_impact_report.json",
            description="Base vs. Optimized financial comparison"
        )

        # Save baseline validation as CSV
        validation_path = self.output_dir / "baseline_validation.csv"
        import pandas as pd
        pd.DataFrame([reports["baseline_validation"]]).to_csv(validation_path, index=False)
        logger.info(f"Saved: {validation_path}")
        self.journey.log_report_saved(
            filename="baseline_validation.csv",
            description="Baseline forecast accuracy metrics"
        )

        # Save execution log
        log_path = self.output_dir / "agent_execution_log.txt"
        self._save_execution_log(log_path)
        logger.info(f"Saved: {log_path}")
        self.journey.log_report_saved(
            filename="agent_execution_log.txt",
            description="Complete agent interaction log"
        )

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

        # Print quick summary to console
        quick_summary = generate_quick_summary(output_dir=str(self.output_dir))
        print("\n" + quick_summary)
