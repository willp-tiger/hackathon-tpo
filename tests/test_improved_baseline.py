"""
Test script for improved baseline forecasting methods.

This script tests the newly implemented baseline calculation approaches:
1. PPG-Retailer-Week Fixed Effects
2. Improved Regression with better features
3. STL Decomposition (retailer-aware)
4. Quantile Regression

Expected improvement: From 185-265% MAPE → 15-50% MAPE
Working at PPG (Product Group) granularity: 11 PPGs across 2 retailers
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

# Also add stderr to ensure all output is visible
logger.add(
    sys.stderr,
    level="DEBUG",
    format="{time:HH:mm:ss} | {level: <8} | {message}",
    colorize=False,
    enqueue=False
)


def main():
    """Run improved baseline forecasting test."""

    logger.info("=" * 80)
    logger.info("TESTING IMPROVED BASELINE FORECASTING METHODS")
    logger.info("=" * 80)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        logger.info("Set it with: set ANTHROPIC_API_KEY=your_key_here")
        return

    # Initialize Agent A
    logger.info("\nInitializing Agent A with improved baseline tools...")
    agent = AnalystAgent(data_dir="case-data", output_dir="outputs")

    # Run analysis
    logger.info("\nStarting LLM-powered analysis...")
    logger.info("Claude will now test multiple improved baseline approaches")
    logger.info("Expected MAPE improvement: 185-265% to 15-50%")
    logger.info("NOTE: Analysis takes 10-15 minutes - watch for iteration logs below")
    logger.info("")
    sys.stdout.flush()

    try:
        parameters = agent.analyze()
        sys.stdout.flush()

        logger.info("\n" + "=" * 80)
        logger.info("ANALYSIS COMPLETE")
        logger.info("=" * 80)

        # Display results
        logger.info(f"\nBaseline Velocity: {parameters.get('baseline_velocity_avg', 'N/A'):.2f} units")

        # Display approach log
        if 'approach_log' in parameters:
            logger.info("\n--- Approaches Tried ---")
            for idx, attempt in enumerate(parameters['approach_log'], 1):
                approach = attempt.get('approach', 'unknown')
                mape = attempt.get('mape', 0)
                status = attempt.get('status', 'unknown')
                logger.info(f"{idx}. {approach}: MAPE = {mape:.2f}% ({status})")

        # Display improvement metrics
        if parameters.get('approach_log'):
            old_mape = max([a.get('mape', 0) for a in parameters['approach_log'] if 'old' in a.get('approach', '').lower()] or [185])
            new_mape = min([a.get('mape', 999) for a in parameters['approach_log'] if 'old' not in a.get('approach', '').lower()])

            logger.info(f"\n--- Improvement Summary ---")
            logger.info(f"Old approach MAPE: ~{old_mape:.1f}%")
            logger.info(f"Best new approach MAPE: {new_mape:.1f}%")

            if new_mape < old_mape:
                improvement = ((old_mape - new_mape) / old_mape) * 100
                logger.info(f"✅ IMPROVEMENT: {improvement:.1f}% reduction in error")
            else:
                logger.warning(f"⚠️ No improvement detected - needs investigation")

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
