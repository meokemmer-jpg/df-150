import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib

# Dynamically import the module named '150' (allowed by Python via importlib)
mod = importlib.import_module('150')
InsuranceTracker = mod.InsuranceTracker

def test_insurance_tracker():
    tracker = InsuranceTracker()

    # Initially everything zero
    assert tracker.insured_value == 0
    assert tracker.uninsured_value == 0
    assert tracker.total_premium == 0
    assert tracker.open_claims_count == 0
    assert tracker.coverage_gap_count == 0

    # Add assets
    tracker.add_asset('A1', 'Building', 1000000.0)
    tracker.add_asset('A2', 'Equipment', 200000.0)
    tracker.add_asset('A3', 'Inventory', 50000.0)

    # All uninsured -> gap count = 3
    assert tracker.coverage_gap_count == 3
    assert tracker.insured_value == 0
    assert tracker.uninsured_value == 1250000.0

    # Set insurance for A1 (fully insured)
    tracker.set_insured_amount('A1', 1000000.0)
    assert tracker.insured_value == 1000000.0
    assert tracker.uninsured_value == 250000.0  # A2+A3 still uninsured
    assert tracker.coverage_gap_count == 2

    # Set partial insurance for A2 (underinsured)
    tracker.set_insured_amount('A2', 100000.0)
    assert tracker.insured_value == 1100000.0
    assert tracker.uninsured_value == 150000.0  # A2 100k gap + A3 50k gap
    # Gap count: A2 insured < value, A3 uninsured -> 2
    assert tracker.coverage_gap_count == 2

    # Fully insure A3
    tracker.set_insured_amount('A3', 50000.0)
    assert tracker.coverage_gap_count == 1  # only A2 underinsured
    assert tracker.insured_value == 1150000.0
    assert tracker.uninsured_value == 100000.0

    # Set premiums
    tracker.set_premium('A1', 5000.0)
    tracker.set_premium('A2', 1500.0)
    tracker.set_premium('A3', 250.0)
    assert tracker.total_premium == 6750.0

    # Add claims
    tracker.add_claim('C1', 'A1', 200000.0)
    tracker.add_claim('C2', 'A2', 50000.0)
    assert tracker.open_claims_count == 2

    # Close one claim
    tracker.close_claim('C1')
    assert tracker.open_claims_count == 1

    # Full report
    report = tracker.report()
    assert report == {
        'insured_value': 1150000.0,
        'uninsured_value': 100000.0,
        'total_premium': 6750.0,
        'open_claims_count': 1,
        'coverage_gap_count': 1,
    }

    # Trying to over-insure should raise
    try:
        tracker.set_insured_amount('A1', 999999999.0)
        assert False, 'Expected ValueError for over-insurance'
    except ValueError:
        pass  # expected

    # Duplicate additions raise
    try:
        tracker.add_asset('A1', 'dup', 1.0)
        assert False, 'Expected ValueError for duplicate asset'
    except ValueError:
        pass

    # Negative amounts raise
    try:
        tracker.set_insured_amount('A1', -1)
        assert False, 'Expected ValueError for negative insured amount'
    except ValueError:
        pass

    try:
        tracker.set_premium('A1', -1)
        assert False, 'Expected ValueError for negative premium'
    except ValueError:
        pass

