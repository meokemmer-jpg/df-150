import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
import importlib
import pytest

# Hinweis: `from 150 import KPMInsuranceTracker` ist in Python syntaktisch
# ungueltig, weil Modulnamen nicht mit einer Ziffer beginnen duerfen.
# Deshalb wird das Modul 150.py hier importlib-gestuetzt importiert.
m = importlib.import_module("150")
KPMInsuranceTracker = m.KPMInsuranceTracker


def test_asset_insurance_status_and_coverage_gaps():
    tracker = KPMInsuranceTracker()

    tracker.add_asset("a1", 100_000.0, 80_000.0)
    tracker.add_asset("a2", 50_000.0, 50_000.0)
    tracker.add_asset("a3", 20_000.0)

    tracker.set_policy("a1", 80_000.0, 1_200.0)
    tracker.set_policy("a2", 50_000.0, 600.0)
    tracker.set_policy("a3", 0.0, 0.0)

    status = tracker.status()

    assert status["total_asset_value_euro"] == 170_000.0
    assert status["insured_value_euro"] == 130_000.0
    assert status["uninsured_value_euro"] == 40_000.0
    assert status["premium_total_euro"] == 1_800.0
    assert status["open_claims_count"] == 0
    assert status["coverage_gaps"] == [
        {"asset_id": "a1", "gap_euro": 20_000.0},
        {"asset_id": "a3", "gap_euro": 20_000.0},
    ]


def test_open_claims_count():
    tracker = KPMInsuranceTracker()
    tracker.add_asset("a1", 100_000.0, 100_000.0)

    claim_1 = tracker.open_claim("a1", 5_000.0)
    claim_2 = tracker.open_claim("a1", 2_000.0)

    assert tracker.status()["open_claims_count"] == 2

    tracker.close_claim(claim_1)
    assert tracker.status()["open_claims_count"] == 1

    tracker.close_claim(claim_2)
    assert tracker.status()["open_claims_count"] == 0


def test_validation_rejects_negative_values_and_unknown_assets():
    tracker = KPMInsuranceTracker()
    tracker.add_asset("a1", 50_000.0)

    with pytest.raises(ValueError):
        tracker.add_asset("negative_asset", -1.0)

    with pytest.raises(KeyError):
        tracker.open_claim("missing_asset", 1.0)
