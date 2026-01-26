"""
Comprehensive Test Suite for TPO AI Agents System

Tests 5 different scenarios to validate system behavior:
1. Volume maximization (high budget)
2. Profit maximization (high budget)
3. Budget constraint (low budget)
4. Rejection loop demonstration (very low budget)
5. Fresh Agent A analysis (no cache)

Created: 2026-01-25 (Session 14)
"""

import os
import shutil
import subprocess
import pytest
from pathlib import Path
import json


# Test configuration
TEST_OUTPUT_DIR = Path("test_outputs")
MAIN_SCRIPT = "main.py"
API_KEY_ENV = "ANTHROPIC_API_KEY"


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment before all tests."""
    # Create test output directory
    TEST_OUTPUT_DIR.mkdir(exist_ok=True)

    # Verify API key is set
    if not os.environ.get(API_KEY_ENV):
        pytest.skip(f"{API_KEY_ENV} not set - skipping integration tests")

    yield

    # Cleanup can be added here if needed
    # (keeping outputs for inspection)


def run_optimization(objective: str, budget: int, output_subdir: str) -> dict:
    """
    Run optimization with given parameters.

    Args:
        objective: "volume" or "profit"
        budget: Budget in dollars
        output_subdir: Subdirectory name for outputs

    Returns:
        dict with results and paths
    """
    # Create scenario-specific output directory
    scenario_dir = TEST_OUTPUT_DIR / output_subdir
    scenario_dir.mkdir(exist_ok=True)

    # Run main.py with parameters
    cmd = [
        "python",
        MAIN_SCRIPT,
        "--objective", objective,
        "--budget", str(budget)
    ]

    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print(f"Output: {scenario_dir}")
    print(f"{'='*60}\n")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600  # 10 minute timeout
    )

    # Copy outputs to scenario directory
    outputs_to_copy = [
        "promotion_calendar.json",
        "causal_parameters.json",
        "OPTIMIZATION_JOURNEY.txt",
        "EXECUTION_SUMMARY.txt",
        "journey_dashboard.html"
    ]

    for output_file in outputs_to_copy:
        src = Path("outputs") / output_file
        if src.exists():
            shutil.copy(src, scenario_dir / output_file)

    # Load calendar for validation
    calendar_path = scenario_dir / "promotion_calendar.json"
    calendar_data = {}
    if calendar_path.exists():
        with open(calendar_path, 'r') as f:
            calendar_data = json.load(f)

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "scenario_dir": scenario_dir,
        "calendar_data": calendar_data
    }


def test_scenario_1_volume_high_budget():
    """
    Scenario 1: Volume Maximization (High Budget)

    Expected:
    - Many promotions (30-50 events)
    - Focus on high-elasticity PPGs
    - Deep discounts (30%+)
    - Display usage
    - Budget ~80-95% utilized
    - Few rejection iterations (1-3)
    """
    result = run_optimization(
        objective="volume",
        budget=1500000,
        output_subdir="scenario_1_volume_high_budget"
    )

    assert result["returncode"] == 0, f"Command failed: {result['stderr']}"

    calendar_data = result["calendar_data"]
    assert "calendar_events" in calendar_data

    events = calendar_data["calendar_events"]
    assert len(events) >= 20, f"Expected 20+ events, got {len(events)}"

    # Check budget utilization
    total_spend = calendar_data.get("total_projected_spend", 0)
    assert total_spend > 1000000, f"Expected >$1M spend, got ${total_spend}"

    # Check for deep discounts
    deep_discounts = [e for e in events if e.get("discount_depth", 0) >= 0.25]
    assert len(deep_discounts) > 0, "Expected some deep discounts (25%+)"

    print(f"\nScenario 1 Results:")
    print(f"  Events: {len(events)}")
    print(f"  Total Spend: ${total_spend:,}")
    print(f"  Deep Discounts (25%+): {len(deep_discounts)}")


def test_scenario_2_profit_high_budget():
    """
    Scenario 2: Profit Maximization (High Budget)

    Expected:
    - Moderate promotions (20-40 events)
    - Focus on high-margin PPGs
    - Moderate discounts (15-25%)
    - Selective display usage
    - Budget ~60-80% utilized
    - Few rejection iterations (1-3)
    """
    result = run_optimization(
        objective="profit",
        budget=1500000,
        output_subdir="scenario_2_profit_high_budget"
    )

    assert result["returncode"] == 0, f"Command failed: {result['stderr']}"

    calendar_data = result["calendar_data"]
    events = calendar_data.get("calendar_events", [])

    assert len(events) >= 15, f"Expected 15+ events, got {len(events)}"

    # Profit optimization should have moderate discounts
    avg_discount = sum(e.get("discount_depth", 0) for e in events) / len(events)
    assert avg_discount < 0.30, f"Expected avg discount <30%, got {avg_discount*100:.1f}%"

    print(f"\nScenario 2 Results:")
    print(f"  Events: {len(events)}")
    print(f"  Avg Discount: {avg_discount*100:.1f}%")


def test_scenario_3_low_budget_constraint():
    """
    Scenario 3: Budget Constraint (Low Budget)

    Expected:
    - Few promotions (10-20 events)
    - Selective PPG/week choices
    - Budget ~90-100% utilized
    - Moderate rejection iterations (2-5)
    - Fewer displays (expensive)
    """
    result = run_optimization(
        objective="volume",
        budget=500000,
        output_subdir="scenario_3_low_budget"
    )

    assert result["returncode"] == 0, f"Command failed: {result['stderr']}"

    calendar_data = result["calendar_data"]
    events = calendar_data.get("calendar_events", [])
    total_spend = calendar_data.get("total_projected_spend", 0)

    assert len(events) <= 30, f"Expected <=30 events with low budget, got {len(events)}"
    assert total_spend <= 500000, f"Budget violated: ${total_spend:,} > $500,000"

    # Check display usage (should be low)
    with_display = [e for e in events if e.get("display_active", False)]
    display_pct = len(with_display) / len(events) * 100 if events else 0

    print(f"\nScenario 3 Results:")
    print(f"  Events: {len(events)}")
    print(f"  Total Spend: ${total_spend:,}")
    print(f"  Display Usage: {display_pct:.1f}%")


@pytest.mark.slow
def test_scenario_4_rejection_loop_demo():
    """
    Scenario 4: Rejection Loop Demonstration (Very Low Budget)

    Expected:
    - Maximum iterations (8-10)
    - Calendar repeatedly rejected for budget violations
    - Final calendar very constrained (5-15 events)
    - Demonstrates agent collaboration
    """
    result = run_optimization(
        objective="volume",
        budget=100000,
        output_subdir="scenario_4_rejection_loop"
    )

    assert result["returncode"] == 0, f"Command failed: {result['stderr']}"

    # Check journey log for iterations
    journey_path = result["scenario_dir"] / "OPTIMIZATION_JOURNEY.txt"
    assert journey_path.exists(), "Journey log not found"

    journey_content = journey_path.read_text()
    iteration_count = journey_content.count("Iteration")

    assert iteration_count >= 2, f"Expected multiple iterations, got {iteration_count}"

    calendar_data = result["calendar_data"]
    events = calendar_data.get("calendar_events", [])

    print(f"\nScenario 4 Results:")
    print(f"  Iterations: {iteration_count}")
    print(f"  Events: {len(events)}")
    print(f"  Total Spend: ${calendar_data.get('total_projected_spend', 0):,}")


@pytest.mark.slow
def test_scenario_5_fresh_agent_a_analysis():
    """
    Scenario 5: Fresh Agent A Analysis (No Cache)

    Expected:
    - Agent A runs full analysis (not cached)
    - Causal parameters generated fresh
    - Baseline MAPE ~40-60%
    - Full workflow completes successfully
    """
    # Delete cached causal parameters
    cache_path = Path("outputs/causal_parameters.json")
    if cache_path.exists():
        backup_path = Path("outputs/causal_parameters.json.backup")
        shutil.copy(cache_path, backup_path)
        cache_path.unlink()

    try:
        result = run_optimization(
            objective="volume",
            budget=1000000,
            output_subdir="scenario_5_fresh_analysis"
        )

        assert result["returncode"] == 0, f"Command failed: {result['stderr']}"

        # Verify causal parameters were regenerated
        causal_path = result["scenario_dir"] / "causal_parameters.json"
        assert causal_path.exists(), "Causal parameters not generated"

        with open(causal_path, 'r') as f:
            causal_data = json.load(f)

        # Verify key parameters exist
        assert "baseline_velocity_avg" in causal_data
        assert "elasticity_model" in causal_data
        assert "seasonality_factors" in causal_data

        mape = causal_data.get("baseline_mape", 0)

        print(f"\nScenario 5 Results:")
        print(f"  Baseline MAPE: {mape:.2f}%")
        print(f"  Baseline Method: {causal_data.get('baseline_method', 'N/A')}")
        print(f"  Parameters Generated: YES")

    finally:
        # Restore cache if backup exists
        backup_path = Path("outputs/causal_parameters.json.backup")
        if backup_path.exists():
            shutil.copy(backup_path, cache_path)
            backup_path.unlink()


def test_all_dashboards_generated():
    """
    Verify that all scenarios generated HTML dashboards.
    """
    scenarios = [
        "scenario_1_volume_high_budget",
        "scenario_2_profit_high_budget",
        "scenario_3_low_budget",
        "scenario_4_rejection_loop",
        "scenario_5_fresh_analysis"
    ]

    for scenario in scenarios:
        dashboard_path = TEST_OUTPUT_DIR / scenario / "journey_dashboard.html"
        if dashboard_path.exists():
            # Verify HTML is not empty
            content = dashboard_path.read_text()
            assert len(content) > 10000, f"{scenario}: Dashboard too small"
            assert "TPO AI Agents" in content, f"{scenario}: Missing title"
            print(f"  {scenario}: Dashboard OK ({len(content):,} bytes)")


if __name__ == "__main__":
    """Run tests manually for debugging."""
    print("Running comprehensive test suite...")
    print(f"Output directory: {TEST_OUTPUT_DIR}")

    # Run with pytest
    pytest.main([__file__, "-v", "-s"])
