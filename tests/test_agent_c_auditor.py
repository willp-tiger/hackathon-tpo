"""Test Agent C (Auditor) constraint validation."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.auditor import AuditorAgent
from loguru import logger
import json

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")

def get_path(name):
    return str(Path(__file__).parent / "fixtures" / name)

def get_constraints():
    return {
        'budget_limit': 1000000,
        'min_gap_weeks': {'Retailer 0': 4, 'Retailer 1': 2},
        'max_promos_per_ppg': {'Retailer 0': 8, 'Retailer 1': 12},
        'blackout_weeks': {'Retailer 0': [44, 25, 51, 52], 'Retailer 1': [47, 49, 51, 52]},
        'max_discount': {'Retailer 0': 0.40, 'Retailer 1': 0.25}
    }

def test_valid(agent):
    logger.info("TEST 1: Valid Calendar")
    result = agent.audit(get_path("calendar_valid.json"), get_constraints())
    assert result['status'] == 'APPROVED'
    assert len(result['violations']) == 0
    logger.info("PASSED")
    return result

def test_budget(agent):
    logger.info("TEST 2: Budget Violation")
    result = agent.audit(get_path("calendar_budget_violation.json"), get_constraints())
    assert result['status'] == 'REJECTED'
    logger.info("PASSED")
    return result

def test_gap(agent):
    logger.info("TEST 3: Gap Violations")
    result = agent.audit(get_path("calendar_gap_violation.json"), get_constraints())
    assert result['status'] == 'REJECTED'
    logger.info("PASSED")
    return result

def test_frequency(agent):
    logger.info("TEST 4: Frequency Violations")
    result = agent.audit(get_path("calendar_frequency_violation.json"), get_constraints())
    assert result['status'] == 'REJECTED'
    logger.info("PASSED")
    return result

def test_blackout(agent):
    logger.info("TEST 5: Blackout Violations")
    result = agent.audit(get_path("calendar_blackout_violation.json"), get_constraints())
    assert result['status'] == 'REJECTED'
    logger.info("PASSED")
    return result

def main():
    logger.info("TESTING AGENT C")
    agent = AuditorAgent(data_dir="case-data", output_dir="outputs")
    
    tests = [test_valid, test_budget, test_gap, test_frequency, test_blackout]
    passed = 0
    for test in tests:
        try:
            test(agent)
            passed += 1
        except Exception as e:
            logger.error(f"FAILED: {e}")
    
    logger.info(f"Results: {passed}/{len(tests)} passed")
    if passed == len(tests):
        logger.info("ALL TESTS PASSED")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
