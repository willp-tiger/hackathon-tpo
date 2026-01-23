"""
Main entry point for TPO optimization system
"""

import argparse
import sys
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

from src.orchestrator import TPOOrchestrator


def setup_logging(log_level: str = "INFO", log_file: str = "outputs/agent_execution_log.txt"):
    """
    Configure logging.

    Args:
        log_level: Logging level
        log_file: Path to log file
    """
    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level
    )

    # Add file handler
    Path(log_file).parent.mkdir(exist_ok=True)
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level=log_level
    )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Trade Promotion Optimization - Multi-Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Optimize for volume with $1M budget
  python main.py --objective volume --budget 1000000

  # Optimize for profit with $1.5M budget
  python main.py --objective profit --budget 1500000

  # Run with debug logging
  python main.py --objective volume --budget 1000000 --log-level DEBUG
        """
    )

    parser.add_argument(
        "--objective",
        type=str,
        choices=["volume", "profit"],
        default="volume",
        help="Optimization objective (default: volume)"
    )

    parser.add_argument(
        "--budget",
        type=float,
        default=1_000_000,
        help="Total annual budget in dollars (default: 1000000)"
    )

    parser.add_argument(
        "--data-dir",
        type=str,
        default="case-data",
        help="Directory containing input data files (default: case-data)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Directory for output files (default: outputs)"
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Maximum iterations for optimization loop (default: 10)"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    return parser.parse_args()


def main():
    """Main execution function."""
    # Load environment variables
    load_dotenv()

    # Parse arguments
    args = parse_args()

    # Setup logging
    setup_logging(log_level=args.log_level)

    logger.info("Trade Promotion Optimization System")
    logger.info("=" * 80)

    try:
        # Initialize orchestrator
        orchestrator = TPOOrchestrator(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            max_iterations=args.max_iterations
        )

        # Run optimization
        results = orchestrator.run(
            objective=args.objective,
            budget=args.budget
        )

        # Print summary
        print("\n" + "=" * 80)
        print("OPTIMIZATION COMPLETE")
        print("=" * 80)
        print(f"Objective: {args.objective.upper()}")
        print(f"Budget: ${args.budget:,.0f}")
        print(f"Final Status: {results['reports']['audit_summary']['status']}")
        print(f"Calendar Events: {len(results['calendar']['calendar_events'])}")
        print(f"Total Spend: ${results['calendar']['total_projected_spend']:,.0f}")
        print(f"\nOutputs saved to: {args.output_dir}/")
        print("  - optimized_calendar.csv")
        print("  - financial_impact_report.json")
        print("  - baseline_validation.csv")
        print("  - agent_execution_log.txt")
        print("=" * 80)

        return 0

    except Exception as e:
        logger.exception(f"Error during optimization: {e}")
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
