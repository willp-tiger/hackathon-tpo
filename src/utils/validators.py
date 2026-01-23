"""
Validation utilities for data and calendar formats
"""

from typing import Dict, Any, List
from loguru import logger


def validate_calendar_format(calendar: Dict[str, Any]) -> bool:
    """
    Validate that a calendar has the required format.

    Args:
        calendar: Calendar dictionary to validate

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["objective", "total_projected_spend", "budget_limit", "calendar_events"]

    for field in required_fields:
        if field not in calendar:
            logger.error(f"Missing required field: {field}")
            return False

    # Validate calendar events
    events = calendar.get("calendar_events", [])
    if not isinstance(events, list):
        logger.error("calendar_events must be a list")
        return False

    for i, event in enumerate(events):
        if not validate_event_format(event, i):
            return False

    return True


def validate_event_format(event: Dict[str, Any], index: int = 0) -> bool:
    """
    Validate that a calendar event has the required format.

    Args:
        event: Event dictionary to validate
        index: Event index for error reporting

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["week", "sku", "discount_depth", "display_active"]

    for field in required_fields:
        if field not in event:
            logger.error(f"Event {index} missing required field: {field}")
            return False

    # Validate week number
    week = event.get("week")
    if not isinstance(week, int) or week < 1 or week > 52:
        logger.error(f"Event {index} has invalid week number: {week}")
        return False

    # Validate discount depth
    discount = event.get("discount_depth")
    if not isinstance(discount, (int, float)) or discount < 0 or discount > 1:
        logger.error(f"Event {index} has invalid discount depth: {discount}")
        return False

    # Validate display_active
    display = event.get("display_active")
    if not isinstance(display, bool):
        logger.error(f"Event {index} has invalid display_active: {display}")
        return False

    return True


def validate_constraints(constraints: Dict[str, Any]) -> bool:
    """
    Validate constraints dictionary format.

    Args:
        constraints: Constraints dictionary to validate

    Returns:
        True if valid, False otherwise
    """
    expected_fields = [
        "min_gap_weeks",
        "max_promotions_per_sku_per_year",
        "total_annual_budget"
    ]

    for field in expected_fields:
        if field not in constraints:
            logger.warning(f"Constraints missing optional field: {field}")

    return True


def validate_causal_parameters(params: Dict[str, Any]) -> bool:
    """
    Validate causal parameters format from Analyst agent.

    Args:
        params: Causal parameters dictionary

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["baseline_velocity_avg", "elasticity_model", "display_lift_multiplier"]

    for field in required_fields:
        if field not in params:
            logger.error(f"Causal parameters missing required field: {field}")
            return False

    # Validate elasticity model structure
    elasticity = params.get("elasticity_model", {})
    if "discount_lift_factors" not in elasticity:
        logger.error("Elasticity model missing discount_lift_factors")
        return False

    return True


def validate_audit_report(report: Dict[str, Any]) -> bool:
    """
    Validate audit report format from Auditor agent.

    Args:
        report: Audit report dictionary

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["status", "violations", "feedback"]

    for field in required_fields:
        if field not in report:
            logger.error(f"Audit report missing required field: {field}")
            return False

    # Validate status
    status = report.get("status")
    if status not in ["APPROVED", "REJECTED"]:
        logger.error(f"Invalid audit status: {status}")
        return False

    # Validate violations format
    violations = report.get("violations", [])
    if not isinstance(violations, list):
        logger.error("violations must be a list")
        return False

    return True
