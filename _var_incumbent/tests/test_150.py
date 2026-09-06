import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
# test_150.py – run with pytest in the same directory as 150.py
# NOTE: Python cannot parse `from 150 import ...` because 150 is a number.
# We emulate the required import via importlib to make the test executable.
from importlib import import_module

# Load the module compiled from 150.py (equivalent to `from 150 import InsuranceTracker`)
InsuranceTracker = import_module('150').InsuranceTracker


def test_initial_state():
    t = InsuranceTracker()
    assert t.insured_value == 0
    assert t.uninsured_value == 0
    assert t.premium_total == 0.0
    assert t.open_claims_count == 0
    assert t.coverage_gaps == []


def test_add_insured_asset():
    t = InsuranceTracker()
    t.add_asset('house', 250_000, insured=True, premium=500)
    assert t.insured_value == 250_000
    assert t.uninsured_value == 0
    assert t.premium_total == 500.0


def test_add_uninsured_asset_and_gaps():
    t = InsuranceTracker()
    t.add_asset('boat', 30_000, insured=False)
    t.add_asset('car', 15_000, insured=True, premium=800)
    assert t.insured_value == 15_000
    assert t.uninsured_value == 30_000
    assert t.coverage_gaps == ['boat']
    assert t.premium_total == 800.0


def test_remove_asset():
    t = InsuranceTracker()
    t.add_asset('ring', 5_000, insured=True, premium=100)
    t.remove_asset('ring')
    assert t.insured_value == 0
    assert t.premium_total == 0.0


def test_change_insurance_status():
    t = InsuranceTracker()
    t.add_asset('art', 20_000, insured=False)
    t.set_insured_status('art', True)
    assert t.insured_value == 20_000
    assert t.uninsured_value == 0
    assert t.coverage_gaps == []


def test_claims_lifecycle():
    t = InsuranceTracker()
    c1 = t.file_claim()
    c2 = t.file_claim()
    assert t.open_claims_count == 2
    t.settle_claim(c1)
    assert t.open_claims_count == 1
    # settling unknown claim is a no-op
    t.settle_claim(999)
    assert t.open_claims_count == 1


def test_multiple_assets_coverage_gaps():
    t = InsuranceTracker()
    t.add_asset('a1', 100, True, 10)
    t.add_asset('a2', 200, False, 5)
    t.add_asset('a3', 300, False)
    gaps = t.coverage_gaps
    assert set(gaps) == {'a2', 'a3'}
    assert len(gaps) == 2
    assert t.uninsured_value == 500
    assert t.insured_value == 100
    assert t.premium_total == 15.0

