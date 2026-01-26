"""
Demo Scenarios Runner for TPO AI Agents

Runs 3 key demonstration scenarios to showcase the system capabilities.
Each scenario demonstrates different aspects of the multi-agent system.

Usage:
    python run_demo_scenarios.py

Outputs:
    demo_outputs/scenario_1/ - Volume maximization
    demo_outputs/scenario_2/ - Profit maximization
    demo_outputs/scenario_3/ - Budget constraint with rejection loop

Created: 2026-01-25 (Session 14)
"""

import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime


def print_header(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def run_scenario(name: str, objective: str, budget: int, description: str):
    """Run a single scenario and save outputs."""
    print_header(f"SCENARIO: {name}")
    print(f"Description: {description}")
    print(f"Objective: {objective.upper()}")
    print(f"Budget: ${budget:,}")
    print()

    # Create output directory
    output_dir = Path("demo_outputs") / name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run optimization
    cmd = [
        "python", "main.py",
        "--objective", objective,
        "--budget", str(budget)
    ]

    print(f"Running: {' '.join(cmd)}")
    print(f"Please wait...\n")

    start_time = datetime.now()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        elapsed = (datetime.now() - start_time).total_seconds()

        if result.returncode == 0:
            print(f"SUCCESS - Completed in {elapsed:.1f}s")

            # Copy outputs
            files_copied = 0
            for output_file in [
                "promotion_calendar.json",
                "causal_parameters.json",
                "OPTIMIZATION_JOURNEY.txt",
                "EXECUTION_SUMMARY.txt",
                "journey_dashboard.html"
            ]:
                src = Path("outputs") / output_file
                if src.exists():
                    shutil.copy(src, output_dir / output_file)
                    files_copied += 1

            print(f"Saved {files_copied} files to: {output_dir}")
            print(f"View dashboard: {output_dir / 'journey_dashboard.html'}")

            # Print summary from execution report
            summary_path = output_dir / "EXECUTION_SUMMARY.txt"
            if summary_path.exists():
                print("\nQuick Summary:")
                content = summary_path.read_text()
                # Extract key metrics
                for line in content.split('\n'):
                    if any(keyword in line for keyword in ["Total Events:", "Total Spend:", "MAPE:", "Total Iterations:"]):
                        print(f"  {line.strip()}")

            return True

        else:
            print(f"FAILED - Return code: {result.returncode}")
            print(f"Error: {result.stderr[:500]}")
            return False

    except subprocess.TimeoutExpired:
        print("TIMEOUT - Scenario exceeded 10 minutes")
        return False

    except Exception as e:
        print(f"ERROR - {str(e)}")
        return False


def main():
    """Run all demo scenarios."""
    print_header("TPO AI AGENTS - DEMO SCENARIOS RUNNER")
    print("This will run 3 demonstration scenarios showcasing the multi-agent system.")
    print("Each scenario takes 2-5 minutes to complete.")
    print()

    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set your API key:")
        print("  Windows: set ANTHROPIC_API_KEY=your_key_here")
        print("  Unix: export ANTHROPIC_API_KEY=your_key_here")
        return

    # Create demo outputs directory
    Path("demo_outputs").mkdir(exist_ok=True)

    scenarios = [
        {
            "name": "scenario_1_volume_max",
            "objective": "volume",
            "budget": 1500000,
            "description": "Volume Maximization - High budget, aggressive promotions"
        },
        {
            "name": "scenario_2_profit_max",
            "objective": "profit",
            "budget": 1500000,
            "description": "Profit Maximization - High budget, selective promotions"
        },
        {
            "name": "scenario_3_budget_constraint",
            "objective": "volume",
            "budget": 500000,
            "description": "Budget Constraint - Low budget, rejection loop demonstration"
        }
    ]

    results = []

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[{i}/3] Starting {scenario['name']}...")

        success = run_scenario(
            name=scenario["name"],
            objective=scenario["objective"],
            budget=scenario["budget"],
            description=scenario["description"]
        )

        results.append((scenario["name"], success))

        # Pause between scenarios
        if i < len(scenarios):
            print("\n" + "-" * 70)
            input("Press Enter to continue to next scenario...")

    # Final summary
    print_header("DEMO SCENARIOS COMPLETE")

    print("Results Summary:")
    for name, success in results:
        status = "SUCCESS" if success else "FAILED"
        print(f"  [{status}] {name}")

    successful_count = sum(1 for _, success in results if success)
    print(f"\nCompleted: {successful_count}/{len(scenarios)} scenarios")

    print("\nOutputs saved in: demo_outputs/")
    print("\nTo view dashboards, open in browser:")
    for name, success in results:
        if success:
            print(f"  demo_outputs/{name}/journey_dashboard.html")

    print("\n" + "=" * 70)
    print("Thank you for using TPO AI Agents!")
    print("=" * 70)


if __name__ == "__main__":
    main()
