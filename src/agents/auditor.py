"""
Agent C: The Auditor (LLM-Powered Compliance Validator)

This agent uses Claude API to validate promotional calendars against business constraints
through a hybrid approach: deterministic validation tools + LLM-powered feedback generation.
It ensures 100% accuracy on constraint detection with actionable remediation suggestions.
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
from anthropic import Anthropic
from datetime import datetime
from collections import defaultdict

from ..utils.data_loader import DataLoader


class AuditorAgent:
    """
    LLM-powered auditor that validates promotional calendars against business constraints.

    Uses Claude API with deterministic validation tools to:
    1. Calculate total spend and validate against budget
    2. Check gap rule violations (min spacing per PPG-Retailer)
    3. Check frequency violations (max promos per PPG)
    4. Check blackout period violations
    5. Generate actionable feedback and save audit report
    """

    def __init__(self, data_dir: str = "case-data", output_dir: str = "outputs", reasoning_callback=None):
        """
        Initialize the Auditor Agent.

        Args:
            data_dir: Directory containing input data files
            output_dir: Directory for output files
            reasoning_callback: Optional callback function(reasoning_text) to log agent reasoning
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.reasoning_callback = reasoning_callback

        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = Anthropic(api_key=api_key, base_url='https://api.ai-gateway.tigeranalytics.com')

        # Initialize data loader
        self.data_loader = DataLoader(str(self.data_dir))

        # Storage for data used by tools
        self.finance_data: Optional[pd.DataFrame] = None
        self.promo_config: Optional[pd.DataFrame] = None
        self.causal_parameters: Optional[Dict[str, Any]] = None
        self.calendar_data: Optional[Dict[str, Any]] = None

        # Execution log
        self.execution_log: List[str] = []

    def _log(self, message: str):
        """Add message to execution log and logger."""
        self.execution_log.append(message)
        logger.info(message)

    def _load_required_data(self):
        """Load all required data files for validation."""
        # Note: Finance data loading removed - margin calculations unreliable at PPG level
        # (Finance.xlsx has PPG-level averages aggregating multiple SKUs)

        if self.promo_config is None:
            self._log("Loading Promo config for display fees...")
            self.promo_config = self.data_loader.load_promo_config()

        if self.causal_parameters is None:
            causal_path = self.output_dir / "causal_parameters.json"
            if causal_path.exists():
                self._log("Loading causal parameters from Agent A...")
                with open(causal_path, 'r') as f:
                    self.causal_parameters = json.load(f)
            else:
                logger.warning("causal_parameters.json not found - baseline calculations may be limited")

    def _define_tools(self, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Define tools available to Agent C for constraint validation.

        Args:
            constraints: Dictionary with constraint values (budget_limit, min_gap_weeks, etc.)

        Returns:
            List of tool definitions in Anthropic API format
        """
        return [
            {
                "name": "calculate_total_spend",
                "description": "Calculate total TPR + display costs for entire calendar and validate against budget limit. Returns breakdown by PPG and budget utilization percentage.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "budget_limit": {
                            "type": "number",
                            "description": "Maximum allowed spend in dollars"
                        }
                    },
                    "required": ["budget_limit"]
                }
            },
            {
                "name": "check_gap_violations",
                "description": "Check minimum week gap between promotions for each PPG-Retailer combination. Returns all violations with specific week pairs.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "min_gap_weeks": {
                            "type": "number",
                            "description": "Minimum weeks required between promotions for same PPG-Retailer (default: 4)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "check_frequency_violations",
                "description": "Check maximum promotions per PPG across all retailers (annual limit). Returns PPG summary and any violations.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "max_promos_per_ppg": {
                            "type": "number",
                            "description": "Maximum promotions allowed per PPG per year (default: 12)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "check_blackout_violations",
                "description": "Check if any promotions are scheduled in prohibited blackout weeks. Returns all violations.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "blackout_weeks": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "List of weeks where promotions are prohibited (e.g., [1, 52])"
                        }
                    },
                    "required": ["blackout_weeks"]
                }
            },
            {
                "name": "save_audit_report",
                "description": "Save complete audit report with all violations, warnings, and feedback to JSON file.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["APPROVED", "REJECTED"],
                            "description": "Audit status based on violations"
                        },
                        "violations": {
                            "type": "array",
                            "description": "List of all violations found"
                        },
                        "warnings": {
                            "type": "array",
                            "description": "List of non-critical warnings"
                        },
                        "feedback": {
                            "type": "string",
                            "description": "Natural language feedback for Agent B"
                        },
                        "validation_details": {
                            "type": "object",
                            "description": "Summary of all validation checks"
                        }
                    },
                    "required": ["status", "violations", "feedback"]
                }
            }
        ]

    # ========== TOOL IMPLEMENTATIONS ==========

    def _tool_calculate_total_spend(self, budget_limit: float) -> Dict[str, Any]:
        """
        Calculate total promotion cost and validate against budget.

        Returns budget breakdown, utilization, and violation if over budget.
        """
        self._load_required_data()

        if not self.calendar_data or "calendar_events" not in self.calendar_data:
            return {
                "status": "ERROR",
                "error": "No calendar data loaded"
            }

        events = self.calendar_data["calendar_events"]
        total_tpr_cost = 0.0
        total_display_cost = 0.0
        breakdown_by_ppg = defaultdict(float)

        # Get baseline velocity (required for cost calculations)
        if not self.causal_parameters or "baseline_velocity_avg" not in self.causal_parameters:
            return {
                "status": "ERROR",
                "error": "Baseline velocity not found in causal parameters - cannot calculate costs"
            }
        baseline_velocity = self.causal_parameters["baseline_velocity_avg"]

        for event in events:
            if event != "" and isinstance(event, str):
                event = json.loads(event)
            ppg = event["ppg"]
            discount_depth = event["discount_depth"]
            display_tier = event.get("display_tier", "none")
            display_active = event.get("display_active", False)

            # Get unit price from finance data
            # Note: Finance has "Brand_Group_APN" format, Sales has "Brand_Group" format
            unit_price = 10.0  # Default fallback
            if self.finance_data is not None:
                # Match by prefix since Finance has APN suffixes
                ppg_finance = self.finance_data[self.finance_data["PPG"].str.startswith(ppg + "_", na=False)]
                if not ppg_finance.empty:
                    # Average across all APNs for this PPG
                    unit_price = ppg_finance["List Price"].mean()
                else:
                    logger.warning(f"PPG '{ppg}' not found in Finance.xlsx - using default price $10.00")

            # Calculate TPR cost = baseline_units * discount_depth * unit_price
            tpr_cost = baseline_velocity * discount_depth * unit_price
            total_tpr_cost += tpr_cost

            # Calculate display cost
            display_cost = 0.0
            if display_active and display_tier.lower() != "none":
                # Get display fee from promo config
                # Promo_config has "Promo Type" column like "display_gold  ( per week)"
                if self.promo_config is not None:
                    tier_pattern = f"display_{display_tier.lower()}"
                    matching_rows = self.promo_config[
                        self.promo_config["Promo Type"].str.contains(tier_pattern, case=False, na=False)
                    ]
                    if not matching_rows.empty:
                        cost_str = str(matching_rows.iloc[0]["fixed Spend (USD)"]).strip()
                        try:
                            display_cost = float(cost_str)
                        except ValueError:
                            logger.warning(f"Invalid display cost format: '{cost_str}'")
                total_display_cost += display_cost

            # Track by PPG
            breakdown_by_ppg[ppg] += tpr_cost + display_cost

        total_spend = total_tpr_cost + total_display_cost
        budget_remaining = budget_limit - total_spend
        budget_utilization_pct = (total_spend / budget_limit) * 100 if budget_limit > 0 else 0

        result = {
            "status": "PASS" if total_spend <= budget_limit else "VIOLATED",
            "total_tpr_cost": round(total_tpr_cost, 2),
            "total_display_cost": round(total_display_cost, 2),
            "total_spend": round(total_spend, 2),
            "budget_limit": budget_limit,
            "budget_remaining": round(budget_remaining, 2),
            "budget_utilization_pct": round(budget_utilization_pct, 1),
            "breakdown_by_ppg": {k: round(v, 2) for k, v in breakdown_by_ppg.items()},
            "violation": None
        }

        if total_spend > budget_limit:
            overage = total_spend - budget_limit
            result["violation"] = {
                "type": "Budget Constraint",
                "severity": "CRITICAL",
                "overage": round(overage, 2),
                "overage_pct": round((overage / budget_limit) * 100, 1),
                "details": f"Total spend ${total_spend:,.0f} exceeds budget limit ${budget_limit:,.0f}"
            }

        return result

    def _tool_check_gap_violations(self, min_gap_weeks: int = 4) -> Dict[str, Any]:
        """
        Check minimum spacing between promotions per PPG-Retailer.

        Returns all violations with specific week pairs.
        """
        if not self.calendar_data or "calendar_events" not in self.calendar_data:
            return {"status": "ERROR", "error": "No calendar data loaded"}

        events = self.calendar_data["calendar_events"]

        # Group events by (PPG, Retailer)
        ppg_retailer_events = defaultdict(list)
        for event in events:
            if event != "" and isinstance(event, str):
                event = json.loads(event)
            key = (event["ppg"], event["retailer"])
            ppg_retailer_events[key].append(event["week"])

        violations = []
        ppg_retailer_gaps = {}

        # Check gaps for each PPG-Retailer combination
        for (ppg, retailer), weeks in ppg_retailer_events.items():
            sorted_weeks = sorted(weeks)
            gaps = []

            for i in range(len(sorted_weeks) - 1):
                gap = sorted_weeks[i + 1] - sorted_weeks[i]
                gaps.append(gap)

                if gap < min_gap_weeks:
                    violations.append({
                        "ppg": ppg,
                        "retailer": retailer,
                        "week1": sorted_weeks[i],
                        "week2": sorted_weeks[i + 1],
                        "gap": gap,
                        "min_required": min_gap_weeks,
                        "shortfall": min_gap_weeks - gap,
                        "recommendation": f"Move week {sorted_weeks[i + 1]} to week {sorted_weeks[i] + min_gap_weeks} or later to meet {min_gap_weeks}-week gap requirement"
                    })

            ppg_retailer_gaps[f"({ppg}, {retailer})"] = gaps

        return {
            "status": "PASS" if len(violations) == 0 else "VIOLATED",
            "violations": violations,
            "violation_count": len(violations),
            "ppg_retailer_gaps": ppg_retailer_gaps,
            "severity": "CRITICAL" if len(violations) > 0 else None
        }

    def _tool_check_frequency_violations(self, max_promos_per_ppg: int = 12) -> Dict[str, Any]:
        """
        Count promotions per PPG and check against limit.

        Returns PPG summary and any violations.
        """
        if not self.calendar_data or "calendar_events" not in self.calendar_data:
            return {"status": "ERROR", "error": "No calendar data loaded"}

        events = self.calendar_data["calendar_events"]

        # Count promos per PPG (across all retailers)
        promo_counts = defaultdict(int)
        for event in events:
            if event !="" and isinstance(event, str):
                event = json.loads(event)
            promo_counts[event["ppg"]] += 1

        # Check for violations
        violations = []
        for ppg, count in promo_counts.items():
            if count > max_promos_per_ppg:
                violations.append({
                    "ppg": ppg,
                    "promo_count": count,
                    "max_allowed": max_promos_per_ppg,
                    "overage": count - max_promos_per_ppg,
                    "recommendation": f"Remove {count - max_promos_per_ppg} lowest-performing weeks for this PPG"
                })

        return {
            "status": "PASS" if len(violations) == 0 else "VIOLATED",
            "violations": violations,
            "violation_count": len(violations),
            "ppg_summary": dict(promo_counts),
            "max_allowed": max_promos_per_ppg,
            "severity": "CRITICAL" if len(violations) > 0 else None
        }

    def _tool_check_blackout_violations(self, blackout_weeks: List[int]) -> Dict[str, Any]:
        """
        Check if any promotions are scheduled in blackout weeks.

        Returns all violations.
        """
        if not self.calendar_data or "calendar_events" not in self.calendar_data:
            return {"status": "ERROR", "error": "No calendar data loaded"}

        events = self.calendar_data["calendar_events"]

        violations = []
        for event in events:
            if event != "" and isinstance(event, str):
                event = json.loads(event)
            if event["week"] in blackout_weeks:
                violations.append({
                    "week": event["week"],
                    "ppg": event["ppg"],
                    "retailer": event["retailer"],
                    "reason": f"Week {event['week']} is in blackout period",
                    "recommendation": f"Move to adjacent non-blackout week or remove event"
                })

        return {
            "status": "PASS" if len(violations) == 0 else "VIOLATED",
            "violations": violations,
            "violation_count": len(violations),
            "blackout_weeks": blackout_weeks,
            "events_checked": len(events),
            "severity": "CRITICAL" if len(violations) > 0 else None
        }

    def _tool_save_audit_report(
        self,
        status: str,
        violations: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]],
        feedback: str,
        validation_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save comprehensive audit report to JSON file.

        Returns saved file path.
        """
        iteration = self.calendar_data.get("iteration", 1) if self.calendar_data else 1

        # Build calendar summary
        calendar_summary = {}
        if self.calendar_data and "calendar_events" in self.calendar_data:
            events = self.calendar_data["calendar_events"]
            
            calendar_summary = {
                "total_events": len(events),
                "unique_ppgs": len(set(json.loads(e)["ppg"] for e in events)),
                "unique_retailers": len(set(json.loads(e)["retailer"] for e in events)),
                "weeks_covered": sorted(set(json.loads(e)["week"] for e in events))
            }

        # Add budget info if available
        if "budget_limit" in self.calendar_data:
            calendar_summary["budget_limit"] = self.calendar_data["budget_limit"]
        if "total_projected_spend" in self.calendar_data:
            calendar_summary["total_spend"] = self.calendar_data["total_projected_spend"]

        # Build audit report
        audit_report = {
            "status": status,
            "iteration": iteration,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "calendar_id": f"draft_calendar_iteration_{iteration}.json",
            "calendar_summary": calendar_summary,
            "violations": violations,
            "warnings": warnings,
            "validation_details": validation_details,
            "feedback": feedback,
            "next_steps": []
        }

        # Add next steps based on status
        if status == "REJECTED":
            if violations:
                audit_report["next_steps"] = [
                    f"Address {len(violations)} critical violation(s)",
                    "Revise calendar and resubmit",
                    f"Target iteration {iteration + 1}"
                ]
        else:
            audit_report["next_steps"] = [
                "Calendar approved - proceed to execution",
                "Generate financial impact report",
                "Create final deliverables"
            ]

        # Save to file
        output_path = self.output_dir / f"audit_report_iteration_{iteration}.json"
        with open(output_path, 'w') as f:
            json.dump(audit_report, f, indent=2)

        self._log(f"Audit report saved to {output_path}")

        return {
            "status": "saved",
            "file_path": str(output_path),
            "report_size_bytes": output_path.stat().st_size
        }

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """
        Execute a tool and return its result.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool execution result
        """
        self._log(f"Executing tool: {tool_name} with input: {tool_input}")

        try:
            if tool_name == "calculate_total_spend":
                result = self._tool_calculate_total_spend(**tool_input)
            elif tool_name == "check_gap_violations":
                result = self._tool_check_gap_violations(**tool_input)
            elif tool_name == "check_frequency_violations":
                result = self._tool_check_frequency_violations(**tool_input)
            elif tool_name == "check_blackout_violations":
                result = self._tool_check_blackout_violations(**tool_input)
            elif tool_name == "save_audit_report":
                result = self._tool_save_audit_report(**tool_input)
            else:
                result = {"error": f"Unknown tool: {tool_name}"}

            # Log result (truncated)
            result_str = str(result)
            if len(result_str) > 1000:
                result_str = result_str[:1000] + "... (truncated)"
            self._log(f"Tool {tool_name} result: {result_str}")

            return result

        except Exception as e:
            error_msg = f"Error executing tool {tool_name}: {str(e)}"
            self._log(error_msg)
            logger.exception(error_msg)
            return {"error": error_msg}

    def _build_system_prompt(self, constraints: Dict[str, Any]) -> str:
        """
        Build system prompt with constraint values injected.

        Args:
            constraints: Dictionary with constraint values

        Returns:
            System prompt string
        """
        budget_limit = constraints.get("budget_limit", 1000000)
        min_gap_weeks = constraints.get("min_gap_weeks", 4)
        max_promos_per_ppg = constraints.get("max_promos_per_ppg", 12)
        blackout_weeks = constraints.get("blackout_weeks", [1, 52])

        return f"""You are Agent C, the compliance auditor for promotional calendar validation.

Your role is CRITICAL: ensure all calendars meet business constraints before execution.

You are STRICT, DETERMINISTIC, and HELPFUL.

STRICT: Any critical violation = REJECTED status (no exceptions)
DETERMINISTIC: Same calendar always produces same validation result
HELPFUL: Provide clear, actionable feedback to help Agent B fix violations

---

VALIDATION WORKFLOW:

1. Execute ALL validation tools systematically:
   a. calculate_total_spend (budget check)
   b. check_gap_violations (minimum spacing per PPG-Retailer)
   c. check_frequency_violations (max promos per PPG)
   d. check_blackout_violations (prohibited weeks)

2. Aggregate results:
   - Collect all CRITICAL violations
   - Collect all WARNINGS
   - Calculate summary statistics

3. Determine status:
   - IF any CRITICAL violation: Status = REJECTED
   - IF zero CRITICAL violations: Status = APPROVED

4. Generate feedback:
   - List all violations with specific details
   - Provide quantitative remediation targets (e.g., "Reduce spend by $50K")
   - Suggest specific actions (e.g., "Move week 14 to week 16")
   - Prioritize by business impact

5. Save audit report using save_audit_report tool

---

CONSTRAINTS (ENFORCE EXACTLY):

Budget: Total TPR + display costs ≤ ${budget_limit:,.0f}
Gap Rule: Min {min_gap_weeks} weeks between promos per PPG-Retailer
Frequency: Max {max_promos_per_ppg} promos per PPG per year (across all retailers)
Blackout: No promos in weeks {blackout_weeks}

---

FEEDBACK PRINCIPLES:

1. Be specific: Don't say "violations exist", say "Week 12 and 14 for Brand 1_Group 20 violate gap rule"
2. Be quantitative: "Reduce spend by $50K" not "reduce spend"
3. Be actionable: "Move week 14 to week 16" not "fix gaps"
4. Be prioritized: List violations by severity and business impact
5. Be encouraging: Acknowledge progress if violations decreased from previous iteration

---

IMPORTANT: Execute ALL 4 validation tools before making final decision. Do not skip any checks."""

    def audit(
        self,
        calendar_path: str,
        constraints: Dict[str, Any],
        max_iterations: int = 20
    ) -> Dict[str, Any]:
        """
        Audit a promotional calendar against business constraints.

        Args:
            calendar_path: Path to calendar JSON file from Agent B
            constraints: Dictionary with constraint values (budget_limit, min_gap_weeks, etc.)
            max_iterations: Maximum conversation iterations (default: 20)

        Returns:
            Audit result dictionary with status, violations, and feedback
        """
        self._log("=" * 80)
        self._log("AGENT C: AUDITOR - Starting calendar validation")
        self._log("=" * 80)

        # Load calendar data
        with open(calendar_path, 'r') as f:
            self.calendar_data = json.load(f)

        self._log(f"Loaded calendar: {calendar_path}")
        self._log(f"Calendar has {len(self.calendar_data.get('calendar_events', []))} events")
        self._log(f"Constraints: {constraints}")

        # Load required data
        self._load_required_data()

        # Define tools
        tools = self._define_tools(constraints)

        # Build system prompt
        system_prompt = self._build_system_prompt(constraints)

        # Initialize conversation
        messages = [
            {
                "role": "user",
                "content": f"Validate the promotional calendar. It has {len(self.calendar_data.get('calendar_events', []))} events. Execute all validation tools and provide audit report."
            }
        ]

        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            self._log(f"\n--- Iteration {iteration} ---")

            # Call Claude API
            response = self.client.messages.create(
                model="gemini-2.5-flash",
                max_tokens=4096,
                system=system_prompt,
                tools=tools,
                messages=messages
            )

            # Log Claude's response and send to callback
            reasoning_parts = []
            for block in response.content:
                if hasattr(block, 'text'):
                    self._log(f"Claude: {block.text}")
                    reasoning_parts.append(block.text)

            # Send reasoning to orchestrator via callback
            if reasoning_parts and self.reasoning_callback:
                reasoning_text = " ".join(reasoning_parts).strip()
                self.reasoning_callback(f"Agent C: {reasoning_text}")

            # Process response
            if response.stop_reason == "tool_use":
                # Execute tools
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_result = self._execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(tool_result)
                        })

                # Add assistant message and tool results to conversation
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

            elif response.stop_reason == "end_turn":
                self._log("Agent C completed validation.")
                break
            else:
                self._log(f"Unexpected stop reason: {response.stop_reason}")
                break

        # Save execution log
        log_path = self.output_dir / f"agent_c_execution_log_iteration_{self.calendar_data.get('iteration', 1)}.txt"
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(self.execution_log))
        logger.info(f"Execution log saved to {log_path}")

        # Return final audit result (load from saved file)
        iteration_num = self.calendar_data.get("iteration", 1)
        audit_report_path = self.output_dir / f"audit_report_iteration_{iteration_num}.json"
        if audit_report_path.exists():
            with open(audit_report_path, 'r') as f:
                return json.load(f)
        else:
            return {
                "status": "ERROR",
                "error": "Audit report not generated",
                "iterations": iteration
            }
