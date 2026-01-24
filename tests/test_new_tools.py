"""
Test script for Session 4 new promotion lift tools.

Tests:
1. Tier-specific display lifts
2. Feature lift
3. Tactic combinations
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import directly with absolute imports
import os
os.chdir(project_root)

from utils.data_loader import DataLoader
from agents.analyst import AnalystAgent

def test_new_tools():
    """Test the 3 new tools added in Session 4."""

    print("=" * 80)
    print("Session 4: Testing New Promotion Lift Tools")
    print("=" * 80)

    # Initialize agent
    data_dir = Path(__file__).parent.parent / "case-data"
    agent = AnalystAgent(str(data_dir))

    # Load data manually (agent needs sales_data to be set)
    loader = DataLoader(str(data_dir))
    agent.sales_data = loader.load_sales()

    print(f"\nLoaded sales data: {len(agent.sales_data)} records")
    print(f"Promotional records (TPR > 0): {agent.sales_data['TPR'].gt(0).sum()}")
    print(f"Non-promotional records (TPR = 0): {agent.sales_data['TPR'].eq(0).sum()}")

    # Test 1: Tier-specific display lifts
    print("\n" + "=" * 80)
    print("TEST 1: Tier-Specific Display Lifts")
    print("=" * 80)

    result1 = agent._tool_calculate_display_lift_by_tier()

    if "error" in result1:
        print(f"ERROR: {result1['error']}")
    else:
        print("\n✅ Tier-Specific Display Lifts:")
        print(f"  Platinum lift: {result1.get('platinum_lift', 'N/A'):.2f}x (n={result1.get('n_platinum', 0)})")
        print(f"  Gold lift:     {result1.get('gold_lift', 'N/A'):.2f}x (n={result1.get('n_gold', 0)})")
        print(f"  Silver lift:   {result1.get('silver_lift', 'N/A'):.2f}x (n={result1.get('n_silver', 0)})")
        print(f"  Bronze lift:   {result1.get('bronze_lift', 'N/A'):.2f}x (n={result1.get('n_bronze', 0)})")
        print(f"  TPR-only baseline: {result1.get('no_display_baseline', 0):.0f} units")
        print(f"  TPR-only count: {result1.get('n_tpr_only', 0)}")

    # Test 2: Feature lift
    print("\n" + "=" * 80)
    print("TEST 2: Feature Lift")
    print("=" * 80)

    result2 = agent._tool_calculate_feature_lift()

    if "error" in result2:
        print(f"ERROR: {result2['error']}")
    else:
        print("\n✅ Feature Lift:")
        print(f"  Feature multiplier: {result2.get('multiplier', 'N/A'):.2f}x")
        print(f"  With feature: {result2.get('n_with_feature', 0)} promos, avg {result2.get('with_feature_avg', 0):.0f} units")
        print(f"  Without feature: {result2.get('n_without_feature', 0)} promos, avg {result2.get('no_feature_baseline', 0):.0f} units")

    # Test 3: Tactic combinations
    print("\n" + "=" * 80)
    print("TEST 3: Tactic Combinations")
    print("=" * 80)

    result3 = agent._tool_calculate_tactic_combinations()

    if "error" in result3:
        print(f"ERROR: {result3['error']}")
    else:
        print("\n✅ Tactic Combinations:")
        print(f"  TPR only:          {result3.get('tpr_only', 0):.0f} units (n={result3['sample_sizes'].get('tpr_only', 0)})")
        print(f"  TPR + Display:     {result3.get('tpr_plus_display', 0):.0f} units (n={result3['sample_sizes'].get('tpr_display', 0)})")
        print(f"  TPR + Feature:     {result3.get('tpr_plus_feature', 0):.0f} units (n={result3['sample_sizes'].get('tpr_feature', 0)})")
        print(f"  TPR + Both:        {result3.get('tpr_plus_both', 0):.0f} units (n={result3['sample_sizes'].get('tpr_both', 0)})")
        print(f"  Interaction effect: {result3.get('interaction_effect', 'N/A')}")

        # Calculate expected values for comparison
        tpr_only = result3.get('tpr_only', 0)
        tpr_display = result3.get('tpr_plus_display', 0)
        tpr_feature = result3.get('tpr_plus_feature', 0)
        tpr_both = result3.get('tpr_plus_both', 0)

        if tpr_only > 0:
            display_lift = tpr_display / tpr_only
            feature_lift = tpr_feature / tpr_only
            additive_expected = tpr_only + (tpr_display - tpr_only) + (tpr_feature - tpr_only)
            multiplicative_expected = tpr_only * display_lift * feature_lift

            print(f"\n  Analysis:")
            print(f"    Display lift factor: {display_lift:.2f}x")
            print(f"    Feature lift factor: {feature_lift:.2f}x")
            print(f"    Additive expected: {additive_expected:.0f} units")
            print(f"    Multiplicative expected: {multiplicative_expected:.0f} units")
            print(f"    Actual (TPR + Both): {tpr_both:.0f} units")

            if tpr_both > multiplicative_expected:
                print(f"    ✅ SYNERGISTIC: Actual > Multiplicative ({tpr_both/multiplicative_expected:.1f}x)")
            else:
                print(f"    ⚠️  Less than multiplicative ({tpr_both/multiplicative_expected:.1f}x)")

    print("\n" + "=" * 80)
    print("✅ All new tools tested successfully!")
    print("=" * 80)

    return result1, result2, result3

if __name__ == "__main__":
    test_new_tools()
