import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib
import pytest

# Import the module whose file is named '150.py'
# (using importlib, because '150' is not a valid Python identifier)
AssetInsuranceTracker = importlib.import_module('150').AssetInsuranceTracker


def test_tracker_initial_state():
    """A fresh tracker should report all zeros and no gaps."""
    tracker = AssetInsuranceTracker()
    assert tracker.get_insured_value() == 0.0
    assert tracker.get_uninsured_value() == 0.0
    assert tracker.get_total_premium() == 0.0
    assert tracker.get_open_claims_count() == 0
    assert tracker.get_coverage_gaps() == []


def test_add_and_update_assets():
    """Core workflow: add assets, update insurance, check derived metrics."""
    tracker = AssetInsuranceTracker()
    tracker.add_asset("asset1", 50_000)
    tracker.add_asset("asset2", 30_000, insured=True, premium=200, open_claims=1)
    tracker.add_asset("asset3", 20_000, insured=True, premium=150)

    # Totals after initial adding
    assert tracker.get_insured_value() == 50_000   # asset2 + asset3
    assert tracker.get_uninsured_value() == 50_000  # asset1
    assert tracker.get_total_premium() == 350       # 200 + 150
    assert tracker.get_open_claims_count() == 1

    gaps = tracker.get_coverage_gaps()
    assert len(gaps) == 1
    assert gaps[0].asset_id == "asset1"

    # Update asset1 to insured
    tracker.update_insurance("asset1", insured=True, premium=100, open_claims=0)

    assert tracker.get_insured_value() == 100_000
    assert tracker.get_uninsured_value() == 0.0
    assert tracker.get_total_premium() == 450      # 350 + 100
    assert tracker.get_open_claims_count() == 1    # only asset2 still has 1
    assert len(tracker.get_coverage_gaps()) == 0   # no uninsured assets with value


def test_report_structure():
    """generate_report must return the correct dictionary fields."""
    tracker = AssetInsuranceTracker()
    tracker.add_asset("a1", 10_000, insured=True, premium=50)
    tracker.add_asset("a2", 0, insured=False)       # value zero, no gap
    tracker.add_asset("a3", 20_000, insured=False)  # gap

    report = tracker.generate_report()

    assert report["insured_value_eur"] == 10_000
    assert report["uninsured_value_eur"] == 20_000
    assert report["premium_total_eur"] == 50
    assert report["open_claims_count"] == 0
    assert set(report["coverage_gaps"]) == {"a3"}
    assert "report_date" in report


def test_update_nonexistent_asset_raises():
    """Updating a non-registered asset must raise KeyError."""
    tracker = AssetInsuranceTracker()
    with pytest.raises(KeyError, match="noasset"):
        tracker.update_insurance("noasset", insured=True)
