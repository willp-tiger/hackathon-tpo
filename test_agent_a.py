"""
Quick test script for Agent A implementation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.data_loader import DataLoader
from agents.analyst import AnalystAgent
from loguru import logger
import json

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

def main():
    print("=" * 80)
    print("Testing Agent A (Analyst) Implementation")
    print("=" * 80)

    # Load data
    print("\n[1/5] Loading data...")
    data_dir = Path(__file__).parent / "case-data"
    loader = DataLoader(data_dir)

    sales_df = loader.load_sales()
    promo_df = loader.load_promotions()
    finance_df = loader.load_financials()

    print(f"  [OK] Loaded {len(sales_df)} sales records")
    print(f"  [OK] Loaded {len(promo_df)} promotion records")
    print(f"  [OK] Loaded {len(finance_df)} finance records")

    # Initialize Agent A
    print("\n[2/5] Initializing Agent A...")
    agent = AnalystAgent(sales_df, promo_df, finance_df)
    print("  [OK] Agent initialized")

    # Run analysis
    print("\n[3/5] Running causal inference analysis...")
    parameters = agent.analyze()
    print("  [OK] Analysis complete")

    print(f"\n  Baseline Velocity: {parameters['baseline_velocity_avg']:.2f} units/week")
    print(f"  Base Price Elasticity: {parameters['elasticity_model']['base_price_elasticity']:.2f}")
    print(f"  Discount Lift Factors:")
    for depth, lift in parameters['elasticity_model']['discount_lift_factors'].items():
        print(f"    - {depth}: {lift:.2f}x")
    print(f"  Display Lift Multiplier: {parameters['display_lift_multiplier']:.2f}x")
    print(f"  Seasonality Factors: {len(parameters['seasonality_factors'])} weeks")

    # Validate forecast
    print("\n[4/5] Validating baseline forecast...")
    metrics = agent.validate_baseline_forecast(holdout_weeks=12)
    print(f"  [OK] Validation complete")
    print(f"    - MAPE: {metrics['mape']:.2%}")
    print(f"    - RMSE: {metrics['rmse']:.2f}")
    print(f"    - MAE: {metrics['mae']:.2f}")

    if metrics['mape'] < 0.15:
        print(f"  [PASS] MAPE < 15% threshold MET")
    else:
        print(f"  [WARN] MAPE exceeds 15% threshold (got {metrics['mape']:.2%})")

    # Save parameters
    print("\n[5/5] Saving causal parameters...")
    output_path = Path(__file__).parent / "outputs" / "causal_parameters.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(parameters, f, indent=2)

    print(f"  [OK] Saved to {output_path}")

    print("\n" + "=" * 80)
    print("Agent A Test Complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
