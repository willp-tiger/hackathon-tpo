"""
Test script for complete Agent A execution with all tools.

This script tests the full Agent A workflow within 20 iterations:
1. Load data previews
2. Calculate baseline (PPG-Week Fixed Effects)
3. Validate baseline
4. Calculate elasticity and discount lift
5. Calculate tier-specific display lifts
6. Calculate feature lift
7. Calculate tactic combinations
8. Calculate seasonality factors
9. Save causal parameters

Expected: All tools execute successfully within iteration limit.
"""

import os
import sys
from pathlib import Path

# Force unbuffered output for live logging
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.analyst import AnalystAgent
from loguru import logger

# Configure logging with immediate flushing for live output
logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    colorize=True,
    enqueue=False  # Disable queue for immediate output
)


def main():
    """Run complete Agent A workflow test."""

    logger.info("=" * 80)
    logger.info("TESTING COMPLETE AGENT A WORKFLOW (20 ITERATION LIMIT)")
    logger.info("=" * 80)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        logger.info("Set it with: set ANTHROPIC_API_KEY=your_key_here")
        return

    # Initialize Agent A
    logger.info("\nInitializing Agent A...")
    agent = AnalystAgent(data_dir="case-data", output_dir="outputs")

    # Run analysis
    logger.info("\nStarting LLM-powered analysis...")
    logger.info("Expected tools to execute:")
    logger.info("  1. load_sales_preview")
    logger.info("  2. load_promotion_preview")
    logger.info("  3. calculate_baseline_ppg_week_fixed_effects")
    logger.info("  4. validate_baseline_forecast")
    logger.info("  5. calculate_elasticity_and_lift")
    logger.info("  6. calculate_display_lift_by_tier")
    logger.info("  7. calculate_feature_lift")
    logger.info("  8. calculate_tactic_combinations")
    logger.info("  9. calculate_seasonality_factors")
    logger.info(" 10. save_causal_parameters")
    logger.info("\nNOTE: Analysis takes 5-10 minutes - watch for iteration logs below")
    logger.info("")
    sys.stdout.flush()

    try:
        parameters = agent.analyze()
        sys.stdout.flush()

        logger.info("\n" + "=" * 80)
        logger.info("ANALYSIS COMPLETE - VALIDATING OUTPUTS")
        logger.info("=" * 80)

        # Validate all expected outputs are present
        validation_passed = True

        # Check baseline
        if 'baseline_velocity_avg' in parameters:
            logger.info(f"✅ Baseline velocity: {parameters['baseline_velocity_avg']:.2f} units")
        else:
            logger.error("❌ Missing: baseline_velocity_avg")
            validation_passed = False

        # Check elasticity model
        if 'elasticity_model' in parameters:
            logger.info(f"✅ Elasticity model: {len(parameters['elasticity_model'].get('discount_lift_factors', {}))} discount buckets")
        else:
            logger.error("❌ Missing: elasticity_model")
            validation_passed = False

        # Check tier-specific displays (NEW in Session 4)
        if 'tier_specific_display_lifts' in parameters:
            lifts = parameters['tier_specific_display_lifts']
            logger.info(f"✅ Tier-specific display lifts:")
            logger.info(f"   Platinum: {lifts.get('platinum_lift', 'N/A'):.2f}x")
            logger.info(f"   Gold: {lifts.get('gold_lift', 'N/A'):.2f}x")
            logger.info(f"   Silver: {lifts.get('silver_lift', 'N/A'):.2f}x")
            logger.info(f"   Bronze: {lifts.get('bronze_lift', 'N/A'):.2f}x")
        else:
            logger.error("❌ Missing: tier_specific_display_lifts (NEW TOOL)")
            validation_passed = False

        # Check feature lift (NEW in Session 4)
        if 'feature_lift_multiplier' in parameters:
            logger.info(f"✅ Feature lift multiplier: {parameters['feature_lift_multiplier']:.2f}x")
        else:
            logger.error("❌ Missing: feature_lift_multiplier (NEW TOOL)")
            validation_passed = False

        # Check tactic combinations (NEW in Session 4)
        if 'tactic_combination_effects' in parameters:
            tactics = parameters['tactic_combination_effects']
            logger.info(f"✅ Tactic combinations:")
            logger.info(f"   TPR only: {tactics.get('tpr_only', 'N/A'):.0f} units")
            logger.info(f"   TPR + Display: {tactics.get('tpr_plus_display', 'N/A'):.0f} units")
            logger.info(f"   TPR + Feature: {tactics.get('tpr_plus_feature', 'N/A'):.0f} units")
            logger.info(f"   TPR + Both: {tactics.get('tpr_plus_both', 'N/A'):.0f} units")
        else:
            logger.error("❌ Missing: tactic_combination_effects (NEW TOOL)")
            validation_passed = False

        # Check seasonality
        if 'seasonality_factors' in parameters:
            logger.info(f"✅ Seasonality factors: {len(parameters['seasonality_factors'])} weeks")
        else:
            logger.error("❌ Missing: seasonality_factors")
            validation_passed = False

        # Check approach log
        if 'approach_log' in parameters:
            logger.info(f"✅ Approach log: {len(parameters['approach_log'])} approaches tried")
            for idx, attempt in enumerate(parameters['approach_log'], 1):
                approach = attempt.get('approach', 'unknown')
                mape = attempt.get('mape', 0)
                status = attempt.get('status', 'unknown')
                logger.info(f"   {idx}. {approach}: MAPE = {mape:.2f}% ({status})")
        else:
            logger.error("❌ Missing: approach_log")
            validation_passed = False

        # Final validation
        logger.info("\n" + "=" * 80)
        if validation_passed:
            logger.info("✅ ALL TOOLS EXECUTED SUCCESSFULLY")
            logger.info("✅ Agent A workflow complete within 20 iterations")
        else:
            logger.error("❌ VALIDATION FAILED - Some tools did not execute")
            logger.error("Check execution log for details")
            return 1

        logger.info(f"\n📁 Results saved to:")
        logger.info(f"   - outputs/causal_parameters.json")
        logger.info(f"   - outputs/agent_a_execution_log.txt")

    except Exception as e:
        logger.error(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
