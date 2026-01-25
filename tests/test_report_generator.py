"""
Test script for ExecutionReportGenerator

Tests the report generator with existing outputs from Session 11.
"""

from datetime import datetime, timedelta
from src.utils.report_generator import ExecutionReportGenerator, generate_quick_summary


def test_comprehensive_report():
    """Test comprehensive report generation with existing outputs."""

    print("Testing Comprehensive Report Generation...")
    print("="*60)

    # Create report generator
    generator = ExecutionReportGenerator(output_dir="outputs")

    # Simulate optimization result (from Session 11)
    optimization_result = {
        'status': 'REJECTED',  # Session 11 hit max iterations
        'iterations': 10,
        'objective': 'volume',
        'violations_history': [
            [
                {'type': 'GAP', 'details': 'Gap violation for PPG_1 at Retailer 0'},
                {'type': 'GAP', 'details': 'Gap violation for PPG_0 at Retailer 1'}
            ]
        ]
    }

    # Simulate timing
    start_time = datetime.now() - timedelta(minutes=2, seconds=30)
    end_time = datetime.now()

    # Generate report
    report = generator.generate_comprehensive_report(
        objective='volume',
        budget=100000.0,
        optimization_result=optimization_result,
        start_time=start_time,
        end_time=end_time
    )

    print("\nReport generated successfully!")
    print(f"Report saved to: {generator.report_path}")
    print(f"Report length: {len(report)} characters")
    print("\n" + "="*60)
    print("REPORT PREVIEW (first 1000 characters):")
    print("="*60)
    print(report[:1000])
    print("="*60)
    print("\nFull report saved to outputs/EXECUTION_SUMMARY.txt")

    return report


def test_quick_summary():
    """Test quick summary generation."""

    print("\n\nTesting Quick Summary Generation...")
    print("="*60)

    summary = generate_quick_summary(output_dir="outputs")

    print(summary)
    print("\nQuick summary generated successfully!")

    return summary


if __name__ == "__main__":
    print("ExecutionReportGenerator Test Suite")
    print("="*60)
    print()

    # Test 1: Comprehensive report
    try:
        report = test_comprehensive_report()
        print("[PASS] Comprehensive report generation")
    except Exception as e:
        print(f"[FAIL] Comprehensive report generation: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Quick summary
    try:
        summary = test_quick_summary()
        print("[PASS] Quick summary generation")
    except Exception as e:
        print(f"[FAIL] Quick summary generation: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("Test suite complete!")
    print("="*60)
