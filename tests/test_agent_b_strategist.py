"""
Test script for Agent B (Strategist)

Tests calendar generation for both volume and profit objectives.
"""

import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.strategist import StrategistAgent


def test_volume_objective():
    """Test calendar generation for volume objective."""
    print("\n" + "=" * 80)
    print("TEST 1: Volume Objective Calendar Generation")
    print("=" * 80 + "\n")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return False

    try:
        agent = StrategistAgent(
            api_key=api_key,
            objective="volume",
            budget_limit=1000000,
            max_iterations=5  # Limit for testing
        )

        result = agent.generate_calendar()

        print("\n" + "-" * 80)
        print("RESULT:")
        print("-" * 80)
        print(f"Events Generated: {result.get('event_count', 0)}")
        print(f"Total Spend: ${result.get('total_spend', 0):,.0f}")
        print(f"Budget Utilization: {result.get('budget_utilization_pct', 0):.1f}%")
        print(f"Iterations: {result.get('iterations', 0)}")
        print("\nSample Events:")
        for event in result.get('calendar_events', [])[:3]:
            print(f"  - Week {event['week']}: {event['ppg']} @ {event['retailer']}")
            print(f"    Discount: {event['discount_depth']*100:.0f}%, Display: {event['display_tier']}")
            print(f"    Reasoning: {event.get('reasoning', 'N/A')[:80]}...")

        print("\n[PASS] Volume calendar generated successfully\n")
        return True

    except Exception as e:
        print(f"\n[FAIL] {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_profit_objective():
    """Test calendar generation for profit objective."""
    print("\n" + "=" * 80)
    print("TEST 2: Profit Objective Calendar Generation")
    print("=" * 80 + "\n")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return False

    try:
        agent = StrategistAgent(
            api_key=api_key,
            objective="profit",
            budget_limit=1500000,
            max_iterations=5
        )

        result = agent.generate_calendar()

        print("\n" + "-" * 80)
        print("RESULT:")
        print("-" * 80)
        print(f"Events Generated: {result.get('event_count', 0)}")
        print(f"Total Spend: ${result.get('total_spend', 0):,.0f}")
        print(f"Budget Utilization: {result.get('budget_utilization_pct', 0):.1f}%")

        print("\n[PASS] Profit calendar generated successfully\n")
        return True

    except Exception as e:
        print(f"\n[FAIL] {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Agent B (Strategist) Test Suite")
    print("=" * 80)

    results = []

    # Test 1: Volume Objective
    results.append(("Volume Objective", test_volume_objective()))

    # Test 2: Profit Objective
    results.append(("Profit Objective", test_profit_objective()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    sys.exit(0 if all(p for _, p in results) else 1)
