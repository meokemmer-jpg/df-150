import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
# The literal syntax `from 150 import ...` is not valid Python because "150"
# is not an identifier. This is the executable equivalent:
from importlib import import_module
from pathlib import Path
import sys

import pytest

_HERE = Path(__file__).resolve().parent
for _base in (_HERE, _HERE.parent):
    if (_base / "150.py").exists():
        sys.path.insert(0, str(_base))
        break

_150 = import_module("150")
Asset = _150.Asset
Policy = _150.Policy
Claim = _150.Claim
InsuranceTracker = _150.InsuranceTracker
calculate_asset_status = _150.calculate_asset_status
calculate_insured_uninsured_values = _150.calculate_insured_uninsured_values
calculate_premium_total = _150.calculate_premium_total
calculate_open_claims_count = _150.calculate_open_claims_count


def test_per_asset_status_insured_partial_uninsured():
    tracker = InsuranceTracker()
    tracker.register_asset("house", 300_000)
    tracker.register_asset("car", 20_000)
    tracker.register_asset("boat", 5_000)

    tracker.register_policy("P1", "house", 250_000, 900)
    tracker.register_policy("P2", "house", 50_000, 100)
    tracker.register_policy("P3", "car", 20_000, 400)

    house = tracker.asset_status("house")
    car = tracker.asset_status("car")
    boat = tracker.asset_status("boat")

    assert house.status == "insured"
    assert house.covered_value == pytest.approx(300_000)
    assert house.uncovered_value == 0
    assert house.has_coverage_gap is False

    assert car.status == "insured"
    assert car.covered_value == pytest.approx(20_000)
    assert car.uncovered_value == 0

    assert boat.status == "uninsured"
    assert boat.covered_value == 0
    assert boat.uncovered_value == pytest.approx(5_000)
    assert boat.has_coverage_gap is True


def test_partial_coverage_creates_gap():
    tracker = InsuranceTracker()
    tracker.register_asset("jewelry", 100_000)
    tracker.register_policy("P4", "jewelry", 40_000, 250)

    status = tracker.asset_status("jewelry")

    assert status.status == "partial"
    assert status.covered_value == pytest.approx(40_000)
    assert status.uncovered_value == pytest.approx(60_000)
    assert status.coverage_percent == pytest.approx(0.4)
    assert status.has_coverage_gap is True
    assert len(tracker.coverage_gaps()) == 1


def test_totals_premium_and_open_claims():
    tracker = InsuranceTracker()
    tracker.register_asset("a", 10_000)
    tracker.register_asset("b", 20_000)
    tracker.register_asset("c", 30_000)

    tracker.register_policy("P5", "a", 10_000, 100)
    tracker.register_policy("P6", "b", 10_000, 200)

    tracker.register_claim("C1", "a", "open")
    tracker.register_claim("C2", "b", "pending")
    tracker.register_claim("C3", "c", "closed")

    insured, uninsured = tracker.insured_uninsured_values()
    assert insured == pytest.approx(20_000)
    assert uninsured == pytest.approx(40_000)
    assert tracker.premium_total() == pytest.approx(300)
    assert tracker.open_claims_count() == 2
    assert len(tracker.coverage_gaps()) == 2

    summary = tracker.summary()
    assert summary["insured_value"] == pytest.approx(20_000)
    assert summary["uninsured_value"] == pytest.approx(40_000)
    assert summary["premium_total"] == pytest.approx(300)
    assert summary["open_claims"] == 2
    assert summary["coverage_gaps"] == 2


def test_tracker_never_auto_buys_or_cancels():
    tracker = InsuranceTracker()
    tracker.register_asset("machine", 50_000)
    tracker.register_policy("P7", "machine", 50_000, 350)
    tracker.register_claim("C4", "machine", "open")

    assert tracker.asset_status("machine").status == "insured"
    assert tracker.coverage_gaps() == []
    assert tracker.premium_total() == pytest.approx(350)

    tracker.register_asset("fleet", 80_000)

    assert tracker.asset_status("fleet").status == "uninsured"
    assert tracker.premium_total() == pytest.approx(350)


def test_calculate_asset_status_caps_coverage_at_asset_value():
    asset = Asset("plant", 100_000)
    policies = [
        Policy("p1", "plant", 60_000, 200),
        Policy("p2", "plant", 60_000, 220),
    ]

    status = calculate_asset_status(asset, policies)

    assert status.status == "insured"
    assert status.covered_value == pytest.approx(100_000)
    assert status.uncovered_value == 0
    assert status.coverage_percent == pytest.approx(1.0)


def test_pure_calculators_are_exposed():
    assets = [Asset("a", 100), Asset("b", 200)]
    policies = [Policy("p1", "a", 100, 50), Policy("p2", "b", 100, 60)]
    claims = [Claim("c1", "a", "open"), Claim("c2", "b", "closed")]

    insured, uninsured = calculate_insured_uninsured_values(assets, policies)
    assert insured == pytest.approx(200.0)
    assert uninsured == pytest.approx(100.0)
    assert calculate_premium_total(policies) == pytest.approx(110)
    assert calculate_open_claims_count(claims) == 1


def test_report_is_json_serializable():
    tracker = InsuranceTracker()
    tracker.register_asset("a", 10_000)
    tracker.register_policy("P8", "a", 10_000, 50)

    report = tracker.report(report_date="2026-05-17")

    assert report["schema"] == "df-150-kpm-insurance-coverage-1.0"
    assert report["date"] == "2026-05-17"
    assert report["insured_value"] == pytest.approx(10_000)
    assert report["assets"][0]["status"] == "insured"

