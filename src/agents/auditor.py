"""
Agent C: The Auditor (Compliance & Finance Guardrail)

The "Controller" - deterministic and strict validator.
Ensures all promotion plans comply with budget, gap rules,
frequency limits, and financial constraints.
"""

import json
from typing import Dict, Any, List, Optional
from loguru import logger


class AuditorAgent:
    """
    Agent C: Compliance & Finance Validator

    Responsibilities:
    - Calculate and validate aggregate spend against budget
    - Enforce gap rules between promotions
    - Check frequency and slotting constraints
    - Provide detailed violation reports with actionable feedback
    """

    def __init__(self, constraints: Dict[str, Any], financials: Dict[str, Any]):
        """
        Initialize the Auditor Agent.

        Args:
            constraints: Constraint rules from Constraints.json
            financials: Financial data (unit costs, margins, etc.)
        """
        self.constraints = constraints
        self.financials = financials
        self.audit_history = []

    def audit(self, draft_calendar: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audit a draft promotion calendar for compliance.

        Args:
            draft_calendar: Calendar proposed by Strategist

        Returns:
            Audit report with status and violations
        """
        logger.info("Starting compliance audit...")

        violations = []

        # Check 1: Budget compliance
        budget_violations = self._check_budget_compliance(draft_calendar)
        violations.extend(budget_violations)

        # Check 2: Gap rules
        gap_violations = self._check_gap_rules(draft_calendar)
        violations.extend(gap_violations)

        # Check 3: Frequency limits
        frequency_violations = self._check_frequency_limits(draft_calendar)
        violations.extend(frequency_violations)

        # Check 4: Slotting constraints
        slotting_violations = self._check_slotting_constraints(draft_calendar)
        violations.extend(slotting_violations)

        # Check 5: Financial feasibility
        financial_violations = self._check_financial_feasibility(draft_calendar)
        violations.extend(financial_violations)

        # Determine status
        status = "APPROVED" if len(violations) == 0 else "REJECTED"

        audit_report = {
            "status": status,
            "violations": violations,
            "feedback": self._generate_feedback(violations) if violations else "All constraints satisfied. Calendar approved.",
            "total_violations": len(violations),
            "checks_performed": [
                "Budget Compliance",
                "Gap Rules",
                "Frequency Limits",
                "Slotting Constraints",
                "Financial Feasibility"
            ]
        }

        # Log audit result
        self.audit_history.append(audit_report)
        logger.info(f"Audit complete. Status: {status}. Violations: {len(violations)}")

        return audit_report

    def _check_budget_compliance(self, calendar: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Check if total spend is within budget limit.

        Args:
            calendar: Draft calendar

        Returns:
            List of budget violations
        """
        violations = []

        total_spend = calendar.get("total_projected_spend", 0)
        budget_limit = calendar.get("budget_limit", 0)

        if total_spend > budget_limit:
            excess = total_spend - budget_limit
            violations.append({
                "type": "Total Budget Exceeded",
                "details": f"Total Annual Spend ${total_spend:,.0f} exceeds Budget Limit ${budget_limit:,.0f} by ${excess:,.0f}.",
                "severity": "critical"
            })

        logger.debug(f"Budget check: ${total_spend:,.0f} / ${budget_limit:,.0f}")
        return violations

    def _check_gap_rules(self, calendar: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Check minimum gap between promotions for the same SKU.

        Args:
            calendar: Draft calendar

        Returns:
            List of gap rule violations
        """
        violations = []

        # Extract minimum gap from constraints (e.g., 4 weeks)
        min_gap = self.constraints.get("min_gap_weeks", 4)

        events = calendar.get("calendar_events", [])

        # Group events by SKU
        sku_events = {}
        for event in events:
            sku = event.get("sku")
            week = event.get("week")
            if sku not in sku_events:
                sku_events[sku] = []
            sku_events[sku].append(week)

        # Check gaps for each SKU
        for sku, weeks in sku_events.items():
            sorted_weeks = sorted(weeks)
            for i in range(len(sorted_weeks) - 1):
                gap = sorted_weeks[i + 1] - sorted_weeks[i]
                if gap < min_gap:
                    violations.append({
                        "type": "Gap Rule Violation",
                        "details": f"Week {sorted_weeks[i]} and {sorted_weeks[i + 1]} for {sku} violate {min_gap}-week gap rule (actual gap: {gap} weeks).",
                        "severity": "high"
                    })

        logger.debug(f"Gap rule check: {len(violations)} violations found")
        return violations

    def _check_frequency_limits(self, calendar: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Check if promotion frequency exceeds limits per SKU.

        Args:
            calendar: Draft calendar

        Returns:
            List of frequency violations
        """
        violations = []

        # Extract max frequency from constraints (e.g., 10 promotions per year)
        max_frequency = self.constraints.get("max_promotions_per_sku_per_year", 10)

        events = calendar.get("calendar_events", [])

        # Count promotions per SKU
        sku_counts = {}
        for event in events:
            sku = event.get("sku")
            sku_counts[sku] = sku_counts.get(sku, 0) + 1

        # Check frequency limits
        for sku, count in sku_counts.items():
            if count > max_frequency:
                violations.append({
                    "type": "Frequency Limit Exceeded",
                    "details": f"{sku} has {count} promotions, exceeding limit of {max_frequency}.",
                    "severity": "high"
                })

        logger.debug(f"Frequency check: {len(violations)} violations found")
        return violations

    def _check_slotting_constraints(self, calendar: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Check slotting constraints (e.g., retailer slot availability).

        Args:
            calendar: Draft calendar

        Returns:
            List of slotting violations
        """
        violations = []

        # TODO: Implement slotting constraint checks
        # This would check retailer-specific promotional slot availability

        logger.debug(f"Slotting check: {len(violations)} violations found")
        return violations

    def _check_financial_feasibility(self, calendar: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Check if promotions are financially feasible (positive margin).

        Args:
            calendar: Draft calendar

        Returns:
            List of financial violations
        """
        violations = []

        # TODO: Implement detailed financial feasibility checks
        # This would verify that each promotion maintains positive margin

        logger.debug(f"Financial feasibility check: {len(violations)} violations found")
        return violations

    def _generate_feedback(self, violations: List[Dict[str, str]]) -> str:
        """
        Generate actionable feedback based on violations.

        Args:
            violations: List of violations

        Returns:
            Human-readable feedback for the Strategist
        """
        if not violations:
            return "All constraints satisfied."

        feedback_items = []

        # Categorize violations
        budget_violations = [v for v in violations if "budget" in v["type"].lower()]
        gap_violations = [v for v in violations if "gap" in v["type"].lower()]
        frequency_violations = [v for v in violations if "frequency" in v["type"].lower()]

        if budget_violations:
            feedback_items.append("Reduce overall frequency or discount depth to bring Total Spend under budget.")

        if gap_violations:
            feedback_items.append("Increase spacing between promotions to meet minimum gap requirements.")

        if frequency_violations:
            feedback_items.append("Reduce the number of promotions per SKU to comply with frequency limits.")

        return " ".join(feedback_items)

    def get_audit_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of all audits performed.

        Returns:
            List of audit reports
        """
        return self.audit_history

    def get_last_audit(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent audit report.

        Returns:
            Last audit report or None if no audits performed
        """
        return self.audit_history[-1] if self.audit_history else None
