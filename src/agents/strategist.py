"""
Agent B: The Strategist (Optimizer)

The creative intelligence that constructs a future promotion calendar
optimized for specific business objectives (Volume or Profit).
"""

import json
from typing import Dict, Any, List, Optional
from loguru import logger


class StrategistAgent:
    """
    Agent B: Promotion Calendar Optimizer

    Responsibilities:
    - Ingest causal parameters from Agent A
    - Generate promotion calendar optimized for Volume or Profit objective
    - Iterate based on feedback from Agent C (Auditor)
    - Provide clear reasoning for each promotion decision
    """

    def __init__(
        self,
        causal_parameters: Dict[str, Any],
        budget_limit: float,
        display_config: Dict[str, Any],
        objective: str = "volume"
    ):
        """
        Initialize the Strategist Agent.

        Args:
            causal_parameters: Output from Agent A
            budget_limit: Total annual budget constraint
            display_config: Display configuration and costs
            objective: Optimization objective - "volume" or "profit"
        """
        self.causal_parameters = causal_parameters
        self.budget_limit = budget_limit
        self.display_config = display_config
        self.objective = objective.lower()
        self.iteration_count = 0
        self.draft_calendar = None

        if self.objective not in ["volume", "profit"]:
            raise ValueError(f"Invalid objective: {objective}. Must be 'volume' or 'profit'")

    def generate_calendar(self, feedback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate or regenerate promotion calendar.

        Args:
            feedback: Optional feedback from Auditor for iteration

        Returns:
            Draft calendar with promotion events and reasoning
        """
        self.iteration_count += 1

        if feedback:
            logger.info(f"Iteration {self.iteration_count}: Regenerating based on auditor feedback")
            logger.debug(f"Feedback received: {feedback}")
        else:
            logger.info(f"Iteration {self.iteration_count}: Generating initial calendar")

        # Generate calendar based on objective
        if self.objective == "volume":
            calendar = self._optimize_for_volume(feedback)
        else:
            calendar = self._optimize_for_profit(feedback)

        self.draft_calendar = calendar
        return calendar

    def _optimize_for_volume(self, feedback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate calendar optimized for maximum unit volume.

        Args:
            feedback: Optional auditor feedback for adjustments

        Returns:
            Calendar optimized for volume
        """
        logger.debug("Optimizing for maximum unit volume...")

        # Extract elasticity parameters
        elasticity = self.causal_parameters.get("elasticity_model", {})
        baseline = self.causal_parameters.get("baseline_velocity_avg", 150)
        display_lift = self.causal_parameters.get("display_lift_multiplier", 1.4)

        # TODO: Implement intelligent calendar generation
        # For now, create a placeholder structure

        calendar_events = []

        # Example: Q1 peak promotion
        calendar_events.append({
            "week": 12,
            "sku": "SKU_123",
            "discount_depth": 0.30,
            "display_active": True,
            "reasoning": "Selected 30% depth to maximize unit velocity during Q1 peak.",
            "projected_outcome": "Lift of 3.8x baseline.",
            "projected_units": int(baseline * 3.8 * display_lift),
            "projected_spend": 0  # TODO: Calculate actual spend
        })

        total_spend = sum(event["projected_spend"] for event in calendar_events)

        return {
            "objective": "Maximize Unit Volume (Market Share)",
            "total_projected_spend": total_spend,
            "budget_limit": self.budget_limit,
            "iteration": self.iteration_count,
            "calendar_events": calendar_events,
            "adjustments_made": self._get_adjustments_description(feedback) if feedback else None
        }

    def _optimize_for_profit(self, feedback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate calendar optimized for maximum profit.

        Args:
            feedback: Optional auditor feedback for adjustments

        Returns:
            Calendar optimized for profit
        """
        logger.debug("Optimizing for maximum profit margin...")

        # Extract elasticity parameters
        elasticity = self.causal_parameters.get("elasticity_model", {})
        baseline = self.causal_parameters.get("baseline_velocity_avg", 150)

        # TODO: Implement profit optimization logic
        # For now, create a placeholder structure

        calendar_events = []

        # Example: More conservative promotion strategy for profit
        calendar_events.append({
            "week": 16,
            "sku": "SKU_123",
            "discount_depth": 0.15,
            "display_active": False,
            "reasoning": "Selected 15% depth to balance volume and margin preservation.",
            "projected_outcome": "Lift of 1.8x baseline with higher margin retention.",
            "projected_units": int(baseline * 1.8),
            "projected_margin": 0,  # TODO: Calculate actual margin
            "projected_spend": 0  # TODO: Calculate actual spend
        })

        total_spend = sum(event["projected_spend"] for event in calendar_events)

        return {
            "objective": "Maximize Profit Margin",
            "total_projected_spend": total_spend,
            "budget_limit": self.budget_limit,
            "iteration": self.iteration_count,
            "calendar_events": calendar_events,
            "adjustments_made": self._get_adjustments_description(feedback) if feedback else None
        }

    def _get_adjustments_description(self, feedback: Dict[str, Any]) -> str:
        """
        Generate human-readable description of adjustments made based on feedback.

        Args:
            feedback: Auditor feedback

        Returns:
            Description of adjustments
        """
        if not feedback or feedback.get("status") == "APPROVED":
            return "No adjustments needed"

        violations = feedback.get("violations", [])
        adjustments = []

        for violation in violations:
            violation_type = violation.get("type", "Unknown")
            if "budget" in violation_type.lower():
                adjustments.append("Reduced promotion frequency and depth to meet budget")
            elif "gap" in violation_type.lower():
                adjustments.append("Increased spacing between promotions to meet gap rules")
            elif "frequency" in violation_type.lower():
                adjustments.append("Reduced total promotion count to meet frequency limits")

        return "; ".join(adjustments) if adjustments else "Addressed compliance violations"

    def get_draft_calendar(self) -> Optional[Dict[str, Any]]:
        """
        Get the current draft calendar.

        Returns:
            Draft calendar or None if not yet generated
        """
        return self.draft_calendar

    def get_iteration_count(self) -> int:
        """
        Get the current iteration count.

        Returns:
            Number of iterations executed
        """
        return self.iteration_count
