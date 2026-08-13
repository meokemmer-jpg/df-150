import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib
import sys
from pathlib import Path

# Python 3 allows an import of a file named "150.py" only via importlib,
# because `from 150 import ...` is syntactically invalid: module names must be
# valid identifiers and cannot start with a digit.
# The requested literal import would be:
# from 150 import InsuranceTracker
sys.path.insert(0, str(Path(__file__).resolve().parent))
df150 = importlib.import_module("150")
InsuranceTracker = df150.InsuranceTracker


def test_asset_insurance_tracking_core():
    tracker = InsuranceTracker()
    tracker.add_asset("DE0001", 100_000.0)
    tracker.add_asset("DE0002", 250_000.0, insured=True, premium_eur=1_250.0)
    tracker.add_asset("DE0003", 50_000.0)
    tracker.add_asset("DE0004", 0.0)  # zero value: no coverage gap

    assert tracker.insured_value_eur() == 250_000.0
    assert tracker.uninsured_value_eur() == 150_000.0  # 100k + 50k
    assert tracker.premium_total_eur() == 1_250.0
    assert tracker.open_claims_count == 0
    assert tracker.coverage_gaps() == ["DE0001", "DE0003"]


def test_claims_and_manual_status_update():
    tracker = InsuranceTracker()
    tracker.add_asset("A", 10_000.0)

    tracker.register_claim()
    tracker.register_claim()
    tracker.settle_claim()
    assert tracker.open_claims_count == 1

    # Manual status recording - not auto-buy/cancel.
    tracker.record_insurance_status("A", insured=True, premium_eur=200.0)
    assert tracker.insured_value_eur() == 10_000.0
    assert tracker.uninsured_value_eur() == 0.0
    assert tracker.premium_total_eur() == 200.0
    assert tracker.coverage_gaps() == []

    report = tracker.report()
    assert report["insured_value_eur"] == 10_000.0
    assert report["uninsured_value_eur"] == 0.0
    assert report["premium_total_eur"] == 200.0
    assert report["open_claims_count"] == 1
    assert report["coverage_gaps"] == []


def test_no_auto_policy_buy_or_cancel_methods():
    tracker = InsuranceTracker()
    assert not hasattr(tracker, "buy_policy")
    assert not hasattr(tracker, "cancel_policy")
    assert not hasattr(tracker, "auto_buy")
    assert not hasattr(tracker, "auto_cancel")
