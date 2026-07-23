import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
# test_150.py
# Use dynamic import because '150' is not a valid Python module identifier.
import importlib
import sys
import os
import json
import pytest

sys.path.insert(0, '.')
module = importlib.import_module('150')
InsuranceTracker = module.InsuranceTracker

# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

def test_tracker_initial_summary():
    tracker = InsuranceTracker()
    summary = tracker.get_summary()
    assert summary['total_insured_value_eur'] == 0.0
    assert summary['total_uninsured_value_eur'] == 0.0
    assert summary['total_premium_eur'] == 0.0
    assert summary['total_open_claims_count'] == 0
    assert summary['coverage_gaps'] == []
    assert summary['coverage_gaps_count'] == 0

def test_add_asset_and_summary():
    tracker = InsuranceTracker()
    tracker.add_asset('A1', 1000, insured=True, premium=50, open_claims=2)
    tracker.add_asset('A2', 2000, insured=False, premium=0, open_claims=0)
    tracker.add_asset('A3', 3000, insured=True, premium=100, open_claims=1)
    summary = tracker.get_summary()
    assert summary['total_insured_value_eur'] == 4000.0
    assert summary['total_uninsured_value_eur'] == 2000.0
    assert summary['total_premium_eur'] == 150.0
    assert summary['total_open_claims_count'] == 3
    assert summary['coverage_gaps'] == ['A2']
    assert summary['coverage_gaps_count'] == 1

def test_update_asset():
    tracker = InsuranceTracker()
    tracker.add_asset('A1', 1000, insured=False)
    tracker.update_asset('A1', insured=True, premium=75)
    summary = tracker.get_summary()
    assert summary['total_insured_value_eur'] == 1000.0
    assert summary['total_uninsured_value_eur'] == 0.0
    assert summary['total_premium_eur'] == 75.0
    assert summary['coverage_gaps'] == []

def test_remove_asset():
    tracker = InsuranceTracker()
    tracker.add_asset('A1', 500, insured=True)
    tracker.remove_asset('A1')
    assert len(tracker.assets) == 0
    summary = tracker.get_summary()
    assert summary['total_insured_value_eur'] == 0.0

def test_coverage_gaps_only_uninsured_with_positive_value():
    tracker = InsuranceTracker()
    tracker.add_asset('A1', 0, insured=False)   # zero value → no gap
    tracker.add_asset('A2', -100, insured=False) # negative → no gap
    tracker.add_asset('A3', 100, insured=True)   # insured → no gap
    tracker.add_asset('A4', 200, insured=False)  # uninsured positive → gap
    summary = tracker.get_summary()
    assert summary['coverage_gaps'] == ['A4']

def test_generate_report(tmpdir):
    original_cwd = os.getcwd()
    try:
        os.chdir(tmpdir)
        tracker = InsuranceTracker()
        tracker.add_asset('A1', 100, insured=True, premium=10)
        filename = tracker.generate_report('2025-01-15')
        expected_path = 'reports/df-150-2025-01-15.json'
        assert os.path.exists(expected_path)
        with open(expected_path) as f:
            data = json.load(f)
        assert data['date'] == '2025-01-15'
        assert data['asset_count'] == 1
        assert data['summary']['total_insured_value_eur'] == 100.0
        assert 'assets' in data
        # cleanup
        os.remove(expected_path)
        os.rmdir('reports')
    finally:
        os.chdir(original_cwd)

def test_duplicate_asset_raises():
    tracker = InsuranceTracker()
    tracker.add_asset('A1', 100)
    with pytest.raises(ValueError):
        tracker.add_asset('A1', 200)

def test_update_nonexistent_raises():
    tracker = InsuranceTracker()
    with pytest.raises(KeyError):
        tracker.update_asset('X', insured=True)

def test_remove_nonexistent_raises():
    tracker = InsuranceTracker()
    with pytest.raises(KeyError):
        tracker.remove_asset('X')

