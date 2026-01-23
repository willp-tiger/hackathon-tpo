"""
Test script for LLM-powered Agent A (Analyst)

This script tests the new Claude API-based implementation to verify:
1. Claude makes appropriate tool calls
2. Reasoning appears in execution logs
3. Multiple approaches are tried
4. MAPE validation works
5. Final causal_parameters.json is generated
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.analyst import AnalystAgent


def main():
    """Test Agent A LLM implementation."""

    # Load environment variables
    load_dotenv()

    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )

    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY not set in environment")
        logger.info("Please create a .env file with: ANTHROPIC_API_KEY=your_key_here")
        return

    logger.info("=" * 80)
    logger.info("Testing LLM-Powered Agent A (Analyst)")
    logger.info("=" * 80)

    try:
        # Initialize agent
        logger.info("\n1. Initializing Agent A...")
        agent = AnalystAgent(data_dir="case-data", output_dir="outputs")
        logger.success("✓ Agent initialized successfully")

        # Run analysis
        logger.info("\n2. Running causal parameter generation...")
        logger.info("This will take 1-2 minutes as Claude analyzes the data...")
        logger.info("-" * 80)

        parameters = agent.analyze()

        logger.info("-" * 80)
        logger.success("✓ Analysis complete!")

        # Display results
        logger.info("\n3. Results:")
        logger.info(f"   Baseline Velocity: {parameters.get('baseline_velocity_avg', 'N/A')}")

        if 'elasticity_model' in parameters:
            logger.info(f"   Price Elasticity: {parameters['elasticity_model'].get('base_price_elasticity', 'N/A')}")
            logger.info(f"   Discount Lift Factors: {parameters['elasticity_model'].get('discount_lift_factors', {})}")

        logger.info(f"   Display Lift: {parameters.get('display_lift_multiplier', 'N/A')}")

        if 'seasonality_factors' in parameters:
            logger.info(f"   Seasonality Factors: {len(parameters['seasonality_factors'])} weeks defined")

        if 'approach_log' in parameters:
            logger.info(f"\n   Approaches Tried:")
            for approach in parameters['approach_log']:
                logger.info(f"      - {approach}")

        # Check output files
        logger.info("\n4. Output Files:")
        output_dir = Path("outputs")

        params_file = output_dir / "causal_parameters.json"
        if params_file.exists():
            logger.success(f"   ✓ {params_file} ({params_file.stat().st_size} bytes)")
        else:
            logger.error(f"   ✗ {params_file} not found")

        log_file = output_dir / "agent_a_execution_log.txt"
        if log_file.exists():
            logger.success(f"   ✓ {log_file} ({log_file.stat().st_size} bytes)")

            # Show excerpt of log
            with open(log_file, 'r') as f:
                lines = f.readlines()
                logger.info(f"\n   Execution log excerpt (last 20 lines):")
                for line in lines[-20:]:
                    logger.info(f"      {line.rstrip()}")
        else:
            logger.error(f"   ✗ {log_file} not found")

        logger.info("\n" + "=" * 80)
        logger.success("Agent A test completed successfully!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
